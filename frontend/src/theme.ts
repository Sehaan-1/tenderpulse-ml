import { alpha, createTheme, type PaletteMode } from "@mui/material/styles";

export const categoryColors = {
  Works: "#1976D2",
  Goods: "#2E7D32",
  Services: "#ED6C02",
  Unclassified: "#7C8797"
};

export function buildTheme(mode: PaletteMode) {
  const isDark = mode === "dark";

  return createTheme({
    palette: {
      mode,
      primary: {
        main: "#3B82F6",
        dark: "#1D4ED8",
        light: "#93C5FD"
      },
      secondary: {
        main: "#14B8A6"
      },
      success: {
        main: categoryColors.Goods
      },
      warning: {
        main: categoryColors.Services
      },
      info: {
        main: categoryColors.Works
      },
      background: {
        default: isDark ? "#0B1220" : "#F5F7FB",
        paper: isDark ? "#111B2E" : "#FFFFFF"
      },
      text: {
        primary: isDark ? "#E8EEF8" : "#182033",
        secondary: isDark ? "#98A6BA" : "#667085"
      },
      divider: isDark ? alpha("#E8EEF8", 0.1) : alpha("#182033", 0.12)
    },
    shape: {
      borderRadius: 8
    },
    typography: {
      fontFamily: ["Inter", "Roboto", "Helvetica", "Arial", "sans-serif"].join(","),
      h4: {
        fontWeight: 700,
        letterSpacing: 0
      },
      h5: {
        fontWeight: 700,
        letterSpacing: 0
      },
      h6: {
        fontWeight: 700,
        letterSpacing: 0
      },
      button: {
        textTransform: "none",
        fontWeight: 700
      }
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            minWidth: 320
          }
        }
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: "none"
          }
        }
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundImage: "none"
          }
        }
      },
      MuiButtonBase: {
        defaultProps: {
          disableRipple: true
        }
      }
    }
  });
}
