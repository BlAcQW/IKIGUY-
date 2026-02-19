import React, { useState } from 'react';
import { GitCompare, Info, Zap, Rocket, Target } from 'lucide-react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { API_BASE_URL } from '@/config/api-config';

/**
 * Speech-to-Speech Real-Time Comparison
 *
 * Provides side-by-side comparison of Custom VoicePipeline vs HF Speech-to-Speech
 * using FastRTC for hands-free, low-latency voice conversations.
 *
 * Features:
 * - Automatic turn-taking (speaks when you pause)
 * - Barge-in support (interrupt anytime)
 * - <50ms latency
 * - Side-by-side real-time testing
 */
const SpeechToSpeech: React.FC = () => {
  const [assistantId, setAssistantId] = useState('default-assistant');

  // Construct FastRTC iframe URLs
  const customUrl = `${API_BASE_URL}/speech-to-speech/webrtc/custom`;
  const hfUrl = `${API_BASE_URL}/speech-to-speech/webrtc/hf`;

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      <DashboardSidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <GitCompare className="w-8 h-8 text-indigo-600" />
                Speech-to-Speech Comparison
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1 flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Real-time hands-free testing with FastRTC
              </p>
            </div>
          </div>
        </div>

        {/* Info Banner */}
        <div className="bg-indigo-50 dark:bg-indigo-900/20 border-b border-indigo-200 dark:border-indigo-800 px-6 py-3">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-indigo-900 dark:text-indigo-100">
              <p className="font-semibold mb-1">How to use:</p>
              <ul className="list-disc list-inside space-y-1 text-indigo-800 dark:text-indigo-200">
                <li><strong>Click "Start"</strong> on either implementation to begin</li>
                <li><strong>Speak naturally</strong> - the system responds automatically when you pause</li>
                <li><strong>Compare in real-time</strong> - test both implementations side-by-side</li>
                <li><strong>Barge-in supported</strong> - you can interrupt the assistant anytime</li>
                <li><strong>Ultra-low latency</strong> - &lt;50ms audio chunks for smooth conversation</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Main Content - Side-by-Side FastRTC Interfaces */}
        <div className="flex-1 overflow-hidden p-6">
          <div className="grid md:grid-cols-2 gap-6 h-full">
            {/* Custom VoicePipeline */}
            <div className="flex flex-col bg-white dark:bg-gray-900 rounded-lg border-2 border-blue-300 dark:border-blue-700 shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 border-b border-blue-200 dark:border-blue-700">
                <h2 className="text-xl font-bold flex items-center gap-2 text-blue-900 dark:text-blue-100">
                  <Rocket className="w-6 h-6" />
                  Custom VoicePipeline
                </h2>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  Our optimized implementation • 20+ TTS providers • Voice cloning
                </p>
              </div>
              <div className="flex-1 relative">
                <iframe
                  src={customUrl}
                  className="absolute inset-0 w-full h-full border-0"
                  allow="microphone *; camera *"
                  title="Custom VoicePipeline"
                />
              </div>
            </div>

            {/* HF Speech-to-Speech */}
            <div className="flex flex-col bg-white dark:bg-gray-900 rounded-lg border-2 border-green-300 dark:border-green-700 shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 border-b border-green-200 dark:border-green-700">
                <h2 className="text-xl font-bold flex items-center gap-2 text-green-900 dark:text-green-100">
                  <Target className="w-6 h-6" />
                  HF Speech-to-Speech
                </h2>
                <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                  HuggingFace reference • Modular architecture • Open source
                </p>
              </div>
              <div className="flex-1 relative">
                <iframe
                  src={hfUrl}
                  className="absolute inset-0 w-full h-full border-0"
                  allow="microphone *; camera *"
                  title="HF Speech-to-Speech"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Feature Comparison Footer */}
        <div className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 px-6 py-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Turn-taking</p>
              <p className="text-sm font-semibold text-green-600 dark:text-green-400">✓ Automatic</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Latency</p>
              <p className="text-sm font-semibold text-green-600 dark:text-green-400">&lt;50ms</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Barge-in</p>
              <p className="text-sm font-semibold text-green-600 dark:text-green-400">✓ Supported</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">VAD</p>
              <p className="text-sm font-semibold text-blue-600 dark:text-blue-400">Silero v5</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Hands-free</p>
              <p className="text-sm font-semibold text-green-600 dark:text-green-400">✓ Yes</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpeechToSpeech;
