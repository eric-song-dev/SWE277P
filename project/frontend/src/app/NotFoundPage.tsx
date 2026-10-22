import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { Link } from "react-router";
import Page from "./Page";

// The catch-all child route: an unknown address shows this inside the shell, so the nav stays.
export default function NotFoundPage() {
  return (
    <Page title="Page not found">
      <Box sx={{ p: "28px 40px", display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 2 }}>
        <Typography>There is no page at this address.</Typography>
        <Button component={Link} to="/chat" variant="contained">
          Go to Chat
        </Button>
      </Box>
    </Page>
  );
}
