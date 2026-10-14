import { test as base, expect } from '@playwright/test';
import { spawn } from 'node:child_process';
import { resolve } from 'node:path';

// Every test/retry owns a fresh PostgreSQL database and server process.
export const test = base.extend<{ crmBackend: void }>({
  crmBackend: [async ({ request }, use) => {
    const ready = 'http://127.0.0.1:18000/api/ready';
    const occupied = await request.get(ready, { timeout: 500 }).catch(() => null);
    if (occupied) throw new Error('Port 18000 is already in use. Stop the test server before E2E checks.');
    const cwd = resolve(process.cwd(), '../backend');
    const child = spawn(resolve(cwd, '.venv/bin/python'), ['tests/tools/e2e_server.py'], {
      cwd, env: { ...process.env, PYTHONPATH: '.', PYTHONUNBUFFERED: '1' }, stdio: 'inherit',
    });
    let startError: Error | undefined;
    child.on('error', error => { startError = error; });
    try {
      const deadline = Date.now() + 60_000;
      let started = false;
      while (Date.now() < deadline) {
        if (startError) throw startError;
        if (child.exitCode !== null) throw new Error(`Isolated CRM server exited: ${child.exitCode}`);
        const response = await request.get(ready, { timeout: 500 }).catch(() => null);
        if (response?.ok()) { started = true; break; }
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      if (!started) throw new Error('Isolated CRM server did not become ready.');
      await use();
    } finally {
      if (child.exitCode === null && child.pid) {
        const exited = new Promise<void>(resolve => child.once('exit', () => resolve()));
        child.kill('SIGTERM');
        const timeout = setTimeout(() => child.kill('SIGKILL'), 10_000);
        await exited;
        clearTimeout(timeout);
      }
    }
  }, { auto: true, timeout: 90_000 }],
});
export { expect };
