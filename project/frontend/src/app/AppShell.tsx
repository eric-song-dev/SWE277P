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
import { tokens } from "./theme";

const NAV = [
  { to: "/chat", label: "Chat", icon: <ChatIcon fontSize="small" /> },
  { to: "/upload", label: "Upload", icon: <UploadFileIcon fontSize="small" /> },
  {
    to: "/dataset",
    label: "Dataset",
    icon: <TableChartIcon fontSize="small" />,
  },
  {
    to: "/settings",
    label: "Settings",
    icon: <SettingsIcon fontSize="small" />,
  },
];

const whiteRing = { outline: "2px solid #FFFFFF", outlineOffset: "2px" };

export default function AppShell() {
  const me = useQuery({
    queryKey: ["me"],
    queryFn: () => apiGet<MeOut>("/api/me"),
    retry: false,
  });
  const [collapsed, setCollapsed] = useState(false);
  const toggleLabel = collapsed ? "Expand navigation" : "Collapse navigation";

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      <Box
        component="nav"
        aria-label="Main navigation"
        sx={{
          flex: `0 0 ${collapsed ? 72 : 248}px`,
          width: collapsed ? 72 : 248,
          position: "sticky",
          top: 0,
          height: "100vh",
          boxSizing: "border-box",
          bgcolor: tokens.navy,
          color: "#FFFFFF",
          display: "flex",
          flexDirection: "column",
          pb: "20px",
          overflow: "hidden",
          transition: "flex-basis 150ms ease, width 150ms ease",
          "& a:focus-visible, & button:focus-visible, & .Mui-focusVisible": whiteRing,
        }}
      >
        <Box
          sx={{
            minHeight: 88,
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
              <Typography
                sx={{
                  fontSize: 19,
                  fontWeight: 700,
                  lineHeight: 1.25,
                  whiteSpace: "nowrap",
                }}
              >
                GPSRC Data Hub
              </Typography>
              <Typography
                sx={{
                  fontSize: 13,
                  color: tokens.navMuted,
                  lineHeight: 1.35,
                  mt: "4px",
                }}
              >
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
              "&:hover, &:focus-visible": {
                bgcolor: "rgba(255,255,255,0.12)",
                color: "#FFFFFF",
              },
            }}
          >
            {collapsed ? (
              <KeyboardDoubleArrowRightIcon fontSize="small" />
            ) : (
              <KeyboardDoubleArrowLeftIcon fontSize="small" />
            )}
          </ButtonBase>
        </Box>
        <Box sx={{ display: "flex", flexDirection: "column", gap: "2px", pt: 2 }}>
          {NAV.map((item) => (
            <ButtonBase
              key={item.to}
              component={NavLink}
              to={item.to}
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
                },
              }}
            >
              {item.icon}
              {!collapsed && <span>{item.label}</span>}
            </ButtonBase>
          ))}
        </Box>
        {!collapsed && (
          <Typography
            sx={{
              mt: "auto",
              pt: "20px",
              px: "24px",
              fontSize: 14,
              color: tokens.navMuted,
            }}
          >
            {me.isError ? "Not connected" : me.data ? `Signed in as ${me.data.display_name}` : ""}
          </Typography>
        )}
      </Box>
      <Box component="main" sx={{ flex: 1, minWidth: 0, bgcolor: tokens.page }}>
        <Suspense fallback={<CircularProgress size={24} aria-label="Loading page" sx={{ m: 4 }} />}>
          <Outlet />
        </Suspense>
      </Box>
    </Box>
  );
}
