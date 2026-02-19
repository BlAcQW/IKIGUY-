import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { API_ENDPOINTS, apiRequest } from '@/config/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Search,
  Plus,
  MoreVertical,
  Edit,
  Trash2,
  Shield,
  UserCheck,
  UserX,
  Mail,
  Calendar,
  Loader2,
  RefreshCw,
  Send,
  Clock,
  CheckCircle,
  XCircle,
  Copy
} from 'lucide-react';
import { toast } from '@/components/ui/use-toast';
import { format } from 'date-fns';

interface User {
  id: string;
  email: string;
  name: string;
  role: 'universal_admin' | 'admin' | 'user' | 'moderator';
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  last_login: string | null;
  email_verified: boolean;
  organization_id: string | null;
  organization_name: string | null;
}

interface CreateUserData {
  email: string;
  name: string;
  password: string;
  role: 'universal_admin' | 'admin' | 'user' | 'moderator';
  sendWelcomeEmail: boolean;
}

interface Invitation {
  id: string;
  email: string;
  token: string;
  role: string;
  status: 'pending' | 'accepted' | 'expired' | 'cancelled';
  invited_by: string;
  referral_code: string | null;
  created_at: string;
  expires_at: string;
  accepted_at?: string;
}

interface InviteUserData {
  email: string;
  role: 'universal_admin' | 'admin' | 'user' | 'moderator';
  message: string;
  send_email: boolean;
}

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRole, setSelectedRole] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [createUserData, setCreateUserData] = useState<CreateUserData>({
    email: '',
    name: '',
    password: '',
    role: 'user',
    sendWelcomeEmail: true,
  });

  // Invitation states
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [invitationsLoading, setInvitationsLoading] = useState(false);
  const [isInviteDialogOpen, setIsInviteDialogOpen] = useState(false);
  const [inviteUserData, setInviteUserData] = useState<InviteUserData>({
    email: '',
    role: 'user',
    message: '',
    send_email: true,
  });

  // Fetch users
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (selectedRole !== 'all') params.append('role', selectedRole);
      if (selectedStatus !== 'all') params.append('status', selectedStatus);

      const response = await apiRequest(`${API_ENDPOINTS.adminUsers}?${params}`);

      if (!response.ok) throw new Error('Failed to fetch users');

      const data = await response.json();
      setUsers(data.users);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch users',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [searchQuery, selectedRole, selectedStatus]);

  // Fetch invitations
  const fetchInvitations = async () => {
    setInvitationsLoading(true);
    try {
      const response = await apiRequest(API_ENDPOINTS.adminInvitations);

      if (!response.ok) throw new Error('Failed to fetch invitations');

      const data = await response.json();
      setInvitations(data.invitations || []);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch invitations',
        variant: 'destructive',
      });
    } finally {
      setInvitationsLoading(false);
    }
  };

  useEffect(() => {
    fetchInvitations();
  }, []);

  // Create user
  const handleCreateUser = async () => {
    try {
      const response = await apiRequest(API_ENDPOINTS.adminUsers, {
        method: 'POST',
        body: JSON.stringify(createUserData),
      });

      if (!response.ok) throw new Error('Failed to create user');

      toast({
        title: 'Success',
        description: 'User created successfully',
      });

      setIsCreateDialogOpen(false);
      setCreateUserData({
        email: '',
        name: '',
        password: '',
        role: 'user',
        sendWelcomeEmail: true,
      });
      fetchUsers();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create user',
        variant: 'destructive',
      });
    }
  };

  // Invite user
  const handleInviteUser = async () => {
    try {
      const response = await apiRequest(API_ENDPOINTS.adminInvitations, {
        method: 'POST',
        body: JSON.stringify(inviteUserData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send invitation');
      }

      const data = await response.json();

      toast({
        title: 'Success',
        description: `Invitation sent to ${inviteUserData.email}`,
      });

      setIsInviteDialogOpen(false);
      setInviteUserData({
        email: '',
        role: 'user',
        message: '',
        send_email: true,
      });
      fetchInvitations();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to send invitation',
        variant: 'destructive',
      });
    }
  };

  // Cancel invitation
  const handleCancelInvitation = async (invitationId: string) => {
    if (!confirm('Are you sure you want to cancel this invitation?')) return;

    try {
      const response = await apiRequest(API_ENDPOINTS.adminInvitation(invitationId), {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to cancel invitation');

      toast({
        title: 'Success',
        description: 'Invitation cancelled successfully',
      });

      fetchInvitations();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to cancel invitation',
        variant: 'destructive',
      });
    }
  };

  // Resend invitation
  const handleResendInvitation = async (invitationId: string) => {
    try {
      const response = await apiRequest(API_ENDPOINTS.adminInvitationResend(invitationId), {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to resend invitation');

      toast({
        title: 'Success',
        description: 'Invitation resent successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to resend invitation',
        variant: 'destructive',
      });
    }
  };

  // Copy invitation link
  const handleCopyInvitationLink = (token: string) => {
    const invitationUrl = `${window.location.origin}/accept-invitation?token=${token}`;
    navigator.clipboard.writeText(invitationUrl);
    toast({
      title: 'Success',
      description: 'Invitation link copied to clipboard',
    });
  };

  // Update user
  const handleUpdateUser = async (userId: string, updates: Partial<User>) => {
    try {
      const response = await apiRequest(API_ENDPOINTS.adminUser(userId), {
        method: 'PATCH',
        body: JSON.stringify(updates),
      });

      if (!response.ok) throw new Error('Failed to update user');

      toast({
        title: 'Success',
        description: 'User updated successfully',
      });

      fetchUsers();
      setIsEditDialogOpen(false);
      setEditingUser(null);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update user',
        variant: 'destructive',
      });
    }
  };

  // Delete user
  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      const response = await apiRequest(API_ENDPOINTS.adminUser(userId), {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to delete user');

      toast({
        title: 'Success',
        description: 'User deleted successfully',
      });

      fetchUsers();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete user',
        variant: 'destructive',
      });
    }
  };

  // Toggle user status
  const handleToggleStatus = async (userId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
    await handleUpdateUser(userId, { status: newStatus });
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'universal_admin':
        return 'destructive';
      case 'admin':
        return 'destructive';
      case 'moderator':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'default';
      case 'inactive':
        return 'secondary';
      case 'suspended':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
    <div className="p-8 pb-12">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">User Management</h1>
        <p className="text-muted-foreground">Manage user accounts, roles, and permissions</p>
      </div>

      {/* Filters and Search */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Search & Filter</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 flex-wrap">
            <div className="flex-1 min-w-[300px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
                <Input
                  placeholder="Search by email or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={selectedRole} onValueChange={setSelectedRole}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="All Roles" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="universal_admin">Universal Admin</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="moderator">Moderator</SelectItem>
                <SelectItem value="user">User</SelectItem>
              </SelectContent>
            </Select>
            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="suspended">Suspended</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={fetchUsers} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Dialog open={isInviteDialogOpen} onOpenChange={setIsInviteDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="default">
                  <Send className="h-4 w-4 mr-2" />
                  Invite User
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Invite New User</DialogTitle>
                  <DialogDescription>
                    Send an invitation email. User will create their own password and be automatically registered as your affiliate.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="invite-email">Email</Label>
                    <Input
                      id="invite-email"
                      type="email"
                      value={inviteUserData.email}
                      onChange={(e) => setInviteUserData({ ...inviteUserData, email: e.target.value })}
                      placeholder="newuser@example.com"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="invite-role">Role</Label>
                    <Select
                      value={inviteUserData.role}
                      onValueChange={(value: 'universal_admin' | 'admin' | 'user' | 'moderator') =>
                        setInviteUserData({ ...inviteUserData, role: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="user">User</SelectItem>
                        <SelectItem value="moderator">Moderator</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="universal_admin">Universal Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="invite-message">Personal Message (Optional)</Label>
                    <Textarea
                      id="invite-message"
                      value={inviteUserData.message}
                      onChange={(e) => setInviteUserData({ ...inviteUserData, message: e.target.value })}
                      placeholder="Welcome to our platform! We're excited to have you join us."
                      rows={3}
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="send-email"
                      checked={inviteUserData.send_email}
                      onCheckedChange={(checked) =>
                        setInviteUserData({ ...inviteUserData, send_email: checked })
                      }
                    />
                    <Label htmlFor="send-email">Send invitation email</Label>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsInviteDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleInviteUser}>Send Invitation</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">
                  <Plus className="h-4 w-4 mr-2" />
                  Create User
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Create New User</DialogTitle>
                  <DialogDescription>
                    Add a new user to the system with specified role and permissions.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={createUserData.email}
                      onChange={(e) => setCreateUserData({ ...createUserData, email: e.target.value })}
                      placeholder="user@example.com"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="name">Name</Label>
                    <Input
                      id="name"
                      value={createUserData.name}
                      onChange={(e) => setCreateUserData({ ...createUserData, name: e.target.value })}
                      placeholder="John Doe"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={createUserData.password}
                      onChange={(e) => setCreateUserData({ ...createUserData, password: e.target.value })}
                      placeholder="••••••••"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="role">Role</Label>
                    <Select
                      value={createUserData.role}
                      onValueChange={(value: 'universal_admin' | 'admin' | 'user' | 'moderator') =>
                        setCreateUserData({ ...createUserData, role: value })
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="user">User</SelectItem>
                        <SelectItem value="moderator">Moderator</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="universal_admin">Universal Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="welcome-email"
                      checked={createUserData.sendWelcomeEmail}
                      onCheckedChange={(checked) => 
                        setCreateUserData({ ...createUserData, sendWelcomeEmail: checked })
                      }
                    />
                    <Label htmlFor="welcome-email">Send welcome email</Label>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleCreateUser}>Create User</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardContent>
      </Card>

      {/* Users and Invitations Tabs */}
      <Tabs defaultValue="users" className="space-y-4">
        <TabsList>
          <TabsTrigger value="users">Users ({users.length})</TabsTrigger>
          <TabsTrigger value="invitations">
            Invitations ({invitations.filter(inv => inv.status === 'pending').length} pending)
          </TabsTrigger>
        </TabsList>

        {/* Users Tab */}
        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle>Users</CardTitle>
              <CardDescription>
                Total: {users.length} users
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
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Organization</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{user.name}</div>
                        <div className="text-sm text-muted-foreground flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          {user.email}
                        </div>
                        {user.email_verified && (
                          <Badge variant="outline" className="mt-1">
                            <UserCheck className="h-3 w-3 mr-1" />
                            Verified
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getRoleBadgeVariant(user.role)}>
                        <Shield className="h-3 w-3 mr-1" />
                        {user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(user.status)}>
                        {user.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {user.organization_name ? (
                          <div>
                            <div className="font-medium">{user.organization_name}</div>
                            <div className="text-xs text-muted-foreground">{user.organization_id}</div>
                          </div>
                        ) : (
                          <span className="text-muted-foreground italic">No organization</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        <Calendar className="h-3 w-3 inline mr-1" />
                        {user.created_at && !isNaN(new Date(user.created_at).getTime())
                          ? format(new Date(user.created_at), 'MMM d, yyyy')
                          : 'N/A'
                        }
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm text-muted-foreground">
                        {user.last_login && !isNaN(new Date(user.last_login).getTime())
                          ? format(new Date(user.last_login), 'MMM d, yyyy HH:mm')
                          : 'Never'
                        }
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => {
                              setEditingUser(user);
                              setIsEditDialogOpen(true);
                            }}
                          >
                            <Edit className="h-4 w-4 mr-2" />
                            Edit User
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleToggleStatus(user.id, user.status)}
                          >
                            {user.status === 'active' ? (
                              <>
                                <UserX className="h-4 w-4 mr-2" />
                                Deactivate
                              </>
                            ) : (
                              <>
                                <UserCheck className="h-4 w-4 mr-2" />
                                Activate
                              </>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => handleDeleteUser(user.id)}
                            className="text-destructive"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete User
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </TabsContent>

    {/* Invitations Tab */}
    <TabsContent value="invitations">
      <Card>
        <CardHeader>
          <CardTitle>Pending Invitations</CardTitle>
          <CardDescription>
            Manage user invitations and track their status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {invitationsLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : invitations.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No invitations found. Click "Invite User" to send your first invitation.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Invited By</TableHead>
                  <TableHead>Sent</TableHead>
                  <TableHead>Expires</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invitations.map((invitation) => (
                  <TableRow key={invitation.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{invitation.email}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{invitation.role}</Badge>
                    </TableCell>
                    <TableCell>
                      {invitation.status === 'pending' && (
                        <Badge variant="default">
                          <Clock className="h-3 w-3 mr-1" />
                          Pending
                        </Badge>
                      )}
                      {invitation.status === 'accepted' && (
                        <Badge variant="default" className="bg-green-500">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Accepted
                        </Badge>
                      )}
                      {invitation.status === 'expired' && (
                        <Badge variant="secondary">
                          <XCircle className="h-3 w-3 mr-1" />
                          Expired
                        </Badge>
                      )}
                      {invitation.status === 'cancelled' && (
                        <Badge variant="destructive">
                          <XCircle className="h-3 w-3 mr-1" />
                          Cancelled
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {invitation.invited_by}
                        {invitation.referral_code && (
                          <div className="text-xs text-muted-foreground">
                            Ref: {invitation.referral_code}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {invitation.created_at && !isNaN(new Date(invitation.created_at).getTime())
                          ? format(new Date(invitation.created_at), 'MMM d, yyyy')
                          : 'N/A'
                        }
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {invitation.expires_at && !isNaN(new Date(invitation.expires_at).getTime())
                          ? format(new Date(invitation.expires_at), 'MMM d, yyyy')
                          : 'N/A'
                        }
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Actions</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => handleCopyInvitationLink(invitation.token)}
                          >
                            <Copy className="h-4 w-4 mr-2" />
                            Copy Link
                          </DropdownMenuItem>
                          {invitation.status === 'pending' && (
                            <>
                              <DropdownMenuItem
                                onClick={() => handleResendInvitation(invitation.id)}
                              >
                                <Send className="h-4 w-4 mr-2" />
                                Resend Email
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => handleCancelInvitation(invitation.id)}
                                className="text-destructive"
                              >
                                <XCircle className="h-4 w-4 mr-2" />
                                Cancel Invitation
                              </DropdownMenuItem>
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </TabsContent>
  </Tabs>

      {/* Edit User Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>
              Update user information and permissions.
            </DialogDescription>
          </DialogHeader>
          {editingUser && (
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="edit-name">Name</Label>
                <Input
                  id="edit-name"
                  value={editingUser.name}
                  onChange={(e) => setEditingUser({ ...editingUser, name: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-email">Email</Label>
                <Input
                  id="edit-email"
                  type="email"
                  value={editingUser.email}
                  onChange={(e) => setEditingUser({ ...editingUser, email: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-role">Role</Label>
                <Select
                  value={editingUser.role}
                  onValueChange={(value: 'universal_admin' | 'admin' | 'user' | 'moderator') =>
                    setEditingUser({ ...editingUser, role: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="user">User</SelectItem>
                    <SelectItem value="moderator">Moderator</SelectItem>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="universal_admin">Universal Admin</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="edit-status">Status</Label>
                <Select
                  value={editingUser.status}
                  onValueChange={(value: 'active' | 'inactive' | 'suspended') => 
                    setEditingUser({ ...editingUser, status: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                    <SelectItem value="suspended">Suspended</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={() => editingUser && handleUpdateUser(editingUser.id, editingUser)}
            >
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}