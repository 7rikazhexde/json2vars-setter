# Minimal JSON configuration parser used to demonstrate consuming the
# json2vars-setter matrix file in a Julia project. Parsing uses the JSON.jl
# package declared in Project.toml.

using JSON

"""
    parse_config(contents; silent=false)

Parse `contents` (JSON text) into a `Dict`. Returns `nothing` on parse failure.
"""
function parse_config(contents::AbstractString; silent::Bool = false)
    try
        return JSON.parse(contents)
    catch err
        silent || println(stderr, "Error parsing JSON: ", err)
        return nothing
    end
end

if abspath(PROGRAM_FILE) == @__FILE__
    result = parse_config(read("julia_project_matrix.json", String))
    result === nothing || println(JSON.json(result, 2))
end
