import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { CommitSummary } from "../../api/types";

const COUNTS: [keyof CommitSummary, string][] = [
  ["linked_by_netid", "Linked by NetID"],
  ["linked_by_email", "Linked by email"],
  ["new_people", "New people"],
  ["unlinked", "Unlinked"],
  ["flagged_rows", "Flagged rows"],
  ["skipped", "Skipped"],
  ["duplicates_in_event", "Duplicates in event"],
];

export default function CommitSummaryView({ summary }: { summary: CommitSummary }) {
  return (
    <Stack spacing={1}>
      <Typography variant="h6" component="p">
        {summary.inserted} rows imported
      </Typography>
      <Stack component="dl" spacing={0.5} sx={{ m: 0 }}>
        {COUNTS.map(([key, label]) => (
          <Stack key={key} direction="row" spacing={1}>
            <Typography component="dt" color="text.secondary">
              {label}
            </Typography>
            <Typography component="dd" sx={{ m: 0 }}>
              {summary[key]}
            </Typography>
          </Stack>
        ))}
      </Stack>
    </Stack>
  );
}
