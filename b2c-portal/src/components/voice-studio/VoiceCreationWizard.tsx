import React, { useState, useRef } from 'react';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

import { 
  X, 
  Upload, 
  Mic, 
  Play, 
  Square, 
  Pause,
  ChevronLeft,
  ChevronRight,
  Download,
  Database,
  Wand2,
  FileAudio,
  User,
  Settings,
  Brain,
  Volume2,
  StopCircle
} from 'lucide-react';

interface VoiceCreationWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onVoiceCreated: (voice: any) => void;
}

type WizardStep = 'method' | 'upload' | 'record' | 'dataset' | 'configure' | 'training' | 'preview';

interface VoiceData {
  name: string;
  description: string;
  language: string;
  accent: string;
  gender: 'male' | 'female' | 'neutral';
  provider: 'xtts' | 'coqui_tts' | 'f5_tts' | 'melotts' | 'openvoice' | 'elevenlabs' | 'meta_mms';
  audioFile?: File;
  recordedAudio?: Blob;
  selectedDataset?: string;
  trainingConfig: {
    epochs: number;
    batchSize: number;
    learningRate: number;
  };
}

export const VoiceCreationWizard: React.FC<VoiceCreationWizardProps> = ({
  isOpen,
  onClose,
  onVoiceCreated
}) => {
  const [currentStep, setCurrentStep] = useState<WizardStep>('method');
  
  // Initialize logging
  React.useEffect(() => {
    if (isOpen) {
      console.log('🎯 VoiceStudio: Voice Creation Wizard opened');
      console.log('📝 Initial step:', 'method');
    }
  }, [isOpen]);
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [isTraining, setIsTraining] = useState(false);
  const [recordedAudioUrl, setRecordedAudioUrl] = useState<string | null>(null);
  const [createdVoiceAudioUrl, setCreatedVoiceAudioUrl] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const trainingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const [voiceData, setVoiceData] = useState<VoiceData>({
    name: '',
    description: '',
    language: 'en',
    accent: 'neutral',
    gender: 'neutral',
    provider: 'melotts', // Force MeloTTS as default
    trainingConfig: {
      epochs: 1000,
      batchSize: 8,
      learningRate: 0.0001
    }
  });

  // Force provider to melotts on component mount to override any cached values
  React.useEffect(() => {
    console.log('🔧 VoiceStudio: Forcing provider to melotts');
    setVoiceData(prev => ({ ...prev, provider: 'melotts' }));
    
    // Cleanup function to clear intervals on unmount
    return () => {
      if (trainingIntervalRef.current) {
        clearInterval(trainingIntervalRef.current);
        console.log('🧹 VoiceStudio: Cleaned up training interval on unmount');
      }
      if (audioRef.current) {
        audioRef.current.pause();
        console.log('🧹 VoiceStudio: Stopped audio on unmount');
      }
    };
  }, []);

  // Helper function for step changes with logging
  const goToStep = (step: WizardStep, context?: string) => {
    console.log(`🔄 VoiceStudio: Step change from '${currentStep}' to '${step}'${context ? ` (${context})` : ''}`);
    setCurrentStep(step);
  };

  const availableDatasets = [
    {
      id: 'bible_tts_twi',
      name: 'BibleTTS Twi (Asante)',
      language: 'Twi',
      speakers: 2,
      duration: '12 hours',
      description: 'High-quality Asante Twi speech from biblical text readings',
      source: 'BibleTTS Research Project'
    },
    {
      id: 'bible_tts_akuapem',
      name: 'BibleTTS Twi (Akuapem)',  
      language: 'Twi',
      speakers: 2,
      duration: '10 hours',
      description: 'Natural Akuapem Twi speech recordings',
      source: 'BibleTTS Research Project'
    },
    {
      id: 'ghananlp_twi',
      name: 'GhanaNLP Twi Corpus',
      language: 'Twi',
      speakers: 15,
      duration: '25 hours', 
      description: 'Diverse Twi speech corpus from Ghana',
      source: 'GhanaNLP'
    },
    {
      id: 'meta_mms_ga',
      name: 'Meta MMS Ga Dataset',
      language: 'Ga',
      speakers: 8,
      duration: '18 hours',
      description: 'Ga language speech data from Meta MMS',
      source: 'Meta AI'
    },
    {
      id: 'meta_mms_ewe',
      name: 'Meta MMS Ewe Dataset', 
      language: 'Ewe',
      speakers: 6,
      duration: '15 hours',
      description: 'Ewe language TTS training data',
      source: 'Meta AI'
    },
    {
      id: 'common_voice_hausa',
      name: 'Common Voice Hausa',
      language: 'Hausa',
      speakers: 45,
      duration: '32 hours',
      description: 'Community-contributed Hausa speech recordings',
      source: 'Mozilla Common Voice'
    }
  ];

  const wizardSteps = [
    { id: 'method', title: 'Creation Method', icon: Wand2 },
    { id: 'upload', title: 'Audio Source', icon: Upload },
    { id: 'dataset', title: 'Training Data', icon: Database },
    { id: 'configure', title: 'Configuration', icon: Settings },
    { id: 'training', title: 'Training', icon: Brain },
    { id: 'preview', title: 'Preview', icon: Play }
  ];

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    console.log('📁 VoiceStudio: File upload initiated');
    const file = event.target.files?.[0];
    if (file) {
      console.log('✅ VoiceStudio: File selected:', {
        name: file.name,
        size: `${(file.size / 1024 / 1024).toFixed(2)} MB`,
        type: file.type,
        duration: 'analyzing...'
      });
      setVoiceData(prev => ({ ...prev, audioFile: file }));
      console.log('💾 VoiceStudio: File stored in voice data');
    } else {
      console.log('❌ VoiceStudio: No file selected');
    }
  };

  const startRecording = async () => {
    console.log('🎙️ VoiceStudio: Starting audio recording...');
    try {
      console.log('🔍 VoiceStudio: Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log('✅ VoiceStudio: Microphone access granted');
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      console.log('📱 VoiceStudio: MediaRecorder initialized');
      
      const chunks: BlobPart[] = [];
      mediaRecorder.ondataavailable = (event) => {
        console.log(`📊 VoiceStudio: Audio data chunk received (${event.data.size} bytes)`);
        chunks.push(event.data);
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        console.log('🎵 VoiceStudio: Recording completed:', {
          size: `${(blob.size / 1024).toFixed(2)} KB`,
          type: blob.type,
          chunks: chunks.length
        });
        
        // Create audio URL for playback
        const audioUrl = URL.createObjectURL(blob);
        setRecordedAudioUrl(audioUrl);
        console.log('🎧 VoiceStudio: Audio URL created for playback');
        
        setVoiceData(prev => ({ ...prev, recordedAudio: blob }));
        stream.getTracks().forEach(track => track.stop());
        console.log('🔇 VoiceStudio: Microphone stream stopped');
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      console.log('▶️ VoiceStudio: Recording started successfully');
    } catch (error) {
      console.error('❌ VoiceStudio: Error starting recording:', error);
      console.log('💡 VoiceStudio: Check microphone permissions or try refreshing the page');
    }
  };

  const stopRecording = () => {
    console.log('⏹️ VoiceStudio: Stopping audio recording...');
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      console.log('✅ VoiceStudio: Recording stopped successfully');
    } else {
      console.log('⚠️ VoiceStudio: No active recording to stop');
    }
  };

  const playRecordedAudio = () => {
    if (recordedAudioUrl && !isPlaying) {
      console.log('▶️ VoiceStudio: Playing recorded audio...');
      const audio = new Audio(recordedAudioUrl);
      audioRef.current = audio;
      
      audio.onended = () => {
        setIsPlaying(false);
        console.log('⏹️ VoiceStudio: Recorded audio playback ended');
      };
      
      audio.onerror = (error) => {
        setIsPlaying(false);
        console.error('❌ VoiceStudio: Audio playback error:', error);
      };
      
      audio.play()
        .then(() => {
          setIsPlaying(true);
          console.log('✅ VoiceStudio: Recorded audio playback started');
        })
        .catch(error => {
          console.error('❌ VoiceStudio: Failed to play recorded audio:', error);
        });
    }
  };

  const stopPlayback = () => {
    if (audioRef.current && isPlaying) {
      console.log('⏸️ VoiceStudio: Stopping audio playback...');
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      console.log('✅ VoiceStudio: Audio playback stopped');
    }
  };

  const stopVoicePlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
      console.log('⏹️ VoiceStudio: Voice playback stopped by user');
    }
  };

  const playCreatedVoice = async (sampleText: string = "Hello, this is a test of my created voice.") => {
    console.log('🎙️ VoiceStudio: Testing created voice with text:', sampleText);
    try {
      // Using API_BASE_URL from api-config;
      console.log('🌐 VoiceStudio: Requesting voice synthesis...');
      
      // Use the voice training API to synthesize with the created voice
      const response = await fetch(`${API_BASE_URL}/api/voice-lab/synthesize-voice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: sampleText,
          voice_id: localStorage.getItem('voiceStudio_lastJobId'),
          provider: voiceData.provider,
          gender: voiceData.gender,
          accent: voiceData.accent,
          language: voiceData.language
        })
      });
      
      console.log('📋 VoiceStudio: Synthesis parameters:', {
        provider: voiceData.provider,
        gender: voiceData.gender,
        accent: voiceData.accent,
        language: voiceData.language
      });
      
      if (response.ok) {
        // Check if response is JSON (base64 encoded) or binary
        const contentType = response.headers.get('content-type') || '';
        
        if (contentType.includes('application/json')) {
          // Handle JSON response with base64 audio
          const jsonResponse = await response.json();
          const base64Audio = jsonResponse.audio;
          
          if (base64Audio) {
            console.log('🎵 VoiceStudio: Converting base64 audio to blob...');
            const audioData = atob(base64Audio);
            const audioArray = new Uint8Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
              audioArray[i] = audioData.charCodeAt(i);
            }
            
            const audioBlob = new Blob([audioArray], { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            setCreatedVoiceAudioUrl(audioUrl);
            
            console.log('✅ VoiceStudio: Voice synthesis successful, playing...');
            
            // Stop any existing audio
            if (audioRef.current) {
              audioRef.current.pause();
              audioRef.current.currentTime = 0;
            }
            
            const audio = new Audio(audioUrl);
            audioRef.current = audio;
            
            audio.onended = () => {
              setIsPlaying(false);
              console.log('⏹️ VoiceStudio: Voice playback ended');
            };
            
            audio.play();
            setIsPlaying(true);
          } else {
            console.error('❌ VoiceStudio: No audio data in response');
          }
        } else {
          // Handle binary response
          const audioBlob = await response.blob();
          const audioUrl = URL.createObjectURL(audioBlob);
          setCreatedVoiceAudioUrl(audioUrl);
          
          console.log('✅ VoiceStudio: Voice synthesis successful, playing...');
          
          // Stop any existing audio
          if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
          }
          
          const audio = new Audio(audioUrl);
          audioRef.current = audio;
          
          audio.onended = () => {
            setIsPlaying(false);
            console.log('⏹️ VoiceStudio: Voice playback ended');
          };
          
          audio.play();
          setIsPlaying(true);
        }
      } else {
        console.error('❌ VoiceStudio: Voice synthesis failed:', response.statusText);
      }
    } catch (error) {
      console.error('❌ VoiceStudio: Error testing created voice:', error);
    }
  };

  const startTraining = async () => {
    console.log('🚀 VoiceStudio: Starting voice training process...');
    console.log('📋 VoiceStudio: Training configuration:', {
      name: voiceData.name,
      provider: voiceData.provider,
      language: voiceData.language,
      epochs: voiceData.trainingConfig.epochs,
      batchSize: voiceData.trainingConfig.batchSize,
      learningRate: voiceData.trainingConfig.learningRate,
      hasAudioFile: !!voiceData.audioFile,
      hasRecordedAudio: !!voiceData.recordedAudio,
      selectedDataset: voiceData.selectedDataset
    });
    
    setIsTraining(true);
    setTrainingProgress(0);
    console.log('⏱️ VoiceStudio: Training state initialized');
    
    // Clear any existing training interval
    if (trainingIntervalRef.current) {
      clearInterval(trainingIntervalRef.current);
      console.log('🔄 VoiceStudio: Cleared existing training interval');
    }
    
    // Simulate training progress
    const interval = setInterval(() => {
      setTrainingProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          trainingIntervalRef.current = null;
          setIsTraining(false);
          goToStep('preview', 'training completed');
          console.log('🎉 VoiceStudio: Training simulation completed (100%)');
          return 100;
        }
        const newProgress = prev + 2;
        if (newProgress % 20 === 0) {
          console.log(`📊 VoiceStudio: Training progress: ${newProgress}%`);
        }
        return newProgress;
      });
    }, 200);
    
    // Store interval reference for cleanup
    trainingIntervalRef.current = interval;
    
    try {
      // Using API_BASE_URL from api-config;
      console.log('🌐 VoiceStudio: API endpoint:', `${API_BASE_URL}/api/voice-lab/voice/train`);
      
      const requestPayload = {
        voiceData,
        dataset: voiceData.selectedDataset,
        config: voiceData.trainingConfig
      };
      console.log('📤 VoiceStudio: Sending training request:', requestPayload);
      console.log('🔍 VoiceStudio: Provider being sent:', voiceData.provider);
      
      // Call backend API to start voice training
      const response = await fetch(`${API_BASE_URL}/api/voice-lab/voice/train`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestPayload)
      });
      
      console.log('📥 VoiceStudio: API response status:', response.status, response.statusText);
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ VoiceStudio: API request successful!');
        console.log('📋 VoiceStudio: Training job details:', {
          jobId: result.job_id,
          status: result.status,
          provider: result.provider,
          voiceName: result.voice_name,
          estimatedTime: result.estimated_time,
          progressUrl: result.progress_url
        });
        
        // Store job info for monitoring
        if (result.job_id) {
          console.log('💾 VoiceStudio: Storing job ID for progress tracking:', result.job_id);
          localStorage.setItem('voiceStudio_lastJobId', result.job_id);
        }
        
        // Don't call onVoiceCreated here - it closes the modal!
        // The voice is only "created" when user clicks "Create Voice" in preview
        console.log('✅ VoiceStudio: Training job started successfully, continuing to show progress');
      } else {
        const errorData = await response.text();
        console.error('❌ VoiceStudio: API request failed:', {
          status: response.status,
          statusText: response.statusText,
          body: errorData
        });
      }
    } catch (error) {
      console.error('❌ VoiceStudio: Training error:', error);
      console.log('🔍 VoiceStudio: Error details:', {
        message: error.message,
        type: error.constructor.name,
        stack: error.stack?.split('\n').slice(0, 3)
      });
      setIsTraining(false);
      if (trainingIntervalRef.current) {
        clearInterval(trainingIntervalRef.current);
        trainingIntervalRef.current = null;
      }
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'method':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-2">Choose Creation Method</h3>
              <p className="text-gray-600">How would you like to create your voice?</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => {
                  console.log('📁 VoiceStudio: User selected "Upload Audio" method');
                  goToStep('upload', 'user selected upload method');
                }}
                className="p-6 border-2 border-border rounded-lg hover:border-primary transition-colors text-left"
              >
                <Upload className="w-8 h-8 text-indigo-600 mb-3" />
                <h4 className="font-semibold mb-2">Upload Audio Sample</h4>
                <p className="text-sm text-gray-600">
                  Clone a voice using 3-30 seconds of clean audio
                </p>
              </button>
              
              <button
                onClick={() => {
                  console.log('🎙️ VoiceStudio: User selected "Record Audio" method');
                  goToStep('record', 'user selected record method');
                }}
                className="p-6 border-2 border-border rounded-lg hover:border-primary transition-colors text-left"
              >
                <Mic className="w-8 h-8 text-indigo-600 mb-3" />
                <h4 className="font-semibold mb-2">Record New Sample</h4>
                <p className="text-sm text-gray-600">
                  Record your voice directly in the browser
                </p>
              </button>
              
              <button
                onClick={() => {
                  console.log('📊 VoiceStudio: User selected "Use Dataset" method');
                  goToStep('dataset', 'user selected dataset method');
                }}
                className="p-6 border-2 border-border rounded-lg hover:border-primary transition-colors text-left"
              >
                <Database className="w-8 h-8 text-indigo-600 mb-3" />
                <h4 className="font-semibold mb-2">Use Training Dataset</h4>
                <p className="text-sm text-gray-600">
                  Train from African language speech datasets
                </p>
              </button>
              
              <button
                onClick={() => {
                  console.log('🤖 VoiceStudio: User selected "AI Generate" method');
                  goToStep('configure', 'user selected AI generate method');
                }}
                className="p-6 border-2 border-border rounded-lg hover:border-primary transition-colors text-left"
              >
                <Brain className="w-8 h-8 text-indigo-600 mb-3" />
                <h4 className="font-semibold mb-2">AI Voice Generation</h4>
                <p className="text-sm text-gray-600">
                  Generate synthetic voice from text description
                </p>
              </button>
            </div>
          </div>
        );

      case 'upload':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-2">Upload Audio Sample</h3>
              <p className="text-gray-600">Upload a clean 3-30 second audio file</p>
            </div>
            
            <div 
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-border rounded-lg p-12 text-center hover:border-primary transition-colors cursor-pointer"
            >
              <Upload className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-lg font-medium mb-2">Click to upload audio file</p>
              <p className="text-gray-600">Supports WAV, MP3, M4A files</p>
              
              {voiceData.audioFile && (
                <div className="mt-4 p-3 bg-primary/10 rounded-md">
                  <FileAudio className="w-5 h-5 text-indigo-600 inline mr-2" />
                  <span className="text-sm font-medium">{voiceData.audioFile.name}</span>
                </div>
              )}
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleFileUpload}
              className="hidden"
            />
            
            <div className="bg-muted/50 p-4 rounded-lg">
              <h4 className="font-medium mb-2">Tips for best results:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Use clear, noise-free audio</li>
                <li>• 22kHz sample rate recommended</li>
                <li>• Natural speech works better than reading</li>
                <li>• Consistent tone and emotion</li>
              </ul>
            </div>
          </div>
        );

      case 'record':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-2">Record Audio Sample</h3>
              <p className="text-gray-600">Record 10-30 seconds of natural speech</p>
            </div>
            
            <div className="text-center">
              <div className="w-32 h-32 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`w-20 h-20 rounded-full flex items-center justify-center transition-colors ${
                    isRecording 
                      ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse' 
                      : 'bg-indigo-600 hover:bg-primary/90 text-primary-foreground'
                  }`}
                >
                  {isRecording ? <Square className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
                </button>
              </div>
              
              <p className="text-lg font-medium mb-2">
                {isRecording ? 'Recording...' : 'Click to start recording'}
              </p>
              
              {voiceData.recordedAudio && (
                <div className="mt-6 p-4 bg-primary/10 rounded-md inline-block">
                  <div className="flex items-center gap-3">
                    <FileAudio className="w-5 h-5 text-indigo-600" />
                    <span className="text-sm font-medium">Recording complete</span>
                    <div className="flex gap-2">
                      <button
                        onClick={isPlaying ? stopPlayback : playRecordedAudio}
                        className="flex items-center gap-1 px-3 py-1 bg-indigo-600 hover:bg-primary/90 text-primary-foreground rounded text-sm transition-colors"
                      >
                        {isPlaying ? (
                          <>
                            <Pause className="w-4 h-4" />
                            Stop
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4" />
                            Play
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => {
                          console.log('🗑️ VoiceStudio: User requested to re-record audio');
                          setVoiceData(prev => ({ ...prev, recordedAudio: undefined }));
                          setRecordedAudioUrl(null);
                          setIsPlaying(false);
                        }}
                        className="flex items-center gap-1 px-3 py-1 bg-muted hover:bg-muted/80 text-gray-600 rounded text-sm transition-colors"
                      >
                        <Mic className="w-4 h-4" />
                        Re-record
                      </button>
                    </div>
                  </div>
                  {recordedAudioUrl && (
                    <div className="mt-2 text-xs text-gray-600">
                      Audio ready for playback
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="bg-muted/50 p-4 rounded-lg">
              <h4 className="font-medium mb-2">Recording guidelines:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Speak naturally in a quiet environment</li>
                <li>• Use your normal speaking voice</li>
                <li>• Say a few sentences about yourself</li>
                <li>• Avoid background noise</li>
              </ul>
            </div>
          </div>
        );

      case 'dataset':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-2">Select Training Dataset</h3>
              <p className="text-gray-600">Choose from curated African language datasets</p>
            </div>
            
            <div className="grid grid-cols-1 gap-4 max-h-96 overflow-y-auto">
              {availableDatasets.map((dataset) => (
                <button
                  key={dataset.id}
                  onClick={() => {
                    console.log('📋 VoiceStudio: Dataset selected:', {
                      id: dataset.id,
                      name: dataset.name,
                      language: dataset.language,
                      duration: dataset.duration,
                      speakers: dataset.speakers
                    });
                    setVoiceData(prev => ({ ...prev, selectedDataset: dataset.id }));
                  }}
                  className={`p-4 border-2 rounded-lg text-left transition-colors ${
                    voiceData.selectedDataset === dataset.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold mb-1">{dataset.name}</h4>
                      <p className="text-sm text-gray-600 mb-2">{dataset.description}</p>
                      
                      <div className="flex items-center gap-4 text-xs text-gray-600">
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {dataset.speakers} speakers
                        </span>
                        <span>{dataset.duration}</span>
                        <span>{dataset.language}</span>
                      </div>
                      
                      <div className="mt-2">
                        <span className="text-xs bg-muted px-2 py-1 rounded">
                          {dataset.source}
                        </span>
                      </div>
                    </div>
                    
                    <Database className="w-5 h-5 text-indigo-600 ml-4" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        );

      case 'configure':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-2">Voice Configuration</h3>
              <p className="text-gray-600">Set up your voice parameters</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium mb-2">Voice Name</label>
                <input
                  type="text"
                  value={voiceData.name}
                  onChange={(e) => setVoiceData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:border-primary"
                  placeholder="My Custom Voice"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Gender</label>
                <select
                  value={voiceData.gender}
                  onChange={(e) => setVoiceData(prev => ({ ...prev, gender: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:border-primary"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="neutral">Neutral</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Language</label>
                <select
                  value={voiceData.language}
                  onChange={(e) => setVoiceData(prev => ({ ...prev, language: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:border-primary"
                >
                  <option value="en">English</option>
                  <option value="twi">Twi</option>
                  <option value="ga">Ga</option>
                  <option value="ewe">Ewe</option>
                  <option value="hausa">Hausa</option>
                  <option value="yoruba">Yoruba</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Accent</label>
                <input
                  type="text"
                  value={voiceData.accent}
                  onChange={(e) => setVoiceData(prev => ({ ...prev, accent: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:border-primary"
                  placeholder="Ghanaian, Nigerian, etc."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Provider</label>
                <select
                  value={voiceData.provider}
                  onChange={(e) => {
                    const selectedProvider = e.target.value;
                    console.log('🔄 VoiceStudio: Provider changed:', {
                      from: voiceData.provider,
                      to: selectedProvider,
                      isLocal: ['xtts', 'coqui_tts', 'f5_tts', 'melotts', 'openvoice'].includes(selectedProvider)
                    });
                    setVoiceData(prev => ({ ...prev, provider: selectedProvider as any }));
                  }}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:border-primary"
                >
                  <option value="xtts">XTTS Twi v1 (Voice Cloning) ✅</option>
                  <option value="coqui_tts">Coqui TTS (Local) ✅</option>
                  <option value="f5_tts">F5-TTS (Local)</option>
                  <option value="melotts">MeloTTS (Local)</option>
                  <option value="openvoice">OpenVoice (Local)</option>
                  <option value="elevenlabs">ElevenLabs (External)</option>
                  <option value="meta_mms">Meta MMS (External)</option>
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <textarea
                value={voiceData.description}
                onChange={(e) => setVoiceData(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:border-primary"
                rows={3}
                placeholder="Describe the voice characteristics and best use cases..."
              />
            </div>

            <div className="bg-muted/50 p-4 rounded-lg">
              <h4 className="font-medium mb-3">Advanced Training Settings</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Epochs</label>
                  <input
                    type="number"
                    value={voiceData.trainingConfig.epochs}
                    onChange={(e) => setVoiceData(prev => ({
                      ...prev,
                      trainingConfig: { ...prev.trainingConfig, epochs: parseInt(e.target.value) }
                    }))}
                    className="w-full px-2 py-1 text-sm border border-border rounded bg-background"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Batch Size</label>
                  <input
                    type="number"
                    value={voiceData.trainingConfig.batchSize}
                    onChange={(e) => setVoiceData(prev => ({
                      ...prev,
                      trainingConfig: { ...prev.trainingConfig, batchSize: parseInt(e.target.value) }
                    }))}
                    className="w-full px-2 py-1 text-sm border border-border rounded bg-background"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Learning Rate</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={voiceData.trainingConfig.learningRate}
                    onChange={(e) => setVoiceData(prev => ({
                      ...prev,
                      trainingConfig: { ...prev.trainingConfig, learningRate: parseFloat(e.target.value) }
                    }))}
                    className="w-full px-2 py-1 text-sm border border-border rounded bg-background"
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 'training':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-2">Voice Training</h3>
              <p className="text-gray-600">
                {isTraining ? 'Training your voice model...' : 'Ready to start training'}
              </p>
            </div>
            
            <div className="max-w-md mx-auto">
              <div className="bg-muted/50 p-6 rounded-lg">
                <Brain className="w-12 h-12 text-indigo-600 mx-auto mb-4" />
                
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Training Progress</span>
                      <span>{trainingProgress}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div 
                        className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${trainingProgress}%` }}
                      />
                    </div>
                  </div>
                  
                  {!isTraining && trainingProgress === 0 && (
                    <button
                      onClick={startTraining}
                      className="w-full bg-indigo-600 hover:bg-primary/90 text-primary-foreground py-2 px-4 rounded-md font-medium"
                    >
                      Start Training
                    </button>
                  )}
                  
                  {isTraining && (
                    <div className="text-center text-sm text-gray-600">
                      <p>This may take several minutes...</p>
                      <p className="mt-1">Estimated time: {Math.ceil((100 - trainingProgress) / 5)} minutes</p>
                    </div>
                  )}
                  
                  {trainingProgress === 100 && !isTraining && (
                    <div className="text-center">
                      <p className="text-green-600 font-medium mb-2">Training Complete!</p>
                      <button
                        onClick={() => setCurrentStep('preview')}
                        className="w-full bg-indigo-600 hover:bg-primary/90 text-primary-foreground py-2 px-4 rounded-md font-medium"
                      >
                        Preview Voice
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        );

      case 'preview':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-2">Voice Preview</h3>
              <p className="text-gray-600">Test your newly created voice</p>
            </div>
            
            <div className="max-w-2xl mx-auto">
              <div className="bg-muted/50 p-6 rounded-lg mb-6">
                <h4 className="font-semibold mb-3">Voice Details</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Name:</span>
                    <span className="ml-2 font-medium">{voiceData.name}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Language:</span>
                    <span className="ml-2 font-medium">{voiceData.language}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Gender:</span>
                    <span className="ml-2 font-medium">{voiceData.gender}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Provider:</span>
                    <span className="ml-2 font-medium">{voiceData.provider}</span>
                  </div>
                </div>
              </div>
              
              <div className="bg-card border border-border p-6 rounded-lg">
                <h4 className="font-semibold mb-3">Test Voice</h4>
                <textarea
                  id="voice-test-text"
                  className="w-full px-3 py-2 border border-border rounded-md bg-background focus:outline-none focus:border-primary mb-4"
                  rows={3}
                  placeholder="Enter text to test your voice..."
                  defaultValue="Akwaaba! Welcome to Kasa AI. This is my custom voice speaking in both English and Twi."
                />
                
                <div className="flex items-center gap-3">
                  {!isPlaying ? (
                    <>
                      <button
                        onClick={() => {
                          const textArea = document.getElementById('voice-test-text') as HTMLTextAreaElement;
                          const testText = textArea?.value || "Hello, this is a test of my created voice.";
                          console.log('🎭 VoiceStudio: Testing voice with custom text');
                          playCreatedVoice(testText);
                        }}
                        className="flex items-center gap-2 bg-indigo-600 hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-md transition-colors"
                      >
                        <Play className="w-4 h-4" />
                        Test Voice
                      </button>
                      
                      <button 
                        onClick={() => {
                          console.log('🎭 VoiceStudio: Testing voice with default sample');
                          playCreatedVoice("Akwaaba! Welcome to Kasa AI. This is my custom voice.");
                        }}
                        className="flex items-center gap-2 bg-muted hover:bg-muted/80 px-4 py-2 rounded-md transition-colors"
                      >
                        <Volume2 className="w-4 h-4" />
                        Quick Test
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => {
                        console.log('⏹️ VoiceStudio: User clicked stop button');
                        stopVoicePlayback();
                      }}
                      className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md transition-colors"
                    >
                      <StopCircle className="w-4 h-4" />
                      Stop Playing
                    </button>
                  )}
                  
                  <button className="flex items-center gap-2 bg-muted hover:bg-muted/80 px-4 py-2 rounded-md transition-colors">
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 'method':
        return true;
      case 'upload':
        return !!voiceData.audioFile;
      case 'record':
        return !!voiceData.recordedAudio;
      case 'dataset':
        return !!voiceData.selectedDataset;
      case 'configure':
        return !!voiceData.name && !!voiceData.language;
      case 'training':
        return trainingProgress === 100;
      case 'preview':
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    console.log(`➡️ VoiceStudio: Next button clicked from step: ${currentStep}`);
    
    // Smart navigation based on current step and selected method
    switch (currentStep) {
      case 'method':
        // This case shouldn't happen since method selection bypasses Next button
        console.log('⚠️ VoiceStudio: Unexpected Next from method step');
        break;
      
      case 'upload':
        goToStep('configure', 'completed upload, going to configure');
        break;
      
      case 'record':
        goToStep('configure', 'completed recording, going to configure');
        break;
      
      case 'dataset':
        goToStep('configure', 'selected dataset, going to configure');
        break;
      
      case 'configure':
        goToStep('training', 'configured voice, starting training');
        break;
      
      case 'training':
        goToStep('preview', 'training complete, going to preview');
        break;
      
      default:
        console.log('⚠️ VoiceStudio: Cannot proceed - already at last step or unknown step');
    }
  };

  const handleBack = () => {
    console.log(`⬅️ VoiceStudio: Back button clicked from step: ${currentStep}`);
    
    // Smart back navigation
    switch (currentStep) {
      case 'upload':
      case 'record':
      case 'dataset':
        goToStep('method', 'going back to method selection');
        break;
      
      case 'configure':
        // Go back based on what method was selected
        if (voiceData.audioFile) {
          goToStep('upload', 'going back to upload');
        } else if (voiceData.recordedAudio) {
          goToStep('record', 'going back to recording');
        } else if (voiceData.selectedDataset) {
          goToStep('dataset', 'going back to dataset');
        } else {
          goToStep('method', 'going back to method selection');
        }
        break;
      
      case 'training':
        // Reset training state when going back
        console.log('🔄 VoiceStudio: Resetting training state');
        if (trainingIntervalRef.current) {
          clearInterval(trainingIntervalRef.current);
          trainingIntervalRef.current = null;
        }
        setIsTraining(false);
        setTrainingProgress(0);
        goToStep('configure', 'going back to configure');
        break;
      
      case 'preview':
        // Reset training progress when going back from preview
        setTrainingProgress(0);
        setIsTraining(false);
        goToStep('training', 'going back to training');
        break;
      
      default:
        console.log('⚠️ VoiceStudio: Cannot go back - already at first step or unknown step');
    }
  };

  const handleFinish = () => {
    console.log('🏁 VoiceStudio: Finish button clicked - Creating final voice object');
    
    // Create the voice object
    const newVoice = {
      id: `voice-${Date.now()}`,
      name: voiceData.name,
      description: voiceData.description,
      language: voiceData.language,
      accent: voiceData.accent,
      gender: voiceData.gender,
      provider: voiceData.provider.toUpperCase(),
      isCustom: true,
      isCloned: !!voiceData.audioFile || !!voiceData.recordedAudio,
      createdAt: new Date().toISOString(),
      rating: 0,
      totalUses: 0,
      pricePerMinute: 0.05,
      latency: 300,
      bestFor: [voiceData.language, voiceData.accent],
      capabilities: ['custom', 'cloned']
    };
    
    console.log('✅ VoiceStudio: Voice object created:', newVoice);
    console.log('📤 VoiceStudio: Calling onVoiceCreated callback');
    onVoiceCreated(newVoice);
    console.log('🚪 VoiceStudio: Closing wizard modal');
    onClose();
  };

  if (!isOpen) return null;

  const currentStepIndex = wizardSteps.findIndex(step => step.id === currentStep);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-card border border-border rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div>
            <h2 className="text-xl font-semibold">Create New Voice</h2>
            <p className="text-sm text-gray-600 mt-1">
              Step {currentStepIndex + 1} of {wizardSteps.length}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress */}
        <div className="px-6 py-4 border-b border-border">
          <div className="flex items-center justify-between">
            {wizardSteps.map((step, index) => {
              const Icon = step.icon;
              const isActive = step.id === currentStep;
              const isCompleted = index < currentStepIndex;
              
              return (
                <div key={step.id} className="flex items-center">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                    isActive 
                      ? 'border-primary bg-indigo-600 text-primary-foreground' 
                      : isCompleted 
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-muted-foreground/30 text-gray-600'
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="ml-2 hidden md:block">
                    <div className={`text-sm font-medium ${isActive ? 'text-primary' : 'text-gray-600'}`}>
                      {step.title}
                    </div>
                  </div>
                  {index < wizardSteps.length - 1 && (
                    <div className={`w-8 h-0.5 mx-4 ${isCompleted ? 'bg-primary' : 'bg-muted-foreground/30'}`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          {renderStepContent()}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-border">
          <button
            onClick={handleBack}
            disabled={currentStepIndex === 0}
            className="flex items-center gap-2 px-4 py-2 text-sm border border-border rounded-md hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>
          
          <div className="flex items-center gap-3">
            {currentStep === 'preview' ? (
              <button
                onClick={handleFinish}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-primary/90 text-primary-foreground px-6 py-2 rounded-md font-medium"
              >
                Create Voice
              </button>
            ) : (
              <button
                onClick={handleNext}
                disabled={!canProceed()}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};