import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import type { LlmProfileOut } from "../../api/types";
import ProfileForm from "./ProfileForm";
import ProfileList from "./ProfileList";
import { useProfiles } from "./useProfiles";

export default function SettingsPage() {
  const profiles = useProfiles();
  // undefined: dialog closed; null: adding a new profile.
  const [editing, setEditing] = useState<LlmProfileOut | null | undefined>(undefined);

  return (
    <Stack spacing={2} sx={{ maxWidth: 720 }}>
      <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between" }}>
        <Typography variant="h5" component="h1">
          Settings
        </Typography>
        {profiles.data && profiles.data.length > 0 && (
          <Button variant="contained" onClick={() => setEditing(null)}>
            Add AI model
          </Button>
        )}
      </Stack>
      {profiles.isError && <Alert severity="error">Could not load your AI models.</Alert>}
      {profiles.data && profiles.data.length === 0 && (
        <Stack spacing={2} sx={{ alignItems: "flex-start" }}>
          <Typography>No AI models yet. Add one to start asking questions.</Typography>
          <Button variant="contained" onClick={() => setEditing(null)}>
            Add AI model
          </Button>
        </Stack>
      )}
      {profiles.data && profiles.data.length > 0 && (
        <ProfileList profiles={profiles.data} onEdit={setEditing} />
      )}
      {editing !== undefined && <ProfileForm profile={editing} onClose={() => setEditing(undefined)} />}
    </Stack>
  );
}
