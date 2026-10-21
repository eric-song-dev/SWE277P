// Mirrors the backend Pydantic schemas by name. Dates and datetimes arrive as ISO strings.

// app/auth/schemas.py
export interface MeOut {
  id: number;
  username: string;
  display_name: string;
  auth_mode: string;
}

// app/imports/schemas.py
export interface SkippedRowOut {
  source_row: number;
  reason: string;
}

export interface ErrorOut {
  code: string;
  message: string;
  details: Record<string, unknown> | null;
}

export interface EventDraftOut {
  name: string;
  event_date: string | null;
  term: string | null;
  modality: string | null;
  sponsors_hosts: string | null;
  event_type: string | null;
  on_campus_groups: boolean;
  attendance_source_note: string | null;
  student_worker: string | null;
}

export interface ImportPreview {
  id: number | null;
  file_name: string;
  status: "pending" | "duplicate" | "rejected";
  source: string | null;
  source_display: string | null;
  row_count: number;
  skipped: SkippedRowOut[];
  flag_counts: Record<string, number>;
  event_draft: EventDraftOut | null;
  duplicate_of: number | null;
  error: ErrorOut | null;
}

export interface ImportPreviewBatch {
  files: ImportPreview[];
}

export interface EventDetailsIn {
  name: string;
  event_date?: string | null;
  term: string;
  modality: "In Person" | "Virtual" | "Hybrid";
  sponsors_hosts?: string | null;
  event_type: string;
  attendance_source_note?: string | null;
  student_worker?: string | null;
}

export interface CommitSummary {
  import_id: number;
  event_id: number;
  inserted: number;
  linked_by_netid: number;
  linked_by_email: number;
  new_people: number;
  unlinked: number;
  flagged_rows: number;
  skipped: number;
  duplicates_in_event: number;
}

export interface ImportEventRef {
  id: number;
  name: string;
  term: string;
}

export interface ImportUserRef {
  id: number;
  display_name: string;
}

export interface ImportFileOut {
  id: number;
  file_name: string;
  source: string;
  status: string;
  row_count: number | null;
  skipped_count: number | null;
  event: ImportEventRef | null;
  flag_count: number;
  uploaded_by: ImportUserRef;
  uploaded_at: string;
  committed_at: string | null;
}

// app/events/schemas.py
export interface EventOut {
  id: number;
  name: string;
  event_date: string | null;
  term: string;
  academic_year: string | null;
  modality: string | null;
  event_type: string | null;
  attendee_count: number;
}

// app/llm/schemas.py
export interface LlmProfileIn {
  name: string;
  preset: string;
  base_url?: string | null;
  model: string;
  api_key?: string | null;
  share_results_with_llm?: boolean | null;
}

export interface LlmProfilePatch {
  name?: string | null;
  preset?: string | null;
  base_url?: string | null;
  model?: string | null;
  api_key?: string | null;
  share_results_with_llm?: boolean | null;
}

export interface LlmProfileOut {
  id: number;
  name: string;
  preset: string;
  base_url: string | null;
  model: string;
  api_key_hint: string | null;
  has_api_key: boolean;
  share_results_with_llm: boolean;
  json_mode: boolean | null;
  is_default: boolean;
  last_tested_at: string | null;
  last_test_ok: boolean | null;
}

export interface PresetOut {
  key: string;
  label: string;
  base_url: string | null;
  share_results_default: boolean;
}

export interface ProbeResultOut {
  ok: boolean;
  json_mode: boolean | null;
  models: string[];
  error: string | null;
  latency_ms: number;
}

// app/chat/schemas.py
export interface MessageIn {
  question: string;
  llm_profile_id?: number | null;
  share_results?: boolean;
}

export interface ConversationOut {
  id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface TurnOut {
  id: number;
  seq: number;
  question: string;
  kind: "answer" | "clarification" | "error";
  sql: string | null;
  interpretation: string | null;
  assumptions: string[] | null;
  clarification_question: string | null;
  row_count: number | null;
  truncated: boolean;
  analysis_text: string | null;
  analysis_source: "llm" | "local" | null;
  results_shared: boolean;
  llm_profile_id: number | null;
  model: string | null;
  error_code: string | null;
  created_at: string;
}

export interface ConversationDetail extends ConversationOut {
  turns: TurnOut[];
}

// Cells are JSON values; non-finite numbers arrive as strings.
export interface QueryResultOut {
  columns: string[];
  rows: unknown[][];
  row_count: number;
  truncated: boolean;
}

// SSE events from POST /api/chat/conversations/{id}/messages
export type SseEvent =
  | { event: "step"; data: { name: string; attempt: number } }
  | { event: "clarification"; data: { question: string } }
  | { event: "sql"; data: { sql: string; interpretation: string; assumptions: string[] } }
  | { event: "result"; data: QueryResultOut }
  | { event: "analysis_delta"; data: { text: string } }
  | {
      event: "analysis";
      data: { text: string; source: "llm" | "local"; results_shared: boolean };
    }
  | { event: "error"; data: { code: string; message: string } }
  | { event: "done"; data: { turn_id: number | null } };
