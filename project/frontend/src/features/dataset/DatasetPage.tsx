import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import DownloadIcon from "@mui/icons-material/Download";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useState } from "react";
import { Link as RouterLink } from "react-router";
import { ApiError, apiDownload } from "../../api/client";
import type { ImportFileOut } from "../../api/types";
import PageHeader from "../../app/PageHeader";
import { gridSx, tokens } from "../../app/theme";
import { useImportHistory } from "../upload/useImports";

const PLATFORMS: Record<string, string> = { campusgroups: "CampusGroups", twelvetwenty: "12twenty" };
const STATUSES: Record<string, string> = { committed: "Committed", pending: "Pending" };

// Long values truncate with an ellipsis; the title keeps the full text available.
const titled = ({ formattedValue }: { formattedValue?: unknown }) => (
  <Box
    component="span"
    title={String(formattedValue ?? "")}
    sx={{ display: "block", minWidth: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
  >
    {String(formattedValue ?? "")}
  </Box>
);

const columns: GridColDef<ImportFileOut>[] = [
  { field: "file_name", headerName: "File", flex: 2, minWidth: 120, renderCell: titled },
  {
    field: "event",
    headerName: "Event",
    flex: 2,
    minWidth: 120,
    valueGetter: (_, row) => row.event?.name ?? "",
    renderCell: titled,
  },
  { field: "term", headerName: "Term", width: 90, valueGetter: (_, row) => row.event?.term ?? "" },
  {
    field: "source",
    headerName: "Platform",
    width: 120,
    valueGetter: (_, row) => PLATFORMS[row.source] ?? row.source,
  },
  {
    field: "row_count",
    headerName: "Rows",
    type: "number",
    width: 88,
    disableColumnMenu: true,
    valueGetter: (_, row) => row.imported_rows ?? row.row_count,
  },
  { field: "flag_count", headerName: "Flags", type: "number", width: 88, disableColumnMenu: true },
  {
    field: "uploaded_by",
    headerName: "Uploaded by",
    flex: 1,
    minWidth: 100,
    valueGetter: (_, row) => row.uploaded_by.display_name,
    renderCell: titled,
  },
  {
    field: "uploaded_at",
    headerName: "Uploaded at",
    type: "dateTime",
    width: 170,
    // A Date, so the column sorts by time; only the display is localized.
    valueGetter: (_, row) => new Date(row.uploaded_at),
    // No seconds, so a two-digit hour still fits; the cell's title holds the full time.
    valueFormatter: (value: Date) =>
      value.toLocaleString(undefined, {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "numeric",
        minute: "2-digit",
      }),
    renderCell: ({ row, formattedValue }) => (
      <span title={new Date(row.uploaded_at).toLocaleString()}>{String(formattedValue ?? "")}</span>
    ),
  },
  {
    field: "status",
    headerName: "Status",
    width: 100,
    valueGetter: (_, row) => STATUSES[row.status] ?? row.status,
    // A pending import is finished on the Upload page.
    renderCell: ({ row, value }) =>
      row.status === "pending" ? (
        <Link component={RouterLink} to="/upload">
          {value}
        </Link>
      ) : (
        value
      ),
  },
];

export default function DatasetPage() {
  const history = useImportHistory();
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function download(format: "xlsx" | "csv") {
    setDownloading(true);
    setError(null);
    try {
      await apiDownload(`/api/dataset/export?format=${format}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Download failed.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Dataset"
        actions={
          <>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              disabled={downloading}
              onClick={() => download("xlsx")}
            >
              Download full dataset (.xlsx)
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              disabled={downloading}
              onClick={() => download("csv")}
              sx={{ borderColor: tokens.control }}
            >
              Download full dataset (.csv)
            </Button>
          </>
        }
      />
      <Stack spacing={2} sx={{ px: "40px", py: "28px" }}>
        {error && <Alert severity="error">{error}</Alert>}
        {history.isError && <Alert severity="error">{history.error.message}</Alert>}
        {history.data && history.data.length === 0 && (
          <Stack spacing={1} sx={{ alignItems: "flex-start" }}>
            <Typography>No files imported yet.</Typography>
            <Link component={RouterLink} to="/upload">
              Upload
            </Link>
          </Stack>
        )}
        {history.data && history.data.length > 0 && (
          <Box sx={{ display: "flex", flexDirection: "column", maxHeight: 640 }}>
            <DataGrid
              rows={history.data}
              columns={columns}
              density="compact"
              pageSizeOptions={[100]}
              initialState={{ pagination: { paginationModel: { pageSize: 100 } } }}
              disableRowSelectionOnClick
              sx={gridSx}
            />
          </Box>
        )}
      </Stack>
    </>
  );
}
