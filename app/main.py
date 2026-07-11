"""
App entrypoint. Run with:
    uvicorn app.main:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs (Swagger UI) -
this is FastAPI's free testing interface, useful for your Phase 5 demo.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import lifespan
from app.routers import auth, records, consent


app = FastAPI(
    title="SPRMS API",
    description="Secure Patient Record Management System - backend API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(records.router)
app.include_router(consent.router)
app.mount("/", StaticFiles(directory=".", html=True), name="static")


@app.get("/health")
async def health_check():
    """Simple endpoint to confirm the API is up - not security-relevant."""
    return {"status": "ok"}