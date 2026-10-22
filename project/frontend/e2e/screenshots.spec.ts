import path from "node:path";
import { expect, test, type Page } from "@playwright/test";

// Window-sized PNGs of the whole page, for the midterm report, from synthetic sample data and the "Demo" profile.

const BAGEL_OCTOBER = path.resolve(
  import.meta.dirname,
  "../../backend/sample_data/exports/Bagel Breakfast - October.csv",
);
const SCREENSHOTS = path.resolve(import.meta.dirname, "../../docs/screenshots");

test.use({ viewport: { width: 1440, height: 900 } });

// The shell fills the window and its panes scroll on their own: the main area and, on Chat, the
// conversation pane.
const PANES = `Array.from(document.querySelectorAll('main, section[aria-label="Conversation"]'))`;

async function shoot(page: Page, name: string, minHeight = 900) {
  // A window-sized capture of the whole page: grow the window until no pane scrolls.
  const extra = await page.evaluate<number>(`Math.max(0, ...${PANES}.map((el) => el.scrollHeight - el.clientHeight))`);
  await page.setViewportSize({ width: 1440, height: Math.max(minHeight, 900 + extra) });
  await page.evaluate("new Promise((resolve) => requestAnimationFrame(() => resolve(null)))");
  const fits = await page.evaluate<boolean>(`${PANES}.every((el) => el.scrollHeight <= el.clientHeight)`);
  expect(fits).toBe(true);
  await page.screenshot({ path: path.join(SCREENSHOTS, name), fullPage: false, animations: "disabled" });
  await page.setViewportSize({ width: 1440, height: 900 });
}

// Asks a question from backend/app/llm/fake_script.json and waits for the scripted reply, the end
// of the stream, and the conversation list to show the new conversation.
async function ask(page: Page, question: string, reply: string, conversations: number) {
  await page.getByRole("textbox").fill(question);
  await page.keyboard.press("Enter");
  await expect(page.getByText(reply)).toBeVisible();
  await expect(page.getByRole("status")).toHaveCount(0);
  await expect(page.getByRole("navigation", { name: "Recent questions" }).getByRole("link")).toHaveCount(conversations);
}

test("midterm screenshots", async ({ page }) => {
  await test.step("upload preview", async () => {
    await page.goto("/upload");
    await page.setInputFiles("input[type=file]", BAGEL_OCTOBER);
    await expect(page.getByText("CampusGroups")).toBeVisible();
    await page.getByLabel("Format").click();
    await page.getByRole("option", { name: "In Person" }).click();
    await page.getByLabel("Event type").fill("Wellness/Mental Health");
    await page.getByLabel("Sponsor/Host/Partners").fill("GPSRC");
    await page.getByLabel("Sponsor/Host/Partners").blur();
    await shoot(page, "01-upload-preview.png");
  });

  await test.step("commit summary", async () => {
    await page.getByRole("button", { name: "Commit" }).click();
    await expect(page.getByText(/38 rows imported/)).toBeVisible();
    await shoot(page, "02-commit-summary.png");
  });

  await test.step("dataset after the commit", async () => {
    await page.goto("/dataset");
    await expect(page.getByRole("grid")).toContainText("Bagel Breakfast");
    await shoot(page, "06-dataset.png");
  });

  await test.step("chat answer with the SQL", async () => {
    await page.goto("/chat");
    await page.getByRole("button", { name: "New chat" }).click();
    await ask(
      page,
      "How many unique people attended Bagel Breakfast, October?",
      "38 unique people attended the October Bagel Breakfast.",
      1,
    );
    await expect(page.getByRole("grid")).toContainText("38");
    // Reopen the conversation so there is no live turn (it has a min-height and leaves the page scrolled).
    await page.reload();
    await page.getByRole("button", { name: "Show results" }).click();
    await expect(page.getByRole("grid")).toContainText("38");
    await page.getByRole("button", { name: "Show the SQL query" }).click();
    await expect(page.getByText(/SELECT COUNT\(DISTINCT person_key\)/)).toBeVisible();
    // The thread scrolls inside the chat page, so the window itself must be tall enough for the whole card.
    await shoot(page, "03-chat-answer.png", 1100);
  });

  await test.step("clarifying question", async () => {
    await page.getByRole("button", { name: "New chat" }).click();
    await ask(
      page,
      "How many people attended events this year?",
      "Do you mean the 2026-27 academic year or calendar year 2026?",
      2,
    );
    await page.reload();
    await expect(page.getByText("Do you mean the 2026-27 academic year or calendar year 2026?")).toBeVisible();
    await shoot(page, "04-clarification.png");
  });

  await test.step("settings", async () => {
    await page.goto("/settings");
    // The e2e stack holds only the scripted profile.
    await expect(page.getByRole("article")).toHaveCount(1);
    await expect(page.getByRole("article", { name: "Demo" })).toContainText("Demo (scripted)");
    await shoot(page, "05-settings.png");
  });

  await test.step("collapsed navigation", async () => {
    await page.goto("/chat");
    await page.getByRole("button", { name: "Collapse navigation" }).click();
    await expect(page.getByRole("button", { name: "Expand navigation" })).toBeVisible();
    await shoot(page, "07-nav-collapsed.png");
    // Leave the nav open for whatever runs next.
    await page.getByRole("button", { name: "Expand navigation" }).click();
  });
});
