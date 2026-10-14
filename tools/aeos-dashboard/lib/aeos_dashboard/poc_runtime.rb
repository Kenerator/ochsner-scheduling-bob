# frozen_string_literal: true

require "pathname"
require "yaml"
require "json"
require "digest"
require "open3"
require "time"
require "fileutils"
require "tmpdir"

module AeosDashboard
  module PocRuntime
    LIBRARIES = %w[errors timestamp schema_validator metrics renderer source_guard generator poc_input poc_snapshot_builder profiles/poc poc_cli poc_bundle].freeze
    FILES = (LIBRARIES.map { |name| "lib/aeos_dashboard/#{name}.rb" } + %w[
      lib/aeos_dashboard/poc_runtime.rb poc-flight-deck config/poc-metric-policy-v1.yaml
      schemas/poc-project.schema.json schemas/poc-snapshot.schema.json
      templates/poc/level-1.md.erb templates/poc/level-2.md.erb templates/poc/manager.md.erb
      templates/poc/engineering.md.erb templates/poc/standalone.html.erb
      poc-self-check POC-EXPORT-NOTICE.md
    ]).freeze
    LOADED_ROOT = Pathname.new(__dir__).join("../..").realpath.freeze
    # Capture the implementation/resource bytes at process load, not from a
    # subsequently selected project's possibly different bundle.
    LOADED_DIGESTS = FILES.to_h { |relative| [relative, Digest::SHA256.file(LOADED_ROOT.join(relative)).hexdigest] }.freeze

    def self.validate_resources!(project_root, resources)
      resources = Pathname.new(resources).expand_path
      PocPaths.directory(project_root, resources) # Before manifest/content IO.
      raise ValidationError, "project runtime directory missing" unless resources.directory?
      FILES.each do |relative|
        path = PocPaths.resolve(resources, relative)
        raise ValidationError, "selected runtime differs from loaded implementation" unless Digest::SHA256.file(path).hexdigest == LOADED_DIGESTS.fetch(relative)
      end
      resources
    end
  end
end

AeosDashboard::PocRuntime::LIBRARIES.each { |name| require_relative name }
