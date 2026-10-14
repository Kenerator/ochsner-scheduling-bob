# frozen_string_literal: true

require "digest"
require "open3"
require "time"

module AeosDashboard
  class SourceGuard
    Capture = Struct.new(:commit, :hashes, :source_state_timestamp, :uncommitted_sources, keyword_init: true)

    def initialize(project_root:, source_paths:, rendered_at:, current_max_age_seconds:)
      @project_root = Pathname.new(project_root)
      @source_paths = source_paths.map { |path| Pathname.new(path) }
      @rendered_at = Timestamp.validate!(rendered_at)
      @current_max_age_seconds = current_max_age_seconds.to_i
    end

    def capture
      commit = git_value("rev-parse", "HEAD")
      Capture.new(
        commit: commit,
        hashes: @source_paths.to_h { |path| [relative(path), Digest::SHA256.file(path.to_s).hexdigest] },
        source_state_timestamp: latest_source_timestamp,
        uncommitted_sources: uncommitted_sources(commit)
      )
    end

    def changed?(before_capture, after_capture)
      before_capture.hashes != after_capture.hashes
    end

    def metadata(capture, state_milestone:, scope_baseline_version:, consistency_warnings: [], freshness_override: nil)
      consistency = consistency_warnings.empty? ? "CONSISTENT" : "DEGRADED"
      {
        "commit" => capture.commit || "UNKNOWN",
        "source_state_timestamp" => capture.source_state_timestamp || "UNKNOWN",
        "state_milestone" => state_milestone || "UNKNOWN",
        "scope_baseline_version" => scope_baseline_version || "UNKNOWN",
        "hashes" => capture.hashes,
        "input_state" => capture.uncommitted_sources.nil? ? "UNKNOWN" : (capture.uncommitted_sources.empty? ? "COMMITTED" : "WORKING_TREE"),
        "uncommitted_sources" => capture.uncommitted_sources || [],
        "freshness" => freshness_override || freshness(capture),
        "consistency" => freshness_override == "INCONSISTENT" ? "INCONSISTENT" : consistency,
        "consistency_warnings" => consistency_warnings
      }
    end

    private

    def relative(path)
      path.relative_path_from(@project_root).to_s
    rescue ArgumentError
      path.to_s
    end

    def git_env
      {
        "HOME" => @project_root.to_s,
        "XDG_CONFIG_HOME" => @project_root.join("tmp/aeos-dashboard-git-config").to_s,
        "GIT_CONFIG_NOSYSTEM" => "1"
      }
    end

    def git_value(*arguments)
      stdout, _stderr, status = Open3.capture3(git_env, "git", "-C", @project_root.to_s, *arguments)
      status.success? ? stdout.strip : nil
    end

    def latest_source_timestamp
      relative_paths = @source_paths.map { |path| relative(path) }
      git_value("log", "-1", "--format=%cI", "--", *relative_paths)
    end

    def uncommitted_sources(commit)
      return nil unless commit

      paths = @source_paths.map { |path| relative(path) }
      tree = git_value("ls-tree", "-r", "-z", commit, "--", *paths)
      hashes = git_value("hash-object", "--no-filters", "--", *@source_paths.map(&:to_s))
      return nil unless tree && hashes

      blobs = tree.split("\0").to_h do |entry|
        metadata, path = entry.split("\t", 2)
        [path, metadata.split.last]
      end
      current = hashes.lines.map(&:strip)
      return nil unless current.length == paths.length

      paths.zip(current).map { |path, hash| path unless blobs[path] == hash }.compact.sort
    end

    def freshness(capture)
      return "UNKNOWN" unless capture.commit && capture.source_state_timestamp

      age = Time.iso8601(@rendered_at) - Time.iso8601(capture.source_state_timestamp)
      age > @current_max_age_seconds ? "STALE" : "CURRENT"
    rescue ArgumentError
      "UNKNOWN"
    end
  end
end
