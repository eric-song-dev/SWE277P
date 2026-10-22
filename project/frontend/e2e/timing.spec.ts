import { execFileSync } from "node:child_process";
import path from "node:path";
import { expect, test } from "@playwright/test";

// A10: the time from a question to the downloaded Excel file is under 60 s. This runs against the
// main stack with the sample data loaded and a real LLM profile (named by HUB_E2E_PROFILE), so it
// makes real API calls and is skipped unless that variable is set.
const PROFILE = process.env.HUB_E2E_PROFILE;
const PROJECT_DIR = path.resolve(import.meta.dirname, "../..");
const BASE_URL = process.env.HUB_E2E_BASE_URL ?? "http://127.0.0.1:8080";
const LIMIT_MS = 60_000;
const HEALTH_TIMEOUT_MS = 2 * 60_000;
const REQUEST_TIMEOUT_MS = 5_000;

// q01, q04 and q14 of backend/benchmark/questions.yaml, verbatim.
const QUESTIONS = [
  { id: "q01", text: "How many unique Biological Sciences students came to a Bagel Breakfast in Fall 2026?" },
  { id: "q04", text: "List the emails of everyone who attended any Bagel Breakfast." },
  { id: "q14", text: "List everyone who attended 5 or more events, with how many events each attended." },
];

async function waitForHealth() {
  const deadline = Date.now() + HEALTH_TIMEOUT_MS;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${BASE_URL}/api/health`, { signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS) });
      if (res.ok) return;
    } catch {
      // The API is still restarting.
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`${BASE_URL}/api/health did not answer within ${HEALTH_TIMEOUT_MS / 1000} s`);
}

test.describe.configure({ mode: "serial" });
test.skip(!PROFILE, "Set HUB_E2E_PROFILE to the name of a real AI profile to run the timing check.");

test.beforeAll(async () => {
  // Restart the API so the first question is a cold start. Same compose files as the stack's own.
  test.setTimeout(HEALTH_TIMEOUT_MS + 60_000);
  execFileSync("docker", ["compose", "restart", "api"], { cwd: PROJECT_DIR, stdio: "pipe", timeout: 120_000 });
  await waitForHealth();
});

for (const q of QUESTIONS) {
  test(`${q.id}: question to downloaded Excel under 60 s`, async ({ page }) => {
    test.setTimeout(LIMIT_MS + 60_000);
    await page.goto("/chat");
    await page.getByRole("button", { name: "New chat" }).click();
    await page.getByLabel("Answering with").click();
    await page.getByRole("option", { name: PROFILE!, exact: true }).click();

    await page.getByRole("textbox").fill(q.text);
    const start = Date.now();
    await page.keyboard.press("Enter");

    const xlsx = page.getByRole("button", { name: ".xlsx" });
    await xlsx.waitFor({ timeout: LIMIT_MS });
    const [download] = await Promise.all([page.waitForEvent("download", { timeout: LIMIT_MS }), xlsx.click()]);
    const elapsed = Date.now() - start;

    console.log(`TIMING ${q.id}: ${elapsed} ms (${download.suggestedFilename()})`);
    expect(download.suggestedFilename()).toMatch(/\.xlsx$/);
    expect(elapsed).toBeLessThan(LIMIT_MS);
  });
}
