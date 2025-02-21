use json2vars_setter_rs::parse_config;
use std::path::PathBuf;

#[test]
fn test_parse_valid_config() {
    let config_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join(".github")
        .join("workflows")
        .join("rust_project_matrix.json");

    #[allow(clippy::needless_borrows_for_generic_args)]
    let config = parse_config(&config_path, false).expect("Failed to parse config");

    assert!(config.os.contains(&"ubuntu-latest".to_string()));
    assert!(config.os.contains(&"windows-latest".to_string()));
    assert!(config.os.contains(&"macos-latest".to_string()));

    let rust_versions = config.versions.get("rust").expect("No Rust versions found");
    assert!(rust_versions.contains(&"1.80.0".to_string()));
    assert!(rust_versions.contains(&"1.81.0".to_string()));
    assert!(rust_versions.contains(&"1.82.0".to_string()));
    assert!(rust_versions.contains(&"1.83.0".to_string()));
    assert!(rust_versions.contains(&"1.84.0".to_string()));
    assert!(rust_versions.contains(&"1.84.1".to_string()));
    assert!(rust_versions.contains(&"1.85.0".to_string()));
    assert!(rust_versions.contains(&"stable".to_string()));

    assert_eq!(config.ghpages_branch, "ghgapes");
}
