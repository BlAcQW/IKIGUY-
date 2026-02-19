"""
InkWave - Interactive AI Bookshop Backend.

A mobile-first audiobook platform with AI-powered voice interaction.

Features:
- Voice Q&A with RAG (Gemini 2.5 Flash)
- Audio book library
- Reading progress tracking
- Wallet & usage management

Integrates with @apps/shared/integration/ services:
- GeminiService for RAG
- STTService for Whisper transcription
- TTSService for OpenAI TTS
- WalletService for payments
"""

# Load environment variables BEFORE any other imports
from dotenv import load_dotenv
from pathlib import Path

# Get the backend directory (parent of app/)
backend_dir = Path(__file__).parent.parent
env_file = backend_dir / ".env"
load_dotenv(dotenv_path=env_file)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import sys
import os
from pathlib import Path

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.core.config import settings
from app.core.database import Database
from app.core.cache import CacheService
from app.api.routes import books, voice, admin, wallet, analytics, organizations, feedback, voice_settings, reading, interaction, recommendations, audio, voice_library, profile, auth, tts, payments, audiobook, author_images, book_voice_settings, storage, book_invitations, comments, social, users, leaderboard, tracking, book_clubs, achievements, streaks, notifications, authors, bookmarks, consumption
from app.api.websocket import voice_chat as ws_voice_chat, webrtc_signaling as ws_webrtc
from apps.shared.middleware import OrganizationContextMiddleware
from apps.shared.services.organization_service import get_organization_service
from apps.shared.routes.tts_routes import router as unified_tts_router
from apps.shared.routes.provider_routes import router as provider_router
from apps.shared.routes.asr_routes import router as asr_router
from apps.shared.routes.llm_routes import router as llm_router
from apps.shared.routes.voice_settings_routes import create_voice_settings_router
from apps.shared.routes.reference_audio_routes import create_reference_audio_router
from apps.shared.routes.url_shortening_routes import create_url_shortening_router
from apps.shared.startup import initialize_default_organization
from app.core.auth import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")

    # Connect to database
    await Database.connect()
    print("✅ MongoDB connected")

    # Connect to Redis cache
    await CacheService.connect()

    # Initialize organization service
    db = Database.get_database()
    org_service = get_organization_service(db)
    await org_service.initialize_indexes()
    print("✅ Organization service initialized")

    # Initialize default organization
    await initialize_default_organization()

    # Initialize default provider configurations
    try:
        from app.services.provider_service import ProviderService
        await ProviderService.initialize_default_providers()
        print("✅ Default providers initialized")
    except Exception as e:
        print(f"⚠️  Provider initialization error: {e}")

    # Initialize wallet service
    try:
        from app.services.wallet_service import get_wallet_service
        wallet_service = await get_wallet_service(db=db)
        if wallet_service.initialized:
            print("✅ Wallet service initialized")
        else:
            print("⚠️  Wallet service failed to initialize - wallet features may be unavailable")
    except Exception as e:
        print(f"⚠️  Wallet service initialization error: {e}")

    # Create indexes for payment records collection (persistent idempotency)
    try:
        await db.payment_records.create_index("reference", unique=True)
        await db.payment_records.create_index("user_id")
        await db.payment_records.create_index("status")
        await db.payment_records.create_index("created_at")
        print("✅ Payment records indexes created")
    except Exception as e:
        print(f"⚠️  Payment records index creation error: {e}")

    # Initialize storage file serving routes (using shared service from @shared)
    try:
        from app.api.routes.storage import create_inkwave_storage_router
        storage_router = await create_inkwave_storage_router()
        app.include_router(storage_router)
        print("✅ Storage file serving routes initialized (using @shared service)")
    except Exception as e:
        print(f"⚠️  Storage routes initialization error: {e}")

    print(f"📖 API Documentation: /api/docs")
    print(f"🎙️  Voice Q&A: {settings.API_V1_PREFIX}/voice/qa")
    print(f"📚 Books API: {settings.API_V1_PREFIX}/books")
    print(f"👤 Admin Panel: {settings.API_V1_PREFIX}/admin")
    print(f"💰 Wallet API: {settings.API_V1_PREFIX}/wallet/balance")

    yield
    # Shutdown
    print(f"👋 {settings.APP_NAME} shutting down...")
    await CacheService.disconnect()
    await Database.disconnect()
    print("✅ MongoDB disconnected")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Interactive AI Bookshop - Audio learning platform with voice Q&A",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Organization Context Middleware
app.add_middleware(OrganizationContextMiddleware)

# Mount static files for avatars and uploads
static_path = Path(__file__).parent.parent / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Register API routes
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)  # Authentication
app.include_router(book_invitations.router, prefix=settings.API_V1_PREFIX)  # Book invitations
app.include_router(organizations.router, prefix=settings.API_V1_PREFIX)
app.include_router(profile.router, prefix=settings.API_V1_PREFIX)  # User profile
# Social features
app.include_router(social.router, prefix=settings.API_V1_PREFIX)  # Social (follow/unfollow/block)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)  # User discovery (search/profiles)
app.include_router(leaderboard.router, prefix=settings.API_V1_PREFIX)  # Leaderboard (top listeners)
app.include_router(achievements.router, prefix=settings.API_V1_PREFIX)  # Achievements & badges
app.include_router(streaks.router, prefix=settings.API_V1_PREFIX)  # Daily listening streaks
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)  # In-app notifications
app.include_router(books.router, prefix=settings.API_V1_PREFIX)
app.include_router(book_voice_settings.router, prefix=settings.API_V1_PREFIX)
app.include_router(comments.router, prefix=settings.API_V1_PREFIX)  # Book comments/reviews
app.include_router(book_clubs.router, prefix=settings.API_V1_PREFIX)  # Book clubs
app.include_router(reading.router, prefix=settings.API_V1_PREFIX)
app.include_router(bookmarks.router, prefix=settings.API_V1_PREFIX)  # Bookmarked books

# Storage file serving (using shared service from @shared)
# This will be initialized in the lifespan context
app.include_router(interaction.router, prefix=settings.API_V1_PREFIX)
app.include_router(audio.router, prefix=settings.API_V1_PREFIX)  # Audio narration
app.include_router(voice.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)
app.include_router(wallet.router, prefix=settings.API_V1_PREFIX)
app.include_router(payments.router, prefix=settings.API_V1_PREFIX)  # ExpressPay payments
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(tracking.router, prefix=settings.API_V1_PREFIX)  # Error & event tracking
app.include_router(consumption.router, prefix=settings.API_V1_PREFIX)  # Consumption activity tracking
app.include_router(feedback.router, prefix=settings.API_V1_PREFIX)
app.include_router(voice_settings.router, prefix=settings.API_V1_PREFIX)
app.include_router(tts.router, prefix=settings.API_V1_PREFIX)
app.include_router(voice_library.router, prefix=f"{settings.API_V1_PREFIX}/voice-library", tags=["Voice Library"])
# Also mount at /api/voice-library for consistency with other apps
app.include_router(voice_library.router, prefix="/api/voice-library", tags=["Voice Library"])
# Reference Audio (using shared router)
reference_audio_router = create_reference_audio_router(
    get_current_user_func=get_current_user,
    storage_config={
        "username": os.getenv("HETZNER_STORAGE_USERNAME"),
        "password": os.getenv("HETZNER_STORAGE_PASSWORD"),
        "host": os.getenv("HETZNER_STORAGE_HOST")
    },
    storage_base_path="inkwave/reference_audio"  # App-specific path
)
app.include_router(reference_audio_router, prefix=settings.API_V1_PREFIX, tags=["Reference Audio"])
app.include_router(recommendations.router, prefix=settings.API_V1_PREFIX)
app.include_router(audiobook.router, prefix=settings.API_V1_PREFIX)  # Audiobook narration
app.include_router(author_images.router, prefix=settings.API_V1_PREFIX)  # Author image search
app.include_router(authors.router, prefix=settings.API_V1_PREFIX)  # Author management

# Short URLs - using shared service (both API endpoints and redirect)
url_shortening_router = create_url_shortening_router(
    get_database_func=lambda: Database.get_database(),
    base_url=getattr(settings, 'FRONTEND_URL', 'https://inkwave.ailabsafrica.com'),
    app_name="inkwave"
)
app.include_router(url_shortening_router, prefix=settings.API_V1_PREFIX, tags=["Short URLs"])  # /api/v1/short-urls/*
app.include_router(url_shortening_router, tags=["Short URLs"])  # /s/{short_code} redirect

# WebSocket routes for real-time voice chat
app.include_router(ws_voice_chat.router, prefix="/ws", tags=["Voice Chat WebSocket"])
app.include_router(ws_webrtc.router, prefix="/ws", tags=["WebRTC Signaling"])

# Include unified TTS routes (new standardized endpoints)
app.include_router(unified_tts_router, prefix="/api/tts", tags=["TTS Unified"])

# Include unified provider discovery routes (TTS, ASR, LLM)
app.include_router(provider_router, prefix="/api/v1", tags=["Providers"])

# Include unified ASR routes
app.include_router(asr_router, prefix="/api/asr", tags=["ASR"])

# Include ASR WebSocket routes (mounted at /ws/asr for frontend compatibility)
from apps.shared.routes.asr_routes import ws_router as asr_ws_router
app.include_router(asr_ws_router, prefix="/ws/asr", tags=["ASR WebSocket"])

# Include unified LLM routes
app.include_router(llm_router, prefix="/api/llm", tags=["LLM"])

# Include unified voice settings routes
unified_voice_settings_router = create_voice_settings_router(
    get_current_user_func=get_current_user,
    get_database_func=lambda: Database.get_database()
)
app.include_router(unified_voice_settings_router, prefix="/api/voice-settings", tags=["Voice Settings"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "tagline": "Your AI-powered audiobook companion",
        "version": settings.APP_VERSION,
        "status": "active",
        "docs": "/api/docs",
        "features": [
            "Voice Q&A with RAG (Gemini 2.5 Flash)",
            "OpenAI Whisper STT",
            "OpenAI TTS",
            "Reading progress tracking",
            "Wallet & usage management"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "inkwave-backend",
        "version": settings.APP_VERSION
    }
