import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { 
  FlaskConical, 
  Mic, 
  Play, 
  Square, 
  Download, 
  Upload,
  AudioWaveform,
  Brain,
  Zap,
  Globe,
  Settings2,
  TestTube,
  Loader2,
  Pause,
  Package
} from 'lucide-react';
import * as VoiceRDLabAPI from '@/lib/voice-rd-lab';
import ModelManagement from '@/components/voice/ModelManagement';

export default function VoiceRDLab() {
  const { toast } = useToast();
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedEngine, setSelectedEngine] = useState('meta_mms');
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [inputText, setInputText] = useState('');
  const [currentAudio, setCurrentAudio] = useState<Blob | null>(null);
  const [audioMetadata, setAudioMetadata] = useState<any>(null);
  const [ttsModels, setTtsModels] = useState<Record<string, any>>({});
  const [servicesHealth, setServicesHealth] = useState<Record<string, string>>({});
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [voiceParams, setVoiceParams] = useState({
    pitch: 1.0,
    speed: 1.0,
    emotion: 'neutral'
  });

  // Load models and health status on mount
  useEffect(() => {
    loadModels();
    checkServicesHealth();
  }, []);

  const loadModels = async () => {
    try {
      const { models } = await VoiceRDLabAPI.listTTSModels();
      setTtsModels(models);
    } catch (error) {
      console.error('Failed to load models:', error);
      toast({
        title: 'Error',
        description: 'Failed to load TTS models',
        variant: 'destructive',
      });
    }
  };

  const checkServicesHealth = async () => {
    try {
      const health = await VoiceRDLabAPI.checkHealth();
      setServicesHealth(health.services);
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };

  const handleSynthesize = async () => {
    if (!inputText.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter text to synthesize',
        variant: 'destructive',
      });
      return;
    }

    setIsProcessing(true);
    try {
      const audioBlob = await VoiceRDLabAPI.synthesizeSpeech({
        text: inputText,
        model_id: selectedEngine,
        language: selectedLanguage,
        parameters: voiceParams,
      });

      setCurrentAudio(audioBlob);
      setAudioMetadata((audioBlob as any).metadata);
      
      toast({
        title: 'Success',
        description: 'Speech synthesized successfully',
      });
    } catch (error) {
      console.error('Synthesis error:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to synthesize speech',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePlay = () => {
    if (currentAudio) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      
      const audio = VoiceRDLabAPI.playAudioBlob(currentAudio);
      audioRef.current = audio;
      setIsPlaying(true);
      
      audio.addEventListener('ended', () => {
        setIsPlaying(false);
        audioRef.current = null;
      });
    }
  };

  const handleStop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsPlaying(false);
    }
  };

  const handleDownload = () => {
    if (currentAudio) {
      const filename = `${selectedEngine}_${selectedLanguage}_${Date.now()}.wav`;
      VoiceRDLabAPI.downloadAudioBlob(currentAudio, filename);
    }
  };

  // Get available languages for selected model
  const getAvailableLanguages = () => {
    const model = ttsModels[selectedEngine];
    if (!model) return [];
    return model.languages.map((code: string) => {
      const languageNames: Record<string, string> = {
        'en': 'English',
        'twi': 'Twi',
        'ewe': 'Ewe',
        'hau': 'Hausa',
        'aka': 'Akan',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ar': 'Arabic'
      };
      return { code, name: languageNames[code] || code.toUpperCase() };
    });
  };

  return (
    <div className="flex h-screen bg-background">
      <DashboardSidebar />
      <div className="flex-1 overflow-auto">
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg">
              <FlaskConical className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Voice R&D Lab</h1>
              <p className="text-gray-600">Experiment with voice synthesis and cloning technologies</p>
            </div>
          </div>

      {/* Main Content */}
      <Tabs defaultValue="models" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="models">Model Manager</TabsTrigger>
          <TabsTrigger value="synthesis">Voice Synthesis</TabsTrigger>
          <TabsTrigger value="cloning">Voice Cloning</TabsTrigger>
          <TabsTrigger value="analysis">Voice Analysis</TabsTrigger>
          <TabsTrigger value="benchmark">Benchmarking</TabsTrigger>
        </TabsList>

        {/* Model Management Tab */}
        <TabsContent value="models">
          <ModelManagement />
        </TabsContent>

        {/* Voice Synthesis Tab */}
        <TabsContent value="synthesis" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Input Section */}
            <Card>
              <CardHeader>
                <CardTitle>Input Configuration</CardTitle>
                <CardDescription>Configure text and voice parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="tts-engine">TTS Engine</Label>
                  <Select value={selectedEngine} onValueChange={(value) => {
                    setSelectedEngine(value);
                    // Reset language if not supported by new engine
                    const model = ttsModels[value];
                    if (model && !model.languages.includes(selectedLanguage)) {
                      setSelectedLanguage(model.languages[0] || 'en');
                    }
                  }}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(ttsModels).map(([id, model]) => (
                        <SelectItem key={id} value={id}>
                          <div className="flex items-center gap-2">
                            {model.name}
                            <Badge 
                              variant={servicesHealth[id] === 'healthy' ? 'default' : 
                                      servicesHealth[id] === 'degraded' ? 'secondary' : 'destructive'} 
                              className="text-xs"
                            >
                              {servicesHealth[id] || model.status}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="language">Language</Label>
                  <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {getAvailableLanguages().map(lang => (
                        <SelectItem key={lang.code} value={lang.code}>
                          {lang.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="text-input">Text Input</Label>
                  <Textarea 
                    id="text-input"
                    placeholder="Enter text to synthesize..."
                    className="min-h-[100px]"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Voice Parameters</Label>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <Label className="w-20">Pitch</Label>
                      <Slider 
                        value={[voiceParams.pitch]} 
                        onValueChange={([value]) => setVoiceParams({...voiceParams, pitch: value})}
                        min={0.5}
                        max={2}
                        step={0.1}
                        className="flex-1"
                      />
                      <span className="w-12 text-sm">{voiceParams.pitch}x</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Label className="w-20">Speed</Label>
                      <Slider 
                        value={[voiceParams.speed]} 
                        onValueChange={([value]) => setVoiceParams({...voiceParams, speed: value})}
                        min={0.5}
                        max={2}
                        step={0.1}
                        className="flex-1"
                      />
                      <span className="w-12 text-sm">{voiceParams.speed}x</span>
                    </div>
                  </div>
                </div>

                <Button 
                  className="w-full" 
                  disabled={isProcessing || !inputText.trim()}
                  onClick={handleSynthesize}
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Generate Speech
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Output Section */}
            <Card>
              <CardHeader>
                <CardTitle>Output & Playback</CardTitle>
                <CardDescription>Listen to and analyze generated speech</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="h-32 bg-muted rounded-lg flex items-center justify-center">
                  {currentAudio ? (
                    <div className="text-center">
                      <AudioWaveform className="h-8 w-8 mx-auto mb-2 text-indigo-600" />
                      <p className="text-sm text-gray-600">Audio ready</p>
                    </div>
                  ) : (
                    <AudioWaveform className="h-8 w-8 text-gray-600" />
                  )}
                </div>
                
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    className="flex-1"
                    disabled={!currentAudio}
                    onClick={isPlaying ? handleStop : handlePlay}
                  >
                    {isPlaying ? (
                      <>
                        <Pause className="mr-2 h-4 w-4" />
                        Stop
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Play
                      </>
                    )}
                  </Button>
                  <Button 
                    variant="outline" 
                    className="flex-1"
                    disabled={!currentAudio}
                    onClick={handleDownload}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                </div>

                <div className="space-y-2">
                  <Label>Generation Metrics</Label>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Processing Time:</span>
                      <span>{audioMetadata?.processingTime ? `${audioMetadata.processingTime}s` : '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Audio Duration:</span>
                      <span>{currentAudio ? 'Calculating...' : '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Sample Rate:</span>
                      <span>{currentAudio ? '22050 Hz' : '-'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">File Size:</span>
                      <span>{currentAudio ? `${(currentAudio.size / 1024).toFixed(2)} KB` : '-'}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Engine Status */}
          <Card>
            <CardHeader>
              <CardTitle>TTS Engine Status</CardTitle>
              <CardDescription>Real-time status of available TTS engines</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {Object.entries(ttsModels).map(([id, model]) => {
                  const status = servicesHealth[id] || model.status;
                  const isHealthy = status === 'healthy' || status === 'active';
                  const isDegraded = status === 'degraded';
                  
                  return (
                    <div key={id} className="flex flex-col items-center gap-2 p-3 border rounded-lg">
                      <div className={`w-3 h-3 rounded-full ${
                        isHealthy ? 'bg-green-500' : 
                        isDegraded ? 'bg-yellow-500' : 
                        'bg-gray-300'
                      }`} />
                      <span className="text-sm font-medium text-center">{model.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {status}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Voice Cloning Tab */}
        <TabsContent value="cloning" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Voice Cloning</CardTitle>
              <CardDescription>Clone voices using reference audio samples</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <TestTube className="h-4 w-4" />
                <AlertDescription>
                  Voice cloning feature using OpenVoice technology. Upload a reference audio to clone the voice.
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <div className="border-2 border-dashed rounded-lg p-8 text-center">
                  <Upload className="mx-auto h-12 w-12 text-gray-600 mb-4" />
                  <Button variant="secondary">
                    Upload Reference Audio
                  </Button>
                  <p className="text-sm text-gray-600 mt-2">
                    WAV, MP3, or M4A (max 10MB)
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Target Text</Label>
                  <Textarea placeholder="Enter text to speak in cloned voice..." />
                </div>

                <Button className="w-full" disabled>
                  <Brain className="mr-2 h-4 w-4" />
                  Clone & Generate
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Voice Analysis Tab */}
        <TabsContent value="analysis" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Voice Analysis</CardTitle>
              <CardDescription>Analyze voice characteristics and quality metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center h-64 text-gray-600">
                <div className="text-center">
                  <AudioWaveform className="h-12 w-12 mx-auto mb-4" />
                  <p>Voice analysis tools coming soon</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Benchmarking Tab */}
        <TabsContent value="benchmark" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Benchmarking</CardTitle>
              <CardDescription>Compare TTS engines performance and quality</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center h-64 text-gray-600">
                <div className="text-center">
                  <Zap className="h-12 w-12 mx-auto mb-4" />
                  <p>Benchmarking tools coming soon</p>
                </div>
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