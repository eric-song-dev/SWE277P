import { defineConfig, devices } from "@playwright/test";

// A10 (question to downloaded Excel under 60 s) runs against the main stack, with its samples
// loaded and a real LLM profile, so there is no global setup: nothing here starts or stops a stack.
// See the `e2e:timing` entry in CLAUDE.md.
export default defineConfig({
  testDir: "./e2e",
  testMatch: "timing.spec.ts",
  workers: 1,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  reporter: "list",
  use: {
    baseURL: process.env.HUB_E2E_BASE_URL ?? "http://127.0.0.1:8080",
    acceptDownloads: true,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
