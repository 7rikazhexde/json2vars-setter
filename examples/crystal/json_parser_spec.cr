# Spec for json_parser.cr using Crystal's built-in `spec` framework. A failing
# expectation exits non-zero, which fails the CI matrix leg.

require "spec"
require "./json_parser"

SAMPLE = <<-JSON
{
  "os": ["ubuntu-latest", "macos-latest"],
  "versions": { "crystal": ["1.19.2", "1.20.2"] },
  "ghpages_branch": "ghgapes"
}
JSON

describe "parse_config" do
  it "parses the matrix configuration" do
    parsed = parse_config(SAMPLE)
    parsed.should_not be_nil
    config = parsed.not_nil!

    os = config["os"].as_a.map(&.as_s)
    os.size.should eq(2)
    os.should contain("ubuntu-latest")
    os.should contain("macos-latest")

    # Assert structure, not specific version values, so bumping the matrix
    # versions never requires editing this spec.
    versions = config["versions"]["crystal"].as_a.map(&.as_s)
    versions.empty?.should be_false
    versions.all? { |v| !v.empty? }.should be_true

    config["ghpages_branch"].as_s.should eq("ghgapes")
  end

  it "returns nil for invalid JSON" do
    parse_config("not json", silent: true).should be_nil
  end
end
