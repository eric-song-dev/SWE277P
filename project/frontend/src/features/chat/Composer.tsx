import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { useState } from "react";

// The backend's MessageIn limit, applied to the trimmed question.
const MAX_LENGTH = 2000;

interface Props {
  disabled: boolean;
  // Returns false when the question was not accepted, which keeps the text in the box.
  onSend: (question: string) => boolean;
}

export default function Composer({ disabled, onSend }: Props) {
  const [text, setText] = useState("");
  const question = text.trim();
  const tooLong = question.length > MAX_LENGTH;
  const canSend = !disabled && question !== "" && !tooLong;

  function submit() {
    if (!canSend) return;
    if (onSend(question)) setText("");
  }

  return (
    <Stack direction="row" spacing={1} sx={{ alignItems: "flex-start", flexGrow: 1 }}>
      <TextField
        fullWidth
        multiline
        maxRows={8}
        placeholder="Ask a question about the attendance data"
        value={text}
        disabled={disabled}
        error={tooLong}
        helperText={
          tooLong
            ? `${question.length.toLocaleString("en-US")} / ${MAX_LENGTH.toLocaleString("en-US")} characters. Shorten your question.`
            : undefined
        }
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          // Shift+Enter keeps the newline; Enter while an IME is composing picks a candidate.
          if (e.key !== "Enter" || e.shiftKey || e.nativeEvent.isComposing) return;
          e.preventDefault();
          submit();
        }}
        slotProps={{ htmlInput: { "aria-label": "Question" } }}
      />
      <Button variant="contained" onClick={submit} disabled={!canSend} sx={{ mt: 1 }}>
        Send
      </Button>
    </Stack>
  );
}
