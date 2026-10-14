# frozen_string_literal: true

require "digest"
require "json"
require "time"

module AeosDashboard
  class PocSnapshotBuilder
    STAGES = %w[implementation verification acceptance].freeze

    def initialize(inputs:, metric_policy:)
      @inputs, @policy = inputs, metric_policy
    end

    def build(rendered_at:, source:)
      Timestamp.validate!(rendered_at)
      @diagnostics = @inputs.fetch("diagnostics").dup
      requirements = @inputs.fetch("requirements").map { |row| evaluate(row, rendered_at, source) }
      active = requirements.reject { |row| row.fetch("scope_state") == "DEFERRED" }
      elements = @inputs.fetch("elements").map { |row| row.merge("summary" => summary(active.select { |req| row.fetch("requirement_ids").include?(req.fetch("id")) })) }
      capabilities = @inputs.fetch("capabilities").map do |row|
        row.merge("dependencies" => row.fetch("depends_on"), "summary" => summary(active.select { |req| row.fetch("requirement_ids").include?(req.fetch("id")) }))
      end
      begin
        capabilities = Metrics.dependency_order(capabilities)
        Metrics.dependency_order(requirements)
      rescue ValidationError => error
        @diagnostics << error.message
      end
      blockers = @inputs.fetch("gaps").select do |row|
        row.fetch("state") == "OPEN" && (row.fetch("requirement_ids").empty? || active.any? { |req| row.fetch("requirement_ids").include?(req.fetch("id")) })
      end
      identity = Digest::SHA256.hexdigest(JSON.generate(source.fetch("hashes")))[0, 12]
      {"schema_version" => 1, "profile" => "poc", "mechanism_version" => "1.0.0", "policy_version" => @policy.fetch("policy_version"),
        "project" => @inputs.fetch("project"), "run_id" => @inputs.dig("project", "id"),
        "snapshot_id" => "poc-#{Time.iso8601(rendered_at).strftime('%Y%m%dt%H%M%S')}-#{identity}", "rendered_at" => rendered_at,
        "source" => source, "scope_version" => @inputs.fetch("scope_version"), "summary" => summary(active),
        "requirements" => requirements, "elements" => elements, "capabilities" => capabilities,
        "gaps" => @inputs.fetch("gaps"), "attention" => @inputs.fetch("attention"), "blockers" => blockers,
        "recommended_action" => blockers.empty? ? "Inspect unknown evidence and mapped next steps; no acceptance is inferred." : blockers.first.fetch("title"),
        "movement" => {"status" => "UNKNOWN", "note" => "No source-supported comparable prior snapshot supplied."}, "diagnostics" => @diagnostics.uniq}
    end

    private

    def evaluate(row, rendered_at, source)
      result = Marshal.load(Marshal.dump(row))
      records = result.delete("evidence_records")
      records = [] unless result.fetch("native_definition_known")
      %w[verification acceptance].each do |stage|
        kind = stage == "verification" ? "qualification" : "human_decision"
        applicable = records.select { |record| record.fetch("kind") == kind && applicable?(record, row.fetch("id"), rendered_at, source) }
        next if applicable.empty?
        outcomes = applicable.map { |record| record.fetch("result") }.uniq
        if outcomes.length != 1
          @diagnostics << "#{row.fetch('id')}: contradictory #{stage} evidence"
          next
        end
        positive = stage == "verification" ? "PASS" : "ACCEPTED"
        # Decisions are recorded source references, never new gate authority.
        if stage == "acceptance" && applicable.any? { |record| !PocPaths.native_reference?(record["human_reference"]) }
          @diagnostics << "#{row.fetch('id')}: acceptance requires a valid explicit human decision reference"
          next
        end
        result.fetch("lifecycle")[stage] = {"status" => outcomes.first == positive ? "COMPLETE" : "IN_PROGRESS", "result" => outcomes.first,
          "evidence" => applicable.map { |record|
            entry = {"reference" => record.fetch("reference"), "source_revision" => record.fetch("source_revision"), "executed_at" => record.fetch("executed_at"), "kind" => kind}
            entry["human_reference"] = record.fetch("human_reference") if stage == "acceptance"
            entry
          }}
      end
      result.merge(Metrics.requirement_completion(result, @policy))
    end

    def applicable?(record, id, rendered_at, source)
      reason = if !record.fetch("scope").include?(id)
        "does not cover requirement"
      elsif source.fetch("input_state", "UNKNOWN") != "COMMITTED"
        "working input is not executed-commit evidence"
      elsif !record.fetch("artifacts_valid")
        "artifact digest mismatch"
      elsif record.fetch("source_revision") != source.fetch("commit") && !record.fetch("scope_hashes_valid")
        "candidate mismatch without unchanged-scope hashes"
      else
        begin
          age = Time.iso8601(rendered_at) - Time.iso8601(record.fetch("executed_at"))
          if age < 0
            "execution time is in the future"
          elsif age > @policy.dig("freshness", "evidence_max_age_seconds")
            "evidence is stale"
          end
        rescue ArgumentError
          "invalid evidence timestamp"
        end
      end
      @diagnostics << "#{id}: #{reason}" if reason
      reason.nil?
    end

    def summary(rows)
      rows = rows.uniq { |row| row.fetch("id") }
      counts = STAGES.to_h do |stage|
        states = rows.map { |row| row.dig("lifecycle", stage, "status") }
        [stage, {"complete" => states.count("COMPLETE"), "unknown" => states.count("UNKNOWN"), "applicable" => states.count { |state| state != "NOT_APPLICABLE" }}]
      end
      known = !rows.empty? && counts.values.all? { |count| count.fetch("unknown").zero? }
      denominator = rows.sum { |row| row.fetch("weight") }.to_f
      percent = if known && denominator > 0
        (rows.sum { |row| row.fetch("completion_range").sum / 2.0 * row.fetch("weight") } / denominator).round
      end
      counts.merge("requirement_count" => rows.length, "weight_denominator" => denominator,
        "estimate_status" => known ? "ESTIMATED" : "UNAVAILABLE", "completion_percent" => percent)
    end
  end
end
