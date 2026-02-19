import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  Download,
  PlusCircle,
  RefreshCw,
  Filter,
  Search
} from 'lucide-react';

interface ClonedVoice {
  filename: string;
  voice_name: string;
  provider: string;
  language: string;
  timestamp: string;
  file_path: string;
  file_size: number;
}

interface ClonedVoicesPanelProps {
  onVoiceRegistered?: (voice: any) => void;
}

export const ClonedVoicesPanel: React.FC<ClonedVoicesPanelProps> = ({
  onVoiceRegistered
}) => {
  const [clonedVoices, setClonedVoices] = useState<ClonedVoice[]>([]);
  const [loading, setLoading] = useState(false);
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const [filterProvider, setFilterProvider] = useState<string>('');
  const [filterLanguage, setFilterLanguage] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);

  // Fetch cloned voices from API
  const fetchClonedVoices = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterProvider) params.append('provider', filterProvider);
      if (filterLanguage) params.append('language', filterLanguage);

      const response = await fetch(`/api/cloned-voices/list?${params}`);
      const data = await response.json();

      if (data.success) {
        setClonedVoices(data.voices);
      }
    } catch (error) {
      console.error('Error fetching cloned voices:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClonedVoices();
  }, [filterProvider, filterLanguage]);

  // Play cloned voice
  const handlePlay = async (voice: ClonedVoice) => {
    if (playingVoice === voice.filename) {
      // Pause if already playing
      if (audioElement) {
        audioElement.pause();
        setPlayingVoice(null);
      }
      return;
    }

    // Stop previous audio
    if (audioElement) {
      audioElement.pause();
    }

    try {
      const audio = new Audio(
        `/api/cloned-voices/play/${voice.provider}/${voice.filename}`
      );

      audio.onended = () => {
        setPlayingVoice(null);
      };

      audio.onerror = () => {
        console.error('Error playing audio');
        setPlayingVoice(null);
      };

      setAudioElement(audio);
      setPlayingVoice(voice.filename);
      await audio.play();
    } catch (error) {
      console.error('Error playing voice:', error);
      setPlayingVoice(null);
    }
  };

  // Register cloned voice in library
  const handleRegister = async (voice: ClonedVoice) => {
    try {
      const response = await fetch('/api/cloned-voices/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: voice.filename,
          tags: [voice.provider, 'cloned', voice.language]
        })
      });

      const data = await response.json();

      if (data.success) {
        alert(`Voice "${data.voice.name}" registered successfully!`);
        if (onVoiceRegistered) {
          onVoiceRegistered(data.voice);
        }
      } else {
        alert('Failed to register voice');
      }
    } catch (error) {
      console.error('Error registering voice:', error);
      alert('Error registering voice');
    }
  };

  // Download cloned voice
  const handleDownload = (voice: ClonedVoice) => {
    const link = document.createElement('a');
    link.href = `/api/cloned-voices/download/${voice.provider}/${voice.filename}`;
    link.download = voice.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Filter voices by search query
  const filteredVoices = clonedVoices.filter((voice) =>
    voice.voice_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Get unique providers and languages
  const providers = Array.from(new Set(clonedVoices.map((v) => v.provider)));
  const languages = Array.from(new Set(clonedVoices.map((v) => v.language)));

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Cloned Voices</h3>
          <p className="text-sm text-muted-foreground">
            {filteredVoices.length} voices available from voice-lab
          </p>
        </div>

        <button
          onClick={fetchClonedVoices}
          disabled={loading}
          className="flex items-center gap-2 bg-muted hover:bg-muted/80 px-3 py-2 rounded text-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search voices..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-muted border border-input rounded text-sm"
            />
          </div>
        </div>

        <select
          value={filterProvider}
          onChange={(e) => setFilterProvider(e.target.value)}
          className="bg-muted border border-input rounded px-3 py-2 text-sm"
        >
          <option value="">All Providers</option>
          {providers.map((provider) => (
            <option key={provider} value={provider}>
              {provider.toUpperCase()}
            </option>
          ))}
        </select>

        <select
          value={filterLanguage}
          onChange={(e) => setFilterLanguage(e.target.value)}
          className="bg-muted border border-input rounded px-3 py-2 text-sm"
        >
          <option value="">All Languages</option>
          {languages.map((lang) => (
            <option key={lang} value={lang}>
              {lang === 'eng' ? 'English' : lang === 'twi' ? 'Twi' : lang.toUpperCase()}
            </option>
          ))}
        </select>
      </div>

      {/* Voice List */}
      <div className="space-y-2">
        {loading ? (
          <div className="text-center py-8">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-muted-foreground" />
            <p className="text-sm text-muted-foreground mt-2">Loading...</p>
          </div>
        ) : filteredVoices.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">No cloned voices found</p>
          </div>
        ) : (
          filteredVoices.map((voice) => (
            <div
              key={voice.filename}
              className="border rounded-lg p-4 hover:bg-accent/50 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium">
                      {voice.voice_name.replace(/_/g, ' ')}
                    </h4>
                    <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                      {voice.provider.toUpperCase()}
                    </span>
                    <span className="text-xs bg-muted px-2 py-0.5 rounded">
                      {voice.language === 'eng'
                        ? 'English'
                        : voice.language === 'twi'
                        ? 'Twi'
                        : voice.language.toUpperCase()}
                    </span>
                  </div>

                  <p className="text-xs text-muted-foreground">
                    {(voice.file_size / 1024).toFixed(1)} KB · Created{' '}
                    {new Date(
                      voice.timestamp.replace(/_/g, ' ').replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3')
                    ).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePlay(voice)}
                  className="flex items-center gap-1 bg-indigo-600 hover:bg-primary/90 text-white px-3 py-1.5 rounded text-sm"
                >
                  {playingVoice === voice.filename ? (
                    <>
                      <Pause className="w-3 h-3" />
                      Pause
                    </>
                  ) : (
                    <>
                      <Play className="w-3 h-3" />
                      Play
                    </>
                  )}
                </button>

                <button
                  onClick={() => handleRegister(voice)}
                  className="flex items-center gap-1 bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded text-sm"
                >
                  <PlusCircle className="w-3 h-3" />
                  Add to Library
                </button>

                <button
                  onClick={() => handleDownload(voice)}
                  className="flex items-center gap-1 bg-muted hover:bg-muted/80 px-3 py-1.5 rounded text-sm"
                >
                  <Download className="w-3 h-3" />
                  Download
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
