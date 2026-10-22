import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";
import { tokens } from "./theme";

// The slim white bar at the top of every page, Chat included: the title on the left and the page's
// actions on the right, with 34px buttons to match Chat's model select. It is 59px tall (a 34px
// control, 12px padding and the 1px line) on every page, with or without actions and while they load.
export default function PageHeader({ title, actions }: { title: string; actions?: ReactNode }) {
  return (
    <Box
      component="header"
      sx={{
        flexShrink: 0,
        minHeight: 59,
        boxSizing: "border-box",
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px 24px",
        px: "40px",
        py: "12px",
        bgcolor: "#FFFFFF",
        borderBottom: `1px solid ${tokens.border}`,
      }}
    >
      <Typography variant="h1" sx={{ m: 0 }}>
        {title}
      </Typography>
      {actions && (
        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: 1,
            "& .MuiButton-root": { minHeight: 34, py: "4px", px: "14px", fontSize: 15, lineHeight: 1.5 },
            "& .MuiButton-startIcon": { mr: "6px" },
            "& .MuiButton-startIcon > svg": { fontSize: 18 },
          }}
        >
          {actions}
        </Box>
      )}
    </Box>
  );
}
