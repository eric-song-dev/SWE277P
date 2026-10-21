import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiSend, apiUpload } from "../../api/client";
import type { CommitSummary, ImportPreview } from "../../api/types";
import UploadPage from "./UploadPage";

// Keep the real ApiError class; automocking would blank its constructor.
vi.mock("../../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../api/client")>()),
  apiGet: vi.fn(),
  apiSend: vi.fn(),
  apiUpload: vi.fn(),
}));

function pending(id: number, name: string): ImportPreview {
  return {
    id,
    file_name: `${name}.csv`,
    status: "pending",
    source: "campusgroups",
    source_display: "CampusGroups",
    row_count: 38,
    skipped: [{ source_row: 7, reason: "blank row" }],
    flag_counts: { missing_netid: 2, odd_code: 1 },
    event_draft: {
      name,
      event_date: null,
      term: "Fall 2026",
      modality: "In Person",
      sponsors_hosts: null,
      event_type: "Fellowships",
      on_campus_groups: true,
      attendance_source_note: null,
      student_worker: null,
    },
    duplicate_of: null,
    error: null,
  };
}

const blank = { source: null, source_display: null, row_count: 0, skipped: [], flag_counts: {}, event_draft: null };

const duplicate: ImportPreview = {
  ...blank, id: null, file_name: "dup.csv", status: "duplicate", duplicate_of: 3, error: null,
};
const rejected: ImportPreview = {
  ...blank,
  id: null,
  file_name: "bad.csv",
  status: "rejected",
  duplicate_of: null,
  error: { code: "missing_columns", message: "Required columns are missing.", details: { missing: ["Net ID"] } },
};

const summary: CommitSummary = {
  import_id: 5, event_id: 9, inserted: 38, linked_by_netid: 30, linked_by_email: 4,
  new_people: 3, unlinked: 1, flagged_rows: 2, skipped: 1, duplicates_in_event: 0,
};

async function drop(files: File[]) {
  const user = userEvent.setup({ applyAccept: false });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <UploadPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  await user.upload(document.querySelector("input[type=file]") as HTMLInputElement, files);
  return user;
}

const csv = (name: string) => new File(["a"], name, { type: "text/csv" });

describe("UploadPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders one card per file with its status", async () => {
    vi.mocked(apiUpload).mockResolvedValueOnce({ files: [pending(5, "Mixer"), duplicate, rejected] });
    await drop([csv("a.csv"), csv("dup.csv"), csv("bad.csv")]);
    expect(await screen.findByText(/Missing columns: Net ID/)).toBeInTheDocument();
    expect(screen.getByText("Required columns are missing.")).toBeInTheDocument();
    expect(screen.getByText("Already imported")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Dataset/ })).toHaveAttribute("href", "/dataset");
    expect(screen.getAllByText("CampusGroups")).toHaveLength(1);
    expect(screen.getByText("Missing NetID: 2")).toBeInTheDocument();
    expect(screen.getByText("odd_code: 1")).toBeInTheDocument();
    expect(screen.getByLabelText(/Format/)).toBeInTheDocument();
  });

  it("shows an alert when the upload request fails", async () => {
    vi.mocked(apiUpload).mockRejectedValueOnce(new Error("boom"));
    await drop([csv("a.csv")]);
    expect(await screen.findByRole("alert")).toHaveTextContent(/Upload failed/);
  });

  it("lists files with an unsupported type", async () => {
    await drop([new File(["a"], "notes.txt", { type: "text/plain" })]);
    expect(await screen.findByText(/notes\.txt/)).toBeInTheDocument();
    expect(apiUpload).not.toHaveBeenCalled();
  });

  it("commits one card, shows the summary, and keeps other cards' edits", async () => {
    vi.mocked(apiUpload).mockResolvedValueOnce({ files: [pending(5, "Mixer"), pending(6, "Panel")] });
    const user = await drop([csv("a.csv"), csv("b.csv")]);
    const cardA = (await screen.findByText("Mixer.csv")).closest("[data-testid=preview-card]") as HTMLElement;
    const cardB = screen.getByText("Panel.csv").closest("[data-testid=preview-card]") as HTMLElement;
    const nameB = within(cardB).getByLabelText(/Event name/);
    await user.type(nameB, " edited");
    vi.mocked(apiSend).mockResolvedValueOnce(summary);
    await user.click(within(cardA).getByRole("button", { name: "Commit" }));
    expect(apiSend).toHaveBeenCalledWith("POST", "/api/imports/5/commit", expect.objectContaining({ name: "Mixer" }));
    expect(await within(cardA).findByText("38 rows imported")).toBeInTheDocument();
    expect(within(cardA).getByText("Linked by NetID")).toBeInTheDocument();
    expect(within(cardA).getByText("Duplicates in event")).toBeInTheDocument();
    expect(within(cardB).getByLabelText(/Event name/)).toHaveValue("Panel edited");
  });

  it("discards one card without touching the other", async () => {
    vi.mocked(apiUpload).mockResolvedValueOnce({ files: [pending(5, "Mixer"), pending(6, "Panel")] });
    const user = await drop([csv("a.csv"), csv("b.csv")]);
    const cardA = (await screen.findByText("Mixer.csv")).closest("[data-testid=preview-card]") as HTMLElement;
    vi.mocked(apiSend).mockResolvedValueOnce(undefined);
    await user.click(within(cardA).getByRole("button", { name: "Discard" }));
    await waitFor(() => expect(screen.queryByText("Mixer.csv")).not.toBeInTheDocument());
    expect(apiSend).toHaveBeenCalledWith("DELETE", "/api/imports/5");
    expect(screen.getByText("Panel.csv")).toBeInTheDocument();
  });

  it("does not add a second card for an already pending import", async () => {
    vi.mocked(apiUpload)
      .mockResolvedValueOnce({ files: [pending(5, "Mixer")] })
      .mockResolvedValueOnce({ files: [pending(5, "Mixer")] });
    const user = await drop([csv("a.csv")]);
    await screen.findByText("Mixer.csv");
    await user.upload(document.querySelector("input[type=file]") as HTMLInputElement, csv("a.csv"));
    await waitFor(() => expect(apiUpload).toHaveBeenCalledTimes(2));
    expect(screen.getAllByText("Mixer.csv")).toHaveLength(1);
  });

  it("keeps every batch's cards when a second drop starts before the first upload resolves", async () => {
    let releaseFirst: (value: { files: ImportPreview[] }) => void = () => {};
    vi.mocked(apiUpload)
      .mockReturnValueOnce(new Promise((resolve) => (releaseFirst = resolve)))
      .mockResolvedValueOnce({ files: [pending(6, "Panel")] });
    const user = await drop([csv("a.csv")]);
    await user.upload(document.querySelector("input[type=file]") as HTMLInputElement, csv("b.csv"));
    expect(await screen.findByText("Panel.csv")).toBeInTheDocument();
    releaseFirst({ files: [pending(5, "Mixer")] });
    expect(await screen.findByText("Mixer.csv")).toBeInTheDocument();
    expect(screen.getByText("Panel.csv")).toBeInTheDocument();
  });
});
