import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import DownloadIcon from "@mui/icons-material/Download";
import { useMutation } from "@tanstack/react-query";
import { apiDownload } from "../../api/client";
import type { QueryResultOut, TurnOut } from "../../api/types";
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

function rowsLabel(n: number) {
  return n === 1 ? "1 row" : `${n} rows`;
}

export default function AnswerCard({ turn, result, onShowResults, showResultsPending, rerun, resultsError }: Props) {
  const v = view(turn);
  const rowCount = result?.row_count ?? v.rowCount;
  const reading = [v.interpretation, ...v.assumptions].filter((line): line is string => !!line);
  const download = useMutation({
    mutationFn: (format: "xlsx" | "csv") => apiDownload(`/api/chat/turns/${v.id}/export?format=${format}`),
  });

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={2}>
          {isLive(turn) && turn.status === "streaming" && <StepIndicator step={turn.step} />}

          {v.analysis && (
            <Box>
              {v.llmAnalysis && (
                <Typography variant="caption" color="text.secondary">
                  AI-generated summary. Check it against the table.
                </Typography>
              )}
              <Typography sx={{ whiteSpace: "pre-wrap" }}>{v.analysis}</Typography>
            </Box>
          )}

          {result && (
            <Stack spacing={1}>
              {rerun && <Typography variant="subtitle2">Re-run on current data</Typography>}
              <ResultGrid result={result} />
              {result.truncated && (
                <Alert severity="info">
                  Showing the first {result.row_count} rows. Export to get all rows.
                </Alert>
              )}
            </Stack>
          )}
          {!result && !isLive(turn) && onShowResults && (
            <Box>
              <Button variant="outlined" size="small" disabled={showResultsPending} onClick={onShowResults}>
                {showResultsPending ? "Loading results…" : "Show results"}
              </Button>
            </Box>
          )}
          {resultsError && <Alert severity="error">{resultsError}</Alert>}

          {reading.length > 0 && (
            <Box>
              <Typography variant="subtitle2">How I read your question</Typography>
              <Box component="ul" sx={{ my: 0, pl: 3 }}>
                {reading.map((line, i) => (
                  <Typography component="li" variant="body2" key={i}>
                    {line}
                  </Typography>
                ))}
              </Box>
            </Box>
          )}

          {v.sql !== null && <SqlAccordion sql={v.sql} />}

          {(rowCount !== null || v.id !== null) && (
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
              {rowCount !== null && (
                <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>
                  {rowsLabel(rowCount)}
                </Typography>
              )}
              {v.id !== null && (
                <>
                  <Typography variant="body2">Export</Typography>
                  {(["xlsx", "csv"] as const).map((format) => (
                    <Button
                      key={format}
                      size="small"
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      sx={{ textTransform: "none" }}
                      disabled={download.isPending}
                      onClick={() => download.mutate(format)}
                    >
                      .{format}
                    </Button>
                  ))}
                </>
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
        </Stack>
      </CardContent>
    </Card>
  );
}
