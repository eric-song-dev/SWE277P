import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiDownload, apiGet } from "../../api/client";
import type { ImportFileOut } from "../../api/types";
import DatasetPage from "./DatasetPage";

// Keep the real ApiError class; automocking would blank its constructor.
vi.mock("../../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../api/client")>()),
  apiGet: vi.fn(),
  apiDownload: vi.fn(),
}));

const imports: ImportFileOut[] = [
  {
    id: 1,
    file_name: "career-fair.csv",
    source: "campusgroups",
    status: "committed",
    row_count: 38,
    skipped_count: 0,
    event: { id: 4, name: "Career Fair", term: "Fall 2026" },
    flag_count: 3,
    uploaded_by: { id: 1, display_name: "Ada Lovelace" },
    uploaded_at: "2026-10-01T17:30:00Z",
    committed_at: "2026-10-01T17:35:00Z",
  },
  {
    id: 2,
    file_name: "mixer.xlsx",
    source: "twelvetwenty",
    status: "pending",
    row_count: 12,
    skipped_count: 1,
    event: null,
    flag_count: 0,
    uploaded_by: { id: 1, display_name: "Ada Lovelace" },
    uploaded_at: "2026-10-02T17:30:00Z",
    committed_at: null,
  },
];

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <DatasetPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("DatasetPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("lists the import history", async () => {
    vi.mocked(apiGet).mockResolvedValueOnce(imports);
    renderPage();
    expect(await screen.findByText("career-fair.csv")).toBeInTheDocument();
    expect(screen.getByText("Career Fair")).toBeInTheDocument();
    expect(screen.getByText("CampusGroups")).toBeInTheDocument();
    expect(screen.getByText("12twenty")).toBeInTheDocument();
    expect(screen.getAllByText("Ada Lovelace")).toHaveLength(2);
    expect(apiGet).toHaveBeenCalledWith("/api/imports");
  });

  it("shows the status in words", async () => {
    vi.mocked(apiGet).mockResolvedValueOnce(imports);
    renderPage();
    await screen.findByText("career-fair.csv");
    const statuses = screen
      .getAllByRole("gridcell")
      .filter((cell) => cell.getAttribute("data-field") === "status")
      .map((cell) => cell.textContent);
    expect(statuses).toEqual(["Committed", "Pending"]);
  });

  it("links a Pending row to the Upload page and leaves Committed as text", async () => {
    vi.mocked(apiGet).mockResolvedValueOnce(imports);
    renderPage();
    await screen.findByText("career-fair.csv");
    expect(screen.getByRole("link", { name: "Pending" })).toHaveAttribute("href", "/upload");
    expect(screen.queryByRole("link", { name: "Committed" })).not.toBeInTheDocument();
  });

  it("sorts Uploaded at by time, not by its text", async () => {
    // As text, "10/10/2026" sorts before "10/8/2026" and "10/9/2026".
    vi.mocked(apiGet).mockResolvedValueOnce([
      { ...imports[0], uploaded_at: "2026-10-09T17:30:00Z" },
      { ...imports[1], uploaded_at: "2026-10-08T17:30:00Z" },
      { ...imports[0], id: 3, file_name: "panel.csv", uploaded_at: "2026-10-10T17:30:00Z" },
    ]);
    renderPage();
    await screen.findByText("career-fair.csv");
    await userEvent.click(within(screen.getByRole("columnheader", { name: "Uploaded at" })).getByText("Uploaded at"));
    const files = screen
      .getAllByRole("gridcell")
      .filter((cell) => cell.getAttribute("data-field") === "file_name")
      .map((cell) => cell.textContent);
    expect(files).toEqual(["mixer.xlsx", "career-fair.csv", "panel.csv"]);
    expect(screen.getByText(new Date("2026-10-08T17:30:00Z").toLocaleString())).toBeInTheDocument();
  });

  it("has a level 1 Dataset heading and download icons on both downloads", async () => {
    vi.mocked(apiGet).mockResolvedValueOnce(imports);
    renderPage();
    await screen.findByText("career-fair.csv");
    expect(screen.getByRole("heading", { level: 1, name: "Dataset" })).toBeInTheDocument();
    for (const name of ["Download full dataset (.xlsx)", "Download full dataset (.csv)"]) {
      const button = screen.getByRole("button", { name });
      expect(button.querySelector('svg[data-testid="DownloadIcon"]')).not.toBeNull();
    }
  });

  it("downloads the full dataset in either format", async () => {
    vi.mocked(apiGet).mockResolvedValueOnce(imports);
    vi.mocked(apiDownload).mockResolvedValue({ fileName: "d.xlsx", truncated: false, rowCap: null });
    renderPage();
    await screen.findByText("career-fair.csv");
    await userEvent.click(screen.getByRole("button", { name: "Download full dataset (.xlsx)" }));
    await waitFor(() => expect(apiDownload).toHaveBeenCalledWith("/api/dataset/export?format=xlsx"));
    await userEvent.click(screen.getByRole("button", { name: "Download full dataset (.csv)" }));
    await waitFor(() => expect(apiDownload).toHaveBeenCalledWith("/api/dataset/export?format=csv"));
  });

  it("shows a download error and disables both buttons while downloading", async () => {
    vi.mocked(apiGet).mockResolvedValueOnce(imports);
    let reject!: (e: Error) => void;
    vi.mocked(apiDownload).mockReturnValueOnce(new Promise((_, r) => (reject = r)));
    renderPage();
    await screen.findByText("career-fair.csv");
    await userEvent.click(screen.getByRole("button", { name: "Download full dataset (.xlsx)" }));
    expect(screen.getByRole("button", { name: "Download full dataset (.csv)" })).toBeDisabled();
    reject(new ApiError(500, "export_failed", "Export failed."));
    expect(await screen.findByText("Export failed.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download full dataset (.csv)" })).toBeEnabled();
  });

  it("links to Upload when nothing is imported", async () => {
    vi.mocked(apiGet).mockResolvedValueOnce([]);
    renderPage();
    expect(await screen.findByText("No files imported yet.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Upload" })).toHaveAttribute("href", "/upload");
  });

  it("shows the error when the history fails to load", async () => {
    vi.mocked(apiGet).mockRejectedValueOnce(new ApiError(500, "unavailable", "History unavailable."));
    renderPage();
    expect(await screen.findByText("History unavailable.")).toBeInTheDocument();
  });
});
