use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Debug, Serialize, Deserialize)]
pub struct MatrixConfig {
    pub os: Vec<String>,
    pub versions: std::collections::HashMap<String, Vec<String>>,
    pub ghpages_branch: String,
}

pub fn parse_config<P: AsRef<Path>>(file_path: P, silent: bool) -> Option<MatrixConfig> {
    match fs::read_to_string(file_path) {
        Ok(contents) => match serde_json::from_str(&contents) {
            Ok(config) => Some(config),
            Err(e) => {
                if !silent {
                    eprintln!("Error parsing JSON: {}", e);
                }
                None
            }
        },
        Err(e) => {
            if !silent {
                eprintln!("Error reading file: {}", e);
            }
            None
        }
    }
}
