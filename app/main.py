from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users, ingestion, risk, alerts, eeg
from contextlib import asynccontextmanager
from app.jobs.scheduler import start_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-load ML model bundle at startup for zero-latency first inference
    try:
        from app.services.eeg_inference import get_model_bundle
        bundle = get_model_bundle()
        print(f"ML Model bundle pre-loaded successfully: {bundle.get('model_name', 'Random Forest')}")
    except Exception as e:
        print(f"Warning: ML model pre-load during startup encountered: {e}")

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
