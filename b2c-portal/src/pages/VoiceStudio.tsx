import React, { useState, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { VoiceCreationWizard } from '@/components/voice-studio/VoiceCreationWizard';
import { VoiceManager } from '@/components/voice-studio/VoiceManager';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';
import { useClonedVoices } from '@/hooks/useClonedVoices';
import { useTTSProvider } from '@/hooks/useTTSProvider';
import { useVoiceLibrary } from '@/hooks/useVoiceLibrary';

import {
  Search,
  Play,
  Plus,
  Copy,
  Download,
  Upload,
  Mic,
  Volume2,
  ChevronLeft,
  ChevronRight,
  Filter,
  MoreVertical,
  Heart,
  Star,
  Globe,
  Clock,
  DollarSign,
  User,
  Settings,
  FileText,
  Zap,
  Brain,
  Headphones,
  Smartphone,
  Monitor,
  Target,
  Shield,
  Languages,
  Calendar,
  CheckCircle,
  AlertCircle,
  Info,
  X,
  ArrowRight,
  ArrowLeft,
  Trash2
} from 'lucide-react';

interface Voice {
  id: string;
  name: string;
  provider: string;
  gender: 'male' | 'female' | 'neutral';
  accent: string;
  language: string;
  bestFor: string[];
  pricePerMinute: number;
  latency: number;
  image: string;
  isFeatured: boolean;
  isCloned: boolean;
  isCustom: boolean;
  rating: number;
  totalUses: number;
  createdAt: string;
  description: string;
  capabilities: string[];
}

interface VoiceStudioProps {}

const VoiceStudio: React.FC<VoiceStudioProps> = () => {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedGender, setSelectedGender] = useState('');
  const [selectedAccent, setSelectedAccent] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [showCloneModal, setShowCloneModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showSyncModal, setShowSyncModal] = useState(false);
  const [showCreateWizard, setShowCreateWizard] = useState(false);
  const [showBatchCloneModal, setShowBatchCloneModal] = useState(false);
  const [activeView, setActiveView] = useState<'gallery' | 'manager'>('gallery');
  const [selectedVoice, setSelectedVoice] = useState<Voice | null>(null);
  const [isPlaying, setIsPlaying] = useState<string | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  const [deleteConfirmVoiceId, setDeleteConfirmVoiceId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);

  // Use TTS provider hook to get dynamic providers
  const {
    providers: ttsProviders,
    isLoadingProviders,
    getLanguages,
    getSpeakers
  } = useTTSProvider();

  // Use cloned voices hook
  const {
    voices: clonedVoices,
    isLoading: isLoadingCloned,
    error: clonedError,
    fetchClonedVoices,
    batchCloneVoices,
    deleteVoice: deleteClonedVoice
  } = useClonedVoices();

  // Use centralized voice library hook
  const voiceLibrary = useVoiceLibrary();

  // API Configuration
  // Using API_BASE_URL from api-config;

  // Load voices from backend
  useEffect(() => {
    loadVoicesFromAPI();
  }, []);

  // Fetch available languages when provider changes
  useEffect(() => {
    const fetchProviderLanguages = async () => {
      if (!selectedProvider || !ttsProviders[selectedProvider]) {
        setAvailableLanguages([]);
        return;
      }

      try {
        const languages = await getLanguages();
        setAvailableLanguages(languages);
      } catch (error) {
        console.error('Failed to fetch languages:', error);
        setAvailableLanguages([]);
      }
    };

    fetchProviderLanguages();
  }, [selectedProvider, ttsProviders, getLanguages]);

  const loadVoicesFromAPI = async () => {
    try {
      // Fetch library voices from centralized voice library
      const libraryData = await voiceLibrary.fetchVoices();
      let libraryVoices: Voice[] = [];

      if (libraryData && libraryData.voices) {
        // Convert library voices to Voice format
        libraryVoices = libraryData.voices.map((voice: any) => ({
          id: voice.voice_id,
          name: voice.name,
          provider: 'Voice Library',
          gender: (voice.characteristics?.gender || 'unknown') as 'male' | 'female' | 'neutral',
          accent: voice.characteristics?.accent || 'General',
          language: voice.characteristics?.language === 'en' ? 'English' : (voice.characteristics?.language || 'English').toUpperCase(),
          bestFor: voice.metadata?.use_cases || ['Reference Voice', 'Voice Library'],
          pricePerMinute: 0.01,
          latency: 100,
          image: '/api/placeholder/150/150',
          isFeatured: voice.metadata?.featured || false,
          isCloned: false,
          isCustom: true,
          rating: voice.stats?.rating?.average || 4.8,
          totalUses: voice.stats?.uses || 0,
          createdAt: voice.created_at,
          description: voice.description || 'Voice library entry',
          capabilities: ['Voice Library', 'Reference Audio', ...(voice.metadata?.categories || [])]
        }));
      }

      const response = await fetch(`${API_BASE_URL}/api/voice-lab/voices`);
      if (response.ok) {
        const apiVoices = await response.json();

        // Convert API voices to our format
        const convertedVoices: Voice[] = apiVoices.map((voice: any, index: number) => ({
          id: voice.voice_id,
          name: voice.name,
          provider: 'AKAN_MMS',
          gender: voice.gender as 'male' | 'female' | 'neutral',
          accent: voice.dialect || 'Asante',
          language: voice.language === 'tw' ? 'Twi' : voice.language,
          bestFor: ['Conversational', 'Education'],
          pricePerMinute: 0.02,
          latency: 300,
          image: '/api/placeholder/150/150',
          isFeatured: index < 2,
          isCloned: false,
          isCustom: false,
          rating: 4.7,
          totalUses: Math.floor(Math.random() * 1000) + 100,
          createdAt: '2025-09-09',
          description: voice.description || 'Native Twi voice',
          capabilities: ['Real-time', 'High Quality', 'African Languages']
        }));

        // Add cloned voices
        const clonedVoicesList: Voice[] = clonedVoices
          .filter(v => v.status === 'completed')
          .map((voice, index) => ({
            id: voice.voice_id,
            name: voice.name,
            provider: voice.provider.toUpperCase(),
            gender: voice.gender,
            accent: voice.accent,
            language: voice.language === 'en' ? 'English' : voice.language,
            bestFor: ['Cloned Voice', 'Custom'],
            pricePerMinute: 0.03,
            latency: 400,
            image: '/api/placeholder/150/150',
            isFeatured: false,
            isCloned: true,
            isCustom: true,
            rating: 4.5,
            totalUses: 0,
            createdAt: voice.cloned_at,
            description: voice.description || 'Cloned voice',
            capabilities: voice.capabilities
          }));

        const allVoices = [...libraryVoices, ...convertedVoices, ...clonedVoicesList];
        setVoices(allVoices);
      } else {
        console.error('Failed to load voices from API - HTTP', response.status);
        setVoices(libraryVoices);
      }
    } catch (error) {
      console.error('Error loading voices:', error);
      setVoices([]);
    }
  };

  // Handle batch cloning
  const handleBatchClone = async () => {
    setShowBatchCloneModal(true);
  };

  const executeBatchClone = async (providers: string[]) => {
    try {
      const result = await batchCloneVoices(providers);
      if (result) {
        alert(`Successfully cloned ${result.total_voices} voices!`);
        // Refresh voices list
        await loadVoicesFromAPI();
      }
    } catch (error) {
      console.error('Batch cloning failed:', error);
      alert('Batch cloning failed. Please try again.');
    } finally {
      setShowBatchCloneModal(false);
    }
  };

  // Use dynamic providers from TTS API instead of hardcoded list

  // Voice operation handlers
  const handleVoiceCreated = (newVoice: Voice) => {
    setVoices(prev => [newVoice, ...prev]);
    setShowCreateWizard(false);
  };

  const handleVoiceUpdate = (updatedVoice: Voice) => {
    setVoices(prev => prev.map(voice => 
      voice.id === updatedVoice.id ? updatedVoice : voice
    ));
  };

  const handleVoiceDelete = async (voiceId: string) => {
    const voice = voices.find(v => v.id === voiceId);
    if (!voice) return;

    // Only allow deletion of cloned voices
    if (!voice.isCloned) {
      console.warn('Cannot delete non-cloned voices');
      return;
    }

    setDeleteConfirmVoiceId(voiceId);
  };

  const confirmDeleteVoice = async () => {
    if (!deleteConfirmVoiceId) return;

    setIsDeleting(true);
    try {
      const success = await deleteClonedVoice(deleteConfirmVoiceId);

      if (success) {
        // Remove from local state
        setVoices(prev => prev.filter(voice => voice.id !== deleteConfirmVoiceId));

        // Stop audio if this voice is playing
        if (isPlaying === deleteConfirmVoiceId) {
          if (audioElement) {
            audioElement.pause();
            audioElement.currentTime = 0;
          }
          setIsPlaying(null);
          setAudioElement(null);
        }
      }
    } catch (error) {
      console.error('Failed to delete voice:', error);
    } finally {
      setIsDeleting(false);
      setDeleteConfirmVoiceId(null);
    }
  };

  const cancelDeleteVoice = () => {
    setDeleteConfirmVoiceId(null);
  };

  const handleVoiceClone = (voice: Voice) => {
    setSelectedVoice(voice);
    setShowCloneModal(true);
  };
  const genders = ['male', 'female', 'neutral'];
  const accents = ['American', 'British', 'Australian', 'Canadian', 'Irish', 'Scottish', 'Arabic', 'Spanish', 'French', 'German', 'Italian'];

  const filteredVoices = voices.filter(voice => {
    // Add null checks to prevent errors with undefined properties
    const matchesSearch = (voice.name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
                         (voice.description?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
                         (voice.bestFor || []).some(tag => (tag?.toLowerCase() || '').includes(searchTerm.toLowerCase()));
    const matchesProvider = !selectedProvider || voice.provider === selectedProvider;
    const matchesGender = !selectedGender || voice.gender === selectedGender;
    const matchesAccent = !selectedAccent || (voice.accent?.toLowerCase() || '').includes(selectedAccent.toLowerCase());
    const matchesLanguage = !selectedLanguage || (voice.language?.toLowerCase() || '').includes(selectedLanguage.toLowerCase());

    return matchesSearch && matchesProvider && matchesGender && matchesAccent && matchesLanguage;
  });

  const handlePlayVoice = async (voiceId: string) => {
    // Stop currently playing audio
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
    }

    // If clicking the same voice, just stop
    if (isPlaying === voiceId) {
      setIsPlaying(null);
      setAudioElement(null);
      return;
    }

    // Find the voice
    const voice = voices.find(v => v.id === voiceId);
    if (!voice) return;

    try {
      let audioUrl: string;

      // For library voices, get the audio from library endpoint
      if (voice.provider === 'Library') {
        audioUrl = `${API_BASE_URL}/api/voice-lab/library-voices/${voice.id}/audio`;
      } else if (voice.isCloned) {
        // For cloned voices, get the reference audio from the API
        audioUrl = `${API_BASE_URL}/api/voice-lab/voices/cloned/${voice.id}/audio`;
      } else {
        // For API voices, synthesize a sample text
        const response = await fetch(`${API_BASE_URL}/api/voice-lab/synthesize`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: 'Akwaaba. Me din de ' + voice.name,
            voice_id: voice.id,
            speed: 1.0,
            pitch: 0.0,
            output_format: 'wav'
          })
        });

        if (!response.ok) {
          console.error('Failed to synthesize voice sample');
          return;
        }

        const data = await response.json();

        // Convert base64 to audio blob
        const audioBase64 = data.audio_base64 || data.audio;
        const audioBytes = Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0));
        const blob = new Blob([audioBytes], { type: 'audio/wav' });
        audioUrl = URL.createObjectURL(blob);
      }

      // Create and play audio
      const audio = new Audio(audioUrl);
      audio.onended = () => {
        setIsPlaying(null);
        setAudioElement(null);
        if (voice.isCloned) {
          // For cloned voices, revoke the object URL
        } else {
          URL.revokeObjectURL(audioUrl);
        }
      };

      audio.onerror = () => {
        console.error('Audio playback error');
        setIsPlaying(null);
        setAudioElement(null);
      };

      await audio.play();
      setIsPlaying(voiceId);
      setAudioElement(audio);

    } catch (error) {
      console.error('Error playing voice:', error);
      setIsPlaying(null);
    }
  };

  const handleCloneVoice = (voice: Voice) => {
    setSelectedVoice(voice);
    setShowCloneModal(true);
  };

  const handleCreateVoice = () => {
    setShowCreateModal(true);
  };

  const handleSyncVoices = () => {
    setShowSyncModal(true);
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      <DashboardSidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Header */}
        <div className="bg-card border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Volume2 className="h-6 w-6 text-indigo-600" />
            <h1 className="text-2xl font-bold text-foreground">Voice Studio</h1>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* View Switcher */}
            <div className="flex items-center bg-muted p-1 rounded-lg">
              <button
                onClick={() => setActiveView('gallery')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  activeView === 'gallery' 
                    ? 'bg-background text-foreground shadow-sm' 
                    : 'text-gray-600 hover:text-foreground'
                }`}
              >
                Gallery
              </button>
              <button
                onClick={() => setActiveView('manager')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  activeView === 'manager' 
                    ? 'bg-background text-foreground shadow-sm' 
                    : 'text-gray-600 hover:text-foreground'
                }`}
              >
                My Voices
              </button>
            </div>

            <div className="text-center">
              <div className="text-sm text-gray-600">Available Voices</div>
              <div className="text-lg font-semibold">{voices.length}</div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowCreateWizard(true)}
                className="flex items-center space-x-1 bg-indigo-600 hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-md text-sm font-medium"
              >
                <Plus className="w-4 h-4" />
                <span>Create Voice</span>
              </button>

              <button
                onClick={handleBatchClone}
                className="flex items-center space-x-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                disabled={isLoadingCloned}
              >
                <Copy className="w-4 h-4" />
                <span>{isLoadingCloned ? 'Cloning...' : 'Batch Clone'}</span>
              </button>

              <button className="flex items-center space-x-1 px-3 py-1 text-gray-600 hover:text-foreground text-sm">
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </button>
              <button className="flex items-center space-x-1 px-3 py-1 text-gray-600 hover:text-foreground text-sm">
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {activeView === 'manager' ? (
          <VoiceManager 
            voices={voices}
            onVoiceUpdate={handleVoiceUpdate}
            onVoiceDelete={handleVoiceDelete}
            onVoiceClone={handleVoiceClone}
          />
        ) : (
          <>
        {/* All Voices Section */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">Explore all voices</h2>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleCloneVoice}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-md text-sm"
              >
                <Copy className="w-4 h-4" />
                <span>Clone</span>
              </button>
              <button
                onClick={handleCreateVoice}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md text-sm"
              >
                <Plus className="w-4 h-4" />
                <span>+ Add</span>
              </button>
              <button
                onClick={handleSyncVoices}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-md text-sm"
              >
                <Download className="w-4 h-4" />
                <span>Sync</span>
              </button>
            </div>
          </div>

          {/* Filters */}
          <div className="bg-gray-800 rounded-lg p-4 mb-6">
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search by keyword, id, use..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                className="px-4 py-2 bg-card border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                disabled={isLoadingProviders}
              >
                <option value="">All Providers</option>
                {Object.values(ttsProviders)
                  .filter(provider => provider.status === 'online')
                  .map(provider => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
              </select>

              <select
                value={selectedGender}
                onChange={(e) => setSelectedGender(e.target.value)}
                className="px-4 py-2 bg-card border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              >
                <option value="">All Genders</option>
                {genders.map(gender => (
                  <option key={gender} value={gender}>{gender.charAt(0).toUpperCase() + gender.slice(1)}</option>
                ))}
              </select>

              <select
                value={selectedAccent}
                onChange={(e) => setSelectedAccent(e.target.value)}
                className="px-4 py-2 bg-card border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              >
                <option value="">All Accents</option>
                {accents.map(accent => (
                  <option key={accent} value={accent}>{accent}</option>
                ))}
              </select>

              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                className="px-4 py-2 bg-card border border-border rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              >
                <option value="">All Languages</option>
                {selectedProvider && availableLanguages.length > 0 ? (
                  availableLanguages.map(lang => (
                    <option key={lang} value={lang}>{lang}</option>
                  ))
                ) : (
                  <>
                    <option value="en">English</option>
                    <option value="twi">Twi</option>
                    <option value="multi">Multi-language</option>
                  </>
                )}
              </select>
            </div>
          </div>

          {/* Voice Grid */}
          {filteredVoices.length === 0 ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center max-w-md">
                <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Volume2 className="w-10 h-10 text-gray-400" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">No Voices Available</h3>
                <p className="text-gray-600 mb-6">
                  {voices.length === 0
                    ? "Get started by loading voices from the API or using the Batch Clone feature to create custom voices."
                    : "No voices match your current filters. Try adjusting your search criteria."
                  }
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  {voices.length === 0 && (
                    <button
                      onClick={handleBatchClone}
                      className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                    >
                      Batch Clone Voices
                    </button>
                  )}
                  {filteredVoices.length === 0 && voices.length > 0 && (
                    <button
                      onClick={() => {
                        setSearchTerm('');
                        setSelectedProvider('');
                        setSelectedGender('');
                        setSelectedAccent('');
                        setSelectedLanguage('');
                      }}
                      className="px-6 py-2.5 bg-gray-200 hover:bg-gray-300 text-gray-900 rounded-lg font-medium transition-colors"
                    >
                      Clear Filters
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
              {filteredVoices.map((voice) => (
              <div
                key={voice.id}
                className="bg-card rounded-md p-3 border border-border hover:border-primary transition-colors cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1 mb-0.5">
                      <h3 className="text-sm font-medium truncate text-foreground">{voice.name}</h3>
                      {voice.isCloned && (
                        <span className="px-1 py-0.5 bg-green-100 text-green-700 text-[9px] rounded font-medium">
                          CLONED
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">{voice.provider}</p>
                  </div>
                  <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                    <button
                      onClick={() => handlePlayVoice(voice.id)}
                      className={`w-7 h-7 rounded-full flex items-center justify-center transition-colors ${
                        isPlaying === voice.id
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-primary/10 hover:bg-primary text-primary group-hover:text-primary-foreground'
                      }`}
                    >
                      {isPlaying === voice.id ? (
                        <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Play className="w-3 h-3" />
                      )}
                    </button>
                    {voice.isCloned && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleVoiceDelete(voice.id);
                        }}
                        className="w-7 h-7 rounded-full flex items-center justify-center transition-colors bg-red-50 hover:bg-red-100 text-red-600"
                        title="Delete cloned voice"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex flex-wrap gap-1">
                    {voice.bestFor.slice(0, 2).map((tag, tagIndex) => (
                      <span
                        key={tagIndex}
                        className="px-1.5 py-0.5 bg-primary/10 text-primary text-[10px] rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <span>{voice.gender}</span>
                    <span>{voice.accent}</span>
                  </div>

                  <div className="flex items-center justify-between pt-1 border-t border-border/50">
                    <div className="flex items-center space-x-1">
                      <Star className="w-2.5 h-2.5 text-yellow-500 fill-current" />
                      <span className="text-[10px] text-muted-foreground">{voice.rating}</span>
                    </div>
                    <button
                      onClick={() => handleCloneVoice(voice)}
                      className="text-[10px] text-primary hover:underline"
                    >
                      Clone
                    </button>
                  </div>
                </div>
              </div>
            ))}
            </div>
          )}
        </div>
          </>
        )}
      </div>

      {/* Clone Voice Modal */}
      {showCloneModal && selectedVoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96 max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Clone Voice</h3>
              <button
                onClick={() => setShowCloneModal(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Voice Name</label>
                <input
                  type="text"
                  placeholder={`${selectedVoice.name} (Clone)`}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  placeholder="Describe your cloned voice..."
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Best For</label>
                <input
                  type="text"
                  placeholder="e.g., Customer Service, Entertainment"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setShowCloneModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-md text-sm"
                >
                  Cancel
                </button>
                <button className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md text-sm">
                  Clone Voice
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Voice Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96 max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Create New Voice</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Voice Name</label>
                <input
                  type="text"
                  placeholder="Enter voice name"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Upload Audio Sample</label>
                <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center">
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">Drop audio file here or click to browse</p>
                  <p className="text-xs text-gray-500 mt-1">MP3, WAV, M4A up to 10MB</p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  placeholder="Describe your voice..."
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-md text-sm"
                >
                  Cancel
                </button>
                <button className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md text-sm">
                  Create Voice
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sync Voices Modal */}
      {showSyncModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96 max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Sync Voices</h3>
              <button
                onClick={() => setShowSyncModal(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Provider</label>
                <select className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:border-primary">
                  <option value="">Select Provider</option>
                  {Object.values(ttsProviders)
                    .filter(provider => provider.status === 'online' && provider.capabilities?.voiceCloning)
                    .map(provider => (
                      <option key={provider.id} value={provider.id}>
                        {provider.name}
                      </option>
                    ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">API Key</label>
                <input
                  type="password"
                  placeholder="Enter API key"
                  className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground focus:outline-none focus:border-primary"
                />
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setShowSyncModal(false)}
                  className="flex-1 px-4 py-2 bg-muted hover:bg-muted/80 rounded-md text-sm"
                >
                  Cancel
                </button>
                <button className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-primary/90 text-primary-foreground rounded-md text-sm">
                  Sync Voices
                </button>
              </div>
            </div>
          </div>
        </div>
        )}
      </div>

      {/* Voice Creation Wizard */}
      <VoiceCreationWizard
        isOpen={showCreateWizard}
        onClose={() => setShowCreateWizard(false)}
        onVoiceCreated={handleVoiceCreated}
      />

      {/* Batch Clone Modal */}
      {showBatchCloneModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-[500px] max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Batch Clone Ghanaian Voices</h3>
              <button
                onClick={() => setShowBatchCloneModal(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-300 mb-3">
                  This will clone all Ghanaian voices from the voice-lab directory using the selected TTS providers.
                </p>
                <div className="bg-gray-700 rounded-lg p-3 mb-3">
                  <p className="text-xs text-gray-400 mb-2">Voices to be cloned:</p>
                  <ul className="text-xs text-gray-300 space-y-1">
                    <li>• Nana Aba</li>
                    <li>• Nana Aba (24-bit)</li>
                    <li>• Adom Okyere</li>
                    <li>• Juliet Bawuah</li>
                    <li>• Archbishop 1</li>
                    <li>• Archbishop 2</li>
                  </ul>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Select TTS Providers</label>
                <div className="space-y-2">
                  {Object.values(ttsProviders)
                    .filter(provider => provider.status === 'online' && provider.capabilities?.voiceCloning)
                    .map(provider => (
                      <label key={provider.id} className="flex items-start space-x-2 p-2 bg-gray-700 rounded hover:bg-gray-600 cursor-pointer">
                        <input
                          type="checkbox"
                          className="mt-1"
                          defaultChecked={['xtts', 'f5tts', 'styletts2', 'openvoice'].includes(provider.id)}
                          id={`provider-${provider.id}`}
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium">{provider.name}</div>
                          <div className="text-xs text-gray-400">
                            {provider.capabilities?.voiceCloning && 'Voice Cloning'}
                            {provider.languages && ` • ${provider.languages} languages`}
                          </div>
                        </div>
                      </label>
                    ))}
                  {Object.values(ttsProviders).filter(p => p.status === 'online' && p.capabilities?.voiceCloning).length === 0 && (
                    <div className="text-gray-400 text-sm">No voice cloning providers available</div>
                  )}
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  onClick={() => setShowBatchCloneModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-md text-sm"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    const checkedProviders = Object.values(ttsProviders)
                      .filter(provider => provider.status === 'online' && provider.capabilities?.voiceCloning)
                      .filter(provider => (document.getElementById(`provider-${provider.id}`) as HTMLInputElement)?.checked)
                      .map(provider => provider.id);
                    executeBatchClone(checkedProviders);
                  }}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-md text-sm"
                  disabled={isLoadingCloned}
                >
                  {isLoadingCloned ? 'Cloning...' : 'Start Batch Clone'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

        {/* Floating Action Button */}
        <div className="fixed bottom-6 right-6">
          <button className="w-14 h-14 bg-indigo-600 hover:bg-primary/90 rounded-full flex items-center justify-center shadow-lg transition-colors">
            <Brain className="w-6 h-6 text-primary-foreground" />
          </button>
        </div>

        {/* Delete Confirmation Modal */}
        {deleteConfirmVoiceId && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-card rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
              <div className="flex items-start gap-4 mb-4">
                <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                  <Trash2 className="w-5 h-5 text-red-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    Delete Cloned Voice?
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    This will permanently delete the cloned voice metadata and any custom uploaded audio files.
                    Master voice files will be preserved.
                  </p>
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={cancelDeleteVoice}
                  disabled={isDeleting}
                  className="px-4 py-2 text-sm font-medium text-foreground bg-muted hover:bg-muted/80 rounded-md transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDeleteVoice}
                  disabled={isDeleting}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  {isDeleting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Deleting...</span>
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4" />
                      <span>Delete</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
    </div>
  );
};

export default VoiceStudio;
