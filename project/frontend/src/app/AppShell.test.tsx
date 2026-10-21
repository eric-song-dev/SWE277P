import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { apiGet } from "../api/client";
import AppShell from "./AppShell";

vi.mock("../api/client");

function renderShell(path = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <AppShell />,
        children: ["chat", "upload", "dataset", "settings"].map((p) => ({ path: p, element: <div>{p}</div> })),
      },
    ],
    { initialEntries: [path] },
  );
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

describe("AppShell", () => {
  afterEach(cleanup);

  it("shows the signed-in display name", async () => {
    vi.mocked(apiGet).mockResolvedValue({
      id: 1,
      username: "ada",
      display_name: "Ada Lovelace",
      auth_mode: "none",
    });
    renderShell();
    expect(await screen.findByText("Signed in as Ada Lovelace")).toBeTruthy();
  });

  it("shows 'Not connected' when /api/me fails and still renders the nav", async () => {
    vi.mocked(apiGet).mockRejectedValue(new Error("down"));
    renderShell();
    expect(await screen.findByText("Not connected")).toBeTruthy();
    expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeTruthy();
  });

  it("collapses to an icon rail and expands again", async () => {
    vi.mocked(apiGet).mockResolvedValue({ id: 1, username: "ada", display_name: "Ada Lovelace", auth_mode: "none" });
    const user = userEvent.setup();
    renderShell();
    await screen.findByText("Signed in as Ada Lovelace");
    const toggle = screen.getByRole("button", { name: "Collapse navigation" });
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    await user.click(toggle);
    const expand = screen.getByRole("button", { name: "Expand navigation" });
    expect(expand.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByText("GPSRC Data Hub")).toBeNull();
    expect(screen.queryByText("Signed in as Ada Lovelace")).toBeNull();
    for (const name of ["Chat", "Upload", "Dataset", "Settings"]) {
      expect(screen.getByRole("link", { name }).getAttribute("title")).toBe(name);
    }
    await user.click(expand);
    expect(screen.getByText("GPSRC Data Hub")).toBeTruthy();
    expect(screen.getByText("Signed in as Ada Lovelace")).toBeTruthy();
  });

  it("marks the current page", async () => {
    vi.mocked(apiGet).mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderShell("/upload");
    for (let i = 0; i < 2; i++) {
      expect(screen.getByRole("link", { name: "Upload" }).getAttribute("aria-current")).toBe("page");
      expect(screen.getByRole("link", { name: "Chat" }).getAttribute("aria-current")).toBeNull();
      if (i === 0) await user.click(screen.getByRole("button", { name: "Collapse navigation" }));
    }
  });
});
