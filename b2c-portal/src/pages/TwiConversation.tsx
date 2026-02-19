import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { VoiceActivityDetector } from '@/utils/vad';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

import { 
  Mic, 
  MicOff,
  Volume2,
  VolumeX,
  Loader2,
  WifiOff,
  Wifi,
  MessageSquare,
  User,
  Bot,
  Send
} from 'lucide-react';

// Using API_BASE_URL from api-config;
const WS_BASE_URL = API_BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://');

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  transcription?: {
    confidence?: number;
    language?: string;
  };
}

export default function TwiConversation() {
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTranscription, setCurrentTranscription] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [textInput, setTextInput] = useState('');
  const [useVAD, setUseVAD] = useState(true);
  const [volumeLevel, setVolumeLevel] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [ttsProvider, setTtsProvider] = useState('akan');
  
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<Blob[]>([]);
  const vadRef = useRef<VoiceActivityDetector | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentTranscription]);

  // Initialize WebSocket connection
  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket(`${WS_BASE_URL}/api/voice-lab/ws/chat`);
      
      ws.onopen = () => {
        console.log('🔌 WebSocket connected');
        setIsConnected(true);
        
        // Start a new session
        const sessionRequest = {
          type: 'start_session',
          domain: 'general',
          language: 'tw',
          dialect: 'asante',
          tts_provider: ttsProvider
        };
        console.log('📤 Sending session start:', sessionRequest);
        ws.send(JSON.stringify(sessionRequest));
        
        toast({
          title: '✅ Connected',
          description: 'Ready for Twi conversation',
        });
      };

      ws.onmessage = async (event) => {
        console.log('📨 WebSocket message received:', event.data);
        const data = JSON.parse(event.data);
        console.log('📊 Parsed message type:', data.type, 'Data:', data);
        
        switch (data.type) {
          case 'session_started':
            console.log('✅ Session started with ID:', data.session_id);
            setSessionId(data.session_id);
            setMessages(prev => [...prev, {
              id: `system-${Date.now()}`,
              role: 'system',
              content: 'Akwaaba! Me yɛ AI assistant. Mete Twi ne English. Dɛn na metumi aboa wo?',
              timestamp: new Date()
            }]);
            break;
            
          case 'partial_transcription':
            setCurrentTranscription(data.text);
            break;
            
          case 'final_transcription':
            console.log('📝 Final transcription received:', data.text, 'Confidence:', data.confidence);
            setCurrentTranscription('');
            setMessages(prev => [...prev, {
              id: `user-${Date.now()}`,
              role: 'user',
              content: data.text,
              timestamp: new Date(),
              transcription: {
                confidence: data.confidence,
                language: data.language
              }
            }]);
            break;
            
          case 'response':
            console.log('🤖 AI response received:', data.text?.substring(0, 100) + '...');
            console.log('🔊 Audio available:', !!data.audio, 'Muted:', isMuted);
            setIsProcessing(false);
            setMessages(prev => [...prev, {
              id: `assistant-${Date.now()}`,
              role: 'assistant',
              content: data.text,
              timestamp: new Date()
            }]);
            
            // Play audio response if available and not muted
            if (data.audio && !isMuted) {
              console.log('🎵 Playing audio response...');
              playAudioResponse(data.audio);
            } else if (!data.audio) {
              console.log('⚠️ No audio in response');
            }
            break;
            
          case 'error':
            console.error('❌ WebSocket error:', data.message);
            toast({
              title: 'Error',
              description: data.message,
              variant: 'destructive',
            });
            setIsProcessing(false);
            break;
            
          default:
            console.warn('⚠️ Unknown message type:', data.type);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        setSessionId(null); // Clear session on error
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setSessionId(null); // Clear session on disconnect
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 3000);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      toast({
        title: 'Connection Failed',
        description: 'Unable to connect to the server',
        variant: 'destructive',
      });
    }
  }, [isMuted, toast]);

  // Initialize on mount
  useEffect(() => {
    connectWebSocket();
    
    // Initialize audio context
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
    };
  }, [connectWebSocket]);

  // Start recording with VAD
  const startRecording = async () => {
    try {
      // Ensure we have a session before recording
      if (!sessionId) {
        console.warn('⚠️ No session ID yet, requesting new session...');
        
        // Request a new session if not connected
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          const sessionRequest = {
            type: 'start_session',
            domain: 'general',
            language: 'tw',
            dialect: 'asante',
            tts_provider: ttsProvider
          };
          console.log('📤 Requesting new session before recording:', sessionRequest);
          wsRef.current.send(JSON.stringify(sessionRequest));
          
          // Wait a moment for session to be created
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Check if session was created
          if (!sessionId) {
            toast({
              title: '⚠️ Session Not Ready',
              description: 'Please wait for connection to establish',
              variant: 'destructive',
            });
            return;
          }
        } else {
          toast({
            title: '❌ Not Connected',
            description: 'Please wait for connection to establish',
            variant: 'destructive',
          });
          return;
        }
      }
      
      console.log('✅ Session ready:', sessionId);
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        } 
      });
      
      streamRef.current = stream;
      
      // Initialize VAD if enabled
      if (useVAD) {
        vadRef.current = new VoiceActivityDetector({
          energyThreshold: 0.02,
          silenceTimeout: 1500,
          speechTimeout: 300,
          onSpeechStart: () => {
            console.log('🎤 VAD: Speech started - beginning recording');
            setIsSpeaking(true);
            startActualRecording(stream);
          },
          onSpeechEnd: () => {
            console.log('🔇 VAD: Speech ended - stopping recording');
            setIsSpeaking(false);
            stopActualRecording();
          },
          onVolumeChange: (volume) => {
            setVolumeLevel(Math.min(volume * 100, 100));
          }
        });
        
        await vadRef.current.start(stream);
        setIsRecording(true);
        
        toast({
          title: '🎤 VAD Active',
          description: 'Start speaking to record automatically',
        });
      } else {
        // Manual recording without VAD
        startActualRecording(stream);
        setIsRecording(true);
        
        toast({
          title: '🎤 Recording',
          description: 'Speak in Twi...',
        });
      }
    } catch (error) {
      console.error('Failed to start recording:', error);
      toast({
        title: 'Error',
        description: 'Failed to access microphone',
        variant: 'destructive',
      });
    }
  };
  
  // Start actual recording (called by VAD or manually)
  const startActualRecording = (stream: MediaStream) => {
    if (mediaRecorderRef.current) {
      console.log('⚠️ Recording already in progress');
      return;
    }
    
    console.log('🔴 Starting actual recording...');
    mediaRecorderRef.current = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus'
    });
    
    const chunks: Blob[] = [];
    
    mediaRecorderRef.current.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data);
        console.log(`🎧 Audio chunk received: ${event.data.size} bytes, Total chunks: ${chunks.length}`);
        
        // Send audio chunk via WebSocket for real-time processing
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64 = reader.result?.toString().split(',')[1];
            if (base64) {
              console.log(`📡 Sending audio chunk: ${base64.length} bytes (base64)`);
              wsRef.current?.send(JSON.stringify({
                type: 'audio_chunk',
                audio: base64,
                session_id: sessionId
              }));
            }
          };
          reader.readAsDataURL(event.data);
        } else {
          console.warn('⚠️ WebSocket not ready, chunk not sent');
        }
      }
    };
    
    mediaRecorderRef.current.onstop = async () => {
      const audioBlob = new Blob(chunks, { type: 'audio/webm' });
      console.log(`🎬 Recording stopped. Total audio size: ${audioBlob.size} bytes`);
      
      // Send complete audio for final transcription
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result?.toString().split(',')[1];
        if (base64 && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          const message = {
            type: 'voice_message',
            audio_base64: base64,
            session_id: sessionId
          };
          console.log(`🚀 Sending complete voice message: ${base64.length} bytes (base64), Session: ${sessionId}`);
          setIsProcessing(true);
          wsRef.current.send(JSON.stringify(message));
        } else {
          console.error('❌ Cannot send voice message - WebSocket not ready or no base64 data');
        }
      };
      reader.readAsDataURL(audioBlob);
      
      // Reset for next recording if VAD is active
      if (useVAD) {
        mediaRecorderRef.current = null;
      }
    };
    
    // Start recording with 250ms chunks for real-time streaming
    mediaRecorderRef.current.start(250);
  };
  
  // Stop actual recording (called by VAD or manually)
  const stopActualRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
  };

  // Stop recording
  const stopRecording = () => {
    // Stop VAD if active
    if (vadRef.current) {
      vadRef.current.stop();
      vadRef.current = null;
    }
    
    // Stop recording
    stopActualRecording();
    
    // Stop media stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    setIsRecording(false);
    setIsSpeaking(false);
    setVolumeLevel(0);
  };

  // Play audio response
  const playAudioResponse = async (audioBase64: string) => {
    try {
      // Create a blob from base64 (gTTS returns MP3)
      const audioData = atob(audioBase64);
      const arrayBuffer = new ArrayBuffer(audioData.length);
      const view = new Uint8Array(arrayBuffer);
      
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i);
      }
      
      // Detect audio format (WAV from Akan TTS, MP3 from gTTS)
      // Check WAV header (RIFF)
      const isWav = view[0] === 0x52 && view[1] === 0x49 && view[2] === 0x46 && view[3] === 0x46;
      const mimeType = isWav ? 'audio/wav' : 'audio/mpeg';
      
      // Create blob with proper MIME type
      const audioBlob = new Blob([arrayBuffer], { type: mimeType });
      const audioUrl = URL.createObjectURL(audioBlob);
      console.log(`🎵 Audio format detected: ${mimeType}`);
      
      // Use HTML5 Audio API for MP3 playback
      const audio = new Audio(audioUrl);
      audio.volume = isMuted ? 0 : 1;
      
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = (e) => {
        console.error('Audio playback error:', e);
        // Fallback to AudioContext if available
        if (audioContextRef.current) {
          audioContextRef.current.decodeAudioData(arrayBuffer.slice(0))
            .then(audioBuffer => {
              const source = audioContextRef.current!.createBufferSource();
              source.buffer = audioBuffer;
              source.connect(audioContextRef.current!.destination);
              source.start();
            })
            .catch(err => console.error('AudioContext fallback failed:', err));
        }
      };
      
      await audio.play();
      console.log('🎵 Successfully playing TTS audio response');
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  };

  // Change TTS provider
  const changeTtsProvider = (newProvider: string) => {
    setTtsProvider(newProvider);
    
    // Send change to backend if connected
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && sessionId) {
      const message = {
        type: 'change_tts_provider',
        tts_provider: newProvider,
        session_id: sessionId
      };
      console.log('🔊 Changing TTS provider:', message);
      wsRef.current.send(JSON.stringify(message));
    }
    
    toast({
      title: '🔊 TTS Provider Changed',
      description: `Now using ${newProvider === 'akan' ? 'Akan MMS' : 'Google'} TTS`,
    });
  };

  // Send text message
  const sendTextMessage = () => {
    if (!textInput.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('⚠️ Cannot send text - input empty or WebSocket not ready');
      return;
    }
    
    const message = {
      type: 'text_message',
      text: textInput,
      session_id: sessionId
    };
    console.log('💬 Sending text message:', message);
    setIsProcessing(true);
    wsRef.current.send(JSON.stringify(message));
    
    setMessages(prev => [...prev, {
      id: `user-${Date.now()}`,
      role: 'user',
      content: textInput,
      timestamp: new Date()
    }]);
    
    setTextInput('');
  };

  return (
    <div className="flex h-screen bg-background">
      <DashboardSidebar />
      
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-card border-b border-border p-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2 text-foreground">
                <MessageSquare className="h-6 w-6 text-indigo-600" />
                Twi Real-time Conversation
              </h1>
              <p className="text-base text-gray-600 mt-1">
                Powered by Akan Whisper (92.9% accuracy) + Gemini AI
              </p>
            </div>
            <div className="flex items-center gap-4">
              <Badge variant={isConnected ? "default" : "destructive"}>
                {isConnected ? (
                  <>
                    <Wifi className="w-3 h-3 mr-1" />
                    Connected
                  </>
                ) : (
                  <>
                    <WifiOff className="w-3 h-3 mr-1" />
                    Disconnected
                  </>
                )}
              </Badge>
              
              {/* TTS Provider Selector */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">TTS:</span>
                <Select value={ttsProvider} onValueChange={changeTtsProvider}>
                  <SelectTrigger className="w-32 h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="akan">
                      <div>
                        <div className="font-medium">Akan MMS</div>
                        <div className="text-xs text-gray-600">Native Twi</div>
                      </div>
                    </SelectItem>
                    <SelectItem value="gtts">
                      <div>
                        <div className="font-medium">Google TTS</div>
                        <div className="text-xs text-gray-600">English accent</div>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Badge variant={useVAD ? "default" : "secondary"}>
                VAD: {useVAD ? 'ON' : 'OFF'}
              </Badge>
              <Button
                onClick={() => setUseVAD(!useVAD)}
                variant="outline"
                size="sm"
                title="Toggle Voice Activity Detection"
              >
                {useVAD ? 'Auto' : 'Manual'}
              </Button>
              <Button
                onClick={() => setIsMuted(!isMuted)}
                variant="outline"
                size="sm"
              >
                {isMuted ? (
                  <VolumeX className="h-4 w-4" />
                ) : (
                  <Volume2 className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex gap-3 max-w-[80%] ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                    message.role === 'user' ? 'bg-indigo-600 text-primary-foreground' : 
                    message.role === 'assistant' ? 'bg-blue-500 text-white' : 
                    'bg-muted text-gray-600'
                  }`}>
                    {message.role === 'user' ? <User className="w-5 h-5" /> : 
                     message.role === 'assistant' ? <Bot className="w-5 h-5" /> : 
                     <MessageSquare className="w-5 h-5" />}
                  </div>
                  <div>
                    <div className={`rounded-lg p-4 ${
                      message.role === 'user' ? 'bg-indigo-600 text-primary-foreground' : 
                      message.role === 'system' ? 'bg-muted' :
                      'bg-card border border-border shadow-sm'
                    }`}>
                      <p className="text-base leading-7">{message.content}</p>
                      {message.transcription?.confidence && (
                        <p className="text-sm mt-2 opacity-70">
                          {(message.transcription.confidence * 100).toFixed(1)}% confidence
                        </p>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-2 opacity-60">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Current transcription */}
            {currentTranscription && (
              <div className="flex justify-end">
                <div className="flex gap-3 max-w-[80%] flex-row-reverse">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/50 flex items-center justify-center">
                    <User className="w-4 h-4 text-white" />
                  </div>
                  <div className="rounded-lg p-4 bg-primary/10 border border-primary/20">
                    <p className="text-base italic text-foreground opacity-80 leading-7">{currentTranscription}...</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Processing indicator */}
            {isProcessing && (
              <div className="flex justify-start">
                <div className="flex gap-3 max-w-[80%]">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="rounded-lg p-3 bg-card border border-border">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Controls */}
        <div className="bg-card border-t border-border p-6">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              {/* Text input */}
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendTextMessage()}
                placeholder="Type in Twi or English..."
                className="flex-1 px-5 py-3 text-base bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent placeholder:text-gray-600"
                disabled={!isConnected || isProcessing}
              />
              
              {/* Send button */}
              <Button
                onClick={sendTextMessage}
                disabled={!isConnected || !textInput.trim() || isProcessing}
              >
                <Send className="w-4 h-4" />
              </Button>
              
              {/* Voice button */}
              <Button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={!isConnected || isProcessing}
                variant={isRecording ? "destructive" : "default"}
                size="lg"
                className="rounded-full w-14 h-14 p-0"
              >
                {isRecording ? (
                  <MicOff className="w-6 h-6" />
                ) : (
                  <Mic className="w-6 h-6" />
                )}
              </Button>
            </div>
            
            {isRecording && (
              <div className="mt-3 space-y-2">
                {/* VAD Status */}
                {useVAD && (
                  <div className="text-center">
                    <Badge variant={isSpeaking ? "default" : "secondary"} className="mb-2">
                      {isSpeaking ? '🎤 Speaking Detected' : '⏸️ Listening...'}
                    </Badge>
                  </div>
                )}
                
                {/* Volume Level */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span>Volume</span>
                    <span>{Math.round(volumeLevel)}%</span>
                  </div>
                  <div className="h-3 bg-muted rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-100 ${
                        isSpeaking ? 'bg-green-500' : 
                        volumeLevel > 50 ? 'bg-yellow-500' : 
                        'bg-blue-500'
                      }`}
                      style={{ width: `${volumeLevel}%` }}
                    />
                  </div>
                </div>
                
                <p className="text-sm text-center text-gray-600 mt-2 font-semibold">
                  {useVAD ? 
                    'VAD Active - Speak naturally, recording will start automatically' : 
                    'Recording... Click to stop'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}