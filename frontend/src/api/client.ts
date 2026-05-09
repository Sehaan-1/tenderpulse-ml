import type {
  AnalyticsSummary,
  ClassifyResponse,
  EvaluationResponse,
  TenderListResponse,
  TenderRecord
} from "../types/tender";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      message = payload.detail ?? message;
    } catch {
      // Keep the HTTP status fallback.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export interface TenderQuery {
  page?: number;
  pageSize?: number;
  search?: string;
  category?: string;
  org?: string;
  dateFrom?: string;
  dateTo?: string;
}

function queryString(params: TenderQuery): string {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.pageSize) query.set("page_size", String(params.pageSize));
  if (params.search) query.set("search", params.search);
  if (params.category && params.category !== "All") query.set("category", params.category);
  if (params.org) query.set("org", params.org);
  if (params.dateFrom) query.set("date_from", params.dateFrom);
  if (params.dateTo) query.set("date_to", params.dateTo);
  return query.toString();
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),
  tenders: (params: TenderQuery = {}) => {
    const qs = queryString(params);
    return request<TenderListResponse>(`/api/tenders${qs ? `?${qs}` : ""}`);
  },
  tender: (id: string) => request<TenderRecord>(`/api/tenders/${encodeURIComponent(id)}`),
  summary: () => request<AnalyticsSummary>("/api/analytics/summary"),
  evaluation: () => request<EvaluationResponse>("/api/analytics/evaluation"),
  classify: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ClassifyResponse>("/api/classify", {
      method: "POST",
      body: form
    });
  }
};

