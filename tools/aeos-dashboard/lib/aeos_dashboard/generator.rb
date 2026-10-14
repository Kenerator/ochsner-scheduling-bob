# frozen_string_literal: true

require "fileutils"
require "digest"
require "find"
require "open3"
require "tmpdir"

module AeosDashboard
  class Generator
    attr_reader :project_root, :run_dir, :output_root, :rendered_at

    def initialize(project_root:, run_dir:, output_root:, rendered_at:, profile: nil, resource_root: nil)
      @project_root = Pathname.new(project_root).realpath
      @run_dir = Pathname.new(run_dir).realpath
      @output_root = Pathname.new(output_root).expand_path
      @rendered_at = Timestamp.validate!(rendered_at)
      @profile = profile || Profiles::Sdk.new(project_root: @project_root, run_dir: @run_dir,
        resource_root: resource_root || @project_root.join("tools/aeos-dashboard"), config_path: nil)
    end

    def generate
      @profile.validate_output_root!(output_root) if @profile.respond_to?(:validate_output_root!)
      ensure_ignored_output!
      policy = YAML.load_file(@profile.metric_policy_path.to_s)
      guard = SourceGuard.new(
        project_root: project_root,
        source_paths: @profile.source_paths,
        rendered_at: rendered_at,
        current_max_age_seconds: policy.dig("freshness", "current_max_age_seconds")
      )
      guarded_paths = @profile.guarded_paths
      guarded_before = guarded_inventory(guarded_paths)
      before = guard.capture
      loaded = @profile.load
      metadata = @profile.source_metadata(inputs: loaded)
      source = guard.metadata(before, **metadata)
      snapshot = build_snapshot(loaded, source)
      artifacts = Renderer.new(@profile.template_root).render(snapshot)
      if @profile.respond_to?(:seal_generated_artifacts?) && @profile.seal_generated_artifacts?
        Renderer.new(@profile.template_root).seal_poc_artifacts(snapshot, artifacts)
      end

      after = guard.capture
      if guard.changed?(before, after)
        raise GenerationError, "PoC canonical source changed during generation" if @profile.respond_to?(:reject_changed_source?) && @profile.reject_changed_source?
        warnings = metadata.fetch(:consistency_warnings) + ["Canonical source commit or hash changed during generation."]
        source = guard.metadata(before, **metadata.merge(consistency_warnings: warnings, freshness_override: "INCONSISTENT"))
        snapshot = build_snapshot(loaded, source)
        artifacts = Renderer.new(@profile.template_root).render(snapshot)
      end

      SchemaValidator.validate!(snapshot, SchemaValidator.load(@profile.schema_path))
      @profile.validate_snapshot_path!(output_root, snapshot.fetch("run_id"), snapshot.fetch("snapshot_id")) if @profile.respond_to?(:validate_snapshot_path!)
      @profile.validate_latest_pointer!(output_root.join(snapshot.fetch("run_id")), snapshot.fetch("run_id")) if @profile.respond_to?(:validate_latest_pointer!)
      ensure_ignored_artifacts!(snapshot.fetch("run_id"), snapshot.fetch("snapshot_id"), artifacts.keys)
      output_dir = write_atomically(snapshot.fetch("run_id"), snapshot.fetch("snapshot_id"), artifacts)
      unless guarded_inventory(guarded_paths) == guarded_before
        FileUtils.rm_rf(output_dir.to_s)
        raise GenerationError, "guarded dashboard input changed during generation; completed snapshot removed"
      end
      latest = write_latest(output_dir)

      {
        "output_dir" => output_dir,
        "latest_path" => latest,
        "snapshot" => snapshot,
        "artifacts" => artifacts.keys
      }
    end

    private

    def build_snapshot(loaded, source)
      @profile.build_snapshot(inputs: loaded, rendered_at: rendered_at, source: source)
    end

    def ensure_ignored_output!
      candidate = output_root.join(".aeos-ignore-probe")
      raise GenerationError, "output root is not ignored by Git: #{output_root}" unless ignored_by_git?(candidate)
    end

    def ensure_ignored_artifacts!(run_id, snapshot_id, artifact_names)
      final = output_root.join(run_id, snapshot_id)
      unignored = artifact_names.reject { |name| ignored_by_git?(final.join(name)) }
      return if unignored.empty?

      raise GenerationError, "generated artifacts are not ignored by Git: #{unignored.join(', ')}"
    end

    def write_latest(output_dir)
      @profile.validate_latest_pointer!(output_dir.dirname, output_dir.dirname.basename.to_s) if @profile.respond_to?(:validate_latest_pointer!)
      latest = output_dir.dirname.join("latest.html")
      raise GenerationError, "latest entry point is not ignored or is a symlink: #{latest}" unless ignored_by_git?(latest) && !latest.symlink?

      target = "#{output_dir.basename}/index.html"
      temporary = latest.dirname.join(".latest-#{Process.pid}.tmp")
      created = false
      label = @profile.respond_to?(:latest_label) ? @profile.latest_label : "Open latest verified snapshot"
      File.open(temporary.to_s, File::WRONLY | File::CREAT | File::EXCL, 0o600) do |file|
        created = true
        file.write("<!doctype html><meta charset=\"utf-8\"><meta http-equiv=\"refresh\" content=\"0; url=#{target}\"><title>Latest AEOS Flight Deck</title><a href=\"#{target}\">#{label}</a>\n")
      end
      File.rename(temporary.to_s, latest.to_s)
      latest
    ensure
      FileUtils.rm_f(temporary.to_s) if defined?(created) && created && temporary
    end

    def ignored_by_git?(path)
      _stdout, _stderr, status = Open3.capture3(git_env, "git", "-C", project_root.to_s, "check-ignore", "-q", path.to_s)
      status.success?
    end

    def write_atomically(run_id, snapshot_id, artifacts)
      @profile.validate_snapshot_path!(output_root, run_id, snapshot_id) if @profile.respond_to?(:validate_snapshot_path!)
      run_root = output_root.join(run_id)
      final = run_root.join(snapshot_id)
      raise GenerationError, "snapshot output already exists: #{final}" if final.exist? || final.symlink?

      FileUtils.mkdir_p(run_root.to_s)
      temporary = Pathname.new(Dir.mktmpdir(".#{snapshot_id}.tmp-", run_root.to_s))
      artifacts.each { |name, body| temporary.join(name).write(body) }
      File.rename(temporary.to_s, final.to_s)
      final
    ensure
      FileUtils.rm_rf(temporary.to_s) if defined?(temporary) && temporary && temporary.exist?
    end

    def git_env
      {
        "HOME" => project_root.to_s,
        "XDG_CONFIG_HOME" => project_root.join("tmp/aeos-dashboard-git-config").to_s,
        "GIT_CONFIG_NOSYSTEM" => "1"
      }
    end

    def guarded_inventory(paths)
      entries = {}
      paths.each do |root|
        root = Pathname.new(root).expand_path
        relative_guard_path(root)
        unless root.exist? || root.symlink?
          entries[relative_guard_path(root)] = "MISSING"
          next
        end

        if root.directory? && !root.symlink?
          Find.find(root.to_s) do |candidate|
            path = Pathname.new(candidate)
            entries[relative_guard_path(path)] = guarded_fingerprint(path)
            Find.prune if path.symlink?
          end
        else
          entries[relative_guard_path(root)] = guarded_fingerprint(root)
        end
      end
      entries.sort.to_h
    end

    def guarded_fingerprint(path)
      stat = File.lstat(path.to_s)
      mode = format("%04o", stat.mode & 0o7777)
      return "L:#{mode}:#{File.readlink(path.to_s)}" if stat.symlink?
      return "D:#{mode}" if stat.directory?
      return "F:#{mode}:#{stat.size}:#{Digest::SHA256.file(path.to_s).hexdigest}" if stat.file?

      "O:#{mode}:#{stat.ftype}"
    end

    def relative_guard_path(path)
      relative = path.relative_path_from(project_root)
      if relative.each_filename.first == ".."
        raise GenerationError, "guarded dashboard path escapes project root: #{path}"
      end

      relative.to_s
    end
  end
end
