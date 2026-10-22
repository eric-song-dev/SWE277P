import Box from "@mui/material/Box";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import Typography from "@mui/material/Typography";
import { NavLink } from "react-router";
import { tokens } from "../../app/theme";
import { useConversations } from "./useConversations";

// "Recent questions" in the side nav, on every page. It fills the nav's free height and scrolls
// inside it, so the nav links above and the footer below stay put. "New chat" is the first nav link.
export default function ConversationList() {
  const conversations = useConversations();

  return (
    <Box
      component="nav"
      aria-labelledby="recent-questions"
      sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", mt: "28px", px: 2 }}
    >
      <Typography
        id="recent-questions"
        component="h2"
        sx={{ pl: 1.5, pb: 1, fontSize: 15, fontWeight: 600, color: tokens.navMuted, whiteSpace: "nowrap" }}
      >
        Recent questions
      </Typography>
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          overscrollBehavior: "contain",
          pb: 1.5,
          // A thin, light scrollbar; the default grey bar stands out on navy.
          scrollbarWidth: "thin",
          scrollbarColor: "rgba(255,255,255,0.3) transparent",
        }}
      >
        {conversations.isError && (
          <Typography sx={{ px: 1.5, fontSize: 14, color: tokens.navMuted }}>Could not load your conversations.</Typography>
        )}
        {conversations.data?.length === 0 && (
          <Typography sx={{ px: 1.5, fontSize: 14, color: tokens.navMuted }}>No conversations yet.</Typography>
        )}
        <List disablePadding sx={{ display: "flex", flexDirection: "column", gap: "2px" }}>
          {conversations.data?.map((conversation) => {
            const title = conversation.title ?? "New conversation";
            return (
              <ListItemButton
                key={conversation.id}
                component={NavLink}
                to={`/chat/${conversation.id}`}
                title={title}
                sx={{
                  display: "block",
                  p: "8px 12px",
                  borderRadius: "8px",
                  fontSize: 15,
                  lineHeight: 1.4,
                  color: tokens.navText,
                  "&:hover": { bgcolor: "rgba(255,255,255,0.08)" },
                  "&.active": { bgcolor: "rgba(255,255,255,0.14)", color: "#FFFFFF", fontWeight: 600 },
                  "&.active:hover": { bgcolor: "rgba(255,255,255,0.18)" },
                }}
              >
                {/* Two lines at most; the full title is on hover. */}
                <Box
                  component="span"
                  sx={{ display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}
                >
                  {title}
                </Box>
              </ListItemButton>
            );
          })}
        </List>
      </Box>
    </Box>
  );
}
