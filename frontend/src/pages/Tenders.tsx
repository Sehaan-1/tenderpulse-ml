import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  FormControl,
  InputAdornment,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import type { GridPaginationModel } from "@mui/x-data-grid";
import TenderTable from "../components/TenderTable";
import { api } from "../api/client";
import type { TenderListResponse } from "../types/tender";

export default function Tenders() {
  const [payload, setPayload] = useState<TenderListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [org, setOrg] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 25
  });

  useEffect(() => {
    let active = true;
    setLoading(true);
    api
      .tenders({
        page: paginationModel.page + 1,
        pageSize: paginationModel.pageSize,
        search,
        category,
        org,
        dateFrom,
        dateTo
      })
      .then((data) => {
        if (active) {
          setPayload(data);
          setError(null);
        }
      })
      .catch((err: Error) => active && setError(err.message))
      .finally(() => active && setLoading(false));

    return () => {
      active = false;
    };
  }, [category, dateFrom, dateTo, org, paginationModel.page, paginationModel.pageSize, search]);

  const resetPage = () => setPaginationModel((model) => ({ ...model, page: 0 }));

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4">Tenders</Typography>
        <Typography variant="body2" color="text.secondary">
          Search, filter, sort, and inspect enriched tender records.
        </Typography>
      </Box>

      <Paper variant="outlined" sx={{ p: 2.5 }}>
        <Box
          sx={{
            display: "grid",
            gap: 2,
            gridTemplateColumns: {
              xs: "1fr",
              md: "minmax(220px, 1.4fr) minmax(160px, 0.7fr) minmax(220px, 1fr) repeat(2, minmax(150px, 0.7fr))"
            }
          }}
        >
          <TextField
            label="Search"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              resetPage();
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              )
            }}
          />
          <FormControl>
            <InputLabel id="category-filter-label">Category</InputLabel>
            <Select
              labelId="category-filter-label"
              label="Category"
              value={category}
              onChange={(event) => {
                setCategory(event.target.value);
                resetPage();
              }}
            >
              {(payload?.categories ?? ["All", "Goods", "Services", "Works"]).map((item) => (
                <MenuItem key={item} value={item}>
                  {item}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label="Organization"
            value={org}
            onChange={(event) => {
              setOrg(event.target.value);
              resetPage();
            }}
          />
          <TextField
            label="From"
            type="date"
            value={dateFrom}
            onChange={(event) => {
              setDateFrom(event.target.value);
              resetPage();
            }}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="To"
            type="date"
            value={dateTo}
            onChange={(event) => {
              setDateTo(event.target.value);
              resetPage();
            }}
            InputLabelProps={{ shrink: true }}
          />
        </Box>
      </Paper>

      {error && <Alert severity="error">{error}</Alert>}

      <Paper variant="outlined" sx={{ p: 1 }}>
        <TenderTable
          rows={payload?.items ?? []}
          loading={loading}
          rowCount={payload?.total ?? 0}
          paginationMode="server"
          paginationModel={paginationModel}
          onPaginationModelChange={setPaginationModel}
          height={640}
        />
      </Paper>
    </Stack>
  );
}

