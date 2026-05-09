import { useMemo, useState } from "react";
import {
  Box,
  Button,
  Chip,
  Divider,
  Drawer,
  LinearProgress,
  Stack,
  Typography
} from "@mui/material";
import { alpha } from "@mui/material/styles";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import {
  DataGrid,
  type GridColDef,
  type GridPaginationModel,
  type GridRowParams
} from "@mui/x-data-grid";
import { categoryColors } from "../theme";
import type { TenderRecord } from "../types/tender";

interface TenderTableProps {
  rows: TenderRecord[];
  loading?: boolean;
  rowCount?: number;
  height?: number;
  paginationMode?: "client" | "server";
  paginationModel?: GridPaginationModel;
  onPaginationModelChange?: (model: GridPaginationModel) => void;
}

function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(date);
}

function formatPercent(value?: number | null) {
  if (value == null) return "-";
  return `${Math.round(value * 100)}%`;
}

function categoryColor(category?: string) {
  return categoryColors[category as keyof typeof categoryColors] ?? categoryColors.Unclassified;
}

export default function TenderTable({
  rows,
  loading = false,
  rowCount,
  height = 560,
  paginationMode = "client",
  paginationModel,
  onPaginationModelChange
}: TenderTableProps) {
  const [selected, setSelected] = useState<TenderRecord | null>(null);

  const columns = useMemo<GridColDef<TenderRecord>[]>(
    () => [
      {
        field: "clean_title",
        headerName: "Tender",
        flex: 1.5,
        minWidth: 280,
        valueGetter: (_, row) => row.clean_title || row.title,
        renderCell: (params) => (
          <Box sx={{ py: 1, minWidth: 0 }}>
            <Typography variant="body2" fontWeight={700} noWrap title={params.value as string}>
              {params.value as string}
            </Typography>
            <Typography variant="caption" color="text.secondary" noWrap display="block">
              {params.row.tender_id}
            </Typography>
          </Box>
        )
      },
      {
        field: "predicted_category",
        headerName: "Category",
        width: 132,
        renderCell: (params) => {
          const color = categoryColor(params.value as string);
          return (
            <Chip
              size="small"
              label={params.value as string}
              sx={{
                color,
                borderColor: alpha(color, 0.45),
                bgcolor: alpha(color, 0.12),
                fontWeight: 700
              }}
              variant="outlined"
            />
          );
        }
      },
      {
        field: "category_confidence",
        headerName: "Confidence",
        width: 150,
        valueFormatter: (value) => formatPercent(value as number | null),
        renderCell: (params) => {
          const value = Number(params.value ?? 0);
          return (
            <Stack sx={{ width: "100%" }} spacing={0.5}>
              <Typography variant="caption" color="text.secondary">
                {formatPercent(params.value as number | null)}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.max(0, Math.min(100, value * 100))}
                sx={{ height: 6, borderRadius: 1 }}
              />
            </Stack>
          );
        }
      },
      {
        field: "org_chain",
        headerName: "Organization",
        minWidth: 220,
        flex: 1,
        renderCell: (params) => (
          <Typography variant="body2" noWrap title={String(params.value ?? "")}>
            {String(params.value ?? "-")}
          </Typography>
        )
      },
      {
        field: "published_date",
        headerName: "Published",
        width: 132,
        valueFormatter: (value) => formatDate(value as string | null)
      },
      {
        field: "closing_date",
        headerName: "Closing",
        width: 132,
        valueFormatter: (value) => formatDate(value as string | null)
      }
    ],
    []
  );

  const getRowId = (row: TenderRecord) => row.record_key || row.tender_id || row.title;

  return (
    <>
      <Box sx={{ height, width: "100%" }}>
        <DataGrid
          rows={rows}
          columns={columns}
          getRowId={getRowId}
          loading={loading}
          rowCount={rowCount}
          paginationMode={paginationMode}
          paginationModel={paginationModel}
          onPaginationModelChange={onPaginationModelChange}
          pageSizeOptions={[10, 25, 50, 100]}
          disableRowSelectionOnClick
          onRowClick={(params: GridRowParams<TenderRecord>) => setSelected(params.row)}
          sx={{
            border: 0,
            bgcolor: "background.paper",
            borderRadius: 1,
            "& .MuiDataGrid-cell": {
              alignItems: "center"
            },
            "& .MuiDataGrid-row": {
              cursor: "pointer"
            }
          }}
        />
      </Box>

      <Drawer anchor="right" open={Boolean(selected)} onClose={() => setSelected(null)}>
        <Box sx={{ width: { xs: 320, sm: 440 }, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Tender Detail
          </Typography>
          <Typography variant="body1" fontWeight={800} sx={{ mb: 2 }}>
            {selected?.clean_title || selected?.title}
          </Typography>
          <Stack spacing={1.5} divider={<Divider flexItem />}>
            <Detail label="Tender ID" value={selected?.tender_id} />
            <Detail label="Category" value={selected?.predicted_category} />
            <Detail label="Confidence" value={formatPercent(selected?.category_confidence)} />
            <Detail label="Organization" value={selected?.org_chain} />
            <Detail label="Published" value={formatDate(selected?.published_date)} />
            <Detail label="Closing" value={formatDate(selected?.closing_date)} />
            <Detail label="Reference" value={selected?.reference_number} />
          </Stack>
          {selected?.detail_url && (
            <Button
              sx={{ mt: 3 }}
              variant="contained"
              endIcon={<OpenInNewIcon />}
              href={selected.detail_url}
              target="_blank"
              rel="noreferrer"
            >
              Open Source
            </Button>
          )}
        </Box>
      </Drawer>
    </>
  );
}

function Detail({ label, value }: { label: string; value?: string | number | null }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" sx={{ overflowWrap: "anywhere" }}>
        {value || "-"}
      </Typography>
    </Box>
  );
}

