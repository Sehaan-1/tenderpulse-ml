"""FastAPI entry point for the TenderPulse ML dashboard."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.analytics import router as analytics_router
from backend.api.classify import router as classify_router
from backend.api.tenders import router as tenders_router

app = FastAPI(
    title="TenderPulse ML API",
    description="API for browsing, classifying, and evaluating TenderPulse ML data.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenders_router)
app.include_router(classify_router)
app.include_router(analytics_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

