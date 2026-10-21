import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useMutation } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { apiGet } from "../../api/client";
import type { QueryResultOut, TurnOut } from "../../api/types";
import AnswerCard from "./AnswerCard";
import type { LiveTurn } from "./chatStream";

interface Props {
  turns: TurnOut[];
  live: LiveTurn | null;
  resultsByTurnId: Record<number, QueryResultOut>;
  busy: boolean;
  onRetryLive: () => void;
  onResend: (question: string) => void;
}

export default function Thread({ turns, live, resultsByTurnId, busy, onRetryLive, onResend }: Props) {
  const saved = [...turns].sort((a, b) => a.seq - b.seq);
  // The live turn replaces its saved copy (it has the rows and the full error message).
  const liveIsSaved = live !== null && saved.some((turn) => turn.id === live.turnId);
  // Keyed by seq, so the live card keeps its state when its saved copy arrives at the same seq.
  const nextSeq = (saved.at(-1)?.seq ?? 0) + 1;

  return (
    <Stack spacing={3}>
      {saved.map((turn) =>
        live !== null && turn.id === live.turnId ? (
          <TurnItem key={turn.seq} turn={live} busy={busy} onRetry={onRetryLive} />
        ) : (
          <TurnItem
            key={turn.seq}
            turn={turn}
            result={resultsByTurnId[turn.id]}
            busy={busy}
            onRetry={() => onResend(turn.question)}
          />
        ),
      )}
      {live !== null && !liveIsSaved && <TurnItem key={nextSeq} turn={live} busy={busy} onRetry={onRetryLive} />}
    </Stack>
  );
}

function TurnItem({
  turn,
  result,
  busy,
  onRetry,
}: {
  turn: TurnOut | LiveTurn;
  result?: QueryResultOut;
  busy: boolean;
  onRetry: () => void;
}) {
  const rerun = useMutation({
    mutationFn: (id: number) => apiGet<QueryResultOut>(`/api/chat/turns/${id}/rerun`),
  });

  let error: string | undefined;
  let clarification: string | null | undefined;
  if ("status" in turn) {
    error = turn.status === "error" ? (turn.error?.message ?? "Something went wrong. Retry.") : undefined;
    clarification = turn.clarification;
  } else {
    // TurnOut keeps only the code, not the message.
    error = turn.kind === "error" ? `This question could not be answered (${turn.error_code}).` : undefined;
    clarification = turn.kind === "clarification" ? turn.clarification_question : undefined;
  }

  let answer: ReactNode;
  if (error) {
    answer = (
      <Alert
        severity="error"
        action={
          <Button color="inherit" size="small" disabled={busy} onClick={onRetry}>
            Retry
          </Button>
        }
      >
        {error}
      </Alert>
    );
  } else if (clarification) {
    answer = <Bubble from="assistant">{clarification}</Bubble>;
  } else if ("status" in turn) {
    answer = <AnswerCard turn={turn} result={turn.result} />;
  } else {
    // Saved answers have no rows; re-run the logged SQL on request.
    answer = (
      <AnswerCard
        turn={turn}
        result={result ?? rerun.data}
        rerun={result === undefined && rerun.isSuccess}
        onShowResults={() => {
          if (!rerun.isPending) rerun.mutate(turn.id);
        }}
        resultsError={rerun.error?.message}
      />
    );
  }

  return (
    <Stack spacing={1}>
      <Bubble from="user">{turn.question}</Bubble>
      {answer}
    </Stack>
  );
}

function Bubble({ from, children }: { from: "user" | "assistant"; children: ReactNode }) {
  const mine = from === "user";
  return (
    <Box
      sx={{
        alignSelf: mine ? "flex-end" : "flex-start",
        maxWidth: "80%",
        px: 2,
        py: 1,
        borderRadius: 2,
        bgcolor: mine ? "primary.main" : "action.hover",
        color: mine ? "primary.contrastText" : "text.primary",
      }}
    >
      <Typography sx={{ whiteSpace: "pre-wrap" }}>{children}</Typography>
    </Box>
  );
}
