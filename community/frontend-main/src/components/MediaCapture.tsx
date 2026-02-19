import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Mic,
  MicOff,
  Camera,
  CameraOff,
  Play,
  Square,
  Download,
  Upload,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { getDeviceCapabilities, storeOfflineSubmission } from '@/utils/pwa';

interface MediaCaptureProps {
  type: 'audio' | 'video';
  onCapture?: (blob: Blob, metadata: any) => void;
  language?: string;
  maxDuration?: number; // in seconds
}

const MediaCapture = ({
  type = 'audio',
  onCapture,
  language = 'Unknown',
  maxDuration = 300 // 5 minutes default
}: MediaCaptureProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deviceCapabilities, setDeviceCapabilities] = useState(getDeviceCapabilities());

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    checkPermissions();
    return () => {
      stopRecording();
      cleanupStream();
    };
  }, []);

  const checkPermissions = async () => {
    try {
      const constraints = type === 'audio'
        ? { audio: true }
        : { video: true, audio: true };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      setHasPermission(true);

      // Clean up test stream
      stream.getTracks().forEach(track => track.stop());
    } catch (err: any) {
      setHasPermission(false);
      setError(err.message || 'Permission denied');
    }
  };

  const startRecording = async () => {
    try {
      setError(null);

      const constraints = type === 'audio'
        ? {
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              sampleRate: 44100
            }
          }
        : {
            video: {
              width: { ideal: 1280 },
              height: { ideal: 720 },
              facingMode: 'user'
            },
            audio: {
              echoCancellation: true,
              noiseSuppression: true
            }
          };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      // Show video preview for video recording
      if (type === 'video' && videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      // Set up MediaRecorder
      const mimeType = type === 'audio'
        ? 'audio/webm;codecs=opus'
        : 'video/webm;codecs=vp8,opus';

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported(mimeType) ? mimeType : undefined
      });

      const chunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, {
          type: type === 'audio' ? 'audio/webm' : 'video/webm'
        });
        setRecordedBlob(blob);
        cleanupStream();
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(1000); // Capture data every second
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= maxDuration) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);

    } catch (err: any) {
      setError(err.message || 'Failed to start recording');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }

    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const cleanupStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleDownload = () => {
    if (!recordedBlob) return;

    const url = URL.createObjectURL(recordedBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${type}-recording-${Date.now()}.webm`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleSubmit = async () => {
    if (!recordedBlob) return;

    const metadata = {
      type,
      language,
      duration: recordingTime,
      timestamp: Date.now(),
      size: recordedBlob.size,
      mimeType: recordedBlob.type
    };

    try {
      // Store offline if not connected
      if (!navigator.onLine) {
        await storeOfflineSubmission({
          type,
          blob: recordedBlob,
          metadata
        });
        alert('Recording saved offline. It will be uploaded when you\'re back online.');
      } else {
        // Call parent handler
        if (onCapture) {
          onCapture(recordedBlob, metadata);
        }
      }

      // Reset state
      setRecordedBlob(null);
      setRecordingTime(0);
    } catch (error) {
      console.error('Failed to submit recording:', error);
      setError('Failed to submit recording');
    }
  };

  if (hasPermission === null) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Checking device permissions...</p>
        </CardContent>
      </Card>
    );
  }

  if (hasPermission === false) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-5 w-5" />
            Permission Required
          </CardTitle>
          <CardDescription>
            Please allow {type} access to record your contribution.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {error || `${type === 'audio' ? 'Microphone' : 'Camera'} access is needed to record your contribution.`}
            </p>
            <Button onClick={checkPermissions} className="w-full">
              Grant Permission
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {type === 'audio' ? <Mic className="h-5 w-5" /> : <Camera className="h-5 w-5" />}
          {type === 'audio' ? 'Audio Recording' : 'Video Recording'}
        </CardTitle>
        <CardDescription>
          Record your contribution in {language}
          {!deviceCapabilities.isMobile && ' (Mobile optimized)'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Device Info */}
        <div className="flex gap-2 flex-wrap">
          {deviceCapabilities.isMobile && (
            <Badge variant="secondary">Mobile Device</Badge>
          )}
          {deviceCapabilities.hasCamera && type === 'video' && (
            <Badge variant="outline">Camera Available</Badge>
          )}
          {deviceCapabilities.hasMicrophone && (
            <Badge variant="outline">Microphone Available</Badge>
          )}
        </div>

        {/* Video Preview */}
        {type === 'video' && (
          <div className="relative">
            <video
              ref={videoRef}
              className="w-full max-w-md mx-auto rounded-lg bg-black"
              autoPlay
              muted
              playsInline
            />
            {isRecording && (
              <div className="absolute top-4 left-4 bg-red-500 text-white px-2 py-1 rounded text-sm font-medium flex items-center gap-1">
                <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                REC
              </div>
            )}
          </div>
        )}

        {/* Recording Controls */}
        <div className="text-center space-y-4">
          {/* Timer */}
          {(isRecording || recordingTime > 0) && (
            <div className="text-2xl font-mono font-bold">
              {formatTime(recordingTime)}
              {maxDuration && (
                <span className="text-sm text-muted-foreground ml-2">
                  / {formatTime(maxDuration)}
                </span>
              )}
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
              {error}
            </div>
          )}

          {/* Recording Button */}
          {!recordedBlob && (
            <Button
              onClick={isRecording ? stopRecording : startRecording}
              size="lg"
              variant={isRecording ? "destructive" : "default"}
              className="w-full max-w-xs"
            >
              {isRecording ? (
                <>
                  <Square className="h-4 w-4 mr-2" />
                  Stop Recording
                </>
              ) : (
                <>
                  {type === 'audio' ? <Mic className="h-4 w-4 mr-2" /> : <Camera className="h-4 w-4 mr-2" />}
                  Start Recording
                </>
              )}
            </Button>
          )}

          {/* Playback and Submit */}
          {recordedBlob && (
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-2 text-green-600">
                <CheckCircle className="h-5 w-5" />
                <span>Recording completed ({formatTime(recordingTime)})</span>
              </div>

              {/* Audio Playback */}
              {type === 'audio' && (
                <audio controls className="w-full max-w-md mx-auto">
                  <source src={URL.createObjectURL(recordedBlob)} type="audio/webm" />
                  Your browser does not support audio playback.
                </audio>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2 justify-center">
                <Button variant="outline" onClick={handleDownload}>
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
                <Button onClick={handleSubmit}>
                  <Upload className="h-4 w-4 mr-2" />
                  Submit
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setRecordedBlob(null);
                    setRecordingTime(0);
                    setError(null);
                  }}
                >
                  Re-record
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="text-xs text-muted-foreground text-center mt-4 p-3 bg-muted/30 rounded">
          <p><strong>Tips:</strong></p>
          <p>• Find a quiet environment • Speak clearly • Hold device steady</p>
          <p>• Maximum duration: {formatTime(maxDuration)}</p>
        </div>
      </CardContent>
    </Card>
  );
};

export default MediaCapture;