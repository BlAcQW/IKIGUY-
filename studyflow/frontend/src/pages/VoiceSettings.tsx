/**
 * Voice Settings Page
 * Configure voice preferences for TTS, ASR, and LLM
 */

import React, { useState, useEffect } from 'react';
import {
	Volume2,
	Mic,
	Brain,
	Star,
	Save,
	RotateCcw,
	AlertCircle,
	CheckCircle,
	ChevronRight,
	MessageSquare
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { API_BASE_URL, CORE_API_URL, WS_BASE_URL } from '../config/api-config';
import { VoiceGallery } from '../components/voice-library';
import { useVoiceLibrary } from '../hooks/useVoiceLibrary';
import { ComprehensiveTTSSelector } from '../../../../shared/frontend/components/voice-settings/ComprehensiveTTSSelector';
import { useComprehensiveTTS } from '../../../../shared/frontend/hooks/useComprehensiveTTS';
import { VoiceTestingPanel } from '../../../../shared/frontend/components/VoiceTestingPanel';
import { LLMChatTestPanel } from '../../../../shared/frontend/components/voice-settings/LLMChatTestPanel';
import { ASRStreamingTestPanel } from '../../../../shared/frontend/components/voice-settings/ASRStreamingTestPanel';
import { getAuthHeaders, getAuthToken } from '../lib/auth-utils';

interface VoiceSettings {
	user_id: string;
	organization_id: string;
	tts: {
		default_provider: string;
		default_voice: string | null;
		speed: number;
		pitch: number;
	};
	asr: {
		default_provider: string;
		language: string;
		task: string;
	};
	llm: {
		default_model: string;
		temperature: number;
		max_tokens: number;
	};
	voices: {
		favorite_voices: string[];
		custom_voices: string[];
	};
}

export default function VoiceSettings() {
	const navigate = useNavigate();
	const [settings, setSettings] = useState<VoiceSettings | null>(null);
	const [isLoading, setIsLoading] = useState(true);
	const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
	const [isDirty, setIsDirty] = useState(false);
	const [activeTab, setActiveTab] = useState<'tts' | 'asr' | 'llm' | 'voices' | 'test'>('tts');
	const { addToFavorites, removeFromFavorites, getFavorites } = useVoiceLibrary();
	const [favoriteVoices, setFavoriteVoices] = useState<string[]>([]);

	// ASR providers state
	const [asrProviders, setAsrProviders] = useState<Array<{
		id: string;
		name: string;
		description: string;
		icon: string;
		status: string;
		languages?: number;
		metadata?: Record<string, any>;
	}>>([]);
	const [loadingASRProviders, setLoadingASRProviders] = useState(false);

	// LLM providers state
	const [llmProviders, setLlmProviders] = useState<Array<{
		id: string;
		name: string;
		description: string;
		icon: string;
		status: string;
		languages?: number;
		languageList?: string[];
		capabilities?: Record<string, any>;
		metadata?: Record<string, any>;
	}>>([]);
	const [loadingLLMProviders, setLoadingLLMProviders] = useState(false);

	// Preview state
	const [previewLoading, setPreviewLoading] = useState(false);
	const [previewAudio, setPreviewAudio] = useState<HTMLAudioElement | null>(null);
	const [previewText, setPreviewText] = useState('Hello, this is a preview of the selected voice.');

	// Use comprehensive TTS hook for provider selection
	const {
		providers: comprehensiveTTSProviders,
		loading: loadingComprehensiveTTS,
		error: comprehensiveTTSError
	} = useComprehensiveTTS(API_BASE_URL, undefined, {
		onlineOnly: false,
		autoFetch: true,
		endpointPath: '/api/tts/providers',
		getAuthHeaders,
		skipWalletBalance: true
	});

	// Handle voice preview
	const handlePreviewVoice = async (previewText: string) => {
		if (!settings?.tts.default_provider) {
			alert('Please select a TTS provider first');
			return;
		}

		if (previewAudio) {
			previewAudio.pause();
			previewAudio.currentTime = 0;
		}

		setPreviewLoading(true);

		try {
			// Use unified TTS API - accepts both field name formats (provider_id/provider, voice_id/speaker)
			const synthesisRequest = {
				provider_id: settings.tts.default_provider,
				text: previewText,
				language: 'en',
				voice_id: settings.tts.default_voice || undefined,
				speed: settings.tts.speed || 1.0,
				pitch: settings.tts.pitch || 0.0,
				output_format: 'wav'
			};

			const authHeaders = await getAuthHeaders();

			// Use preview endpoint (no billing required)
			const response = await fetch(`${API_BASE_URL}/api/tts/preview`, {
				method: 'POST',
				headers: {
					...authHeaders,
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(synthesisRequest),
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({ detail: response.statusText }));
				throw new Error(errorData.detail || 'TTS synthesis failed');
			}

			const data = await response.json();

			if (data.audio_base64) {
				const audioBlob = await fetch(`data:audio/wav;base64,${data.audio_base64}`).then(r => r.blob());
				const audioUrl = URL.createObjectURL(audioBlob);

				const audio = new Audio(audioUrl);
				setPreviewAudio(audio);

				audio.onended = () => {
					URL.revokeObjectURL(audioUrl);
				};

				await audio.play();
			} else {
				throw new Error('No audio data returned from TTS service');
			}
		} catch (error: any) {
			console.error('TTS preview failed:', error);
			alert(error.message || 'Preview failed');
		} finally {
			setPreviewLoading(false);
		}
	};

	useEffect(() => {
		loadSettings();
		loadFavorites();
		loadProviders();
	}, []);

	const loadFavorites = async () => {
		try {
			const favorites = await getFavorites();
			setFavoriteVoices(favorites.map((v: any) => v.voice_id));
		} catch (error) {
			console.error('Failed to load favorite voices:', error);
		}
	};

	const loadProviders = async () => {
		try {
			setLoadingASRProviders(true);
			setLoadingLLMProviders(true);
			const authHeaders = await getAuthHeaders();
			const response = await fetch(`${API_BASE_URL}/api/v1/voice-settings/providers`, {
				headers: authHeaders,
			});

			if (!response.ok) {
				throw new Error('Failed to load providers');
			}

			const data = await response.json();
			if (data.asr_providers && Array.isArray(data.asr_providers)) {
				setAsrProviders(data.asr_providers);
			}
			if (data.llm_providers && Array.isArray(data.llm_providers)) {
				setLlmProviders(data.llm_providers);
			}
		} catch (error) {
			console.error('Failed to load providers:', error);
		} finally {
			setLoadingASRProviders(false);
			setLoadingLLMProviders(false);
		}
	};

	const loadSettings = async () => {
		try {
			setIsLoading(true);
			const data = await api.voiceSettings.getMySettings();
			// Set default providers if not already set (for better UX)
			const settingsWithDefaults = {
				...data,
				tts: {
					...data.tts,
					default_provider: data.tts.default_provider || 'coqui_tts',
				},
				asr: {
					...data.asr,
					default_provider: data.asr.default_provider || 'faster_whisper_large',
					language: data.asr.language || 'en',
				},
				llm: {
					...data.llm,
					default_model: data.llm.default_model || 'gemini-2.5-flash',
					temperature: data.llm.temperature ?? 0.7,
					max_tokens: data.llm.max_tokens ?? 1000,
				},
			};
			setSettings(settingsWithDefaults);
			setIsDirty(false);
		} catch (error: any) {
			console.error('Failed to load voice settings:', error);
			setSaveStatus('error');
		} finally {
			setIsLoading(false);
		}
	};

	const handleSave = async () => {
		if (!settings || !isDirty) return;

		try {
			setSaveStatus('saving');
			await api.voiceSettings.updateMySettings({
				tts: settings.tts,
				asr: settings.asr,
				llm: settings.llm,
				voices: settings.voices,
			});
			setSaveStatus('success');
			setIsDirty(false);
			setTimeout(() => setSaveStatus('idle'), 3000);
		} catch (error: any) {
			console.error('Failed to save voice settings:', error);
			setSaveStatus('error');
			setTimeout(() => setSaveStatus('idle'), 3000);
		}
	};

	const handleReset = () => {
		if (window.confirm('Are you sure you want to reset your changes?')) {
			loadSettings();
		}
	};

	const updateSettings = (updates: Partial<VoiceSettings>) => {
		if (!settings) return;
		setSettings({ ...settings, ...updates });
		setIsDirty(true);
	};

	const handleFavoriteToggle = async (voiceId: string, isFavorite: boolean) => {
		try {
			if (isFavorite) {
				await removeFromFavorites(voiceId);
				setFavoriteVoices(prev => prev.filter(id => id !== voiceId));
			} else {
				await addToFavorites(voiceId);
				setFavoriteVoices(prev => [...prev, voiceId]);
			}
		} catch (error) {
			console.error('Failed to update favorites:', error);
		}
	};

	const SettingSection = ({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) => (
		<div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
			<div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
				<div className="flex items-center gap-3">
					<div className="p-2 bg-white rounded-lg shadow-sm">
						<Icon className="w-5 h-5 text-blue-600" />
					</div>
					<h3 className="text-lg font-semibold text-gray-900">{title}</h3>
				</div>
			</div>
			<div className="p-6">
				{children}
			</div>
		</div>
	);

	const tabs = [
		{ id: 'tts' as const, label: 'Text-to-Speech', icon: Volume2 },
		{ id: 'asr' as const, label: 'Speech Recognition', icon: Mic },
		{ id: 'llm' as const, label: 'Language Model', icon: Brain },
		{ id: 'voices' as const, label: 'Voice Library', icon: Star },
		{ id: 'test' as const, label: 'Test Conversation', icon: MessageSquare },
	];

	if (isLoading) {
		return (
			<div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
					<p className="text-gray-600">Loading voice settings...</p>
				</div>
			</div>
		);
	}

	if (!settings) {
		return (
			<div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
				<div className="text-center">
					<AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
					<p className="text-gray-600">Failed to load voice settings</p>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
			{/* Header */}
			<header className="bg-white border-b border-gray-200">
				<div className="max-w-7xl mx-auto px-6 py-6">
					<div className="flex items-center justify-between">
						<div>
							<h1 className="text-3xl font-bold text-gray-900">Voice Settings</h1>
							<p className="text-gray-600 mt-1">Configure your voice preferences for TTS, ASR, and LLM</p>
						</div>
						<div className="flex items-center gap-3">
							{saveStatus === 'success' && (
								<div className="flex items-center gap-2 text-green-600">
									<CheckCircle className="w-5 h-5" />
									<span className="text-sm font-medium">Saved successfully!</span>
								</div>
							)}
							{saveStatus === 'error' && (
								<div className="flex items-center gap-2 text-red-600">
									<AlertCircle className="w-5 h-5" />
									<span className="text-sm font-medium">Save failed</span>
								</div>
							)}
							<button
								onClick={handleReset}
								disabled={!isDirty || saveStatus === 'saving'}
								className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
							>
								<RotateCcw className="w-4 h-4" />
								Reset
							</button>
							<button
								onClick={handleSave}
								disabled={!isDirty || saveStatus === 'saving'}
								className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
							>
								<Save className="w-4 h-4" />
								{saveStatus === 'saving' ? 'Saving...' : 'Save Changes'}
							</button>
							<button
								onClick={() => navigate('/dashboard')}
								className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
							>
								Back to Dashboard
							</button>
						</div>
					</div>

					{/* Dirty Warning */}
					{isDirty && (
						<div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
							<div className="flex items-center gap-2 text-yellow-800">
								<AlertCircle className="w-5 h-5" />
								<span className="text-sm font-medium">You have unsaved changes</span>
							</div>
						</div>
					)}
				</div>
			</header>

			<div className="max-w-7xl mx-auto px-6 py-8">
				{/* Tab Navigation */}
				<div className="flex gap-2 mb-6">
					{tabs.map((tab) => {
						const Icon = tab.icon;
						return (
							<button
								key={tab.id}
								onClick={() => setActiveTab(tab.id)}
								className={`flex items-center gap-2 px-4 py-3 rounded-lg transition-all ${activeTab === tab.id
										? 'bg-white shadow-md border border-blue-200 text-blue-600'
										: 'bg-white/50 hover:bg-white text-gray-600 hover:text-gray-900'
									}`}
							>
								<Icon className="w-5 h-5" />
								<span className="font-medium">{tab.label}</span>
								{activeTab === tab.id && <ChevronRight className="w-4 h-4" />}
							</button>
						);
					})}
				</div>

				{/* Tab Content */}
				{activeTab === 'tts' && (
					<SettingSection title="Text-to-Speech Settings" icon={Volume2}>
						<div className="space-y-6">
							<div>
								<p className="text-sm text-gray-600 mb-4">
									Choose your preferred TTS provider and voice for educational content narration
								</p>
								<ComprehensiveTTSSelector
									providers={comprehensiveTTSProviders}
									selectedProviderId={settings.tts.default_provider}
									onSelectProvider={(providerId) => updateSettings({
										tts: { ...settings.tts, default_provider: providerId }
									})}
									selectedVoice={settings.tts.default_voice || undefined}
									onSelectVoice={(voice) => updateSettings({
										tts: { ...settings.tts, default_voice: voice }
									})}
									speed={settings.tts.speed}
									onSpeedChange={(speed) => updateSettings({
										tts: { ...settings.tts, speed }
									})}
									pitch={settings.tts.pitch}
									onPitchChange={(pitch) => updateSettings({
										tts: { ...settings.tts, pitch }
									})}
									showAdvanced={true}
									showOnlineOnly={false}
									isLoading={loadingComprehensiveTTS}
									onPreview={handlePreviewVoice}
									previewLoading={previewLoading}
									previewText={previewText}
									onPreviewTextChange={setPreviewText}
								/>
								{comprehensiveTTSError && (
									<div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
										<p className="text-sm text-red-700">
											⚠️ Error loading TTS providers: {comprehensiveTTSError}
										</p>
									</div>
								)}
							</div>
						</div>
					</SettingSection>
				)}

				{activeTab === 'asr' && (
					<SettingSection title="Speech Recognition Settings" icon={Mic}>
						<div className="space-y-6">
							{/* ASR Provider Selection */}
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-3">
									ASR Provider
								</label>
								<p className="text-sm text-gray-500 mb-4">
									Choose your preferred speech recognition provider. Groq offers ultra-fast transcription at competitive prices.
								</p>
								{loadingASRProviders ? (
									<div className="flex items-center justify-center py-8">
										<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
										<span className="ml-3 text-gray-600">Loading providers...</span>
									</div>
								) : (
									<div className="grid grid-cols-1 md:grid-cols-2 gap-3">
										{asrProviders.map((provider) => {
											const isSelected = settings.asr.default_provider === provider.id;
											return (
												<button
													key={provider.id}
													onClick={() => updateSettings({
														asr: { ...settings.asr, default_provider: provider.id }
													})}
													className={`relative flex items-start p-4 rounded-xl border-2 transition-all text-left ${
														isSelected
															? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
															: 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
													}`}
												>
													{/* Selection indicator */}
													{isSelected && (
														<div className="absolute top-2 right-2">
															<CheckCircle className="w-5 h-5 text-blue-600" />
														</div>
													)}

													<div className="flex-shrink-0 text-2xl mr-3">
														{provider.icon || '🎤'}
													</div>

													<div className="flex-1 min-w-0">
														<div className="font-medium text-gray-900">
															{provider.name}
														</div>
														<div className="text-sm text-gray-500 mt-1 line-clamp-2">
															{provider.description}
														</div>
														{provider.metadata && (
															<div className="flex flex-wrap gap-2 mt-2">
																{provider.metadata.latency && (
																	<span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
																		{provider.metadata.latency}
																	</span>
																)}
																{provider.metadata.cost_per_hour && (
																	<span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
																		{provider.metadata.cost_per_hour}/hr
																	</span>
																)}
																{provider.metadata.speed_factor && (
																	<span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
																		{provider.metadata.speed_factor} real-time
																	</span>
																)}
															</div>
														)}
													</div>
												</button>
											);
										})}
									</div>
								)}
							</div>

							{/* Language Selection */}
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">
									Language
								</label>
								<select
									value={settings.asr.language}
									onChange={(e) => updateSettings({
										asr: { ...settings.asr, language: e.target.value }
									})}
									className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
								>
									<option value="en">English</option>
									<option value="es">Spanish</option>
									<option value="fr">French</option>
									<option value="de">German</option>
									<option value="it">Italian</option>
									<option value="pt">Portuguese</option>
									<option value="nl">Dutch</option>
									<option value="pl">Polish</option>
									<option value="ru">Russian</option>
									<option value="zh">Chinese</option>
									<option value="ja">Japanese</option>
									<option value="ko">Korean</option>
									<option value="ar">Arabic</option>
									<option value="hi">Hindi</option>
									<option value="tr">Turkish</option>
									<option value="tw">Twi (Akan)</option>
								</select>
							</div>

							{/* Task Selection */}
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">
									Task
								</label>
								<select
									value={settings.asr.task}
									onChange={(e) => updateSettings({
										asr: { ...settings.asr, task: e.target.value }
									})}
									className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
								>
									<option value="transcribe">Transcribe (same language)</option>
									<option value="translate">Translate to English</option>
								</select>
								<p className="text-xs text-gray-500 mt-1">
									Translation is only available with Groq Whisper Large v3 and OpenAI Whisper.
								</p>
							</div>

							{/* Current Selection Summary */}
							{settings.asr.default_provider && (
								<div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
									<h4 className="text-sm font-medium text-gray-700 mb-2">Current Selection</h4>
									<div className="flex items-center gap-2">
										<span className="text-lg">
											{asrProviders.find(p => p.id === settings.asr.default_provider)?.icon || '🎤'}
										</span>
										<span className="font-medium">
											{asrProviders.find(p => p.id === settings.asr.default_provider)?.name || settings.asr.default_provider}
										</span>
									</div>
								</div>
							)}

							{/* ASR Test Panel */}
							<div className="mt-6 pt-6 border-t border-gray-200">
								<h4 className="text-sm font-medium text-gray-700 mb-4">Test Speech Recognition</h4>
								<ASRStreamingTestPanel
									apiBaseUrl={API_BASE_URL}
									wsBaseUrl={WS_BASE_URL}
									getAuthToken={getAuthToken}
									selectedProvider={settings.asr.default_provider}
									language={settings.asr.language}
									defaultMode="realtime"
									disabled={!settings.asr.default_provider}
									disabledReason="Select an ASR provider to test speech recognition"
									languages={[
										{ code: 'en', name: 'English', flag: '🇬🇧' },
										{ code: 'tw', name: 'Twi', flag: '🇬🇭' },
										{ code: 'yo', name: 'Yoruba', flag: '🇳🇬' },
										{ code: 'es', name: 'Spanish', flag: '🇪🇸' },
										{ code: 'fr', name: 'French', flag: '🇫🇷' },
									]}
								/>
							</div>
						</div>
					</SettingSection>
				)}

				{activeTab === 'llm' && (
					<SettingSection title="Language Model Settings" icon={Brain}>
						<div className="space-y-6">
							{/* LLM Provider Selection */}
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-3">
									LLM Provider
								</label>
								<p className="text-sm text-gray-500 mb-4">
									Choose your preferred language model for AI tutoring and conversations.
								</p>
								{loadingLLMProviders ? (
									<div className="flex items-center justify-center py-8">
										<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
										<span className="ml-3 text-gray-600">Loading providers...</span>
									</div>
								) : llmProviders.length === 0 ? (
									<div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
										<p className="text-sm text-yellow-700">
											No LLM providers available. Please check your configuration.
										</p>
									</div>
								) : (
									<div className="grid grid-cols-1 md:grid-cols-2 gap-3">
										{llmProviders.map((provider) => {
											const isSelected = settings.llm.default_model === provider.id;
											return (
												<button
													key={provider.id}
													onClick={() => updateSettings({
														llm: { ...settings.llm, default_model: provider.id }
													})}
													className={`relative flex items-start p-4 rounded-xl border-2 transition-all text-left ${
														isSelected
															? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
															: 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
													}`}
												>
													{/* Selection indicator */}
													{isSelected && (
														<div className="absolute top-2 right-2">
															<CheckCircle className="w-5 h-5 text-blue-600" />
														</div>
													)}

													<div className="flex-shrink-0 text-2xl mr-3">
														{provider.icon || '🤖'}
													</div>

													<div className="flex-1 min-w-0">
														<div className="font-medium text-gray-900">
															{provider.name}
														</div>
														<div className="text-sm text-gray-500 mt-1 line-clamp-2">
															{provider.description}
														</div>
														{provider.metadata && (
															<div className="flex flex-wrap gap-2 mt-2">
																{provider.metadata.contextWindow && (
																	<span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
																		{(provider.metadata.contextWindow / 1000).toFixed(0)}K context
																	</span>
																)}
																{provider.metadata.pricing?.inputPer1kTokens !== undefined && (
																	<span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
																		{provider.metadata.pricing.inputPer1kTokens === 0 ? 'Free' : `$${provider.metadata.pricing.inputPer1kTokens}/1K`}
																	</span>
																)}
																{provider.capabilities?.streaming && (
																	<span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
																		Streaming
																	</span>
																)}
																{provider.capabilities?.functionCalling && (
																	<span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
																		Functions
																	</span>
																)}
															</div>
														)}
														{provider.languageList && provider.languageList.length > 0 && (
															<div className="text-xs text-gray-400 mt-1">
																Languages: {provider.languageList.slice(0, 5).join(', ')}{provider.languageList.length > 5 ? ` +${provider.languageList.length - 5} more` : ''}
															</div>
														)}
													</div>
												</button>
											);
										})}
									</div>
								)}
							</div>

							{/* Current Selection Summary */}
							{settings.llm.default_model && (
								<div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
									<h4 className="text-sm font-medium text-gray-700 mb-2">Current Selection</h4>
									<div className="flex items-center gap-2">
										<span className="text-lg">
											{llmProviders.find(p => p.id === settings.llm.default_model)?.icon || '🤖'}
										</span>
										<span className="font-medium">
											{llmProviders.find(p => p.id === settings.llm.default_model)?.name || settings.llm.default_model}
										</span>
									</div>
								</div>
							)}

							{/* Temperature Setting */}
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">
									Temperature: {settings.llm.temperature.toFixed(2)}
								</label>
								<input
									type="range"
									min="0.0"
									max="2.0"
									step="0.1"
									value={settings.llm.temperature}
									onChange={(e) => updateSettings({
										llm: { ...settings.llm, temperature: parseFloat(e.target.value) }
									})}
									className="w-full accent-blue-600"
								/>
								<div className="flex justify-between text-xs text-gray-500 mt-1">
									<span>Focused (0.0)</span>
									<span>Creative (2.0)</span>
								</div>
							</div>

							{/* Max Tokens Setting */}
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">
									Max Tokens: {settings.llm.max_tokens.toLocaleString()}
								</label>
								<input
									type="number"
									min="1"
									max="100000"
									step="100"
									value={settings.llm.max_tokens}
									onChange={(e) => updateSettings({
										llm: { ...settings.llm, max_tokens: parseInt(e.target.value) }
									})}
									className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
								<p className="text-xs text-gray-500 mt-1">
									Maximum number of tokens in the response. Higher values allow longer responses but cost more.
								</p>
							</div>

							{/* LLM Chat Test Panel */}
							<div className="mt-6 pt-6 border-t border-gray-200">
								<h4 className="text-sm font-medium text-gray-700 mb-4">Test Language Model</h4>
								<LLMChatTestPanel
									apiBaseUrl={API_BASE_URL}
									getAuthToken={getAuthToken}
									selectedModel={settings.llm.default_model}
									temperature={settings.llm.temperature}
									maxTokens={settings.llm.max_tokens}
									disabled={!settings.llm.default_model}
									disabledReason="Select an LLM model to test chat"
								/>
							</div>
						</div>
					</SettingSection>
				)}

				{activeTab === 'voices' && (
					<SettingSection title="Voice Library" icon={Star}>
						<div className="space-y-4">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-gray-600 text-sm">
										Browse and manage voices for tutoring and educational content
									</p>
								</div>
								<div className="text-sm text-gray-600">
									<Star className="h-4 w-4 inline mr-1 text-blue-600" />
									{favoriteVoices.length} Favorites
								</div>
							</div>

							<VoiceGallery
								onVoiceSelect={(voice) => {
									updateSettings({
										tts: { ...settings.tts, default_voice: voice.voice_id }
									});
								}}
								selectedVoiceId={settings.tts.default_voice || undefined}
								showFilters={true}
								showStats={true}
								showActions={true}
								defaultLayout="grid"
								defaultFilters={{
									categories: ['Education', 'Tutoring', 'Professional'],
								}}
								pageSize={12}
							/>
						</div>
					</SettingSection>
				)}

				{activeTab === 'test' && (
					<SettingSection title="Test Voice Conversation" icon={MessageSquare}>
						<div className="space-y-4">
							<p className="text-gray-600 text-sm">
								Test your voice settings with a live conversation. Make sure you have configured TTS, ASR, and LLM providers.
							</p>

							{/* Configuration Summary */}
							<div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
								<h4 className="text-sm font-medium text-gray-700 mb-3">Current Configuration</h4>
								<div className="grid grid-cols-3 gap-4 text-sm">
									<div>
										<span className="text-gray-500">TTS:</span>{' '}
										<span className="font-medium">{settings.tts.default_provider || 'Not set'}</span>
									</div>
									<div>
										<span className="text-gray-500">ASR:</span>{' '}
										<span className="font-medium">{settings.asr.default_provider || 'Not set'}</span>
									</div>
									<div>
										<span className="text-gray-500">LLM:</span>{' '}
										<span className="font-medium">{settings.llm.default_model || 'Not set'}</span>
									</div>
								</div>
							</div>

							<VoiceTestingPanel
								assistantId="studyflow-tutor"
								assistantName="StudyFlow AI Tutor"
								apiBaseUrl={CORE_API_URL}
								wsBaseUrl={WS_BASE_URL}
								getAuthToken={getAuthToken}
								assistant={{
									language: settings.asr.language,
									llm_provider: settings.llm.default_model,
									tts_provider: settings.tts.default_provider,
									stt_provider: settings.asr.default_provider,
								}}
								languages={[
									{ code: 'en', name: 'English', flag: '🇬🇧' },
									{ code: 'tw', name: 'Twi', flag: '🇬🇭' },
									{ code: 'yo', name: 'Yoruba', flag: '🇳🇬' },
									{ code: 'es', name: 'Spanish', flag: '🇪🇸' },
									{ code: 'fr', name: 'French', flag: '🇫🇷' },
								]}
								disabled={!settings.tts.default_provider || !settings.asr.default_provider || !settings.llm.default_model}
								disabledReason={
									!settings.tts.default_provider || !settings.asr.default_provider || !settings.llm.default_model
										? 'Please configure TTS, ASR, and LLM providers before testing'
										: undefined
								}
							/>
						</div>
					</SettingSection>
				)}
			</div>
		</div>
	);
}
