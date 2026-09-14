from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, ingestion, risk, alerts, eeg
from contextlib import asynccontextmanager
from app.jobs.scheduler import start_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()

app = FastAPI(
    title="PRAHARI / E+ Backend API",
    description="Wearable Biometric & Environmental Risk Engine with Supabase Integration",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware to allow frontend consumption
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ingestion.router)
app.include_router(risk.router)
app.include_router(alerts.router)
app.include_router(eeg.router)

@app.get("/")
def health_check():
    """Root health-check endpoint"""
    return {
        "status": "healthy",
        "service": "PRAHARI / E+ Companion Backend",
        "supabase_connected": True,
        "api_docs": "/docs"
    }
