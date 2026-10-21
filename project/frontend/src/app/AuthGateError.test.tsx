import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { apiGet } from "../api/client";

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  apiGet: vi.fn(),
}));
vi.mock("./AuthGate", () => ({
  default: () => {
    throw new Error("auth gate render failure");
  },
}));

it("shows the error page when AuthGate throws while rendering", async () => {
  vi.mocked(apiGet).mockResolvedValue({ id: 1, username: "ada", display_name: "Ada", auth_mode: "none" });
  vi.spyOn(console, "error").mockImplementation(() => {});
  window.history.replaceState(null, "", "/upload");
  const { default: App } = await import("./App");
  render(<App />);
  expect(await screen.findByText("Something went wrong. Reload the page to continue.")).toBeInTheDocument();
});
