# frozen_string_literal: true

module AeosDashboard
  class Error < StandardError; end

  class ValidationError < Error
    attr_reader :errors

    def initialize(message, errors: [])
      super(message)
      @errors = errors
    end
  end

  class GenerationError < Error; end
end
