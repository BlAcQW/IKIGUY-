"""WebSocket endpoint for continuous voice conversation with Meta MMS"""

import asyncio
import json
import base64
import logging
import numpy as np
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect, Query
import google.generativeai as genai
import os
from transformers import VitsModel, AutoTokenizer, AutoProcessor, Wav2Vec2ForCTC
import torch
import torchaudio
import scipy.io.wavfile as wavfile
import io
import tempfile
import os
import wave
import struct

logger = logging.getLogger(__name__)

class VoiceConversationManager:
    def __init__(self):
        self.gemini_model = None
        self.tts_model = None
        self.tts_tokenizer = None
        self.stt_processor = None
        self.stt_model = None
        self.conversation_history = []
        self.is_processing = False
        self.lang_code = "eng"
        
    async def initialize(self, lang_code: str = "eng"):
        """Initialize models for the conversation"""
        try:
            self.lang_code = lang_code
            
            # Initialize Gemini
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAACjmMMYIVH2Pq8Ns8KbOud-X8oCQMny4")
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Initialize TTS model
            tts_model_id = f"facebook/mms-tts-{lang_code}"
            self.tts_model = VitsModel.from_pretrained(tts_model_id)
            self.tts_tokenizer = AutoTokenizer.from_pretrained(tts_model_id)
            
            # Initialize STT model
            stt_model_id = "facebook/mms-1b-all"
            self.stt_processor = AutoProcessor.from_pretrained(stt_model_id)
            self.stt_model = Wav2Vec2ForCTC.from_pretrained(stt_model_id)
            
            # Set target language for STT
            self.stt_processor.tokenizer.set_target_lang(lang_code)
            self.stt_model.load_adapter(lang_code)
            
            logger.info(f"Models initialized for language: {lang_code}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
            return False
    
    def decode_wav_from_bytes(self, audio_bytes: bytes) -> tuple:
        """Decode WAV audio bytes to numpy array and sample rate"""
        try:
            with io.BytesIO(audio_bytes) as wav_buffer:
                with wave.open(wav_buffer, 'rb') as wav_file:
                    sample_rate = wav_file.getframerate()
                    frames = wav_file.readframes(wav_file.getnframes())
                    
                    # Convert bytes to numpy array
                    audio_array = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    return audio_array, sample_rate
        except Exception as e:
            logger.error(f"Error decoding WAV: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio to text using Meta MMS"""
        try:
            # Decode WAV audio
            audio_array, sample_rate = self.decode_wav_from_bytes(audio_data)
            logger.info(f"Audio shape: {audio_array.shape}, sample rate: {sample_rate}")
            
            # Resample to 16kHz if needed (MMS expects 16kHz)
            if sample_rate != 16000:
                import torchaudio
                logger.info(f"Resampling from {sample_rate} to 16000 Hz")
                audio_tensor = torch.from_numpy(audio_array).unsqueeze(0)
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                audio_tensor = resampler(audio_tensor)
                audio_array = audio_tensor.squeeze(0).numpy()
                sample_rate = 16000
            
            # Process audio for STT
            inputs = self.stt_processor(audio_array, sampling_rate=sample_rate, return_tensors="pt")
            
            with torch.no_grad():
                outputs = self.stt_model(**inputs).logits
                
            ids = torch.argmax(outputs, dim=-1)[0]
            transcription = self.stt_processor.decode(ids)
            
            logger.info(f"Transcribed: {transcription}")
            return transcription
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return ""
    
    async def generate_response(self, text: str) -> str:
        """Generate response using Gemini"""
        try:
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": text})
            
            # Build context
            context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in self.conversation_history[-10:]  # Keep last 10 messages
            ])
            
            # Get greeting based on language
            greetings = {
                "aka": "Respond in Akan/Twi. Be friendly and conversational.",
                "ewe": "Respond in Ewe. Be friendly and conversational.",
                "yor": "Respond in Yoruba. Be friendly and conversational.",
                "hau": "Respond in Hausa. Be friendly and conversational.",
                "eng": "Respond in English. Be friendly and conversational."
            }
            
            prompt = f"{greetings.get(self.lang_code, greetings['eng'])}\n\nConversation:\n{context}\n\nAssistant:"
            
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text
            
            # Add to history
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            logger.info(f"Generated response: {response_text}")
            return response_text
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return "I'm sorry, I couldn't process that."
    
    async def synthesize_speech(self, text: str) -> bytes:
        """Convert text to speech using Meta MMS"""
        try:
            inputs = self.tts_tokenizer(text, return_tensors="pt")
            
            with torch.no_grad():
                output = self.tts_model(**inputs).waveform
            
            # Convert to audio bytes
            waveform = output.squeeze().cpu().numpy()
            waveform = np.int16(waveform * 32767)
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(waveform.tobytes())
            
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""

async def websocket_conversation(websocket: WebSocket, lang_code: str = Query(default="eng")):
    """WebSocket endpoint for continuous voice conversation"""
    logger.info(f"WebSocket connection attempt for language: {lang_code}")
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    manager = VoiceConversationManager()
    
    try:
        # Initialize models
        logger.info(f"Initializing models for language: {lang_code}")
        success = await manager.initialize(lang_code)
        if not success:
            await websocket.send_json({
                "type": "error",
                "message": "Failed to initialize models"
            })
            await websocket.close()
            return
        
        # Send ready signal
        await websocket.send_json({
            "type": "ready",
            "message": "Conversation started. Listening..."
        })
        
        while True:
            # Receive audio data
            message = await websocket.receive_json()
            logger.info(f"Received message type: {message.get('type')}")
            
            if message["type"] == "audio":
                # Decode base64 audio
                audio_data = base64.b64decode(message["data"])
                logger.info(f"Received audio data: {len(audio_data)} bytes")
                
                # Send processing status
                await websocket.send_json({
                    "type": "status",
                    "message": "Processing..."
                })
                
                # Transcribe audio
                transcript = await manager.transcribe_audio(audio_data)
                
                if transcript:
                    # Send transcript
                    await websocket.send_json({
                        "type": "transcript",
                        "text": transcript
                    })
                    
                    # Generate response
                    response_text = await manager.generate_response(transcript)
                    
                    # Send response text
                    await websocket.send_json({
                        "type": "response",
                        "text": response_text
                    })
                    
                    # Synthesize speech
                    audio_response = await manager.synthesize_speech(response_text)
                    
                    if audio_response:
                        # Send audio response
                        await websocket.send_json({
                            "type": "audio_response",
                            "data": base64.b64encode(audio_response).decode()
                        })
                    
                    # Ready for next input
                    await websocket.send_json({
                        "type": "ready",
                        "message": "Listening..."
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Could not understand audio"
                    })
                    
            elif message["type"] == "stop":
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        try:
            await websocket.close()
        except:
            pass