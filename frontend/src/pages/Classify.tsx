import { useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  LinearProgress,
  Paper,
  Stack,
  Typography
} from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import CategoryChart from "../components/CategoryChart";
import FileUpload from "../components/FileUpload";
import StatCard from "../components/StatCard";
import TenderTable from "../components/TenderTable";
import { api } from "../api/client";
import type { ClassifyResponse, TenderRecord } from "../types/tender";

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export default function Classify() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ClassifyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const rows = useMemo<TenderRecord[]>(() => {
    return (result?.results ?? []).map((row, index) => ({
      ...row,
      record_key: row.record_key || `${row.tender_id || "upload"}-${index}`
    }));
  }, [result]);

  const runClassification = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const payload = await api.classify(file);
      setResult(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Classification failed");
    } finally {
      setLoading(false);
    }
  };

  const download = () => {
    if (!result) return;
    const blob = new Blob([result.enriched_jsonl], { type: "application/x-ndjson" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${file?.name.replace(/\.jsonl$/i, "") || "tenders"}_enriched.jsonl`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4">Classify</Typography>
        <Typography variant="body2" color="text.secondary">
          Upload tender JSONL and enrich each record with category predictions.
        </Typography>
      </Box>

      <Box
        sx={{
          display: "grid",
          gap: 2,
          gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 0.9fr) minmax(0, 1.1fr)" }
        }}
      >
        <Stack spacing={2}>
          <FileUpload file={file} onFile={setFile} disabled={loading} />
          <Stack direction="row" spacing={1.5} flexWrap="wrap" useFlexGap>
            <Button
              variant="contained"
              startIcon={<PlayArrowIcon />}
              disabled={!file || loading}
              onClick={runClassification}
            >
              Run Classification
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              disabled={!result || loading}
              onClick={download}
            >
              Download JSONL
            </Button>
          </Stack>
          {loading && <LinearProgress />}
          {error && <Alert severity="error">{error}</Alert>}
          {result?.errors.length ? (
            <Alert severity="warning">{result.errors.length} rows were skipped.</Alert>
          ) : null}
        </Stack>

        {result ? (
          <Box
            sx={{
              display: "grid",
              gap: 2,
              gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" }
            }}
          >
            <StatCard title="Classified" value={result.total.toLocaleString("en-IN")} />
            <StatCard title="Avg Confidence" value={percent(result.avg_confidence)} />
            <Box sx={{ gridColumn: "1 / -1" }}>
              <CategoryChart data={result.category_counts} title="Upload Categories" />
            </Box>
          </Box>
        ) : (
          <Paper variant="outlined" sx={{ p: 2.5, minHeight: 250 }}>
            <Typography variant="h6">Ready</Typography>
            <Typography variant="body2" color="text.secondary">
              The backend will use the local BART-large-MNLI model.
            </Typography>
          </Paper>
        )}
      </Box>

      {result && (
        <Paper variant="outlined" sx={{ p: 2.5 }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Results Preview
          </Typography>
          <TenderTable rows={rows} height={520} />
        </Paper>
      )}
    </Stack>
  );
}

