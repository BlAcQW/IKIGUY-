"""
African Language Community Data Platform API

Main FastAPI application for community-driven African language data collection
and organization platform.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn

from database import connect_to_mongo, close_mongo_connection
from routes import auth, submissions, validation, community, governance, datasets, notebooks
from routers import languages_new as languages
from routers import models, pipelines, dataset_versions, resources, discovery, drive
from models.responses import HealthResponse
from models.ml_models import ModelType
from core.config import get_settings
from typing import List

settings = get_settings()
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Handles database connections and cleanup.
    """
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="African Language Community Data Platform",
    description="Community-driven platform for collecting and organizing African language data for voice AI systems",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins to fix CORS issues
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring service status.

    Returns:
        HealthResponse: Service health status and version info
    """
    return HealthResponse(
        status="healthy",
        message="African Language Community Platform API is running",
        version="1.0.0"
    )


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(languages.router, prefix="/api/v1/languages", tags=["languages"])
app.include_router(notebooks.router, prefix="/api/v1/notebooks", tags=["notebooks"])
app.include_router(submissions.router, prefix="/api/v1/submit", tags=["submissions"])
app.include_router(validation.router, prefix="/api/v1/validate", tags=["validation"])
app.include_router(community.router, prefix="/api/v1/community", tags=["community"])
app.include_router(governance.router, prefix="/api/v1/governance", tags=["governance"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])

# MLOps Platform Routers (Phase 4)
app.include_router(models.router, prefix="/api/v1")
app.include_router(pipelines.router, prefix="/api/v1")
app.include_router(dataset_versions.router, prefix="/api/v1/datasets")  # Note: router has no prefix
app.include_router(resources.router, prefix="/api/v1")
app.include_router(discovery.router, prefix="/api/v1")
app.include_router(drive.router, prefix="/api/v1")  # Community Drive (file management)


# Model Types Endpoints
# Define model type metadata with categories and supported languages
MODEL_TYPE_METADATA = {
    "tts": {
        "category": "tts",
        "description": "Text-to-Speech models that convert written text into natural-sounding speech",
        "supported_languages": ["twi", "yor", "swa", "hau", "amh", "zul"]
    },
    "asr": {
        "category": "asr",
        "description": "Automatic Speech Recognition models for transcribing spoken language to text",
        "supported_languages": ["twi", "yor", "swa", "hau", "amh", "zul", "ibo"]
    },
    "llm": {
        "category": "llm",
        "description": "Large Language Models for text generation and understanding",
        "supported_languages": ["swa", "hau", "amh", "yor"]
    },
    "nmt": {
        "category": "llm",
        "description": "Neural Machine Translation models for translating between languages",
        "supported_languages": ["swa", "hau", "yor", "zul", "amh"]
    },
    "ner": {
        "category": "llm",
        "description": "Named Entity Recognition models for identifying entities in text",
        "supported_languages": ["swa", "hau", "yor"]
    },
    "pos": {
        "category": "llm",
        "description": "Part-of-Speech tagging models for grammatical analysis",
        "supported_languages": ["swa", "yor", "hau"]
    },
    "sentiment": {
        "category": "llm",
        "description": "Sentiment analysis models for detecting emotional tone in text",
        "supported_languages": ["swa", "hau", "yor"]
    },
    "custom": {
        "category": "llm",
        "description": "Custom models for specialized tasks",
        "supported_languages": []
    }
}


@app.get("/api/v1/model-types", tags=["model-types"])
async def get_model_types() -> List[dict]:
    """
    Get all available model types.

    Returns:
        List of model types with id, name, category, description, and supported_languages
    """
    model_types = []
    for mt in ModelType:
        metadata = MODEL_TYPE_METADATA.get(mt.value, {
            "category": "llm",
            "description": f"{mt.name} model type",
            "supported_languages": []
        })
        model_types.append({
            "id": mt.value,
            "name": mt.name,
            "category": metadata["category"],
            "description": metadata["description"],
            "supported_languages": metadata["supported_languages"]
        })
    return model_types


@app.get("/api/v1/model-types/{model_type_id}", tags=["model-types"])
async def get_model_type(model_type_id: str) -> dict:
    """
    Get a specific model type by ID.

    Args:
        model_type_id: The model type identifier

    Returns:
        Model type details

    Raises:
        404: Model type not found
    """
    for mt in ModelType:
        if mt.value == model_type_id:
            metadata = MODEL_TYPE_METADATA.get(mt.value, {
                "category": "llm",
                "description": f"{mt.name} model type",
                "supported_languages": []
            })
            return {
                "id": mt.value,
                "name": mt.name,
                "category": metadata["category"],
                "description": metadata["description"],
                "supported_languages": metadata["supported_languages"]
            }
    raise HTTPException(status_code=404, detail=f"Model type '{model_type_id}' not found")


@app.get("/")
async def root():
    """
    Root endpoint with platform information.

    Returns:
        dict: Platform welcome message and documentation links
    """
    return {
        "message": "Welcome to the African Language Community Data Platform",
        "description": "Community-driven platform for African language voice AI development",
        "documentation": "/docs",
        "version": "1.0.0",
        "supported_languages": [
            "Twi (Akan)", "Yoruba", "Swahili", "Ga", "Ewe", "Xhosa"
        ],
        "language_families": [
            "Niger-Congo", "Afroasiatic", "Nilo-Saharan"
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True if settings.ENVIRONMENT == "development" else False
    )