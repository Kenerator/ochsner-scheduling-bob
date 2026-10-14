# frozen_string_literal: true

require "find"

module AeosDashboard
  # A manifest is a closure/digest check, not a signature or release approval.
  module PocBundle
    module_function

    def verify(root)
      root = Pathname.new(root).realpath
      manifest_path = root.join("export-manifest.json")
      raise ValidationError, "bundle manifest must be a regular file" if manifest_path.symlink? || !manifest_path.file?
      manifest = PocPaths.structured(manifest_path)
      expected_keys = %w[schema_version mechanism_version source_revision working_tree_state files notices]
      raise ValidationError, "unsupported bundle manifest" unless manifest.keys.sort == expected_keys.sort && manifest["schema_version"] == 1 && manifest["mechanism_version"] == "1.0.0"
      raise ValidationError, "invalid source identity" unless manifest["source_revision"].is_a?(String) && manifest["source_revision"].match?(/\A[0-9a-f]{40}\z/)
      raise ValidationError, "invalid source state" unless %w[CLEAN DIRTY].include?(manifest["working_tree_state"])
      raise ValidationError, "missing applicable notice" unless manifest["notices"] == ["POC-EXPORT-NOTICE.md"]
      rows = manifest["files"]
      raise ValidationError, "invalid bundle files" unless rows.is_a?(Array) && rows.all? { |row| row.is_a?(Hash) && row.keys.sort == %w[path sha256] }
      raise ValidationError, "bundle file allowlist mismatch" unless rows.map { |row| row["path"] } == PocRuntime::FILES.sort
      expected = PocRuntime::FILES + ["export-manifest.json"]
      actual = []
      Find.find(root.to_s) do |name|
        path = Pathname.new(name)
        raise ValidationError, "bundle symlink rejected" if path.symlink?
        next if path.directory?
        raise ValidationError, "bundle contains nonregular content" unless path.file?
        actual << path.relative_path_from(root).to_s
      end
      raise ValidationError, "undeclared bundle content" unless actual.sort == expected.sort
      rows.each do |row|
        path = PocPaths.resolve(root, row.fetch("path"))
        digest = row.fetch("sha256")
        raise ValidationError, "bundle digest mismatch" unless digest.is_a?(String) && digest.match?(/\A[0-9a-f]{64}\z/) && Digest::SHA256.file(path).hexdigest == digest
      end
      manifest
    end
  end
end
