import { skipToken, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiSend } from "../../api/client";
import type {
  LlmProfileIn,
  LlmProfileOut,
  LlmProfilePatch,
  PresetOut,
  ProbeResultOut,
} from "../../api/types";

const PROFILES_KEY = ["llm-profiles"];

export function useProfiles() {
  return useQuery({
    queryKey: PROFILES_KEY,
    queryFn: () => apiGet<LlmProfileOut[]>("/api/llm-profiles"),
  });
}

export function usePresets() {
  return useQuery({
    queryKey: ["llm-presets"],
    queryFn: () => apiGet<PresetOut[]>("/api/llm-profiles/presets"),
    staleTime: Infinity,
  });
}

// The latest probe result for a profile. It is only ever written by useProbeProfile.
export function useProbeResult(id: number | undefined) {
  return useQuery<ProbeResultOut | null>({
    queryKey: ["llm-probe", id],
    queryFn: skipToken,
  });
}

export function useSaveProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (args: { id?: number; body: LlmProfileIn | LlmProfilePatch }) =>
      args.id === undefined
        ? apiSend<LlmProfileOut>("POST", "/api/llm-profiles", args.body)
        : apiSend<LlmProfileOut>("PATCH", `/api/llm-profiles/${args.id}`, args.body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROFILES_KEY }),
  });
}

export function useDeleteProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiSend<void>("DELETE", `/api/llm-profiles/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROFILES_KEY }),
  });
}

export function useSetDefault() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiSend<LlmProfileOut>("POST", `/api/llm-profiles/${id}/default`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: PROFILES_KEY }),
  });
}

export function useProbeProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiSend<ProbeResultOut>("POST", `/api/llm-profiles/${id}/test`),
    onSuccess: (result, id) => {
      queryClient.setQueryData(["llm-probe", id], result);
      return queryClient.invalidateQueries({ queryKey: PROFILES_KEY });
    },
  });
}
