"""
F5-TTS Service Enhancement: Local Reference Audio Support

Add this code to your F5-TTS server to enable using local reference audio
files instead of uploading them via HTTP (bypasses file size limits).

Copy this file to RunPod: /workspace/f5tts_local_reference.py
Then integrate into your existing F5-TTS service.
"""

import os
from pathlib import Path
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import Response
import torchaudio

# Configuration
VOICE_REFERENCE_DIR = "/workspace/voice_references"

# Initialize directory
Path(VOICE_REFERENCE_DIR).mkdir(parents=True, exist_ok=True)


def add_local_reference_endpoints(app: FastAPI, f5tts_model):
    """
    Add local reference audio endpoints to existing F5-TTS FastAPI app.

    Args:
        app: FastAPI application instance
        f5tts_model: Your F5-TTS model instance
    """

    @app.post("/clone_local")
    async def clone_with_local_reference(
        text: str = Form(..., description="Text to synthesize"),
        reference_filename: str = Form(..., description="Filename in /workspace/voice_references/"),
        language: str = Form("en", description="Language code (en, zh, ja, ko)"),
        speed: float = Form(1.0, description="Speech speed (0.5-2.0)"),
        remove_silence: bool = Form(True, description="Remove silence from output")
    ):
        """
        Generate speech using local reference audio (no upload required).

        This endpoint allows using large reference audio files (>1GB) that would
        be too large to upload via HTTP. The reference audio must be pre-uploaded
        to /workspace/voice_references/ directory.

        Example:
            POST /clone_local
            Form data:
                text: "Hello, this is a test"
                reference_filename: "archbishop_56min.wav"
                language: "en"
                speed: 1.0
        """
        # Build full path
        reference_path = os.path.join(VOICE_REFERENCE_DIR, reference_filename)

        # Validate file exists
        if not os.path.exists(reference_path):
            raise HTTPException(
                status_code=404,
                detail=f"Reference audio not found: {reference_filename}. "
                       f"Available files: {list_voice_references_sync()}"
            )

        # Security check: prevent path traversal
        resolved_path = os.path.realpath(reference_path)
        if not resolved_path.startswith(os.path.realpath(VOICE_REFERENCE_DIR)):
            raise HTTPException(
                status_code=403,
                detail="Access denied: Invalid file path"
            )

        try:
            # Load audio from local filesystem
            audio, sample_rate = torchaudio.load(reference_path)

            # Generate speech with F5-TTS
            # NOTE: Adjust this based on your actual F5-TTS model interface
            result_audio = f5tts_model.infer(
                text=text,
                reference_audio=audio,
                reference_sr=sample_rate,
                language=language,
                speed=speed,
                remove_silence=remove_silence
            )

            # Convert to bytes (adjust format as needed)
            # This is a placeholder - use your actual audio output format
            import io
            buffer = io.BytesIO()
            torchaudio.save(buffer, result_audio, sample_rate, format="wav")
            audio_bytes = buffer.getvalue()

            return Response(
                content=audio_bytes,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": f"attachment; filename=output.wav"
                }
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Voice cloning failed: {str(e)}"
            )

    @app.get("/voice_references")
    async def list_voice_references():
        """
        List all available pre-uploaded voice reference files.

        Returns:
            Dictionary with list of available reference files and their metadata
        """
        files = []

        try:
            for filename in os.listdir(VOICE_REFERENCE_DIR):
                filepath = os.path.join(VOICE_REFERENCE_DIR, filename)

                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    files.append({
                        "filename": filename,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": stat.st_mtime,
                        "path": filepath
                    })

            # Sort by filename
            files.sort(key=lambda x: x["filename"])

            return {
                "voice_references": files,
                "total": len(files),
                "directory": VOICE_REFERENCE_DIR
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list voice references: {str(e)}"
            )

    def list_voice_references_sync():
        """Synchronous version for error messages"""
        try:
            return [f for f in os.listdir(VOICE_REFERENCE_DIR) if os.path.isfile(os.path.join(VOICE_REFERENCE_DIR, f))]
        except:
            return []

    @app.post("/upload_reference")
    async def upload_reference_file(
        filename: str = Form(...),
        audio_data: bytes = Form(...)
    ):
        """
        Upload a reference audio file to local storage.

        This is an alternative to SCP for uploading reference files.
        Use this if you don't have SSH access but need to upload via HTTP.

        Note: Still has file size limits (~1GB depending on nginx config)
        """
        # Validate filename
        if "/" in filename or "\\" in filename or ".." in filename:
            raise HTTPException(
                status_code=400,
                detail="Invalid filename"
            )

        filepath = os.path.join(VOICE_REFERENCE_DIR, filename)

        try:
            # Write file
            with open(filepath, "wb") as f:
                f.write(audio_data)

            file_size = os.path.getsize(filepath)

            return {
                "message": "Reference file uploaded successfully",
                "filename": filename,
                "path": filepath,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2)
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Upload failed: {str(e)}"
            )

    return app


# Integration Example
if __name__ == "__main__":
    """
    Example integration with existing F5-TTS server.

    In your actual F5-TTS server file, add:

    from f5tts_local_reference import add_local_reference_endpoints

    # After creating your FastAPI app and loading F5-TTS model:
    app = add_local_reference_endpoints(app, f5tts_model)
    """

    from fastapi import FastAPI
    import uvicorn

    # Create FastAPI app
    app = FastAPI(
        title="F5-TTS with Local Reference Support",
        description="Enhanced F5-TTS with local reference audio support"
    )

    # Placeholder for F5-TTS model
    class MockF5TTSModel:
        def infer(self, text, reference_audio, reference_sr, language, speed, remove_silence):
            # This is a mock - replace with actual F5-TTS inference
            import torch
            # Return dummy audio
            return torch.randn(1, 16000 * 2)  # 2 seconds at 16kHz

    mock_model = MockF5TTSModel()

    # Add local reference endpoints
    app = add_local_reference_endpoints(app, mock_model)

    # Add health endpoint
    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "F5-TTS"}

    print("=" * 60)
    print("F5-TTS Server with Local Reference Support")
    print("=" * 60)
    print()
    print("Endpoints:")
    print("  POST /clone_local       - Clone voice with local reference")
    print("  GET  /voice_references  - List available reference files")
    print("  POST /upload_reference  - Upload reference file via HTTP")
    print("  GET  /health            - Health check")
    print()
    print(f"Reference directory: {VOICE_REFERENCE_DIR}")
    print()

    # Run server
    uvicorn.run(app, host="0.0.0.0", port=8002)
