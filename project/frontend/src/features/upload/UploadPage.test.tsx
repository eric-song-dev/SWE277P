import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, Link, RouterProvider } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiGet, apiSend, apiUpload } from "../../api/client";
import type { CommitSummary, ImportFileOut, ImportPreview } from "../../api/types";
import { UploadProvider } from "./UploadContext";
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

function renderUpload(path = "/upload") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(
    [
      { path: "/upload", element: <UploadPage /> },
      { path: "/chat", element: <Link to="/upload">Back to upload</Link> },
    ],
    { initialEntries: [path] },
  );
  // The provider sits above the routes, like the app shell's.
  render(
    <QueryClientProvider client={client}>
      <UploadProvider>
        <RouterProvider router={router} />
      </UploadProvider>
    </QueryClientProvider>,
  );
  return { router, user: userEvent.setup({ applyAccept: false }) };
}

async function drop(files: File[]) {
  const { user } = renderUpload();
  await user.upload(document.querySelector("input[type=file]") as HTMLInputElement, files);
  return user;
}

function importRow(id: number, status: "pending" | "committed"): ImportFileOut {
  return {
    id,
    file_name: `Mixer-${id}.csv`,
    source: "campusgroups",
    status,
    row_count: 38,
    skipped_count: 0,
    event: null,
    flag_count: 0,
    uploaded_by: { id: 1, display_name: "Ada" },
    uploaded_at: "2026-10-02T17:30:00Z",
    committed_at: null,
  };
}

const csv = (name: string) => new File(["a"], name, { type: "text/csv" });

describe("UploadPage", () => {
  it("has a level 1 Upload heading and the drop zone copy", () => {
    vi.mocked(apiGet).mockResolvedValue([]);
    renderUpload();
    expect(screen.getByRole("heading", { level: 1, name: "Upload" })).toBeInTheDocument();
    expect(screen.getByText("Drop CSV or Excel files here, or click to choose. (.csv, .xlsx, .xlsm)")).toBeInTheDocument();
  });

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiGet).mockResolvedValue([]);
  });

  it("renders one card per file with its status", async () => {
    vi.mocked(apiUpload).mockResolvedValueOnce({ files: [pending(5, "Mixer"), duplicate, rejected] });
    await drop([csv("a.csv"), csv("dup.csv"), csv("bad.csv")]);
    expect(await screen.findByText(/Missing columns: Net ID/)).toBeInTheDocument();
    expect(screen.getByText("Required columns are missing.")).toBeInTheDocument();
    expect(screen.getByText("Already imported")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Dataset/ })).toHaveAttribute("href", "/dataset");
    expect(screen.getAllByText("CampusGroups")).toHaveLength(1);
    expect(screen.getByText("NetID missing: 2")).toBeInTheDocument();
    expect(screen.getByText("odd_code: 1")).toBeInTheDocument();
    expect(screen.getByLabelText(/Format/)).toBeInTheDocument();
  });

  it("shows no raw codes for a 12twenty preview", async () => {
    vi.mocked(apiUpload).mockResolvedValueOnce({
      files: [
        {
          ...pending(8, "Career Panel"),
          source: "twelvetwenty",
          source_display: "12twenty",
          skipped: [
            { source_row: 4, reason: "not_attended" },
            { source_row: 9, reason: "not_attended" },
          ],
          flag_counts: {
            missing_netid: 2,
            missing_email: 1,
            missing_school: 3,
            missing_department: 3,
            missing_affiliation: 1,
            non_standard_email: 2,
            missing_degree: 1,
            not_attended_skipped: 2,
          },
        },
      ],
    });
    await drop([csv("a.csv")]);
    const card = (await screen.findByText("Career Panel.csv")).closest("[data-testid=preview-card]") as HTMLElement;
    expect(within(card).getByText("Non-standard email, NetID not derived: 2")).toBeInTheDocument();
    expect(within(card).getByText("Degree missing: 1")).toBeInTheDocument();
    expect(within(card).getByText("Row 4: Not marked as attended")).toBeInTheDocument();
    expect(card.textContent).not.toMatch(/[a-z]+_[a-z]+/);
  });

  it("labels the identity flags too", async () => {
    vi.mocked(apiUpload).mockResolvedValueOnce({
      files: [
        {
          ...pending(9, "Mixer"),
          skipped: [],
          flag_counts: {
            missing_identity: 1,
            missing_domestic_international: 4,
            netid_email_conflict: 1,
            email_owned_by_other: 1,
            duplicate_in_event: 1,
          },
        },
      ],
    });
    await drop([csv("a.csv")]);
    const card = (await screen.findByText("Mixer.csv")).closest("[data-testid=preview-card]") as HTMLElement;
    expect(within(card).getByText("Email belongs to another person: 1")).toBeInTheDocument();
    expect(card.textContent).not.toMatch(/[a-z]+_[a-z]+/);
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

  it("reports an earlier batch's failure even after a later batch succeeded", async () => {
    let failFirst: (error: Error) => void = () => {};
    vi.mocked(apiUpload)
      .mockReturnValueOnce(new Promise((_, reject) => (failFirst = reject)))
      .mockResolvedValueOnce({ files: [pending(6, "Panel")] });
    const user = await drop([csv("a.csv")]);
    await user.upload(document.querySelector("input[type=file]") as HTMLInputElement, csv("b.csv"));
    expect(await screen.findByText("Panel.csv")).toBeInTheDocument();
    failFirst(new Error("boom"));
    expect(await screen.findByText(/Upload failed for a\.csv: boom/)).toBeInTheDocument();
    expect(screen.getByText("Panel.csv")).toBeInTheDocument();
  });

  it("gives two copies of one export in one batch a single card", async () => {
    const log = vi.spyOn(console, "error").mockImplementation(() => {});
    vi.mocked(apiUpload).mockResolvedValueOnce({ files: [pending(5, "Mixer"), pending(5, "Mixer")] });
    await drop([csv("a.csv"), csv("a-copy.csv")]);
    await screen.findByText("Mixer.csv");
    expect(screen.getAllByText("Mixer.csv")).toHaveLength(1);
    expect(log).not.toHaveBeenCalledWith(expect.stringContaining("same key"), expect.anything());
    log.mockRestore();
  });

  it("shows the server's pending imports when the page opens", async () => {
    vi.mocked(apiGet).mockImplementation(async (path) => {
      if (path === "/api/imports") return [importRow(5, "pending"), importRow(4, "committed")];
      if (path === "/api/imports/5/preview") return pending(5, "Mixer");
      throw new Error(`unexpected GET ${path}`);
    });
    const { user } = renderUpload();
    const card = (await screen.findByText("Mixer.csv")).closest("[data-testid=preview-card]") as HTMLElement;
    expect(screen.getAllByTestId("preview-card")).toHaveLength(1);
    vi.mocked(apiSend).mockResolvedValueOnce(summary);
    await user.click(within(card).getByRole("button", { name: "Commit" }));
    expect(apiSend).toHaveBeenCalledWith("POST", "/api/imports/5/commit", expect.objectContaining({ name: "Mixer" }));
    expect(await within(card).findByText("38 rows imported")).toBeInTheDocument();
  });

  describe("a pending import that no longer loads", () => {
    const COPY = "Could not load this pending import. Try again, or discard it and upload the file again.";
    const oldRow = { ...importRow(9, "pending"), file_name: "Old.csv" };

    function mockServer(previewOk: { current: boolean }, listed: { current: boolean } = { current: true }) {
      vi.mocked(apiGet).mockImplementation(async (path) => {
        if (path === "/api/imports") return listed.current ? [oldRow] : [];
        if (path === "/api/imports/9/preview") {
          if (previewOk.current) return { ...pending(9, "Old") };
          throw new ApiError(422, "unknown_format", "Unknown format.");
        }
        throw new Error(`unexpected GET ${path}`);
      });
    }

    it("shows the file name with Try again and Discard", async () => {
      mockServer({ current: false });
      renderUpload();
      expect(await screen.findByText("Old.csv")).toBeInTheDocument();
      expect(screen.getByText(COPY)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Discard" })).toBeInTheDocument();
      expect(screen.queryByText(/Reload the page to try again/)).not.toBeInTheDocument();
    });

    it("discards it and drops the card once the history no longer lists it", async () => {
      const listed = { current: true };
      mockServer({ current: false }, listed);
      const { user } = renderUpload();
      await screen.findByText("Old.csv");
      vi.mocked(apiSend).mockImplementationOnce(async () => {
        listed.current = false;
      });
      await user.click(screen.getByRole("button", { name: "Discard" }));
      expect(apiSend).toHaveBeenCalledWith("DELETE", "/api/imports/9");
      await waitFor(() => expect(screen.queryByText("Old.csv")).not.toBeInTheDocument());
    });

    it("shows the server's message and keeps the card when the discard fails", async () => {
      mockServer({ current: false });
      const { user } = renderUpload();
      await screen.findByText("Old.csv");
      vi.mocked(apiSend).mockRejectedValueOnce(new ApiError(500, "server_error", "Could not discard."));
      await user.click(screen.getByRole("button", { name: "Discard" }));
      expect(await screen.findByText("Could not discard.")).toBeInTheDocument();
      expect(screen.getByText("Old.csv")).toBeInTheDocument();
    });

    it("replaces the card with the preview when Try again succeeds", async () => {
      const ok = { current: false };
      mockServer(ok);
      const { user } = renderUpload();
      await screen.findByText(COPY);
      ok.current = true;
      await user.click(screen.getByRole("button", { name: "Try again" }));
      const card = (await screen.findByText("Old.csv")).closest("[data-testid=preview-card]");
      expect(card).not.toBeNull();
      expect(screen.queryByText(COPY)).not.toBeInTheDocument();
    });

    it("keeps the card when Try again fails again", async () => {
      mockServer({ current: false });
      const { user } = renderUpload();
      await screen.findByText(COPY);
      await user.click(screen.getByRole("button", { name: "Try again" }));
      await waitFor(() => expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled());
      expect(screen.getByText(COPY)).toBeInTheDocument();
    });
  });

  it("keeps typed edits and a commit summary when the user leaves and comes back", async () => {
    vi.mocked(apiUpload).mockResolvedValueOnce({ files: [pending(5, "Mixer"), pending(6, "Panel")] });
    const { router, user } = renderUpload();
    await user.upload(document.querySelector("input[type=file]") as HTMLInputElement, [csv("a.csv"), csv("b.csv")]);
    const cardA = (await screen.findByText("Mixer.csv")).closest("[data-testid=preview-card]") as HTMLElement;
    const cardB = screen.getByText("Panel.csv").closest("[data-testid=preview-card]") as HTMLElement;
    await user.type(within(cardB).getByLabelText(/Event name/), " edited");
    vi.mocked(apiSend).mockResolvedValueOnce(summary);
    await user.click(within(cardA).getByRole("button", { name: "Commit" }));
    await within(cardA).findByText("38 rows imported");

    await act(() => router.navigate("/chat"));
    expect(screen.queryByText("Panel.csv")).not.toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: "Back to upload" }));

    const backB = (await screen.findByText("Panel.csv")).closest("[data-testid=preview-card]") as HTMLElement;
    expect(within(backB).getByLabelText(/Event name/)).toHaveValue("Panel edited");
    const backA = screen.getByText("Mixer.csv").closest("[data-testid=preview-card]") as HTMLElement;
    expect(within(backA).getByText("38 rows imported")).toBeInTheDocument();
  });
});
