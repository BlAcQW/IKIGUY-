/**
 * useAudioPlayer Hook
 * Manages audio playback state and controls
 */

import { useState, useRef, useEffect, useCallback } from 'react';

interface UseAudioPlayerProps {
  src?: string;
  onEnded?: () => void;
  onTimeUpdate?: (currentTime: number) => void;
  onLoadedMetadata?: (duration: number) => void;
}

export const useAudioPlayer = ({
  src,
  onEnded,
  onTimeUpdate,
  onLoadedMetadata,
}: UseAudioPlayerProps = {}) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const shouldAutoPlay = useRef(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [volume, setVolume] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize audio element
  useEffect(() => {
    const audio = new Audio();
    audioRef.current = audio;

    // Prevent autoload to avoid browser warnings for empty src
    audio.preload = 'none';
    // Explicitly set src to empty string to avoid CSP violations with 'about:blank'
    audio.src = '';

    /**
     * Check if audio element has a valid playable source
     */
    const hasValidSource = (): boolean => {
      const audioSrc = audio.src;
      return audioSrc !== '' &&
             audioSrc !== 'about:blank' &&
             audioSrc !== window.location.href &&
             !audioSrc.startsWith('http://') &&
             !audioSrc.startsWith('https://') &&
             (audioSrc.startsWith('data:audio/') || audioSrc.startsWith('blob:'));
    };

    audio.addEventListener('loadstart', () => {
      // Only log if we have a valid source
      if (hasValidSource()) {
        console.log('Audio loadstart event fired');
      }
      setIsLoading(true);
    });
    audio.addEventListener('canplay', () => {
      console.log('Audio canplay event fired. shouldAutoPlay:', shouldAutoPlay.current);
      setIsLoading(false);
      // Auto-play if requested (after audio generation)
      if (shouldAutoPlay.current) {
        console.log('Auto-playing audio...');
        shouldAutoPlay.current = false;
        audio.play()
          .then(() => {
            console.log('Auto-play successful');
            setIsPlaying(true);
          })
          .catch((err) => {
            console.error('Auto-play failed:', err);
            setError('Failed to play audio');
          });
      }
    });
    audio.addEventListener('error', () => {
      setIsLoading(false);
      shouldAutoPlay.current = false; // Clear auto-play on error
      // Only set error if we actually have a valid src (avoid errors when src is empty or about:blank)
      if (hasValidSource()) {
        setError('Failed to load audio');
      }
    });

    audio.addEventListener('timeupdate', () => {
      const time = audio.currentTime;
      setCurrentTime(time);
      onTimeUpdate?.(time);
    });

    audio.addEventListener('loadedmetadata', () => {
      const dur = audio.duration;
      setDuration(dur);
      onLoadedMetadata?.(dur);
    });

    audio.addEventListener('ended', () => {
      setIsPlaying(false);
      onEnded?.();
    });

    return () => {
      audio.pause();
      audio.src = '';
    };
  }, [onEnded, onTimeUpdate, onLoadedMetadata]);

  // Update src when it changes
  useEffect(() => {
    if (audioRef.current) {
      if (src) {
        // Only set src and load if we have a valid source
        console.log('Setting audio src:', src.substring(0, 50) + '...');
        audioRef.current.src = src;
        audioRef.current.preload = 'metadata'; // Enable preload when we have audio
        audioRef.current.load();
        setError(null);
      } else {
        // Set to empty string to avoid CSP violations with 'about:blank'
        audioRef.current.src = '';
        audioRef.current.preload = 'none'; // Disable preload when no audio
        setError(null);
      }
    }
  }, [src]);

  const play = useCallback(async () => {
    if (audioRef.current) {
      // Don't try to play if source is about:blank or empty
      const currentSrc = audioRef.current.src;
      if (!currentSrc || currentSrc === 'about:blank' || currentSrc === window.location.href) {
        return;
      }
      try {
        const playPromise = audioRef.current.play();
        if (playPromise !== undefined) {
          await playPromise;
          setIsPlaying(true);
          setError(null);
        }
      } catch (err: any) {
        // Ignore AbortError - happens when play() is interrupted by pause()
        // Also ignore NotSupportedError for invalid sources
        if (err.name === 'AbortError' || err.name === 'NotSupportedError') {
          return;
        }
        console.error('Error playing audio:', err);
        setError('Failed to play audio');
        setIsPlaying(false);
      }
    }
  }, []);

  const pause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  const togglePlay = useCallback(() => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  }, [isPlaying, play, pause]);

  const seek = useCallback((time: number) => {
    if (audioRef.current && isFinite(time) && time >= 0) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  }, []);

  const skipForward = useCallback((seconds: number = 15) => {
    if (audioRef.current && isFinite(duration) && duration > 0) {
      const newTime = Math.min(audioRef.current.currentTime + seconds, duration);
      seek(newTime);
    }
  }, [duration, seek]);

  const skipBackward = useCallback((seconds: number = 15) => {
    if (audioRef.current && isFinite(duration) && duration > 0) {
      const newTime = Math.max(audioRef.current.currentTime - seconds, 0);
      seek(newTime);
    }
  }, [duration, seek]);

  const changePlaybackRate = useCallback((rate: number) => {
    if (audioRef.current) {
      audioRef.current.playbackRate = rate;
      setPlaybackRate(rate);
    }
  }, []);

  const changeVolume = useCallback((vol: number) => {
    if (audioRef.current) {
      audioRef.current.volume = vol;
      setVolume(vol);
    }
  }, []);

  const enableAutoPlay = useCallback(() => {
    console.log('enableAutoPlay() called - setting shouldAutoPlay to true');
    shouldAutoPlay.current = true;
  }, []);

  return {
    // State
    isPlaying,
    currentTime,
    duration,
    playbackRate,
    volume,
    isLoading,
    error,
    // Controls
    play,
    pause,
    togglePlay,
    seek,
    skipForward,
    skipBackward,
    changePlaybackRate,
    changeVolume,
    enableAutoPlay,
  };
};
