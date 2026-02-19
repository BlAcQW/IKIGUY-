import React, { useState, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api-client';
import { useOrganization } from '@/contexts/OrganizationContext';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Users,
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Download,
  Upload,
  Edit,
  Trash2,
  Eye,
  UserPlus,
  Database,
  Calendar,
  TrendingUp,
  LayoutGrid,
  List
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import CreateAudienceDialog from '@/components/audiences/CreateAudienceDialog';
import EditAudienceDialog from '@/components/audiences/EditAudienceDialog';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


interface Audience {
  id: string;
  name: string;
  description?: string;
  size: number;
  status: 'active' | 'draft' | 'archived';
  created_at: string;
  updated_at: string;
  tenant_id: string;
  source: 'csv_upload' | 'manual' | 'api' | 'crm_sync';
  tags?: string[];
  metadata?: {
    last_used?: string;
    campaign_count?: number;
    conversion_rate?: number;
  };
}

interface AudienceStats {
  total_audiences: number;
  total_contacts: number;
  active_audiences: number;
  recent_uploads: number;
}

const Audiences: React.FC = () => {
  const { toast } = useToast();
  const { currentOrganization } = useOrganization();
  const [audiences, setAudiences] = useState<Audience[]>([]);
  const [stats, setStats] = useState<AudienceStats>({
    total_audiences: 0,
    total_contacts: 0,
    active_audiences: 0,
    recent_uploads: 0
  });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table'); // Default to table view
  const [selectedAudience, setSelectedAudience] = useState<Audience | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [audienceContacts, setAudienceContacts] = useState<Array<{phone: string; name: string; email: string}>>([]);
  const [loadingContacts, setLoadingContacts] = useState(false);

  // Using API_BASE_URL from api-config;

  // Fetch audiences
  // Reason: Using api-client which automatically adds X-Organization-ID header
  // This ensures audiences are filtered by current organization
  const fetchAudiences = async () => {
    setLoading(true);
    try {
      const data = await api.get<Audience[]>('/audiences/');
      setAudiences(data);

      // Calculate stats
      const activeAudiences = data.filter((a: Audience) => a.status === 'active').length;
      const totalContacts = data.reduce((sum: number, a: Audience) => sum + a.size, 0);
      const recentUploads = data.filter((a: Audience) => {
        const createdDate = new Date(a.created_at);
        const sevenDaysAgo = new Date();
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        return createdDate > sevenDaysAgo;
      }).length;

      setStats({
        total_audiences: data.length,
        total_contacts: totalContacts,
        active_audiences: activeAudiences,
        recent_uploads: recentUploads
      });

    } catch (error) {
      console.error('Error fetching audiences:', error);
      toast({
        title: "Failed to load audiences",
        description: "Please check your connection and try again.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch audience contacts when details dialog opens
  useEffect(() => {
    if (showDetailsDialog && selectedAudience) {
      const fetchContacts = async () => {
        setLoadingContacts(true);
        try {
          const response = await api.get<{contacts: Array<{phone: string; name: string; email: string}>, total: number, returned: number}>(
            `/audiences/${selectedAudience.id}/contacts?limit=5`
          );
          setAudienceContacts(response.contacts || []);
        } catch (error) {
          console.error('Error fetching audience contacts:', error);
          toast({
            title: "Failed to load contacts",
            description: "Could not fetch audience contacts",
            variant: "destructive"
          });
          setAudienceContacts([]);
        } finally {
          setLoadingContacts(false);
        }
      };
      fetchContacts();
    }
  }, [showDetailsDialog, selectedAudience, toast]);

  // Reason: Fetch audiences when component mounts or when organization changes
  // This ensures audiences are refreshed when user switches organizations
  useEffect(() => {
    if (currentOrganization) {
      fetchAudiences();
    }
  }, [currentOrganization]);

  // Filter audiences based on search term
  const filteredAudiences = audiences.filter(audience =>
    audience.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    audience.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Delete audience
  const handleDeleteAudience = async (audienceId: string) => {
    try {
      await api.delete(`/audiences/${audienceId}`);

      toast({
        title: "Audience deleted",
        description: "The audience has been successfully deleted."
      });

      fetchAudiences();
    } catch (error) {
      console.error('Error deleting audience:', error);
      toast({
        title: "Failed to delete audience",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  // Edit audience
  const handleEditAudience = (audience: Audience) => {
    setSelectedAudience(audience);
    setShowEditDialog(true);
  };

  // Export audience
  const handleExportAudience = async (audienceId: string) => {
    try {
      // Reason: Export endpoint returns a blob, need to use fetch with api headers manually
      const currentOrgId = localStorage.getItem('kasaai_current_organization_id');
      const accessToken = localStorage.getItem('mongo_access_token');

      const headers: HeadersInit = {
        'Authorization': `Bearer ${accessToken}`,
      };

      if (currentOrgId) {
        headers['X-Organization-ID'] = currentOrgId;
      }

      const response = await fetch(`${API_BASE_URL}/audiences/${audienceId}/export`, {
        headers
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `audience_${audienceId}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);

      toast({
        title: "Export completed",
        description: "Audience data has been downloaded."
      });
    } catch (error) {
      console.error('Error exporting audience:', error);
      toast({
        title: "Failed to export audience",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-800 border-green-200">Active</Badge>;
      case 'draft':
        return <Badge variant="outline">Draft</Badge>;
      case 'archived':
        return <Badge variant="secondary">Archived</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getSourceBadge = (source: string) => {
    const sourceLabels = {
      'csv_upload': 'CSV Upload',
      'manual': 'Manual',
      'api': 'API',
      'crm_sync': 'CRM Sync'
    };
    return <Badge variant="outline">{sourceLabels[source as keyof typeof sourceLabels] || source}</Badge>;
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-background">
        <DashboardSidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-gray-600">Loading audiences...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />

      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 pb-12 max-w-7xl">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Audiences</h1>
              <p className="text-gray-600">
                Manage your contact lists and audience segments
              </p>
            </div>
            
            <div className="flex gap-2">
              <Button 
                variant="outline"
                className="gap-2"
                onClick={() => setShowCreateDialog(true)}
              >
                <Upload className="h-4 w-4" />
                Import CSV
              </Button>
              <Button 
                className="gap-2"
                onClick={() => setShowCreateDialog(true)}
              >
                <Plus className="h-4 w-4" />
                Create Audience
              </Button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Audiences</CardTitle>
                <Database className="h-4 w-4 text-gray-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_audiences}</div>
                <p className="text-xs text-gray-600">
                  {stats.active_audiences} active
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Contacts</CardTitle>
                <Users className="h-4 w-4 text-gray-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total_contacts.toLocaleString()}</div>
                <p className="text-xs text-gray-600">
                  Across all audiences
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Recent Uploads</CardTitle>
                <Calendar className="h-4 w-4 text-gray-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.recent_uploads}</div>
                <p className="text-xs text-gray-600">
                  Last 7 days
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg. Conversion</CardTitle>
                <TrendingUp className="h-4 w-4 text-gray-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">12.4%</div>
                <p className="text-xs text-gray-600">
                  Campaign success rate
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Search and Filters */}
          <div className="flex items-center gap-4 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-600 h-4 w-4" />
              <Input
                placeholder="Search audiences..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex gap-2">
              <Button variant="outline" className="gap-2">
                <Filter className="h-4 w-4" />
                Filter
              </Button>

              {/* View Mode Toggle */}
              <div className="flex border rounded-md">
                <Button
                  variant={viewMode === 'table' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('table')}
                  className="rounded-r-none"
                >
                  <List className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'card' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('card')}
                  className="rounded-l-none"
                >
                  <LayoutGrid className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Audiences Table/Grid */}
          {filteredAudiences.length === 0 ? (
            <Card className="p-8 text-center">
              <div className="mx-auto w-12 h-12 bg-muted rounded-lg flex items-center justify-center mb-4">
                <Users className="h-6 w-6 text-gray-600" />
              </div>
              <h3 className="text-lg font-semibold mb-2">No audiences yet</h3>
              <p className="text-gray-600 mb-4">
                Create your first audience to start building targeted campaigns.
              </p>
              <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                <Plus className="h-4 w-4" />
                Create First Audience
              </Button>
            </Card>
          ) : viewMode === 'table' ? (
            /* Table View */
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Contacts</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAudiences.map((audience) => (
                    <TableRow
                      key={audience.id}
                      className="hover:bg-accent/50 cursor-pointer"
                      onClick={() => {
                        setSelectedAudience(audience);
                        setShowDetailsDialog(true);
                      }}
                    >
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4 text-indigo-600" />
                          <div>
                            <div className="font-medium">{audience.name}</div>
                            <div className="text-xs text-gray-600 line-clamp-1">
                              {audience.description || 'No description'}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(audience.status)}</TableCell>
                      <TableCell>{getSourceBadge(audience.source)}</TableCell>
                      <TableCell className="font-medium">{audience.size.toLocaleString()}</TableCell>
                      <TableCell className="text-sm text-gray-600">
                        {new Date(audience.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditAudience(audience)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleExportAudience(audience.id)}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteAudience(audience.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          ) : (
            /* Card View */
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredAudiences.map((audience) => (
                <Card key={audience.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Users className="h-5 w-5 text-indigo-600" />
                        <div>
                          <CardTitle className="text-lg">{audience.name}</CardTitle>
                          <CardDescription className="mt-1">
                            {audience.description || 'No description'}
                          </CardDescription>
                        </div>
                      </div>
                      
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => {
                            setSelectedAudience(audience);
                            setShowDetailsDialog(true);
                          }}>
                            <Eye className="h-4 w-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleEditAudience(audience)}>
                            <Edit className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleExportAudience(audience.id)}>
                            <Download className="h-4 w-4 mr-2" />
                            Export
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDeleteAudience(audience.id)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                    
                    <div className="flex items-center gap-2 mt-2">
                      {getStatusBadge(audience.status)}
                      {getSourceBadge(audience.source)}
                      <span className="text-xs text-gray-600">
                        {new Date(audience.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">Contacts</span>
                      <span className="font-medium">{audience.size.toLocaleString()}</span>
                    </div>
                    
                    {audience.metadata?.campaign_count !== undefined && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Campaigns</span>
                        <span className="font-medium">{audience.metadata.campaign_count}</span>
                      </div>
                    )}
                    
                    {audience.metadata?.conversion_rate !== undefined && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Conversion Rate</span>
                        <span className="font-medium">{audience.metadata.conversion_rate}%</span>
                      </div>
                    )}

                    <div className="flex gap-2 pt-2">
                      <Button 
                        size="sm" 
                        className="flex-1 gap-2"
                        onClick={() => {
                          setSelectedAudience(audience);
                          setShowDetailsDialog(true);
                        }}
                      >
                        <Eye className="h-3 w-3" />
                        View
                      </Button>
                      <Button size="sm" variant="outline" className="gap-2">
                        <UserPlus className="h-3 w-3" />
                        Use in Campaign
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Create Audience Dialog */}
        <CreateAudienceDialog
          open={showCreateDialog}
          onOpenChange={setShowCreateDialog}
          onAudienceCreated={fetchAudiences}
        />

        {/* Edit Audience Dialog */}
        <EditAudienceDialog
          open={showEditDialog}
          onOpenChange={setShowEditDialog}
          audience={selectedAudience}
          onAudienceUpdated={fetchAudiences}
        />

        {/* Audience Details Dialog */}
        <Dialog open={showDetailsDialog} onOpenChange={(open) => {
          setShowDetailsDialog(open);
          if (!open) {
            setAudienceContacts([]);
          }
        }}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                {selectedAudience?.name}
              </DialogTitle>
              <DialogDescription>
                Audience details and statistics
              </DialogDescription>
            </DialogHeader>
            
            {selectedAudience && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Status</label>
                    <div className="mt-1">{getStatusBadge(selectedAudience.status)}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Source</label>
                    <div className="mt-1">{getSourceBadge(selectedAudience.source)}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Total Contacts</label>
                    <div className="mt-1 text-lg font-semibold">{selectedAudience.size.toLocaleString()}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Created</label>
                    <div className="mt-1">{new Date(selectedAudience.created_at).toLocaleDateString()}</div>
                  </div>
                </div>
                
                {selectedAudience.description && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Description</label>
                    <p className="mt-1 text-sm">{selectedAudience.description}</p>
                  </div>
                )}

                {/* First 5 Contacts Preview */}
                <div>
                  <label className="text-sm font-medium text-gray-600 mb-2 block">
                    First 5 Contacts
                  </label>
                  {loadingContacts ? (
                    <div className="text-sm text-gray-500 py-4">Loading contacts...</div>
                  ) : audienceContacts.length > 0 ? (
                    <div className="border rounded-lg overflow-hidden">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Phone</TableHead>
                            <TableHead>Email</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {audienceContacts.map((contact, index) => (
                            <TableRow key={index}>
                              <TableCell>{contact.name || '-'}</TableCell>
                              <TableCell className="font-mono text-sm">{contact.phone || '-'}</TableCell>
                              <TableCell>{contact.email || '-'}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500 py-4 border rounded-lg text-center">
                      No contacts found
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button
                    className="gap-2"
                    onClick={() => handleEditAudience(selectedAudience)}
                  >
                    <Edit className="h-4 w-4" />
                    Edit Audience
                  </Button>
                  <Button 
                    variant="outline" 
                    className="gap-2"
                    onClick={() => handleExportAudience(selectedAudience.id)}
                  >
                    <Download className="h-4 w-4" />
                    Export
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default Audiences;