/**
 * GreetingAudioPlayer Component
 *
 * Plays voice greeting audio after successful check-in
 * with visual feedback and controls
 */

import { useState, useEffect, useRef } from 'react';
import { Volume2, VolumeX, Play, Pause, AlertCircle } from 'lucide-react';
import type { GreetingAudio } from '../lib/api';

interface GreetingAudioPlayerProps {
  greetingAudio: GreetingAudio;
  autoPlay?: boolean;
  onPlaybackComplete?: () => void;
}

export default function GreetingAudioPlayer({
  greetingAudio,
  autoPlay = true,
  onPlaybackComplete
}: GreetingAudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    // Set up event listeners
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleEnded = () => {
      setIsPlaying(false);
      if (onPlaybackComplete) {
        onPlaybackComplete();
      }
    };
    const handleError = () => {
      setError('Failed to play audio');
      setIsPlaying(false);
    };
    const handleLoadedData = () => {
      // Audio is loaded, safe to play
      if (autoPlay) {
        // Small delay to ensure browser is ready
        setTimeout(() => {
          audio.play().catch((err) => {
            console.error('Auto-play failed:', err);
            setError('Please click play to hear your greeting');
          });
        }, 100);
      }
    };

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);
    audio.addEventListener('loadeddata', handleLoadedData);

    // Trigger load if already loaded
    if (audio.readyState >= 2) {
      handleLoadedData();
    }

    return () => {
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
      audio.removeEventListener('loadeddata', handleLoadedData);
    };
  }, [autoPlay, onPlaybackComplete]);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play().catch((err) => {
        console.error('Play failed:', err);
        setError('Failed to play audio');
      });
    }
  };

  const toggleMute = () => {
    const audio = audioRef.current;
    if (!audio) return;

    audio.muted = !audio.muted;
    setIsMuted(!isMuted);
  };

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
      <div className="flex items-center space-x-4">
        {/* Play/Pause Button */}
        <button
          onClick={togglePlayPause}
          className="flex-shrink-0 bg-purple-600 hover:bg-purple-700 text-white rounded-full p-3 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? (
            <Pause className="w-6 h-6" />
          ) : (
            <Play className="w-6 h-6" />
          )}
        </button>

        {/* Greeting Text */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-purple-900 mb-1">
            Voice Greeting
          </p>
          <p className="text-sm text-gray-700 truncate">
            {greetingAudio.text}
          </p>
          {greetingAudio.duration_seconds && (
            <p className="text-xs text-gray-500 mt-1">
              Duration: {greetingAudio.duration_seconds.toFixed(1)}s
            </p>
          )}
        </div>

        {/* Mute/Unmute Button */}
        <button
          onClick={toggleMute}
          className="flex-shrink-0 text-gray-600 hover:text-purple-600 transition-colors p-2 rounded-full hover:bg-purple-100"
          aria-label={isMuted ? 'Unmute' : 'Mute'}
        >
          {isMuted ? (
            <VolumeX className="w-5 h-5" />
          ) : (
            <Volume2 className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Waveform Animation */}
      {isPlaying && !error && (
        <div className="mt-3 flex items-center justify-center space-x-1">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="bg-purple-500 rounded-full animate-pulse"
              style={{
                width: '3px',
                height: `${Math.random() * 16 + 8}px`,
                animationDelay: `${i * 0.05}s`,
                animationDuration: '0.8s'
              }}
            />
          ))}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-3 flex items-center text-amber-600 text-sm">
          <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Hidden Audio Element */}
      <audio
        ref={audioRef}
        src={greetingAudio.audio_url}
        preload="auto"
      />

      {/* Provider Badge */}
      <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
        <span>Powered by {greetingAudio.provider_used}</span>
        {greetingAudio.cost_usd !== undefined && (
          <span>${greetingAudio.cost_usd.toFixed(4)}</span>
        )}
      </div>
    </div>
  );
}
