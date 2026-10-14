# frozen_string_literal: true

require "json"
require "yaml"
require "digest"

module AeosDashboard
  # Shared PoC path/structured-input rules. Never discover another project.
  module PocPaths
    module_function

    def native_reference?(reference)
      reference.is_a?(Hash) && reference.keys.sort == %w[message_id thread_id turn_id] && reference.values.all? do |value|
        value.is_a?(String) && value.match?(/\A(?!00000000-0000-0000-0000-000000000000\z)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\z/)
      end
    end

    def directory(root, path)
      relative = Pathname.new(path).relative_path_from(root)
      parts = relative.each_filename.to_a
      raise ValidationError, "output escapes project or selects root" if parts.empty? || parts == ["."] || parts.any? { |part| part == ".." || part.start_with?(".") }
      cursor = root
      parts.each do |part|
        cursor = cursor.join(part)
        raise ValidationError, "symlink or non-directory output rejected" if cursor.symlink? || (cursor.exist? && !cursor.directory?)
      end
      path
    end

    def resolve(root, value, missing: false)
      raise ValidationError, "invalid project-relative reference" unless value.is_a?(String) && !value.empty? && !value.include?("\0")
      relative = Pathname.new(value)
      parts = relative.each_filename.to_a
      sensitive = /\A(?:private|intake|credentials?|secrets?)(?:\z|\.(?!py\z|rb\z))|(?:\A|[-_])intake(?:[-_.]|\z)|\Aprivate[-_]key|\APoR-|\.(?:pem|p12|pfx|key)\z/i
      if relative.absolute? || parts.any? { |part| part == ".." || part.start_with?(".") || part.match?(sensitive) } || (parts & %w[auth bw]).any?
        raise ValidationError, "private or escaping project reference rejected"
      end
      path = root
      parts.each do |part|
        path = path.join(part)
        raise ValidationError, "symlink project reference rejected" if path.symlink?
      end
      if path.exist?
        raise ValidationError, "project reference is not a regular file" unless path.file?
        raise ValidationError, "project reference escapes root" unless path.realpath.to_s.start_with?(root.to_s + File::SEPARATOR)
      elsif !missing
        raise ValidationError, "required project reference is missing"
      end
      path
    end

    def read(path)
      raise ValidationError, "project input is too large" if path.size > 2_000_000
      text = path.read(encoding: "UTF-8")
      raise ValidationError, "project input is not UTF-8" unless text.valid_encoding?
      text
    end

    def structured(path)
      text = read(path)
      tree = Psych.parse_stream(text)
      check_yaml_keys(tree)
      value = YAML.safe_load(text, permitted_classes: [], permitted_symbols: [], aliases: false)
      raise ValidationError, "structured project input must be an object" unless value.is_a?(Hash)
      value
    rescue Psych::Exception, JSON::ParserError
      raise ValidationError, "invalid structured project input"
    end

    def check_yaml_keys(node)
      if node.is_a?(Psych::Nodes::Mapping)
        keys = node.children.each_slice(2).map(&:first)
        raise ValidationError, "unsupported structured field" unless keys.all? { |key| key.is_a?(Psych::Nodes::Scalar) }
        values = keys.map(&:value)
        raise ValidationError, "duplicate structured field" unless values.uniq.length == values.length
      end
      Array(node.respond_to?(:children) ? node.children : nil).each { |child| check_yaml_keys(child) }
    end
  end

  class PocInput
    attr_reader :source_paths

    def initialize(project_root:, config_path:)
      supplied_root = Pathname.new(project_root).expand_path
      @root = supplied_root.realpath
      config = Pathname.new(config_path)
      # macOS /var -> /private/var is a root alias, not an input escape.
      # Derive the supplied relative path before checking every child component.
      config = config.relative_path_from(supplied_root) if config.absolute?
      @config_path = PocPaths.resolve(@root, config.to_s)
      @source_paths = []
    end

    def load
      @source_paths = [@config_path]
      @diagnostics = []
      config = PocPaths.structured(@config_path)
      schema = Pathname.new(__dir__).join("../../schemas/poc-project.schema.json")
      SchemaValidator.validate!(config, SchemaValidator.load(schema))
      %w[requirements capabilities elements].each do |key|
        ids = config.fetch(key).map { |row| row.fetch("id") }
        raise ValidationError, "duplicate #{key} identity" unless ids.uniq.length == ids.length
      end
      sources = config.fetch("sources").transform_values { |value| source(value) }
      specification = PocPaths.read(sources.fetch("specification"))
      tasks = PocPaths.read(sources.fetch("tasks"))
      definition_rows = specification.scan(/^\s*[-*]\s+\*\*([A-Z][A-Z0-9]*-\d+[a-z]?)(?:\s+[^*]+)?\*\*\s*:\s*(.*)$/)
      raise ValidationError, "duplicate native requirement identity" unless definition_rows.map(&:first).uniq.length == definition_rows.length
      definitions = definition_rows.to_h
      rows = tasks.scan(/^\s*-\s+\[([xX ])\]\s+(T\d+[a-z]?)\b/)
      task_ids = rows.map(&:last)
      raise ValidationError, "duplicate native task identity" unless task_ids.uniq.length == task_ids.length
      checked = rows.to_h { |mark, id| [id, mark.downcase == "x"] }
      requirements = config.fetch("requirements").map do |row|
        weight = row.fetch("weight", 1)
        raise ValidationError, "requirement weight must be finite and positive" unless weight.finite? && weight > 0
        id = row.fetch("id")
        known = definitions.key?(id)
        @diagnostics << "#{id}: not defined in selected native specification" unless known
        missing = row.fetch("task_ids").reject { |task| checked.key?(task) }
        missing.each { |task| @diagnostics << "#{id}: unknown native task #{task}" }
        implementation = if !known || !missing.empty? || row.fetch("task_ids").empty?
          "UNKNOWN"
        elsif row.fetch("task_ids").all? { |task| checked.fetch(task) }
          "COMPLETE"
        elsif row.fetch("task_ids").none? { |task| checked.fetch(task) }
          "NOT_STARTED"
        else
          "IN_PROGRESS"
        end
        records = row.fetch("evidence_refs").map do |reference|
          evidence(reference, id)
        end.compact
        row.merge("native_definition_known" => known, "title" => row.fetch("title", definitions.fetch(id, id)), "scope_state" => row.fetch("scope_state", "ACTIVE"),
          "weight" => row.fetch("weight", 1), "dependencies" => row.fetch("depends_on", []),
          "applicable_lifecycle_stages" => %w[implementation verification acceptance], "evidence_records" => records,
          "lifecycle" => {"implementation" => {"status" => implementation, "evidence" => row.fetch("task_ids")},
            "verification" => {"status" => "UNKNOWN", "evidence" => []}, "acceptance" => {"status" => "UNKNOWN", "evidence" => []}})
      end
      known_ids = requirements.map { |row| row.fetch("id") }
      (config.fetch("elements") + config.fetch("capabilities")).each do |row|
        (row.fetch("requirement_ids") - known_ids).each { |id| @diagnostics << "#{row.fetch('id')}: unmapped requirement #{id}" }
      end
      capability_ids = config.fetch("capabilities").map { |row| row.fetch("id") }
      requirements.each do |row|
        (row.fetch("capability_ids") - capability_ids).each { |id| @diagnostics << "#{row.fetch('id')}: unknown capability #{id}" }
      end
      gaps = config.fetch("gaps", []).map { |row| row.merge("reference" => public_reference(row.fetch("reference"))) }
      attention = config.fetch("attention", []).map { |row| row.merge("reference" => public_reference(row.fetch("reference"))) }
      {"project" => config.fetch("project"), "scope_version" => config.fetch("scope_version", "poc-v1"),
        "requirements" => requirements, "capabilities" => config.fetch("capabilities"), "elements" => config.fetch("elements"),
        "gaps" => gaps, "attention" => attention, "diagnostics" => @diagnostics,
        "source_paths" => @source_paths.uniq, "source_root" => @root}
    rescue Errno::ENOENT, ArgumentError, EncodingError
      raise ValidationError, "required project input could not be read safely"
    end

    private

    def source(reference)
      path = PocPaths.resolve(@root, reference)
      @source_paths << path
      path
    end

    def public_reference(reference)
      source(reference)
      reference
    end

    def evidence(reference, requirement_id)
      path = PocPaths.resolve(@root, reference, missing: true)
      unless path.file?
        @diagnostics << "#{requirement_id}: referenced evidence is missing"
        return nil
      end
      @source_paths << path
      unless %w[.json .yaml .yml].include?(path.extname)
        @diagnostics << "#{requirement_id}: narrative evidence is linked, not interpreted as approval"
        return nil
      end
      record = PocPaths.structured(path)
      if record["kind"] == "human_decision" && record.key?("human_reference") && !PocPaths.native_reference?(record["human_reference"])
        @diagnostics << "#{requirement_id}: human decision reference is blank or invalid"
        return nil
      end
      SchemaValidator.validate!(record, SchemaValidator.load(Pathname.new(__dir__).join("../../schemas/poc-project.schema.json")).fetch("definitions").fetch("evidence"))
      results = record.fetch("kind") == "qualification" ? %w[PASS FAIL] : %w[ACCEPTED REJECTED]
      raise ValidationError, "evidence result does not match its kind" unless results.include?(record.fetch("result"))
      valid = record.fetch("artifacts").all? do |artifact|
        target = source(artifact.fetch("path"))
        Digest::SHA256.file(target).hexdigest == artifact.fetch("sha256")
      end
      scope = record.fetch("scope_hashes", {})
      scope_valid = !scope.empty? && scope.all? { |relative, digest| Digest::SHA256.file(source(relative)).hexdigest == digest }
      record.merge("reference" => reference, "artifacts_valid" => valid, "scope_hashes_valid" => scope_valid)
    rescue ValidationError => error
      # Unsafe references are fatal before reading; malformed evidence is unknown.
      raise if error.message.match?(/private|escaping|symlink|escapes/)
      @diagnostics << "#{requirement_id}: structured evidence is invalid or unavailable"
      nil
    end
  end
end
