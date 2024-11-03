// main.go
package main

import (
	"encoding/json"
	"fmt"
	"json2vars-setter-example/jsonparser"
	"path/filepath"
	"runtime"
)

func main() {
	_, filename, _, ok := runtime.Caller(0)
	if !ok {
		fmt.Println("Error getting current file path")
		return
	}

	// プロジェクトルートからの相対パスでJSONファイルを指定
	configPath := filepath.Join(filepath.Dir(filename), "../../.github/workflows/go_project_matrix.json")

	config, err := jsonparser.ParseConfig(configPath, false)
	if err != nil {
		return
	}

	// 整形してJSON出力
	output, _ := json.MarshalIndent(config, "", "  ")
	fmt.Println(string(output))
}
