# frozen_string_literal: true

require "date"

module AeosDashboard
  module Timestamp
    PATTERN = /\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}\z/.freeze

    module_function

    def validate!(value)
      if value.is_a?(String) && PATTERN.match?(value)
        date = value[0, 10].split("-").map(&:to_i)
        hour, minute, second = value[11, 8].split(":").map(&:to_i)
        offset_hour, offset_minute = value[20, 5].split(":").map(&:to_i)
        return value if Date.valid_date?(*date) && hour < 24 && minute < 60 && second < 60 && offset_hour < 24 && offset_minute < 60
      end

      raise ValidationError, "rendered timestamp must be a valid YYYY-MM-DDTHH:MM:SS±HH:MM"
    end
  end
end
