import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(new URL('../artifacts/dhumsharath/package.json', import.meta.url));
const { loadConfigFromFile } = await import(pathToFileURL(require.resolve('vite')).href);

async function withEnv(values, run) {
  const names = ['PORT', 'BASE_PATH', 'REPL_ID', 'NODE_ENV'];
  const previous = Object.fromEntries(names.map(name => [name, process.env[name]]));
  try {
    for (const name of names) {
      if (values[name] === undefined) delete process.env[name];
      else process.env[name] = values[name];
    }
    await run();
  } finally {
    for (const name of names) {
      if (previous[name] === undefined) delete process.env[name];
      else process.env[name] = previous[name];
    }
  }
}

for (const [artifact, defaultPort] of [['dhumsharath', 5173], ['mockup-sandbox', 5174]]) {
  const configFile = fileURLToPath(new URL(`../artifacts/${artifact}/vite.config.ts`, import.meta.url));
  const load = () => loadConfigFromFile({ command: 'build', mode: 'production' }, configFile, undefined, 'silent');

  test(`${artifact} config loads without hosting variables`, () => withEnv({}, async () => {
    const { config } = await load();
    assert.equal(config.base, '/');
    assert.equal(config.server.port, defaultPort);
    assert.equal(config.preview.port, defaultPort);
  }));

  test(`${artifact} config preserves explicit hosting overrides`, () => withEnv({ PORT: '8123', BASE_PATH: '/hosted/' }, async () => {
    const { config } = await load();
    assert.equal(config.base, '/hosted/');
    assert.equal(config.server.port, 8123);
    assert.equal(config.preview.port, 8123);
  }));

  test(`${artifact} config rejects invalid explicit ports`, async () => {
    for (const PORT of ['invalid', '0', '-1', '65536', '1.5', 'Infinity', '']) {
      await withEnv({ PORT, BASE_PATH: '/' }, () => assert.rejects(load, /Invalid PORT value/));
    }
  });

  test(`${artifact} config still rejects an empty explicit base path`, () => withEnv({ BASE_PATH: '' }, () => assert.rejects(load, /BASE_PATH/)));
}
