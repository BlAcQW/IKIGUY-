import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { toast } from '@/components/ui/use-toast';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

import {
  Play, Square, RotateCw, Power, Terminal, FileText, Plus, Trash2,
  Edit, Save, Copy, AlertTriangle, CheckCircle, XCircle, Clock,
  MemoryStick, Cpu, HardDrive, Activity, Settings, RefreshCw,
  ChevronDown, ChevronRight, Search, Filter, X, Container
} from 'lucide-react';

interface Service {
  service_name: string;
  display_name: string;
  category: string;
  status: string;
  is_enabled: boolean;
  memory_current?: string;
  memory_limit?: string;
  cpu_usage?: string;
  uptime?: string;
  pid?: number;
  active_since?: string;
  logs: string[];
  can_start: boolean;
  can_stop: boolean;
  can_restart: boolean;
  file_path?: string;
}

interface DockerService {
  id: string;
  name: string;
  status: 'running' | 'stopped' | 'paused' | 'restarting' | 'unknown';
  gpu_memory?: string;
  description: string;
  endpoint?: string;
  port?: number;
}

interface ServiceTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  template?: string;
  variables?: Record<string, string>;
}

// Using API_BASE_URL from api-config;

export default function ServiceManagement() {
  const [services, setServices] = useState<Service[]>([]);
  const [filteredServices, setFilteredServices] = useState<Service[]>([]);
  const [dockerServices, setDockerServices] = useState<DockerService[]>([]);
  const [loading, setLoading] = useState(false);
  const [dockerLoading, setDockerLoading] = useState(false);
  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [showServiceModal, setShowServiceModal] = useState(false);
  const [serviceFile, setServiceFile] = useState<string>('');
  const [editingFile, setEditingFile] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [templates, setTemplates] = useState<ServiceTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [newServiceData, setNewServiceData] = useState({
    service_name: '',
    display_name: '',
    category: 'application',
    description: '',
    content: ''
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'systemd' | 'docker'>('systemd');

  // Fetch services
  const fetchServices = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/services/list`);
      if (!response.ok) throw new Error('Failed to fetch services');
      const data = await response.json();
      setServices(data.services);
      filterServices(data.services, searchTerm, selectedCategory);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch services',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch docker services
  const fetchDockerServices = async () => {
    setDockerLoading(true);
    try {
      // Initialize with known TTS services
      const ttsServices: DockerService[] = [
        {
          id: 'f5tts',
          name: 'F5-TTS',
          status: 'unknown',
          description: 'Flow-matching TTS with voice cloning',
          gpu_memory: '~6-8GB',
          endpoint: 'http://localhost:8006',
          port: 8006,
        },
        {
          id: 'styletts2',
          name: 'StyleTTS2',
          status: 'unknown',
          description: 'Expressive TTS with style transfer',
          gpu_memory: '~4-5GB',
          endpoint: 'http://localhost:8007',
          port: 8007,
        },
        {
          id: 'coqui',
          name: 'Coqui XTTS',
          status: 'unknown',
          description: 'Voice cloning TTS',
          gpu_memory: '~4-6GB',
          endpoint: 'https://coqui.ailabsafrica.com',
          port: 8005,
        },
        {
          id: 'melotts',
          name: 'MeloTTS',
          status: 'unknown',
          description: 'Fast multilingual TTS',
          gpu_memory: '~2-3GB',
          endpoint: 'https://melotts.ailabsafrica.com',
          port: 8001,
        },
        {
          id: 'openvoice',
          name: 'OpenVoice',
          status: 'unknown',
          description: 'Voice cloning with emotion',
          gpu_memory: '~4-6GB',
          endpoint: 'https://openvoice.ailabsafrica.com',
          port: 8003,
        },
        {
          id: 'kokoro',
          name: 'Kokoro TTS',
          status: 'unknown',
          description: 'High-quality TTS synthesis',
          gpu_memory: '~1-2GB',
          endpoint: 'https://kokoro.ailabsafrica.com',
          port: 8010,
        },
        {
          id: 'moshi',
          name: 'Kyutai Moshi',
          status: 'unknown',
          description: 'Real-time conversational AI (Not recommended)',
          gpu_memory: '~21GB',
          endpoint: 'http://localhost:8011',
          port: 8011,
        },
      ];

      // Check status for each service
      const servicesWithStatus = await Promise.all(
        ttsServices.map(async (service) => {
          try {
            // Try to get container status from backend
            const response = await fetch(`${API_BASE_URL}/api/system/docker/${service.id}/status`);
            if (response.ok) {
              const data = await response.json();
              return {
                ...service,
                status: data.status as DockerService['status'],
                gpu_memory: data.gpu_memory,
              };
            }
          } catch (error) {
            console.error(`Failed to fetch status for ${service.id}:`, error);
          }
          return service;
        })
      );

      setDockerServices(servicesWithStatus);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch Docker services',
        variant: 'destructive',
      });
    } finally {
      setDockerLoading(false);
    }
  };

  // Fetch templates
  const fetchTemplates = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/services/templates`);
      if (!response.ok) throw new Error('Failed to fetch templates');
      const data = await response.json();
      setTemplates(data.templates);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  // Docker service actions
  const performDockerAction = async (serviceId: string, action: 'start' | 'stop' | 'restart') => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/system/docker/${serviceId}/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to ${action} ${serviceId}`);
      }

      toast({
        title: 'Success',
        description: `${serviceId} ${action} successful`,
      });

      // Refresh docker services
      setTimeout(() => fetchDockerServices(), 1000);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || `Failed to ${action} service`,
        variant: 'destructive',
      });
    }
  };

  // Service actions
  const performServiceAction = async (serviceName: string, action: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/services/${serviceName}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, service_name: serviceName })
      });
      
      if (!response.ok) throw new Error(`Failed to ${action} service`);
      
      const result = await response.json();
      toast({
        title: 'Success',
        description: `Service ${action} completed`,
      });
      
      // Update service in list
      const updatedServices = services.map(s => 
        s.service_name === serviceName ? result.status : s
      );
      setServices(updatedServices);
      filterServices(updatedServices, searchTerm, selectedCategory);
      
      if (selectedService?.service_name === serviceName) {
        setSelectedService(result.status);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to ${action} service`,
        variant: 'destructive',
      });
    }
  };

  // Fetch service file
  const fetchServiceFile = async (serviceName: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/services/${serviceName}/file`);
      if (!response.ok) throw new Error('Failed to fetch service file');
      const data = await response.json();
      setServiceFile(data.content);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch service file',
        variant: 'destructive',
      });
    }
  };

  // Filter services
  const filterServices = (serviceList: Service[], search: string, category: string) => {
    let filtered = serviceList;
    
    if (category !== 'all') {
      filtered = filtered.filter(s => s.category === category);
    }
    
    if (search) {
      filtered = filtered.filter(s => 
        s.service_name.toLowerCase().includes(search.toLowerCase()) ||
        s.display_name.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    setFilteredServices(filtered);
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'active':
      case 'running':
        return 'bg-green-500';
      case 'inactive':
      case 'stopped':
        return 'bg-gray-500';
      case 'failed':
        return 'bg-red-500';
      case 'restarting':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-400';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'active':
      case 'running':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'inactive':
      case 'stopped':
        return <XCircle className="h-5 w-5 text-gray-500" />;
      case 'failed':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'restarting':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      default:
        return <Activity className="h-5 w-5 text-gray-400" />;
    }
  };

  // Open service modal
  const openServiceModal = (service: Service) => {
    setSelectedService(service);
    fetchServiceFile(service.service_name);
    setShowServiceModal(true);
  };

  // Close service modal
  const closeServiceModal = () => {
    setShowServiceModal(false);
    setSelectedService(null);
    setServiceFile('');
    setEditingFile(false);
  };

  useEffect(() => {
    if (selectedTab === 'systemd') {
      fetchServices();
      fetchTemplates();
    } else {
      fetchDockerServices();
    }
  }, [selectedTab]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        if (selectedTab === 'systemd') {
          fetchServices();
        } else {
          fetchDockerServices();
        }
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, selectedTab]);

  // Auto-refresh Docker services every 10 seconds when Docker tab is active
  useEffect(() => {
    if (selectedTab === 'docker') {
      const interval = setInterval(() => {
        fetchDockerServices();
      }, 10000); // 10 seconds
      return () => clearInterval(interval);
    }
  }, [selectedTab]);

  useEffect(() => {
    filterServices(services, searchTerm, selectedCategory);
  }, [searchTerm, selectedCategory]);

  const categories = ['all', ...new Set(services.map(s => s.category))];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl text-heading">Service Management</h2>
          <p className="text-gray-600 text-body">Monitor and control system services and Docker containers</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={autoRefresh ? 'bg-blue-50' : ''}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </Button>
          <Button
            onClick={() => selectedTab === 'systemd' ? fetchServices() : fetchDockerServices()}
            variant="outline"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          {selectedTab === 'systemd' && (
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Service
            </Button>
          )}
        </div>
      </div>

      {/* Service Type Tabs */}
      <Tabs value={selectedTab} onValueChange={(val) => setSelectedTab(val as 'systemd' | 'docker')}>
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="systemd">
            <Settings className="h-4 w-4 mr-2" />
            SystemD Services
          </TabsTrigger>
          <TabsTrigger value="docker">
            <Container className="h-4 w-4 mr-2" />
            Docker TTS Services
          </TabsTrigger>
        </TabsList>

        {/* SystemD Services Tab */}
        <TabsContent value="systemd" className="space-y-4 mt-6">

        {/* Filters */}
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-600" />
              <Input
                placeholder="Search services..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent>
              {categories.map(cat => (
                <SelectItem key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Services Grid */}
        <Card>
          <CardHeader>
            <CardTitle>Services ({filteredServices.length})</CardTitle>
            <CardDescription>Click on a service to view details and manage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredServices.map(service => (
                <div
                  key={service.service_name}
                  className="border rounded-lg p-4 cursor-pointer transition-all hover:shadow-lg hover:border-blue-300"
                  onClick={() => openServiceModal(service)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(service.status)}
                      <Badge className={`${getStatusColor(service.status)} text-white`}>
                        {service.status}
                      </Badge>
                    </div>
                    {service.is_enabled && (
                      <Badge variant="outline" className="text-xs">
                        Enabled
                      </Badge>
                    )}
                  </div>

                  <div className="space-y-1">
                    <h4 className="font-semibold text-lg text-heading">{service.display_name}</h4>
                    <p className="text-sm text-gray-600">{service.service_name}</p>
                    <p className="text-xs text-gray-600 capitalize">
                      Category: {service.category}
                    </p>
                  </div>

                  {(service.memory_current || service.cpu_usage) && (
                    <div className="mt-3 pt-3 border-t space-y-1">
                      {service.memory_current && (
                        <div className="flex items-center gap-2 text-xs">
                          <MemoryStick className="h-3 w-3" />
                          <span>{service.memory_current}</span>
                        </div>
                      )}
                      {service.cpu_usage && (
                        <div className="flex items-center gap-2 text-xs">
                          <Cpu className="h-3 w-3" />
                          <span>{service.cpu_usage}</span>
                        </div>
                      )}
                      {service.uptime && (
                        <div className="flex items-center gap-2 text-xs">
                          <Clock className="h-3 w-3" />
                          <span>{service.uptime}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        </TabsContent>

        {/* Docker TTS Services Tab */}
        <TabsContent value="docker" className="space-y-4 mt-6">
          {/* GPU Warning */}
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>GPU Memory Management</AlertTitle>
            <AlertDescription>
              Local GPU: 20GB VRAM. Moshi requires ~21GB (not recommended for local use).
              F5-TTS and StyleTTS2 can run on RunPod (46GB NVIDIA A40) as backup.
              Status updates automatically every 10 seconds.
            </AlertDescription>
          </Alert>

          {/* Docker Services Grid */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                TTS Docker Services ({dockerServices.length})
                {selectedTab === 'docker' && (
                  <Badge variant="outline" className="text-xs font-normal">
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Auto-refresh: 10s
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>Manage Docker-based TTS services with GPU allocation. Status updates automatically.</CardDescription>
            </CardHeader>
            <CardContent>
              {dockerLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {dockerServices.map(service => (
                    <div
                      key={service.id}
                      className="border rounded-lg p-3 hover:shadow-lg hover:border-blue-300 transition-all bg-white"
                    >
                      {/* Service Header */}
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-base truncate">{service.name}</h4>
                          <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{service.description}</p>
                        </div>
                        <Badge
                          className={`${getStatusColor(service.status)} text-white ml-2 flex-shrink-0 text-xs`}
                        >
                          {service.status}
                        </Badge>
                      </div>

                      {/* GPU Memory & Port */}
                      <div className="mb-2 space-y-1">
                        {service.gpu_memory && (
                          <div className="flex items-center gap-1.5 text-xs text-gray-600">
                            <MemoryStick className="h-3 w-3 flex-shrink-0" />
                            <span className="font-medium">GPU:</span>
                            <span>{service.gpu_memory}</span>
                          </div>
                        )}
                        {service.port && (
                          <div className="flex items-center gap-1.5 text-xs text-gray-500">
                            <span className="font-medium">Port:</span>
                            <span>{service.port}</span>
                          </div>
                        )}
                      </div>

                      {/* Actions - 2x2 Grid */}
                      <div className="grid grid-cols-2 gap-1.5">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => performDockerAction(service.id, 'start')}
                          disabled={service.status === 'running'}
                          className="text-xs h-8 px-2"
                        >
                          <Play className="h-3 w-3 mr-1" />
                          Start
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => performDockerAction(service.id, 'stop')}
                          disabled={service.status === 'stopped'}
                          className="text-xs h-8 px-2"
                        >
                          <Square className="h-3 w-3 mr-1" />
                          Stop
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => performDockerAction(service.id, 'restart')}
                          disabled={service.status === 'unknown'}
                          className="text-xs h-8 px-2 col-span-2"
                        >
                          <RotateCw className="h-3 w-3 mr-1" />
                          Restart
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Remote Services (Backup) */}
          <Card>
            <CardHeader>
              <CardTitle>Remote Services (RunPod - Backup)</CardTitle>
              <CardDescription>Alternative TTS services on separate GPU infrastructure</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="bg-blue-50 dark:bg-blue-950 rounded-lg p-4 border border-blue-200 mb-3">
                  <p className="text-xs text-gray-700 dark:text-gray-300">
                    <strong>Note:</strong> F5-TTS and StyleTTS2 are now available locally (above).
                    RunPod versions remain available as backup.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200 p-5">
                    <h4 className="font-semibold text-lg mb-2">F5-TTS (RunPod)</h4>
                    <p className="text-sm text-gray-600 mb-3">
                      Flow-matching TTS with voice cloning (4 languages)
                    </p>
                    <div className="flex items-center gap-2 mb-3">
                      <Badge className="bg-green-500 text-white">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Online
                      </Badge>
                      <span className="text-xs text-gray-500">https://f5tts.ailabsafrica.com</span>
                    </div>
                    <p className="text-xs text-gray-500">GPU: NVIDIA A40 (46GB) on RunPod</p>
                  </div>

                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border-2 border-purple-200 p-5">
                    <h4 className="font-semibold text-lg mb-2">StyleTTS2 (RunPod)</h4>
                    <p className="text-sm text-gray-600 mb-3">
                      Expressive TTS with style transfer and emotion control
                    </p>
                    <div className="flex items-center gap-2 mb-3">
                      <Badge className="bg-green-500 text-white">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Online
                      </Badge>
                      <span className="text-xs text-gray-500">https://styletts.ailabsafrica.com</span>
                    </div>
                    <p className="text-xs text-gray-500">GPU: NVIDIA A40 (46GB) on RunPod</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Service Details Modal */}
      <Dialog open={showServiceModal} onOpenChange={setShowServiceModal}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
          {selectedService && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <DialogTitle className="text-2xl">{selectedService.display_name}</DialogTitle>
                    <DialogDescription className="mt-1">
                      {selectedService.service_name} • {selectedService.category}
                    </DialogDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={closeServiceModal}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </DialogHeader>

              <div className="mt-4">
                {/* Action Buttons */}
                <div className="flex gap-2 mb-4">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => performServiceAction(selectedService.service_name, 'start')}
                    disabled={!selectedService.can_start || selectedService.status === 'active'}
                  >
                    <Play className="h-4 w-4 mr-1" />
                    Start
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => performServiceAction(selectedService.service_name, 'stop')}
                    disabled={!selectedService.can_stop || selectedService.status === 'inactive'}
                  >
                    <Square className="h-4 w-4 mr-1" />
                    Stop
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => performServiceAction(selectedService.service_name, 'restart')}
                    disabled={!selectedService.can_restart}
                  >
                    <RotateCw className="h-4 w-4 mr-1" />
                    Restart
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => performServiceAction(selectedService.service_name, 'enable')}
                    disabled={selectedService.is_enabled}
                  >
                    <Power className="h-4 w-4 mr-1" />
                    Enable
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => performServiceAction(selectedService.service_name, 'disable')}
                    disabled={!selectedService.is_enabled}
                  >
                    <Power className="h-4 w-4 mr-1" />
                    Disable
                  </Button>
                </div>

                {/* Tabs */}
                <Tabs defaultValue="status" className="h-[50vh]">
                  <TabsList className="grid grid-cols-3 w-full max-w-md">
                    <TabsTrigger value="status">Status</TabsTrigger>
                    <TabsTrigger value="logs">Logs</TabsTrigger>
                    <TabsTrigger value="file">Configuration</TabsTrigger>
                  </TabsList>

                  <TabsContent value="status" className="mt-4 space-y-4">
                    <div className="grid grid-cols-2 gap-6">
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Status:</span>
                          <Badge className={`${getStatusColor(selectedService.status)} text-white`}>
                            {selectedService.status}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Enabled:</span>
                          <span>{selectedService.is_enabled ? 'Yes' : 'No'}</span>
                        </div>
                        {selectedService.pid && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">PID:</span>
                            <span>{selectedService.pid}</span>
                          </div>
                        )}
                        {selectedService.active_since && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Active Since:</span>
                            <span className="text-sm">{selectedService.active_since}</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="space-y-3">
                        {selectedService.uptime && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Uptime:</span>
                            <span>{selectedService.uptime}</span>
                          </div>
                        )}
                        {selectedService.memory_current && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Memory:</span>
                            <span>{selectedService.memory_current}</span>
                          </div>
                        )}
                        {selectedService.memory_limit && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Memory Limit:</span>
                            <span>{selectedService.memory_limit}</span>
                          </div>
                        )}
                        {selectedService.cpu_usage && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">CPU:</span>
                            <span>{selectedService.cpu_usage}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {selectedService.file_path && (
                      <div className="pt-4 border-t">
                        <div className="flex justify-between">
                          <span className="text-gray-600">File Path:</span>
                          <code className="text-sm bg-gray-100 px-2 py-1 rounded">{selectedService.file_path}</code>
                        </div>
                      </div>
                    )}
                  </TabsContent>
                  
                  <TabsContent value="logs" className="mt-4">
                    <ScrollArea className="h-[40vh] rounded border p-4 bg-gray-50">
                      {selectedService.logs && selectedService.logs.length > 0 ? (
                        <div className="space-y-1">
                          {selectedService.logs.map((log, idx) => (
                            <div key={idx} className="font-mono text-xs">
                              {log}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-600">No logs available</p>
                      )}
                    </ScrollArea>
                  </TabsContent>
                  
                  <TabsContent value="file" className="mt-4">
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <Label>Service Configuration</Label>
                        <div className="flex gap-2">
                          {editingFile ? (
                            <>
                              <Button size="sm" onClick={() => setEditingFile(false)} variant="outline">
                                Cancel
                              </Button>
                              <Button size="sm" onClick={() => {/* Save logic */}}>
                                <Save className="h-4 w-4 mr-1" />
                                Save
                              </Button>
                            </>
                          ) : (
                            <Button size="sm" onClick={() => setEditingFile(true)} variant="outline">
                              <Edit className="h-4 w-4 mr-1" />
                              Edit
                            </Button>
                          )}
                        </div>
                      </div>
                      <Textarea
                        value={serviceFile}
                        onChange={(e) => setServiceFile(e.target.value)}
                        readOnly={!editingFile}
                        className="font-mono text-xs h-[35vh]"
                        placeholder="Service file content..."
                      />
                    </div>
                  </TabsContent>
                </Tabs>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Service Dialog (keep existing) */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Create New Service</DialogTitle>
            <DialogDescription>
              Create a new systemd service
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Service Name</Label>
                <Input
                  value={newServiceData.service_name}
                  onChange={(e) => setNewServiceData(prev => ({ ...prev, service_name: e.target.value }))}
                  placeholder="my-service"
                />
              </div>
              <div>
                <Label>Display Name</Label>
                <Input
                  value={newServiceData.display_name}
                  onChange={(e) => setNewServiceData(prev => ({ ...prev, display_name: e.target.value }))}
                  placeholder="My Service"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Category</Label>
                <Select
                  value={newServiceData.category}
                  onValueChange={(value) => setNewServiceData(prev => ({ ...prev, category: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="application">Application</SelectItem>
                    <SelectItem value="voice">Voice</SelectItem>
                    <SelectItem value="database">Database</SelectItem>
                    <SelectItem value="web">Web</SelectItem>
                    <SelectItem value="monitoring">Monitoring</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Template</Label>
                <Select
                  value={selectedTemplate}
                  onValueChange={setSelectedTemplate}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select template" />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map(t => (
                      <SelectItem key={t.id} value={t.id}>
                        {t.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div>
              <Label>Description</Label>
              <Input
                value={newServiceData.description}
                onChange={(e) => setNewServiceData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Service description"
              />
            </div>
            
            <div>
              <Label>Service Configuration</Label>
              <Textarea
                value={newServiceData.content}
                onChange={(e) => setNewServiceData(prev => ({ ...prev, content: e.target.value }))}
                className="font-mono text-sm h-64"
                placeholder="[Unit]
Description=My Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/myapp
Restart=always

[Install]
WantedBy=multi-user.target"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => {/* Create logic */}}>
              Create Service
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}