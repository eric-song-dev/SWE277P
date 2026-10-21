import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Link from "@mui/material/Link";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useCallback, useState } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router";
import { ApiError } from "../../api/client";
import type { LlmProfileOut } from "../../api/types";
import { useProfiles } from "../settings/useProfiles";
import Composer from "./Composer";
import ConversationList from "./ConversationList";
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

  function ask(question: string) {
    if (profile) send(question, profile.id, shareResults);
  }

  function retryLive() {
    if (profile) retry(profile.id, shareResults);
  }

  function chooseProfile(id: number) {
    setChosenProfileId(id);
    rememberProfileId(id);
  }

  let main;
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
        {conversationId === null && live === null && (
          <Typography color="text.secondary">Ask a question about the attendance data to start.</Typography>
        )}
        {/* Turn cards are keyed by seq, which restarts in every conversation, so each one gets
            fresh cards. The draft's remount on its first send comes before any stream event. */}
        <Thread
          key={conversationId ?? "draft"}
          turns={conversation.data?.turns ?? []}
          live={live}
          resultsByTurnId={resultsByTurnId}
          busy={streaming}
          onRetryLive={retryLive}
          onResend={ask}
        />
        {profile && (
          <Stack
            direction="row"
            spacing={2}
            sx={{ position: "sticky", bottom: 0, py: 2, bgcolor: "background.default", alignItems: "flex-start" }}
          >
            <Composer disabled={streaming} onSend={ask} />
            <ShareResultsSwitch checked={shareResults} allowed={allowed} onChange={setChoice} />
          </Stack>
        )}
      </>
    );
  }

  return (
    <Box sx={{ display: "flex", gap: 3, alignItems: "flex-start" }}>
      <ConversationList />
      <Stack spacing={2} sx={{ flexGrow: 1, minWidth: 0 }}>
        {profiles.isError && <Alert severity="error">Could not load your AI models.</Alert>}
        {profiles.data?.length === 0 && (
          <Alert severity="info">
            Add an AI model in Settings to start.{" "}
            <Link component={RouterLink} to="/settings">
              Go to Settings
            </Link>
          </Alert>
        )}
        {profile && profiles.data && (
          <Box>
            <ProfileSelect profiles={profiles.data} value={profile.id} onChange={chooseProfile} />
          </Box>
        )}
        {main}
      </Stack>
    </Box>
  );
}
