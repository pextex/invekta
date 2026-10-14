import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 60_000,
  use: {
    baseURL: "http://localhost:5173",
    viewport: { width: 1920, height: 1080 },
    headless: true,
    launchOptions: { executablePath: process.env.CRM_CHROMIUM_PATH },
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command:
        "cd ../backend && PYTHONPATH=. .venv/bin/python tests/tools/e2e_server.py",
      url: "http://127.0.0.1:18000/api/ready",
      reuseExistingServer: false,
      timeout: 90_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173 --strictPort",
      url: "http://localhost:5173",
      env: { CRM_DEV_API_TARGET: "http://127.0.0.1:18000" },
      reuseExistingServer: false,
    },
  ],
});
