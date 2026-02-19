import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Mic, MicOff, Loader2, Volume2, AlertCircle } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


const API_URL = API_BASE_URL;

export default function AudioTest() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [language, setLanguage] = useState('aka');
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [error, setError] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [status, setStatus] = useState('Ready to chat...');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

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
    };
  }, []);

  const setupRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000
        } 
      });
      
      // Try to use WAV if available, fallback to webm
      let mimeType = 'audio/webm';
      if (MediaRecorder.isTypeSupported('audio/wav')) {
        mimeType = 'audio/wav';
      } else if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';
      }
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      
      // Setup audio level monitoring
      if (audioContextRef.current) {
        const source = audioContextRef.current.createMediaStreamSource(stream);
        const analyser = audioContextRef.current.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyserRef.current = analyser;
      }
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = [];
        await sendAudioToServer(audioBlob);
      };
      
      return true;
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setError('Cannot access microphone. Please check permissions.');
      return false;
    }
  };

  const updateAudioLevel = () => {
    if (analyserRef.current && isRecording) {
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel((average / 255) * 100);
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  };

  const startRecording = async () => {
    setError('');
    if (!mediaRecorderRef.current) {
      const success = await setupRecording();
      if (!success) return;
    }
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
      audioChunksRef.current = [];
      mediaRecorderRef.current.start();
      setIsRecording(true);
      setStatus('Listening...');
      updateAudioLevel();
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setStatus('Processing...');
      setAudioLevel(0);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    }
  };

  const convertWebMToWAV = async (webmBlob: Blob): Promise<Blob> => {
    // Create an audio context to decode the WebM
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const arrayBuffer = await webmBlob.arrayBuffer();
    
    try {
      // Decode the audio data
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      
      // Convert to WAV format
      const length = audioBuffer.length * audioBuffer.numberOfChannels * 2;
      const buffer = new ArrayBuffer(44 + length);
      const view = new DataView(buffer);
      const channels: Float32Array[] = [];
      let sample;
      let offset = 0;
      let pos = 0;
      
      // Write WAV header
      const setUint16 = (data: number) => {
        view.setUint16(pos, data, true);
        pos += 2;
      };
      const setUint32 = (data: number) => {
        view.setUint32(pos, data, true);
        pos += 4;
      };
      
      // RIFF identifier
      setUint32(0x46464952); // "RIFF"
      setUint32(36 + length); // file length - 8
      setUint32(0x45564157); // "WAVE"
      
      // fmt sub-chunk
      setUint32(0x20746d66); // "fmt "
      setUint32(16); // size
      setUint16(1); // PCM
      setUint16(audioBuffer.numberOfChannels);
      setUint32(audioBuffer.sampleRate);
      setUint32(audioBuffer.sampleRate * 2 * audioBuffer.numberOfChannels); // byte rate
      setUint16(audioBuffer.numberOfChannels * 2); // block align
      setUint16(16); // bits per sample
      
      // data sub-chunk
      setUint32(0x61746164); // "data"
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
      // If conversion fails, return original blob
      return webmBlob;
    } finally {
      audioContext.close();
    }
  };

  const sendAudioToServer = async (audioBlob: Blob) => {
    setIsProcessing(true);
    setError('');
    
    try {
      // Convert WebM to WAV
      const wavBlob = await convertWebMToWAV(audioBlob);
      
      const formData = new FormData();
      formData.append('audio_file', wavBlob, 'recording.wav');
      
      const response = await fetch(`${API_URL}/voice/mms/chat?lang_code=${language}`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        // Get response headers
        const transcriptHeader = response.headers.get('X-Transcript');
        const responseHeader = response.headers.get('X-Response');
        
        if (transcriptHeader) {
          setTranscript(decodeURIComponent(transcriptHeader));
        }
        if (responseHeader) {
          setResponse(decodeURIComponent(responseHeader));
        }
        
        // Play audio response
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        if (audioPlayerRef.current) {
          audioPlayerRef.current.src = audioUrl;
          audioPlayerRef.current.play();
        } else {
          const audio = new Audio(audioUrl);
          audioPlayerRef.current = audio;
          audio.play();
        }
        
        setStatus('Ready to chat...');
      } else {
        const errorData = await response.text();
        setError(`Error: ${errorData}`);
        setStatus('Error occurred');
      }
    } catch (error) {
      console.error('Error:', error);
      setError('Failed to connect to server. Make sure the backend is running.');
      setStatus('Connection error');
    } finally {
      setIsProcessing(false);
    }
  };

  const languages = [
    { value: 'aka', label: 'Akan/Twi 🇬🇭', greeting: 'Akwaaba! Mesrɛ wo, kasa.' },
    { value: 'ewe', label: 'Ewe 🇹🇬', greeting: 'Woezɔ! Miaɖe gbea.' },
    { value: 'yor', label: 'Yoruba 🇳🇬', greeting: 'Ẹ káàbọ̀! Jọwọ sọ̀rọ̀.' },
    { value: 'hau', label: 'Hausa 🇳🇬', greeting: 'Barka da zuwa! Don Allah yi magana.' },
    { value: 'eng', label: 'English 🇬🇧', greeting: 'Hello! How can I help you today?' }
  ];

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-6 w-6" />
            Meta MMS + Gemini Voice Test
          </CardTitle>
          <CardDescription>
            Test the Meta MMS speech recognition and synthesis with Gemini AI responses
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Language Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Language</label>
            <Select value={language} onValueChange={setLanguage}>
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

          {/* Recording Button and Status */}
          <div className="flex flex-col items-center space-y-4">
            <Button
              size="lg"
              variant={isRecording ? "destructive" : "default"}
              className="w-48 h-48 rounded-full"
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <Loader2 className="h-16 w-16 animate-spin" />
              ) : isRecording ? (
                <MicOff className="h-16 w-16" />
              ) : (
                <Mic className="h-16 w-16" />
              )}
            </Button>
            
            {/* Audio Level Indicator */}
            {isRecording && (
              <div className="w-full max-w-xs space-y-2">
                <div className="flex items-center gap-2">
                  <Volume2 className="h-4 w-4" />
                  <Progress value={audioLevel} className="flex-1" />
                </div>
                <p className="text-sm text-center text-gray-600">Listening...</p>
              </div>
            )}
            
            <p className="text-sm text-gray-600">
              {isRecording ? 'Release to stop' : 'Hold to talk'}
            </p>
          </div>

          {/* Status */}
          <div className="text-center">
            <p className="text-sm font-medium">{status}</p>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Conversation Display */}
          {(transcript || response) && (
            <Card className="bg-muted/50">
              <CardContent className="pt-6 space-y-4">
                {transcript && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-gray-600">You said:</p>
                    <p className="text-lg">{transcript}</p>
                  </div>
                )}
                {response && (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-gray-600">Assistant:</p>
                    <p className="text-lg">{response}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Instructions */}
          <Card className="bg-muted/30">
            <CardContent className="pt-6">
              <h3 className="font-medium mb-2">How to use:</h3>
              <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                <li>Select your preferred language</li>
                <li>Hold the microphone button and speak</li>
                <li>Release to send your message</li>
                <li>Wait for the AI response</li>
                <li>The response will be spoken back to you</li>
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