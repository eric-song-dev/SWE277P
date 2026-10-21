import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiSend, apiUpload } from "../../api/client";
import type {
  CommitSummary,
  EventDetailsIn,
  ImportFileOut,
  ImportPreview,
  ImportPreviewBatch,
} from "../../api/types";

const IMPORTS_KEY = ["imports"];

export function useImportHistory() {
  return useQuery({
    queryKey: IMPORTS_KEY,
    queryFn: () => apiGet<ImportFileOut[]>("/api/imports"),
  });
}

export function usePreviewUpload() {
  return useMutation({
    mutationFn: async (files: File[]): Promise<ImportPreview[]> =>
      (await apiUpload<ImportPreviewBatch>("/api/imports", files)).files,
  });
}

export function useCommitImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (args: { id: number; details: EventDetailsIn }) =>
      apiSend<CommitSummary>("POST", `/api/imports/${args.id}/commit`, args.details),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: IMPORTS_KEY }),
  });
}

export function useDiscardImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiSend<void>("DELETE", `/api/imports/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: IMPORTS_KEY }),
  });
}
