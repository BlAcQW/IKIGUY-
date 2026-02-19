import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Mic, MicOff, Loader2, Volume2, AlertCircle, Play, Square } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


const API_URL = API_BASE_URL;
const WS_URL = API_URL.replace('https://', 'wss://').replace('http://', 'ws://');

export default function ContinuousChat() {
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [language, setLanguage] = useState('eng');
  const [status, setStatus] = useState('Click Start to begin conversation');
  const [conversation, setConversation] = useState<Array<{role: string, text: string}>>([]);
  const [error, setError] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [isAssistantSpeaking, setIsAssistantSpeaking] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const silenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const conversationEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize audio context
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
    };
  }, []);

  // Auto-scroll to bottom when conversation updates
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  const setupRecording = async () => {
    try {
      console.log('🎤 Setting up recording...');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000
        } 
      });
      
      console.log('🎤 Got media stream, creating MediaRecorder...');
      const mediaRecorder = new MediaRecorder(stream, { 
        mimeType: 'audio/webm;codecs=opus' 
      });
      mediaRecorderRef.current = mediaRecorder;
      console.log('📹 MediaRecorder created, state:', mediaRecorder.state);
      
      // Setup audio level monitoring
      if (audioContextRef.current) {
        console.log('🎚️ Setting up audio level monitoring...');
        const source = audioContextRef.current.createMediaStreamSource(stream);
        const analyser = audioContextRef.current.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyserRef.current = analyser;
        console.log('✅ Audio analyser connected');
      } else {
        console.warn('⚠️ No audio context for level monitoring');
      }
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          console.log('🎙️ Audio data available:', event.data.size, 'bytes');
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        console.log('🛑 Recording stopped, chunks:', audioChunksRef.current.length);
        if (audioChunksRef.current.length > 0) {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          console.log('📦 Created audio blob:', audioBlob.size, 'bytes');
          audioChunksRef.current = [];
          await sendAudioToServer(audioBlob);
        }
      };
      
      return true;
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setError('Cannot access microphone. Please check permissions.');
      return false;
    }
  };

  const updateAudioLevel = () => {
    if (analyserRef.current) {
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel((average / 255) * 100);
      
      // Detect silence (low audio level for extended period)
      if (average < 10) {
        if (!silenceTimeoutRef.current) {
          console.log('🔇 Silence detected, starting timeout...');
          silenceTimeoutRef.current = setTimeout(() => {
            console.log('⏰ Silence timeout triggered, stopping recording...');
            // Stop current recording and send audio
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
              mediaRecorderRef.current.stop();
              setTimeout(() => {
                // Start new recording after a brief pause
                if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
                  console.log('🎤 Starting new recording...');
                  audioChunksRef.current = [];
                  mediaRecorderRef.current.start();
                }
              }, 100);
            }
            silenceTimeoutRef.current = null;
          }, 1500); // 1.5 seconds of silence triggers send
        }
      } else {
        // Clear silence timeout if there's sound
        if (silenceTimeoutRef.current) {
          console.log('🔊 Sound detected, clearing silence timeout');
          clearTimeout(silenceTimeoutRef.current);
          silenceTimeoutRef.current = null;
        }
      }
      
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  };

  const convertWebMToWAV = async (webmBlob: Blob): Promise<Blob> => {
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const arrayBuffer = await webmBlob.arrayBuffer();
    
    try {
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      const length = audioBuffer.length * audioBuffer.numberOfChannels * 2;
      const buffer = new ArrayBuffer(44 + length);
      const view = new DataView(buffer);
      const channels: Float32Array[] = [];
      let sample;
      let offset = 0;
      let pos = 0;
      
      const setUint16 = (data: number) => {
        view.setUint16(pos, data, true);
        pos += 2;
      };
      const setUint32 = (data: number) => {
        view.setUint32(pos, data, true);
        pos += 4;
      };
      
      // RIFF identifier
      setUint32(0x46464952);
      setUint32(36 + length);
      setUint32(0x45564157);
      
      // fmt sub-chunk
      setUint32(0x20746d66);
      setUint32(16);
      setUint16(1);
      setUint16(audioBuffer.numberOfChannels);
      setUint32(audioBuffer.sampleRate);
      setUint32(audioBuffer.sampleRate * 2 * audioBuffer.numberOfChannels);
      setUint16(audioBuffer.numberOfChannels * 2);
      setUint16(16);
      
      // data sub-chunk
      setUint32(0x61746164);
      setUint32(length);
      
      // Write interleaved PCM samples
      for (let i = 0; i < audioBuffer.numberOfChannels; i++) {
        channels.push(audioBuffer.getChannelData(i));
      }
      
      offset = 44;
      for (let i = 0; i < audioBuffer.length; i++) {
        for (let channel = 0; channel < audioBuffer.numberOfChannels; channel++) {
          sample = Math.max(-1, Math.min(1, channels[channel][i]));
          view.setInt16(offset, sample * 0x7FFF, true);
          offset += 2;
        }
      }
      
      return new Blob([buffer], { type: 'audio/wav' });
    } catch (error) {
      console.error('Error converting to WAV:', error);
      return webmBlob;
    } finally {
      audioContext.close();
    }
  };

  const sendAudioToServer = async (audioBlob: Blob) => {
    console.log('📤 Sending audio to server, blob size:', audioBlob.size);
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.warn('⚠️ WebSocket not ready, state:', wsRef.current?.readyState);
      return;
    }
    
    try {
      // Convert to WAV
      console.log('🔄 Converting WebM to WAV...');
      const wavBlob = await convertWebMToWAV(audioBlob);
      console.log('✅ WAV conversion complete, size:', wavBlob.size);
      
      // Convert to base64
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result?.toString().split(',')[1];
        if (base64 && wsRef.current) {
          console.log('📡 Sending audio data to WebSocket, base64 length:', base64.length);
          wsRef.current.send(JSON.stringify({
            type: 'audio',
            data: base64
          }));
        }
      };
      reader.readAsDataURL(wavBlob);
    } catch (error) {
      console.error('❌ Error sending audio:', error);
    }
  };

  const connectWebSocket = () => {
    const wsUrl = `${WS_URL}/voice/mms/conversation?lang_code=${language}`;
    console.log('🔌 Connecting to WebSocket:', wsUrl);
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('✅ WebSocket connected successfully');
      setIsConnected(true);
      setError('');
      setStatus('Connected. Initializing...');
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('📨 WebSocket message received:', message.type, message);
      
      switch (message.type) {
        case 'ready':
          setStatus(message.message);
          setIsProcessing(false);
          setIsAssistantSpeaking(false);
          setCurrentTranscript('');
          // Start recording when ready
          if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
            console.log('🎙️ Starting recording after ready signal');
            audioChunksRef.current = [];
            mediaRecorderRef.current.start();
            updateAudioLevel();
          } else {
            console.log('⚠️ MediaRecorder not ready or already recording:', mediaRecorderRef.current?.state);
          }
          break;
          
        case 'status':
          setStatus(message.message);
          setIsProcessing(true);
          setCurrentTranscript('');
          break;
          
        case 'transcript':
          setCurrentTranscript(message.text);
          setConversation(prev => [...prev, { role: 'user', text: message.text }]);
          break;
          
        case 'response':
          setConversation(prev => [...prev, { role: 'assistant', text: message.text }]);
          setIsAssistantSpeaking(true);
          break;
          
        case 'audio_response':
          // Play audio response
          const audioData = atob(message.data);
          const audioArray = new Uint8Array(audioData.length);
          for (let i = 0; i < audioData.length; i++) {
            audioArray[i] = audioData.charCodeAt(i);
          }
          const audioBlob = new Blob([audioArray], { type: 'audio/wav' });
          const audioUrl = URL.createObjectURL(audioBlob);
          
          if (audioPlayerRef.current) {
            audioPlayerRef.current.src = audioUrl;
            audioPlayerRef.current.onended = () => {
              setIsAssistantSpeaking(false);
            };
            audioPlayerRef.current.play();
          } else {
            const audio = new Audio(audioUrl);
            audioPlayerRef.current = audio;
            audio.onended = () => {
              setIsAssistantSpeaking(false);
            };
            audio.play();
          }
          break;
          
        case 'error':
          setError(message.message);
          setIsProcessing(false);
          setIsAssistantSpeaking(false);
          break;
      }
    };
    
    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setError('Connection error occurred');
      setIsConnected(false);
    };
    
    ws.onclose = (event) => {
      console.log('🔌 WebSocket closed:', event.code, event.reason);
      setIsConnected(false);
      setStatus('Disconnected');
      setIsListening(false);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
    
    wsRef.current = ws;
  };

  const startConversation = async () => {
    console.log('🚀 Starting conversation...');
    setError('');
    setIsListening(true);
    
    // Setup recording first
    const success = await setupRecording();
    if (!success) {
      console.error('❌ Failed to setup recording');
      setIsListening(false);
      return;
    }
    
    console.log('✅ Recording setup complete');
    
    // Connect WebSocket
    connectWebSocket();
  };

  const stopConversation = () => {
    console.log('🛑 Stopping conversation...');
    // Stop recording
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      console.log('🛑 Stopping active recording...');
      mediaRecorderRef.current.stop();
    }
    
    // Send stop message
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('📤 Sending stop message to server');
      wsRef.current.send(JSON.stringify({ type: 'stop' }));
      wsRef.current.close();
    }
    
    setIsListening(false);
    setIsConnected(false);
    setStatus('Conversation ended');
    setCurrentTranscript('');
    setIsAssistantSpeaking(false);
    
    // Stop audio level monitoring
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    // Clear timeouts
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
      silenceTimeoutRef.current = null;
    }
  };

  const languages = [
    { value: 'aka', label: 'Akan/Twi 🇬🇭', greeting: 'Akwaaba! Mesrɛ wo, kasa.' },
    { value: 'ewe', label: 'Ewe 🇹🇬', greeting: 'Woezɔ! Miaɖe gbea.' },
    { value: 'yor', label: 'Yoruba 🇳🇬', greeting: 'Ẹ káàbọ̀! Jọwọ sọ̀rọ̀.' },
    { value: 'hau', label: 'Hausa 🇳🇬', greeting: 'Barka da zuwa! Don Allah yi magana.' },
    { value: 'eng', label: 'English 🇬🇧', greeting: 'Hello! Start speaking and I\'ll respond continuously.' }
  ];

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-6 w-6" />
            Continuous Voice Conversation
          </CardTitle>
          <CardDescription>
            Have a natural, continuous conversation with AI. Speak naturally and the assistant will respond.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Language Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Language</label>
            <Select value={language} onValueChange={setLanguage} disabled={isConnected}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {languages.map((lang) => (
                  <SelectItem key={lang.value} value={lang.value}>
                    {lang.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-sm text-gray-600">
              {languages.find(l => l.value === language)?.greeting}
            </p>
          </div>

          {/* Control Buttons */}
          <div className="flex justify-center gap-4">
            {!isListening ? (
              <Button
                size="lg"
                onClick={startConversation}
                disabled={isProcessing}
                className="flex items-center gap-2"
              >
                <Play className="h-5 w-5" />
                Start Conversation
              </Button>
            ) : (
              <Button
                size="lg"
                variant="destructive"
                onClick={stopConversation}
                className="flex items-center gap-2"
              >
                <Square className="h-5 w-5" />
                Stop Conversation
              </Button>
            )}
          </div>

          {/* Status Display */}
          <div className="text-center space-y-2">
            <p className="text-sm font-medium">{status}</p>
            {isProcessing && (
              <div className="flex justify-center">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            )}
          </div>

          {/* Current Transcript Display */}
          {(currentTranscript || isAssistantSpeaking) && (
            <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
              <CardContent className="pt-4">
                <div className="flex items-start gap-2">
                  <div className="mt-1">
                    {isAssistantSpeaking ? (
                      <Volume2 className="h-5 w-5 text-blue-600 animate-pulse" />
                    ) : (
                      <Mic className="h-5 w-5 text-blue-600" />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-1">
                      {isAssistantSpeaking ? 'Assistant is speaking...' : 'You said:'}
                    </p>
                    {currentTranscript && (
                      <p className="text-base text-gray-800 dark:text-gray-200">
                        {currentTranscript}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Audio Level Indicator */}
          {isListening && !isProcessing && (
            <div className="w-full space-y-2">
              <div className="flex items-center gap-2">
                <Volume2 className="h-4 w-4" />
                <Progress value={audioLevel} className="flex-1" />
              </div>
              <p className="text-sm text-center text-gray-600">
                Listening... Speak naturally, pause when done
              </p>
            </div>
          )}

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Conversation Display */}
          {conversation.length > 0 && (
            <Card className="bg-muted/50">
              <CardContent className="pt-6">
                <div className="max-h-96 overflow-y-auto space-y-4 pr-2">
                  {conversation.map((msg, idx) => (
                    <div 
                      key={idx} 
                      className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-2' : ''}`}>
                        <div className={`rounded-lg p-3 ${
                          msg.role === 'user' 
                            ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100' 
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
                        }`}>
                          <p className="text-xs font-medium mb-1 opacity-70">
                            {msg.role === 'user' ? 'You' : 'Assistant'}
                          </p>
                          <p className="text-sm">{msg.text}</p>
                        </div>
                      </div>
                      {msg.role === 'user' ? (
                        <Mic className="h-6 w-6 text-blue-500 mt-2 order-1" />
                      ) : (
                        <Volume2 className="h-6 w-6 text-gray-500 mt-2" />
                      )}
                    </div>
                  ))}
                  <div ref={conversationEndRef} />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Instructions */}
          <Card className="bg-muted/30">
            <CardContent className="pt-6">
              <h3 className="font-medium mb-2">How it works:</h3>
              <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                <li>Select your preferred language</li>
                <li>Click "Start Conversation" to begin</li>
                <li>Speak naturally - the AI listens continuously</li>
                <li>Pause briefly when you finish speaking</li>
                <li>The AI will respond and then listen for your reply</li>
                <li>Click "Stop Conversation" when done</li>
              </ol>
            </CardContent>
          </Card>

          {/* Hidden Audio Player */}
          <audio ref={audioPlayerRef} className="hidden" />
        </CardContent>
      </Card>
    </div>
  );
}