import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import LinearProgress from "@mui/material/LinearProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useRef, useState } from "react";
import { useDropzone } from "react-dropzone";
import type { FileRejection } from "react-dropzone";
import type { ImportPreview } from "../../api/types";
import FilePreviewCard from "./FilePreviewCard";
import { usePreviewUpload } from "./useImports";

const ACCEPT = {
  "text/csv": [".csv"],
  "application/vnd.ms-excel": [".csv"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/vnd.ms-excel.sheet.macroEnabled.12": [".xlsm"],
};

interface Card {
  key: string;
  preview: ImportPreview;
}

export default function UploadPage() {
  const upload = usePreviewUpload();
  const [cards, setCards] = useState<Card[]>([]);
  const [rejected, setRejected] = useState<string[]>([]);
  // One entry per failed batch; the mutation's own error only tracks the latest call.
  const [failures, setFailures] = useState<{ key: number; message: string }[]>([]);
  const nextKey = useRef(0);

  function addPreviews(previews: ImportPreview[]) {
    setCards((current) => {
      // Re-dropping a pending file returns the same import, which already has a card.
      const seen = new Set(current.map((c) => c.preview.id).filter((id) => id !== null));
      const added = previews
        .filter((p) => p.id === null || !seen.has(p.id))
        .map((preview) => ({
          key: preview.id === null ? `file-${nextKey.current++}` : `import-${preview.id}`,
          preview,
        }));
      return [...added, ...current];
    });
  }

  function onDrop(accepted: File[], fileRejections: FileRejection[]) {
    setRejected(fileRejections.map((r) => r.file.name));
    // mutate() callbacks only fire for the latest call, so a second drop would lose the first batch.
    if (accepted.length === 0) return;
    const names = accepted.map((f) => f.name).join(", ");
    upload.mutateAsync(accepted).then(addPreviews, (error: Error) => {
      const key = nextKey.current++;
      setFailures((current) => [...current, { key, message: `Upload failed for ${names}: ${error.message}` }]);
    });
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: ACCEPT });

  return (
    <Stack spacing={2} sx={{ maxWidth: 720 }}>
      <Typography variant="h5" component="h1">
        Upload
      </Typography>
      <Box
        {...getRootProps()}
        sx={{
          border: 2,
          borderStyle: "dashed",
          borderColor: isDragActive ? "primary.main" : "divider",
          borderRadius: 1,
          p: 4,
          textAlign: "center",
          cursor: "pointer",
        }}
      >
        <input {...getInputProps()} />
        <Typography>Drop CSV or Excel files here, or click to choose. (.csv, .xlsx, .xlsm)</Typography>
      </Box>
      {upload.isPending && <LinearProgress aria-label="Uploading" />}
      {failures.map((failure) => (
        <Alert
          key={failure.key}
          severity="error"
          onClose={() => setFailures((current) => current.filter((f) => f.key !== failure.key))}
        >
          {failure.message}
        </Alert>
      ))}
      {rejected.length > 0 && (
        <Alert severity="warning">Unsupported file type, not uploaded: {rejected.join(", ")}</Alert>
      )}
      {cards.map((card) => (
        <FilePreviewCard
          key={card.key}
          preview={card.preview}
          onRemove={() => setCards((current) => current.filter((c) => c.key !== card.key))}
        />
      ))}
    </Stack>
  );
}
