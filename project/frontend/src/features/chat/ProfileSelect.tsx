import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import Box from "@mui/material/Box";
import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import type { LlmProfileOut } from "../../api/types";
import { tokens } from "../../app/theme";

interface Props {
  profiles: LlmProfileOut[];
  value: number;
  onChange: (id: number) => void;
}

function Chevron({ className }: { className?: string }) {
  return <KeyboardArrowDownIcon className={className} sx={{ color: tokens.muted, right: "12px" }} />;
}

export default function ProfileSelect({ profiles, value, onChange }: Props) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
      {/* The select carries the accessible name; this is the visible label. */}
      <Typography component="span" aria-hidden="true" sx={{ fontSize: 15, fontWeight: 600, color: tokens.muted }}>
        AI model
      </Typography>
      <TextField
        select
        size="small"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        slotProps={{ select: { IconComponent: Chevron, SelectDisplayProps: { "aria-label": "AI model" } } }}
        sx={{
          minWidth: 200,
          "& .MuiOutlinedInput-root": { borderRadius: "8px", fontSize: 15, fontWeight: 600, color: tokens.ink },
          "& .MuiOutlinedInput-notchedOutline": { borderColor: tokens.control },
        }}
      >
        {profiles.map((profile) => (
          <MenuItem key={profile.id} value={profile.id}>
            {profile.name}
          </MenuItem>
        ))}
      </TextField>
    </Box>
  );
}
