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
import { toast } from '@/components/ui/use-toast';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

import { 
  Play, Square, RotateCw, Power, Terminal, FileText, Plus, Trash2, 
  Edit, Save, Copy, AlertTriangle, CheckCircle, XCircle, Clock,
  MemoryStick, Cpu, HardDrive, Activity, Settings, RefreshCw,
  ChevronDown, ChevronRight, Search, Filter
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
  const [loading, setLoading] = useState(false);
  const [selectedService, setSelectedService] = useState<Service | null>(null);
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
  const [expandedServices, setExpandedServices] = useState<Set<string>>(new Set());
  const [autoRefresh, setAutoRefresh] = useState(false);

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

  // Save service file
  const saveServiceFile = async () => {
    if (!selectedService) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/services/${selectedService.service_name}/file`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: serviceFile })
      });
      
      if (!response.ok) throw new Error('Failed to save service file');
      
      toast({
        title: 'Success',
        description: 'Service file saved successfully',
      });
      setEditingFile(false);
      
      // Reload daemon
      await reloadDaemon();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save service file',
        variant: 'destructive',
      });
    }
  };

  // Create new service
  const createService = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/services/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newServiceData,
          enable: true,
          start: false
        })
      });
      
      if (!response.ok) throw new Error('Failed to create service');
      
      toast({
        title: 'Success',
        description: 'Service created successfully',
      });
      
      setShowCreateDialog(false);
      fetchServices();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create service',
        variant: 'destructive',
      });
    }
  };

  // Delete service
  const deleteService = async (serviceName: string) => {
    if (!confirm(`Are you sure you want to delete ${serviceName}?`)) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/services/${serviceName}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to delete service');
      
      toast({
        title: 'Success',
        description: 'Service deleted successfully',
      });
      
      fetchServices();
      setSelectedService(null);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete service',
        variant: 'destructive',
      });
    }
  };

  // Reload systemd daemon
  const reloadDaemon = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/services/daemon-reload`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('Failed to reload daemon');
      
      toast({
        title: 'Success',
        description: 'Systemd daemon reloaded',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to reload daemon',
        variant: 'destructive',
      });
    }
  };

  // Load template
  const loadTemplate = async (templateId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/services/templates/${templateId}`);
      if (!response.ok) throw new Error('Failed to fetch template');
      const data = await response.json();
      
      setNewServiceData(prev => ({
        ...prev,
        content: data.template,
        category: data.category
      }));
      
      // Apply default variables
      if (data.variables) {
        let content = data.template;
        Object.entries(data.variables).forEach(([key, value]) => {
          content = content.replace(new RegExp(`{${key}}`, 'g'), value as string);
        });
        setNewServiceData(prev => ({ ...prev, content }));
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load template',
        variant: 'destructive',
      });
    }
  };

  // Filter services
  const filterServices = (serviceList: Service[], search: string, category: string) => {
    let filtered = serviceList;
    
    if (search) {
      filtered = filtered.filter(s => 
        s.service_name.toLowerCase().includes(search.toLowerCase()) ||
        s.display_name.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    if (category !== 'all') {
      filtered = filtered.filter(s => s.category === category);
    }
    
    setFilteredServices(filtered);
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'running':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'inactive':
      case 'stopped':
        return <XCircle className="h-4 w-4 text-gray-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'running':
        return 'bg-green-500';
      case 'inactive':
      case 'stopped':
        return 'bg-gray-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-yellow-500';
    }
  };

  // Get category icon
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'voice':
        return <Activity className="h-4 w-4" />;
      case 'database':
        return <HardDrive className="h-4 w-4" />;
      case 'web':
        return <Terminal className="h-4 w-4" />;
      case 'monitoring':
        return <Activity className="h-4 w-4" />;
      default:
        return <Settings className="h-4 w-4" />;
    }
  };

  useEffect(() => {
    fetchServices();
    fetchTemplates();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchServices, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  useEffect(() => {
    filterServices(services, searchTerm, selectedCategory);
  }, [searchTerm, selectedCategory]);

  const categories = ['all', ...new Set(services.map(s => s.category))];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Service Management</h2>
          <p className="text-gray-600">Monitor and control system services</p>
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
          <Button onClick={fetchServices} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={reloadDaemon} variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Reload Daemon
          </Button>
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Service
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New Service</DialogTitle>
                <DialogDescription>
                  Create a new systemd service from template or custom configuration
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
                        <SelectItem value="system">System</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Template</Label>
                    <Select
                      value={selectedTemplate}
                      onValueChange={(value) => {
                        setSelectedTemplate(value);
                        loadTemplate(value);
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select template" />
                      </SelectTrigger>
                      <SelectContent>
                        {templates.map(template => (
                          <SelectItem key={template.id} value={template.id}>
                            {template.name}
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
                  <Label>Service File Content</Label>
                  <Textarea
                    value={newServiceData.content}
                    onChange={(e) => setNewServiceData(prev => ({ ...prev, content: e.target.value }))}
                    className="font-mono text-sm h-96"
                    placeholder="[Unit]&#10;Description=My Service&#10;..."
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={createService}>
                  Create Service
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search services..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {categories.map(cat => (
              <SelectItem key={cat} value={cat}>
                {cat === 'all' ? 'All Categories' : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-12 gap-6">
        {/* Service List */}
        <div className="col-span-5">
          <Card>
            <CardHeader>
              <CardTitle>Services ({filteredServices.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-2">
                  {filteredServices.map(service => (
                    <div
                      key={service.service_name}
                      className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                        selectedService?.service_name === service.service_name ? 'bg-blue-50 border-blue-300' : 'hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        setSelectedService(service);
                        fetchServiceFile(service.service_name);
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(service.status)}
                          <div>
                            <div className="font-medium">{service.display_name}</div>
                            <div className="text-sm text-gray-600">{service.service_name}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {service.memory_current && (
                            <Badge variant="outline" className="text-xs">
                              <MemoryStick className="h-3 w-3 mr-1" />
                              {service.memory_current}
                            </Badge>
                          )}
                          <Badge variant="outline" className="text-xs">
                            {getCategoryIcon(service.category)}
                            <span className="ml-1">{service.category}</span>
                          </Badge>
                        </div>
                      </div>
                      
                      {expandedServices.has(service.service_name) && (
                        <div className="mt-3 pt-3 border-t space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Status:</span>
                            <Badge className={getStatusColor(service.status)}>
                              {service.status}
                            </Badge>
                          </div>
                          {service.uptime && (
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Uptime:</span>
                              <span>{service.uptime}</span>
                            </div>
                          )}
                          {service.cpu_usage && (
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">CPU:</span>
                              <span>{service.cpu_usage}</span>
                            </div>
                          )}
                          <div className="flex gap-1 mt-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                performServiceAction(service.service_name, 'start');
                              }}
                              disabled={!service.can_start || service.status === 'active'}
                            >
                              <Play className="h-3 w-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                performServiceAction(service.service_name, 'stop');
                              }}
                              disabled={!service.can_stop || service.status === 'inactive'}
                            >
                              <Square className="h-3 w-3" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => {
                                e.stopPropagation();
                                performServiceAction(service.service_name, 'restart');
                              }}
                              disabled={!service.can_restart}
                            >
                              <RotateCw className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      )}
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        className="mt-2 w-full"
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedServices(prev => {
                            const next = new Set(prev);
                            if (next.has(service.service_name)) {
                              next.delete(service.service_name);
                            } else {
                              next.add(service.service_name);
                            }
                            return next;
                          });
                        }}
                      >
                        {expandedServices.has(service.service_name) ? (
                          <>
                            <ChevronDown className="h-3 w-3 mr-1" />
                            Less
                          </>
                        ) : (
                          <>
                            <ChevronRight className="h-3 w-3 mr-1" />
                            More
                          </>
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Service Details */}
        <div className="col-span-7">
          {selectedService ? (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>{selectedService.display_name}</CardTitle>
                    <CardDescription>{selectedService.service_name}</CardDescription>
                  </div>
                  <div className="flex gap-2">
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
                      variant="destructive"
                      onClick={() => deleteService(selectedService.service_name)}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="status">
                  <TabsList>
                    <TabsTrigger value="status">Status</TabsTrigger>
                    <TabsTrigger value="file">Service File</TabsTrigger>
                    <TabsTrigger value="logs">Logs</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="status" className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Status:</span>
                          <Badge className={getStatusColor(selectedService.status)}>
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
                      
                      <div className="space-y-2">
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
                          <code className="text-sm">{selectedService.file_path}</code>
                        </div>
                      </div>
                    )}
                  </TabsContent>
                  
                  <TabsContent value="file">
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <Label>Service Configuration</Label>
                        <div className="flex gap-2">
                          {editingFile ? (
                            <>
                              <Button size="sm" onClick={saveServiceFile}>
                                <Save className="h-4 w-4 mr-1" />
                                Save
                              </Button>
                              <Button size="sm" variant="outline" onClick={() => setEditingFile(false)}>
                                Cancel
                              </Button>
                            </>
                          ) : (
                            <Button size="sm" variant="outline" onClick={() => setEditingFile(true)}>
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
                        className="font-mono text-sm h-96"
                      />
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="logs">
                    <ScrollArea className="h-96">
                      <pre className="text-xs font-mono">
                        {selectedService.logs.join('\n')}
                      </pre>
                    </ScrollArea>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center h-96">
                <p className="text-gray-600">Select a service to view details</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}