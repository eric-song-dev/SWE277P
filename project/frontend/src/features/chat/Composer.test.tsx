import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Composer from "./Composer";

function setup(onSend: (q: string) => boolean = () => true, busy = false) {
  const send = vi.fn(onSend);
  render(
    <Composer
      disabled={false}
      busy={busy}
      onSend={send}
      toolbar={<span>Toolbar content</span>}
    />,
  );
  return {
    send,
    user: userEvent.setup(),
    box: screen.getByRole("textbox", { name: "Question" }),
  };
}

describe("Composer", () => {
  it("shows the placeholder and no disclaimer under the box", () => {
    const { box } = setup();
    expect(box).toHaveAttribute(
      "placeholder",
      "Ask a question about your data",
    );
    // Each answer card carries its own caution line instead.
    expect(screen.queryByText(/AI can make mistakes/)).not.toBeInTheDocument();
  });

  it("sends the trimmed text on Enter and clears it", async () => {
    const { send, user, box } = setup();
    await user.type(box, "  How many came?  {Enter}");
    expect(send).toHaveBeenCalledWith("How many came?");
    expect(box).toHaveValue("");
  });

  it("adds a newline on Shift+Enter", async () => {
    const { send, user, box } = setup();
    await user.type(box, "a{Shift>}{Enter}{/Shift}b");
    expect(box).toHaveValue("a\nb");
    expect(send).not.toHaveBeenCalled();
  });

  it("warns about a 2,001-character question and disables Send", async () => {
    const { user, box } = setup();
    await user.click(box);
    await user.paste("x".repeat(2001));
    expect(
      screen.getByText("2,001 / 2,000 characters. Shorten your question."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  });

  it("keeps the text when onSend returns false", async () => {
    const { send, user, box } = setup(() => false);
    await user.type(box, "Keep me{Enter}");
    expect(send).toHaveBeenCalledOnce();
    expect(box).toHaveValue("Keep me");
  });

  it("stays typeable while busy but neither Send nor Enter sends", async () => {
    const { send, user, box } = setup(() => true, true);
    await user.type(box, "Next one{Enter}");
    expect(box).toHaveValue("Next one");
    expect(send).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  });

  it("holds the textbox, the toolbar and Send in one question box", () => {
    setup();
    const qbox = screen.getByTestId("question-box");
    expect(
      within(qbox).getByRole("textbox", { name: "Question" }),
    ).toBeInTheDocument();
    expect(within(qbox).getByText("Toolbar content")).toBeInTheDocument();
    expect(
      within(qbox).getByRole("button", { name: "Send" }),
    ).toBeInTheDocument();
  });
});
