import Box from "@mui/material/Box";
import Switch from "@mui/material/Switch";
import Tooltip from "@mui/material/Tooltip";
import { useId } from "react";
import { tokens } from "../../app/theme";

interface Props {
  checked: boolean;
  // The profile's share_results_with_llm: the ceiling for this switch.
  allowed: boolean;
  onChange: (checked: boolean) => void;
}

const ON_HELP =
  "On: the AI reads the results to summarize them. PII (such as emails and names) may be shared with the AI.";
const OFF_HELP =
  "Off: the AI sees only your question. You get the results without an AI summary.";

// 40x22 track, 16 px knob that shifts 18 px.
const switchSx = {
  width: 40,
  height: 22,
  p: 0,
  mt: "1px",
  flexShrink: 0,
  "& .MuiSwitch-switchBase": {
    p: "3px",
    "&.Mui-checked": { transform: "translateX(18px)", color: "#FFFFFF" },
    "&.Mui-checked + .MuiSwitch-track": { bgcolor: tokens.primary, opacity: 1 },
    "&.Mui-disabled + .MuiSwitch-track": { opacity: 0.5 },
  },
  "& .MuiSwitch-thumb": {
    width: 16,
    height: 16,
    bgcolor: "#FFFFFF",
    boxShadow: "0 1px 2px rgba(0,34,68,0.3)",
  },
  "& .MuiSwitch-track": {
    borderRadius: "11px",
    bgcolor: tokens.muted,
    opacity: 1,
  },
};

export default function ShareResultsSwitch({
  checked,
  allowed,
  onChange,
}: Props) {
  const id = useId();
  const helperId = `${id}-help`;
  const effective = allowed && checked;
  const control = (
    <Box
      sx={{
        display: "flex",
        alignItems: "flex-start",
        gap: "10px",
        minWidth: 0,
      }}
    >
      <Switch
        id={id}
        checked={effective}
        disabled={!allowed}
        onChange={(e) => onChange(e.target.checked)}
        sx={switchSx}
        slotProps={{ input: { "aria-describedby": helperId } }}
      />
      <Box sx={{ display: "flex", flexDirection: "column", minWidth: 0 }}>
        <Box
          component="label"
          htmlFor={id}
          sx={{
            fontWeight: 600,
            lineHeight: 1.5,
            cursor: allowed ? "pointer" : "default",
          }}
        >
          Let AI see the results
        </Box>
        <Box
          id={helperId}
          sx={{ fontSize: 14, lineHeight: 1.45, color: tokens.muted }}
        >
          {effective ? ON_HELP : OFF_HELP}
        </Box>
      </Box>
    </Box>
  );

  return allowed ? (
    control
  ) : (
    // A disabled control fires no mouse events, so the tooltip needs a wrapper.
    <Tooltip title="This AI model isn't allowed to receive results. Change it in Settings.">
      <span>{control}</span>
    </Tooltip>
  );
}
