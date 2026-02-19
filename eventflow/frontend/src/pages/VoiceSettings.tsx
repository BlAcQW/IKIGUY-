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
	ChevronRight
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { API_BASE_URL } from '../config/api-config';
import { VoiceGallery } from '../components/voice-library';
import { useVoiceLibrary } from '../hooks/useVoiceLibrary';
import { ComprehensiveTTSSelector } from '../../../../shared/frontend/components/voice-settings/ComprehensiveTTSSelector';
import { useComprehensiveTTS } from '../../../../shared/frontend/hooks/useComprehensiveTTS';
import { getAuthHeaders } from '../lib/auth-utils';

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
	const [activeTab, setActiveTab] = useState<'tts' | 'asr' | 'llm' | 'voices'>('tts');
	const { addToFavorites, removeFromFavorites, getFavorites } = useVoiceLibrary();
	const [favoriteVoices, setFavoriteVoices] = useState<string[]>([]);

	const [previewLoading, setPreviewLoading] = useState(false);
	const [previewAudio, setPreviewAudio] = useState<HTMLAudioElement | null>(null);

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
	}, []);

	const loadFavorites = async () => {
		try {
			const favorites = await getFavorites();
			setFavoriteVoices(favorites.map((v: any) => v.voice_id));
		} catch (error) {
			console.error('Failed to load favorite voices:', error);
		}
	};

	const loadSettings = async () => {
		try {
			setIsLoading(true);
			const data = await api.voiceSettings.getMySettings();
			setSettings(data);
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
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">
									Default Provider
								</label>
								<input
									type="text"
									value={settings.asr.default_provider}
									onChange={(e) => updateSettings({
										asr: { ...settings.asr, default_provider: e.target.value }
									})}
									className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
							</div>

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
									<option value="zh">Chinese</option>
									<option value="ar">Arabic</option>
									<option value="hi">Hindi</option>
								</select>
							</div>

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
									<option value="transcribe">Transcribe</option>
									<option value="translate">Translate</option>
								</select>
							</div>
						</div>
					</SettingSection>
				)}

				{activeTab === 'llm' && (
					<SettingSection title="Language Model Settings" icon={Brain}>
						<div className="space-y-6">
							<div>
								<label className="block text-sm font-medium text-gray-700 mb-2">
									Default Model
								</label>
								<input
									type="text"
									value={settings.llm.default_model}
									onChange={(e) => updateSettings({
										llm: { ...settings.llm, default_model: e.target.value }
									})}
									className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
							</div>

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
			</div>
		</div>
	);
}
