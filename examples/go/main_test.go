package main

import (
	"testing"
)

func TestMain(t *testing.T) {
	// mainパッケージの機能をテスト
	t.Run("main function can be executed", func(t *testing.T) {
		// エラーが発生しないことを確認
		main()
	})
}
