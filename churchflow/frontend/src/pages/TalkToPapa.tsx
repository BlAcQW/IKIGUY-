/**
 * Talk To Papa Page
 *
 * Voice assistant page using VAPI widget for Action Chapel International.
 * Allows users to interact with Papa AI assistant for church services.
 */

import { useEffect, useState, useRef } from 'react';
import { ArrowLeft, Phone, PhoneCall, Mic, MicOff, Loader2, PhoneOff, Volume2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// VAPI SDK types
declare global {
  interface Window {
    Vapi?: any;
    vapiSDK?: any;
  }
}

type CallStatus = 'idle' | 'connecting' | 'connected' | 'ended';

export default function TalkToPapa() {
  const navigate = useNavigate();
  const [callStatus, setCallStatus] = useState<CallStatus>('idle');
  const [isMuted, setIsMuted] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string>('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const vapiRef = useRef<any>(null);

  // VAPI configuration
  const VAPI_PUBLIC_KEY = '0c22dcea-0d6c-4fc0-8fb2-93292d8575e8';
  const ASSISTANT_ID = 'c2854d74-dafe-445c-8c34-1326c2310cb7';

  useEffect(() => {
    // Load VAPI Web SDK from official CDN
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/gh/VapiAI/html-script-tag@latest/dist/assets/index.js';
    script.async = true;
    script.defer = true;

    script.onload = () => {
      // Small delay to ensure SDK is fully initialized
      setTimeout(() => {
        try {
          if (window.vapiSDK) {
            // Initialize VAPI using the official SDK method
            vapiRef.current = window.vapiSDK.run({
              apiKey: VAPI_PUBLIC_KEY,
              assistant: ASSISTANT_ID,
              config: {
                // Hide the default button - we use our own UI
                hide: true,
                position: 'bottom-right'
              }
            });

            // Set up event listeners
            if (vapiRef.current) {
              vapiRef.current.on('call-start', () => {
                setCallStatus('connected');
                setTranscript('');
              });

              vapiRef.current.on('call-end', () => {
                setCallStatus('ended');
                setTimeout(() => setCallStatus('idle'), 2000);
              });

              vapiRef.current.on('speech-start', () => {
                setIsSpeaking(true);
              });

              vapiRef.current.on('speech-end', () => {
                setIsSpeaking(false);
              });

              vapiRef.current.on('message', (message: any) => {
                if (message.type === 'transcript' && message.transcriptType === 'final') {
                  setTranscript(prev => prev + (message.role === 'user' ? '\nYou: ' : '\nPapa: ') + message.transcript);
                }
              });

              vapiRef.current.on('error', (e: any) => {
                console.error('VAPI Error:', e);
                setError('Connection error. Please try again.');
                setCallStatus('idle');
              });
            }

            setIsLoading(false);
          } else {
            setError('Voice SDK not available. Please refresh.');
            setIsLoading(false);
          }
        } catch (e) {
          console.error('Failed to initialize VAPI:', e);
          setError('Failed to initialize voice assistant.');
          setIsLoading(false);
        }
      }, 500);
    };

    script.onerror = () => {
      setError('Failed to load voice assistant. Please refresh the page.');
      setIsLoading(false);
    };

    document.body.appendChild(script);

    return () => {
      // Cleanup
      if (vapiRef.current) {
        try {
          vapiRef.current.stop();
        } catch (e) {
          // Ignore cleanup errors
        }
      }
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, []);

  const startCall = async () => {
    if (!vapiRef.current) {
      setError('Voice assistant not ready. Please refresh.');
      return;
    }

    setCallStatus('connecting');
    setError(null);

    try {
      // The SDK's run() method returns a vapi instance
      // We can start the call using the start() method
      if (typeof vapiRef.current.start === 'function') {
        await vapiRef.current.start();
      } else {
        // Alternative: trigger the call via the SDK's button click
        const vapiButton = document.querySelector('[data-vapi-btn]') as HTMLButtonElement;
        if (vapiButton) {
          vapiButton.click();
        } else {
          throw new Error('Unable to start call');
        }
      }
    } catch (e: any) {
      console.error('Failed to start call:', e);
      setError(e.message || 'Failed to start call. Please check microphone permissions.');
      setCallStatus('idle');
    }
  };

  const endCall = () => {
    if (vapiRef.current) {
      vapiRef.current.stop();
    }
    setCallStatus('ended');
    setTimeout(() => setCallStatus('idle'), 2000);
  };

  const toggleMute = () => {
    if (vapiRef.current) {
      vapiRef.current.setMuted(!isMuted);
      setIsMuted(!isMuted);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-md border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-2 text-gray-300 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span className="hidden sm:inline">Back</span>
            </button>
            <h1 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
              <Phone className="w-5 h-5 sm:w-6 sm:h-6 text-teal-500" />
              Talk To Papa
            </h1>
            <div className="w-16 sm:w-20"></div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 sm:py-8">
        <div className="max-w-2xl mx-auto">

          {/* Call Interface Card - Primary Focus */}
          <div className="bg-gray-800/70 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-700 p-6 sm:p-8 mb-6">
            {/* Avatar/Status */}
            <div className="text-center mb-6">
              <div className={`relative inline-flex items-center justify-center w-24 h-24 sm:w-28 sm:h-28 rounded-full mb-4 ${
                callStatus === 'connected'
                  ? 'bg-teal-500/30 ring-4 ring-teal-500/50'
                  : 'bg-gray-700/50'
              }`}>
                {/* Speaking indicator */}
                {callStatus === 'connected' && isSpeaking && (
                  <div className="absolute inset-0 rounded-full bg-teal-500/30 animate-ping" />
                )}
                <Phone className={`w-12 h-12 sm:w-14 sm:h-14 ${
                  callStatus === 'connected' ? 'text-teal-400' : 'text-gray-400'
                }`} />
              </div>

              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-1">
                Papa's Assistant
              </h2>
              <p className="text-gray-400">
                {callStatus === 'idle' && 'Ready to help you'}
                {callStatus === 'connecting' && 'Connecting...'}
                {callStatus === 'connected' && (isSpeaking ? 'Speaking...' : 'Listening...')}
                {callStatus === 'ended' && 'Call ended'}
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm text-center">
                {error}
              </div>
            )}

            {/* Call Button */}
            <div className="flex justify-center gap-4 mb-6">
              {callStatus === 'idle' && (
                <button
                  onClick={startCall}
                  disabled={isLoading}
                  className="flex items-center gap-3 px-8 py-4 bg-teal-600 hover:bg-teal-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-full text-lg shadow-lg shadow-teal-500/30 transition-all transform hover:scale-105 active:scale-95"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-6 h-6 animate-spin" />
                      <span>Loading...</span>
                    </>
                  ) : (
                    <>
                      <PhoneCall className="w-6 h-6" />
                      <span>Start Call</span>
                    </>
                  )}
                </button>
              )}

              {callStatus === 'connecting' && (
                <button
                  disabled
                  className="flex items-center gap-3 px-8 py-4 bg-yellow-600 text-white font-semibold rounded-full text-lg"
                >
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <span>Connecting...</span>
                </button>
              )}

              {callStatus === 'connected' && (
                <div className="flex items-center gap-3">
                  <button
                    onClick={toggleMute}
                    className={`p-4 rounded-full transition-all ${
                      isMuted
                        ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                        : 'bg-gray-700 text-white hover:bg-gray-600'
                    }`}
                    title={isMuted ? 'Unmute' : 'Mute'}
                  >
                    {isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
                  </button>

                  <button
                    onClick={endCall}
                    className="flex items-center gap-3 px-8 py-4 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-full text-lg shadow-lg shadow-red-500/30 transition-all"
                  >
                    <PhoneOff className="w-6 h-6" />
                    <span>End Call</span>
                  </button>
                </div>
              )}

              {callStatus === 'ended' && (
                <div className="text-center">
                  <p className="text-gray-400 mb-4">Call ended</p>
                  <button
                    onClick={() => setCallStatus('idle')}
                    className="text-teal-500 hover:text-teal-400 font-medium"
                  >
                    Start new call
                  </button>
                </div>
              )}
            </div>

            {/* Live Transcript (when connected) */}
            {callStatus === 'connected' && (
              <div className="bg-gray-900/50 rounded-lg p-4 max-h-40 overflow-y-auto">
                <div className="flex items-center gap-2 text-gray-400 text-sm mb-2">
                  <Volume2 className="w-4 h-4" />
                  <span>Live Transcript</span>
                </div>
                <p className="text-gray-300 text-sm whitespace-pre-wrap">
                  {transcript || 'Waiting for conversation...'}
                </p>
              </div>
            )}
          </div>

          {/* Quick Info - Collapsible on mobile */}
          <div className="bg-gray-800/40 backdrop-blur-sm rounded-xl border border-gray-700/50 p-5">
            <div className="grid sm:grid-cols-2 gap-4 text-sm">
              <div>
                <h3 className="text-white font-medium mb-2 flex items-center gap-2">
                  <span className="w-6 h-6 bg-teal-500/20 rounded-full flex items-center justify-center text-teal-500 text-xs">?</span>
                  What Papa Can Help With
                </h3>
                <ul className="text-gray-400 space-y-1 pl-8">
                  <li>• Tithes & offerings</li>
                  <li>• Counseling sessions</li>
                  <li>• Wedding/funeral arrangements</li>
                  <li>• Baby dedications</li>
                  <li>• General inquiries</li>
                </ul>
              </div>
              <div>
                <h3 className="text-white font-medium mb-2 flex items-center gap-2">
                  <span className="w-6 h-6 bg-teal-500/20 rounded-full flex items-center justify-center text-teal-500 text-xs">!</span>
                  Tips for Best Experience
                </h3>
                <ul className="text-gray-400 space-y-1 pl-8">
                  <li>• Use headphones for clarity</li>
                  <li>• Speak clearly and naturally</li>
                  <li>• Allow microphone access</li>
                  <li>• Find a quiet environment</li>
                </ul>
              </div>
            </div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 text-center text-gray-500">
        <p className="text-xs">
          Powered by AI Labs Africa | Action Chapel International
        </p>
      </footer>
    </div>
  );
}
