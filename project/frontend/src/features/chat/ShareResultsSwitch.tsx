import FormControl from "@mui/material/FormControl";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormHelperText from "@mui/material/FormHelperText";
import Switch from "@mui/material/Switch";
import Tooltip from "@mui/material/Tooltip";
import { useId } from "react";

interface Props {
  checked: boolean;
  // The profile's share_results_with_llm: the ceiling for this switch.
  allowed: boolean;
  onChange: (checked: boolean) => void;
}

export default function ShareResultsSwitch({ checked, allowed, onChange }: Props) {
  const helperId = useId();
  const control = (
    <FormControlLabel
      label="Let AI see the results"
      control={
        <Switch
          checked={allowed && checked}
          disabled={!allowed}
          onChange={(e) => onChange(e.target.checked)}
          slotProps={{ input: { "aria-describedby": helperId } }}
        />
      }
    />
  );

  return (
    <FormControl sx={{ flexShrink: 0, maxWidth: 280 }}>
      {allowed ? (
        control
      ) : (
        // A disabled control fires no mouse events, so the tooltip needs a wrapper.
        <Tooltip title="This AI model isn't allowed to receive results. Change it in Settings.">
          <span>{control}</span>
        </Tooltip>
      )}
      <FormHelperText id={helperId} sx={{ mx: 0 }}>
        Off: AI only writes the SQL. Results stay on this computer.
      </FormHelperText>
    </FormControl>
  );
}
