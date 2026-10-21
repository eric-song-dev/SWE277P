import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { apiGet } from "../api/client";
import AppShell from "./AppShell";

vi.mock("../api/client");

function renderShell() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter([{ path: "/", element: <AppShell /> }]);
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
    expect(await screen.findByText("Ada Lovelace")).toBeTruthy();
  });

  it("shows 'Not connected' when /api/me fails and still renders the nav", async () => {
    vi.mocked(apiGet).mockRejectedValue(new Error("down"));
    renderShell();
    expect(await screen.findByText("Not connected")).toBeTruthy();
    expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeTruthy();
  });
});
