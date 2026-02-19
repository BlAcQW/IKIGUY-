"""
Shared Routes Module

Provides reusable FastAPI routers for all KasaAI applications.

Usage:
    from apps.shared.routes.tts_routes import router as tts_router
    from apps.shared.routes.provider_routes import router as provider_router
    from apps.shared.routes.asr_routes import router as asr_router
    from apps.shared.routes.llm_routes import router as llm_router
    from apps.shared.routes.voice_settings_routes import create_voice_settings_router
    from apps.shared.routes.conversation_routes import create_conversation_router
    from apps.shared.routes.storage_routes import create_storage_router

    app.include_router(tts_router, prefix="/api/tts", tags=["TTS"])
    app.include_router(provider_router, prefix="/api/v1", tags=["Providers"])
    app.include_router(asr_router, prefix="/api/asr", tags=["ASR"])
    app.include_router(llm_router, prefix="/api/llm", tags=["LLM"])
    
    # Storage file serving (part of Hetzner Storage Box and Drive Service)
    storage_service = StorageFileService(storage_backend=hetzner_storage, base_path="kasaai/inkwave")
    storage_router = create_storage_router(storage_service, prefix="/api/v1/storage")
    app.include_router(storage_router)

Available Routers:
    - tts_routes.router: TTS synthesis, provider listing, cost estimation
    - provider_routes.router: Unified provider discovery for TTS, ASR, LLM
    - asr_routes.router: ASR transcription with billing
    - llm_routes.router: LLM chat with streaming
    - voice_settings_routes: Factory for voice settings (requires auth injection)
    - conversation_routes: Factory for conversation pipeline (requires auth injection)
    - storage_routes: Factory for file serving from Hetzner storage (part of drive service)

Author: KasaAI Team
Date: 2025-11-26
"""

# Note: Imports are done explicitly from submodules to avoid circular imports
# and missing export issues. Import directly from the module you need.
#
# Example:
#   from apps.shared.routes.tts_routes import router as tts_router
#   from apps.shared.routes.provider_routes import router as provider_router
#   from apps.shared.routes.conversation_routes import create_conversation_router
#   from apps.shared.routes.storage_routes import create_storage_router
#   from apps.shared.routes.storage_routes import create_storage_router

