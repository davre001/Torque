// Managed commands only; repository npm lifecycle scripts are not invoked.
const fs = require('node:fs');
const { spawnSync } = require('node:child_process');
const config = JSON.parse(fs.readFileSync('/acceptance/config.json', 'utf8'));
// Keep package caches and generated configuration in the bounded writable tmpfs.
fs.cpSync('/workspace', '/tmp/project', {recursive:true, filter:p=>!p.replaceAll('\\', '/').split('/').includes('node_modules')});
const packageRoot = config.package_root || '';
for (const directory of new Set(['', packageRoot])) {
  const source = '/workspace/'+(directory ? directory+'/' : '')+'node_modules';
  const destination = '/tmp/project/'+(directory ? directory+'/' : '')+'node_modules';
  if (fs.existsSync(source)) {
    fs.mkdirSync(destination, {recursive:true});
    for (const name of fs.readdirSync(source)) fs.symlinkSync(source+'/'+name, destination+'/'+name, fs.statSync(source+'/'+name).isDirectory() ? 'junction' : 'file');
  }
}
process.chdir('/tmp/project'+(packageRoot ? '/'+packageRoot : ''));
const start = Date.now();
const tests = config.test_files.filter(p => /\.(?:test|spec)\.[cm]?[jt]sx?$/.test(p)).map(p=>packageRoot ? p.slice(packageRoot.length+1) : p);
let command, args;
if (config.engine === 'vitest') {
  command = './node_modules/.bin/vitest'; args = ['run', '--reporter=json', '--outputFile=/tmp/results.json', ...tests];
} else if (config.engine === 'jest') {
  command = './node_modules/.bin/jest'; args = ['--runInBand', '--json', '--outputFile=/tmp/results.json', ...tests];
} else {
  command = 'node'; args = ['--test', '--test-reporter=tap', ...tests];
}
const result = tests.length ? spawnSync(command, args, {encoding:'utf8', maxBuffer:100000, timeout:110000}) : {status:125, stderr:'Select at least one .test or .spec file'};
const text = ((result.stdout || '') + (result.stderr || '')).slice(-20000);
let valid = false;
try {
  if (config.engine === 'node') {
    const names = [...text.matchAll(/^\s*# Subtest: (.+)$/gm)].map(match=>match[1].replaceAll('\\', '/'));
    const named = names.some(name=>!tests.some(file=>name===file || name.endsWith('/'+file)));
    valid = named && /^# tests [1-9][0-9]*$/m.test(text) && /^# (?:pass|fail) [1-9][0-9]*$/m.test(text);
  }
  else {
    if (fs.statSync('/tmp/results.json').size > 100000) throw Error();
    const report = JSON.parse(fs.readFileSync('/tmp/results.json','utf8'));
    valid = report.numTotalTests > 0 && report.numPassedTests + report.numFailedTests > 0;
  }
} catch {}
const passed = result.status === 0 && valid;
console.log(text.replaceAll('TORQUE_TEST_RESULT=', 'TEST_LOG='));
console.log('TORQUE_TEST_RESULT=' + JSON.stringify({assertions_passed:Number(passed), failure_kind:passed ? null : valid ? 'assertion' : 'infrastructure', cases:[{name:'Frozen repository test suite',passed,duration_ms:Date.now()-start,stdout:text.slice(-4000),stderr:passed?'':text.slice(-4000),stacktrace:passed?'':text.slice(-6000)}]}));
process.exit(passed ? 0 : result.status || 125);
