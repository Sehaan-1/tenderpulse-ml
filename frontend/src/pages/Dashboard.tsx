import { useEffect, useMemo, useState } from "react";
import { Alert, Box, CircularProgress, Paper, Stack, Typography } from "@mui/material";
import AssignmentIcon from "@mui/icons-material/Assignment";
import CategoryIcon from "@mui/icons-material/Category";
import InsightsIcon from "@mui/icons-material/Insights";
import VerifiedIcon from "@mui/icons-material/Verified";
import CategoryChart from "../components/CategoryChart";
import ConfidenceChart from "../components/ConfidenceChart";
import StatCard from "../components/StatCard";
import TenderTable from "../components/TenderTable";
import { api } from "../api/client";
import { categoryColors } from "../theme";
import type { AnalyticsSummary } from "../types/tender";

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export default function Dashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api
      .summary()
      .then((payload) => {
        if (active) {
          setSummary(payload);
          setError(null);
        }
      })
      .catch((err: Error) => active && setError(err.message))
      .finally(() => active && setLoading(false));

    return () => {
      active = false;
    };
  }, []);

  const counts = useMemo(() => {
    const map = new Map(summary?.category_counts.map((item) => [item.label, item.count]));
    return {
      Goods: map.get("Goods") ?? 0,
      Services: map.get("Services") ?? 0,
      Works: map.get("Works") ?? 0
    };
  }, [summary]);

  if (loading) {
    return (
      <Box sx={{ minHeight: 360, display: "grid", placeItems: "center" }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !summary) {
    return <Alert severity="error">{error || "Dashboard data is unavailable."}</Alert>;
  }

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4">Dashboard</Typography>
        <Typography variant="body2" color="text.secondary">
          {summary.total.toLocaleString("en-IN")} enriched tender records
        </Typography>
      </Box>

      <Box
        sx={{
          display: "grid",
          gap: 2,
          gridTemplateColumns: {
            xs: "1fr",
            sm: "repeat(2, minmax(0, 1fr))",
            lg: "repeat(6, minmax(0, 1fr))"
          }
        }}
      >
        <StatCard
          title="Total Tenders"
          value={summary.total.toLocaleString("en-IN")}
          detail="enriched records"
          icon={<AssignmentIcon />}
        />
        <StatCard
          title="Works"
          value={counts.Works.toLocaleString("en-IN")}
          color={categoryColors.Works}
          icon={<CategoryIcon />}
        />
        <StatCard
          title="Goods"
          value={counts.Goods.toLocaleString("en-IN")}
          color={categoryColors.Goods}
          icon={<CategoryIcon />}
        />
        <StatCard
          title="Services"
          value={counts.Services.toLocaleString("en-IN")}
          color={categoryColors.Services}
          icon={<CategoryIcon />}
        />
        <StatCard
          title="Avg Confidence"
          value={percent(summary.avg_confidence)}
          detail="zero-shot score"
          color="#14B8A6"
          icon={<InsightsIcon />}
        />
        <StatCard
          title="Accuracy"
          value={percent(summary.accuracy)}
          detail={`${percent(summary.baseline_accuracy)} baseline`}
          color="#A855F7"
          icon={<VerifiedIcon />}
        />
      </Box>

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", lg: "minmax(0, 0.9fr) minmax(0, 1.1fr)" },
          gap: 2
        }}
      >
        <CategoryChart data={summary.category_counts} />
        <ConfidenceChart data={summary.confidence_buckets} />
      </Box>

      <Paper variant="outlined" sx={{ p: 2.5 }}>
        <Typography variant="h6" sx={{ mb: 1.5 }}>
          Recent Tenders
        </Typography>
        <TenderTable rows={summary.recent_tenders} height={420} />
      </Paper>
    </Stack>
  );
}

