use json2vars_setter_rs::parse_config;
use std::path::PathBuf;

fn main() {
    let config_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join(".github")
        .join("json2vars-setter")
        .join("rust_project_matrix.json");

    #[allow(clippy::needless_borrows_for_generic_args)]
    match parse_config(&config_path, false) {
        Some(config) => {
            println!("{}", serde_json::to_string_pretty(&config).unwrap());
        }
        None => {
            std::process::exit(1);
        }
    }
}
