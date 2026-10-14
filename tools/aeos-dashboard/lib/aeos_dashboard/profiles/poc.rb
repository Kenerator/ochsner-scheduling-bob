# frozen_string_literal: true

module AeosDashboard
  module Profiles
    class Poc
      def initialize(project_root:, run_dir: nil, resource_root:, config_path:)
        supplied_root = Pathname.new(project_root).expand_path
        @root = supplied_root.realpath
        resources = Pathname.new(resource_root).expand_path
        resources = @root.join(resources.relative_path_from(supplied_root)) if resources.to_s.start_with?(supplied_root.to_s + "/")
        @resources = PocRuntime.validate_resources!(@root, resources)
        @input = PocInput.new(project_root: supplied_root, config_path: config_path)
      end

      def source_paths
        @input.load
        @input.source_paths + PocRuntime::FILES.map { |relative| @resources.join(relative) }
      end

      def guarded_paths
        source_paths
      end

      def metric_policy_path; @resources.join("config/poc-metric-policy-v1.yaml"); end
      def schema_path; @resources.join("schemas/poc-snapshot.schema.json"); end
      def template_root; @resources.join("templates/poc"); end
      def load; @input.load; end

      def validate_output_root!(path)
        PocPaths.directory(@root, path)
        id = @input.load.dig("project", "id")
        depth = path.join(id, "snapshot").relative_path_from(@root).each_filename.count
        @evidence_prefix = "../" * depth
      end

      def reject_changed_source?; true; end
      def validate_snapshot_path!(output_root, project_id, snapshot_id)
        raise ValidationError, "invalid PoC project identity" unless project_id.is_a?(String) && project_id.match?(/\A[a-z0-9][a-z0-9-]{0,63}\z/)
        raise ValidationError, "invalid PoC snapshot identity" unless snapshot_id.is_a?(String) && snapshot_id.match?(/\Apoc-[a-z0-9-]{1,123}\z/)
        PocPaths.directory(@root, output_root.join(project_id, snapshot_id))
      end
      def seal_generated_artifacts?; true; end
      def latest_label; "Open latest generated PoC snapshot"; end

      def recognized_snapshot?(path, project_id)
        PocPaths.directory(@root, path)
        return false if path.symlink? || !path.directory? || !path.basename.to_s.match?(/\Apoc-[a-z0-9-]+\z/)
        expected = Renderer::ARTIFACT_TEMPLATES.keys + ["snapshot.yaml"]
        return false unless path.children.map { |child| child.basename.to_s }.sort == expected.sort
        return false unless path.children.all? { |child| child.file? && !child.symlink? }
        snapshot = PocPaths.structured(path.join("snapshot.yaml"))
        SchemaValidator.validate!(snapshot, SchemaValidator.load(schema_path))
        digests = snapshot["generated_artifacts"]
        return false unless digests.is_a?(Hash) && digests.keys.sort == Renderer::ARTIFACT_TEMPLATES.keys.sort
        return false unless snapshot["integrity_mode"] == "index-footer-v1"
        index = PocPaths.read(path.join("index.html"))
        footer = index.match(/\n<!-- poc-snapshot-sha256:([0-9a-f]{64}) -->\n\z/)
        return false unless footer && footer[1] == Digest::SHA256.file(path.join("snapshot.yaml")).hexdigest
        return false unless digests.all? do |name, digest|
          actual = name == "index.html" ? Digest::SHA256.hexdigest(index[0...footer.begin(0)]) : Digest::SHA256.file(path.join(name)).hexdigest
          actual == digest
        end
        snapshot.fetch("profile") == "poc" && snapshot.fetch("run_id") == project_id && snapshot.fetch("snapshot_id") == path.basename.to_s
      rescue Error, SystemCallError, Psych::Exception
        false
      end

      def latest_snapshot(parent, project_id)
        PocPaths.directory(@root, parent)
        pointer = parent.join("latest.html")
        raise ValidationError, "no recognized latest snapshot" unless pointer.file? && !pointer.symlink?
        content = PocPaths.read(pointer)
        target = content[/url=(poc-[a-z0-9-]+)\/index\.html/, 1]
        path = target && parent.join(target)
        raise ValidationError, "latest pointer is not a recognized project snapshot" unless path && recognized_snapshot?(path, project_id)
        relative = "#{target}/index.html"
        expected = "<!doctype html><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"0; url=#{relative}\"><title>Latest AEOS Flight Deck</title><a href=\"#{relative}\">#{latest_label}</a>\n"
        raise ValidationError, "latest pointer contains unrecognized content" unless content == expected
        path
      end

      def validate_latest_pointer!(parent, project_id)
        PocPaths.directory(@root, parent)
        pointer = parent.join("latest.html")
        latest_snapshot(parent, project_id) if pointer.exist? || pointer.symlink?
      end

      def source_metadata(inputs:)
        {state_milestone: "Project-local canonical specification and native tasks", scope_baseline_version: inputs.fetch("scope_version"),
          consistency_warnings: inputs.fetch("diagnostics")}
      end

      def build_snapshot(inputs:, rendered_at:, source:)
        PocSnapshotBuilder.new(inputs: inputs, metric_policy: YAML.load_file(metric_policy_path)).build(rendered_at: rendered_at, source: source).merge("evidence_prefix" => @evidence_prefix || "../../../../")
      end
    end
  end
end
