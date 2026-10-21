import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

// Collapsed until opened; the SQL is not in the DOM before that.
export default function SqlAccordion({ sql }: { sql: string }) {
  function copy() {
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText(sql).catch(() => {});
  }

  return (
    <Accordion variant="outlined" disableGutters slotProps={{ transition: { unmountOnExit: true } }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>SQL</AccordionSummary>
      <AccordionDetails>
        <Box component="pre" sx={{ m: 0, mb: 1, whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 13 }}>
          {sql}
        </Box>
        <Button size="small" startIcon={<ContentCopyIcon />} onClick={copy}>
          Copy
        </Button>
      </AccordionDetails>
    </Accordion>
  );
}
