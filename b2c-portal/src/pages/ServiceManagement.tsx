/**
 * Service Management Page
 *
 * Admin page for starting/stopping TTS and AI services
 */

import React, { useState, useEffect } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';

interface Service {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'unknown';
  type: 'docker' | 'systemd';
  gpu_memory?: string;
  description: string;
}

export const ServiceManagement: React.FC = () => {
  const [services, setServices] = useState<Service[]>([
    {
      id: 'moshi',
      name: 'Moshi (Kyutai)',
      status: 'unknown',
      type: 'docker',
      description: 'Real-time conversational AI - Requires ~19GB GPU',
    },
    {
      id: 'coqui',
      name: 'Coqui XTTS',
      status: 'unknown',
      type: 'docker',
      description: 'Voice cloning TTS - Requires ~4GB GPU',
    },
    {
      id: 'melotts',
      name: 'MeloTTS',
      status: 'unknown',
      type: 'docker',
      description: 'Fast multilingual TTS - Requires ~2GB GPU',
    },
    {
      id: 'openvoice',
      name: 'OpenVoice',
      status: 'unknown',
      type: 'docker',
      description: 'Voice cloning with emotion - Requires ~4GB GPU',
    },
    {
      id: 'kasaai-core-backend',
      name: 'Core Backend',
      status: 'unknown',
      type: 'systemd',
      description: 'Main API backend - Requires ~1.4GB GPU',
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleServiceAction = async (serviceId: string, action: 'start' | 'stop' | 'restart') => {
    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch('/api/services/control', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          service_id: serviceId,
          action: action,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({
          type: 'success',
          text: `${serviceId} ${action} successful`,
        });
        // Refresh service status
        fetchServiceStatus();
      } else {
        setMessage({
          type: 'error',
          text: data.detail || `Failed to ${action} ${serviceId}`,
        });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchServiceStatus = async () => {
    try {
      const response = await fetch('/api/services/status');
      const data = await response.json();

      setServices((prev) =>
        prev.map((service) => ({
          ...service,
          status: data[service.id]?.status || 'unknown',
          gpu_memory: data[service.id]?.gpu_memory,
        }))
      );
    } catch (error) {
      console.error('Failed to fetch service status:', error);
    }
  };

  useEffect(() => {
    fetchServiceStatus();
    // Refresh every 10 seconds
    const interval = setInterval(fetchServiceStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'stopped':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return '✓';
      case 'stopped':
        return '●';
      default:
        return '?';
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <DashboardSidebar />

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Service Management</h1>
            <p className="text-gray-600">
              Manage TTS and AI services. Note: Services share GPU memory (20GB total).
            </p>
          </div>

          {/* Message */}
          {message && (
            <div
              className={`mb-6 p-4 rounded-lg border ${
                message.type === 'success'
                  ? 'bg-green-50 border-green-200 text-green-800'
                  : 'bg-red-50 border-red-200 text-red-800'
              }`}
            >
              {message.text}
            </div>
          )}

          {/* GPU Warning */}
          <div className="mb-6 p-4 bg-yellow-50 border-l-4 border-yellow-400">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-2xl">⚠️</span>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">GPU Memory Constraint</h3>
                <p className="mt-1 text-sm text-yellow-700">
                  Total GPU: 20GB. Moshi requires ~19GB alone. Running Moshi will stop other TTS
                  services automatically. F5-TTS and StyleTTS2 are running on RunPod (separate GPU).
                </p>
              </div>
            </div>
          </div>

          {/* Services Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {services.map((service) => (
              <div key={service.id} className="bg-white rounded-lg border border-gray-200 p-6">
                {/* Service Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{service.name}</h3>
                    <p className="text-sm text-gray-500 mt-1">{service.description}</p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                      service.status
                    )}`}
                  >
                    {getStatusIcon(service.status)} {service.status}
                  </span>
                </div>

                {/* GPU Memory */}
                {service.gpu_memory && (
                  <div className="mb-4 text-sm text-gray-600">
                    <span className="font-medium">GPU Memory:</span> {service.gpu_memory}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleServiceAction(service.id, 'start')}
                    disabled={loading || service.status === 'running'}
                    className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium"
                  >
                    Start
                  </button>
                  <button
                    onClick={() => handleServiceAction(service.id, 'stop')}
                    disabled={loading || service.status === 'stopped'}
                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium"
                  >
                    Stop
                  </button>
                  <button
                    onClick={() => handleServiceAction(service.id, 'restart')}
                    disabled={loading}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium"
                  >
                    Restart
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Remote Services */}
          <div className="mt-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Remote Services (RunPod)</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">F5-TTS</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Flow-matching TTS with voice cloning (4 languages)
                </p>
                <div className="flex items-center gap-2 mb-3">
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-300">
                    ✓ Online
                  </span>
                  <span className="text-xs text-gray-500">https://f5tts.ailabsafrica.com</span>
                </div>
                <p className="text-xs text-gray-500">GPU: NVIDIA A40 (46GB) on RunPod</p>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border-2 border-purple-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">StyleTTS2</h3>
                <p className="text-sm text-gray-600 mb-3">
                  Expressive TTS with style transfer and emotion control
                </p>
                <div className="flex items-center gap-2 mb-3">
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-300">
                    ✓ Online
                  </span>
                  <span className="text-xs text-gray-500">https://styletts.ailabsafrica.com</span>
                </div>
                <p className="text-xs text-gray-500">GPU: NVIDIA A40 (46GB) on RunPod</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
