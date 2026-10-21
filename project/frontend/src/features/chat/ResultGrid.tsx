import Box from "@mui/material/Box";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useMemo } from "react";
import type { QueryResultOut } from "../../api/types";

// Shown as-is, except objects and booleans, which React would not render.
function cell(value: unknown) {
  if (value === null || typeof value === "number" || typeof value === "string") return value;
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

export default function ResultGrid({ result }: { result: QueryResultOut }) {
  // Index-based fields: column names can repeat or contain dots.
  const columns = useMemo<GridColDef[]>(
    () => result.columns.map((name, i) => ({ field: `c${i}`, headerName: name, flex: 1, minWidth: 120 })),
    [result.columns],
  );
  const rows = useMemo(
    () =>
      result.rows.map((row, r) => {
        const out: Record<string, unknown> = { id: r };
        row.forEach((value, i) => (out[`c${i}`] = cell(value)));
        return out;
      }),
    [result.rows],
  );

  return (
    <Box sx={{ display: "flex", flexDirection: "column", maxHeight: 440 }}>
      <DataGrid
        rows={rows}
        columns={columns}
        density="compact"
        pageSizeOptions={[100]}
        initialState={{ pagination: { paginationModel: { pageSize: 100 } } }}
        disableRowSelectionOnClick
      />
    </Box>
  );
}
