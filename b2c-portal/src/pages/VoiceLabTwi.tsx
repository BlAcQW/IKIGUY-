import React, { useState, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import {
  Mic,
  Play,
  Square,
  Download,
  Upload,
  AudioWaveform,
  Globe,
  Loader2,
  Pause,
  CheckCircle,
  Info
} from 'lucide-react';
import { useAudioRecorder } from '@/hooks/useAudioRecorder';
import { useVoiceTranscription } from '@/hooks/useVoiceTranscription';
import { useVoiceSynthesis } from '@/hooks/useVoiceSynthesis';
import { DIALECT_OPTIONS, DEFAULT_DIALECT, DEFAULT_ASR_MODEL, DEFAULT_TTS_MODEL } from '@/config/voice-models';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';
import { downloadAudioBlob } from '@/lib/audio-utils';


// Using API_BASE_URL from api-config;

export default function VoiceLabTwi() {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Use the new shared hooks
  const { isRecording, audioBlob, startRecording: startAudioRecording, stopRecording: stopAudioRecording, clearRecording, error: recordingError } = useAudioRecorder({
    onRecordingComplete: (blob) => handleRecordingComplete(blob),
    onError: (error) => {
      toast({
        title: 'Recording Error',
        description: error.message,
        variant: 'destructive',
      });
    }
  });

  const { transcribe, isTranscribing, result: transcriptionResult, error: transcriptionError, clearResult: clearTranscription } = useVoiceTranscription();

  const { synthesize, play, stop: stopAudio, isSynthesizing, isPlaying, result: synthesisResult, error: synthesisError, clearResult: clearSynthesis } = useVoiceSynthesis();

  // State management
  const [selectedDialect, setSelectedDialect] = useState(DEFAULT_DIALECT);
  const [inputText, setInputText] = useState('');
  const [transcribedText, setTranscribedText] = useState('');
  const [enhancedText, setEnhancedText] = useState('');
  const [confidence, setConfidence] = useState<number | null>(null);
  const [currentAudio, setCurrentAudio] = useState<Blob | null>(null);

  const SAMPLE_TEXTS = {
    asante: "Me ma wo akye. Wo ho te sɛn? Me pɛ sɛ mekasa Twi.",
    akuapem: "Me ma wo akye. Wo ho te sɛn? Me pɛ sɛ mekasa Twi.",
    fante: "Me ma wo akye. Wo ho te sɛn? Me pɛ dɛ mekasa Mfantse."
  };

  // Handle recording complete
  const handleRecordingComplete = async (audioBlob: Blob) => {
    console.log('[VoiceLabTwi] 🎤 Recording complete, starting transcription...');
    setCurrentAudio(audioBlob);
    setTranscribedText('');
    setEnhancedText('');
    setConfidence(null);

    try {
      const result = await transcribe(audioBlob, {
        language: 'tw',
        dialect: selectedDialect,
        model: DEFAULT_ASR_MODEL,
        enhanceText: true,
        returnTimestamps: false
      });

      setTranscribedText(result.text);
      setEnhancedText(result.enhancedText || result.text);
      setConfidence(result.confidence);

      toast({
        title: '✅ Transcription Complete',
        description: `Confidence: ${(result.confidence * 100).toFixed(1)}%`,
      });
    } catch (error) {
      console.error('[VoiceLabTwi] ❌ Transcription error:', error);
      toast({
        title: 'Error',
        description: 'Failed to transcribe audio',
        variant: 'destructive',
      });
    }
  };

  // Start/stop recording handlers
  const handleStartRecording = async () => {
    toast({
      title: '🎤 Recording',
      description: 'Speak in Twi...',
    });
    await startAudioRecording();
  };

  const handleStopRecording = () => {
    stopAudioRecording();
  };

  // Synthesize speech using the hook
  const handleSynthesizeSpeech = async () => {
    if (!inputText.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter text to synthesize',
        variant: 'destructive',
      });
      return;
    }

    console.log('[VoiceLabTwi] 🔊 Starting synthesis...');

    try {
      const result = await synthesize(inputText, {
        model: DEFAULT_TTS_MODEL,
        voiceId: `${selectedDialect}_female_1`,
        language: 'tw',
        dialect: selectedDialect,
        speed: 1.0,
        pitch: 0.0
      });

      // Play the synthesized audio
      await play(result.audioBase64);

      toast({
        title: '✅ Speech Synthesized',
        description: 'Playing audio...',
      });
    } catch (error) {
      console.error('[VoiceLabTwi] ❌ Synthesis error:', error);
      toast({
        title: 'Error',
        description: 'Failed to synthesize speech',
        variant: 'destructive',
      });
    }
  };

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const audioBlob = new Blob([file], { type: file.type });
    setCurrentAudio(audioBlob);
    await handleRecordingComplete(audioBlob);
  };

  // Download audio
  const downloadAudio = () => {
    if (!currentAudio) return;
    downloadAudioBlob(currentAudio, `twi_audio_${Date.now()}.wav`);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <DashboardSidebar />
      
      <div className="flex-1 overflow-y-auto">
        <div className="p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Globe className="h-8 w-8 text-indigo-600" />
              Voice Lab - Twi/Akan ASR & TTS
            </h1>
            <p className="text-gray-600 mt-2">
              Advanced speech recognition and synthesis for Ghanaian languages
            </p>
          </div>

          <Alert className="mb-6">
            <Info className="h-4 w-4" />
            <AlertDescription>
              <strong>Model:</strong> GiftMark/akan-whisper-model (92.9% accuracy) • 
              <strong>Languages:</strong> Asante Twi, Akuapem Twi, Fante • 
              <strong>Features:</strong> Enhanced text processing with numbers, dates, and phonemes
            </AlertDescription>
          </Alert>

          <Tabs defaultValue="transcribe" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="transcribe">
                <Mic className="mr-2 h-4 w-4" />
                Speech to Text
              </TabsTrigger>
              <TabsTrigger value="synthesize">
                <AudioWaveform className="mr-2 h-4 w-4" />
                Text to Speech
              </TabsTrigger>
              <TabsTrigger value="process">
                <Globe className="mr-2 h-4 w-4" />
                Text Processing
              </TabsTrigger>
            </TabsList>

            <TabsContent value="transcribe">
              <Card>
                <CardHeader>
                  <CardTitle>Speech Recognition (ASR)</CardTitle>
                  <CardDescription>
                    Record or upload audio in Twi to get accurate transcriptions
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Dialect Selection */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Dialect</label>
                    <Select value={selectedDialect} onValueChange={setSelectedDialect}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {DIALECT_OPTIONS.map(dialect => (
                          <SelectItem key={dialect.value} value={dialect.value}>
                            {dialect.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Recording Controls */}
                  <div className="flex gap-4">
                    <Button
                      onClick={isRecording ? handleStopRecording : handleStartRecording}
                      variant={isRecording ? "destructive" : "default"}
                      className="flex-1"
                      disabled={isTranscribing}
                    >
                      {isRecording ? (
                        <>
                          <Square className="mr-2 h-4 w-4" />
                          Stop Recording
                        </>
                      ) : (
                        <>
                          <Mic className="mr-2 h-4 w-4" />
                          Start Recording
                        </>
                      )}
                    </Button>

                    <Button
                      onClick={() => fileInputRef.current?.click()}
                      variant="outline"
                      disabled={isTranscribing || isRecording}
                    >
                      <Upload className="mr-2 h-4 w-4" />
                      Upload Audio
                    </Button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="audio/*"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </div>

                  {/* Processing Indicator */}
                  {isTranscribing && (
                    <div className="flex items-center justify-center p-8 bg-gray-50 rounded-lg">
                      <Loader2 className="h-8 w-8 animate-spin text-indigo-600 mr-3" />
                      <span>Transcribing audio...</span>
                    </div>
                  )}

                  {/* Transcription Results */}
                  {transcribedText && (
                    <div className="space-y-4">
                      <div className="p-4 bg-blue-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold">Original Transcription</h3>
                          {confidence && (
                            <Badge variant="secondary">
                              <CheckCircle className="mr-1 h-3 w-3" />
                              {(confidence * 100).toFixed(1)}% confidence
                            </Badge>
                          )}
                        </div>
                        <p className="text-gray-800">{transcribedText}</p>
                      </div>

                      {enhancedText && enhancedText !== transcribedText && (
                        <div className="p-4 bg-green-50 rounded-lg">
                          <h3 className="font-semibold mb-2">Enhanced Text</h3>
                          <p className="text-gray-800">{enhancedText}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Audio Player */}
                  {currentAudio && (
                    <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                      <Button
                        onClick={togglePlayback}
                        size="sm"
                        variant="outline"
                      >
                        {isPlaying ? (
                          <Pause className="h-4 w-4" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                      </Button>
                      <audio
                        ref={audioRef}
                        onEnded={() => setIsPlaying(false)}
                        className="flex-1"
                        controls
                      />
                      <Button
                        onClick={downloadAudio}
                        size="sm"
                        variant="outline"
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="synthesize">
              <Card>
                <CardHeader>
                  <CardTitle>Text to Speech (TTS)</CardTitle>
                  <CardDescription>
                    Convert Twi text to natural-sounding speech
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Dialect Selection */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Dialect</label>
                    <Select value={selectedDialect} onValueChange={setSelectedDialect}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {DIALECT_OPTIONS.map(dialect => (
                          <SelectItem key={dialect.value} value={dialect.value}>
                            {dialect.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Text Input */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Text to Synthesize</label>
                    <Textarea
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      placeholder="Enter Twi text here..."
                      rows={4}
                      className="font-mono"
                    />
                    <div className="flex gap-2">
                      <Button
                        onClick={() => setInputText(SAMPLE_TEXTS[selectedDialect])}
                        size="sm"
                        variant="outline"
                      >
                        Use Sample Text
                      </Button>
                      <Button
                        onClick={() => setInputText('')}
                        size="sm"
                        variant="outline"
                      >
                        Clear
                      </Button>
                    </div>
                  </div>

                  {/* Synthesize Button */}
                  <Button
                    onClick={handleSynthesizeSpeech}
                    className="w-full"
                    disabled={isSynthesizing || isPlaying || !inputText.trim()}
                  >
                    {isSynthesizing || isPlaying ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {isSynthesizing ? 'Synthesizing...' : 'Playing...'}
                      </>
                    ) : (
                      <>
                        <AudioWaveform className="mr-2 h-4 w-4" />
                        Synthesize Speech
                      </>
                    )}
                  </Button>

                  {/* Audio Player */}
                  {currentAudio && (
                    <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
                      <Button
                        onClick={stopAudio}
                        size="sm"
                        variant="outline"
                        disabled={!isPlaying}
                      >
                        {isPlaying ? (
                          <Pause className="h-4 w-4" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                      </Button>
                      <audio
                        ref={audioRef}
                        onEnded={() => setIsPlaying(false)}
                        className="flex-1"
                        controls
                      />
                      <Button
                        onClick={downloadAudio}
                        size="sm"
                        variant="outline"
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="process">
              <Card>
                <CardHeader>
                  <CardTitle>Enhanced Text Processing</CardTitle>
                  <CardDescription>
                    Process Twi text with advanced features like number expansion and phoneme generation
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                      Features include: Number to Twi conversion (0-1,000,000+), 
                      currency processing (GH₵, $, €, £), date/time formatting, 
                      abbreviation expansion, and IPA phoneme generation.
                    </AlertDescription>
                  </Alert>

                  <div className="space-y-4">
                    <Textarea
                      placeholder="Enter text with numbers, dates, or currencies..."
                      rows={4}
                      className="font-mono"
                      defaultValue="Mepɛ GH₵100. Today is 25/12/2024 at 3:30pm."
                    />
                    <Button className="w-full">
                      <Globe className="mr-2 h-4 w-4" />
                      Process Text
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}