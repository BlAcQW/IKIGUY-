/**
 * Custom Tools Page
 *
 * Standalone page for managing custom tools.
 * Shows all registered tools with ability to register, edit, and delete.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Search,
  Plus,
  Wrench,
  ExternalLink,
  Activity,
  AlertTriangle,
  CheckCircle,
  MoreVertical,
  Trash2,
  Edit,
  FileText,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { customToolsService } from '@/services/CustomToolsService';
import { useOrganization } from '@/contexts/OrganizationContext';

interface CustomTool {
  id: string;
  name: string;
  description: string;
  tool_type: string;
  is_active: boolean;
  config: any;
  created_at: string;
  updated_at: string;
}

const CustomTools: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { currentOrganization } = useOrganization();

  // State
  const [tools, setTools] = useState<CustomTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Delete confirmation dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [toolToDelete, setToolToDelete] = useState<CustomTool | null>(null);
  const [deleting, setDeleting] = useState(false);

  // Fetch tools
  const fetchTools = async () => {
    setLoading(true);
    try {
      const response = await customToolsService.getCustomTools();
      // Response has structure: { success, tools, total, categories }
      setTools(response.tools || []);
    } catch (error) {
      console.error('Error fetching custom tools:', error);
      toast({
        title: 'Failed to load custom tools',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
      // Set empty array on error to prevent filter errors
      setTools([]);
    } finally {
      setLoading(false);
    }
  };

  // Delete tool
  const handleDelete = async () => {
    if (!toolToDelete) return;

    setDeleting(true);
    try {
      await customToolsService.deleteCustomTool(toolToDelete.id);
      toast({
        title: 'Tool deleted',
        description: `${toolToDelete.name} has been successfully removed.`,
      });
      fetchTools();
      setDeleteDialogOpen(false);
      setToolToDelete(null);
    } catch (error) {
      console.error('Error deleting tool:', error);
      toast({
        title: 'Failed to delete tool',
        description: error instanceof Error ? error.message : 'Please try again.',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
    }
  };

  // Navigate to tool detail
  const handleViewTool = (toolId: string) => {
    navigate(`/custom-tools/${toolId}`);
  };

  // Filter tools
  const filteredTools = tools.filter((tool) => {
    const matchesSearch =
      searchKeyword === '' ||
      tool.name.toLowerCase().includes(searchKeyword.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchKeyword.toLowerCase());

    const matchesType = typeFilter === 'all' || tool.tool_type === typeFilter;
    const matchesStatus = statusFilter === 'all' || (statusFilter === 'active' ? tool.is_active : !tool.is_active);

    return matchesSearch && matchesType && matchesStatus;
  });

  // Get unique tool types
  const toolTypes = Array.from(new Set(tools.map((t) => t.tool_type)));

  useEffect(() => {
    fetchTools();
  }, []);

  return (
    <div className="flex h-screen bg-background text-foreground">
      <DashboardSidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Wrench className="h-6 w-6" />
                Custom Tools
              </h1>
              <p className="text-gray-600">
                Manage your custom tools and integrations ({filteredTools.length} tools)
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button onClick={() => navigate('/custom-tools/register')}>
                <Plus className="h-4 w-4 mr-2" />
                Register Tool
              </Button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="p-6 border-b border-border bg-muted/50">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
                <Input
                  placeholder="Search tools by name or description..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Type Filter */}
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {toolTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Status Filter */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Tools Table */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                <p className="text-gray-600">Loading custom tools...</p>
              </div>
            </div>
          ) : filteredTools.length === 0 ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <Wrench className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No custom tools found</h3>
                <p className="text-gray-600 mb-4">
                  {searchKeyword || typeFilter !== 'all' || statusFilter !== 'all'
                    ? 'Try adjusting your filters to see more results.'
                    : 'Get started by registering your first custom tool.'}
                </p>
                {!searchKeyword && typeFilter === 'all' && statusFilter === 'all' && (
                  <Button onClick={() => navigate('/custom-tools/register')}>
                    <Plus className="h-4 w-4 mr-2" />
                    Register Tool
                  </Button>
                )}
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Tool Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Last Updated</TableHead>
                        <TableHead className="w-[100px]">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredTools.map((tool) => (
                        <TableRow
                          key={tool.id}
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => handleViewTool(tool.id)}
                        >
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <Wrench className="h-4 w-4 text-gray-600" />
                              <span className="font-medium">{tool.name}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="capitalize">
                              {tool.tool_type}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {tool.is_active ? (
                              <Badge variant="default" className="bg-green-600">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Active
                              </Badge>
                            ) : (
                              <Badge variant="secondary">
                                <AlertTriangle className="h-3 w-3 mr-1" />
                                Inactive
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            <p className="text-sm text-gray-600 line-clamp-2 max-w-md">
                              {tool.description}
                            </p>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">
                              {new Date(tool.updated_at).toLocaleDateString()}
                            </div>
                            <div className="text-xs text-gray-600">
                              {new Date(tool.updated_at).toLocaleTimeString()}
                            </div>
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem onClick={() => handleViewTool(tool.id)}>
                                  <ExternalLink className="h-4 w-4 mr-2" />
                                  View Details
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleViewTool(tool.id)}>
                                  <FileText className="h-4 w-4 mr-2" />
                                  View Logs
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={(e) => {
                                  e.stopPropagation();
                                  // TODO: Open edit dialog
                                  toast({
                                    title: 'Edit functionality',
                                    description: 'Edit tool configuration will be available in the detail page.',
                                  });
                                }}>
                                  <Edit className="h-4 w-4 mr-2" />
                                  Edit
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setToolToDelete(tool);
                                    setDeleteDialogOpen(true);
                                  }}
                                >
                                  <Trash2 className="h-4 w-4 mr-2" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Custom Tool</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{toolToDelete?.name}</strong>?
              This action cannot be undone and will remove all associated configurations.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setToolToDelete(null);
              }}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete Tool'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CustomTools;
