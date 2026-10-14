# frozen_string_literal: true

module AeosDashboard
  module Metrics
    module_function

    def requirement_completion(requirement, policy)
      weights = policy.fetch("lifecycle_stages")
      credit = policy.fetch("status_credit_ranges")
      applicable = Array(requirement.fetch("applicable_lifecycle_stages"))
      weighted_low = 0.0
      weighted_high = 0.0
      denominator = 0.0
      evidence_stages = 0

      applicable.each do |stage|
        evaluation = requirement.fetch("lifecycle").fetch(stage)
        status = evaluation.fetch("status")
        next if status == "NOT_APPLICABLE"

        weight = weights.fetch(stage).to_f
        range = credit.fetch(status).map(&:to_f)
        denominator += weight
        weighted_low += weight * range[0]
        weighted_high += weight * range[1]
        evidence_stages += 1 unless Array(evaluation["evidence"]).empty?
      end

      completion =
        if denominator.zero?
          [0.0, 0.0]
        else
          [weighted_low / denominator * 100, weighted_high / denominator * 100]
        end

      {
        "completion_range" => completion.map { |value| round_range(value) },
        "evidence_coverage" => applicable.empty? ? 0.0 : (evidence_stages.to_f / applicable.length * 100).round(1),
        "applicable_stage_count" => applicable.length
      }
    end

    def horizon(requirements, horizon_id, registry, policy, source_consistency, source_freshness)
      included = requirements.select { |requirement| Array(requirement["release_horizons"]).include?(horizon_id) }
      results = included.map { |requirement| requirement_completion(requirement, policy) }
      low = results.empty? ? 0.0 : results.sum { |result| result.dig("completion_range", 0) } / results.length
      high = results.empty? ? 0.0 : results.sum { |result| result.dig("completion_range", 1) } / results.length
      evidence = results.empty? ? 0.0 : results.sum { |result| result["evidence_coverage"] } / results.length
      previous = registry.fetch("previous_horizons").fetch(horizon_id)
      previous_range = previous.fetch("completion_range").map(&:to_f)
      trend =
        if previous.fetch("comparable", false)
          trend_label((low + high) / 2.0, previous_range.sum / 2.0)
        else
          "UNKNOWN"
        end
      confidence = confidence_label(evidence, policy, source_consistency, source_freshness, included)

      {
        "id" => horizon_id,
        "title" => horizon_title(horizon_id),
        "included_requirement_ids" => included.map { |requirement| requirement.fetch("id") },
        "included_requirement_count" => included.length,
        "deferred_requirement_ids" => included.select { |requirement| requirement["scope_state"] == "DEFERRED" }.map { |requirement| requirement.fetch("id") },
        "completion_range" => [round_range(low), round_range(high)],
        "display_completion" => display_range(low, high),
        "trend" => trend,
        "previous_meaningful_snapshot" => previous,
        "confidence" => confidence,
        "evidence_coverage" => "#{evidence.round}%",
        "blocked_critical_requirements" => blocked_critical(included),
        "principal_remaining_gap" => principal_gap(included)
      }
    end

    def release_centric(requirements, policy, source_consistency, source_freshness, capability_catalog: {}, unmapped_capability_targets: {})
      release_policy = policy.fetch("release_centric")
      selected_target = release_policy.fetch("current_release_target")
      ordered = dependency_order(requirements)
      dependency_index = ordered.each_with_index.to_h { |requirement, index| [requirement.fetch("id"), index] }
      target_requirements = requirements.group_by { |requirement| requirement.fetch("release_target") }
      target_estimates = target_requirements.keys.sort_by { |target| release_target_sort_key(target, selected_target) }.map do |target|
        release_estimate(
          target: target,
          requirements: target_requirements.fetch(target),
          policy: policy,
          source_consistency: source_consistency,
          source_freshness: source_freshness,
          capability_catalog: capability_catalog,
          dependency_index: dependency_index,
          unmapped_capability_targets: unmapped_capability_targets
        )
      end
      current = target_estimates.find { |estimate| estimate.fetch("target") == selected_target }
      raise ValidationError, "selected release target #{selected_target} has no canonical requirements" unless current

      rc_core_requirements = requirements.select do |requirement|
        requirement.fetch("release_target") == selected_target && Array(requirement.fetch("release_horizons")).include?("rc_core")
      end
      rc_core = release_estimate(
        target: selected_target,
        requirements: rc_core_requirements,
        policy: policy,
        source_consistency: source_consistency,
        source_freshness: source_freshness,
        capability_catalog: capability_catalog,
        dependency_index: dependency_index,
        unmapped_capability_targets: {}
      )

      {
        "current_release" => current,
        "private_rc_core" => rc_core,
        "release_targets" => target_estimates,
        "capabilities" => target_estimates.flat_map { |estimate| estimate.fetch("capabilities") },
        "sdk_components" => sdk_components(
          ordered,
          policy,
          source_consistency,
          source_freshness,
          capability_catalog
        ),
        "major_elements" => release_policy.fetch("major_elements").map do |element|
          keys = element.fetch("repository_keys")
          element_requirements = target_requirements.fetch(selected_target).select do |requirement|
            (requirement.fetch("participating_repositories").keys & keys).any?
          end
          release_estimate(
            target: selected_target,
            requirements: element_requirements,
            policy: policy,
            source_consistency: source_consistency,
            source_freshness: source_freshness,
            capability_catalog: capability_catalog,
            dependency_index: dependency_index,
            unmapped_capability_targets: {}
          ).merge("id" => element.fetch("id"), "title" => element.fetch("title"))
        end
      }
    end

    def velocity(events, policy)
      categories = policy.fetch("velocity_categories")
      counts = categories.to_h { |category| [category, 0] }
      seen = {}
      Array(events).each do |event|
        id = event.fetch("id")
        raise ValidationError, "duplicate velocity event #{id}" if seen[id]

        category = event.fetch("category")
        raise ValidationError, "unknown velocity category #{category}" unless counts.key?(category)

        seen[id] = true
        counts[category] += 1 if event.fetch("accepted", true)
      end

      ratio_policy = policy.fetch("report_to_product")
      planning = ratio_policy.fetch("planning_categories").sum { |category| counts.fetch(category, 0) }
      product = ratio_policy.fetch("product_categories").sum { |category| counts.fetch(category, 0) }
      ratio = product.zero? ? "UNKNOWN" : format("%.2f", planning.to_f / product)

      {
        "meaningful_event_window" => ratio_policy.fetch("meaningful_event_window"),
        "counts" => counts,
        "report_to_product_ratio" => ratio,
        "previous_report_to_product_ratio" => "UNKNOWN",
        "threshold" => "<= 0.50",
        "trend" => "UNKNOWN",
        "corrective_posture" => ratio == "UNKNOWN" ? "UNKNOWN" : (ratio.to_f <= 0.5 ? "WITHIN_POLICY" : "CORRECTIVE_FOCUS_REQUIRED")
      }
    end

    def capability_rollup(requirements, policy, capability_catalog:, target:, dependency_index:, unmapped_capability_targets:, source_consistency:, source_freshness:)
      mapped_ids = requirements.flat_map { |requirement| Array(requirement["capability_mappings"]) }.uniq
      unmapped_ids = unmapped_capability_targets.select { |_id, assigned_target| assigned_target == target }.keys
      (mapped_ids + unmapped_ids).uniq.map do |capability_id|
        mapped = requirements.select { |requirement| Array(requirement["capability_mappings"]).include?(capability_id) }
        catalog_entry = capability_catalog.fetch(capability_id, {})
        name = catalog_entry.fetch("name", capability_id)
        if mapped.empty?
          {
            "id" => capability_id,
            "name" => name,
            "target" => target,
            "estimate_status" => "UNAVAILABLE",
            "completion_percent" => nil,
            "display_completion" => "Estimate unavailable",
            "confidence" => "LOW",
            "weight" => 0.0,
            "requirement_ids" => [],
            "repositories" => [],
            "dependency_rank" => -1,
            "estimate_note" => "No canonical requirement relationship is recorded."
          }
        else
          allocated_weight = lambda do |requirement|
            mappings = Array(requirement.fetch("capability_mappings"))
            criticality_weight(requirement, policy) / mappings.length
          end
          weight = mapped.sum { |requirement| allocated_weight.call(requirement) }
          completion = mapped.sum { |requirement| scalar_requirement_completion(requirement, policy) * allocated_weight.call(requirement) } / weight
          evidence = mapped.sum { |requirement| requirement_completion(requirement, policy).fetch("evidence_coverage") } / mapped.length
          {
            "id" => capability_id,
            "name" => name,
            "target" => target,
            "estimate_status" => "ESTIMATED",
            "completion_percent" => round_scalar(completion),
            "display_completion" => display_percentage(completion),
            "confidence" => confidence_label(evidence, policy, source_consistency, source_freshness, mapped),
            "weight" => weight,
            "requirement_ids" => mapped.map { |requirement| requirement.fetch("id") },
            "repositories" => mapped.flat_map { |requirement| requirement.fetch("participating_repositories").keys }.uniq,
            "dependency_rank" => mapped.map { |requirement| dependency_index.fetch(requirement.fetch("id")) }.min,
            "estimate_note" => nil
          }
        end
      end.sort_by { |row| [row.fetch("dependency_rank"), row.fetch("id").sub(/\AC/, "").to_i] }
    end

    def sdk_components(requirements, policy, source_consistency, source_freshness, capability_catalog)
      requirements.select do |requirement|
        requirement.fetch("participating_repositories").key?("SDK") && !requirement.fetch("participating_repositories").key?("Peeler")
      end.map.with_index do |requirement, index|
        evidence = requirement_completion(requirement, policy).fetch("evidence_coverage")
        {
          "id" => requirement.fetch("id"),
          "title" => requirement.fetch("title"),
          "target" => requirement.fetch("release_target"),
          "completion_percent" => scalar_requirement_completion(requirement, policy),
          "display_completion" => display_percentage(scalar_requirement_completion(requirement, policy)),
          "confidence" => confidence_label(evidence, policy, source_consistency, source_freshness, [requirement]),
          "capabilities" => Array(requirement.fetch("capability_mappings")).map { |id| "#{id} #{capability_catalog.fetch(id, {}).fetch('name', id)}" },
          "dependency_rank" => index
        }
      end
    end

    def ai_usage(data)
      source = data.fetch("measurement_source", "UNKNOWN")
      reliability = data.fetch("reliability", "UNKNOWN")
      capacity = data.fetch("capacity_consumed_or_remaining", "UNKNOWN")
      efficiency =
        if reliability == "UNKNOWN" || capacity == "UNKNOWN" || !capacity.is_a?(Numeric) || capacity.zero?
          "UNKNOWN"
        else
          format("%.2f", data.fetch("accepted_deliverable_movement", 0).to_f / capacity)
        end

      data.merge(
        "efficiency" => efficiency,
        "provenance" => source,
        "interpretation" => efficiency == "UNKNOWN" ? "Authoritative usage accounting is absent or conflicting." : "Accepted deliverable movement per unit of reported capacity."
      )
    end

    def blocked_critical(requirements)
      requirements.count do |requirement|
        %w[CRITICAL_PATH RELEASE_CRITICAL].include?(requirement["criticality"]) &&
          requirement.fetch("lifecycle").values.any? { |evaluation| evaluation["status"] == "BLOCKED" }
      end
    end

    def principal_gap(requirements)
      ordered = requirements.sort_by do |requirement|
        criticality = { "CRITICAL_PATH" => 0, "RELEASE_CRITICAL" => 1, "STANDARD" => 2 }.fetch(requirement["criticality"], 3)
        [criticality, requirement.fetch("title")]
      end
      ordered.each do |requirement|
        requirement.fetch("applicable_lifecycle_stages").each do |stage|
          evaluation = requirement.fetch("lifecycle").fetch(stage)
          next if evaluation["status"] == "ACCEPTED"

          blocker = evaluation["blocker"]
          return "#{requirement['title']}: #{blocker == 'NOT_APPLICABLE' ? stage.tr('_', ' ') : blocker}"
        end
      end
      "No remaining applicable lifecycle gap recorded."
    end

    def confidence_label(evidence, policy, source_consistency, source_freshness, requirements)
      return "UNKNOWN" if requirements.empty?
      return "LOW" unless source_freshness == "CURRENT"
      return "MEDIUM" unless source_consistency == "CONSISTENT"
      return "LOW" if requirements.any? { |requirement| requirement.fetch("lifecycle").values.any? { |stage| stage["status"] == "UNKNOWN" } }

      thresholds = policy.fetch("confidence")
      fraction = evidence / 100.0
      return "HIGH" if fraction >= thresholds.fetch("high_evidence_coverage").to_f
      return "MEDIUM" if fraction >= thresholds.fetch("medium_evidence_coverage").to_f

      "LOW"
    end

    def horizon_title(id)
      {
        "rc_core" => "RC Core",
        "committed_v2" => "Committed v2",
        "release_readiness" => "Public/package/production release readiness"
      }.fetch(id)
    end

    def trend_label(current, previous)
      return "UP" if current > previous + 2
      return "DOWN" if current < previous - 2

      "FLAT"
    end

    def display_range(low, high)
      rounded_low = round_range(low)
      rounded_high = round_range(high)
      rounded_low == rounded_high ? "#{rounded_low.round}%" : "#{rounded_low.round}–#{rounded_high.round}%"
    end

    def round_range(value)
      (value / 5.0).round * 5.0
    end

    def release_estimate(target:, requirements:, policy:, source_consistency:, source_freshness:, capability_catalog:, dependency_index:, unmapped_capability_targets:)
      rollup = capability_rollup(
        requirements,
        policy,
        capability_catalog: capability_catalog,
        target: target,
        dependency_index: dependency_index,
        unmapped_capability_targets: unmapped_capability_targets,
        source_consistency: source_consistency,
        source_freshness: source_freshness
      )
      estimated_capabilities = rollup.select { |capability| capability.fetch("estimate_status") == "ESTIMATED" && capability.fetch("weight").positive? }
      total_weight = estimated_capabilities.sum { |capability| capability.fetch("weight") }
      completion = total_weight.zero? ? nil : estimated_capabilities.sum { |capability| capability.fetch("completion_percent") * capability.fetch("weight") } / total_weight
      evidence = requirements.empty? ? 0.0 : requirements.sum { |requirement| requirement_completion(requirement, policy).fetch("evidence_coverage") } / requirements.length

      {
        "target" => target,
        "estimate_status" => completion.nil? ? "UNAVAILABLE" : "ESTIMATED",
        "completion_percent" => completion.nil? ? nil : round_scalar(completion),
        "display_completion" => completion.nil? ? "Estimate unavailable" : display_percentage(completion),
        "included_requirement_ids" => requirements.map { |requirement| requirement.fetch("id") },
        "requirement_count" => requirements.length,
        "capability_count" => rollup.length,
        "capabilities" => rollup,
        "confidence" => confidence_label(evidence, policy, source_consistency, source_freshness, requirements),
        "principal_remaining_gap" => requirements.empty? ? "No canonical requirement relationship is recorded." : principal_gap(requirements)
      }
    end

    def scalar_requirement_completion(requirement, policy)
      low, high = requirement_completion(requirement, policy).fetch("completion_range")
      round_scalar((low + high) / 2.0)
    end

    def round_scalar(value)
      value.round
    end

    def display_percentage(value)
      "#{round_scalar(value)}%"
    end

    def release_target_sort_key(target, selected_target)
      return [0, 0] if target == selected_target
      return [2, 0] if target == "v2.x"

      [1, target.split(".").last.to_i]
    end

    def dependency_order(requirements)
      by_id = requirements.to_h { |requirement| [requirement.fetch("id"), requirement] }
      visiting = {}
      visited = {}
      ordered = []
      visit = lambda do |requirement|
        id = requirement.fetch("id")
        raise ValidationError, "cyclic requirement dependency at #{id}" if visiting[id]
        return if visited[id]

        visiting[id] = true
        Array(requirement.fetch("dependencies")).each do |dependency|
          raise ValidationError, "unknown requirement dependency #{dependency}" unless by_id.key?(dependency)

          visit.call(by_id.fetch(dependency))
        end
        visiting.delete(id)
        visited[id] = true
        ordered << requirement
      end
      requirements.each { |requirement| visit.call(requirement) }
      ordered
    end

    def criticality_weight(requirement, policy)
      policy.fetch("release_centric").fetch("criticality_weights").fetch(requirement.fetch("criticality")).to_f
    end
  end
end
