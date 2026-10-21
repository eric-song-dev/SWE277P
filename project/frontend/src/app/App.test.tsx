import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { apiGet } from "../api/client";

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  apiGet: vi.fn(),
}));
// An open tab after a rebuild: the page's chunk is gone.
vi.mock("../features/dataset/DatasetPage", () => {
  throw new Error("Failed to fetch dynamically imported module");
});

afterEach(() => vi.unstubAllGlobals());

it("shows a plain message with Reload when a page fails to load", async () => {
  vi.mocked(apiGet).mockResolvedValue({ id: 1, username: "ada", display_name: "Ada", auth_mode: "none" });
  vi.spyOn(console, "error").mockImplementation(() => {}); // React reports the caught error
  const reload = vi.fn();
  // App creates its browser router on import, from the current URL.
  window.history.replaceState(null, "", "/dataset");
  const { default: App } = await import("./App");
  vi.stubGlobal("location", { ...window.location, reload });
  render(<App />);
  expect(await screen.findByText("Something went wrong. Reload the page to continue.")).toBeInTheDocument();
  await userEvent.click(screen.getByRole("button", { name: "Reload" }));
  expect(reload).toHaveBeenCalledTimes(1);
});
