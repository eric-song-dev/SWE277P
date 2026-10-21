import { defineConfig, devices } from "@playwright/test";

// Each run brings up its own Docker stack (see e2e/global-setup.ts), and each spec uploads the
// files it needs, so run one spec per invocation: `npm run e2e` or `npm run e2e:screenshots`.
export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  // The stack is shared, so the tests run one at a time.
  workers: 1,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:8081",
    acceptDownloads: true,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
