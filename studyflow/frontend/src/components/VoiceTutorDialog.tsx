/**
 * Voice Tutor Dialog Component
 *
 * Provides UI for VAPI-based voice tutoring sessions where students can have
 * natural voice conversations about their study materials.
 *
 * Features:
 * - Assistant creation/configuration
 * - Voice call initiation
 * - Call status indicators
 * - Call timer and cost tracking
 * - Animated speaking indicator
 */

import { useState, useEffect } from 'react';
import {
  Phone,
  PhoneOff,
  Mic,
  MicOff,
  Loader2,
  X,
  Clock,
  DollarSign,
  CheckCircle,
  AlertCircle,
  PhoneCall,
  Sparkles,
} from 'lucide-react';
import { vapiTutoringApi } from '../lib/api';
import { Button } from './ui/button';
import { Card } from './ui/card';

interface VoiceTutorDialogProps {
  materialId: string;
  materialTitle: string;
  onClose: () => void;
}

interface AssistantInfo {
  has_assistant: boolean;
  assistant_id?: string;
  created_at?: string;
}

interface CallInfo {
  session_id: string;
  call_id: string;
  status: string;
}

export default function VoiceTutorDialog({
  materialId,
  materialTitle,
  onClose,
}: VoiceTutorDialogProps) {
  // Assistant state
  const [assistantInfo, setAssistantInfo] = useState<AssistantInfo | null>(null);
  const [loadingAssistant, setLoadingAssistant] = useState(true);
  const [creatingAssistant, setCreatingAssistant] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState('jennifer');

  // Call state
  const [phoneNumber, setPhoneNumber] = useState('');
  const [callInfo, setCallInfo] = useState<CallInfo | null>(null);
  const [callStatus, setCallStatus] = useState<'idle' | 'connecting' | 'active' | 'ended'>('idle');
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);

  // Error/Success state
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Available voices
  const voices = [
    { id: 'jennifer', name: 'Jennifer', description: 'Warm, patient, encouraging', recommended: true },
    { id: 'mark', name: 'Mark', description: 'Clear, professional, supportive', recommended: true },
    { id: 'sarah', name: 'Sarah', description: 'Friendly, energetic, motivating', recommended: false },
    { id: 'david', name: 'David', description: 'Calm, steady, reassuring', recommended: false },
  ];

  useEffect(() => {
    loadAssistantInfo();
  }, [materialId]);

  // Call timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (callStatus === 'active') {
      interval = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [callStatus]);

  const loadAssistantInfo = async () => {
    try {
      setLoadingAssistant(true);
      const data = await vapiTutoringApi.getMaterialAssistant(materialId);
      setAssistantInfo(data);
      setError(null);
    } catch (err: any) {
      console.error('Error loading assistant info:', err);
      setError('Failed to load assistant information');
    } finally {
      setLoadingAssistant(false);
    }
  };

  const handleCreateAssistant = async () => {
    try {
      setCreatingAssistant(true);
      setError(null);

      await vapiTutoringApi.createAssistant({
        material_id: materialId,
        voice_id: selectedVoice,
        language: 'en',
      });

      setSuccess('Voice tutor created successfully!');
      await loadAssistantInfo();
    } catch (err: any) {
      console.error('Error creating assistant:', err);
      setError(err.message || 'Failed to create voice tutor');
    } finally {
      setCreatingAssistant(false);
    }
  };

  const handleStartCall = async () => {
    if (!phoneNumber.trim()) {
      setError('Please enter your phone number');
      return;
    }

    try {
      setCallStatus('connecting');
      setError(null);
      setCallDuration(0);

      const data = await vapiTutoringApi.startSession({
        material_id: materialId,
        phone_number: phoneNumber,
      });

      setCallInfo(data);
      setCallStatus('active');
      setSuccess('Call initiated! You should receive a call shortly.');
    } catch (err: any) {
      console.error('Error starting call:', err);
      setError(err.message || 'Failed to start call');
      setCallStatus('idle');
    }
  };

  const handleEndCall = () => {
    setCallStatus('ended');
    setSuccess(`Call ended. Duration: ${formatDuration(callDuration)}`);
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const estimatedCost = (callDuration / 60) * 0.10; // Rough estimate: $0.10/minute

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
      <div className="w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-2xl bg-white shadow-2xl animate-in zoom-in-95 duration-300">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-purple-700 px-6 py-5 flex items-center justify-between shadow-lg z-10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
              <Phone className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Voice Tutor
              </h2>
              <p className="text-sm text-purple-100 mt-0.5 line-clamp-1">{materialTitle}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-white" />
          </button>
        </div>

        <div className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-88px)]">
          {/* Error/Success Messages */}
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 animate-in slide-in-from-top duration-300">
              <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-900">Error</p>
                <p className="text-sm text-red-700 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-xl flex items-start gap-3 animate-in slide-in-from-top duration-300">
              <CheckCircle className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-green-900">Success</p>
                <p className="text-sm text-green-700 mt-0.5">{success}</p>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loadingAssistant ? (
            <div className="text-center py-16">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
                <Loader2 className="h-8 w-8 text-purple-600 animate-spin" />
              </div>
              <p className="text-gray-900 font-medium">Loading voice tutor...</p>
              <p className="text-sm text-gray-600 mt-1">Please wait a moment</p>
            </div>
          ) : !assistantInfo?.has_assistant ? (
            /* Setup Assistant */
            <div className="space-y-6">
              {/* Header Section */}
              <div className="text-center pb-4 border-b border-gray-200">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-100 to-purple-200 rounded-2xl mb-4">
                  <Sparkles className="h-8 w-8 text-purple-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  Set Up Your Voice Tutor
                </h3>
                <p className="text-sm text-gray-600 max-w-md mx-auto">
                  Create an AI voice tutor for this document. Students can call and have natural
                  conversations to learn the material.
                </p>
              </div>

              {/* Voice Selection */}
              <div>
                <label className="block text-sm font-semibold text-gray-900 mb-3">
                  Select Tutor Voice
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {voices.map((voice) => (
                    <button
                      key={voice.id}
                      onClick={() => setSelectedVoice(voice.id)}
                      className={`group relative p-4 border-2 rounded-xl text-left transition-all duration-200 ${
                        selectedVoice === voice.id
                          ? 'border-purple-600 bg-purple-50 shadow-md scale-[1.02]'
                          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm hover:scale-[1.01]'
                      }`}
                    >
                      {selectedVoice === voice.id && (
                        <div className="absolute top-3 right-3">
                          <CheckCircle className="h-5 w-5 text-purple-600" />
                        </div>
                      )}
                      <div className="flex items-start justify-between mb-2 pr-6">
                        <span className={`font-semibold text-base ${
                          selectedVoice === voice.id ? 'text-purple-900' : 'text-gray-900'
                        }`}>
                          {voice.name}
                        </span>
                        {voice.recommended && (
                          <span className="text-xs bg-purple-600 text-white px-2.5 py-1 rounded-full font-medium">
                            Best
                          </span>
                        )}
                      </div>
                      <p className={`text-xs leading-relaxed ${
                        selectedVoice === voice.id ? 'text-purple-700' : 'text-gray-600'
                      }`}>
                        {voice.description}
                      </p>
                    </button>
                  ))}
                </div>
              </div>

              <Button
                onClick={handleCreateAssistant}
                disabled={creatingAssistant}
                className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white py-6 text-base font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
              >
                {creatingAssistant ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin mr-2" />
                    Creating Voice Tutor...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-5 w-5 mr-2" />
                    Create Voice Tutor
                  </>
                )}
              </Button>
            </div>
          ) : (
            /* Start Call Interface */
            <div className="space-y-6">
              {/* Assistant Info */}
              <div className="p-5 bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-xl">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-purple-600 rounded-lg">
                    <CheckCircle className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-purple-900">Voice Tutor Ready</p>
                    <p className="text-xs text-purple-700 mt-1 leading-relaxed">
                      Your AI voice tutor is configured and ready to help students learn this material.
                    </p>
                  </div>
                </div>
              </div>

              {/* Call Status Display */}
              {callStatus !== 'idle' && (
                <div className="p-8 bg-gradient-to-br from-purple-50 via-purple-50 to-blue-50 border border-purple-200 rounded-2xl">
                  <div className="text-center space-y-6">
                    {/* Animated Speaking Indicator */}
                    {callStatus === 'active' && (
                      <div className="flex justify-center items-end gap-1.5 h-24 mb-2">
                        {[0, 150, 300, 450, 600].map((delay, i) => (
                          <div
                            key={i}
                            className="w-2 bg-gradient-to-t from-purple-600 to-purple-400 rounded-full animate-pulse"
                            style={{
                              animationDelay: `${delay}ms`,
                              height: i === 2 ? '5rem' : i === 1 || i === 3 ? '4rem' : '3rem',
                              animationDuration: '1s',
                            }}
                          />
                        ))}
                      </div>
                    )}

                    {callStatus === 'connecting' && (
                      <div className="inline-flex items-center justify-center w-20 h-20 bg-purple-100 rounded-full mb-2">
                        <PhoneCall className="h-10 w-10 text-purple-600 animate-pulse" />
                      </div>
                    )}

                    {/* Call Status */}
                    <div>
                      <p className="text-3xl font-bold text-gray-900 mb-2">
                        {callStatus === 'connecting' && 'Connecting...'}
                        {callStatus === 'active' && 'Call Active'}
                        {callStatus === 'ended' && 'Call Ended'}
                      </p>
                      {callStatus === 'connecting' && (
                        <p className="text-sm text-gray-600">
                          Initiating call to <span className="font-mono font-semibold">{phoneNumber}</span>
                        </p>
                      )}
                      {callStatus === 'active' && (
                        <p className="text-sm text-purple-700 font-medium">
                          Having conversation about study material
                        </p>
                      )}
                    </div>

                    {/* Call Timer and Cost */}
                    {(callStatus === 'active' || callStatus === 'ended') && (
                      <div className="flex items-center justify-center gap-8">
                        <div className="flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-lg shadow-sm">
                          <Clock className="h-5 w-5 text-gray-600" />
                          <div className="text-left">
                            <p className="text-xs text-gray-600 font-medium">Duration</p>
                            <p className="text-lg font-mono font-bold text-gray-900">{formatDuration(callDuration)}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-lg shadow-sm">
                          <DollarSign className="h-5 w-5 text-gray-600" />
                          <div className="text-left">
                            <p className="text-xs text-gray-600 font-medium">Est. Cost</p>
                            <p className="text-lg font-mono font-bold text-gray-900">${estimatedCost.toFixed(2)}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Call Controls */}
                    {callStatus === 'active' && (
                      <div className="flex justify-center gap-4 pt-4">
                        <button
                          onClick={() => setIsMuted(!isMuted)}
                          className={`p-5 rounded-full transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105 ${
                            isMuted
                              ? 'bg-red-500 text-white hover:bg-red-600'
                              : 'bg-white text-gray-700 hover:bg-gray-50'
                          }`}
                          title={isMuted ? 'Unmute' : 'Mute'}
                        >
                          {isMuted ? <MicOff className="h-6 w-6" /> : <Mic className="h-6 w-6" />}
                        </button>
                        <button
                          onClick={handleEndCall}
                          className="p-5 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-full hover:from-red-700 hover:to-red-800 transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105"
                          title="End Call"
                        >
                          <PhoneOff className="h-6 w-6" />
                        </button>
                      </div>
                    )}

                    {callStatus === 'ended' && (
                      <Button
                        onClick={() => setCallStatus('idle')}
                        className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-lg hover:shadow-xl"
                      >
                        <Phone className="h-5 w-5 mr-2" />
                        Start New Call
                      </Button>
                    )}
                  </div>
                </div>
              )}

              {/* Phone Number Input (only show when idle) */}
              {callStatus === 'idle' && (
                <div className="space-y-5">
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Your Phone Number
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="tel"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        placeholder="+1234567890"
                        className="w-full pl-12 pr-4 py-4 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-600 focus:border-purple-600 transition-colors text-base"
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                      <span className="inline-block w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                      Include country code (e.g., +1 for US, +233 for Ghana)
                    </p>
                  </div>

                  <Button
                    onClick={handleStartCall}
                    disabled={!phoneNumber.trim()}
                    className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:from-gray-300 disabled:to-gray-400 text-white py-6 text-base font-semibold shadow-lg hover:shadow-xl transition-all duration-200"
                  >
                    <PhoneCall className="h-5 w-5 mr-2" />
                    Start Voice Tutoring Call
                  </Button>

                  {/* Info Box */}
                  <div className="p-5 bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-xl">
                    <div className="flex items-start gap-3 mb-3">
                      <div className="p-1.5 bg-blue-600 rounded-lg">
                        <Phone className="h-4 w-4 text-white" />
                      </div>
                      <p className="text-sm font-semibold text-blue-900">
                        How Voice Tutoring Works
                      </p>
                    </div>
                    <ul className="text-sm text-blue-800 space-y-2 ml-1">
                      <li className="flex items-start gap-2">
                        <span className="inline-block w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5 shrink-0"></span>
                        <span>You'll receive a phone call from our AI tutor</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="inline-block w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5 shrink-0"></span>
                        <span>Have a natural conversation about the study material</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="inline-block w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5 shrink-0"></span>
                        <span>Ask questions, request exercises, and get feedback</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="inline-block w-1.5 h-1.5 bg-blue-600 rounded-full mt-1.5 shrink-0"></span>
                        <span>Sessions are tracked and costs are calculated automatically</span>
                      </li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
