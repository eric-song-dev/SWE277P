import path from "node:path";
import { expect, type Page, test } from "@playwright/test";

const BAGEL_OCTOBER = path.resolve(
  import.meta.dirname,
  "../../backend/sample_data/exports/Bagel Breakfast - October.csv",
);

// Puts the Bagel October file in the Hub if it is not there yet, so a test does not depend on another one.
async function ensureBagelImported(page: Page) {
  await page.goto("/upload");
  await page.setInputFiles("input[type=file]", BAGEL_OCTOBER);
  const form = page.getByLabel("Format");
  await form.or(page.getByText(/Already imported/)).waitFor();
  if (await form.isVisible()) {
    await form.click();
    await page.getByRole("option", { name: "In Person" }).click();
    await page.getByLabel("Event type").fill("Wellness/Mental Health");
    await page.getByRole("button", { name: "Commit" }).click();
    await expect(page.getByText(/38 rows imported/)).toBeVisible();
  }
}

// The questions come from backend/app/llm/fake_script.json (the "Demo" profile).
test("upload, ask, export", async ({ page }) => {
  await ensureBagelImported(page);

  await page.goto("/chat");
  await page.getByRole("button", { name: "New chat" }).click();
  await page.getByRole("textbox").fill("How many unique people attended Bagel Breakfast, October?");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("grid")).toContainText("38");
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: ".xlsx" }).click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/^hub-turn-\d+-\d{8}-\d{4}\.xlsx$/);

  await page.getByRole("textbox").fill("Of those, how many are international?");
  await page.keyboard.press("Enter");
  await expect(page.getByRole("grid")).toHaveCount(2);
  await expect(page.getByLabel("Let AI see the results")).toBeChecked(); // kept across the follow-up
});

// Review Focus 1: a long unbroken question wraps and the page never scrolls sideways.
test("a long unbroken question does not widen the page", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 768 });
  await page.goto("/chat");
  await page.getByRole("textbox").fill("x".repeat(300));
  await page.keyboard.press("Enter");
  await expect(page.getByText(/only knows its scripted questions/i)).toBeVisible();
  const fits = await page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth");
  expect(fits).toBe(true);
});

// W-33: after a send in a long conversation the new question scrolls near the top of the pane, with room for its answer.
test("a send in a long conversation scrolls the question to the top", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/chat");
  const box = page.getByRole("textbox");
  const question = "How many unique people attended Bagel Breakfast, October?";
  const thread = page.getByRole("region", { name: "Conversation" });
  const bubbles = thread.getByText(question, { exact: true });
  const total = 7;
  for (let i = 1; i <= total; i++) {
    await box.fill(question);
    await expect(page.getByRole("button", { name: "Send" })).toBeEnabled({ timeout: 30_000 }); // the last answer is done
    await page.keyboard.press("Enter");
    await expect(bubbles).toHaveCount(i);
  }
  await box.fill("done?"); // Send enables again once the last answer has finished
  await expect(page.getByRole("button", { name: "Send" })).toBeEnabled({ timeout: 30_000 });
  await box.fill("");
  // Only the conversation pane scrolls; the page itself never does.
  const overflows = await thread.evaluate((el) => el.scrollHeight > el.clientHeight * 1.5);
  expect(overflows).toBe(true);
  expect(await page.evaluate("document.documentElement.scrollHeight <= window.innerHeight")).toBe(true);

  const mainTop = (await thread.boundingBox())!.y; // the pane's top, under the fixed model row
  const lastQuestion = bubbles.last();
  // Wait for the smooth scroll to settle: the bubble's y is read twice and counts only when it did not move.
  await expect
    .poll(async () => {
      const first = (await lastQuestion.boundingBox())!.y;
      await page.waitForTimeout(100);
      const second = (await lastQuestion.boundingBox())!.y;
      return first === second ? second - mainTop : Number.NaN;
    })
    .toBeLessThan(140);
  const qTop = (await lastQuestion.boundingBox())!.y;
  expect(qTop).toBeGreaterThan(mainTop);

  const lastCard = page.locator("[data-sent-turn] > :nth-child(2)");
  const cardTop = (await lastCard.boundingBox())!.y;
  const bandTop = (await box.boundingBox())!.y;
  expect(cardTop).toBeLessThan(bandTop);

  // The question box and the model row stay put while the pane scrolls back to the top.
  const modelTop = (await page.getByLabel("Answering with").boundingBox())!.y;
  await thread.evaluate((el) => el.scrollTo({ top: 0 }));
  await expect.poll(() => thread.evaluate((el) => el.scrollTop)).toBe(0);
  expect((await box.boundingBox())!.y).toBe(bandTop);
  expect((await page.getByLabel("Answering with").boundingBox())!.y).toBe(modelTop);
});

// W-35/W-36: the Dataset grid fits at 1440x900 and the Rows and Flags titles stay whole next to their sort arrow.
test("the Dataset grid fits and keeps the Rows and Flags titles whole", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await ensureBagelImported(page);
  await page.goto("/dataset");
  const grid = page.getByRole("grid");
  await expect(grid.getByRole("gridcell").first()).toBeVisible(); // the import is listed

  const noSideScroll = await page
    .locator(".MuiDataGrid-virtualScroller")
    .evaluate((el) => el.scrollWidth <= el.clientWidth);
  expect(noSideScroll).toBe(true);

  const gridBox = (await grid.boundingBox())!;
  const status = (await grid.getByRole("columnheader", { name: "Status" }).boundingBox())!;
  expect(status.x).toBeGreaterThanOrEqual(gridBox.x);
  expect(status.x + status.width).toBeLessThanOrEqual(gridBox.x + gridBox.width + 0.5);

  for (const name of ["Rows", "Flags"]) {
    const header = grid.getByRole("columnheader", { name });
    await header.click(); // sorts by this column, so its arrow shows
    await expect(header).toHaveAttribute("aria-sort", "ascending");
    await page.mouse.move(0, 0);
    const whole = await header
      .locator(".MuiDataGrid-columnHeaderTitle")
      .evaluate((el) => el.scrollWidth <= el.clientWidth);
    expect(whole, `${name} title is cut`).toBe(true);
  }
});

// W-37: a grid scrolled sideways still shows a focus ring where Tab lands (its scroll area).
test("Tab into a scrolled answer grid shows an inset focus ring", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await ensureBagelImported(page);
  await page.goto("/chat");
  await page.getByRole("textbox").fill("Demo all columns");
  await page.keyboard.press("Enter");
  const grid = page.getByRole("grid");
  await expect(grid).toBeVisible();
  await expect(grid.getByRole("gridcell").first()).toBeVisible();
  await page.evaluate(`(() => {
    const s = document.querySelector('[role="grid"] .MuiDataGrid-virtualScroller');
    s.scrollLeft = s.scrollWidth;
  })()`);
  await expect
    .poll(() =>
      page.evaluate(`(() => {
        const s = document.querySelector('[role="grid"] .MuiDataGrid-virtualScroller');
        const atEnd = s.scrollLeft > 0 && s.scrollLeft >= s.scrollWidth - s.clientWidth - 1;
        // The grid has dropped its tabbable header from the DOM, so Tab lands on the scroll area.
        const noTabbableHeader = !document.querySelector('[role="grid"] [role="columnheader"][tabindex="0"]');
        return atEnd && noTabbableHeader;
      })()`),
    )
    .toBe(true);
  // Focus the last tabbable element before the grid, then Tab into it.
  await page.evaluate(`(() => {
    const g = document.querySelector('[role="grid"]');
    const all = Array.from(document.querySelectorAll('a[href], button:not([disabled]), input:not([disabled]), textarea, [tabindex="0"]'));
    const before = all.filter((e) => (e.compareDocumentPosition(g) & Node.DOCUMENT_POSITION_FOLLOWING) && !g.contains(e));
    before[before.length - 1].focus();
  })()`);
  const inGrid = "document.querySelector('[role=\"grid\"]').contains(document.activeElement)";
  for (let i = 0; i < 5; i++) {
    await page.keyboard.press("Tab");
    if (await page.evaluate(inGrid)) break;
  }
  expect(await page.evaluate(inGrid)).toBe(true);
  const ring = await page.evaluate<{ cls: string; style: string; width: string; offset: string }>(`(() => {
    const s = getComputedStyle(document.activeElement);
    return { cls: document.activeElement.className, style: s.outlineStyle, width: s.outlineWidth, offset: s.outlineOffset };
  })()`);
  expect(ring.cls).toContain("MuiDataGrid-virtualScroller"); // Tab lands on the scroll area
  expect({ style: ring.style, width: ring.width, offset: ring.offset }).toEqual({
    style: "solid",
    width: "2px",
    offset: "-2px",
  });
});
