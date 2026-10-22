import Box from "@mui/material/Box";
import type { ReactNode } from "react";
import PageHeader from "./PageHeader";

// A page inside the shell: the header bar stays put and only the body below it scrolls, as on Chat.
export default function Page({ title, actions, children }: { title: string; actions?: ReactNode; children: ReactNode }) {
  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <PageHeader title={title} actions={actions} />
      <Box data-page-body sx={{ flex: 1, minHeight: 0, overflowY: "auto", overscrollBehavior: "contain" }}>
        {children}
      </Box>
    </Box>
  );
}
