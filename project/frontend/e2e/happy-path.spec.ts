import path from "node:path";
import { expect, test } from "@playwright/test";

const BAGEL_OCTOBER = path.resolve(
  import.meta.dirname,
  "../../backend/sample_data/exports/Bagel Breakfast - October.csv",
);

// The questions come from backend/app/llm/fake_script.json (the "Demo" profile).
test("upload, ask, export", async ({ page }) => {
  await page.goto("/upload");
  await page.setInputFiles("input[type=file]", BAGEL_OCTOBER);
  await expect(page.getByText("CampusGroups")).toBeVisible();
  await page.getByLabel("Format").click();
  await page.getByRole("option", { name: "In Person" }).click();
  await page.getByLabel("Event type").fill("Wellness/Mental Health");
  await page.getByRole("button", { name: "Commit" }).click();
  await expect(page.getByText(/38 rows imported/)).toBeVisible();

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

// W-33: after a send in a long conversation the new question scrolls near the top, with room for its answer.
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
  await page.waitForTimeout(1500); // the smooth scroll settles
  const overflows = await page.evaluate("document.documentElement.scrollHeight > window.innerHeight * 1.5");
  expect(overflows).toBe(true);

  const mainTop = 0; // the viewport top: the page header has scrolled away
  const lastQuestion = bubbles.last();
  const qTop = (await lastQuestion.boundingBox())!.y;
  expect(qTop - mainTop).toBeLessThan(140);
  expect(qTop).toBeGreaterThan(0);

  const lastCard = page.locator("[data-sent-turn] > :nth-child(2)");
  const cardTop = (await lastCard.boundingBox())!.y;
  const bandTop = (await box.boundingBox())!.y;
  expect(cardTop).toBeLessThan(bandTop);
});

// W-35/W-36: the Dataset grid fits at 1440x900 and the Rows and Flags titles stay whole next to their sort arrow.
test("the Dataset grid fits and keeps the Rows and Flags titles whole", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/dataset");
  const grid = page.getByRole("grid");
  await expect(grid.getByRole("gridcell").first()).toBeVisible(); // the happy path's import is listed

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
