import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";
import type { LlmProfileOut } from "../../api/types";

interface Props {
  profiles: LlmProfileOut[];
  value: number;
  onChange: (id: number) => void;
}

export default function ProfileSelect({ profiles, value, onChange }: Props) {
  return (
    <TextField
      select
      size="small"
      label="AI model"
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      sx={{ minWidth: 220 }}
    >
      {profiles.map((profile) => (
        <MenuItem key={profile.id} value={profile.id}>
          {profile.name}
        </MenuItem>
      ))}
    </TextField>
  );
}
