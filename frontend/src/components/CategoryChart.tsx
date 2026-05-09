import { Box, Paper, Typography } from "@mui/material";
import { PieChart } from "@mui/x-charts/PieChart";
import type { CategoryCount } from "../types/tender";

interface CategoryChartProps {
  data: CategoryCount[];
  title?: string;
}

export default function CategoryChart({ data, title = "Category Distribution" }: CategoryChartProps) {
  const chartData = data.map((item) => ({
    id: item.label,
    label: item.label,
    value: item.count,
    color: item.color
  }));

  return (
    <Paper variant="outlined" sx={{ p: 2.5, height: "100%" }}>
      <Typography variant="h6" sx={{ mb: 1.5 }}>
        {title}
      </Typography>
      <Box sx={{ height: 300 }}>
        <PieChart
          height={300}
          series={[
            {
              data: chartData,
              innerRadius: 58,
              paddingAngle: 2,
              cornerRadius: 4
            }
          ]}
          slotProps={{
            legend: {
              direction: "row",
              position: { vertical: "bottom", horizontal: "middle" },
              padding: 0
            }
          }}
        />
      </Box>
    </Paper>
  );
}

