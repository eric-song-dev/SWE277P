import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { tokens } from "../../app/theme";
import { stepLabel, type LiveTurn } from "./chatStream";

export default function StepIndicator({ step }: { step: LiveTurn["step"] }) {
  return (
    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }} role="status">
      <CircularProgress size={16} sx={{ color: tokens.primary }} />
      <Typography variant="body2" sx={{ color: tokens.muted }}>
        {step ? stepLabel(step) : "Sending the question"}
      </Typography>
    </Stack>
  );
}
