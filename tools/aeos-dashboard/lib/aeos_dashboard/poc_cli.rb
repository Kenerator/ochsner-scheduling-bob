# frozen_string_literal: true

require "optparse"
require "stringio"

module AeosDashboard
  class PocCLI
    COMMANDS = %w[generate open latest list doctor clean].freeze

    def self.run(argv, out: $stdout, err: $stderr, opener: nil, input: $stdin)
      new(out, err, opener, input).run(argv)
    end

    def initialize(out, err, opener, input)
      @out, @err, @opener, @input = out, err, opener, input
    end

    def run(argv)
      args = argv.dup
      if args.empty? || args.include?("--help") || args.include?("-h")
        @out.puts "PoC Flight Deck: generate [--open], open, latest, list, doctor, clean [--yes]. Consumer manifest required; --maintainer-unbundled explicitly selects development without export closure. Offline/key-free; no SDK reconciliation."
        return 0
      end
      command = args.shift
      raise ValidationError, "unsupported PoC command" unless COMMANDS.include?(command)
      options = {}
      parser = OptionParser.new do |p|
        p.on("--root ROOT") { |value| options[:root] = value }
        p.on("--config PATH") { |value| options[:config] = value }
        p.on("--output-root PATH") { |value| options[:output] = value }
        p.on("--rendered-at TIME") { |value| options[:time] = value }
        p.on("--open") { options[:open] = true }
        p.on("--yes") { options[:yes] = true }
        p.on("--maintainer-unbundled") { options[:unbundled] = true }
      end
      parser.parse!(args)
      raise ValidationError, "unexpected PoC arguments" unless args.empty?
      raise ValidationError, "operation option does not apply to this command" if (options[:open] && command != "generate") || (options[:yes] && command != "clean") || (options[:time] && command != "generate")
      supplied = Pathname.new(options.fetch(:root, Pathname.new(__dir__).join("../../../..").to_s)).expand_path
      @root = supplied.realpath
      @resources = @root.join("tools/aeos-dashboard")
      PocRuntime.validate_resources!(@root, @resources)
      manifest = @resources.join("export-manifest.json")
      if manifest.exist? || manifest.symlink?
        PocBundle.verify(@resources)
      elsif !options[:unbundled]
        raise ValidationError, "consumer export manifest is required"
      end
      config = options.fetch(:config, "docs/internal/flight-deck/project.yaml")
      config = project_path(supplied, config)
      @profile = Profiles::Poc.new(project_root: @root, resource_root: @resources, config_path: config)
      @loaded = @profile.load
      @project = @loaded.dig("project", "id")
      @output = project_path(supplied, options.fetch(:output, "tmp/aeos-dashboards"))
      @profile.validate_output_root!(@output)
      raise ValidationError, "dashboard output must be Git-ignored" unless ignored?(@output.join(".poc-ignore-probe"))
      case command
      when "generate"
        result = Generator.new(project_root: @root, run_dir: @root, output_root: @output,
          rendered_at: options.fetch(:time, Time.now.iso8601), profile: @profile, resource_root: @resources).generate
        @out.puts result.fetch("output_dir").join("index.html")
        return open_path(result.fetch("output_dir").join("index.html")) if options[:open]
      when "doctor"
        @profile.source_paths.each { |path| raise ValidationError, "required runtime resource missing" unless path.file? && !path.symlink? }
        @out.puts "Project-local inputs/runtime/output checks passed; no credential, app, network or acceptance action."
        @loaded.fetch("diagnostics").each { |item| @out.puts item }
      when "list"
        snapshots.each { |path| @out.puts path.join("index.html") }
      when "latest", "open"
        path = latest_snapshot.join("index.html")
        @out.puts path
        return open_path(path) if command == "open"
      when "clean"
        return clean(options.fetch(:yes, false))
      end
      0
    rescue OptionParser::ParseError
      @err.puts "Unsupported PoC option; use --help. SDK run/reconcile options are unavailable."
      2
    rescue Error, SystemCallError, ArgumentError, Psych::Exception
      @err.puts "PoC operation failed safely. Check contained public inputs, ignored output, runtime files and reported evidence limits."
      2
    end

    private

    def project_path(supplied, value)
      path = Pathname.new(value)
      raise ValidationError, "path traversal rejected" if path.each_filename.include?("..")
      path = path.relative_path_from(supplied) if path.absolute? && path.to_s.start_with?(supplied.to_s + "/")
      path = path.relative_path_from(@root) if path.absolute? && path.to_s.start_with?(@root.to_s + "/")
      raise ValidationError, "path escapes project" if path.absolute?
      @root.join(path)
    end

    def ignored?(path)
      _out, _err, status = Open3.capture3("git", "-C", @root.to_s, "check-ignore", "-q", path.to_s)
      status.success?
    end

    def project_output
      path = @output.join(@project)
      PocPaths.directory(@root, path)
      path
    end

    def snapshots
      parent = project_output
      return [] unless parent.directory?
      parent.children.select { |path| recognized?(path) }.sort_by { |path| path.basename.to_s }.reverse
    end

    def recognized?(path)
      @profile.recognized_snapshot?(path, @project)
    end

    def latest_snapshot
      @profile.latest_snapshot(project_output, @project)
    end

    def open_path(path)
      opened = if @opener
        @opener.call(path)
      else
        command = RUBY_PLATFORM.include?("darwin") ? "open" : "xdg-open"
        _output, _error, status = Open3.capture3(command, path.to_s)
        status.success?
      end
      return 0 if opened
      @err.puts "Could not open the browser. Use the local file path printed above."
      2
    rescue SystemCallError
      @err.puts "No supported opener available. Use the local file path printed above."
      2
    end

    def clean(yes)
      parent = project_output
      return 0 unless parent.directory?
      rows = snapshots
      expected = rows + [parent.join("latest.html")]
      raise ValidationError, "unknown output content refuses cleanup" unless (parent.children - expected).empty?
      pointer = parent.join("latest.html")
      latest_snapshot if !rows.empty? || pointer.exist? || pointer.symlink?
      unless yes
        @out.puts "Remove #{rows.length} recognized generated snapshots for #{@project}? [y/N]"
        return 0 unless @input.gets.to_s.strip.downcase == "y"
      end
      rows.each { |path| raise ValidationError, "snapshot changed before cleanup" unless recognized?(path) }
      rows.each { |path| FileUtils.remove_entry(path.to_s) }
      pointer.delete if pointer.file? && !pointer.symlink?
      @out.puts "Removed #{rows.length} recognized generated snapshots only."
      0
    end
  end
end
