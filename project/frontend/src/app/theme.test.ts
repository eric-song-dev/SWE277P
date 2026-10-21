import { describe, expect, it } from "vitest";
import { theme, tokens } from "./theme";

describe("theme", () => {
  it("uses the official UCI palette tokens", () => {
    expect(tokens.primary).toBe("#255799");
    expect(tokens.gold).toBe("#FECC07");
    expect(tokens.navy).toBe("#1B3D6D");
    expect(tokens.ink).toBe("#002244");
    expect(tokens.muted).toBe("#555759");
  });

  it("builds the MUI palette from the tokens", () => {
    expect(theme.palette.primary.main).toBe(tokens.primary);
    expect(theme.palette.text.primary).toBe(tokens.ink);
    expect(theme.palette.background.default).toBe(tokens.page);
  });

  it("uses Source Sans 3 at a 16 px body size", () => {
    expect(theme.typography.fontFamily).toMatch(/^"?Source Sans 3/);
    expect(theme.typography.fontSize).toBe(16);
    expect(theme.typography.htmlFontSize).toBe(16);
  });

  it("never contains the outdated UCI colors", () => {
    const text = JSON.stringify(theme).toLowerCase();
    expect(text).not.toContain("#0064a4");
    expect(text).not.toContain("#ffd200");
  });
});
