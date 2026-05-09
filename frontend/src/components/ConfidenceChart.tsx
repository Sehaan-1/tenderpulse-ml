import { Paper, Typography } from "@mui/material";
import { BarChart } from "@mui/x-charts/BarChart";
import type { ConfidenceBucket } from "../types/tender";

interface ConfidenceChartProps {
  data: ConfidenceBucket[];
  title?: string;
}

export default function ConfidenceChart({
  data,
  title = "Confidence Distribution"
}: ConfidenceChartProps) {
  return (
    <Paper variant="outlined" sx={{ p: 2.5, height: "100%" }}>
      <Typography variant="h6" sx={{ mb: 1.5 }}>
        {title}
      </Typography>
      <BarChart
        height={300}
        xAxis={[{ scaleType: "band", data: data.map((bucket) => bucket.label) }]}
        yAxis={[{ min: 0 }]}
        series={[{ data: data.map((bucket) => bucket.count), label: "Tenders", color: "#14B8A6" }]}
        margin={{ top: 20, right: 20, bottom: 44, left: 48 }}
      />
    </Paper>
  );
}

