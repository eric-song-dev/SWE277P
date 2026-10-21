import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";
import { tokens } from "./theme";

export default function PageHeader({ title, actions }: { title: string; actions?: ReactNode }) {
  return (
    <Box
      component="header"
      sx={{
        minHeight: 88,
        boxSizing: "border-box",
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px 24px",
        px: "40px",
        py: "16px",
        bgcolor: "#FFFFFF",
        borderBottom: `1px solid ${tokens.border}`,
      }}
    >
      <Typography variant="h1" sx={{ m: 0 }}>
        {title}
      </Typography>
      {actions && <Box sx={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 1.5 }}>{actions}</Box>}
    </Box>
  );
}
