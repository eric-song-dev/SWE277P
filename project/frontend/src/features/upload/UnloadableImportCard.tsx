import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { tokens } from "../../app/theme";
import { useDiscardImport } from "./useImports";

interface Props {
  importId: number;
  fileName: string;
  // May return a promise (a refetch); the card shows itself as busy until it settles.
  onRetry: () => void | Promise<unknown>;
}

// A pending import the server still holds whose preview cannot be loaded: it can be retried or discarded.
export default function UnloadableImportCard({ importId, fileName, onRetry }: Props) {
  const discard = useDiscardImport();
  const [retrying, setRetrying] = useState(false);

  async function handleRetry() {
    setRetrying(true);
    try {
      await onRetry();
    } finally {
      setRetrying(false);
    }
  }

  return (
    <Card variant="outlined" data-testid="unloadable-card">
      <CardContent sx={{ p: 3, "&:last-child": { pb: 3 } }}>
        <Stack spacing={2}>
          <Typography variant="subtitle1" component="h2" sx={{ fontWeight: 700, color: tokens.navy }}>
            {fileName}
          </Typography>
          <Typography color="error">
            Could not load this pending import. Try again, or discard it and upload the file again.
          </Typography>
          {discard.isError && <Alert severity="error">{discard.error.message}</Alert>}
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              onClick={handleRetry}
              disabled={retrying || discard.isPending}
              sx={{ borderColor: tokens.control }}
            >
              Try again
            </Button>
            <Button
              variant="outlined"
              color="inherit"
              onClick={() => discard.mutate(importId)}
              disabled={retrying || discard.isPending}
              sx={{ borderColor: tokens.control }}
            >
              Discard
            </Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  );
}
