import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiGet, apiSend } from "../../api/client";
import type { LlmProfileOut, PresetOut, ProbeResultOut } from "../../api/types";
import ProfileForm from "./ProfileForm";

// Keep the real ApiError class; automocking would blank its constructor.
vi.mock("../../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../api/client")>()),
  apiGet: vi.fn(),
  apiSend: vi.fn(),
}));

const presets: PresetOut[] = [
  { key: "zotgpt", label: "ZotGPT", base_url: null, share_results_default: true },
  { key: "openai", label: "OpenAI", base_url: "https://api.openai.com/v1", share_results_default: false },
  { key: "custom", label: "Custom", base_url: null, share_results_default: false },
  { key: "fake", label: "Demo (scripted)", base_url: null, share_results_default: false },
];

const openaiProfile: LlmProfileOut = {
  id: 1,
  name: "Lab OpenAI",
  preset: "openai",
  base_url: "https://api.openai.com/v1",
  model: "gpt-4.1-mini",
  api_key_hint: null,
  has_api_key: true,
  share_results_with_llm: false,
  json_mode: null,
  is_default: true,
  last_tested_at: null,
  last_test_ok: null,
};

function renderForm(profile: LlmProfileOut | null, probe?: ProbeResultOut) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  if (probe && profile) client.setQueryData(["llm-probe", profile.id], probe);
  const onClose = vi.fn();
  render(
    <QueryClientProvider client={client}>
      <ProfileForm profile={profile} onClose={onClose} />
    </QueryClientProvider>,
  );
  return { onClose, client };
}

describe("ProfileForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiGet).mockResolvedValue(presets);
  });

  it("never pre-fills the key and omits it when left empty", async () => {
    const user = userEvent.setup();
    const { onClose } = renderForm({ ...openaiProfile, api_key_hint: "sk-…abcd" });
    const key = (await screen.findByLabelText(/API key/i)) as HTMLInputElement;
    expect(key.value).toBe("");
    expect(key).toHaveAttribute("type", "password");
    expect(key).toHaveAttribute("autocomplete", "off");
    expect(screen.getByText(/sk-…abcd/)).toBeInTheDocument();
    vi.mocked(apiSend).mockResolvedValueOnce(openaiProfile);
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(apiSend).toHaveBeenCalledWith("PATCH", "/api/llm-profiles/1", expect.not.objectContaining({ api_key: expect.anything() }));
    expect(onClose).toHaveBeenCalled();
  });

  it("sends only the changed fields when renaming", async () => {
    const user = userEvent.setup();
    renderForm(openaiProfile);
    const name = await screen.findByLabelText(/^Name/);
    await user.clear(name);
    await user.type(name, "Renamed");
    vi.mocked(apiSend).mockResolvedValueOnce(openaiProfile);
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(apiSend).toHaveBeenCalledWith("PATCH", "/api/llm-profiles/1", { name: "Renamed" });
  });

  it("sends api_key when one is typed", async () => {
    const user = userEvent.setup();
    renderForm(openaiProfile);
    await user.type(await screen.findByLabelText(/API key/i), "sk-new");
    vi.mocked(apiSend).mockResolvedValueOnce(openaiProfile);
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(apiSend).toHaveBeenCalledWith("PATCH", "/api/llm-profiles/1", { api_key: "sk-new" });
  });

  it("preset fills base URL and sharing default", async () => {
    const user = userEvent.setup();
    renderForm(null);
    const share = await screen.findByRole("switch", { name: /Allow sending query results/i });
    await user.click(screen.getByRole("combobox", { name: /Provider/i }));
    await user.click(await screen.findByRole("option", { name: "ZotGPT" }));
    expect(share).toBeChecked();
    await user.click(screen.getByRole("combobox", { name: /Provider/i }));
    await user.click(await screen.findByRole("option", { name: "OpenAI" }));
    expect(screen.getByLabelText(/Base URL/i)).toHaveValue("https://api.openai.com/v1");
    expect(share).not.toBeChecked();
    expect(screen.getByText(/Lets the chat page's 'Let AI see the results' switch/)).toBeInTheDocument();
  });

  it("creates a profile with the typed values", async () => {
    const user = userEvent.setup();
    renderForm(null);
    await user.type(await screen.findByLabelText(/^Name/), "Mine");
    await user.click(screen.getByRole("combobox", { name: /Provider/i }));
    await user.click(await screen.findByRole("option", { name: "OpenAI" }));
    await user.type(screen.getByLabelText(/^Model/), "gpt-4.1-mini");
    await user.type(screen.getByLabelText(/API key/i), "sk-abc");
    vi.mocked(apiSend).mockResolvedValueOnce(openaiProfile);
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(apiSend).toHaveBeenCalledWith("POST", "/api/llm-profiles", {
      name: "Mine",
      preset: "openai",
      base_url: "https://api.openai.com/v1",
      model: "gpt-4.1-mini",
      api_key: "sk-abc",
      share_results_with_llm: false,
    });
  });

  it("hides base URL and key for the demo preset", async () => {
    const user = userEvent.setup();
    renderForm(null);
    await user.click(await screen.findByRole("combobox", { name: /Provider/i }));
    await user.click(await screen.findByRole("option", { name: "Demo (scripted)" }));
    expect(screen.queryByLabelText(/Base URL/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/API key/i)).not.toBeInTheDocument();
  });

  it("offers model suggestions from the last successful test", async () => {
    const user = userEvent.setup();
    renderForm(openaiProfile, { ok: true, json_mode: true, models: ["gpt-4.1-mini", "gpt-4.1"], error: null, latency_ms: 80 });
    const combobox = await screen.findByRole("combobox", { name: /^Model/ });
    await user.click(await screen.findByRole("button", { name: "Open" })); // the arrow is there, since there are names
    expect(await screen.findByRole("option", { name: "gpt-4.1-mini" })).toBeInTheDocument();
    expect(combobox).toBeInTheDocument();
  });

  it("shows no dropdown arrow on the Model field when there are no names to suggest", async () => {
    renderForm(null);
    await screen.findByRole("combobox", { name: /^Model/ });
    expect(screen.queryByRole("button", { name: "Open" })).not.toBeInTheDocument();
  });

  it("shows no dropdown arrow when the last test listed no names", async () => {
    renderForm(openaiProfile, { ok: true, json_mode: true, models: [], error: null, latency_ms: 1 });
    await screen.findByRole("combobox", { name: /^Model/ });
    expect(screen.queryByRole("button", { name: "Open" })).not.toBeInTheDocument();
  });

  it("shows a taken name on the Name field and keeps the dialog open", async () => {
    const user = userEvent.setup();
    const { onClose } = renderForm(openaiProfile);
    const name = await screen.findByLabelText(/^Name/);
    await user.type(name, "x");
    vi.mocked(apiSend).mockRejectedValueOnce(new ApiError(409, "profile_name_taken", "You already have an AI model with that name."));
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(await screen.findByText("You already have an AI model with that name.")).toBeInTheDocument();
    expect(name).toBeInvalid();
    expect(onClose).not.toHaveBeenCalled();
  });

  it("shows other save errors in an alert", async () => {
    const user = userEvent.setup();
    renderForm(openaiProfile);
    await user.type(await screen.findByLabelText(/^Name/), "x");
    vi.mocked(apiSend).mockRejectedValueOnce(new ApiError(422, "validation_error", "Base URL is not valid."));
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Base URL is not valid.");
  });

  it("sends base_url when the preset changes even if the URL is unchanged", async () => {
    const user = userEvent.setup();
    const custom = { ...openaiProfile, preset: "custom", base_url: "https://llm.example.edu/v1" };
    renderForm(custom);
    await user.click(await screen.findByRole("combobox", { name: /Provider/i }));
    await user.click(await screen.findByRole("option", { name: "ZotGPT" }));
    expect(screen.getByLabelText(/Base URL/i)).toHaveValue("https://llm.example.edu/v1");
    vi.mocked(apiSend).mockResolvedValueOnce(custom);
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(apiSend).toHaveBeenCalledWith("PATCH", "/api/llm-profiles/1", {
      preset: "zotgpt",
      base_url: "https://llm.example.edu/v1",
      share_results_with_llm: true,
    });
  });

  it("clears the previous preset's default URL when the new preset has none", async () => {
    const user = userEvent.setup();
    renderForm(openaiProfile);
    await user.click(await screen.findByRole("combobox", { name: /Provider/i }));
    await user.click(await screen.findByRole("option", { name: "Custom" }));
    expect(screen.getByLabelText(/Base URL/i)).toHaveValue("");
  });

  it("clears the cached probe result after a save", async () => {
    const user = userEvent.setup();
    const { client } = renderForm(openaiProfile, { ok: true, json_mode: true, models: [], error: null, latency_ms: 1 });
    await user.type(await screen.findByLabelText(/^Model/), "-2");
    vi.mocked(apiSend).mockResolvedValueOnce(openaiProfile);
    await user.click(screen.getByRole("button", { name: /save/i }));
    await vi.waitFor(() => expect(client.getQueryData(["llm-probe", 1])).toBeUndefined());
  });

  const CREDS_MSG = "The base URL must not contain a username or password. Put the key in the API key field.";

  it("refuses a base URL with credentials at the field without sending a request", async () => {
    const user = userEvent.setup();
    renderForm(openaiProfile);
    const url = await screen.findByLabelText(/Base URL/);
    await user.clear(url);
    await user.type(url, "https://user:pass@example.com/v1");
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(await screen.findByText(CREDS_MSG)).toBeInTheDocument();
    expect(url).toBeInvalid();
    expect(apiSend).not.toHaveBeenCalled();
    await user.type(url, "x");
    expect(screen.queryByText(CREDS_MSG)).not.toBeInTheDocument();
  });

  it("shows the same message when the server rejects base_url", async () => {
    const user = userEvent.setup();
    renderForm(openaiProfile);
    await user.type(await screen.findByLabelText(/^Name/), "x");
    vi.mocked(apiSend).mockRejectedValueOnce(
      new ApiError(422, "validation_error", "Request validation failed", [
        { loc: ["body", "base_url"], msg: "Value error, base_url must not contain a username or password", type: "value_error" },
      ]),
    );
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(await screen.findByText(CREDS_MSG)).toBeInTheDocument();
    expect(screen.getByLabelText(/Base URL/)).toBeInvalid();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("keeps the form-level error for other base_url 422s", async () => {
    const user = userEvent.setup();
    renderForm(openaiProfile);
    await user.type(await screen.findByLabelText(/^Name/), "x");
    vi.mocked(apiSend).mockRejectedValueOnce(
      new ApiError(422, "validation_error", "Request validation failed", [
        { loc: ["body", "base_url"], msg: "Input should be a valid URL, relative URL without a base", type: "url_parsing" },
      ]),
    );
    await user.click(screen.getByRole("button", { name: /save/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Request validation failed");
    expect(screen.queryByText(CREDS_MSG)).not.toBeInTheDocument();
  });

  it("lists every reported model on open and filters only after typing", async () => {
    const user = userEvent.setup();
    renderForm(
      { ...openaiProfile, model: "deepseek-flash" },
      { ok: true, json_mode: true, models: ["deepseek-flash", "deepseek-v4-pro"], error: null, latency_ms: 5 },
    );
    const model = await screen.findByRole("combobox", { name: /^Model/ });
    await user.click(screen.getByRole("button", { name: /open/i }));
    expect(await screen.findByRole("option", { name: "deepseek-flash" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "deepseek-v4-pro" })).toBeInTheDocument();
    await user.clear(model);
    await user.type(model, "pro");
    expect(screen.getByRole("option", { name: "deepseek-v4-pro" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "deepseek-flash" })).not.toBeInTheDocument();
    // Closing resets: the next open lists everything again, even with "pro" in the field.
    await user.keyboard("{Escape}");
    await user.click(screen.getByRole("button", { name: /open/i }));
    expect(await screen.findByRole("option", { name: "deepseek-flash" })).toBeInTheDocument();
  });
});
