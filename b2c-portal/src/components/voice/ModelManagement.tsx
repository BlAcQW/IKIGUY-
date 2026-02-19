import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from '@/components/ui/use-toast';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

import { 
  Download, Trash2, HardDrive, Package, Search, RefreshCw, 
  GitBranch, Globe, Info, CheckCircle, XCircle, Clock,
  Database, Cpu, Zap, Languages, Mic, Star, TrendingUp,
  FolderOpen, Cloud, Github, AlertTriangle, Loader2
} from 'lucide-react';

// Using API_BASE_URL from api-config;

interface VoiceModel {
  id: string;
  name: string;
  service: string;
  size: string;
  languages?: string[];
  installed: boolean;
  path?: string;
  last_modified?: string;
  source: string;
  actual_size?: string;
  download_url?: string;
}

interface ServiceModels {
  service_name: string;
  models: VoiceModel[];
  total_available: number;
  total_installed: number;
  storage_used: string;
}

interface DiskUsage {
  services: Record<string, string>;
  total_used: string;
  disk_total: string;
  disk_free: string;
  disk_percent: number;
}

export default function ModelManagement() {
  const [services, setServices] = useState<Record<string, ServiceModels>>({});
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<Set<string>>(new Set());
  const [selectedService, setSelectedService] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [diskUsage, setDiskUsage] = useState<DiskUsage | null>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [showRecommendations, setShowRecommendations] = useState(false);

  const fetchModels = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice-models/list`);
      if (!response.ok) throw new Error('Failed to fetch models');
      const data = await response.json();
      setServices(data.services);
      setDiskUsage(data.disk_usage);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch voice models',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice-models/recommendations`);
      if (!response.ok) throw new Error('Failed to fetch recommendations');
      const data = await response.json();
      setRecommendations(data);
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    }
  };

  const downloadModel = async (service: string, modelId: string, source: string) => {
    const downloadKey = `${service}-${modelId}`;
    setDownloading(prev => new Set(prev).add(downloadKey));
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice-models/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service,
          model_id: modelId,
          source
        })
      });
      
      if (!response.ok) throw new Error('Failed to start download');
      
      const result = await response.json();
      toast({
        title: 'Download Started',
        description: `Downloading ${modelId}...`,
      });
      
      // Poll for completion (simplified - in production use WebSocket)
      setTimeout(() => {
        fetchModels();
        setDownloading(prev => {
          const next = new Set(prev);
          next.delete(downloadKey);
          return next;
        });
      }, 30000); // Check after 30 seconds
      
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to download model',
        variant: 'destructive',
      });
      setDownloading(prev => {
        const next = new Set(prev);
        next.delete(downloadKey);
        return next;
      });
    }
  };

  const deleteModel = async (service: string, modelId: string) => {
    if (!confirm(`Are you sure you want to delete ${modelId}?`)) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice-models/${service}/${encodeURIComponent(modelId)}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to delete model');
      
      const result = await response.json();
      toast({
        title: 'Model Deleted',
        description: `Freed ${result.freed_space}`,
      });
      
      fetchModels();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete model',
        variant: 'destructive',
      });
    }
  };

  const cleanupModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice-models/cleanup`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('Failed to cleanup');
      
      const result = await response.json();
      toast({
        title: 'Cleanup Complete',
        description: `Freed ${result.total_freed}`,
      });
      
      fetchModels();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to cleanup models',
        variant: 'destructive',
      });
    }
  };

  useEffect(() => {
    fetchModels();
    fetchRecommendations();
  }, []);

  const getServiceIcon = (service: string) => {
    switch (service.toLowerCase()) {
      case 'coqui': return <Mic className="h-4 w-4" />;
      case 'openvoice': return <Zap className="h-4 w-4" />;
      case 'f5tts': return <Cpu className="h-4 w-4" />;
      case 'melotts': return <Languages className="h-4 w-4" />;
      case 'metamms': return <Globe className="h-4 w-4" />;
      default: return <Package className="h-4 w-4" />;
    }
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'huggingface': return <Cloud className="h-4 w-4" />;
      case 'github': return <Github className="h-4 w-4" />;
      case 'local': return <FolderOpen className="h-4 w-4" />;
      case 'cache': return <Database className="h-4 w-4" />;
      default: return <Package className="h-4 w-4" />;
    }
  };

  const filterModels = () => {
    let allModels: VoiceModel[] = [];
    
    Object.entries(services).forEach(([key, service]) => {
      if (selectedService === 'all' || selectedService === key) {
        allModels = [...allModels, ...service.models];
      }
    });
    
    if (searchQuery) {
      allModels = allModels.filter(model => 
        model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        model.languages?.some(lang => lang.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }
    
    return allModels;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-xl font-semibold">Voice Model Management</h3>
          <p className="text-sm text-gray-600">
            Manage TTS models for all voice services
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={cleanupModels}>
            <Trash2 className="h-4 w-4 mr-2" />
            Cleanup
          </Button>
          <Button variant="outline" onClick={fetchModels} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Disk Usage */}
      {diskUsage && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <HardDrive className="h-4 w-4" />
              Storage Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>Total Models Storage</span>
                <span className="font-medium">{diskUsage.total_used}</span>
              </div>
              <Progress value={diskUsage.disk_percent} className="h-2" />
              <div className="grid grid-cols-5 gap-2 text-xs">
                {Object.entries(diskUsage.services).map(([service, size]) => (
                  <div key={service} className="text-center">
                    <div className="font-medium">{service.toUpperCase()}</div>
                    <div className="text-gray-600">{size}</div>
                  </div>
                ))}
              </div>
              <div className="flex justify-between text-xs text-gray-600">
                <span>Disk Free: {diskUsage.disk_free}</span>
                <span>Total: {diskUsage.disk_total}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
            <Input
              placeholder="Search models by name, ID, or language..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={selectedService} onValueChange={setSelectedService}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Services</SelectItem>
            {Object.keys(services).map(service => (
              <SelectItem key={service} value={service}>
                <div className="flex items-center gap-2">
                  {getServiceIcon(service)}
                  {service.toUpperCase()}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Dialog open={showRecommendations} onOpenChange={setShowRecommendations}>
          <DialogTrigger asChild>
            <Button variant="outline">
              <Star className="h-4 w-4 mr-2" />
              Recommendations
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Recommended Models</DialogTitle>
              <DialogDescription>
                Curated models for different use cases
              </DialogDescription>
            </DialogHeader>
            <ScrollArea className="h-[500px]">
              {recommendations && (
                <div className="space-y-4">
                  {Object.entries(recommendations).map(([category, models]: [string, any[]]) => (
                    <div key={category} className="space-y-2">
                      <h4 className="font-medium capitalize">
                        {category.replace('_', ' ')}
                      </h4>
                      <div className="space-y-2">
                        {models.map((model: any, idx: number) => (
                          <div key={idx} className="border rounded-lg p-3">
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="font-medium">{model.name}</div>
                                <div className="text-sm text-gray-600">
                                  {model.service.toUpperCase()} - {model.model_id}
                                </div>
                                <div className="text-sm mt-1">{model.reason}</div>
                              </div>
                              <Button
                                size="sm"
                                onClick={() => {
                                  downloadModel(model.service, model.model_id, 'huggingface');
                                  setShowRecommendations(false);
                                }}
                              >
                                <Download className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </DialogContent>
        </Dialog>
      </div>

      {/* Models Grid */}
      <Tabs defaultValue="available" className="space-y-4">
        <TabsList>
          <TabsTrigger value="available">Available Models</TabsTrigger>
          <TabsTrigger value="installed">Installed Models</TabsTrigger>
          <TabsTrigger value="all">All Models</TabsTrigger>
        </TabsList>

        <TabsContent value="available">
          <ScrollArea className="h-[600px]">
            <div className="grid gap-3">
              {filterModels()
                .filter(model => !model.installed)
                .map(model => (
                  <ModelCard
                    key={`${model.service}-${model.id}`}
                    model={model}
                    onDownload={() => downloadModel(model.service, model.id, model.source)}
                    onDelete={() => deleteModel(model.service, model.id)}
                    isDownloading={downloading.has(`${model.service}-${model.id}`)}
                    getServiceIcon={getServiceIcon}
                    getSourceIcon={getSourceIcon}
                  />
                ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="installed">
          <ScrollArea className="h-[600px]">
            <div className="grid gap-3">
              {filterModels()
                .filter(model => model.installed)
                .map(model => (
                  <ModelCard
                    key={`${model.service}-${model.id}`}
                    model={model}
                    onDownload={() => downloadModel(model.service, model.id, model.source)}
                    onDelete={() => deleteModel(model.service, model.id)}
                    isDownloading={downloading.has(`${model.service}-${model.id}`)}
                    getServiceIcon={getServiceIcon}
                    getSourceIcon={getSourceIcon}
                  />
                ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="all">
          <ScrollArea className="h-[600px]">
            <div className="grid gap-3">
              {filterModels().map(model => (
                <ModelCard
                  key={`${model.service}-${model.id}`}
                  model={model}
                  onDownload={() => downloadModel(model.service, model.id, model.source)}
                  onDelete={() => deleteModel(model.service, model.id)}
                  isDownloading={downloading.has(`${model.service}-${model.id}`)}
                  getServiceIcon={getServiceIcon}
                  getSourceIcon={getSourceIcon}
                />
              ))}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Model Card Component
function ModelCard({ 
  model, 
  onDownload, 
  onDelete, 
  isDownloading,
  getServiceIcon,
  getSourceIcon
}: {
  model: VoiceModel;
  onDownload: () => void;
  onDelete: () => void;
  isDownloading: boolean;
  getServiceIcon: (service: string) => React.ReactNode;
  getSourceIcon: (source: string) => React.ReactNode;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              {getServiceIcon(model.service)}
              <span className="font-medium">{model.name}</span>
              {model.installed && (
                <Badge variant="default" className="text-xs">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Installed
                </Badge>
              )}
            </div>
            
            <div className="text-sm text-gray-600">
              <code>{model.id}</code>
            </div>
            
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="text-xs">
                {getSourceIcon(model.source)}
                <span className="ml-1">{model.source}</span>
              </Badge>
              
              <Badge variant="outline" className="text-xs">
                <HardDrive className="h-3 w-3 mr-1" />
                {model.actual_size || model.size}
              </Badge>
              
              {model.languages && model.languages.length > 0 && (
                <Badge variant="outline" className="text-xs">
                  <Languages className="h-3 w-3 mr-1" />
                  {model.languages.length === 1 
                    ? model.languages[0] 
                    : `${model.languages.length} languages`}
                </Badge>
              )}
            </div>
            
            {model.path && (
              <div className="text-xs text-gray-600">
                Path: {model.path}
              </div>
            )}
            
            {model.last_modified && (
              <div className="text-xs text-gray-600">
                Modified: {new Date(model.last_modified).toLocaleDateString()}
              </div>
            )}
          </div>
          
          <div className="flex gap-2">
            {!model.installed ? (
              <Button
                size="sm"
                onClick={onDownload}
                disabled={isDownloading}
              >
                {isDownloading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                  </>
                )}
              </Button>
            ) : (
              <Button
                size="sm"
                variant="destructive"
                onClick={onDelete}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}