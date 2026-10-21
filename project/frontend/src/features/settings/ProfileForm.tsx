import Alert from "@mui/material/Alert";
import Autocomplete from "@mui/material/Autocomplete";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormHelperText from "@mui/material/FormHelperText";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import TextField from "@mui/material/TextField";
import { useState } from "react";
import { ApiError } from "../../api/client";
import type { LlmProfileIn, LlmProfileOut, LlmProfilePatch, PresetOut } from "../../api/types";
import { tokens } from "../../app/theme";
import { usePresets, useProbeResult, useSaveProfile } from "./useProfiles";

interface Props {
  profile: LlmProfileOut | null;
  onClose: () => void;
}

export default function ProfileForm({ profile, onClose }: Props) {
  const presets = usePresets();
  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { sx: { borderRadius: "12px" } } }}>
      <DialogTitle sx={{ fontWeight: 700, color: tokens.navy }}>{profile ? "Edit AI model" : "Add AI model"}</DialogTitle>
      {presets.data ? (
        <FormBody profile={profile} presets={presets.data} onClose={onClose} />
      ) : (
        <DialogContent>
          {presets.isError ? <Alert severity="error">Could not load the providers.</Alert> : "Loading…"}
        </DialogContent>
      )}
    </Dialog>
  );
}

function FormBody({ profile, presets, onClose }: Props & { presets: PresetOut[] }) {
  const save = useSaveProfile();
  const probe = useProbeResult(profile?.id);
  const initial = presets.find((p) => p.key === profile?.preset) ?? presets[0];

  const [name, setName] = useState(profile?.name ?? "");
  const [presetKey, setPresetKey] = useState(profile?.preset ?? initial?.key ?? "");
  const [baseUrl, setBaseUrl] = useState(profile?.base_url ?? initial?.base_url ?? "");
  const [model, setModel] = useState(profile?.model ?? "");
  const [apiKey, setApiKey] = useState("");
  const [share, setShare] = useState(profile?.share_results_with_llm ?? initial?.share_results_default ?? false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const preset = presets.find((p) => p.key === presetKey);
  const isFake = presetKey === "fake";
  const needsUrl = !isFake && preset?.base_url == null;
  const valid =
    name.trim() !== "" &&
    model.trim() !== "" &&
    (!needsUrl || baseUrl.trim() !== "") &&
    (profile !== null || isFake || apiKey !== "");

  function pickPreset(key: string) {
    const next = presets.find((p) => p.key === key);
    setPresetKey(key);
    if (next?.base_url) setBaseUrl(next.base_url);
    // Drop the previous preset's default URL; a URL the user typed stays.
    else if (preset?.base_url && baseUrl === preset.base_url) setBaseUrl("");
    setShare(next?.share_results_default ?? false);
  }

  function buildBody(): LlmProfileIn | LlmProfilePatch {
    const url = isFake ? null : baseUrl.trim() || null;
    if (!profile) {
      return {
        name: name.trim(),
        preset: presetKey,
        base_url: url,
        model: model.trim(),
        ...(apiKey && !isFake ? { api_key: apiKey } : {}),
        share_results_with_llm: share,
      };
    }
    // Only changed fields: the server resets the stored test result when these change.
    const patch: LlmProfilePatch = {};
    if (name.trim() !== profile.name) patch.name = name.trim();
    if (presetKey !== profile.preset) patch.preset = presetKey;
    // The server resets base_url on a preset change unless the body carries it.
    if (url !== profile.base_url || presetKey !== profile.preset) patch.base_url = url;
    if (model.trim() !== profile.model) patch.model = model.trim();
    if (share !== profile.share_results_with_llm) patch.share_results_with_llm = share;
    if (apiKey && !isFake) patch.api_key = apiKey;
    return patch;
  }

  function submit() {
    setNameError(null);
    setFormError(null);
    save.mutate(
      { id: profile?.id, body: buildBody() },
      {
        onSuccess: onClose,
        onError: (err) => {
          if (err instanceof ApiError && err.code === "profile_name_taken") setNameError(err.message);
          else setFormError(err instanceof Error ? err.message : "Could not save the AI model.");
        },
      },
    );
  }

  const keyHelp = profile
    ? ["Leave empty to keep the saved key.", profile.api_key_hint ? `Saved key: ${profile.api_key_hint}` : null]
        .filter(Boolean)
        .join(" ")
    : undefined;

  return (
    <>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          {formError && <Alert severity="error">{formError}</Alert>}
          <TextField
            label="Name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={nameError !== null}
            helperText={nameError}
          />
          <TextField select label="Provider" value={presetKey} onChange={(e) => pickPreset(e.target.value)}>
            {presets.map((p) => (
              <MenuItem key={p.key} value={p.key}>
                {p.label}
              </MenuItem>
            ))}
          </TextField>
          {!isFake && (
            <TextField
              label="Base URL"
              required={needsUrl}
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
            />
          )}
          <Autocomplete
            freeSolo
            options={probe.data?.models ?? []}
            inputValue={model}
            onInputChange={(_, value) => setModel(value)}
            renderInput={(params) => <TextField {...params} label="Model" required />}
          />
          {!isFake && (
            <TextField
              label="API key"
              type="password"
              required={profile === null}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              helperText={keyHelp}
              slotProps={{ htmlInput: { autoComplete: "off" } }}
            />
          )}
          <div>
            <FormControlLabel
              control={<Switch checked={share} onChange={(e) => setShare(e.target.checked)} />}
              label="Allow sending query results to this AI"
            />
            <FormHelperText sx={{ ml: 0 }}>
              Lets the chat page's 'Let AI see the results' switch be turned on for this model.
            </FormHelperText>
          </div>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button variant="outlined" onClick={onClose} sx={{ borderColor: tokens.control }}>
          Cancel
        </Button>
        <Button variant="contained" onClick={submit} disabled={!valid || save.isPending}>
          Save
        </Button>
      </DialogActions>
    </>
  );
}
