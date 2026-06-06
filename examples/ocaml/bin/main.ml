(* Minimal JSON configuration parser used to demonstrate consuming the
   json2vars-setter matrix file in an OCaml project. Parsing uses the Yojson
   library (OCaml has no JSON parser in its standard library); the checks are
   plain assertions that exit non-zero on failure, so no test framework is
   required. *)

let parse_config ?(silent = false) (contents : string) : Yojson.Safe.t option =
  try Some (Yojson.Safe.from_string contents)
  with Yojson.Json_error msg ->
    if not silent then prerr_endline ("Error parsing JSON: " ^ msg);
    None

let sample =
  {|
{
  "os": ["ubuntu-latest", "macos-latest"],
  "versions": { "ocaml": ["5.2.1", "5.3.0"] },
  "ghpages_branch": "ghgapes"
}
|}

let failures = ref 0

let check cond msg =
  if not cond then begin
    incr failures;
    Printf.printf "FAIL: %s\n" msg
  end

let () =
  (match parse_config sample with
   | None -> check false "the sample matrix should parse"
   | Some json ->
     let open Yojson.Safe.Util in
     let os = json |> member "os" |> to_list |> List.map to_string in
     check (List.length os = 2) "os should have 2 entries";
     check (List.mem "ubuntu-latest" os) "os should contain ubuntu-latest";
     check (List.mem "macos-latest" os) "os should contain macos-latest";
     (* Assert structure, not specific version values, so bumping the matrix
        versions never requires editing this program. *)
     let versions =
       json |> member "versions" |> member "ocaml" |> to_list |> List.map to_string
     in
     check (versions <> []) "ocaml versions should be a non-empty list";
     check
       (List.for_all (fun v -> String.length v > 0) versions)
       "each ocaml version should be a non-empty string";
     check
       (to_string (member "ghpages_branch" json) = "ghgapes")
       "ghpages_branch should match");
  check
    (parse_config ~silent:true "not json" = None)
    "invalid JSON should fail to parse";
  if !failures > 0 then exit 1;
  print_endline "All tests passed"
