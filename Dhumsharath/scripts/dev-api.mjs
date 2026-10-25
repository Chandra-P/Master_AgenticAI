import { spawnSync } from 'node:child_process';

const packageManager = process.env.npm_execpath;
if (!packageManager) {
  console.error('Start the API with pnpm run dev.');
  process.exit(1);
}

for (const task of ['build', 'start']) {
  // Invoke the active pnpm JavaScript entry point through Node so paths with
  // spaces and Windows .cmd wrappers do not require shell-specific quoting.
  const result = spawnSync(process.execPath, [packageManager, 'run', task], {
    stdio: 'inherit',
    env: { ...process.env, NODE_ENV: 'development', PORT: process.env.PORT ?? '3001' },
  });
  if (result.error) console.error(result.error.message);
  if (result.status !== 0) process.exit(result.status ?? 1);
}
