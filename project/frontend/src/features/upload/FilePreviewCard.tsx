import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Link as RouterLink } from "react-router";
import type { CommitSummary, ImportPreview } from "../../api/types";
import CommitSummaryView from "./CommitSummaryView";
import EventDetailsForm from "./EventDetailsForm";
import { useDiscardImport } from "./useImports";

// Every flag code in spec section 6, worded like the dataset's attendance source notes.
const FLAG_LABELS: Record<string, string> = {
  missing_identity: "Email/NetID unavailable",
  missing_netid: "NetID missing",
  missing_email: "Email missing",
  missing_school: "School missing",
  missing_department: "Department missing",
  missing_affiliation: "Affiliation missing",
  missing_domestic_international: "Domestic/international missing",
  missing_degree: "Degree missing",
  non_standard_email: "Non-standard email, NetID not derived",
  netid_email_conflict: "NetID/email conflict",
  email_owned_by_other: "Email belongs to another person",
  duplicate_in_event: "Duplicate in this event",
  not_attended_skipped: "Skipped, not attended",
};

const SKIP_REASONS: Record<string, string> = {
  not_attended: "Not marked as attended",
};

const STATUS_CHIPS = {
  pending: { label: "Ready to commit", color: "primary" },
  duplicate: { label: "Duplicate", color: "warning" },
  rejected: { label: "Rejected", color: "error" },
} as const;

interface Props {
  preview: ImportPreview;
  onRemove: () => void;
}

function missingColumns(preview: ImportPreview): string[] {
  const missing = preview.error?.details?.missing;
  return Array.isArray(missing) ? missing.map(String) : [];
}

export default function FilePreviewCard({ preview, onRemove }: Props) {
  const discard = useDiscardImport();
  const [summary, setSummary] = useState<CommitSummary | null>(null);
  const chip = STATUS_CHIPS[preview.status];
  const missing = missingColumns(preview);

  function handleDiscard() {
    if (preview.id === null) return;
    discard.mutate(preview.id, { onSuccess: onRemove });
  }

  return (
    <Card variant="outlined" data-testid="preview-card">
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <Typography variant="subtitle1" component="h2" sx={{ flexGrow: 1 }}>
              {preview.file_name}
            </Typography>
            <Chip size="small" label={summary ? "Committed" : chip.label} color={summary ? "success" : chip.color} />
          </Stack>

          {preview.status === "duplicate" && (
            <Stack spacing={0.5}>
              <Typography>Already imported</Typography>
              <Link component={RouterLink} to="/dataset">
                View it on the Dataset page
              </Link>
            </Stack>
          )}

          {preview.status === "rejected" && preview.error && (
            <Stack spacing={0.5}>
              <Typography color="error">{preview.error.message}</Typography>
              {missing.length > 0 && <Typography>Missing columns: {missing.join(", ")}</Typography>}
            </Stack>
          )}

          {preview.status === "pending" && summary && <CommitSummaryView summary={summary} />}

          {preview.status === "pending" && !summary && preview.id !== null && preview.event_draft && (
            <>
              <Stack spacing={1}>
                <Stack direction="row" spacing={1}>
                  <Typography sx={{ fontWeight: "bold" }}>{preview.source_display}</Typography>
                  <Typography>{preview.row_count} rows</Typography>
                </Stack>
                {preview.skipped.length > 0 && (
                  <details>
                    <summary>{preview.skipped.length} rows skipped</summary>
                    <ul>
                      {preview.skipped.map((row) => (
                        <li key={row.source_row}>
                          Row {row.source_row}: {SKIP_REASONS[row.reason] ?? row.reason}
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
                <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                  {Object.entries(preview.flag_counts).map(([code, count]) => (
                    <Chip key={code} size="small" variant="outlined" label={`${FLAG_LABELS[code] ?? code}: ${count}`} />
                  ))}
                </Stack>
              </Stack>
              <EventDetailsForm importId={preview.id} draft={preview.event_draft} onCommitted={setSummary} />
              {discard.isError && <Alert severity="error">{discard.error.message}</Alert>}
              <Button
                color="inherit"
                onClick={handleDiscard}
                disabled={discard.isPending}
                sx={{ alignSelf: "flex-start" }}
              >
                Discard
              </Button>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
