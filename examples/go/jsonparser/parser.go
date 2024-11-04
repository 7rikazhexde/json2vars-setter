// jsonparser/parser.go
package jsonparser

import (
	"encoding/json"
	"fmt"
	"os"
)

// MatrixConfig は設定JSONの構造を定義
type MatrixConfig struct {
	OS            []string            `json:"os"`
	Versions      map[string][]string `json:"versions"`
	GhPagesBranch string              `json:"ghpages_branch"`
}

// ParseConfig はJSONファイルを読み込んで解析する
func ParseConfig(filePath string, silent bool) (*MatrixConfig, error) {
	data, err := os.ReadFile(filePath)
	if err != nil {
		if !silent {
			fmt.Printf("Error reading JSON file: %v\n", err)
		}
		return nil, err
	}

	var config MatrixConfig
	if err := json.Unmarshal(data, &config); err != nil {
		if !silent {
			fmt.Printf("Error parsing JSON: %v\n", err)
		}
		return nil, err
	}

	return &config, nil
}
