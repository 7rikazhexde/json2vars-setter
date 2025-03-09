# frozen_string_literal: true

require 'spec_helper'

RSpec.describe JsonVarsSetter::JsonParser do
  let(:config_path) { File.expand_path('../../../.github/json2vars-setter/ruby_project_matrix.json', __dir__) }

  describe '.parse_config' do
    it 'JSONファイルを解析できること' do
      result = described_class.parse_config(config_path)
      expect(result).to be_a(Hash)
    end

    it '正しくJSONファイルを解析できること' do
      result = described_class.parse_config(config_path)

      expect(result).to be_a(Hash)
      expect(result['os']).to include('ubuntu-latest', 'windows-latest', 'macos-latest')
      expect(result['versions']['ruby']).to include(
            "3.0.6",
            "3.1.6",
            "3.2.6",
            "3.3.6",
            "3.4.0",
            "3.4.1",
            "3.3.7",
            "3.2.7",
            "3.4.2"
            )
      expect(result['ghpages_branch']).to eq('ghgapes')
    end

    it '存在しないファイルの場合はnilを返すこと' do
      result = described_class.parse_config('non-existent.json', silent: true)
      expect(result).to be_nil
    end
  end
end
