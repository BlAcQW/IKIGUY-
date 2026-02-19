import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Key,
  Plus,
  Copy,
  Eye,
  EyeOff,
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Calendar,
  User,
  Shield,
  AlertTriangle,
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

type ApiKeyScope = 'read' | 'write' | 'admin' | 'full';
type ApiKeyStatus = 'active' | 'inactive' | 'expired';

interface ApiKey {
  id: string;
  name: string;
  key: string;
  scope: ApiKeyScope;
  status: ApiKeyStatus;
  createdAt: string;
  lastUsed?: string;
  expiresAt?: string;
  createdBy: string;
  description?: string;
  requestCount: number;
}

export default function ApiKeys() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([
    {
      id: '1',
      name: 'Production API Key',
      key: 'sk_live_4a3b2c1d5e6f7g8h9i0j',
      scope: 'full',
      status: 'active',
      createdAt: '2025-09-15',
      lastUsed: '2025-10-09 14:32:00',
      createdBy: 'alfred.anyan@gmail.com',
      description: 'Main production API key for core services',
      requestCount: 45280,
    },
    {
      id: '2',
      name: 'Development Key',
      key: 'sk_test_9i8h7g6f5e4d3c2b1a0z',
      scope: 'read',
      status: 'active',
      createdAt: '2025-08-20',
      lastUsed: '2025-10-08 09:15:00',
      createdBy: 'dev.team@example.com',
      description: 'Read-only key for development and testing',
      requestCount: 12450,
    },
    {
      id: '3',
      name: 'Integration Key',
      key: 'sk_live_x1y2z3a4b5c6d7e8f9g0',
      scope: 'write',
      status: 'active',
      createdAt: '2025-07-10',
      lastUsed: '2025-10-09 11:20:00',
      createdBy: 'integration@example.com',
      description: 'Key for third-party integrations',
      requestCount: 8920,
    },
    {
      id: '4',
      name: 'Expired Test Key',
      key: 'sk_test_0z9y8x7w6v5u4t3s2r1q',
      scope: 'read',
      status: 'expired',
      createdAt: '2025-05-01',
      lastUsed: '2025-06-30 23:59:00',
      expiresAt: '2025-06-30',
      createdBy: 'test.user@example.com',
      description: 'Temporary test key (expired)',
      requestCount: 3420,
    },
    {
      id: '5',
      name: 'Revoked Admin Key',
      key: 'sk_live_q1w2e3r4t5y6u7i8o9p0',
      scope: 'admin',
      status: 'inactive',
      createdAt: '2025-03-15',
      lastUsed: '2025-08-01 16:45:00',
      createdBy: 'admin@example.com',
      description: 'Revoked due to security concerns',
      requestCount: 28540,
    },
  ]);

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedKeyForDeletion, setSelectedKeyForDeletion] = useState<string | null>(null);
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const [newApiKey, setNewApiKey] = useState({
    name: '',
    scope: 'read' as ApiKeyScope,
    description: '',
    expiresIn: '90', // days
  });
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);

  const generateRandomKey = (scope: ApiKeyScope): string => {
    const prefix = scope === 'read' || scope === 'write' ? 'sk_test_' : 'sk_live_';
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let key = '';
    for (let i = 0; i < 20; i++) {
      key += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return prefix + key;
  };

  const handleCreateApiKey = () => {
    if (!newApiKey.name) {
      toast({
        title: 'Error',
        description: 'Please provide a name for the API key',
        variant: 'destructive',
      });
      return;
    }

    const key = generateRandomKey(newApiKey.scope);
    const expiresAt = newApiKey.expiresIn
      ? new Date(Date.now() + parseInt(newApiKey.expiresIn) * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0]
      : undefined;

    const apiKey: ApiKey = {
      id: Date.now().toString(),
      name: newApiKey.name,
      key: key,
      scope: newApiKey.scope,
      status: 'active',
      createdAt: new Date().toISOString().split('T')[0],
      createdBy: 'alfred.anyan@gmail.com', // Should come from auth context
      description: newApiKey.description,
      expiresAt: expiresAt,
      requestCount: 0,
    };

    setApiKeys([apiKey, ...apiKeys]);
    setGeneratedKey(key);
    setNewApiKey({ name: '', scope: 'read', description: '', expiresIn: '90' });

    toast({
      title: 'API Key Created',
      description: 'Your new API key has been generated. Make sure to copy it now!',
    });
  };

  const handleRevokeKey = (keyId: string) => {
    setApiKeys(apiKeys.map(key =>
      key.id === keyId ? { ...key, status: 'inactive' as ApiKeyStatus } : key
    ));

    toast({
      title: 'API Key Revoked',
      description: 'The API key has been revoked and is no longer valid',
    });
  };

  const handleDeleteKey = () => {
    if (!selectedKeyForDeletion) return;

    setApiKeys(apiKeys.filter(key => key.id !== selectedKeyForDeletion));
    setIsDeleteDialogOpen(false);
    setSelectedKeyForDeletion(null);

    toast({
      title: 'API Key Deleted',
      description: 'The API key has been permanently deleted',
    });
  };

  const toggleKeyVisibility = (keyId: string) => {
    const newVisible = new Set(visibleKeys);
    if (newVisible.has(keyId)) {
      newVisible.delete(keyId);
    } else {
      newVisible.add(keyId);
    }
    setVisibleKeys(newVisible);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: 'API key copied to clipboard',
    });
  };

  const maskKey = (key: string): string => {
    if (key.length <= 10) return '***';
    return key.substring(0, 10) + '***' + key.substring(key.length - 4);
  };

  const getScopeColor = (scope: ApiKeyScope) => {
    switch (scope) {
      case 'read':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'write':
        return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'admin':
        return 'bg-purple-500/10 text-purple-500 border-purple-500/20';
      case 'full':
        return 'bg-red-500/10 text-red-500 border-red-500/20';
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

  const getStatusBadge = (status: ApiKeyStatus) => {
    switch (status) {
      case 'active':
        return (
          <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
            <CheckCircle className="h-3 w-3 mr-1" />
            Active
          </Badge>
        );
      case 'inactive':
        return (
          <Badge variant="outline" className="bg-gray-500/10 text-gray-500 border-gray-500/20">
            <XCircle className="h-3 w-3 mr-1" />
            Revoked
          </Badge>
        );
      case 'expired':
        return (
          <Badge variant="outline" className="bg-red-500/10 text-red-500 border-red-500/20">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Expired
          </Badge>
        );
    }
  };

  const getKeyStats = () => {
    return {
      total: apiKeys.length,
      active: apiKeys.filter(k => k.status === 'active').length,
      inactive: apiKeys.filter(k => k.status === 'inactive').length,
      expired: apiKeys.filter(k => k.status === 'expired').length,
      totalRequests: apiKeys.reduce((sum, k) => sum + k.requestCount, 0),
    };
  };

  const stats = getKeyStats();

  return (
    <div className="p-8 pb-12">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">API Keys</h1>
          <p className="text-muted-foreground">Manage API keys and access tokens</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => setGeneratedKey(null)}>
              <Plus className="h-4 w-4 mr-2" />
              Create API Key
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Create New API Key</DialogTitle>
              <DialogDescription>
                Generate a new API key for programmatic access to the system
              </DialogDescription>
            </DialogHeader>
            {generatedKey ? (
              <div className="space-y-4 py-4">
                <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="font-semibold text-green-500">API Key Created Successfully!</span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Make sure to copy your API key now. You won't be able to see it again!
                  </p>
                  <div className="flex items-center gap-2 p-3 bg-background rounded border">
                    <code className="flex-1 text-sm font-mono">{generatedKey}</code>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => copyToClipboard(generatedKey)}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="key-name">Key Name *</Label>
                  <Input
                    id="key-name"
                    value={newApiKey.name}
                    onChange={(e) => setNewApiKey({ ...newApiKey, name: e.target.value })}
                    placeholder="e.g., Production API Key"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="key-scope">Scope *</Label>
                  <Select
                    value={newApiKey.scope}
                    onValueChange={(value) => setNewApiKey({ ...newApiKey, scope: value as ApiKeyScope })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="read">Read Only</SelectItem>
                      <SelectItem value="write">Read & Write</SelectItem>
                      <SelectItem value="admin">Admin Access</SelectItem>
                      <SelectItem value="full">Full Access</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="key-description">Description (optional)</Label>
                  <Input
                    id="key-description"
                    value={newApiKey.description}
                    onChange={(e) => setNewApiKey({ ...newApiKey, description: e.target.value })}
                    placeholder="What will this key be used for?"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="key-expires">Expires In</Label>
                  <Select
                    value={newApiKey.expiresIn}
                    onValueChange={(value) => setNewApiKey({ ...newApiKey, expiresIn: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="30">30 days</SelectItem>
                      <SelectItem value="60">60 days</SelectItem>
                      <SelectItem value="90">90 days</SelectItem>
                      <SelectItem value="180">180 days</SelectItem>
                      <SelectItem value="365">1 year</SelectItem>
                      <SelectItem value="">Never</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}
            <DialogFooter>
              {generatedKey ? (
                <Button onClick={() => setIsCreateDialogOpen(false)} className="w-full">
                  Done
                </Button>
              ) : (
                <>
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateApiKey} disabled={!newApiKey.name}>
                    Generate Key
                  </Button>
                </>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 md:grid-cols-5 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Keys</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">All API keys</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Active
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.active}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <XCircle className="h-4 w-4 text-gray-500" />
              Revoked
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.inactive}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              Expired
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.expired}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalRequests.toLocaleString()}</div>
          </CardContent>
        </Card>
      </div>

      {/* API Keys Table */}
      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>
            Manage your API keys for programmatic access
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Key</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Usage</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {apiKeys.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                    No API keys found. Create your first API key to get started.
                  </TableCell>
                </TableRow>
              ) : (
                apiKeys.map((apiKey) => (
                  <TableRow key={apiKey.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium flex items-center gap-2">
                          <Key className="h-4 w-4 text-muted-foreground" />
                          {apiKey.name}
                        </div>
                        {apiKey.description && (
                          <div className="text-xs text-muted-foreground mt-1">
                            {apiKey.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <code className="text-sm font-mono">
                          {visibleKeys.has(apiKey.id) ? apiKey.key : maskKey(apiKey.key)}
                        </code>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => toggleKeyVisibility(apiKey.id)}
                        >
                          {visibleKeys.has(apiKey.id) ? (
                            <EyeOff className="h-3 w-3" />
                          ) : (
                            <Eye className="h-3 w-3" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6"
                          onClick={() => copyToClipboard(apiKey.key)}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={getScopeColor(apiKey.scope)}>
                        <Shield className="h-3 w-3 mr-1" />
                        {apiKey.scope}
                      </Badge>
                    </TableCell>
                    <TableCell>{getStatusBadge(apiKey.status)}</TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div className="font-medium">{apiKey.requestCount.toLocaleString()} requests</div>
                        {apiKey.lastUsed && (
                          <div className="text-xs text-muted-foreground">
                            Last used: {apiKey.lastUsed}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3 text-muted-foreground" />
                          {apiKey.createdAt}
                        </div>
                        <div className="flex items-center gap-1 text-xs text-muted-foreground mt-1">
                          <User className="h-3 w-3" />
                          {apiKey.createdBy}
                        </div>
                        {apiKey.expiresAt && (
                          <div className="text-xs text-muted-foreground mt-1">
                            Expires: {apiKey.expiresAt}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {apiKey.status === 'active' && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleRevokeKey(apiKey.id)}
                            title="Revoke key"
                          >
                            <XCircle className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => {
                            setSelectedKeyForDeletion(apiKey.id);
                            setIsDeleteDialogOpen(true);
                          }}
                          title="Delete key"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the API key and
              any applications using this key will no longer be able to access the API.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteKey} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
