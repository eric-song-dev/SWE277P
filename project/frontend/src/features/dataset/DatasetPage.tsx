import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useState } from "react";
import { Link as RouterLink } from "react-router";
import { ApiError, apiDownload } from "../../api/client";
import type { ImportFileOut } from "../../api/types";
import { useImportHistory } from "../upload/useImports";

const PLATFORMS: Record<string, string> = { campusgroups: "CampusGroups", twelvetwenty: "12twenty" };
const STATUSES: Record<string, string> = { committed: "Committed", pending: "Pending" };

const columns: GridColDef<ImportFileOut>[] = [
  { field: "file_name", headerName: "File", flex: 1.5, minWidth: 160 },
  { field: "event", headerName: "Event", flex: 1.5, minWidth: 160, valueGetter: (_, row) => row.event?.name ?? "" },
  { field: "term", headerName: "Term", width: 120, valueGetter: (_, row) => row.event?.term ?? "" },
  {
    field: "source",
    headerName: "Platform",
    width: 130,
    valueGetter: (_, row) => PLATFORMS[row.source] ?? row.source,
  },
  { field: "row_count", headerName: "Rows", type: "number", width: 90 },
  { field: "flag_count", headerName: "Flags", type: "number", width: 90 },
  { field: "uploaded_by", headerName: "Uploaded by", flex: 1, minWidth: 140, valueGetter: (_, row) => row.uploaded_by.display_name },
  {
    field: "uploaded_at",
    headerName: "Uploaded at",
    type: "dateTime",
    width: 180,
    // A Date, so the column sorts by time; only the display is localized.
    valueGetter: (_, row) => new Date(row.uploaded_at),
    valueFormatter: (value: Date) => value.toLocaleString(),
  },
  {
    field: "status",
    headerName: "Status",
    width: 110,
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
    <Stack spacing={2}>
      <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
        <Typography variant="h5" component="h1" sx={{ flexGrow: 1 }}>
          Dataset
        </Typography>
        <Button variant="contained" disabled={downloading} onClick={() => download("xlsx")}>
          Download full dataset (.xlsx)
        </Button>
        <Button variant="outlined" disabled={downloading} onClick={() => download("csv")}>
          Download full dataset (.csv)
        </Button>
      </Stack>
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
          />
        </Box>
      )}
    </Stack>
  );
}
