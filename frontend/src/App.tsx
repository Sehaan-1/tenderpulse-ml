import { useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { CssBaseline, ThemeProvider, type PaletteMode } from "@mui/material";
import { buildTheme } from "./theme";
import Layout from "./components/Layout";
import Analytics from "./pages/Analytics";
import Classify from "./pages/Classify";
import Dashboard from "./pages/Dashboard";
import Tenders from "./pages/Tenders";

const MODE_KEY = "tenderpulse-color-mode";

export default function App() {
  const [mode, setMode] = useState<PaletteMode>(() => {
    const saved = window.localStorage.getItem(MODE_KEY);
    return saved === "light" ? "light" : "dark";
  });

  const theme = useMemo(() => buildTheme(mode), [mode]);

  const toggleMode = () => {
    setMode((current) => {
      const next = current === "dark" ? "light" : "dark";
      window.localStorage.setItem(MODE_KEY, next);
      return next;
    });
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Layout mode={mode} onToggleMode={toggleMode}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/tenders" element={<Tenders />} />
            <Route path="/classify" element={<Classify />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

