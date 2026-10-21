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
