import { vi } from 'vitest'

// Mock LLM providers
export const mockLLMProviders = [
	{
		id: "openai",
		name: "openai",
		display_name: "OpenAI",
		description: "Leading AI research company",
		website: "https://openai.com",
		api_base_url: "https://api.openai.com/v1",
		pricing_model: "per_token",
		features: ["chat", "completion", "embedding"],
		supported_languages: ["en", "es", "fr", "de"],
		max_context_length: 128000,
		is_active: true
	},
	{
		id: "anthropic",
		name: "anthropic",
		display_name: "Anthropic",
		description: "AI safety and research company",
		website: "https://anthropic.com",
		api_base_url: "https://api.anthropic.com",
		pricing_model: "per_token",
		features: ["chat", "completion"],
		supported_languages: ["en"],
		max_context_length: 200000,
		is_active: true
	},
	{
		id: "google",
		name: "google",
		display_name: "Google AI",
		description: "Google's AI research division",
		website: "https://ai.google",
		api_base_url: "https://generativelanguage.googleapis.com",
		pricing_model: "per_token",
		features: ["chat", "completion", "embedding"],
		supported_languages: ["en", "es", "fr", "de", "it", "pt"],
		max_context_length: 1000000,
		is_active: true
	}
]

// Mock LLM models
export const mockLLMModels = [
	{
		id: "gpt-4o",
		provider_id: "openai",
		name: "gpt-4o",
		display_name: "GPT-4o",
		description: "Most capable GPT-4 model",
		model_type: "chat",
		context_length: 128000,
		input_cost_per_1k_tokens: 0.005,
		output_cost_per_1k_tokens: 0.015,
		capabilities: ["chat", "completion", "reasoning"],
		supported_languages: ["en", "es", "fr", "de"],
		performance_metrics: {
			speed: "fast",
			quality: "highest"
		},
		is_active: true,
		is_default: true
	},
	{
		id: "gpt-4o-mini",
		provider_id: "openai",
		name: "gpt-4o-mini",
		display_name: "GPT-4o Mini",
		description: "Faster and more efficient GPT-4 model",
		model_type: "chat",
		context_length: 128000,
		input_cost_per_1k_tokens: 0.00015,
		output_cost_per_1k_tokens: 0.0006,
		capabilities: ["chat", "completion"],
		supported_languages: ["en", "es", "fr", "de"],
		performance_metrics: {
			speed: "very_fast",
			quality: "high"
		},
		is_active: true,
		is_default: false
	},
	{
		id: "claude-3-5-sonnet",
		provider_id: "anthropic",
		name: "claude-3-5-sonnet",
		display_name: "Claude 3.5 Sonnet",
		description: "Most capable Claude model",
		model_type: "chat",
		context_length: 200000,
		input_cost_per_1k_tokens: 0.003,
		output_cost_per_1k_tokens: 0.015,
		capabilities: ["chat", "completion", "reasoning"],
		supported_languages: ["en"],
		performance_metrics: {
			speed: "fast",
			quality: "highest"
		},
		is_active: true,
		is_default: true
	},
	{
		id: "gemini-1.5-pro",
		provider_id: "google",
		name: "gemini-1.5-pro",
		display_name: "Gemini 1.5 Pro",
		description: "Google's most capable model",
		model_type: "chat",
		context_length: 1000000,
		input_cost_per_1k_tokens: 0.00375,
		output_cost_per_1k_tokens: 0.015,
		capabilities: ["chat", "completion", "multimodal"],
		supported_languages: ["en", "es", "fr", "de", "it", "pt"],
		performance_metrics: {
			speed: "medium",
			quality: "highest"
		},
		is_active: true,
		is_default: true
	}
]

// Mock voice providers
export const mockVoiceProviders = [
	{
		id: "elevenlabs",
		name: "elevenlabs",
		display_name: "ElevenLabs",
		description: "AI voice synthesis platform",
		website: "https://elevenlabs.io",
		api_base_url: "https://api.elevenlabs.io/v1",
		provider_type: "TTS",
		pricing_model: "per_character",
		features: ["voice_cloning", "emotion_control"],
		supported_languages: ["en", "es", "fr", "de"],
		supported_voices: 100,
		max_audio_length: 5000,
		latency_ms: 400,
		is_active: true,
		is_default: true
	},
	{
		id: "openai",
		name: "openai",
		display_name: "OpenAI TTS",
		description: "OpenAI's text-to-speech service",
		website: "https://openai.com",
		api_base_url: "https://api.openai.com/v1",
		provider_type: "TTS",
		pricing_model: "per_character",
		features: ["high_quality", "multiple_voices"],
		supported_languages: ["en"],
		supported_voices: 6,
		max_audio_length: 4096,
		latency_ms: 300,
		is_active: true,
		is_default: false
	}
]

// Mock voices
export const mockVoices = [
	{
		id: "adam",
		provider_id: "elevenlabs",
		name: "adam",
		display_name: "Adam",
		description: "Professional male voice",
		gender: "male",
		language: "en",
		language_name: "English",
		country: "US",
		country_name: "United States",
		voice_type: "professional",
		sample_rate: 44100,
		quality: "high",
		features: ["emotion_control", "voice_cloning"],
		is_active: true,
		is_default: true
	},
	{
		id: "bella",
		provider_id: "elevenlabs",
		name: "bella",
		display_name: "Bella",
		description: "Friendly female voice",
		gender: "female",
		language: "en",
		language_name: "English",
		country: "US",
		country_name: "United States",
		voice_type: "friendly",
		sample_rate: 44100,
		quality: "high",
		features: ["emotion_control", "voice_cloning"],
		is_active: true,
		is_default: false
	}
]

// Mock voice agent config
export const mockVoiceAgentConfig = {
	stt_providers: mockVoiceProviders.filter(p => p.provider_type === "STT"),
	tts_providers: mockVoiceProviders.filter(p => p.provider_type === "TTS"),
	voice_providers: mockVoiceProviders,
	voices: mockVoices,
	llm_providers: mockLLMProviders,
	llm_models: mockLLMModels,
	languages: ["en", "es", "fr", "de", "it", "pt", "pl", "hi", "ja", "ko", "zh", "ar", "ru", "tr"],
	countries: ["US", "ES", "FR", "DE", "IT", "PT", "PL", "IN", "JP", "KR", "CN", "SA", "RU", "TR"],
	default_config: {
		stt_provider: "openai",
		stt_model: "gpt-4o-transcribe",
		tts_provider: "elevenlabs",
		tts_voice: "adam",
		llm_provider: "openai",
		llm_model: "gpt-4o",
		language: "en",
		country: "US"
	}
}

// Mock fetch for voice agent endpoints
export const mockVoiceAgentFetch = vi.fn()

// Setup mock responses
export const setupVoiceAgentMocks = () => {
	mockVoiceAgentFetch.mockImplementation((url: string) => {
		if (url.includes('/voice/agent/config')) {
			return Promise.resolve({
				ok: true,
				status: 200,
				json: () => Promise.resolve(mockVoiceAgentConfig)
			})
		}

		if (url.includes('/voice/assistants')) {
			return Promise.resolve({
				ok: true,
				status: 200,
				json: () => Promise.resolve([])
			})
		}

		// Default response for other endpoints
		return Promise.resolve({
			ok: false,
			status: 404,
			json: () => Promise.resolve({ error: 'Not found' })
		})
	})

	// Replace global fetch
	global.fetch = mockVoiceAgentFetch
}

// Cleanup function
export const cleanupVoiceAgentMocks = () => {
	vi.clearAllMocks()
}
