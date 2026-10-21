import Box from "@mui/material/Box";
import ButtonBase from "@mui/material/ButtonBase";
import Button from "@mui/material/Button";
import Collapse from "@mui/material/Collapse";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useEffect, useId, useRef, useState } from "react";
import { tokens } from "../../app/theme";

// Collapsed until opened; the SQL is not in the DOM before that.
export default function SqlAccordion({ sql }: { sql: string }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();

  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle");
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);

  function flash(state: "copied" | "failed") {
    setCopyState(state);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setCopyState("idle"), 2000);
  }

  function copy() {
    if (!navigator.clipboard) return flash("failed");
    navigator.clipboard.writeText(sql).then(
      () => flash("copied"),
      () => flash("failed"),
    );
  }

  return (
    <Box>
      <ButtonBase
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
        onClick={() => setOpen((o) => !o)}
        sx={{
          display: "flex",
          justifyContent: "space-between",
          width: "100%",
          minHeight: 44,
          px: 2,
          py: "10px",
          border: `1px solid ${tokens.border}`,
          borderRadius: "10px",
          bgcolor: tokens.subtle,
          color: tokens.ink,
          fontFamily: "inherit",
          fontSize: "1rem",
          fontWeight: 600,
          textAlign: "left",
          transition: "background-color 120ms",
          "&:hover": { bgcolor: tokens.tableHead },
        }}
      >
        Show the SQL query
        <ExpandMoreIcon
          aria-hidden
          sx={{ transition: "transform 120ms", transform: open ? "rotate(180deg)" : "none" }}
        />
      </ButtonBase>
      <Collapse in={open} unmountOnExit>
        <Box id={panelId} sx={{ pt: 1.5 }}>
          <Box
            component="pre"
            sx={{
              m: 0,
              mb: 1,
              p: 1.5,
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere",
              fontFamily: "monospace",
              fontSize: 13,
              color: tokens.ink,
              bgcolor: tokens.subtle,
              border: `1px solid ${tokens.divider}`,
              borderRadius: "10px",
            }}
          >
            {sql}
          </Box>
          <Button size="small" startIcon={<ContentCopyIcon />} onClick={copy}>
            {copyState === "copied" ? "Copied" : copyState === "failed" ? "Copy failed" : "Copy"}
          </Button>
        </Box>
      </Collapse>
    </Box>
  );
}
