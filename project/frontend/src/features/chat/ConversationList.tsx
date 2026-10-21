import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import AddIcon from "@mui/icons-material/Add";
import { NavLink, useNavigate } from "react-router";
import { tokens } from "../../app/theme";
import { useConversations } from "./useConversations";

export default function ConversationList() {
  const conversations = useConversations();
  const navigate = useNavigate();

  return (
    <Box
      component="nav"
      aria-label="Conversations"
      sx={{
        width: 256,
        flexShrink: 0,
        boxSizing: "border-box",
        bgcolor: "#FFFFFF",
        borderRight: `1px solid ${tokens.border}`,
      }}
    >
      <Box
        sx={{ position: "sticky", top: 0, maxHeight: "100vh", overflowY: "auto", boxSizing: "border-box", p: "20px 16px" }}
      >
      {/* /chat is a draft; the first question creates the conversation. */}
      <Button
        fullWidth
        variant="outlined"
        startIcon={<AddIcon />}
        onClick={() => void navigate("/chat")}
        sx={{
          minHeight: 44,
          mb: "12px",
          color: tokens.primary,
          borderColor: tokens.primary,
          transition: "background-color 120ms ease, color 120ms ease",
          "&:hover, &:focus-visible": { bgcolor: tokens.primary, color: "#FFFFFF", borderColor: tokens.primary },
        }}
      >
        New chat
      </Button>
      {conversations.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          Could not load your conversations.
        </Alert>
      )}
      {conversations.data?.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          No conversations yet.
        </Typography>
      )}
      <List disablePadding sx={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {conversations.data?.map((conversation) => (
          <ListItemButton
            key={conversation.id}
            component={NavLink}
            to={`/chat/${conversation.id}`}
            sx={{
              p: "10px 12px",
              borderRadius: "8px",
              fontSize: 15,
              color: tokens.ink,
              "&.active": { bgcolor: tokens.selected, color: tokens.navy, fontWeight: 600 },
              "&.active .MuiListItemText-primary": { fontWeight: 600 },
            }}
          >
            <ListItemText
              primary={conversation.title ?? "New conversation"}
              slotProps={{ primary: { noWrap: true, sx: { fontSize: 15 } } }}
            />
          </ListItemButton>
        ))}
      </List>
      </Box>
    </Box>
  );
}
