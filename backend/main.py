"""SYJ LeadForge API — FastAPI app.

Run locally with:
    uvicorn backend.main:app --reload

Then browse the interactive docs at http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from leadforge import __version__

from .routers import audits, businesses, leads, scores

app = FastAPI(
    title="SYJ LeadForge API",
    description=(
        "REST API over SYJ LeadForge's core lead qualification and website "
        "audit modules. Every endpoint calls the same functions the CLI "
        "uses, so results are always consistent between the two."
    ),
    version=__version__,
)

# This is a local-first, single-user tool by default (SQLite on disk).
# CORS is left open here for convenience when developing a local
# dashboard against it; if you deploy this behind a public URL, put it
# behind a reverse proxy and restrict allow_origins accordingly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(businesses.router)
app.include_router(audits.router)
app.include_router(scores.router)
app.include_router(leads.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "version": __version__}
