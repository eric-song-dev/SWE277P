import { createContext, useContext } from "react";
import type { CommitSummary, ImportPreview } from "../../api/types";

export interface UploadCard {
  key: string;
  preview: ImportPreview;
  summary: CommitSummary | null;
}

export interface EventFormValues {
  name: string;
  eventDate: string;
  term: string;
  modality: string;
  sponsors: string;
  eventType: string;
  sourceNote: string;
  studentWorker: string;
}

export interface UploadStore {
  cards: UploadCard[];
  addPreviews: (previews: ImportPreview[]) => void;
  removeCard: (key: string) => void;
  setSummary: (key: string, summary: CommitSummary) => void;
  formValues: (importId: number) => EventFormValues | undefined;
  setFormValues: (importId: number, values: EventFormValues) => void;
}

export const UploadContext = createContext<UploadStore | null>(null);

export function useUploadStore(): UploadStore {
  const store = useContext(UploadContext);
  if (!store) throw new Error("useUploadStore needs an UploadProvider");
  return store;
}
