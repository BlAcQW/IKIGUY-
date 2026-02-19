import React, { useState } from 'react';
import {
  Play,
  Pause,
  Download,
  Copy,
  Edit3,
  Trash2,
  Star,
  Heart,
  MoreVertical,
  Volume2,
  Settings,
  Share2,
  Eye,
  Upload
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
  image?: string;
  isFeatured: boolean;
  isCloned: boolean;
  isCustom: boolean;
  rating: number;
  totalUses: number;
  createdAt: string;
  description: string;
  capabilities: string[];
}

interface VoiceManagerProps {
  voices: Voice[];
  onVoiceUpdate: (voice: Voice) => void;
  onVoiceDelete: (voiceId: string) => void;
  onVoiceClone: (voice: Voice) => void;
}

export const VoiceManager: React.FC<VoiceManagerProps> = ({
  voices,
  onVoiceUpdate,
  onVoiceDelete,
  onVoiceClone
}) => {
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const [selectedVoices, setSelectedVoices] = useState<string[]>([]);
  const [showBulkActions, setShowBulkActions] = useState(false);

  const handlePlay = async (voiceId: string, sampleText?: string) => {
    if (playingVoice === voiceId) {
      setPlayingVoice(null);
      return;
    }

    setPlayingVoice(voiceId);
    
    try {
      // Call TTS API to generate audio
      const response = await fetch('/api/voice/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          voiceId,
          text: sampleText || 'Hello, this is a sample of my voice speaking in both English and my native language.',
          language: 'en'
        })
      });

      if (response.ok) {
        const audioData = await response.arrayBuffer();
        const audio = new Audio();
        const blob = new Blob([audioData], { type: 'audio/wav' });
        audio.src = URL.createObjectURL(blob);
        
        audio.onended = () => {
          setPlayingVoice(null);
          URL.revokeObjectURL(audio.src);
        };
        
        await audio.play();
      }
    } catch (error) {
      console.error('Error playing voice:', error);
      setPlayingVoice(null);
    }
  };

  const handleDownload = async (voiceId: string) => {
    try {
      const response = await fetch(`/api/voice/download/${voiceId}`, {
        method: 'GET'
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `voice-${voiceId}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error downloading voice:', error);
    }
  };

  const handleBulkAction = (action: string) => {
    switch (action) {
      case 'delete':
        selectedVoices.forEach(voiceId => onVoiceDelete(voiceId));
        setSelectedVoices([]);
        break;
      case 'export':
        // Handle bulk export
        break;
      case 'favorite':
        // Handle bulk favorite
        break;
    }
    setShowBulkActions(false);
  };

  const formatPrice = (price: number) => {
    return price === 0 ? 'Free' : `$${price.toFixed(3)}/min`;
  };

  const customVoices = voices.filter(voice => voice.isCustom);
  const clonedVoices = voices.filter(voice => voice.isCloned && !voice.isCustom);
  const premiumVoices = voices.filter(voice => !voice.isCustom && !voice.isCloned);

  const VoiceCard: React.FC<{ voice: Voice; showCheckbox?: boolean }> = ({ 
    voice, 
    showCheckbox = false 
  }) => (
    <div className="bg-card border border-border rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-3">
          {showCheckbox && (
            <input
              type="checkbox"
              checked={selectedVoices.includes(voice.id)}
              onChange={(e) => {
                if (e.target.checked) {
                  setSelectedVoices(prev => [...prev, voice.id]);
                } else {
                  setSelectedVoices(prev => prev.filter(id => id !== voice.id));
                }
              }}
              className="mt-1"
            />
          )}
          
          <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
            <Volume2 className="w-6 h-6 text-indigo-600" />
          </div>
          
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-semibold">{voice.name}</h4>
              {voice.isFeatured && <Star className="w-4 h-4 text-yellow-500" />}
              {voice.isCustom && (
                <span className="text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300 px-2 py-1 rounded-full">
                  Custom
                </span>
              )}
              {voice.isCloned && (
                <span className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300 px-2 py-1 rounded-full">
                  Cloned
                </span>
              )}
            </div>
            
            <div className="text-sm text-gray-600 mb-2">
              {voice.provider} • {voice.gender} • {voice.accent}
            </div>
            
            <p className="text-sm text-gray-600 mb-3 line-clamp-2">
              {voice.description}
            </p>
            
            <div className="flex items-center gap-4 text-xs text-gray-600 mb-3">
              <span>{voice.language}</span>
              <span>{formatPrice(voice.pricePerMinute)}</span>
              <span>{voice.latency}ms latency</span>
              <span className="flex items-center gap-1">
                <Star className="w-3 h-3" />
                {voice.rating.toFixed(1)}
              </span>
              <span>{voice.totalUses} uses</span>
            </div>
            
            <div className="flex flex-wrap gap-1 mb-3">
              {voice.bestFor.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="text-xs bg-muted px-2 py-1 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="relative">
          <button className="p-1 hover:bg-accent rounded">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => handlePlay(voice.id)}
          className="flex items-center gap-1 bg-indigo-600 hover:bg-primary/90 text-primary-foreground px-3 py-1.5 rounded text-sm"
        >
          {playingVoice === voice.id ? (
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
          onClick={() => onVoiceClone(voice)}
          className="flex items-center gap-1 bg-muted hover:bg-muted/80 px-3 py-1.5 rounded text-sm"
        >
          <Copy className="w-3 h-3" />
          Clone
        </button>

        <button
          onClick={() => handleDownload(voice.id)}
          className="flex items-center gap-1 bg-muted hover:bg-muted/80 px-3 py-1.5 rounded text-sm"
        >
          <Download className="w-3 h-3" />
          Export
        </button>

        {voice.isCustom && (
          <>
            <button className="flex items-center gap-1 bg-muted hover:bg-muted/80 px-3 py-1.5 rounded text-sm">
              <Edit3 className="w-3 h-3" />
              Edit
            </button>
            
            <button
              onClick={() => onVoiceDelete(voice.id)}
              className="flex items-center gap-1 bg-destructive hover:bg-destructive/90 text-destructive-foreground px-3 py-1.5 rounded text-sm"
            >
              <Trash2 className="w-3 h-3" />
              Delete
            </button>
          </>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Bulk Actions */}
      {selectedVoices.length > 0 && (
        <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium">
                {selectedVoices.length} voices selected
              </span>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => handleBulkAction('favorite')}
                className="flex items-center gap-1 bg-muted hover:bg-muted/80 px-3 py-1.5 rounded text-sm"
              >
                <Heart className="w-3 h-3" />
                Favorite
              </button>
              
              <button
                onClick={() => handleBulkAction('export')}
                className="flex items-center gap-1 bg-muted hover:bg-muted/80 px-3 py-1.5 rounded text-sm"
              >
                <Download className="w-3 h-3" />
                Export
              </button>
              
              <button
                onClick={() => handleBulkAction('delete')}
                className="flex items-center gap-1 bg-destructive hover:bg-destructive/90 text-destructive-foreground px-3 py-1.5 rounded text-sm"
              >
                <Trash2 className="w-3 h-3" />
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Custom Voices Section */}
      {customVoices.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Settings className="w-5 h-5 text-indigo-600" />
              My Custom Voices ({customVoices.length})
            </h3>
            
            <button
              onClick={() => setShowBulkActions(!showBulkActions)}
              className="text-sm text-gray-600 hover:text-foreground"
            >
              Bulk Actions
            </button>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {customVoices.map(voice => (
              <VoiceCard key={voice.id} voice={voice} showCheckbox={showBulkActions} />
            ))}
          </div>
        </div>
      )}

      {/* Cloned Voices Section */}
      {clonedVoices.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Copy className="w-5 h-5 text-indigo-600" />
              Cloned Voices ({clonedVoices.length})
            </h3>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {clonedVoices.map(voice => (
              <VoiceCard key={voice.id} voice={voice} showCheckbox={showBulkActions} />
            ))}
          </div>
        </div>
      )}

      {/* Premium Voices Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Star className="w-5 h-5 text-indigo-600" />
            Premium Voices ({premiumVoices.length})
          </h3>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {premiumVoices.map(voice => (
            <VoiceCard key={voice.id} voice={voice} showCheckbox={showBulkActions} />
          ))}
        </div>
      </div>

      {/* Empty States */}
      {voices.length === 0 && (
        <div className="text-center py-12">
          <Volume2 className="w-16 h-16 text-gray-600/50 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No voices found</h3>
          <p className="text-gray-600 mb-4">
            Create your first custom voice or clone an existing one
          </p>
          <button className="bg-indigo-600 hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-md">
            Create Voice
          </button>
        </div>
      )}
    </div>
  );
};