import Box from "@mui/material/Box";
import ButtonBase from "@mui/material/ButtonBase";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import ChatIcon from "@mui/icons-material/Chat";
import SettingsIcon from "@mui/icons-material/Settings";
import TableChartIcon from "@mui/icons-material/TableChart";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import KeyboardDoubleArrowLeftIcon from "@mui/icons-material/KeyboardDoubleArrowLeft";
import KeyboardDoubleArrowRightIcon from "@mui/icons-material/KeyboardDoubleArrowRight";
import { useQuery } from "@tanstack/react-query";
import { Suspense, useState } from "react";
import { NavLink, Outlet } from "react-router";
import { apiGet } from "../api/client";
import type { MeOut } from "../api/types";
import ConversationList from "../features/chat/ConversationList";
import { tokens } from "./theme";

// "New chat" opens the /chat draft; the first question creates the conversation. It is the current
// page only on the draft itself: an open conversation is marked in "Recent questions" instead.
const NAV = [
  { to: "/chat", label: "New chat", icon: <ChatIcon fontSize="small" />, end: true },
  { to: "/upload", label: "Upload", icon: <UploadFileIcon fontSize="small" />, end: false },
  { to: "/dataset", label: "Dataset", icon: <TableChartIcon fontSize="small" />, end: false },
  { to: "/settings", label: "Settings", icon: <SettingsIcon fontSize="small" />, end: false },
];

const whiteRing = { outline: "2px solid #FFFFFF", outlineOffset: "2px" };
// The links span the nav's full width and the nav clips overflow, so their ring sits inside the link.
const whiteRingInset = { outline: "2px solid #FFFFFF", outlineOffset: "-2px" };

const NAV_WIDTH = 280;
const RAIL_WIDTH = 72;

export default function AppShell() {
  const me = useQuery({ queryKey: ["me"], queryFn: () => apiGet<MeOut>("/api/me"), retry: false });
  const [collapsed, setCollapsed] = useState(false);
  const toggleLabel = collapsed ? "Expand navigation" : "Collapse navigation";

  // The shell fills the window and never scrolls as a whole: the side panel scrolls its list, and
  // each page scrolls only its body under its header bar (Page, and Chat's conversation pane), so
  // the nav, the header bars and the chat's question box never move.
  return (
    <Box sx={{ display: "flex", height: "100dvh", overflow: "hidden" }}>
      <Box
        sx={{
          flex: `0 0 ${collapsed ? RAIL_WIDTH : NAV_WIDTH}px`,
          width: collapsed ? RAIL_WIDTH : NAV_WIDTH,
          height: "100%",
          boxSizing: "border-box",
          bgcolor: tokens.navy,
          color: "#FFFFFF",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          transition: "flex-basis 150ms ease, width 150ms ease",
          "& button.MuiButtonBase-root:focus-visible, & button.MuiButtonBase-root.Mui-focusVisible": whiteRing,
          "& a.MuiButtonBase-root:focus-visible, & a.MuiButtonBase-root.Mui-focusVisible": whiteRingInset,
        }}
      >
        <Box
          sx={{
            flexShrink: 0,
            height: 88,
            boxSizing: "border-box",
            p: collapsed ? "16px 0" : "16px 12px 16px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "space-between",
            gap: 1,
          }}
        >
          {!collapsed && (
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontSize: 19, fontWeight: 700, lineHeight: 1.25, whiteSpace: "nowrap" }}>
                GPSRC Data Hub
              </Typography>
              <Typography sx={{ fontSize: 13, color: tokens.navMuted, lineHeight: 1.35, mt: "4px" }}>
                Graduate &amp; Postdoctoral Scholar Resource Center
              </Typography>
            </Box>
          )}
          <ButtonBase
            aria-label={toggleLabel}
            title={toggleLabel}
            aria-expanded={!collapsed}
            onClick={() => setCollapsed((c) => !c)}
            sx={{
              flex: "0 0 auto",
              width: 40,
              height: 40,
              borderRadius: "8px",
              color: tokens.navMuted,
              transition: "background-color 120ms ease, color 120ms ease",
              "&:hover, &:focus-visible": { bgcolor: "rgba(255,255,255,0.12)", color: "#FFFFFF" },
            }}
          >
            {collapsed ? (
              <KeyboardDoubleArrowRightIcon fontSize="small" />
            ) : (
              <KeyboardDoubleArrowLeftIcon fontSize="small" />
            )}
          </ButtonBase>
        </Box>
        <Box
          component="nav"
          aria-label="Main navigation"
          sx={{ flexShrink: 0, display: "flex", flexDirection: "column", gap: "2px", pt: 2 }}
        >
          {NAV.map((item) => (
            <ButtonBase
              key={item.to}
              component={NavLink}
              to={item.to}
              end={item.end}
              aria-label={item.label}
              title={item.label}
              sx={{
                display: "flex",
                justifyContent: collapsed ? "center" : "flex-start",
                alignItems: "center",
                gap: "12px",
                p: collapsed ? "11px 0" : "11px 24px",
                borderLeft: "3px solid transparent",
                color: tokens.navText,
                textDecoration: "none",
                fontSize: 16,
                transition: "background-color 120ms ease",
                "&:hover": { bgcolor: "rgba(255,255,255,0.08)" },
                "&.active": {
                  borderLeftColor: tokens.gold,
                  bgcolor: "rgba(255,255,255,0.10)",
                  color: "#FFFFFF",
                  fontWeight: 600,
                  "&:hover": { bgcolor: "rgba(255,255,255,0.16)" },
                },
              }}
            >
              {item.icon}
              {!collapsed && <span>{item.label}</span>}
            </ButtonBase>
          ))}
        </Box>
        {collapsed ? <Box sx={{ flex: 1 }} /> : <ConversationList />}
        {!collapsed && (
          <Typography
            sx={{
              flexShrink: 0,
              p: "14px 24px 18px",
              borderTop: "1px solid rgba(255,255,255,0.14)",
              fontSize: 14,
              color: tokens.navMuted,
            }}
          >
            {me.isError ? "Not connected" : me.data ? `Signed in as ${me.data.display_name}` : ""}
          </Typography>
        )}
      </Box>
      <Box
        component="main"
        sx={{ flex: 1, minWidth: 0, height: "100%", overflow: "hidden", bgcolor: tokens.page }}
      >
        <Suspense fallback={<CircularProgress size={24} aria-label="Loading page" sx={{ m: 4 }} />}>
          <Outlet />
        </Suspense>
      </Box>
    </Box>
  );
}
