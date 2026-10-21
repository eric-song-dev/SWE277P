import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
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

// The previews of imports the server still holds as pending, for cards the page does not have
// (the user left /upload or reloaded). Fetched once each; a failed one is counted, not retried.
export function usePendingPreviews(ids: number[]) {
  return useQueries({
    queries: ids.map((id) => ({
      queryKey: ["import-preview", id],
      queryFn: () => apiGet<ImportPreview>(`/api/imports/${id}/preview`),
      staleTime: Infinity,
      gcTime: 0,
      retry: false,
    })),
    combine: (results) => ({
      previews: results.flatMap((r) => (r.data ? [r.data] : [])),
      failed: results.filter((r) => r.isError).length,
    }),
  });
}
