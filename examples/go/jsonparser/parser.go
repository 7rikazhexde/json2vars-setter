// jsonparser/parser.go
package jsonparser

import (
	"encoding/json"
	"fmt"
	"os"
)

// MatrixConfig は設定JSONの構造を定義します
type MatrixConfig struct {
	OS            []string            `json:"os"`
	Versions      map[string][]string `json:"versions"`
	GhPagesBranch string              `json:"ghpages_branch"`
}

// ParseConfig はJSONファイルを読み込んで解析します
func ParseConfig(filePath string, silent bool) (*MatrixConfig, error) {
	data, err := os.ReadFile(filePath)
	if err != nil {
		if !silent {
			fmt.Printf("Error reading config file: %v\n", err)
		}
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var config MatrixConfig
	if err := json.Unmarshal(data, &config); err != nil {
		if !silent {
			fmt.Printf("Error parsing JSON: %v\n", err)
		}
		return nil, fmt.Errorf("failed to parse JSON: %w", err)
	}

	return &config, nil
}
