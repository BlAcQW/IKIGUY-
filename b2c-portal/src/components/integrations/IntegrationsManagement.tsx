import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  ExternalLink,
  CheckCircle,
  AlertCircle,
  Eye,
  EyeOff,
  Save,
  Trash2,
  Key,
  TestTube,
  Settings,
  Loader2
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { IntegrationTester } from './IntegrationTester';
import { IntegrationCategorySidebar } from './IntegrationCategorySidebar';
import { integrationsService } from '@/services/IntegrationsService';
import type { Integration, IntegrationType } from '@/services/IntegrationsService';

// Using Integration interface from IntegrationsService
interface LocalIntegrationState {
  apiKey: string;
  showPassword: boolean;
}


export const IntegrationsManagement: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [localStates, setLocalStates] = useState<Record<string, LocalIntegrationState>>({});
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  const [testing, setTesting] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showConfiguredOnly, setShowConfiguredOnly] = useState(false);
  const { toast } = useToast();

  // Filter integrations based on selected category, search term, and configuration status
  const filteredIntegrations = useMemo(() => {
    let filtered = integrations;

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter(integration => integration.integration_type === selectedCategory);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(integration =>
        integration.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        integration.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        integration.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        integration.integration_type.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by configuration status
    if (showConfiguredOnly) {
      filtered = filtered.filter(integration => integration.is_configured);
    }

    return filtered;
  }, [integrations, selectedCategory, searchTerm, showConfiguredOnly]);

  // Load integrations from API on component mount
  useEffect(() => {
    const loadIntegrations = async () => {
      try {
        setLoading(true);
        const response = await integrationsService.listIntegrations({ per_page: 100 });
        setIntegrations(response.integrations);

        // Initialize local states for API keys from localStorage
        const savedKeys = localStorage.getItem('kasaai_integration_keys');
        if (savedKeys) {
          try {
            const parsed = JSON.parse(savedKeys);
            setLocalStates(parsed);
          } catch (error) {
            console.error('Error loading saved API keys:', error);
          }
        }
      } catch (error) {
        console.error('Error loading integrations:', error);
        toast({
          title: "Error loading integrations",
          description: "Failed to load integrations from server.",
          variant: "destructive"
        });
      } finally {
        setLoading(false);
      }
    };

    loadIntegrations();
  }, [toast]);

  const saveIntegration = async (integrationId: string) => {
    setSaving(prev => ({ ...prev, [integrationId]: true }));

    try {
      const integration = integrations.find(i => i.id === integrationId);
      const localState = localStates[integrationId];

      if (!integration || !localState?.apiKey) {
        toast({
          title: "No API key",
          description: "Please enter an API key before saving.",
          variant: "destructive"
        });
        return;
      }

      // Configure integration via API
      await integrationsService.configureIntegration(integrationId, {
        api_key: localState.apiKey,
        test_connection: false
      });

      // Save API keys to localStorage
      const savedKeys = localStorage.getItem('kasaai_integration_keys') || '{}';
      const parsedKeys = JSON.parse(savedKeys);
      parsedKeys[integrationId] = localState;
      localStorage.setItem('kasaai_integration_keys', JSON.stringify(parsedKeys));

      // Reload integrations to get updated status
      const response = await integrationsService.listIntegrations({ per_page: 100 });
      setIntegrations(response.integrations);

      toast({
        title: "Integration saved",
        description: `${integration.display_name} configuration has been saved successfully.`,
      });
    } catch (error) {
      console.error('Error saving integration:', error);
      toast({
        title: "Error saving integration",
        description: "Failed to save the integration configuration.",
        variant: "destructive"
      });
    } finally {
      setSaving(prev => ({ ...prev, [integrationId]: false }));
    }
  };

  const deleteIntegration = async (integrationId: string) => {
    const integration = integrations.find(i => i.id === integrationId);
    if (!integration) return;

    if (window.confirm(`Are you sure you want to delete the ${integration.display_name} configuration?`)) {
      try {
        // Reset configuration via API (send empty config)
        await integrationsService.configureIntegration(integrationId, {
          api_key: '',
          test_connection: false
        });

        // Remove from localStorage
        const savedKeys = localStorage.getItem('kasaai_integration_keys') || '{}';
        const parsedKeys = JSON.parse(savedKeys);
        delete parsedKeys[integrationId];
        localStorage.setItem('kasaai_integration_keys', JSON.stringify(parsedKeys));

        // Update local states
        setLocalStates(prev => {
          const newState = { ...prev };
          delete newState[integrationId];
          return newState;
        });

        // Reload integrations to get updated status
        const response = await integrationsService.listIntegrations({ per_page: 100 });
        setIntegrations(response.integrations);

        toast({
          title: "Integration deleted",
          description: `${integration.display_name} configuration has been removed.`,
        });
      } catch (error) {
        console.error('Error deleting integration:', error);
        toast({
          title: "Error deleting integration",
          description: "Failed to delete the integration configuration.",
          variant: "destructive"
        });
      }
    }
  };

  const testIntegration = async (integrationId: string) => {
    setTesting(prev => ({ ...prev, [integrationId]: true }));

    try {
      const integration = integrations.find(i => i.id === integrationId);
      const localState = localStates[integrationId];

      if (!integration || !localState?.apiKey) {
        toast({
          title: "No API key",
          description: "Please configure an API key before testing.",
          variant: "destructive"
        });
        return;
      }

      // Test integration via API
      const result = await integrationsService.testIntegration(integrationId);

      if (result.success) {
        toast({
          title: "Test successful",
          description: `${integration.display_name} connection test passed!`,
        });

        // Reload integrations to get updated status
        const response = await integrationsService.listIntegrations({ per_page: 100 });
        setIntegrations(response.integrations);
      } else {
        toast({
          title: "Test failed",
          description: result.message || `${integration.display_name} connection test failed. Please check your API key.`,
          variant: "destructive"
        });
      }
    } catch (error) {
      console.error('Error testing integration:', error);
      toast({
        title: "Test error",
        description: "An error occurred while testing the integration.",
        variant: "destructive"
      });
    } finally {
      setTesting(prev => ({ ...prev, [integrationId]: false }));
    }
  };

  const toggleApiKeyVisibility = (integrationId: string) => {
    setShowApiKeys(prev => ({ ...prev, [integrationId]: !prev[integrationId] }));
  };

  const updateApiKey = (integrationId: string, apiKey: string) => {
    setLocalStates(prev => ({
      ...prev,
      [integrationId]: {
        ...prev[integrationId],
        apiKey,
        showPassword: prev[integrationId]?.showPassword || false
      }
    }));
  };

  const getStatusBadge = (integration: Integration) => {
    switch (integration.status) {
      case 'configured':
        return <Badge className="bg-green-100 text-green-800">Configured</Badge>;
      case 'tested':
        return <Badge className="bg-blue-100 text-blue-800">Tested</Badge>;
      case 'error':
        return <Badge className="bg-red-100 text-red-800">Error</Badge>;
      case 'disabled':
        return <Badge className="bg-gray-100 text-gray-800">Disabled</Badge>;
      default:
        return <Badge variant="outline">Not Configured</Badge>;
    }
  };

  const getCategoryBadge = (category: string) => {
    const colors = {
      tts: 'bg-blue-100 text-blue-800',
      stt: 'bg-purple-100 text-purple-800',
      llm: 'bg-orange-100 text-orange-800',
      telephony: 'bg-green-100 text-green-800',
      messaging: 'bg-pink-100 text-pink-800',
      email: 'bg-indigo-100 text-indigo-800',
      payment: 'bg-emerald-100 text-emerald-800',
      crm: 'bg-cyan-100 text-cyan-800',
      support: 'bg-amber-100 text-amber-800',
      storage: 'bg-slate-100 text-slate-800',
      analytics: 'bg-violet-100 text-violet-800',
      automation: 'bg-rose-100 text-rose-800',
      productivity: 'bg-blue-100 text-blue-800',
      healthcare: 'bg-red-100 text-red-800',
      enterprise: 'bg-gray-100 text-gray-800',
      monitoring: 'bg-yellow-100 text-yellow-800',
      banking: 'bg-green-100 text-green-800'
    };
    
    return (
      <Badge className={colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-800'}>
        {category.toUpperCase()}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading integrations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Category Sidebar */}
      <IntegrationCategorySidebar
        integrations={integrations}
        selectedCategory={selectedCategory}
        onCategorySelect={setSelectedCategory}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        showConfiguredOnly={showConfiguredOnly}
        onShowConfiguredOnlyChange={setShowConfiguredOnly}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="space-y-4 sm:space-y-6 p-3 sm:p-4 lg:p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 sm:gap-0">
            <div>
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold">
                {selectedCategory ? 
                  `${selectedCategory.charAt(0).toUpperCase() + selectedCategory.slice(1)} Integrations` : 
                  'Integrations'
                }
              </h1>
              <p className="text-xs sm:text-sm text-gray-600">
                {selectedCategory ? 
                  `Configure ${selectedCategory} integrations and API keys` :
                  'Configure API keys and test third-party service integrations'
                } ({filteredIntegrations.length} {filteredIntegrations.length === 1 ? 'integration' : 'integrations'})
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setShowApiKeys(prev => 
                Object.keys(prev).reduce((acc, key) => ({ ...acc, [key]: !prev[key] }), {})
              )}
            >
              <Eye className="mr-1.5 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
              Toggle All API Keys
            </Button>
          </div>

      <Tabs defaultValue="configuration" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="configuration" className="flex items-center gap-2">
            <Key className="h-4 w-4" />
            Configuration
          </TabsTrigger>
          <TabsTrigger value="testing" className="flex items-center gap-2">
            <TestTube className="h-4 w-4" />
            Testing
          </TabsTrigger>
        </TabsList>

        <TabsContent value="configuration" className="mt-6">

          {/* Show empty state if no integrations match filters */}
          {filteredIntegrations.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-600 mb-4">
                <Settings className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-semibold mb-2">No integrations found</h3>
                <p className="text-sm">
                  {searchTerm || selectedCategory || showConfiguredOnly ? 
                    'Try adjusting your filters or search terms.' : 
                    'No integrations available.'}
                </p>
              </div>
              {(searchTerm || selectedCategory || showConfiguredOnly) && (
                <Button
                  variant="outline"
                  onClick={() => {
                    setSearchTerm('');
                    setSelectedCategory(null);
                    setShowConfiguredOnly(false);
                  }}
                >
                  Clear all filters
                </Button>
              )}
            </div>
          ) : (
            <div className="grid gap-3 sm:gap-4 lg:gap-6 grid-cols-1 md:grid-cols-2">
              {filteredIntegrations.map((integration) => (
          <Card key={integration.id} className="relative overflow-hidden">
            <CardHeader>
              <div className="flex flex-col sm:flex-row items-start justify-between gap-2 sm:gap-0">
                <div className="flex items-center space-x-2 sm:space-x-3">
                  <div className="text-xl sm:text-2xl">{integration.icon || '🔗'}</div>
                  <div>
                    <CardTitle className="flex items-center space-x-2 text-sm sm:text-base">
                      <span>{integration.display_name}</span>
                      {getStatusBadge(integration)}
                    </CardTitle>
                    <CardDescription className="mt-0.5 sm:mt-1 text-xs sm:text-sm">
                      {integration.description}
                    </CardDescription>
                  </div>
                </div>
                <div className="flex items-center space-x-1 sm:space-x-2">
                  {getCategoryBadge(integration.integration_type)}
                  {integration.website && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => window.open(integration.website, '_blank')}
                    >
                      <ExternalLink className="h-3 w-3 sm:h-4 sm:w-4" />
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-3 sm:space-y-4 p-3 sm:p-4 lg:p-6">
              <div className="space-y-1.5 sm:space-y-2">
                <Label htmlFor={`api-key-${integration.id}`}>API Key</Label>
                <div className="relative">
                  <Input
                    id={`api-key-${integration.id}`}
                    type={showApiKeys[integration.id] ? 'text' : 'password'}
                    placeholder="Enter your API key"
                    value={localStates[integration.id]?.apiKey || ''}
                    onChange={(e) => updateApiKey(integration.id, e.target.value)}
                    className="pr-10 text-xs sm:text-sm"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-2 sm:px-3"
                    onClick={() => toggleApiKeyVisibility(integration.id)}
                  >
                    {showApiKeys[integration.id] ? (
                      <EyeOff className="h-3 w-3 sm:h-4 sm:w-4" />
                    ) : (
                      <Eye className="h-3 w-3 sm:h-4 sm:w-4" />
                    )}
                  </Button>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 sm:gap-0">
                <div className="flex items-center space-x-1 sm:space-x-2">
                  <Button
                    size="sm"
                    onClick={() => saveIntegration(integration.id)}
                    disabled={saving[integration.id]}
                  >
                    <Save className="mr-1.5 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
                    {saving[integration.id] ? 'Saving...' : 'Save'}
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => testIntegration(integration.id)}
                    disabled={testing[integration.id] || !localStates[integration.id]?.apiKey}
                  >
                    <TestTube className="mr-1.5 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
                    {testing[integration.id] ? 'Testing...' : 'Test'}
                  </Button>
                </div>

                {localStates[integration.id]?.apiKey && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteIntegration(integration.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-3 w-3 sm:h-4 sm:w-4" />
                  </Button>
                )}
              </div>

              {integration.is_tested && integration.last_test_result && (
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>Last tested: {new Date(integration.last_test_result.tested_at).toLocaleString()}</span>
                </div>
              )}

              {integration.status === 'error' && (
                <div className="flex items-center space-x-2 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  <span>{integration.last_error || 'Connection test failed'}</span>
                </div>
              )}
            </CardContent>
          </Card>
              ))}
            </div>
          )}

          <Separator />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Settings className="h-5 w-5" />
            Integration Settings
          </CardTitle>
          <CardDescription>
            Global settings for all integrations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Auto-test on save</Label>
              <p className="text-sm text-gray-600">
                Automatically test integrations when saving API keys
              </p>
            </div>
            <div>
              <Label>Encrypt API keys</Label>
              <p className="text-sm text-gray-600">
                Store API keys encrypted in the database
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
        </TabsContent>

        <TabsContent value="testing" className="mt-6">
          <div className="space-y-4">
            <div className="text-center py-4">
              <p className="text-gray-600 mb-4">
                Select an integration below to run tests and validate functionality
              </p>
            </div>
            
            <div className="grid gap-3 sm:gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
              {filteredIntegrations
                .filter(integration => integration.is_configured && localStates[integration.id]?.apiKey)
                .map((integration) => (
                  <Card key={integration.id} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-center space-x-3">
                        <div className="text-xl">{integration.icon || '🔗'}</div>
                        <div>
                          <CardTitle className="text-sm">{integration.display_name}</CardTitle>
                          <CardDescription className="text-xs">
                            {getCategoryBadge(integration.integration_type)}
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <IntegrationTester
                        integrationId={integration.id}
                        integrationName={integration.display_name}
                        category={integration.integration_type}
                      />
                    </CardContent>
                  </Card>
                ))}
            </div>

            {filteredIntegrations.filter(integration => integration.is_configured && localStates[integration.id]?.apiKey).length === 0 && (
              <Card className="text-center py-12">
                <CardContent>
                  <TestTube className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Configured Integrations</h3>
                  <p className="text-gray-600 mb-4">
                    Configure API keys for integrations in the Configuration tab to enable testing.
                  </p>
                  <Button 
                    onClick={() => {
                      const configTab = document.querySelector('[value="configuration"]') as HTMLElement;
                      configTab?.click();
                    }}
                    variant="outline"
                  >
                    <Key className="h-4 w-4 mr-2" />
                    Go to Configuration
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
        </div>
      </div>
    </div>
  );
};
