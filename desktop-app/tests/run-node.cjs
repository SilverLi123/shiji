const { readdirSync } = require('node:fs');
const { join } = require('node:path');
const { spawnSync } = require('node:child_process');
const tests = readdirSync(__dirname).filter(name => /^test_.*\.js$/.test(name)).sort();
for (const test of tests) {
  const result = spawnSync(process.execPath, [join(__dirname, test)], { stdio: 'inherit' });
  if (result.error) { console.error(result.error.message); process.exit(1); }
  if (result.status !== 0) process.exit(result.status || 1);
}
console.log(`PASS: ${tests.length} Node groups`);
