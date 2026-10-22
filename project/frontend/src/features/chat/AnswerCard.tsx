import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import DownloadIcon from "@mui/icons-material/Download";
import { useMutation } from "@tanstack/react-query";
import { apiDownload } from "../../api/client";
import type { QueryResultOut, TurnOut } from "../../api/types";
import { tokens } from "../../app/theme";
import type { LiveTurn } from "./chatStream";
import ResultGrid from "./ResultGrid";
import SqlAccordion from "./SqlAccordion";
import StepIndicator from "./StepIndicator";

interface Props {
  turn: TurnOut | LiveTurn;
  result?: QueryResultOut;
  onShowResults?: () => void;
  showResultsPending?: boolean;
  rerun?: boolean;
  // Why "Show results" failed, from the caller's re-run request.
  resultsError?: string;
}

function isLive(turn: TurnOut | LiveTurn): turn is LiveTurn {
  return "status" in turn;
}

// One shape for a saved turn and a streaming one.
function view(turn: TurnOut | LiveTurn) {
  if (isLive(turn)) {
    return {
      id: typeof turn.turnId === "number" ? turn.turnId : null,
      sql: turn.sql?.sql ?? null,
      interpretation: turn.sql?.interpretation ?? null,
      assumptions: turn.sql?.assumptions ?? [],
      analysis: turn.analysisText,
      // Only an LLM analysis streams deltas, so text before the final event is the LLM's.
      llmAnalysis: turn.analysis ? turn.analysis.source === "llm" : turn.analysisText !== "",
      rowCount: null,
    };
  }
  return {
    id: turn.id,
    sql: turn.sql,
    interpretation: turn.interpretation,
    assumptions: turn.assumptions ?? [],
    analysis: turn.analysis_text ?? "",
    llmAnalysis: turn.analysis_source === "llm",
    rowCount: turn.row_count,
  };
}

// Outlined buttons use the control border and ink text from the design doc.
const outlinedSx = {
  borderColor: tokens.control,
  color: tokens.ink,
  "&:hover": { borderColor: tokens.primary, bgcolor: tokens.subtle },
} as const;

function rowsLabel(n: number, truncated: boolean) {
  const count = n.toLocaleString("en-US");
  if (truncated) return `More than ${count} rows`;
  return n === 1 ? "1 row" : `${count} rows`;
}

export default function AnswerCard({ turn, result, onShowResults, showResultsPending, rerun, resultsError }: Props) {
  const v = view(turn);
  const rowCount = result?.row_count ?? v.rowCount;
  const truncated = result?.truncated ?? (isLive(turn) ? false : turn.truncated);
  const reading = [v.interpretation, ...v.assumptions].filter((line): line is string => !!line);
  const download = useMutation({
    mutationFn: (format: "xlsx" | "csv") => apiDownload(`/api/chat/turns/${v.id}/export?format=${format}`),
  });

  return (
    <Box
      component="article"
      sx={{
        bgcolor: "#FFFFFF",
        border: `1px solid ${tokens.border}`,
        borderRadius: "12px",
        p: 3,
        display: "flex",
        flexDirection: "column",
        gap: "20px",
        minWidth: 0,
      }}
    >
      {isLive(turn) && turn.status === "streaming" && <StepIndicator step={turn.step} />}

      {v.analysis && (
        <Box>
          {/* Every summary carries a caution: the AI wrote it, or the AI wrote the query behind it. */}
          <Typography sx={{ fontSize: 13, color: tokens.muted }}>
            {v.llmAnalysis
              ? "AI-generated summary. Check it against the table."
              : "The AI wrote the SQL, so check it."}
          </Typography>
          <Typography sx={{ fontSize: 18, lineHeight: 1.45, mt: "4px", whiteSpace: "pre-wrap" }}>
            {v.analysis}
          </Typography>
        </Box>
      )}

      {result && (
        <Stack spacing={1}>
          {rerun && <Typography sx={{ fontSize: 15, fontWeight: 600, color: tokens.muted }}>Re-run on current data</Typography>}
          <ResultGrid result={result} />
          {result.truncated && (
            <Alert severity="info">Showing the first {result.row_count.toLocaleString("en-US")} rows. Download the file to get all rows.</Alert>
          )}
        </Stack>
      )}
      {!result && !isLive(turn) && onShowResults && (
        <Box>
          <Button variant="outlined" disabled={showResultsPending} onClick={onShowResults} sx={outlinedSx}>
            {showResultsPending ? "Loading results…" : "Show results"}
          </Button>
        </Box>
      )}
      {resultsError && <Alert severity="error">{resultsError}</Alert>}

      {reading.length > 0 && (
        <Box>
          <Typography component="h2" sx={{ m: 0, mb: "4px", fontSize: 16, fontWeight: 700, color: tokens.navy }}>
            How I read your question
          </Typography>
          <Box component="ul" sx={{ my: 0, pl: "20px" }}>
            {reading.map((line, i) => (
              <Typography component="li" key={i}>
                {line}
              </Typography>
            ))}
          </Box>
        </Box>
      )}

      {v.sql !== null && <SqlAccordion sql={v.sql} />}

      {(rowCount !== null || v.id !== null) && (
        <Stack
          direction="row"
          sx={{
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
            pt: 2,
            borderTop: `1px solid ${tokens.divider}`,
          }}
        >
          <Typography sx={{ color: tokens.muted }}>{rowCount !== null ? rowsLabel(rowCount, truncated) : ""}</Typography>
          {v.id !== null && (
            <Stack direction="row" sx={{ flexWrap: "wrap", gap: 1 }}>
              <Button
                variant="contained"
                disableElevation
                startIcon={<DownloadIcon />}
                disabled={download.isPending}
                onClick={() => download.mutate("xlsx")}
              >
                Download Excel (.xlsx)
              </Button>
              <Button
                variant="outlined"
                startIcon={<DownloadIcon />}
                disabled={download.isPending}
                onClick={() => download.mutate("csv")}
                sx={outlinedSx}
              >
                Download CSV (.csv)
              </Button>
            </Stack>
          )}
        </Stack>
      )}
      {download.data?.truncated && (
        <Alert severity="info">
          {download.data.rowCap === null
            ? "This file does not include every row."
            : `This file stops at ${download.data.rowCap.toLocaleString("en-US")} rows.`}
        </Alert>
      )}
      {download.isError && <Alert severity="error">{download.error.message}</Alert>}
    </Box>
  );
}
