import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";

// The root route's error element: a render error, or a page chunk that no longer exists because
// the app was rebuilt while this tab was open. A reload fetches the current build.
export default function RouteError() {
  return (
    <Box sx={{ p: 3 }}>
      <Alert
        severity="error"
        action={
          <Button color="inherit" size="small" onClick={() => window.location.reload()}>
            Reload
          </Button>
        }
      >
        Something went wrong. Reload the page to continue.
      </Alert>
    </Box>
  );
}
