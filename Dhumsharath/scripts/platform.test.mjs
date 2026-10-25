import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, readFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const guard = fileURLToPath(new URL('./preinstall.mjs', import.meta.url));
const dev = fileURLToPath(new URL('./dev-api.mjs', import.meta.url));

test('package lifecycle scripts use the portable launchers', () => {
  const root = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
  const api = JSON.parse(readFileSync(new URL('../artifacts/api-server/package.json', import.meta.url), 'utf8'));
  assert.equal(root.scripts.preinstall, 'node ./scripts/preinstall.mjs');
  assert.equal(api.scripts.dev, 'node ../../scripts/dev-api.mjs');
});

function fixture(run) {
  const dir = mkdtempSync(join(tmpdir(), 'dhum-platform-'));
  try { run(dir); } finally { rmSync(dir, { recursive: true, force: true }); }
}

test('preinstall accepts pnpm and removes competing lockfiles without a shell', () => fixture(dir => {
  for (const name of ['package-lock.json', 'yarn.lock', 'pnpm-lock.yaml']) writeFileSync(join(dir, name), 'fixture');
  const result = spawnSync(process.execPath, [guard], { cwd: dir, env: { ...process.env, npm_config_user_agent: 'pnpm/10.0.0 npm/? node/v24' } });
  assert.equal(result.status, 0, result.stderr.toString());
  assert.equal(existsSync(join(dir, 'package-lock.json')), false);
  assert.equal(existsSync(join(dir, 'yarn.lock')), false);
  assert.equal(existsSync(join(dir, 'pnpm-lock.yaml')), true);
}));

test('preinstall rejects other package managers and preserves their lockfiles', () => fixture(dir => {
  writeFileSync(join(dir, 'package-lock.json'), 'fixture');
  for (const agent of ['npm/11.0.0', '']) {
    const result = spawnSync(process.execPath, [guard], { cwd: dir, env: { ...process.env, npm_config_user_agent: agent } });
    assert.equal(result.status, 1);
    assert.match(result.stderr.toString(), /Use pnpm instead/);
    assert.equal(existsSync(join(dir, 'package-lock.json')), true);
  }
}));

function runDev(dir, failBuild, port) {
  // A path with spaces exercises the Windows command-line boundary.
  const cli = join(dir, 'fake pnpm.cjs');
  writeFileSync(cli, `const fs = require('node:fs'); fs.appendFileSync('calls.jsonl', JSON.stringify({ args: process.argv.slice(2), env: process.env.NODE_ENV, port: process.env.PORT }) + '\\n'); if (${failBuild} && process.argv[3] === 'build') process.exit(7);`);
  const env = { ...process.env, npm_execpath: cli, NODE_ENV: 'production' };
  delete env.PORT;
  if (port !== undefined) env.PORT = port;
  const result = spawnSync(process.execPath, [dev], { cwd: dir, env });
  const calls = existsSync(join(dir, 'calls.jsonl')) ? readFileSync(join(dir, 'calls.jsonl'), 'utf8').trim().split('\n').map(JSON.parse) : [];
  return { result, calls };
}

test('API dev builds then starts with development environment', () => fixture(dir => {
  const { result, calls } = runDev(dir, false);
  assert.equal(result.status, 0, result.stderr.toString());
  assert.deepEqual(calls, [{ args: ['run', 'build'], env: 'development', port: '3001' }, { args: ['run', 'start'], env: 'development', port: '3001' }]);
}));

test('API dev preserves an explicit port', () => fixture(dir => {
  const { result, calls } = runDev(dir, false, '8123');
  assert.equal(result.status, 0, result.stderr.toString());
  assert.deepEqual(calls.map(call => call.port), ['8123', '8123']);
}));

test('API dev propagates a failed build without starting the server', () => fixture(dir => {
  const { result, calls } = runDev(dir, true);
  assert.equal(result.status, 7);
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0].args, ['run', 'build']);
}));

test('API dev explains how to launch when package-manager context is missing', () => fixture(dir => {
  const env = { ...process.env };
  delete env.npm_execpath;
  const result = spawnSync(process.execPath, [dev], { cwd: dir, env });
  assert.equal(result.status, 1);
  assert.match(result.stderr.toString(), /pnpm run dev/);
}));
