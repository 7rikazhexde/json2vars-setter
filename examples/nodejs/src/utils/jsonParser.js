const fs = require('fs');
const { paths } = require('../config');

/**
 * JSONファイルを解析する
 * @param {string} filePath - 解析するJSONファイルのパス
 * @param {boolean} silent - エラーメッセージを抑制するかどうか
 * @returns {object|null} 解析されたJSONオブジェクト、またはエラー時はnull
 */
function parseConfigJson(filePath = paths.matrixConfig, silent = false) {
  try {
    // パスが存在するか確認
    if (!fs.existsSync(filePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    const jsonContent = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(jsonContent);
  } catch (error) {
    if (!silent) {
      console.error('Error reading or parsing JSON:', error.message);
    }
    return null;
  }
}

module.exports = {
  parseConfigJson,
};
