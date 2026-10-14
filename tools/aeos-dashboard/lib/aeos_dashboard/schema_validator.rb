# frozen_string_literal: true

require "json"

module AeosDashboard
  module SchemaValidator
    module_function

    def load(path)
      JSON.parse(File.read(path.to_s))
    end

    def validate!(data, schema)
      errors = []
      validate_node(data, schema, "$", schema, errors)
      return data if errors.empty?

      raise ValidationError.new(
        "schema validation failed: #{errors.join('; ')}",
        errors: errors
      )
    end

    def validate_node(value, schema, path, root, errors)
      schema = resolve_ref(schema, root)
      validate_type(value, schema["type"], path, errors) if schema["type"]
      return if errors.any? { |error| error.start_with?("#{path} must be") }

      validate_enum(value, schema["enum"], path, errors) if schema["enum"]
      validate_pattern(value, schema["pattern"], path, errors) if schema["pattern"] && value.is_a?(String)
      validate_minimum(value, schema["minimum"], path, errors) if schema.key?("minimum") && value.is_a?(Numeric)
      validate_maximum(value, schema["maximum"], path, errors) if schema.key?("maximum") && value.is_a?(Numeric)

      case value
      when Hash
        validate_object(value, schema, path, root, errors)
      when Array
        validate_array(value, schema, path, root, errors)
      end
    end

    def resolve_ref(schema, root)
      reference = schema["$ref"]
      return schema unless reference
      unless reference.start_with?("#/")
        raise ValidationError, "unsupported schema reference #{reference}"
      end

      reference.delete_prefix("#/").split("/").reduce(root) { |node, key| node.fetch(key) }
    end

    def validate_type(value, expected, path, errors)
      matches = Array(expected).any? do |candidate|
        case candidate
        when "object" then value.is_a?(Hash)
        when "array" then value.is_a?(Array)
        when "string" then value.is_a?(String)
        when "number" then value.is_a?(Numeric)
        when "integer" then value.is_a?(Integer)
        when "boolean" then value == true || value == false
        when "null" then value.nil?
        else false
        end
      end
      errors << "#{path} must be #{Array(expected).join(' or ')}" unless matches
    end

    def validate_enum(value, allowed, path, errors)
      errors << "#{path} must be one of #{allowed.join(', ')}" unless allowed.include?(value)
    end

    def validate_pattern(value, pattern, path, errors)
      errors << "#{path} must match #{pattern}" unless Regexp.new(pattern).match?(value)
    end

    def validate_minimum(value, minimum, path, errors)
      errors << "#{path} must be >= #{minimum}" if value < minimum
    end

    def validate_maximum(value, maximum, path, errors)
      errors << "#{path} must be <= #{maximum}" if value > maximum
    end

    def validate_object(value, schema, path, root, errors)
      Array(schema["required"]).each do |key|
        errors << "#{path}.#{key} is required" unless value.key?(key)
      end

      properties = schema.fetch("properties", {})
      value.each do |key, child|
        child_schema = properties[key]
        if child_schema
          validate_node(child, child_schema, "#{path}.#{key}", root, errors)
        elsif schema["additionalProperties"] == false
          errors << "#{path}.#{key} is not allowed"
        elsif schema["additionalProperties"].is_a?(Hash)
          validate_node(child, schema["additionalProperties"], "#{path}.#{key}", root, errors)
        end
      end
    end

    def validate_array(value, schema, path, root, errors)
      minimum = schema["minItems"]
      errors << "#{path} must contain at least #{minimum} items" if minimum && value.length < minimum
      maximum = schema["maxItems"]
      errors << "#{path} must contain at most #{maximum} items" if maximum && value.length > maximum
      errors << "#{path} must contain unique items" if schema["uniqueItems"] && value.uniq.length != value.length
      return unless schema["items"]

      value.each_with_index do |child, index|
        validate_node(child, schema["items"], "#{path}[#{index}]", root, errors)
      end
    end
  end
end
