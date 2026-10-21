import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import AddIcon from "@mui/icons-material/Add";
import { NavLink, useNavigate } from "react-router";
import { useConversations } from "./useConversations";

export default function ConversationList() {
  const conversations = useConversations();
  const navigate = useNavigate();

  return (
    <Box component="nav" aria-label="Conversations" sx={{ width: 240, flexShrink: 0 }}>
      {/* /chat is a draft; the first question creates the conversation. */}
      <Button fullWidth variant="outlined" startIcon={<AddIcon />} onClick={() => void navigate("/chat")}>
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
      <List dense>
        {conversations.data?.map((conversation) => (
          <ListItemButton
            key={conversation.id}
            component={NavLink}
            to={`/chat/${conversation.id}`}
            sx={{ "&.active": { bgcolor: "action.selected" } }}
          >
            <ListItemText
              primary={conversation.title ?? "New conversation"}
              slotProps={{ primary: { noWrap: true } }}
            />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
}
