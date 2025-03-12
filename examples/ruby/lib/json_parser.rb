# frozen_string_literal: true

require 'json'

module JsonVarsSetter
  class JsonParser
    def self.parse_config(file_path, silent: false)
      JSON.parse(File.read(file_path))
    rescue StandardError => e
      puts "Error reading or parsing JSON: #{e.message}" unless silent
      nil
    end
  end
end

# スクリプトが直接実行された場合の処理
if __FILE__ == $0
  config_path = File.expand_path('../ruby_project_matrix.json', __dir__)
  result = JsonVarsSetter::JsonParser.parse_config(config_path)
  puts JSON.pretty_generate(result) if result
end
