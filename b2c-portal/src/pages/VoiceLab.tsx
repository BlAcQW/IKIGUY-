import React, { useState, useRef, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';
import { blobToBase64, downloadAudioBase64 } from '@/lib/audio-utils';

import {
  Mic,
  MicOff,
  Play,
  Pause,
  Download,
  Upload,
  Volume2,
  Wand2,
  Languages,
  Clock,
  Activity,
  FileAudio,
  Loader2,
  StopCircle,
  RefreshCw
} from 'lucide-react';

// API Configuration - Use core backend API
const API_URL = API_BASE_URL;

interface Voice {
  voice_id: string;
  name: string;
  language: string;
  dialect: string;
  gender: string;
  description: string;
}

export default function VoiceLab() {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('transcribe');

  // Use the voice recorder hook for ASR
  const {
    isRecording,
    isPlaying: isPlayingRecording,
    audioBlob,
    startRecording,
    stopRecording,
    playAudio: playRecordedAudio,
    stopPlayback: stopRecordedPlayback,
    clearRecording
  } = useVoiceRecorder();

  // ASR State
  const [transcription, setTranscription] = useState('');
  const [enhancedTranscription, setEnhancedTranscription] = useState('');
  const [isTranscribing, setIsTranscribing] = useState(false);
  
  // TTS State
  const [ttsText, setTtsText] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('asante_male_1');
  const [speechSpeed, setSpeechSpeed] = useState([1.0]);
  const [pitch, setPitch] = useState([0]);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [synthesizedAudio, setSynthesizedAudio] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  // Voice Cloning State
  const [referenceAudio, setReferenceAudio] = useState<File | null>(null);
  const [cloneText, setCloneText] = useState('');
  const [isCloning, setIsCloning] = useState(false);
  
  // Available Voices
  const [voices, setVoices] = useState<Voice[]>([]);
  const [selectedDialect, setSelectedDialect] = useState('asante');
  
  // Fetch available voices on component mount
  useEffect(() => {
    fetchVoices();
  }, []);
  
  const fetchVoices = async () => {
    try {
      const response = await fetch(`${API_URL}/api/voice-lab/voices`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      if (response.ok) {
        const data = await response.json();
        setVoices(data);
      }
    } catch (error) {
      console.error('Failed to fetch voices:', error);
    }
  };
  
  // Enhanced recording handlers with toast notifications
  const handleStartRecording = async () => {
    try {
      await startRecording();
      toast({
        title: "Recording Started",
        description: "Speak clearly in Twi/Akan",
      });
    } catch (error) {
      console.error('[VoiceLab] Recording error:', error);
      toast({
        title: "Recording Failed",
        description: error instanceof Error ? error.message : "Please grant microphone permissions",
        variant: "destructive"
      });
    }
  };

  const handleStopRecording = () => {
    stopRecording();
    toast({
      title: "Recording Stopped",
      description: "Ready for transcription",
    });
  };
  
  // Transcribe audio
  const transcribeAudio = async () => {
    if (!audioBlob) {
      toast({
        title: "No Audio",
        description: "Please record audio first",
        variant: "destructive"
      });
      return;
    }
    
    setIsTranscribing(true);
    try {
      const audioBase64 = await blobToBase64(audioBlob);

      const response = await fetch(`${API_URL}/api/voice-lab/transcribe`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio_base64: audioBase64,
          language: 'tw',
          dialect: selectedDialect,
          enhance_text: true
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setTranscription(data.text);
        setEnhancedTranscription(data.enhanced_text || data.text);
        toast({
          title: "Transcription Complete",
          description: `Confidence: ${(data.confidence * 100).toFixed(1)}%`,
        });
      } else {
        throw new Error('Transcription failed');
      }
    } catch (error) {
      toast({
        title: "Transcription Failed",
        description: "Please try again",
        variant: "destructive"
      });
    } finally {
      setIsTranscribing(false);
    }
  };
  
  // Synthesize speech
  const synthesizeSpeech = async () => {
    if (!ttsText) {
      toast({
        title: "No Text",
        description: "Please enter text to synthesize",
        variant: "destructive"
      });
      return;
    }
    
    setIsSynthesizing(true);
    try {
      const response = await fetch(`${API_URL}/api/voice-lab/synthesize`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: ttsText,
          voice_id: selectedVoice,
          speed: speechSpeed[0],
          pitch: pitch[0],
          enhance_text: true
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setSynthesizedAudio(data.audio_base64);
        
        // Create audio element
        const audioData = `data:audio/wav;base64,${data.audio_base64}`;
        if (audioRef.current) {
          audioRef.current.src = audioData;
        }
        
        toast({
          title: "Synthesis Complete",
          description: `Voice: ${voices.find(v => v.voice_id === selectedVoice)?.name || selectedVoice}`,
        });
      } else {
        throw new Error('Synthesis failed');
      }
    } catch (error) {
      toast({
        title: "Synthesis Failed",
        description: "Please try again",
        variant: "destructive"
      });
    } finally {
      setIsSynthesizing(false);
    }
  };
  
  // Play/Pause audio
  const togglePlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };
  
  // Download audio
  const downloadAudio = () => {
    if (synthesizedAudio) {
      downloadAudioBase64(synthesizedAudio, 'twi_speech.wav');
      toast({
        title: "Download Started",
        description: "Audio file is being downloaded",
      });
    }
  };
  
  // Clone voice
  const cloneVoice = async () => {
    if (!referenceAudio || !cloneText) {
      toast({
        title: "Missing Input",
        description: "Please provide reference audio and text",
        variant: "destructive"
      });
      return;
    }
    
    setIsCloning(true);
    try {
      const referenceBase64 = await blobToBase64(referenceAudio);

      const response = await fetch(`${API_URL}/api/voice-lab/clone-voice`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reference_audio_base64: referenceBase64,
          text: cloneText,
          voice_name: 'custom'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setSynthesizedAudio(data.audio_base64);
        
        const audioData = `data:audio/wav;base64,${data.audio_base64}`;
        if (audioRef.current) {
          audioRef.current.src = audioData;
        }
        
        toast({
          title: "Voice Cloning Complete",
          description: "Audio generated with cloned voice",
        });
      } else {
        throw new Error('Voice cloning failed');
      }
    } catch (error) {
      toast({
        title: "Voice Cloning Failed",
        description: "Please try again with different audio",
        variant: "destructive"
      });
    } finally {
      setIsCloning(false);
    }
  };
  
  // Handle file upload for voice cloning
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setReferenceAudio(file);
      toast({
        title: "File Uploaded",
        description: `${file.name} ready for voice cloning`,
      });
    }
  };
  
  return (
    <div className="flex min-h-screen">
      <DashboardSidebar />
      <div className="flex-1 space-y-8 p-8">
        <div>
          <h2 className="text-3xl text-heading tracking-tight">Voice Lab</h2>
          <p className="text-gray-600 text-body">
            Advanced ASR and TTS for Twi/Akan languages
          </p>
        </div>
        
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="transcribe">
              <Mic className="mr-2 h-4 w-4" />
              Transcribe
            </TabsTrigger>
            <TabsTrigger value="synthesize">
              <Volume2 className="mr-2 h-4 w-4" />
              Synthesize
            </TabsTrigger>
            <TabsTrigger value="clone">
              <Wand2 className="mr-2 h-4 w-4" />
              Voice Clone
            </TabsTrigger>
          </TabsList>
          
          {/* Transcription Tab */}
          <TabsContent value="transcribe" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Speech to Text</CardTitle>
                <CardDescription>
                  Record or upload audio in Twi/Akan for transcription
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <Select value={selectedDialect} onValueChange={setSelectedDialect}>
                    <SelectTrigger className="w-[200px]">
                      <SelectValue placeholder="Select dialect" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="asante">Asante Twi</SelectItem>
                      <SelectItem value="akuapem">Akuapem Twi</SelectItem>
                      <SelectItem value="fante">Fante</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Button
                    size="lg"
                    variant={isRecording ? "destructive" : "default"}
                    onClick={isRecording ? handleStopRecording : handleStartRecording}
                    disabled={isTranscribing}
                  >
                    {isRecording ? (
                      <>
                        <StopCircle className="mr-2 h-5 w-5" />
                        Stop Recording
                      </>
                    ) : (
                      <>
                        <Mic className="mr-2 h-5 w-5" />
                        Start Recording
                      </>
                    )}
                  </Button>
                  
                  <Button
                    size="lg"
                    onClick={transcribeAudio}
                    disabled={!audioBlob || isTranscribing}
                  >
                    {isTranscribing ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Transcribing...
                      </>
                    ) : (
                      <>
                        <Languages className="mr-2 h-5 w-5" />
                        Transcribe
                      </>
                    )}
                  </Button>
                </div>
                
                {audioBlob && (
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">
                      <FileAudio className="mr-1 h-3 w-3" />
                      Audio Ready
                    </Badge>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={isPlayingRecording ? stopRecordedPlayback : playRecordedAudio}
                    >
                      {isPlayingRecording ? (
                        <>
                          <Pause className="mr-1 h-3 w-3" />
                          Pause
                        </>
                      ) : (
                        <>
                          <Play className="mr-1 h-3 w-3" />
                          Play
                        </>
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={clearRecording}
                      title="Clear recording"
                    >
                      <RefreshCw className="h-3 w-3" />
                    </Button>
                  </div>
                )}
                
                {transcription && (
                  <div className="space-y-4">
                    <div>
                      <Label>Original Transcription</Label>
                      <div className="mt-2 p-4 bg-secondary rounded-lg">
                        <p className="text-sm">{transcription}</p>
                      </div>
                    </div>
                    
                    {enhancedTranscription && (
                      <div>
                        <Label>Enhanced Transcription</Label>
                        <div className="mt-2 p-4 bg-secondary rounded-lg">
                          <p className="text-sm">{enhancedTranscription}</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Synthesis Tab */}
          <TabsContent value="synthesize" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Text to Speech</CardTitle>
                <CardDescription>
                  Convert Twi/Akan text to natural speech
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Text to Synthesize</Label>
                  <Textarea
                    placeholder="Enter Twi/Akan text here..."
                    value={ttsText}
                    onChange={(e) => setTtsText(e.target.value)}
                    className="mt-2 min-h-[100px]"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Voice</Label>
                    <Select value={selectedVoice} onValueChange={setSelectedVoice}>
                      <SelectTrigger className="mt-2">
                        <SelectValue placeholder="Select voice" />
                      </SelectTrigger>
                      <SelectContent>
                        {voices.map((voice) => (
                          <SelectItem key={voice.voice_id} value={voice.voice_id}>
                            {voice.name} ({voice.gender})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label>Speed: {speechSpeed[0]}x</Label>
                    <Slider
                      value={speechSpeed}
                      onValueChange={setSpeechSpeed}
                      min={0.5}
                      max={2}
                      step={0.1}
                      className="mt-2"
                    />
                  </div>
                  
                  <div>
                    <Label>Pitch: {pitch[0] > 0 ? `+${pitch[0]}` : pitch[0]}</Label>
                    <Slider
                      value={pitch}
                      onValueChange={setPitch}
                      min={-5}
                      max={5}
                      step={1}
                      className="mt-2"
                    />
                  </div>
                </div>
                
                <div className="flex items-center gap-4">
                  <Button
                    size="lg"
                    onClick={synthesizeSpeech}
                    disabled={!ttsText || isSynthesizing}
                  >
                    {isSynthesizing ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Synthesizing...
                      </>
                    ) : (
                      <>
                        <Volume2 className="mr-2 h-5 w-5" />
                        Synthesize
                      </>
                    )}
                  </Button>
                  
                  {synthesizedAudio && (
                    <>
                      <Button
                        size="lg"
                        variant="secondary"
                        onClick={togglePlayback}
                      >
                        {isPlaying ? (
                          <>
                            <Pause className="mr-2 h-5 w-5" />
                            Pause
                          </>
                        ) : (
                          <>
                            <Play className="mr-2 h-5 w-5" />
                            Play
                          </>
                        )}
                      </Button>
                      
                      <Button
                        size="lg"
                        variant="outline"
                        onClick={downloadAudio}
                      >
                        <Download className="mr-2 h-5 w-5" />
                        Download
                      </Button>
                    </>
                  )}
                </div>
                
                <audio
                  ref={audioRef}
                  onEnded={() => setIsPlaying(false)}
                  className="hidden"
                />
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* Voice Cloning Tab */}
          <TabsContent value="clone" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Voice Cloning</CardTitle>
                <CardDescription>
                  Clone any voice with just a few seconds of reference audio
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Reference Audio (3-30 seconds)</Label>
                  <div className="mt-2">
                    <input
                      type="file"
                      accept="audio/*"
                      onChange={handleFileUpload}
                      className="hidden"
                      id="audio-upload"
                    />
                    <label htmlFor="audio-upload">
                      <Button variant="outline" asChild>
                        <span>
                          <Upload className="mr-2 h-4 w-4" />
                          Upload Reference Audio
                        </span>
                      </Button>
                    </label>
                    {referenceAudio && (
                      <Badge variant="secondary" className="ml-2">
                        {referenceAudio.name}
                      </Badge>
                    )}
                  </div>
                </div>
                
                <div>
                  <Label>Text to Synthesize</Label>
                  <Textarea
                    placeholder="Enter text for the cloned voice to speak..."
                    value={cloneText}
                    onChange={(e) => setCloneText(e.target.value)}
                    className="mt-2 min-h-[100px]"
                  />
                </div>
                
                <div className="flex items-center gap-4">
                  <Button
                    size="lg"
                    onClick={cloneVoice}
                    disabled={!referenceAudio || !cloneText || isCloning}
                  >
                    {isCloning ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Cloning Voice...
                      </>
                    ) : (
                      <>
                        <Wand2 className="mr-2 h-5 w-5" />
                        Clone Voice
                      </>
                    )}
                  </Button>
                  
                  {synthesizedAudio && (
                    <>
                      <Button
                        size="lg"
                        variant="secondary"
                        onClick={togglePlayback}
                      >
                        {isPlaying ? (
                          <>
                            <Pause className="mr-2 h-5 w-5" />
                            Pause
                          </>
                        ) : (
                          <>
                            <Play className="mr-2 h-5 w-5" />
                            Play
                          </>
                        )}
                      </Button>
                      
                      <Button
                        size="lg"
                        variant="outline"
                        onClick={downloadAudio}
                      >
                        <Download className="mr-2 h-5 w-5" />
                        Download
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
        
        {/* Statistics Card */}
        <Card>
          <CardHeader>
            <CardTitle>Voice Lab Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div className="space-y-2">
                <p className="text-sm text-gray-600">Languages</p>
                <p className="text-2xl font-bold">3</p>
                <p className="text-xs text-gray-600">Asante, Akuapem, Fante</p>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-gray-600">Voices</p>
                <p className="text-2xl font-bold">{voices.length}</p>
                <p className="text-xs text-gray-600">Natural & Cloned</p>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-gray-600">ASR Accuracy</p>
                <p className="text-2xl font-bold">95%</p>
                <p className="text-xs text-gray-600">WER &lt; 15%</p>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-gray-600">TTS Quality</p>
                <p className="text-2xl font-bold">4.2</p>
                <p className="text-xs text-gray-600">MOS Score</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}