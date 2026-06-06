# Minimal JSON configuration parser used to demonstrate consuming the
# json2vars-setter matrix file in a Crystal project. It uses only Crystal's
# standard-library `JSON` module, so no shard dependencies are required.

require "json"

# Parse *contents* (JSON text) into a `JSON::Any`. Returns `nil` on parse failure.
def parse_config(contents : String, silent : Bool = false) : JSON::Any?
  JSON.parse(contents)
rescue ex : JSON::ParseException
  STDERR.puts("Error parsing JSON: #{ex.message}") unless silent
  nil
end
