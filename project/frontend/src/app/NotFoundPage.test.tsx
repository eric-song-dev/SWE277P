import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { apiGet } from "../api/client";

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  apiGet: vi.fn(),
}));

beforeEach(() => {
  // The shell asks for the user and, for its side nav, the conversation list.
  vi.mocked(apiGet).mockImplementation(async (path: string) =>
    path === "/api/conversations" ? [] : { id: 1, username: "ada", display_name: "Ada", auth_mode: "none" },
  );
});
afterEach(() => cleanupRoute());

function cleanupRoute() {
  window.history.replaceState(null, "", "/");
}

async function renderAt(path: string) {
  // App creates its browser router on import, from the current URL.
  vi.resetModules();
  window.history.replaceState(null, "", path);
  const { default: App } = await import("./App");
  render(<App />);
}

it.each(["/foo", "/upload/extra", "/settings/foo"])("shows Page not found inside the shell at %s", async (path) => {
  await renderAt(path);
  expect(await screen.findByRole("heading", { level: 1, name: "Page not found" })).toBeInTheDocument();
  expect(screen.getByText("There is no page at this address.")).toBeInTheDocument();
  expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Go to Chat" })).toHaveAttribute("href", "/chat");
  expect(screen.queryByText("Something went wrong. Reload the page to continue.")).not.toBeInTheDocument();
});
