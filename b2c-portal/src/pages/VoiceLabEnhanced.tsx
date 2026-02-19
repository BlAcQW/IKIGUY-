import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import {
  Mic,
  Play,
  Square,
  Download,
  Upload,
  AudioWaveform,
  Globe,
  Loader2,
  Settings,
  Brain,
  Zap,
  MessageSquare,
  CheckCircle,
  Info,
  RefreshCw
} from 'lucide-react';
import { getAuthHeaders } from '@/lib/auth-utils';
import { useAudioRecorder } from '@/hooks/useAudioRecorder';
import { useVoiceTranscription } from '@/hooks/useVoiceTranscription';
import { useVoiceSynthesis } from '@/hooks/useVoiceSynthesis';
import { sendChatMessage } from '@/services/voice-api';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

import {
  ASR_MODELS,
  TTS_MODELS,
  LLM_MODELS,
  CONVERSATION_MODES,
  DEFAULT_ASR_MODEL,
  DEFAULT_TTS_MODEL,
  DEFAULT_LLM_MODEL,
  DEFAULT_DIALECT,
  DEFAULT_CONVERSATION_MODE,
  getASRModel,
  getTTSModel,
  getLLMModel,
} from '@/config/voice-models';

// Using API_BASE_URL from api-config;

export default function VoiceLabEnhanced() {
  const { toast } = useToast();

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

  // Model selections
  const [selectedASR, setSelectedASR] = useState(DEFAULT_ASR_MODEL);
  const [selectedTTS, setSelectedTTS] = useState(DEFAULT_TTS_MODEL);
  const [selectedLLM, setSelectedLLM] = useState(DEFAULT_LLM_MODEL);
  const [conversationMode, setConversationMode] = useState(DEFAULT_CONVERSATION_MODE);

  // Advanced settings
  const [enableStreaming, setEnableStreaming] = useState(true);
  const [enableVAD, setEnableVAD] = useState(true);
  const [enableConversation, setEnableConversation] = useState(false);
  const [ttsSpeed, setTtsSpeed] = useState([1.0]);
  const [ttsPitch, setTtsPitch] = useState([0]);

  // Text content
  const [inputText, setInputText] = useState('');
  const [transcribedText, setTranscribedText] = useState('');
  const [conversationHistory, setConversationHistory] = useState<Array<{role: string, content: string}>>([]);

  // Get auth headers using MongoDB auth
  const getRequestHeaders = async () => {
    const authHeaders = await getAuthHeaders();
    return {
      ...authHeaders,
      'Content-Type': 'application/json',
    };
  };

  // Handle recording complete - process audio with selected ASR model
  const handleRecordingComplete = async (audioBlob: Blob) => {
    console.log('[VoiceLabEnhanced] 🎤 Recording complete, starting transcription...');

    try {
      const result = await transcribe(audioBlob, {
        language: 'tw',
        dialect: selectedDialect,
        model: selectedASR,
        enableStreaming,
        enableVAD,
        returnTimestamps: false,
        enhanceText: true
      });

      setTranscribedText(result.text);

      // If conversation mode is enabled, process with LLM
      if (enableConversation && result.text) {
        await processWithLLM(result.text);
      }

      toast({
        title: '✅ Transcription Complete',
        description: `Processed with ${selectedASR}`,
      });
    } catch (error) {
      console.error('[VoiceLabEnhanced] ❌ Transcription error:', error);
      toast({
        title: 'Error',
        description: 'Failed to transcribe audio',
        variant: 'destructive',
      });
    }
  };

  // Start/stop recording handlers
  const handleStartRecording = async () => {
    const asrModel = getASRModel(selectedASR);
    toast({
      title: '🎤 Recording',
      description: `Using ${asrModel?.name || selectedASR}`,
    });
    await startAudioRecording();
  };

  const handleStopRecording = () => {
    stopAudioRecording();
  };

  // Process with LLM for conversation using voice-api service
  const processWithLLM = async (text: string) => {
    try {
      const result = await sendChatMessage({
        message: text,
        model: selectedLLM,
        mode: conversationMode,
        history: conversationHistory,
        language: 'tw',
        dialect: selectedDialect,
      });

      // Update conversation history
      setConversationHistory([
        ...conversationHistory,
        { role: 'user', content: text },
        { role: 'assistant', content: result.response },
      ]);

      // Synthesize response
      if (result.response) {
        await handleSynthesizeSpeech(result.response);
      }
    } catch (error) {
      console.error('[VoiceLabEnhanced] ❌ LLM processing error:', error);
      toast({
        title: 'Error',
        description: 'Failed to process with LLM',
        variant: 'destructive',
      });
    }
  };

  // Synthesize speech with selected TTS model using the hook
  const handleSynthesizeSpeech = async (text: string) => {
    console.log('[VoiceLabEnhanced] 🔊 Starting synthesis...');

    try {
      const result = await synthesize(text, {
        model: selectedTTS,
        voiceId: 'default',
        language: 'tw',
        dialect: selectedDialect,
        speed: ttsSpeed[0],
        pitch: ttsPitch[0]
      });

      // Play the synthesized audio
      await play(result.audioBase64);

      toast({
        title: '✅ Speech Synthesized',
        description: `Generated with ${selectedTTS}`,
      });
    } catch (error) {
      console.error('[VoiceLabEnhanced] ❌ Synthesis error:', error);
      toast({
        title: 'Error',
        description: 'Failed to synthesize speech',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="flex min-h-screen">
      <DashboardSidebar />
      <div className="flex-1 space-y-6 p-8">
        <div>
          <h2 className="text-3xl text-heading tracking-tight">Voice Lab Enhanced</h2>
          <p className="text-gray-600 text-body">
            Advanced multi-model ASR, TTS, and Conversational AI for Twi/Akan
          </p>
        </div>

        {/* Model Selection Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Model Configuration
            </CardTitle>
            <CardDescription>
              Select and configure AI models for each component
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* ASR Model Selection */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <AudioWaveform className="h-4 w-4" />
                  ASR Model
                </Label>
                <Select value={selectedASR} onValueChange={setSelectedASR}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(ASR_MODELS).map(([category, models]) => (
                      <div key={category}>
                        <div className="px-2 py-1 text-xs font-semibold text-gray-600">
                          {models.name}
                        </div>
                        {models.variants.map(model => (
                          <SelectItem key={model.id} value={model.id}>
                            <div className="flex items-center justify-between w-full">
                              <span>{model.name}</span>
                              <Badge variant="outline" className="ml-2">
                                {model.accuracy}
                              </Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </div>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* TTS Model Selection */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  TTS Model
                </Label>
                <Select value={selectedTTS} onValueChange={setSelectedTTS}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(TTS_MODELS).map(([category, models]) => (
                      <div key={category}>
                        <div className="px-2 py-1 text-xs font-semibold text-gray-600">
                          {models.name}
                        </div>
                        {models.variants.map(model => (
                          <SelectItem key={model.id} value={model.id}>
                            <div className="flex items-center justify-between w-full">
                              <span>{model.name}</span>
                              <Badge variant="outline" className="ml-2">
                                MOS {model.quality}
                              </Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </div>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* LLM Model Selection */}
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Brain className="h-4 w-4" />
                  LLM Model
                </Label>
                <Select value={selectedLLM} onValueChange={setSelectedLLM} disabled={!enableConversation}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(LLM_MODELS).map(([category, models]) => (
                      <div key={category}>
                        <div className="px-2 py-1 text-xs font-semibold text-gray-600">
                          {models.name}
                        </div>
                        {models.variants.map(model => (
                          <SelectItem key={model.id} value={model.id}>
                            <div className="flex items-center justify-between w-full">
                              <span>{model.name}</span>
                              <Badge variant="outline" className="ml-2">
                                {model.context}
                              </Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </div>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Advanced Settings */}
            <div className="space-y-4 pt-4 border-t">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex items-center justify-between">
                  <Label htmlFor="streaming" className="flex items-center gap-2">
                    <RefreshCw className="h-4 w-4" />
                    Streaming Mode
                  </Label>
                  <Switch
                    id="streaming"
                    checked={enableStreaming}
                    onCheckedChange={setEnableStreaming}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="vad" className="flex items-center gap-2">
                    <AudioWaveform className="h-4 w-4" />
                    Voice Activity Detection
                  </Label>
                  <Switch
                    id="vad"
                    checked={enableVAD}
                    onCheckedChange={setEnableVAD}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <Label htmlFor="conversation" className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    Conversation Mode
                  </Label>
                  <Switch
                    id="conversation"
                    checked={enableConversation}
                    onCheckedChange={setEnableConversation}
                  />
                </div>
              </div>

              {/* TTS Controls */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Speech Speed: {ttsSpeed[0]}x</Label>
                  <Slider
                    value={ttsSpeed}
                    onValueChange={setTtsSpeed}
                    min={0.5}
                    max={2}
                    step={0.1}
                    className="w-full"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Pitch Adjustment: {ttsPitch[0]}</Label>
                  <Slider
                    value={ttsPitch}
                    onValueChange={setTtsPitch}
                    min={-5}
                    max={5}
                    step={1}
                    className="w-full"
                  />
                </div>
              </div>

              {/* Conversation Mode Selection */}
              {enableConversation && (
                <div className="space-y-2">
                  <Label>Conversation Mode</Label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {CONVERSATION_MODES.map(mode => (
                      <Button
                        key={mode.id}
                        variant={conversationMode === mode.id ? "default" : "outline"}
                        size="sm"
                        onClick={() => setConversationMode(mode.id)}
                        className="justify-start"
                      >
                        <span className="mr-2">{mode.icon}</span>
                        {mode.name}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Main Interface */}
        <Card>
          <CardHeader>
            <CardTitle>Voice Interface</CardTitle>
            <CardDescription>
              Record, transcribe, and synthesize speech with selected models
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Dialect Selection */}
            <div className="flex items-center gap-4">
              <Label>Dialect:</Label>
              <Select value={selectedDialect} onValueChange={setSelectedDialect}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="asante">Asante Twi</SelectItem>
                  <SelectItem value="akuapem">Akuapem Twi</SelectItem>
                  <SelectItem value="fante">Fante</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Recording Controls */}
            <div className="flex justify-center">
              <Button
                size="lg"
                variant={isRecording ? "destructive" : "default"}
                onClick={isRecording ? handleStopRecording : handleStartRecording}
                disabled={isTranscribing || isSynthesizing}
                className="min-w-[200px]"
              >
                {isTranscribing || isSynthesizing ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    {isTranscribing ? 'Transcribing...' : 'Synthesizing...'}
                  </>
                ) : isRecording ? (
                  <>
                    <Square className="mr-2 h-5 w-5" />
                    Stop Recording
                  </>
                ) : (
                  <>
                    <Mic className="mr-2 h-5 w-5" />
                    Start Recording
                  </>
                )}
              </Button>
            </div>

            {/* Transcription Result */}
            {transcribedText && (
              <div className="space-y-2">
                <Label>Transcription:</Label>
                <Textarea
                  value={transcribedText}
                  onChange={(e) => setTranscribedText(e.target.value)}
                  className="min-h-[100px]"
                  placeholder="Transcribed text will appear here..."
                />
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleSynthesizeSpeech(transcribedText)}
                    disabled={isSynthesizing || isPlaying}
                  >
                    {isPlaying ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Playing...
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Synthesize Speech
                      </>
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigator.clipboard.writeText(transcribedText)}
                  >
                    Copy Text
                  </Button>
                </div>
              </div>
            )}

            {/* Conversation History */}
            {enableConversation && conversationHistory.length > 0 && (
              <div className="space-y-2">
                <Label>Conversation:</Label>
                <div className="border rounded-lg p-4 max-h-[300px] overflow-y-auto space-y-2">
                  {conversationHistory.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`p-2 rounded ${
                        msg.role === 'user' 
                          ? 'bg-blue-50 ml-8' 
                          : 'bg-gray-50 mr-8'
                      }`}
                    >
                      <div className="text-xs font-semibold text-gray-600 mb-1">
                        {msg.role === 'user' ? 'You' : conversationMode === 'healthcare' ? 'Health Assistant' : conversationMode === 'education' ? 'Tutor' : conversationMode === 'finance' ? 'Financial Advisor' : 'Assistant'}
                      </div>
                      <div className="text-sm">{msg.content}</div>
                    </div>
                  ))}
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setConversationHistory([])}
                >
                  Clear Conversation
                </Button>
              </div>
            )}

            {/* Model Info */}
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-1">
                  <div><strong>ASR:</strong> {getASRModel(selectedASR)?.name || selectedASR}</div>
                  <div><strong>TTS:</strong> {getTTSModel(selectedTTS)?.name || selectedTTS}</div>
                  {enableConversation && (
                    <div><strong>LLM:</strong> {getLLMModel(selectedLLM)?.name || selectedLLM}</div>
                  )}
                </div>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}