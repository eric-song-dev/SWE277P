import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import CardActions from "@mui/material/CardActions";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import type { LlmProfileOut } from "../../api/types";
import { tokens } from "../../app/theme";
import {
  useDeleteProfile,
  usePresets,
  useProbeProfile,
  useProbeResult,
  useSetDefault,
} from "./useProfiles";

const outlinedSx = { borderColor: tokens.control };

// The tag shows the model's result-sharing ceiling (D2) both ways, in the chat switch's words.
const SHARING = {
  on: {
    label: "AI can see results",
    help: 'This AI may read query results, such as names and emails, to summarize them. You can turn it off for a question with "Let AI see the results" in Chat.',
  },
  off: {
    label: "AI never sees results",
    help: "This AI only writes the SQL. Query results stay on this computer.",
  },
};

function SharingTag({ allowed }: { allowed: boolean }) {
  const { label, help } = allowed ? SHARING.on : SHARING.off;
  return (
    <Tooltip title={help} describeChild>
      {/* Focusable, so the explanation is reachable from the keyboard too. */}
      <Chip
        size="small"
        variant="outlined"
        label={label}
        tabIndex={0}
        sx={{ borderColor: tokens.control, color: allowed ? tokens.ink : tokens.muted }}
      />
    </Tooltip>
  );
}

interface Props {
  profiles: LlmProfileOut[];
  onEdit: (profile: LlmProfileOut) => void;
}

export default function ProfileList({ profiles, onEdit }: Props) {
  const remove = useDeleteProfile();
  const [toDelete, setToDelete] = useState<LlmProfileOut | null>(null);

  function closeDelete() {
    remove.reset();
    setToDelete(null);
  }

  return (
    <Stack spacing={2}>
      {profiles.map((profile) => (
        <ProfileCard
          key={profile.id}
          profile={profile}
          onEdit={() => onEdit(profile)}
          onDelete={() => setToDelete(profile)}
        />
      ))}
      <Dialog
        open={toDelete !== null}
        onClose={closeDelete}
        slotProps={{ paper: { sx: { borderRadius: "12px" } } }}
      >
        <DialogTitle sx={{ fontWeight: 700, color: tokens.navy }}>Delete AI model</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Delete "{toDelete?.name}"? Its saved API key is removed too.
          </DialogContentText>
          {remove.isError && <Alert severity="error" sx={{ mt: 1 }}>{remove.error.message}</Alert>}
        </DialogContent>
        <DialogActions>
          <Button variant="outlined" onClick={closeDelete} sx={outlinedSx}>
            Cancel
          </Button>
          <Button
            color="error"
            disabled={remove.isPending}
            onClick={() => {
              if (toDelete) remove.mutate(toDelete.id, { onSuccess: closeDelete });
            }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}

function ProfileCard({
  profile,
  onEdit,
  onDelete,
}: {
  profile: LlmProfileOut;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const presets = usePresets();
  const probe = useProbeProfile();
  const probeResult = useProbeResult(profile.id);
  const setDefault = useSetDefault();
  const presetLabel = presets.data?.find((p) => p.key === profile.preset)?.label ?? profile.preset;

  return (
    <Card component="article" aria-label={profile.name} variant="outlined">
      <CardContent sx={{ p: 3, pb: 1 }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: "center", mb: 1 }}>
          <Typography variant="h6" component="h2" sx={{ fontWeight: 700, color: tokens.navy }}>
            {profile.name}
          </Typography>
          {profile.is_default && (
            <Chip size="small" label="Default" sx={{ bgcolor: tokens.primary, color: "#FFFFFF", fontWeight: 600 }} />
          )}
          <SharingTag allowed={profile.share_results_with_llm} />
        </Stack>
        <Typography variant="body2">{presetLabel}</Typography>
        <Typography variant="body2">{profile.model}</Typography>
        <Typography variant="body2" color="text.secondary">
          {profile.has_api_key ? (profile.api_key_hint ?? "Key saved") : "No key saved"}
        </Typography>
        <TestStatus
          profile={profile}
          result={probeResult.data ?? null}
          error={probe.isError ? probe.error.message : null}
        />
        {setDefault.isError && <Alert severity="error" sx={{ mt: 1 }}>{setDefault.error.message}</Alert>}
      </CardContent>
      <CardActions sx={{ px: 3, pb: 2, gap: 1 }}>
        <Button
          size="small"
          variant="outlined"
          onClick={() => probe.mutate(profile.id)}
          disabled={probe.isPending}
          sx={outlinedSx}
        >
          Test
        </Button>
        <Button size="small" variant="outlined" onClick={onEdit} sx={outlinedSx}>
          Edit
        </Button>
        {!profile.is_default && (
          <Button
            size="small"
            variant="outlined"
            onClick={() => setDefault.mutate(profile.id)}
            disabled={setDefault.isPending}
            sx={outlinedSx}
          >
            Make default
          </Button>
        )}
        <Button size="small" color="error" onClick={onDelete}>
          Delete
        </Button>
      </CardActions>
    </Card>
  );
}

function TestStatus({
  profile,
  result,
  error,
}: {
  profile: LlmProfileOut;
  result: { ok: boolean; error: string | null } | null;
  error: string | null;
}) {
  if (error) return <Alert severity="error" sx={{ mt: 1 }}>{error}</Alert>;
  if (result) {
    return result.ok ? (
      <Alert severity="success" sx={{ mt: 1 }}>Connected</Alert>
    ) : (
      <Alert severity="error" sx={{ mt: 1 }}>{result.error ?? "The test failed."}</Alert>
    );
  }
  let text = "Not tested yet";
  if (profile.last_tested_at) {
    const when = new Date(profile.last_tested_at).toLocaleString();
    text = profile.last_test_ok ? `Last test passed ${when}` : `Last test failed ${when}`;
  }
  return (
    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
      {text}
    </Typography>
  );
}
