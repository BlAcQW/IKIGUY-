import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, GitBranch, TrendingUp, Package, Calendar, User, FileCode, BarChart3 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface ModelVersionsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  modelId: string;
  modelName: string;
  currentVersion: string;
}

export function ModelVersionsModal({
  open,
  onOpenChange,
  modelId,
  modelName,
  currentVersion
}: ModelVersionsModalProps) {
  const { toast } = useToast();
  const [versions, setVersions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<any>(null);
  const [compareVersion1, setCompareVersion1] = useState('');
  const [compareVersion2, setCompareVersion2] = useState('');
  const [comparisonData, setComparisonData] = useState<any>(null);
  const [comparing, setComparing] = useState(false);

  // Form state for creating new version
  const [newVersion, setNewVersion] = useState({
    version_number: '',
    changelog: '',
    architecture_changes: '',
    training_config: '',
    performance_metrics: '',
    file_path: ''
  });

  useEffect(() => {
    if (open) {
      loadVersions();
    }
  }, [open, modelId]);

  const loadVersions = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getModelVersions(modelId);
      setVersions(Array.isArray(data) ? data : (data?.items || []));
    } catch (error) {
      console.error('Failed to load versions:', error);
      toast({
        title: 'Load Failed',
        description: 'Failed to load model versions',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVersion = async () => {
    if (!newVersion.version_number || !newVersion.changelog) {
      toast({
        title: 'Required Fields',
        description: 'Version number and changelog are required',
        variant: 'destructive'
      });
      return;
    }

    try {
      setCreating(true);
      await apiClient.createModelVersion(modelId, {
        version_number: newVersion.version_number,
        changelog: newVersion.changelog,
        architecture_changes: newVersion.architecture_changes || undefined,
        training_config: newVersion.training_config ? JSON.parse(newVersion.training_config) : undefined,
        performance_metrics: newVersion.performance_metrics ? JSON.parse(newVersion.performance_metrics) : undefined,
        file_path: newVersion.file_path || undefined
      });

      toast({
        title: 'Version Created',
        description: `Version ${newVersion.version_number} created successfully`
      });

      // Reset form and reload
      setNewVersion({
        version_number: '',
        changelog: '',
        architecture_changes: '',
        training_config: '',
        performance_metrics: '',
        file_path: ''
      });
      await loadVersions();
    } catch (error) {
      console.error('Failed to create version:', error);
      toast({
        title: 'Creation Failed',
        description: 'Failed to create model version',
        variant: 'destructive'
      });
    } finally {
      setCreating(false);
    }
  };

  const handleCompareVersions = async () => {
    if (!compareVersion1 || !compareVersion2) {
      toast({
        title: 'Select Versions',
        description: 'Please select two versions to compare',
        variant: 'destructive'
      });
      return;
    }

    try {
      setComparing(true);
      const data = await apiClient.compareModelVersions(modelId, compareVersion1, compareVersion2);
      setComparisonData(data);
    } catch (error) {
      console.error('Failed to compare versions:', error);
      toast({
        title: 'Comparison Failed',
        description: 'Failed to compare model versions',
        variant: 'destructive'
      });
    } finally {
      setComparing(false);
    }
  };

  const loadVersionDetails = async (versionNumber: string) => {
    try {
      const data = await apiClient.getModelVersionDetails(modelId, versionNumber);
      setSelectedVersion(data);
    } catch (error) {
      console.error('Failed to load version details:', error);
      toast({
        title: 'Load Failed',
        description: 'Failed to load version details',
        variant: 'destructive'
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Model Versions - {modelName}
          </DialogTitle>
          <DialogDescription>
            Manage and compare different versions of this model
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="list" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="list">Versions</TabsTrigger>
            <TabsTrigger value="create">Create New</TabsTrigger>
            <TabsTrigger value="compare">Compare</TabsTrigger>
            <TabsTrigger value="details">Details</TabsTrigger>
          </TabsList>

          {/* Versions List Tab */}
          <TabsContent value="list" className="space-y-4">
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : versions.length > 0 ? (
              <div className="space-y-3">
                {versions.map((version) => (
                  <Card key={version.version_number} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <Package className="h-5 w-5 text-primary" />
                          <div>
                            <CardTitle className="text-lg">
                              Version {version.version_number}
                              {version.version_number === currentVersion && (
                                <Badge className="ml-2 bg-green-100 text-green-800">Current</Badge>
                              )}
                            </CardTitle>
                            <CardDescription className="flex items-center gap-2 text-xs mt-1">
                              <Calendar className="h-3 w-3" />
                              {new Date(version.created_at).toLocaleDateString()}
                              {version.author_name && (
                                <>
                                  <span>•</span>
                                  <User className="h-3 w-3" />
                                  {version.author_name}
                                </>
                              )}
                            </CardDescription>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => loadVersionDetails(version.version_number)}
                        >
                          View Details
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">{version.changelog}</p>
                      {version.performance_metrics && (
                        <div className="mt-3 flex gap-4 text-xs">
                          {Object.entries(version.performance_metrics).slice(0, 3).map(([key, value]) => (
                            <div key={key} className="flex items-center gap-1">
                              <BarChart3 className="h-3 w-3 text-blue-600" />
                              <span className="font-medium">{key}:</span>
                              <span>{typeof value === 'number' ? value.toFixed(3) : String(value)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Package className="h-16 w-16 mx-auto mb-4 opacity-30" />
                <p className="text-lg font-medium">No Versions Yet</p>
                <p className="text-sm">Create your first model version to get started</p>
              </div>
            )}
          </TabsContent>

          {/* Create New Version Tab */}
          <TabsContent value="create" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Create New Version</CardTitle>
                <CardDescription>Add a new version of this model with updated weights and metrics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="version_number">Version Number *</Label>
                    <Input
                      id="version_number"
                      placeholder="e.g., 1.0.0, v2.1"
                      value={newVersion.version_number}
                      onChange={(e) => setNewVersion({ ...newVersion, version_number: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="file_path">Model File Path</Label>
                    <Input
                      id="file_path"
                      placeholder="path/to/model.pt"
                      value={newVersion.file_path}
                      onChange={(e) => setNewVersion({ ...newVersion, file_path: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="changelog">Changelog *</Label>
                  <Textarea
                    id="changelog"
                    placeholder="What changed in this version? (e.g., Improved accuracy, reduced latency, new training data)"
                    value={newVersion.changelog}
                    onChange={(e) => setNewVersion({ ...newVersion, changelog: e.target.value })}
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="architecture_changes">Architecture Changes</Label>
                  <Textarea
                    id="architecture_changes"
                    placeholder="Describe any model architecture modifications"
                    value={newVersion.architecture_changes}
                    onChange={(e) => setNewVersion({ ...newVersion, architecture_changes: e.target.value })}
                    rows={2}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="training_config">Training Config (JSON)</Label>
                  <Textarea
                    id="training_config"
                    placeholder='{"learning_rate": 0.001, "epochs": 50, "batch_size": 32}'
                    value={newVersion.training_config}
                    onChange={(e) => setNewVersion({ ...newVersion, training_config: e.target.value })}
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="performance_metrics">Performance Metrics (JSON)</Label>
                  <Textarea
                    id="performance_metrics"
                    placeholder='{"accuracy": 0.95, "f1_score": 0.92, "latency_ms": 150}'
                    value={newVersion.performance_metrics}
                    onChange={(e) => setNewVersion({ ...newVersion, performance_metrics: e.target.value })}
                    rows={3}
                  />
                </div>

                <Button
                  onClick={handleCreateVersion}
                  disabled={creating || !newVersion.version_number || !newVersion.changelog}
                  className="w-full"
                >
                  {creating ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Creating Version...
                    </>
                  ) : (
                    'Create Version'
                  )}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Compare Versions Tab */}
          <TabsContent value="compare" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Compare Versions</CardTitle>
                <CardDescription>Select two versions to compare their performance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="version1">Version 1</Label>
                    <Select value={compareVersion1} onValueChange={setCompareVersion1}>
                      <SelectTrigger id="version1">
                        <SelectValue placeholder="Select version" />
                      </SelectTrigger>
                      <SelectContent>
                        {versions.map((v) => (
                          <SelectItem key={v.version_number} value={v.version_number}>
                            {v.version_number}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="version2">Version 2</Label>
                    <Select value={compareVersion2} onValueChange={setCompareVersion2}>
                      <SelectTrigger id="version2">
                        <SelectValue placeholder="Select version" />
                      </SelectTrigger>
                      <SelectContent>
                        {versions.map((v) => (
                          <SelectItem key={v.version_number} value={v.version_number}>
                            {v.version_number}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button
                  onClick={handleCompareVersions}
                  disabled={comparing || !compareVersion1 || !compareVersion2}
                  className="w-full"
                >
                  {comparing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Comparing...
                    </>
                  ) : (
                    <>
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Compare Versions
                    </>
                  )}
                </Button>

                {comparisonData && (
                  <div className="mt-6 space-y-4">
                    <h3 className="font-semibold flex items-center gap-2">
                      <BarChart3 className="h-5 w-5" />
                      Comparison Results
                    </h3>
                    {comparisonData.metrics_comparison && (
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(comparisonData.metrics_comparison).map(([metric, data]: [string, any]) => (
                          <Card key={metric}>
                            <CardHeader className="pb-2">
                              <CardTitle className="text-sm">{metric}</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-1 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">{compareVersion1}:</span>
                                  <span className="font-medium">{data?.v1 || 'N/A'}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">{compareVersion2}:</span>
                                  <span className="font-medium">{data?.v2 || 'N/A'}</span>
                                </div>
                                {data?.difference && (
                                  <div className="flex justify-between pt-1 border-t">
                                    <span className="text-muted-foreground">Difference:</span>
                                    <span className={`font-medium ${data.difference > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                      {data.difference > 0 ? '+' : ''}{data.difference}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}
                    {comparisonData.summary && (
                      <p className="text-sm text-muted-foreground">{comparisonData.summary}</p>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Version Details Tab */}
          <TabsContent value="details" className="space-y-4">
            {selectedVersion ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileCode className="h-5 w-5" />
                    Version {selectedVersion.version_number} Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="text-sm font-semibold">Changelog</Label>
                    <p className="text-sm text-muted-foreground mt-1">{selectedVersion.changelog}</p>
                  </div>

                  {selectedVersion.architecture_changes && (
                    <div>
                      <Label className="text-sm font-semibold">Architecture Changes</Label>
                      <p className="text-sm text-muted-foreground mt-1">{selectedVersion.architecture_changes}</p>
                    </div>
                  )}

                  {selectedVersion.training_config && (
                    <div>
                      <Label className="text-sm font-semibold">Training Configuration</Label>
                      <pre className="text-xs bg-muted p-3 rounded-lg mt-1 overflow-x-auto">
                        {JSON.stringify(selectedVersion.training_config, null, 2)}
                      </pre>
                    </div>
                  )}

                  {selectedVersion.performance_metrics && (
                    <div>
                      <Label className="text-sm font-semibold">Performance Metrics</Label>
                      <div className="grid grid-cols-2 gap-3 mt-2">
                        {Object.entries(selectedVersion.performance_metrics).map(([key, value]) => (
                          <div key={key} className="p-3 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">{key}</p>
                            <p className="text-lg font-semibold">
                              {typeof value === 'number' ? value.toFixed(3) : String(value)}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-4 border-t text-xs text-muted-foreground space-y-1">
                    <p>Created: {new Date(selectedVersion.created_at).toLocaleString()}</p>
                    {selectedVersion.author_name && <p>Author: {selectedVersion.author_name}</p>}
                    {selectedVersion.file_path && <p>File: {selectedVersion.file_path}</p>}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <FileCode className="h-16 w-16 mx-auto mb-4 opacity-30" />
                <p>Select a version from the list to view details</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
