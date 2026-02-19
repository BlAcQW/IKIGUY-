/**
 * Voice R&D Lab API client
 */

import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


// Using API_BASE_URL from api-config;

interface TTSModel {
  name: string;
  provider: string;
  languages: string[];
  features: string[];
  status: string;
}

interface TTSSynthesisRequest {
  text: string;
  model_id: string;
  language: string;
  voice_id?: string;
  parameters?: Record<string, any>;
}

interface VoiceCloningRequest {
  text: string;
  model_id: string;
  language: string;
  reference_audio: File;
}

interface ModelComparisonRequest {
  text: string;
  models: string[];
  language: string;
  parameters?: Record<string, any>;
}

/**
 * Get authentication headers using MongoDB auth
 */
async function getRequestHeaders() {
  const authHeaders = await getAuthHeaders();

  return {
    ...authHeaders,
    'Content-Type': 'application/json',
  };
}

/**
 * List all available TTS models
 */
export async function listTTSModels(): Promise<{ models: Record<string, TTSModel>; total: number }> {
  const headers = await getRequestHeaders();
  
  const response = await fetch(`${API_BASE_URL}/voice/rd-lab/models`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch models: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * List available datasets
 */
export async function listDatasets() {
  const headers = await getRequestHeaders();
  
  const response = await fetch(`${API_BASE_URL}/voice/rd-lab/datasets`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch datasets: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Synthesize speech using specified TTS model
 */
export async function synthesizeSpeech(request: TTSSynthesisRequest): Promise<Blob> {
  const headers = await getRequestHeaders();
  
  const response = await fetch(`${API_BASE_URL}/voice/rd-lab/synthesize`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Synthesis failed: ${error}`);
  }
  
  // Get metadata from headers
  const processingTime = response.headers.get('X-Processing-Time');
  const modelId = response.headers.get('X-Model-ID');
  const language = response.headers.get('X-Language');
  
  const blob = await response.blob();
  
  // Attach metadata to blob
  (blob as any).metadata = {
    processingTime,
    modelId,
    language,
  };
  
  return blob;
}

/**
 * Clone voice from reference audio
 */
export async function cloneVoice(request: VoiceCloningRequest) {
  const authHeaders = await getAuthHeaders();

  const formData = new FormData();
  formData.append('text', request.text);
  formData.append('model_id', request.model_id);
  formData.append('language', request.language);
  formData.append('reference_audio', request.reference_audio);

  const response = await fetch(`${API_BASE_URL}/voice/rd-lab/clone-voice`, {
    method: 'POST',
    headers: {
      ...authHeaders,
    },
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Voice cloning failed: ${error}`);
  }
  
  return response.json();
}

/**
 * Compare multiple TTS models
 */
export async function compareModels(request: ModelComparisonRequest) {
  const headers = await getRequestHeaders();
  
  const response = await fetch(`${API_BASE_URL}/voice/rd-lab/compare-models`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Model comparison failed: ${error}`);
  }
  
  return response.json();
}

/**
 * Get model information
 */
export async function getModelInfo(modelId: string) {
  const headers = await getRequestHeaders();
  
  const response = await fetch(`${API_BASE_URL}/voice/rd-lab/model/${modelId}/info`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch model info: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Get training guide
 */
export async function getTrainingGuide() {
  const headers = await getRequestHeaders();
  
  const response = await fetch(`${API_BASE_URL}/voice/rd-lab/training-guide`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch training guide: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Check health status of R&D Lab services
 */
export async function checkHealth() {
  const headers = await getRequestHeaders();
  
  const response = await fetch(`${API_BASE_URL}/voice/rd-lab/health`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  
  return response.json();
}

/**
 * Helper function to play audio blob
 */
export function playAudioBlob(blob: Blob) {
  const audioUrl = URL.createObjectURL(blob);
  const audio = new Audio(audioUrl);
  
  audio.play().catch(error => {
    console.error('Error playing audio:', error);
  });
  
  // Clean up URL after playing
  audio.addEventListener('ended', () => {
    URL.revokeObjectURL(audioUrl);
  });
  
  return audio;
}

/**
 * Helper function to download audio blob
 */
export function downloadAudioBlob(blob: Blob, filename: string = 'synthesized_speech.wav') {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}