import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiSend } from "../../api/client";
import type { CommitSummary, EventDraftOut } from "../../api/types";
import EventDetailsForm from "./EventDetailsForm";
import { UploadProvider } from "./UploadContext";

// Keep the real ApiError class; automocking would blank its constructor.
vi.mock("../../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../api/client")>()),
  apiSend: vi.fn(),
}));

const draft: EventDraftOut = {
  name: "Resume Workshop",
  event_date: "2026-10-05",
  term: "Fall 2026",
  modality: "Hybrid",
  sponsors_hosts: "Career Center",
  event_type: null,
  on_campus_groups: true,
  attendance_source_note: null,
  student_worker: null,
};

const summary: CommitSummary = {
  import_id: 5,
  event_id: 9,
  inserted: 38,
  linked_by_netid: 30,
  linked_by_email: 4,
  new_people: 3,
  unlinked: 1,
  flagged_rows: 2,
  skipped: 1,
  duplicates_in_event: 0,
};

function renderForm(onCommitted = vi.fn()) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <UploadProvider>
        <EventDetailsForm importId={5} draft={draft} onCommitted={onCommitted} />
      </UploadProvider>
    </QueryClientProvider>,
  );
  return { onCommitted };
}

describe("EventDetailsForm", () => {
  beforeEach(() => vi.clearAllMocks());

  it("prefills from the draft and validates the term", async () => {
    const user = userEvent.setup();
    renderForm();
    expect(screen.getByLabelText(/Event name/)).toHaveValue("Resume Workshop");
    const term = screen.getByLabelText(/Term/);
    expect(term).toHaveValue("Fall 2026");
    await user.clear(term);
    await user.type(term, "fall 26");
    expect(screen.getByText(/Use a season and year/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Commit" })).toBeDisabled();
  });

  it("keeps Commit disabled until the event type is filled in", async () => {
    const user = userEvent.setup();
    renderForm();
    expect(screen.getByRole("button", { name: "Commit" })).toBeDisabled();
    await user.type(screen.getByLabelText(/Event type/), "Wellness/Mental Health");
    expect(screen.getByRole("button", { name: "Commit" })).toBeEnabled();
  });

  it("commits EventDetailsIn once even on a double click, then reports the summary", async () => {
    const user = userEvent.setup();
    const { onCommitted } = renderForm();
    let release: (value: CommitSummary) => void = () => {};
    vi.mocked(apiSend).mockReturnValueOnce(new Promise((resolve) => (release = resolve)));
    await user.type(screen.getByLabelText(/Event type/), "Fellowships");
    await user.dblClick(screen.getByRole("button", { name: "Commit" }));
    release(summary);
    await waitFor(() => expect(onCommitted).toHaveBeenCalledWith(summary));
    expect(apiSend).toHaveBeenCalledTimes(1);
    expect(apiSend).toHaveBeenCalledWith("POST", "/api/imports/5/commit", {
      name: "Resume Workshop",
      event_date: "2026-10-05",
      term: "Fall 2026",
      modality: "Hybrid",
      sponsors_hosts: "Career Center",
      event_type: "Fellowships",
      attendance_source_note: null,
      student_worker: null,
    });
  });

  it("shows a commit error and stays editable", async () => {
    const user = userEvent.setup();
    renderForm();
    vi.mocked(apiSend).mockRejectedValueOnce(new ApiError(409, "already_committed", "Already committed."));
    await user.type(screen.getByLabelText(/Event type/), "Fellowships");
    await user.click(screen.getByRole("button", { name: "Commit" }));
    expect(await screen.findByText("Already committed.")).toBeInTheDocument();
    expect(screen.getByLabelText(/Event name/)).toBeEnabled();
    expect(screen.getByRole("button", { name: "Commit" })).toBeEnabled();
  });
});
