import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useCallback, useRef, useState } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router";
import { ApiError } from "../../api/client";
import type { LlmProfileOut } from "../../api/types";
import { useProfiles } from "../settings/useProfiles";
import Composer from "./Composer";
import { tokens } from "../../app/theme";
import ProfileSelect from "./ProfileSelect";
import ShareResultsSwitch from "./ShareResultsSwitch";
import Thread from "./Thread";
import { useChatStream } from "./useChatStream";
import { useConversation } from "./useConversations";

const PROFILE_KEY = "hub.chat.profileId";

function storedProfileId(): number | null {
  try {
    const id = Number(localStorage.getItem(PROFILE_KEY));
    return Number.isInteger(id) && id > 0 ? id : null;
  } catch {
    return null; // storage blocked
  }
}

function rememberProfileId(id: number) {
  try {
    localStorage.setItem(PROFILE_KEY, String(id));
  } catch {
    // Remembering the choice is only a convenience.
  }
}

// The chosen profile if it still exists, else the default, else the first.
function pickProfile(profiles: LlmProfileOut[], id: number | null): LlmProfileOut | null {
  return profiles.find((p) => p.id === id) ?? profiles.find((p) => p.is_default) ?? profiles[0] ?? null;
}

// The share switch's own choice (null: follow the profile). It resets when the conversation or
// the profile changes; the /chat draft becoming the conversation its first send created is no change.
function useShareChoice(conversationId: number | null, profileId: number | null) {
  const [choice, setChoice] = useState<boolean | null>(null);
  const [scope, setScope] = useState({ conversationId, profileId, createdId: null as number | null });
  if (scope.conversationId !== conversationId || scope.profileId !== profileId) {
    const adopted =
      scope.conversationId === null && conversationId === scope.createdId && scope.profileId === profileId;
    setScope({ conversationId, profileId, createdId: null });
    if (!adopted) setChoice(null);
  }
  const noteCreated = useCallback((id: number) => setScope((s) => ({ ...s, createdId: id })), []);
  return { choice, setChoice, noteCreated };
}

export default function ChatPage() {
  const { conversationId: param } = useParams();
  const validParam = param === undefined || /^\d+$/.test(param);
  const conversationId = param !== undefined && validParam ? Number(param) : null;
  const navigate = useNavigate();

  const profiles = useProfiles();
  const conversation = useConversation(conversationId);
  const [chosenProfileId, setChosenProfileId] = useState(storedProfileId);
  const profile = pickProfile(profiles.data ?? [], chosenProfileId);
  const allowed = profile?.share_results_with_llm ?? false;

  const { choice, setChoice, noteCreated } = useShareChoice(conversationId, profile?.id ?? null);
  const shareResults = allowed && (choice ?? true);

  const onConversationCreated = useCallback(
    (id: number) => {
      noteCreated(id);
      void navigate(`/chat/${id}`, { replace: true });
    },
    [navigate, noteCreated],
  );
  const { live, resultsByTurnId, send, retry } = useChatStream(conversationId, onConversationCreated);
  const streaming = live?.status === "streaming";

  const notFound =
    !validParam || (conversation.error instanceof ApiError && conversation.error.code === "conversation_not_found");

  // Each accepted send or Retry scrolls its new question into view.
  const [sendCount, setSendCount] = useState(0);

  function ask(question: string): boolean {
    const sent = profile ? send(question, profile.id, shareResults) : false;
    if (sent) setSendCount((n) => n + 1);
    return sent;
  }

  function retryLive() {
    if (!profile || streaming) return;
    retry(profile.id, shareResults);
    setSendCount((n) => n + 1);
  }

  function chooseProfile(id: number) {
    setChosenProfileId(id);
    rememberProfileId(id);
  }

  // The scrolling conversation pane's height, for the sent turn's minimum height in Thread.
  const observer = useRef<ResizeObserver | null>(null);
  const paneRef = useCallback((el: HTMLDivElement | null) => {
    observer.current?.disconnect();
    observer.current = null;
    if (!el || typeof ResizeObserver === "undefined") return;
    const publish = () => el.style.setProperty("--thread-height", `${el.clientHeight}px`);
    publish();
    observer.current = new ResizeObserver(publish);
    observer.current.observe(el);
  }, []);

  let main;
  let band = null;
  if (notFound) {
    main = (
      <Alert severity="warning">
        This conversation no longer exists.{" "}
        <Link component={RouterLink} to="/chat">
          Start a new chat
        </Link>
      </Alert>
    );
  } else if (conversation.isError && !conversation.data) {
    // Only when nothing is cached: a failed background refetch keeps the conversation on screen.
    main = (
      <Alert
        severity="error"
        action={
          <Button color="inherit" size="small" onClick={() => void conversation.refetch()}>
            Retry
          </Button>
        }
      >
        Could not load this conversation.
      </Alert>
    );
  } else {
    main = (
      <>
        {conversationId === null && live === null && profile && (
          <Typography color="text.secondary">Ask a question about your data to start.</Typography>
        )}
        {/* Turn cards are keyed by seq, which restarts in every conversation, so each one gets
            fresh cards. The draft's remount on its first send comes before any stream event. */}
        <Box sx={{ flex: 1 }}>
          <Thread
            key={conversationId ?? "draft"}
            turns={conversation.data?.turns ?? []}
            live={live}
            resultsByTurnId={resultsByTurnId}
            busy={streaming}
            sendCount={sendCount}
            onRetryLive={retryLive}
            onResend={(question) => void ask(question)}
          />
        </Box>
      </>
    );
    if (profile) {
      band = (
        <Box
          sx={{
            flexShrink: 0,
            px: "40px",
            pt: 2,
            pb: "20px",
            bgcolor: "#FFFFFF",
            borderTop: `1px solid ${tokens.border}`,
          }}
        >
          <Box sx={{ maxWidth: 880, mx: "auto" }}>
            <Composer
              disabled={false}
              busy={streaming}
              onSend={ask}
              toolbar={<ShareResultsSwitch checked={shareResults} allowed={allowed} onChange={setChoice} />}
            />
          </Box>
        </Box>
      );
    }
  }

  // The page fills the shell's main area: a slim model row and the question box stay put, and only
  // the conversation pane between them scrolls.
  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Box
        component="header"
        sx={{ flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "flex-end", px: "32px", py: "12px" }}
      >
        {/* The page keeps its heading for screen readers; the nav already shows where you are. */}
        <Typography variant="h1" sx={VISUALLY_HIDDEN}>
          Chat
        </Typography>
        {profile && profiles.data && (
          <ProfileSelect profiles={profiles.data} value={profile.id} onChange={chooseProfile} />
        )}
      </Box>
      <Box
        component="section"
        aria-label="Conversation"
        ref={paneRef}
        sx={{ flex: 1, minHeight: 0, overflowY: "auto", overscrollBehavior: "contain" }}
      >
        <Stack
          sx={{
            width: "100%",
            maxWidth: 880 + 80,
            mx: "auto",
            boxSizing: "border-box",
            gap: 2,
            px: "40px",
            pt: "8px",
            pb: "32px",
          }}
        >
          {profiles.isError && <Alert severity="error">Could not load your AI models.</Alert>}
          {profiles.data?.length === 0 && (
            <Alert severity="info">
              Add an AI model in Settings to start.{" "}
              <Link component={RouterLink} to="/settings">
                Go to Settings
              </Link>
            </Alert>
          )}
          {main}
        </Stack>
      </Box>
      {band}
    </Box>
  );
}

const VISUALLY_HIDDEN = {
  position: "absolute",
  width: 1,
  height: 1,
  m: 0,
  overflow: "hidden",
  clip: "rect(0 0 0 0)",
  whiteSpace: "nowrap",
} as const;
