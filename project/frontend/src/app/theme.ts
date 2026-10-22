import { createTheme } from "@mui/material/styles";
import type { SxProps, Theme } from "@mui/material/styles";

// Colors from the official UCI palette plus lightened tints
// (docs/design/2026-10-21-ui-redesign.md). Gold is used only for the 3 px
// active-page bar in the side nav.
export const tokens = {
  primary: "#255799",
  gold: "#FECC07",
  navy: "#1B3D6D",
  ink: "#002244",
  muted: "#555759",
  page: "#F3F6FA",
  selected: "#E4ECF6",
  tableHead: "#EDF2F8",
  border: "#D3DCE8",
  divider: "#E3E9F1",
  subtle: "#F6F8FB",
  control: "#7B8FAE",
  navMuted: "#C9D6E8",
  navText: "#DCE5F1",
} as const;

const focusRing = {
  outline: `2px solid ${tokens.primary}`,
  outlineOffset: "2px",
};

const fontStack =
  '"Source Sans 3", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

export const theme = createTheme({
  palette: {
    primary: { main: tokens.primary },
    text: { primary: tokens.ink, secondary: tokens.muted },
    background: { default: tokens.page },
    divider: tokens.divider,
  },
  typography: {
    fontFamily: fontStack,
    fontSize: 16,
    htmlFontSize: 16,
    // fontSize 16 scales every variant by 16/14, so pin the body sizes.
    body1: { fontSize: "1rem" },
    body2: { fontSize: "0.9375rem" },
    h1: { fontSize: "1.625rem", fontWeight: 700, lineHeight: 1.3, color: tokens.navy },
    button: { fontWeight: 600, textTransform: "none" },
  },
  shape: { borderRadius: 8 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        "p, li, h1, h2, h3, span, a": { textWrap: "pretty" },
        ":focus-visible": focusRing,
        // The shell fills the window and its panes scroll on their own, so the page never
        // rubber-bands and drags the nav or the question box with it.
        "html, body": { overscrollBehavior: "none" },
      },
    },
    MuiButtonBase: {
      styleOverrides: {
        root: {
          "&.Mui-focusVisible": focusRing,
          "&:focus-visible": focusRing,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { minHeight: 40, borderRadius: 8 },
      },
    },
    MuiCard: {
      defaultProps: { variant: "outlined" },
      styleOverrides: {
        root: { borderRadius: 12, borderColor: tokens.border },
      },
    },
    MuiPaper: {
      styleOverrides: {
        outlined: { borderRadius: 12, borderColor: tokens.border },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          "& .MuiOutlinedInput-notchedOutline": { borderColor: tokens.control },
        },
      },
    },
  },
});

// Shared DataGrid look: bordered container, tinted header, light row lines.
export const gridSx: SxProps<Theme> = {
  border: `1px solid ${tokens.border}`,
  borderRadius: "10px",
  fontSize: 15,
  "& .MuiDataGrid-columnHeaders": {
    backgroundColor: tokens.tableHead,
    // The last header's resize handle and (hidden) menu button stick out past the right edge and would add sideways scroll.
    overflow: "hidden",
  },
  "& .MuiDataGrid-columnHeader": {
    backgroundColor: tokens.tableHead,
  },
  "& .MuiDataGrid-columnHeaderTitle": {
    color: tokens.navy,
    fontWeight: 600,
  },
  // Inset, because the grid clips outlines drawn outside its cells.
  "& .MuiDataGrid-columnHeader:focus, & .MuiDataGrid-columnHeader:focus-within": {
    outline: `2px solid ${tokens.primary}`,
    outlineOffset: "-2px",
  },
  "& .MuiDataGrid-cell:focus, & .MuiDataGrid-cell:focus-within": {
    outline: `2px solid ${tokens.primary}`,
    outlineOffset: "-2px",
  },
  // The scroll area takes Tab focus when the grid is scrolled sideways; its outer ring would be clipped by the grid.
  "& .MuiDataGrid-virtualScroller:focus-visible": {
    outline: `2px solid ${tokens.primary}`,
    outlineOffset: "-2px",
  },
  "& .MuiDataGrid-row, & .MuiDataGrid-cell": {
    borderColor: tokens.divider,
  },
  "& .MuiDataGrid-footerContainer": {
    borderColor: tokens.divider,
  },
};
