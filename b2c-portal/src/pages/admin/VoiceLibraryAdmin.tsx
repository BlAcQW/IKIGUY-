/**
 * Voice Library Admin Page
 *
 * Admin interface for managing the centralized voice library.
 * Allows administrators to:
 * - Browse and search all voices
 * - Edit voice metadata
 * - Feature/verify voices
 * - Delete voices
 * - View usage analytics
 * - Manage voice visibility
 */

import React, { useState, useEffect } from 'react';
import { useVoiceLibrary } from '@/hooks/useVoiceLibrary';
import { VoiceGallery } from '@/components/voice-library';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Library,
  Star,
  Shield,
  Trash2,
  Edit,
  Eye,
  TrendingUp,
  Users,
  Download,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { toast } from 'sonner';

interface Voice {
  voice_id: string;
  name: string;
  description?: string;
  characteristics?: {
    gender?: string;
    language?: string;
    accent?: string;
  };
  metadata?: {
    featured?: boolean;
    verified?: boolean;
    tags?: string[];
    categories?: string[];
  };
  stats?: {
    views?: number;
    uses?: number;
    favorites?: number;
    rating?: {
      average?: number;
      count?: number;
    };
  };
  access?: {
    visibility?: string;
  };
  owner?: {
    user_id?: string;
    organization_id?: string;
  };
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export default function VoiceLibraryAdmin() {
  const { fetchVoices, updateVoice, deleteVoice } = useVoiceLibrary();
  const [voices, setVoices] = useState<Voice[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    public: 0,
    private: 0,
    featured: 0,
    verified: 0,
  });
  const [selectedVoice, setSelectedVoice] = useState<Voice | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Edit form state
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    featured: false,
    verified: false,
    visibility: 'private',
    tags: '',
    categories: '',
  });

  useEffect(() => {
    loadVoices();
  }, [refreshKey]);

  const loadVoices = async () => {
    try {
      setLoading(true);
      const data = await fetchVoices({}, 0, 1000); // Load all voices for admin

      if (data && data.voices) {
        setVoices(data.voices);

        // Calculate stats
        const newStats = {
          total: data.voices.length,
          public: data.voices.filter(v => v.access?.visibility === 'public').length,
          private: data.voices.filter(v => v.access?.visibility === 'private').length,
          featured: data.voices.filter(v => v.metadata?.featured).length,
          verified: data.voices.filter(v => v.metadata?.verified).length,
        };
        setStats(newStats);
      }
    } catch (error) {
      console.error('Failed to load voices:', error);
      toast.error('Failed to load voices');
    } finally {
      setLoading(false);
    }
  };

  const handleEditVoice = (voice: Voice) => {
    setSelectedVoice(voice);
    setEditForm({
      name: voice.name || '',
      description: voice.description || '',
      featured: voice.metadata?.featured || false,
      verified: voice.metadata?.verified || false,
      visibility: voice.access?.visibility || 'private',
      tags: voice.metadata?.tags?.join(', ') || '',
      categories: voice.metadata?.categories?.join(', ') || '',
    });
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!selectedVoice) return;

    try {
      setLoading(true);

      const updates = {
        name: editForm.name,
        description: editForm.description,
        metadata: {
          featured: editForm.featured,
          verified: editForm.verified,
          tags: editForm.tags.split(',').map(t => t.trim()).filter(Boolean),
          categories: editForm.categories.split(',').map(c => c.trim()).filter(Boolean),
        },
        access: {
          visibility: editForm.visibility,
        },
      };

      await updateVoice(selectedVoice.voice_id, updates);

      toast.success('Voice updated successfully');
      setEditDialogOpen(false);
      setRefreshKey(prev => prev + 1);
    } catch (error) {
      console.error('Failed to update voice:', error);
      toast.error('Failed to update voice');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteVoice = (voice: Voice) => {
    setSelectedVoice(voice);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!selectedVoice) return;

    try {
      setLoading(true);
      await deleteVoice(selectedVoice.voice_id, true); // Hard delete for admin

      toast.success('Voice deleted successfully');
      setDeleteDialogOpen(false);
      setRefreshKey(prev => prev + 1);
    } catch (error) {
      console.error('Failed to delete voice:', error);
      toast.error('Failed to delete voice');
    } finally {
      setLoading(false);
    }
  };

  const quickFeatureToggle = async (voice: Voice) => {
    try {
      await updateVoice(voice.voice_id, {
        metadata: {
          ...voice.metadata,
          featured: !voice.metadata?.featured,
        },
      });

      toast.success(voice.metadata?.featured ? 'Removed from featured' : 'Added to featured');
      setRefreshKey(prev => prev + 1);
    } catch (error) {
      console.error('Failed to toggle featured:', error);
      toast.error('Failed to update voice');
    }
  };

  const quickVerifyToggle = async (voice: Voice) => {
    try {
      await updateVoice(voice.voice_id, {
        metadata: {
          ...voice.metadata,
          verified: !voice.metadata?.verified,
        },
      });

      toast.success(voice.metadata?.verified ? 'Unverified voice' : 'Verified voice');
      setRefreshKey(prev => prev + 1);
    } catch (error) {
      console.error('Failed to toggle verified:', error);
      toast.error('Failed to update voice');
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Library className="h-8 w-8" />
            Voice Library Administration
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage voices, configure settings, and view analytics
          </p>
        </div>

        <Button onClick={() => setRefreshKey(prev => prev + 1)} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Total Voices</CardDescription>
            <CardTitle className="text-3xl">{stats.total}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Library className="h-4 w-4" />
              <span>All voices</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Public Voices</CardDescription>
            <CardTitle className="text-3xl">{stats.public}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Eye className="h-4 w-4" />
              <span>Visible to all</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Private Voices</CardDescription>
            <CardTitle className="text-3xl">{stats.private}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Users className="h-4 w-4" />
              <span>User-owned</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Featured</CardDescription>
            <CardTitle className="text-3xl">{stats.featured}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              <span>Featured voices</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Verified</CardDescription>
            <CardTitle className="text-3xl">{stats.verified}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Shield className="h-4 w-4" />
              <span>Verified voices</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Voices</TabsTrigger>
          <TabsTrigger value="public">Public</TabsTrigger>
          <TabsTrigger value="featured">Featured</TabsTrigger>
          <TabsTrigger value="pending">Pending Review</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          <VoiceGallery
            key={refreshKey}
            onVoiceSelect={handleEditVoice}
            showFilters={true}
            showStats={true}
            showActions={false}
            defaultLayout="list"
            pageSize={50}
          />
        </TabsContent>

        <TabsContent value="public" className="space-y-4">
          <VoiceGallery
            key={refreshKey}
            onVoiceSelect={handleEditVoice}
            showFilters={true}
            showStats={true}
            showActions={false}
            defaultFilters={{ visibility: 'public' }}
            defaultLayout="list"
            pageSize={50}
          />
        </TabsContent>

        <TabsContent value="featured" className="space-y-4">
          <VoiceGallery
            key={refreshKey}
            onVoiceSelect={handleEditVoice}
            showFilters={true}
            showStats={true}
            showActions={false}
            defaultFilters={{ featured: true }}
            defaultLayout="grid"
            pageSize={50}
          />
        </TabsContent>

        <TabsContent value="pending" className="space-y-4">
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Voices pending admin review will appear here
            </AlertDescription>
          </Alert>
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Voice</DialogTitle>
            <DialogDescription>
              Modify voice metadata and settings
            </DialogDescription>
          </DialogHeader>

          {selectedVoice && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Voice Name</Label>
                <Input
                  id="name"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="visibility">Visibility</Label>
                <Select
                  value={editForm.visibility}
                  onValueChange={(value) => setEditForm({ ...editForm, visibility: value })}
                >
                  <SelectTrigger id="visibility">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="public">Public - Visible to all users</SelectItem>
                    <SelectItem value="organization">Organization - Team members only</SelectItem>
                    <SelectItem value="private">Private - Owner only</SelectItem>
                    <SelectItem value="restricted">Restricted - Specific users</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tags">Tags (comma-separated)</Label>
                <Input
                  id="tags"
                  value={editForm.tags}
                  onChange={(e) => setEditForm({ ...editForm, tags: e.target.value })}
                  placeholder="professional, narration, warm"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="categories">Categories (comma-separated)</Label>
                <Input
                  id="categories"
                  value={editForm.categories}
                  onChange={(e) => setEditForm({ ...editForm, categories: e.target.value })}
                  placeholder="Narration, Audiobook, Professional"
                />
              </div>

              <div className="flex items-center justify-between border rounded-lg p-4">
                <div className="space-y-0.5">
                  <Label htmlFor="featured">Featured Voice</Label>
                  <p className="text-sm text-muted-foreground">
                    Show this voice in featured sections
                  </p>
                </div>
                <Switch
                  id="featured"
                  checked={editForm.featured}
                  onCheckedChange={(checked) => setEditForm({ ...editForm, featured: checked })}
                />
              </div>

              <div className="flex items-center justify-between border rounded-lg p-4">
                <div className="space-y-0.5">
                  <Label htmlFor="verified">Verified Voice</Label>
                  <p className="text-sm text-muted-foreground">
                    Mark as verified by administrators
                  </p>
                </div>
                <Switch
                  id="verified"
                  checked={editForm.verified}
                  onCheckedChange={(checked) => setEditForm({ ...editForm, verified: checked })}
                />
              </div>

              {/* Voice Stats */}
              <div className="border rounded-lg p-4 space-y-2">
                <h4 className="font-medium">Voice Statistics</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Views:</span>{' '}
                    <span className="font-medium">{selectedVoice.stats?.views || 0}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Uses:</span>{' '}
                    <span className="font-medium">{selectedVoice.stats?.uses || 0}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Favorites:</span>{' '}
                    <span className="font-medium">{selectedVoice.stats?.favorites || 0}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Rating:</span>{' '}
                    <span className="font-medium">
                      {selectedVoice.stats?.rating?.average?.toFixed(1) || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex gap-2 pt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDeleteVoice(selectedVoice)}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Voice
                </Button>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdit} disabled={loading}>
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Voice</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedVoice?.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              This will permanently delete the voice and all associated files from both local storage
              and Hetzner backup.
            </AlertDescription>
          </Alert>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete} disabled={loading}>
              {loading ? 'Deleting...' : 'Delete Voice'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
