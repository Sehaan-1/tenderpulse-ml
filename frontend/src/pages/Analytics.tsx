import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  CircularProgress,
  LinearProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from "@mui/material";
import { BarChart } from "@mui/x-charts/BarChart";
import ConfusionMatrix from "../components/ConfusionMatrix";
import StatCard from "../components/StatCard";
import { api } from "../api/client";
import { categoryColors } from "../theme";
import type { AnalyticsSummary, EvaluationResponse } from "../types/tender";

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export default function Analytics() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([api.summary(), api.evaluation()])
      .then(([summaryPayload, evaluationPayload]) => {
        if (active) {
          setSummary(summaryPayload);
          setEvaluation(evaluationPayload);
          setError(null);
        }
      })
      .catch((err: Error) => active && setError(err.message))
      .finally(() => active && setLoading(false));

    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <Box sx={{ minHeight: 360, display: "grid", placeItems: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !summary || !evaluation) {
    return <Alert severity="error">{error || "Analytics data is unavailable."}</Alert>;
  }

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4">Analytics</Typography>
        <Typography variant="body2" color="text.secondary">
          Evaluation metrics from {evaluation.annotated_count} annotated records.
        </Typography>
      </Box>

      <Box
        sx={{
          display: "grid",
          gap: 2,
          gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)", lg: "repeat(4, 1fr)" }
        }}
      >
        <StatCard title="Representative Accuracy" value={percent(evaluation.representative_accuracy)} />
        <StatCard title="Strict Accuracy" value={percent(evaluation.strict_representative_accuracy)} />
        <StatCard title="All Diagnostic Accuracy" value={percent(evaluation.all_accuracy)} />
        <StatCard title="Zero-rule Baseline" value={percent(evaluation.dataset_baseline)} />
      </Box>

      <Paper variant="outlined" sx={{ p: 2.5 }}>
        <Typography variant="h6" sx={{ mb: 1.5 }}>
          Category Distribution Over Time
        </Typography>
        <BarChart
          dataset={summary.monthly_category_counts}
          height={320}
          xAxis={[{ scaleType: "band", dataKey: "month" }]}
          yAxis={[{ min: 0 }]}
          series={[
            { dataKey: "Goods", label: "Goods", stack: "total", color: categoryColors.Goods },
            { dataKey: "Services", label: "Services", stack: "total", color: categoryColors.Services },
            { dataKey: "Works", label: "Works", stack: "total", color: categoryColors.Works }
          ]}
          margin={{ top: 20, right: 20, bottom: 48, left: 48 }}
        />
      </Paper>

      <Box
        sx={{
          display: "grid",
          gap: 2,
          gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 1fr) minmax(0, 1fr)" }
        }}
      >
        <Paper variant="outlined" sx={{ p: 2.5 }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Class Metrics
          </Typography>
          <Stack spacing={2}>
            {evaluation.metrics.map((metric) => (
              <Box key={metric.label}>
                <Stack direction="row" justifyContent="space-between" spacing={2}>
                  <Typography variant="body2" fontWeight={800}>
                    {metric.label}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    F1 {percent(metric.f1)} | n={metric.support}
                  </Typography>
                </Stack>
                <LinearProgress
                  variant="determinate"
                  value={metric.f1 * 100}
                  sx={{
                    mt: 0.75,
                    height: 8,
                    borderRadius: 1,
                    "& .MuiLinearProgress-bar": { bgcolor: metric.color }
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  Precision {percent(metric.precision)} / Recall {percent(metric.recall)}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Paper>
        <ConfusionMatrix labels={evaluation.labels} matrix={evaluation.confusion_matrix} />
      </Box>

      <Box
        sx={{
          display: "grid",
          gap: 2,
          gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 0.8fr) minmax(0, 1.2fr)" }
        }}
      >
        <Paper variant="outlined" sx={{ p: 2.5 }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Error Breakdown
          </Typography>
          <Stack spacing={1.5}>
            {evaluation.failure_counts.map((failure) => (
              <Stack key={failure.label} direction="row" justifyContent="space-between">
                <Typography variant="body2">{failure.label}</Typography>
                <Typography variant="body2" fontWeight={800}>
                  {failure.count}
                </Typography>
              </Stack>
            ))}
          </Stack>
        </Paper>

        <Paper variant="outlined" sx={{ p: 2.5 }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Highest-confidence Errors
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Tender</TableCell>
                  <TableCell>Predicted</TableCell>
                  <TableCell>Actual</TableCell>
                  <TableCell>Failure</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {evaluation.worst_examples.map((row) => (
                  <TableRow key={`${row.tender_id}-${row.predicted_category}-${row.actual_category}`}>
                    <TableCell sx={{ maxWidth: 360 }}>
                      <Typography variant="body2" fontWeight={700} noWrap title={row.clean_title || row.title}>
                        {row.clean_title || row.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {percent(row.category_confidence ?? 0)}
                      </Typography>
                    </TableCell>
                    <TableCell>{row.predicted_category}</TableCell>
                    <TableCell>{row.actual_category}</TableCell>
                    <TableCell>{row.failure}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Box>
    </Stack>
  );
}

