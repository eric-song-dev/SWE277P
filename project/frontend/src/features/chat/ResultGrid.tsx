import Box from "@mui/material/Box";
import { DataGrid, type GridColDef } from "@mui/x-data-grid";
import { useMemo } from "react";
import type { QueryResultOut } from "../../api/types";
import { gridSx } from "../../app/theme";

// Shown as-is, except objects and booleans, which React would not render.
function cell(value: unknown) {
  if (value === null || typeof value === "number" || typeof value === "string") return value;
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}

// A column is numeric when it has a value and every non-null value is a number. Values are shown
// as they are (no thousands separators), so this only sets alignment and tabular figures.
// oxlint-disable-next-line react/only-export-components -- pure helper, tested on its own
export function columnsFor(result: QueryResultOut): GridColDef[] {
  // Index-based fields: column names can repeat or contain dots.
  return result.columns.map((name, i) => {
    const values = result.rows.map((row) => row[i]).filter((v) => v !== null && v !== undefined);
    const numeric = values.length > 0 && values.every((v) => typeof v === "number");
    return {
      field: `c${i}`,
      headerName: name,
      flex: 1,
      minWidth: 120,
      ...(numeric ? { align: "right", headerAlign: "right", cellClassName: "hub-numeric-cell" } : {}),
    } satisfies GridColDef;
  });
}

export default function ResultGrid({ result }: { result: QueryResultOut }) {
  const columns = useMemo(() => columnsFor(result), [result]);
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
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        maxHeight: 440,
        "& .hub-numeric-cell": { fontVariantNumeric: "tabular-nums" },
      }}
    >
      <DataGrid
        rows={rows}
        columns={columns}
        density="compact"
        pageSizeOptions={[100]}
        initialState={{ pagination: { paginationModel: { pageSize: 100 } } }}
        disableRowSelectionOnClick
        sx={gridSx}
      />
    </Box>
  );
}
