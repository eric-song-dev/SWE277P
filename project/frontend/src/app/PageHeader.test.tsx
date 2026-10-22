import Button from "@mui/material/Button";
import { ThemeProvider } from "@mui/material/styles";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import PageHeader from "./PageHeader";
import { theme } from "./theme";

describe("PageHeader", () => {
  afterEach(cleanup);

  it("renders the title as an h1 and the actions", () => {
    render(<PageHeader title="Dataset" actions={<button>Go</button>} />);
    expect(screen.getByRole("heading", { level: 1, name: "Dataset" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Go" })).toBeTruthy();
    expect(document.querySelector("header")).toBeTruthy();
  });

  it("is a slim white bar with a bottom line, a 26px title and compact buttons", () => {
    render(
      <ThemeProvider theme={theme}>
        <PageHeader title="Dataset" actions={<Button variant="contained">Download</Button>} />
      </ThemeProvider>,
    );
    const bar = getComputedStyle(document.querySelector("header")!);
    expect(bar.minHeight).toBe("59px");
    expect(bar.backgroundColor).toBe("rgb(255, 255, 255)");
    expect(bar.borderBottomWidth).toBe("1px");
    expect(getComputedStyle(screen.getByRole("heading", { level: 1 })).fontSize).toBe("26px");
    expect(getComputedStyle(screen.getByRole("button", { name: "Download" })).minHeight).toBe("34px");
  });
});
