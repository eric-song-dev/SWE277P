import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import InputBase from "@mui/material/InputBase";
import Typography from "@mui/material/Typography";
import { useState, type ReactNode } from "react";
import { tokens } from "../../app/theme";

// The backend's MessageIn limit, applied to the trimmed question.
const MAX_LENGTH = 2000;

interface Props {
  disabled: boolean;
  // Returns false when the question was not accepted, which keeps the text in the box.
  onSend: (question: string) => boolean;
  // Shown at the left of the row under the textarea; Send is at its right.
  toolbar?: ReactNode;
}

export default function Composer({ disabled, onSend, toolbar }: Props) {
  const [text, setText] = useState("");
  const question = text.trim();
  const tooLong = question.length > MAX_LENGTH;
  const canSend = !disabled && question !== "" && !tooLong;

  function submit() {
    if (!canSend) return;
    if (onSend(question)) setText("");
  }

  return (
    <Box sx={{ width: "100%" }}>
      <Box
        data-testid="question-box"
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: "10px",
          bgcolor: "#FFFFFF",
          border: `1px solid ${tokens.control}`,
          borderRadius: "12px",
          p: "12px 12px 10px 16px",
          "&:focus-within": {
            outline: `2px solid ${tokens.primary}`,
            outlineOffset: "2px",
          },
        }}
      >
        <InputBase
          multiline
          minRows={2}
          maxRows={8}
          fullWidth
          placeholder="Ask a question about your data"
          value={text}
          disabled={disabled}
          error={tooLong}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            // Shift+Enter keeps the newline; Enter while an IME is composing picks a candidate.
            if (e.key !== "Enter" || e.shiftKey || e.nativeEvent.isComposing)
              return;
            e.preventDefault();
            submit();
          }}
          sx={{
            p: 0,
            lineHeight: 1.5,
            color: tokens.ink,
            overflowWrap: "anywhere",
          }}
          slotProps={{
            input: { "aria-label": "Question", style: { resize: "none" } },
          }}
        />
        {tooLong && (
          <Typography role="alert" sx={{ fontSize: 14, color: "error.main" }}>
            {`${question.length.toLocaleString("en-US")} / ${MAX_LENGTH.toLocaleString("en-US")} characters. Shorten your question.`}
          </Typography>
        )}
        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "10px 16px",
          }}
        >
          <Box sx={{ flex: "1 1 auto", minWidth: 0 }}>{toolbar}</Box>
          <Button
            variant="contained"
            onClick={submit}
            disabled={!canSend}
            sx={{ flexShrink: 0, px: "22px" }}
          >
            Send
          </Button>
        </Box>
      </Box>
      <Typography
        sx={{
          mt: "8px",
          textAlign: "center",
          fontSize: 13,
          color: tokens.muted,
        }}
      >
        AI can make mistakes. Double-check important answers.
      </Typography>
    </Box>
  );
}
