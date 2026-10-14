# frozen_string_literal: true

require "erb"
require "yaml"
require "uri"
require "json"

module AeosDashboard
  class Renderer
    ARTIFACT_TEMPLATES = {
      "level-1-executive-flight-deck.md" => "level-1.md.erb",
      "level-2-executive-matrix-board.md" => "level-2.md.erb",
      "manager.md" => "manager.md.erb",
      "engineering.md" => "engineering.md.erb",
      "index.html" => "standalone.html.erb"
    }.freeze

    def initialize(template_root)
      @template_root = Pathname.new(template_root)
    end

    def render(snapshot)
      context = TemplateContext.new(snapshot)
      artifacts = ARTIFACT_TEMPLATES.to_h do |artifact_name, template_name|
        template = ERB.new(@template_root.join(template_name).read, nil, "-")
        [artifact_name, template.result(context.get_binding)]
      end
      artifacts["snapshot.yaml"] = snapshot_yaml(snapshot)
      artifacts
    end

    def snapshot_yaml(snapshot)
      # PoC snapshots are portable public data and their strict reader rejects
      # YAML aliases. Detach shared Ruby containers before serialization; leave
      # the established SDK representation unchanged.
      serialized = snapshot["profile"] == "poc" ? JSON.parse(JSON.generate(snapshot)) : snapshot
      serialized.to_yaml
    end

    def seal_poc_artifacts(snapshot, artifacts)
      snapshot["integrity_mode"] = "index-footer-v1"
      # The index digest covers its rendered body, excluding only this footer.
      # The footer then binds the complete snapshot bytes, which bind all five
      # view bodies. This detects edits without a seventh file or signature claim.
      snapshot["generated_artifacts"] = artifacts.reject { |name, _body| name == "snapshot.yaml" }.transform_values { |body| Digest::SHA256.hexdigest(body) }
      artifacts["snapshot.yaml"] = snapshot_yaml(snapshot)
      artifacts["index.html"] += "\n<!-- poc-snapshot-sha256:#{Digest::SHA256.hexdigest(artifacts.fetch('snapshot.yaml'))} -->\n"
      artifacts
    end

    class TemplateContext
      attr_reader :snapshot

      def initialize(snapshot)
        @snapshot = snapshot
      end

      def get_binding
        binding
      end

      def table(headers, rows)
        lines = []
        lines << "| #{headers.join(' | ')} |"
        lines << "| #{headers.map { '---' }.join(' | ')} |"
        rows.each { |row| lines << "| #{row.map { |cell| md(cell) }.join(' | ')} |" }
        lines.join("\n")
      end

      def md(value)
        value.to_s.gsub("|", "\\|").gsub("\n", " ")
      end

      def h(value)
        ERB::Util.html_escape(value.to_s)
      end

      def poc_text(value)
        h(value).gsub(/[\\`*_\[\]!]/) { |character| "\\#{character}" }
      end

      def poc_table(headers, rows)
        table(headers.map { |value| poc_text(value) }, rows.map { |row| row.map { |value| poc_text(value) } })
      end

      def poc_counts(summary)
        %w[implementation verification acceptance].map do |stage|
          count = summary.fetch(stage)
          "#{stage.capitalize}: #{count.fetch('complete')}/#{count.fetch('applicable')} complete; #{count.fetch('unknown')} unknown"
        end.join(" · ")
      end

      def poc_estimate(summary)
        summary.fetch("completion_percent").nil? ? "Estimate unavailable" : "#{summary.fetch('completion_percent')}%"
      end

      def poc_reference(reference)
        prefix = snapshot.fetch("evidence_prefix", "../../../../")
        URI::DEFAULT_PARSER.escape(prefix + reference.to_s, /[^a-zA-Z0-9\-._~\/]/)
      end

      def status(value)
        {
          "ACCEPTED" => "✓ ACCEPTED",
          "IN_PROGRESS" => "◐ IN_PROGRESS",
          "BLOCKED" => "✕ BLOCKED",
          "NOT_STARTED" => "○ NOT_STARTED",
          "EVIDENCE_INCOMPLETE" => "△ EVIDENCE_INCOMPLETE",
          "NOT_APPLICABLE" => "— NOT_APPLICABLE",
          "DEFERRED" => "↷ DEFERRED",
          "UNKNOWN" => "? UNKNOWN"
        }.fetch(value.to_s, value.to_s)
      end

      def source_identity
        source = snapshot.fetch("source")
        "#{source.fetch('freshness')} / #{source.fetch('consistency')} · Inputs: #{source.fetch('input_state', 'UNKNOWN')}"
      end

      def source_quality_note
        "Source-file freshness/consistency only; not live status assurance."
      end

      def receiver_source_quality_note
        "Source-file freshness/consistency only; not receiver verification."
      end

      def legacy_lifecycle_note
        "Legacy broader-scope weighted lifecycle estimate; not current GA readiness or remaining effort."
      end

      def ga_readiness
        snapshot["ga_readiness"]
      end

      def ga_gate_summary
        return "No current-release GA readiness object supplied." unless ga_readiness

        counts = ga_readiness.fetch("gates").group_by { |gate| gate.fetch("state") }.transform_values(&:length)
        "#{ga_readiness.fetch('gates').length} gates reported: #{counts.fetch('ACCEPTED', 0)} accepted, #{counts.fetch('OPEN', 0)} open, #{counts.fetch('WAITING', 0)} waiting."
      end

      def ga_completion(rows = ga_readiness && ga_readiness["deliverables"])
        return {"percent" => "N/A", "counts" => "No deliverable baseline supplied"} if rows.nil? || rows.empty?

        verified = rows.count { |row| row.fetch("state") == "VERIFIED" }
        percent = (100.0 * verified / rows.length).round
        percent = [percent, 99].min if verified < rows.length
        {"percent" => "#{percent}%", "counts" => "#{verified}/#{rows.length} verified"}
      end

      def ga_major_elements
        rows = ga_readiness.fetch("deliverables", [])
        %w[SDK Licensing Website Docs Integration].map do |area|
          ga_completion(rows.select { |row| row.fetch("area") == area }).merge("title" => area)
        end
      end

      def ga_completion_note
        "Verified current-GA deliverables; not remaining effort or GA acceptance. Each named outcome counts once; no partial credit. Non-gating/deprecated work is excluded."
      end

      def ga_deliverable_rows
        return [] unless ga_readiness

        ga_readiness.fetch("deliverables", []).map do |row|
          [row.fetch("area"), row.fetch("title"), row.fetch("state"), row.fetch("verified_at", "—"), row.fetch("basis"), row.fetch("evidence")]
        end
      end

      def ga_gate_rows
        return [] unless ga_readiness

        ga_readiness.fetch("gates").map do |gate|
          [gate.fetch("id"), gate.fetch("title"), gate.fetch("owner"), gate.fetch("state"), gate.fetch("evidence"), gate.fetch("next_action")]
        end
      end

      def leadership_gate_rows
        ga_readiness.fetch("gates").map do |gate|
          [gate.fetch("id"), gate.fetch("title"), executive_label(gate.fetch("owner")), gate.fetch("state"), gate.fetch("completed_at", "—"), executive_label(gate.fetch("next_action"))]
        end
      end

      def package_scope_note
        scope = ga_readiness && ga_readiness["package_scope"]
        return "Package scope not supplied; do not infer it from historical matrix counts." unless scope

        labels = {"linux_x86_64" => "Linux x86_64", "macos_aarch64" => "macOS ARM64", "windows_x86_64" => "Windows x86_64", "macos_x86_64" => "macOS x86_64"}
        supported = scope.fetch("required_pro_platforms").map { |platform| labels.fetch(platform, platform) }.join(", ")
        unsupported = scope.fetch("unsupported_platforms").map { |platform| "#{labels.fetch(platform, platform)}: unsupported" }.join("; ")
        "Required Pro packages: #{supported}. CE source builds: #{scope.fetch('ce_source_builds_gating') ? 'gating' : 'non-gating'}. OSS/CE release archives: #{scope.fetch('oss_release_archives') ? 'required' : 'none'}. #{unsupported}."
      end

      def ga_evidence_progress_rows
        return [] unless ga_readiness

        ga_readiness.fetch("evidence_progress").map do |row|
          [row.fetch("label"), row.fetch("status"), row.fetch("evidence")]
        end
      end

      def ga_non_gating_rows
        return [] unless ga_readiness

        ga_readiness.fetch("non_gating").map { |row| [row.fetch("title"), row.fetch("reason")] }
      end

      def executive_waiting_on(row)
        waiting_on = row.fetch("waiting_on").to_s
        return waiting_on unless waiting_on.match?(/codex\/|\breceivers?\b|callback|audit|\bbranches?\b|dirty\.file|\.claude|\b[0-9a-f]{40}\b|\brc_core\b|CORRECTIVE_FOCUS_REQUIRED|WITHIN_POLICY/i)

        "See Release Readiness detail."
      end

      def executive_label(value)
        text = value.to_s
        return "See Release Readiness detail." if text.match?(/codex\/|dirty\.file|\.claude|\b[0-9a-f]{40}\b|\brc_core\b|CORRECTIVE_FOCUS_REQUIRED|WITHIN_POLICY/i)

        text.gsub(/\breceivers?\b/i, "workstream")
          .gsub(/\bcallbacks?\b/i, "handoffs")
          .gsub(/\baudits?\b/i, "reviews")
          .gsub(/\bbranches?\b/i, "variants")
      end

      def release_centric_metrics
        snapshot.fetch("release_centric_metrics")
      end

      def current_release
        release_centric_metrics.fetch("current_release")
      end

      def private_rc_core
        release_centric_metrics.fetch("private_rc_core")
      end

      def release_targets
        release_centric_metrics.fetch("release_targets")
      end

      def major_elements
        release_centric_metrics.fetch("major_elements")
      end

      def current_capabilities
        release_centric_metrics.fetch("capabilities")
      end

      def sdk_components
        release_centric_metrics.fetch("sdk_components")
      end

      def release_mode
        snapshot.fetch("release_mode")
      end

      def action_progress
        snapshot.fetch("action_progress")
      end

      def execution_board
        snapshot.fetch("execution_board")
      end

      def executive_next_action
        executive_label(release_mode.fetch("next_action").fetch("display_summary", release_mode.dig("next_action", "description")))
      end

      def lifecycle_reconciliation
        action_progress.fetch("lifecycle_reconciliation")
      end

      def standing_boundary_count
        snapshot.fetch("standing_boundary_count")
      end

      def sdk_requirements
        dependency_order.select { |requirement| requirement.fetch("participating_repositories").key?("SDK") }
      end

      def target_estimate(target)
        target == "v2.0.0" ? current_release.fetch("display_completion") : snapshot.fetch("release_horizons").fetch("committed_v2").fetch("display_completion")
      end

      def target_note(target)
        return "Current v2.0.0 estimate; deferred work contributes zero." if target == "v2.0.0"

        "Committed-v2 estimate only; #{target} is not independently partitioned in canonical state."
      end

      def horizon_order
        %w[rc_core committed_v2 release_readiness]
      end

      def horizon_label(id)
        snapshot.dig("release_horizons", id, "title") || human_label(id)
      end

      def human_label(value)
        value.to_s.downcase.tr("_", " ").sub(/\A./, &:upcase)
      end

      def stage_order
        %w[implemented tested integrated documented packaged release_ready]
      end

      def integration_stage_order
        %w[clean_base_selected required_changes_identified candidate_constructed repository_validation_accepted cross_repository_validation_accepted federated_manifest_pinned final_disposition]
      end

      def dependency_order(requirements = snapshot.fetch("requirements"))
        by_id = requirements.to_h { |requirement| [requirement.fetch("id"), requirement] }
        visited = {}
        ordered = []
        visit = lambda do |requirement|
          return if visited[requirement.fetch("id")]

          visited[requirement.fetch("id")] = true
          Array(requirement["dependencies"]).each { |dependency| visit.call(by_id.fetch(dependency)) if by_id.key?(dependency) }
          ordered << requirement
        end
        requirements.each { |requirement| visit.call(requirement) }
        ordered
      end

      def approved_release_targets
        %w[v2.0.0 v2.1 v2.2 v2.3 v2.x]
      end

      def target_horizon(target)
        target == "v2.0.0" ? "rc_core" : "committed_v2"
      end

      def capability_label(id)
        {
          "C1" => "RC scope and authority freeze",
          "C2" => "SDK commercially critical core",
          "C3" => "Flagship Examples proof",
          "C4" => "Docs buyer journey",
          "C5" => "Plugins and MCP discovery path",
          "C6" => "Website and commerce convergence",
          "C7" => "Licensing and entitlement readiness",
          "C8" => "Peeler integration checkpoint",
          "C9" => "Release integration and evidence"
        }.fetch(id, human_label(id))
      end

      def engineering_signals
        signals = []
        source = snapshot.fetch("source")
        signals << "#{source.fetch('freshness')} source freshness; rerender before treating readiness as current." unless source.fetch("freshness") == "CURRENT"
        signals << "#{source.fetch('consistency')} source consistency; conflicting evidence remains conservative." unless source.fetch("consistency") == "CONSISTENT"
        signals << "Current #{release_mode.dig('blockers', 0, 'owner').downcase} action: #{release_mode.dig('blockers', 0, 'title')}"
        signals << "Positive signal: Private RC Core is #{private_rc_core.fetch('display_completion')}; Release Mode continues on the separate selected-release path." if private_rc_core["completion_percent"] == 100
        deferred = release_targets.find { |target| target.fetch("target") == "v2.x" }
        signals << "Restoration opportunity: #{deferred.fetch('requirement_count')} deferred v2.x requirements retain their recorded completion evidence." if deferred
        low_confidence = (major_elements + current_capabilities).select { |row| row["confidence"] == "LOW" }.map { |row| row["title"] || row["name"] }.compact.uniq
        signals << "Evidence caution: low confidence for #{low_confidence.join(', ')}." unless low_confidence.empty?
        signals << (standing_boundary_count == 1 ? "1 standing boundary awaits its documented trigger." : "#{standing_boundary_count} standing boundaries await their documented triggers.") if standing_boundary_count.positive?
        signals << "Current source state is consistent and fresh." if signals.empty?
        signals.first(7)
      end
    end
  end
end
