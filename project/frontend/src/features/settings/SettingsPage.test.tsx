import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { apiGet } from "../../api/client";
import SettingsPage from "./SettingsPage";

// Keep the real ApiError class; automocking would blank its constructor.
vi.mock("../../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../api/client")>()),
  apiGet: vi.fn(),
  apiSend: vi.fn(),
}));

describe("SettingsPage", () => {
  it("has a level 1 Settings heading", async () => {
    vi.mocked(apiGet).mockResolvedValue([]);
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <SettingsPage />
      </QueryClientProvider>,
    );
    expect(screen.getByRole("heading", { level: 1, name: "Settings" })).toBeInTheDocument();
    expect(await screen.findByText("No AI models yet. Add one to start asking questions.")).toBeInTheDocument();
  });
});
