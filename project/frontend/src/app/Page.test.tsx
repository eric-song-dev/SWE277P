import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import Page from "./Page";

describe("Page", () => {
  afterEach(cleanup);

  it("keeps the header bar in place and scrolls only the body below it", () => {
    render(
      <Page title="Upload" actions={<button>Go</button>}>
        <p>Body text</p>
      </Page>,
    );
    const header = screen.getByRole("heading", { level: 1, name: "Upload" }).closest("header")!;
    expect(header).toContainElement(screen.getByRole("button", { name: "Go" }));
    const body = screen.getByText("Body text").parentElement!;
    expect(body).toHaveAttribute("data-page-body");
    expect(header).not.toContainElement(body);
    expect(getComputedStyle(body).overflowY).toBe("auto");
    expect(getComputedStyle(header.parentElement!).height).toBe("100%");
  });
});
