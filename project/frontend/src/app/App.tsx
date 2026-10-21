import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy } from "react";
import { Navigate, RouterProvider, createBrowserRouter } from "react-router";
import AppShell from "./AppShell";
import AuthGate from "./AuthGate";
import { theme } from "./theme";

const ChatPage = lazy(() => import("../features/chat/ChatPage"));
const DatasetPage = lazy(() => import("../features/dataset/DatasetPage"));
const SettingsPage = lazy(() => import("../features/settings/SettingsPage"));
const UploadPage = lazy(() => import("../features/upload/UploadPage"));

const queryClient = new QueryClient();

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/chat" replace /> },
      // One route for /chat and /chat/:id, so the page (and its stream) survives the first send.
      { path: "chat/:conversationId?", element: <ChatPage /> },
      { path: "upload", element: <UploadPage /> },
      { path: "dataset", element: <DatasetPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
]);

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <AuthGate>
          <RouterProvider router={router} />
        </AuthGate>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
