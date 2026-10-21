import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navigate, RouterProvider, createBrowserRouter } from "react-router";
import AppShell from "./AppShell";
import AuthGate from "./AuthGate";
import PlaceholderPage from "./PlaceholderPage";
import { theme } from "./theme";

const queryClient = new QueryClient();

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/chat" replace /> },
      { path: "chat", element: <PlaceholderPage title="Chat" /> },
      { path: "upload", element: <PlaceholderPage title="Upload" /> },
      { path: "dataset", element: <PlaceholderPage title="Dataset" /> },
      { path: "settings", element: <PlaceholderPage title="Settings" /> },
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
