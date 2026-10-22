import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { apiGet } from "../api/client";
import type { ConversationOut } from "../api/types";
import AppShell from "./AppShell";

vi.mock("../api/client");

const ME = { id: 1, username: "ada", display_name: "Ada Lovelace", auth_mode: "none" };
const stamp = "2026-10-21T10:00:00Z";
const CONVERSATIONS: ConversationOut[] = [
  { id: 1, title: "How many unique people attended Bagel Breakfast, October?", created_at: stamp, updated_at: stamp },
  { id: 2, title: null, created_at: stamp, updated_at: stamp },
];

// Each path answers on its own; a value of Error makes that request fail.
function mockApi(routes: { me?: unknown; conversations?: unknown }) {
  vi.mocked(apiGet).mockImplementation(async (path: string) => {
    const value = path === "/api/me" ? routes.me : path === "/api/conversations" ? routes.conversations : undefined;
    if (value === undefined || value instanceof Error) throw value ?? new Error(`unexpected GET ${path}`);
    return value;
  });
}

function renderShell(path = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <AppShell />,
        children: ["chat/:conversationId?", "upload", "dataset", "settings"].map((p) => ({
          path: p,
          element: <div>{p}</div>,
        })),
      },
    ],
    { initialEntries: [path] },
  );
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return router;
}

describe("AppShell", () => {
  afterEach(cleanup);

  it("shows the signed-in display name", async () => {
    mockApi({ me: ME, conversations: [] });
    renderShell();
    expect(await screen.findByText("Signed in as Ada Lovelace")).toBeTruthy();
  });

  it("shows 'Not connected' when /api/me fails and still renders the nav", async () => {
    mockApi({ me: new Error("down"), conversations: new Error("down") });
    renderShell();
    expect(await screen.findByText("Not connected")).toBeTruthy();
    expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeTruthy();
    expect(await screen.findByText("Could not load your conversations.")).toBeTruthy();
  });

  it("lists recent questions in the side nav on every page", async () => {
    mockApi({ me: ME, conversations: CONVERSATIONS });
    renderShell("/upload");
    const list = await screen.findByRole("navigation", { name: "Recent questions" });
    const first = await within(list).findByRole("link", {
      name: "How many unique people attended Bagel Breakfast, October?",
    });
    expect(first.getAttribute("href")).toBe("/chat/1");
    expect(first.getAttribute("title")).toBe("How many unique people attended Bagel Breakfast, October?");
    expect(within(list).getByRole("link", { name: "New conversation" }).getAttribute("href")).toBe("/chat/2");
  });

  it("says when there are no conversations yet", async () => {
    mockApi({ me: ME, conversations: [] });
    renderShell("/dataset");
    expect(await screen.findByText("No conversations yet.")).toBeTruthy();
  });

  it("New chat is the first page link and goes to the /chat draft", async () => {
    mockApi({ me: ME, conversations: CONVERSATIONS });
    const user = userEvent.setup();
    const router = renderShell("/settings");
    const main = screen.getByRole("navigation", { name: "Main navigation" });
    const links = within(main).getAllByRole("link");
    expect(links.map((l) => l.getAttribute("aria-label"))).toEqual(["New chat", "Upload", "Dataset", "Settings"]);
    await user.click(links[0]);
    expect(router.state.location.pathname).toBe("/chat");
    expect(links[0].getAttribute("aria-current")).toBe("page");
    // The list has no button of its own.
    const list = await screen.findByRole("navigation", { name: "Recent questions" });
    expect(within(list).queryByRole("button")).toBeNull();
  });

  it("marks an open conversation in the list, not New chat", async () => {
    mockApi({ me: ME, conversations: CONVERSATIONS });
    renderShell("/chat/1");
    const list = await screen.findByRole("navigation", { name: "Recent questions" });
    const open = await within(list).findByRole("link", {
      name: "How many unique people attended Bagel Breakfast, October?",
    });
    expect(open.getAttribute("aria-current")).toBe("page");
    expect(screen.getByRole("link", { name: "New chat" }).getAttribute("aria-current")).toBeNull();
  });

  it("collapses to an icon rail and expands again", async () => {
    mockApi({ me: ME, conversations: CONVERSATIONS });
    const user = userEvent.setup();
    const router = renderShell("/upload");
    await screen.findByText("Signed in as Ada Lovelace");
    const toggle = screen.getByRole("button", { name: "Collapse navigation" });
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    await user.click(toggle);
    const expand = screen.getByRole("button", { name: "Expand navigation" });
    expect(expand.getAttribute("aria-expanded")).toBe("false");
    expect(screen.queryByText("GPSRC Data Hub")).toBeNull();
    expect(screen.queryByText("Signed in as Ada Lovelace")).toBeNull();
    expect(screen.queryByRole("navigation", { name: "Recent questions" })).toBeNull();
    for (const name of ["New chat", "Upload", "Dataset", "Settings"]) {
      expect(screen.getByRole("link", { name }).getAttribute("title")).toBe(name);
    }
    // New chat stays reachable in the rail as the first icon.
    await user.click(screen.getByRole("link", { name: "New chat" }));
    expect(router.state.location.pathname).toBe("/chat");
    await user.click(expand);
    expect(screen.getByText("GPSRC Data Hub")).toBeTruthy();
    expect(screen.getByText("Signed in as Ada Lovelace")).toBeTruthy();
    expect(screen.getByRole("navigation", { name: "Recent questions" })).toBeTruthy();
  });

  it("marks the current page", async () => {
    mockApi({ me: new Error("down"), conversations: [] });
    const user = userEvent.setup();
    renderShell("/upload");
    for (let i = 0; i < 2; i++) {
      expect(screen.getByRole("link", { name: "Upload" }).getAttribute("aria-current")).toBe("page");
      expect(screen.getByRole("link", { name: "New chat" }).getAttribute("aria-current")).toBeNull();
      if (i === 0) await user.click(screen.getByRole("button", { name: "Collapse navigation" }));
    }
  });
});
