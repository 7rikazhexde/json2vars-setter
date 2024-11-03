// jsonparser/parser_test.go
package jsonparser

import (
	"path/filepath"
	"reflect"
	"runtime"
	"testing"
)

func TestParseConfig(t *testing.T) {
	_, filename, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("Error getting current file path")
	}

	configPath := filepath.Join(filepath.Dir(filename), "../../../.github/workflows/go_project_matrix.json")

	tests := []struct {
		name    string
		path    string
		silent  bool
		wantErr bool
		check   func(*MatrixConfig) bool
	}{
		{
			name:    "valid config file",
			path:    configPath,
			silent:  false,
			wantErr: false,
			check: func(c *MatrixConfig) bool {
				// JSONファイルの実際の値と一致するように更新
				expectedOS := []string{"ubuntu-latest", "windows-latest", "macos-latest"}
				expectedVersions := []string{"1.23.0", "1.23.1", "1.23.2"}

				if !reflect.DeepEqual(c.OS, expectedOS) {
					t.Errorf("Expected OS %v, got %v", expectedOS, c.OS)
					return false
				}
				if versions, ok := c.Versions["go"]; !ok || !reflect.DeepEqual(versions, expectedVersions) {
					t.Errorf("Expected versions %v, got %v", expectedVersions, versions)
					return false
				}
				if c.GhPagesBranch != "ghgapes" {
					t.Errorf("Expected ghpages_branch 'ghgapes', got %v", c.GhPagesBranch)
					return false
				}
				return true
			},
		},
		{
			name:    "non-existent file",
			path:    "non-existent.json",
			silent:  true,
			wantErr: true,
			check:   nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			config, err := ParseConfig(tt.path, tt.silent)
			if (err != nil) != tt.wantErr {
				t.Errorf("ParseConfig() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && !tt.check(config) {
				t.Error("ParseConfig() returned unexpected configuration")
			}
		})
	}
}
