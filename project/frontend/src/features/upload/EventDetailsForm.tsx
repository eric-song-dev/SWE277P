import Alert from "@mui/material/Alert";
import Autocomplete from "@mui/material/Autocomplete";
import Button from "@mui/material/Button";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useId, useRef } from "react";
import type { SyntheticEvent } from "react";
import type { CommitSummary, EventDetailsIn, EventDraftOut } from "../../api/types";
import { useUploadStore, type EventFormValues } from "./uploadStore";
import { useCommitImport } from "./useImports";

const TERM_PATTERN = /^(Fall|Winter|Spring|Summer) [0-9]{4}$/;
const MODALITIES: EventDetailsIn["modality"][] = ["In Person", "Virtual", "Hybrid"];
const EVENT_TYPES = ["Professional Development", "Wellness/Mental Health", "Fellowships"];

interface Props {
  importId: number;
  draft: EventDraftOut;
  onCommitted: (summary: CommitSummary) => void;
}

const orNull = (value: string) => value.trim() || null;

export default function EventDetailsForm({ importId, draft, onCommitted }: Props) {
  const id = useId();
  const commit = useCommitImport();
  // Set synchronously so a fast double click cannot send twice before the button disables.
  const inFlight = useRef(false);
  // Kept in the upload store, so typed edits survive leaving the page; a reload starts from the draft.
  const { formValues, setFormValues } = useUploadStore();
  const values: EventFormValues = formValues(importId) ?? {
    name: draft.name,
    eventDate: draft.event_date ?? "",
    term: draft.term ?? "",
    modality: draft.modality ?? "",
    sponsors: draft.sponsors_hosts ?? "",
    eventType: draft.event_type ?? "",
    sourceNote: draft.attendance_source_note ?? "",
    studentWorker: draft.student_worker ?? "",
  };
  const { name, eventDate, term, modality, sponsors, eventType, sourceNote, studentWorker } = values;
  const edit = (patch: Partial<EventFormValues>) => setFormValues(importId, { ...values, ...patch });
  const setName = (name: string) => edit({ name });
  const setEventDate = (eventDate: string) => edit({ eventDate });
  const setTerm = (term: string) => edit({ term });
  const setModality = (modality: string) => edit({ modality });
  const setSponsors = (sponsors: string) => edit({ sponsors });
  const setEventType = (eventType: string) => edit({ eventType });
  const setSourceNote = (sourceNote: string) => edit({ sourceNote });
  const setStudentWorker = (studentWorker: string) => edit({ studentWorker });

  const termValid = TERM_PATTERN.test(term.trim());
  // Required fields still lacking a usable value, in form order.
  const missingFields = [
    name.trim() === "" && "Event name",
    !termValid && "Term",
    !MODALITIES.some((m) => m === modality) && "Format",
    eventType.trim() === "" && "Event type",
  ].filter((label) => label !== false);
  const valid = missingFields.length === 0;

  function submit(event: SyntheticEvent) {
    event.preventDefault();
    if (!valid || inFlight.current) return;
    inFlight.current = true;
    const details: EventDetailsIn = {
      name: name.trim(),
      event_date: eventDate || null,
      term: term.trim(),
      modality: modality as EventDetailsIn["modality"],
      sponsors_hosts: orNull(sponsors),
      event_type: eventType.trim(),
      attendance_source_note: orNull(sourceNote),
      student_worker: orNull(studentWorker),
    };
    commit.mutate(
      { id: importId, details },
      {
        onSuccess: (summary) => onCommitted(summary),
        onSettled: () => {
          inFlight.current = false;
        },
      },
    );
  }

  return (
    <Stack component="form" spacing={2} noValidate onSubmit={submit}>
      <TextField label="Event name" required value={name} onChange={(e) => setName(e.target.value)} />
      <TextField
        label="Event date"
        type="date"
        value={eventDate}
        onChange={(e) => setEventDate(e.target.value)}
        slotProps={{ inputLabel: { shrink: true } }}
      />
      <TextField
        label="Term"
        required
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        error={term !== "" && !termValid}
        helperText={term !== "" && !termValid ? "Use a season and year, like Fall 2026" : "e.g. Fall 2026"}
      />
      <TextField
        select
        id={`${id}-modality`}
        label="Format"
        required
        value={modality}
        onChange={(e) => setModality(e.target.value)}
      >
        {MODALITIES.map((m) => (
          <MenuItem key={m} value={m}>
            {m}
          </MenuItem>
        ))}
      </TextField>
      <TextField label="Sponsor/Host/Partners" value={sponsors} onChange={(e) => setSponsors(e.target.value)} />
      <Autocomplete
        freeSolo
        options={EVENT_TYPES}
        inputValue={eventType}
        onInputChange={(_, value) => setEventType(value)}
        renderInput={(params) => <TextField {...params} label="Event type" required />}
      />
      <TextField
        label="Attendance source note"
        value={sourceNote}
        onChange={(e) => setSourceNote(e.target.value)}
      />
      <TextField
        label="Entered by (student worker)"
        value={studentWorker}
        onChange={(e) => setStudentWorker(e.target.value)}
      />
      {commit.isError && <Alert severity="error">{commit.error.message}</Alert>}
      <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
        <Button type="submit" variant="contained" disabled={!valid || commit.isPending}>
          Commit
        </Button>
        {!valid && (
          <Typography variant="body2" color="text.secondary">
            To commit, fill in: {missingFields.join(", ")}.
          </Typography>
        )}
      </Stack>
    </Stack>
  );
}
