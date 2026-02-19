import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { OrganizationSwitcher } from '@/components/organization/OrganizationSwitcher';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Search,
  Plus,
  Building2,
  Calendar,
  Loader2,
  RefreshCw,
  Users,
  Trash2
} from 'lucide-react';
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
import { toast } from '@/components/ui/use-toast';
import { format } from 'date-fns';
import { api } from '@/lib/api-client';

interface Organization {
  id: string;
  name: string;
  display_name: string;
  description: string;
  industry: string;
  website: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface CreateOrganizationData {
  name: string;
  display_name: string;
  description: string;
  industry: string;
  website: string;
}

export default function Organizations() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [organizationToDelete, setOrganizationToDelete] = useState<Organization | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [createOrgData, setCreateOrgData] = useState<CreateOrganizationData>({
    name: '', // Will be auto-generated from display_name
    display_name: '',
    description: '',
    industry: '',
    website: '',
  });

  // Fetch organizations
  const fetchOrganizations = async () => {
    setLoading(true);
    try {
      const data = await api.get<Organization[]>('/organizations/all', { skipOrgHeader: true });
      setOrganizations(data);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch organizations',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrganizations();
  }, []);

  // Create organization
  const handleCreateOrganization = async () => {
    if (!createOrgData.display_name) {
      toast({
        title: 'Validation Error',
        description: 'Organization display name is required',
        variant: 'destructive',
      });
      return;
    }

    try {
      // Don't send name field - it will be auto-generated from display_name
      const { name, ...dataToSend } = createOrgData;
      await api.post('/organizations', dataToSend, { skipOrgHeader: true });

      toast({
        title: 'Success',
        description: 'Organization created successfully',
      });

      setIsCreateDialogOpen(false);
      setCreateOrgData({
        name: '',
        display_name: '',
        description: '',
        industry: '',
        website: '',
      });
      fetchOrganizations();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create organization',
        variant: 'destructive',
      });
    }
  };

  // Delete organization
  const handleDeleteOrganization = async () => {
    if (!organizationToDelete) return;

    setIsDeleting(true);
    try {
      await api.delete(`/organizations/${organizationToDelete.id}`, { skipOrgHeader: true });

      toast({
        title: 'Success',
        description: `Organization "${organizationToDelete.display_name}" deleted successfully`,
      });

      setIsDeleteDialogOpen(false);
      setOrganizationToDelete(null);
      fetchOrganizations();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete organization',
        variant: 'destructive',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  // Open delete confirmation dialog
  const confirmDeleteOrganization = (org: Organization) => {
    setOrganizationToDelete(org);
    setIsDeleteDialogOpen(true);
  };

  // Filter organizations based on search
  const filteredOrganizations = organizations.filter(org =>
    org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    org.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    org.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-8 pb-12">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Organization Management</h1>
        <p className="text-muted-foreground">Create and manage organizations (universal_admin only)</p>
      </div>

      {/* Organization Switcher - Prominent Display */}
      <Card className="mb-6 bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
        <CardHeader>
          <CardTitle className="text-lg">Switch Organization Context</CardTitle>
          <CardDescription>
            Change the organization you're viewing to manage organization-specific data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <OrganizationSwitcher variant="prominent" className="max-w-md" showSearch={true} />
        </CardContent>
      </Card>

      {/* Filters and Search */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Search & Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 flex-wrap">
            <div className="flex-1 min-w-[300px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Search organizations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Button onClick={fetchOrganizations} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Organization
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Create New Organization</DialogTitle>
                  <DialogDescription>
                    Add a new organization to the system. You will be automatically added as the owner.
                    The organization ID will be auto-generated from the display name.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="display_name">Display Name*</Label>
                    <Input
                      id="display_name"
                      value={createOrgData.display_name}
                      onChange={(e) => setCreateOrgData({ ...createOrgData, display_name: e.target.value })}
                      placeholder="KasaAI Inc"
                      required
                    />
                    <p className="text-xs text-muted-foreground">A friendly name for the organization</p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="description">Description</Label>
                    <Input
                      id="description"
                      value={createOrgData.description}
                      onChange={(e) => setCreateOrgData({ ...createOrgData, description: e.target.value })}
                      placeholder="Voice AI solutions for Africa"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="industry">Industry</Label>
                    <Input
                      id="industry"
                      value={createOrgData.industry}
                      onChange={(e) => setCreateOrgData({ ...createOrgData, industry: e.target.value })}
                      placeholder="Technology"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="website">Website</Label>
                    <Input
                      id="website"
                      type="url"
                      value={createOrgData.website}
                      onChange={(e) => setCreateOrgData({ ...createOrgData, website: e.target.value })}
                      placeholder="https://kasaai.com"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateOrganization}>Create Organization</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardContent>
      </Card>

      {/* Organizations Table */}
      <Card>
        <CardHeader>
          <CardTitle>Organizations</CardTitle>
          <CardDescription>
            Total: {filteredOrganizations.length} organizations
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Organization</TableHead>
                  <TableHead>Industry</TableHead>
                  <TableHead>Website</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrganizations.map((org) => (
                  <TableRow key={org.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-primary" />
                          {org.display_name}
                        </div>
                        <div className="text-sm text-muted-foreground">{org.name}</div>
                        {org.description && (
                          <div className="text-xs text-muted-foreground mt-1">{org.description}</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {org.industry || <span className="text-muted-foreground italic">Not specified</span>}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {org.website ? (
                          <a href={org.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                            {org.website}
                          </a>
                        ) : (
                          <span className="text-muted-foreground italic">Not specified</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={org.is_active ? "default" : "secondary"}>
                        {org.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <Calendar className="h-3 w-3 inline mr-1" />
                        {org.created_at && !isNaN(new Date(org.created_at).getTime())
                          ? format(new Date(org.created_at), 'MMM d, yyyy')
                          : 'N/A'
                        }
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => confirmDeleteOrganization(org)}
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Organization</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete <strong>{organizationToDelete?.display_name}</strong>?
              <br /><br />
              This action will soft-delete the organization. The organization can be restored by a database administrator if needed.
              <br /><br />
              <strong className="text-destructive">Warning:</strong> This may affect automations and campaigns associated with this organization.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteOrganization}
              disabled={isDeleting}
              className="bg-destructive hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete Organization'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
