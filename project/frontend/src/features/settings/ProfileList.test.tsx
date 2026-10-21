import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiGet, apiSend } from "../../api/client";
import type { LlmProfileOut, PresetOut } from "../../api/types";
import ProfileList from "./ProfileList";

// Keep the real ApiError class; automocking would blank its constructor.
vi.mock("../../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../api/client")>()),
  apiGet: vi.fn(),
  apiSend: vi.fn(),
}));

const presets: PresetOut[] = [
  { key: "openai", label: "OpenAI", base_url: "https://api.openai.com/v1", share_results_default: false },
  { key: "zotgpt", label: "ZotGPT", base_url: null, share_results_default: true },
];

const base: LlmProfileOut = {
  id: 1,
  name: "Lab OpenAI",
  preset: "openai",
  base_url: "https://api.openai.com/v1",
  model: "gpt-4.1-mini",
  api_key_hint: "sk-…abcd",
  has_api_key: true,
  share_results_with_llm: false,
  json_mode: null,
  is_default: true,
  last_tested_at: null,
  last_test_ok: null,
};
const second: LlmProfileOut = {
  ...base,
  id: 2,
  name: "Campus ZotGPT",
  preset: "zotgpt",
  api_key_hint: null,
  has_api_key: false,
  share_results_with_llm: true,
  is_default: false,
  last_tested_at: "2026-10-01T12:00:00Z",
  last_test_ok: false,
};

function renderList(onEdit = vi.fn()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <ProfileList profiles={[base, second]} onEdit={onEdit} />
    </QueryClientProvider>,
  );
  return { onEdit };
}

function card(name: string) {
  return screen.getByRole("article", { name });
}

describe("ProfileList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiGet).mockResolvedValue(presets);
  });

  it("shows each profile's details and chips", async () => {
    renderList();
    const first = card("Lab OpenAI");
    expect(await within(first).findByText("OpenAI")).toBeInTheDocument();
    expect(within(first).getByText("gpt-4.1-mini")).toBeInTheDocument();
    expect(within(first).getByText(/sk-…abcd/)).toBeInTheDocument();
    expect(within(first).getByText("Default")).toBeInTheDocument();
    expect(within(first).getByText("Not tested yet")).toBeInTheDocument();
    expect(within(first).queryByText("Can receive results")).not.toBeInTheDocument();
    const other = card("Campus ZotGPT");
    expect(within(other).getByText("Can receive results")).toBeInTheDocument();
    expect(within(other).getByText("No key saved")).toBeInTheDocument();
    expect(within(other).getByText(/Last test failed/)).toBeInTheDocument();
    expect(within(other).queryByText("Default")).not.toBeInTheDocument();
  });

  it("shows 'Connected' after a successful test", async () => {
    const user = userEvent.setup();
    renderList();
    vi.mocked(apiSend).mockResolvedValueOnce({ ok: true, json_mode: true, models: ["gpt-4.1-mini"], error: null, latency_ms: 90 });
    await user.click(within(card("Lab OpenAI")).getByRole("button", { name: "Test" }));
    expect(apiSend).toHaveBeenCalledWith("POST", "/api/llm-profiles/1/test");
    expect(await within(card("Lab OpenAI")).findByText(/Connected/)).toBeInTheDocument();
  });

  it("shows the provider error from a failed test", async () => {
    const user = userEvent.setup();
    renderList();
    vi.mocked(apiSend).mockResolvedValueOnce({ ok: false, json_mode: null, models: [], error: "The AI provider rejected the API key.", latency_ms: 40 });
    await user.click(within(card("Lab OpenAI")).getByRole("button", { name: "Test" }));
    expect(await within(card("Lab OpenAI")).findByText(/rejected the API key/)).toBeInTheDocument();
  });

  it("shows the API error when the test call itself fails", async () => {
    const user = userEvent.setup();
    renderList();
    vi.mocked(apiSend).mockRejectedValueOnce(new ApiError(400, "profile_missing_key", "This AI model has no API key."));
    await user.click(within(card("Campus ZotGPT")).getByRole("button", { name: "Test" }));
    expect(await within(card("Campus ZotGPT")).findByText(/no API key/)).toBeInTheDocument();
  });

  it("makes a profile the default and opens the editor", async () => {
    const user = userEvent.setup();
    const { onEdit } = renderList();
    vi.mocked(apiSend).mockResolvedValueOnce(second);
    await user.click(within(card("Campus ZotGPT")).getByRole("button", { name: "Make default" }));
    expect(apiSend).toHaveBeenCalledWith("POST", "/api/llm-profiles/2/default");
    await user.click(within(card("Campus ZotGPT")).getByRole("button", { name: "Edit" }));
    expect(onEdit).toHaveBeenCalledWith(second);
  });

  it("deletes only after confirmation", async () => {
    const user = userEvent.setup();
    renderList();
    await user.click(within(card("Campus ZotGPT")).getByRole("button", { name: "Delete" }));
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent("Campus ZotGPT");
    expect(apiSend).not.toHaveBeenCalled();
    vi.mocked(apiSend).mockResolvedValueOnce(undefined);
    await user.click(within(dialog).getByRole("button", { name: "Delete" }));
    expect(apiSend).toHaveBeenCalledWith("DELETE", "/api/llm-profiles/2");
  });
});
