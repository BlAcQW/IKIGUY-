"""
API router initialization for StudyFlow.

Aggregates all API routes.
"""

from fastapi import APIRouter

from app.api.routes import auth, materials, tutoring, progress, wallet, usage, analytics, schools, organizations, billing, feedback, voice_settings, collections, voice_chat, assessments, cost_dashboard, dashboard, certificates, gamification, voice_library, exercises, vapi_tutoring, material_voice, voice_agent

api_router = APIRouter()

# Include all routes
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(billing.router)
api_router.include_router(schools.router)
api_router.include_router(materials.router)
api_router.include_router(exercises.router)
api_router.include_router(tutoring.router)
api_router.include_router(vapi_tutoring.router)  # VAPI voice tutoring
api_router.include_router(progress.router)
api_router.include_router(wallet.router)
api_router.include_router(usage.router)
api_router.include_router(analytics.router)
api_router.include_router(feedback.router)
api_router.include_router(voice_settings.router)
# Note: TTS routes now provided by unified @shared/routes/tts_routes.py at /api/tts
# Removed redundant local tts.router (2025-11-23)
api_router.include_router(voice_library.router, prefix="/voice-library", tags=["Voice Library"])
api_router.include_router(collections.router)
api_router.include_router(voice_chat.router)
api_router.include_router(material_voice.router)  # Browser-based voice chat for materials
api_router.include_router(assessments.router)
api_router.include_router(cost_dashboard.router)
api_router.include_router(dashboard.router)
api_router.include_router(certificates.router)
api_router.include_router(gamification.router)
api_router.include_router(voice_agent.router)  # Real-time voice agent (VoiceAgent approach)
