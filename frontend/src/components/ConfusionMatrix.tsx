import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";

interface ConfusionMatrixProps {
  labels: string[];
  matrix: number[][];
}

export default function ConfusionMatrix({ labels, matrix }: ConfusionMatrixProps) {
  const theme = useTheme();
  const max = Math.max(1, ...matrix.flat());

  return (
    <Paper variant="outlined" sx={{ p: 2.5, height: "100%" }}>
      <Typography variant="h6" sx={{ mb: 1.5 }}>
        Confusion Matrix
      </Typography>
      <TableContainer>
        <Table size="small" aria-label="Confusion matrix">
          <TableHead>
            <TableRow>
              <TableCell>Actual</TableCell>
              {labels.map((label) => (
                <TableCell key={label} align="right">
                  {label}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {labels.map((actual, rowIndex) => (
              <TableRow key={actual}>
                <TableCell component="th" scope="row">
                  {actual}
                </TableCell>
                {labels.map((predicted, colIndex) => {
                  const value = matrix[rowIndex]?.[colIndex] ?? 0;
                  const intensity = value / max;
                  return (
                    <TableCell
                      key={predicted}
                      align="right"
                      sx={{
                        fontWeight: 800,
                        bgcolor: alpha(theme.palette.primary.main, 0.08 + intensity * 0.32)
                      }}
                    >
                      {value}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
}

