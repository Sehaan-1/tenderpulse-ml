import type { ReactNode } from "react";
import { Box, Card, CardContent, Typography } from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";

interface StatCardProps {
  title: string;
  value: string;
  detail?: string;
  color?: string;
  icon?: ReactNode;
}

export default function StatCard({ title, value, detail, color, icon }: StatCardProps) {
  const theme = useTheme();
  const accent = color ?? theme.palette.primary.main;

  return (
    <Card
      variant="outlined"
      sx={{
        height: "100%",
        borderColor: alpha(accent, 0.28),
        bgcolor: alpha(accent, theme.palette.mode === "dark" ? 0.08 : 0.04)
      }}
    >
      <CardContent sx={{ display: "flex", gap: 2, alignItems: "flex-start" }}>
        {icon && (
          <Box
            sx={{
              width: 42,
              height: 42,
              flex: "0 0 auto",
              borderRadius: 1.5,
              color: accent,
              bgcolor: alpha(accent, 0.14),
              display: "grid",
              placeItems: "center"
            }}
          >
            {icon}
          </Box>
        )}
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="body2" color="text.secondary" noWrap>
            {title}
          </Typography>
          <Typography variant="h5" sx={{ mt: 0.5 }}>
            {value}
          </Typography>
          {detail && (
            <Typography variant="caption" color="text.secondary">
              {detail}
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

