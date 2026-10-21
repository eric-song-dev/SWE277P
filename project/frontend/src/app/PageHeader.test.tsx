import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import PageHeader from "./PageHeader";

describe("PageHeader", () => {
  afterEach(cleanup);

  it("renders the title as an h1 and the actions", () => {
    render(<PageHeader title="Dataset" actions={<button>Go</button>} />);
    expect(screen.getByRole("heading", { level: 1, name: "Dataset" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Go" })).toBeTruthy();
    expect(document.querySelector("header")).toBeTruthy();
  });
});
