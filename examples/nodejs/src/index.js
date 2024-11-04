const { parseConfigJson } = require('./utils/jsonParser');
const { paths } = require('./config');

function main() {
  const filePath = process.argv[2] || paths.matrixConfig;
  const result = parseConfigJson(filePath);

  if (result) {
    console.log(JSON.stringify(result, null, 2));
    return 0;
  }

  return 1;
}

if (require.main === module) {
  process.exit(main());
}

module.exports = { main };
