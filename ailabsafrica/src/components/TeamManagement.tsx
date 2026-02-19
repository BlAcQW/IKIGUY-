import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { 
  Users, 
  Plus, 
  Settings, 
  UserPlus, 
  Mail, 
  Shield, 
  Activity, 
  Share2, 
  Trash2, 
  Edit, 
  Crown,
  User,
  UserCheck,
  Clock,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface Team {
  id: string;
  name: string;
  description: string;
  slug: string;
  owner_id: string;
  max_members: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface TeamMember {
  user_id: string;
  email: string;
  full_name: string;
  role_name: string;
  role_display_name: string;
  status: string;
  joined_at: string;
  last_active_at: string;
}

interface TeamInvitation {
  id: string;
  team_id: string;
  email: string;
  role_id: string;
  invited_by: string;
  token: string;
  expires_at: string;
  status: string;
  created_at: string;
  team_roles: {
    name: string;
    display_name: string;
  };
}

interface TeamResource {
  id: string;
  team_id: string;
  resource_type: string;
  resource_id: string;
  resource_name: string;
  shared_by: string;
  permissions: {
    read: boolean;
    write: boolean;
    delete: boolean;
  };
  is_public: boolean;
  created_at: string;
}

interface TeamActivity {
  id: string;
  team_id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: any;
  created_at: string;
}

const TeamManagement: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [teamInvitations, setTeamInvitations] = useState<TeamInvitation[]>([]);
  const [teamResources, setTeamResources] = useState<TeamResource[]>([]);
  const [teamActivity, setTeamActivity] = useState<TeamActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [createTeamDialog, setCreateTeamDialog] = useState(false);
  const [inviteMemberDialog, setInviteMemberDialog] = useState(false);
  const [shareResourceDialog, setShareResourceDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const { toast } = useToast();

  // Form states
  const [newTeam, setNewTeam] = useState({
    name: '',
    description: '',
    slug: ''
  });

  const [newInvitation, setNewInvitation] = useState({
    email: '',
    role_name: 'member'
  });

  const [newResource, setNewResource] = useState({
    resource_type: 'assistant',
    resource_id: '',
    resource_name: '',
    permissions: { read: true, write: false, delete: false },
    is_public: false
  });

  useEffect(() => {
    loadUserTeams();
  }, []);

  useEffect(() => {
    if (selectedTeam) {
      loadTeamDetails(selectedTeam.id);
    }
  }, [selectedTeam]);

  const loadUserTeams = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/manage-teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        body: JSON.stringify({
          action: 'get_user_teams'
        })
      });

      const result = await response.json();
      if (result.data) {
        setTeams(result.data);
        if (result.data.length > 0 && !selectedTeam) {
          setSelectedTeam(result.data[0]);
        }
      }
    } catch (error) {
      console.error('Error loading teams:', error);
      toast({
        title: 'Error',
        description: 'Failed to load teams',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const loadTeamDetails = async (teamId: string) => {
    try {
      // Load team members
      const membersResponse = await fetch('/api/manage-teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        body: JSON.stringify({
          action: 'get_team_members',
          team_id: teamId
        })
      });

      const membersResult = await membersResponse.json();
      if (membersResult.data) {
        setTeamMembers(membersResult.data);
      }

      // Load team invitations
      const invitationsResponse = await fetch('/api/manage-teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        body: JSON.stringify({
          action: 'get_team_invitations',
          team_id: teamId
        })
      });

      const invitationsResult = await invitationsResponse.json();
      if (invitationsResult.data) {
        setTeamInvitations(invitationsResult.data);
      }

      // Load team resources
      const resourcesResponse = await fetch('/api/manage-teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        body: JSON.stringify({
          action: 'get_team_resources',
          team_id: teamId
        })
      });

      const resourcesResult = await resourcesResponse.json();
      if (resourcesResult.data) {
        setTeamResources(resourcesResult.data);
      }

      // Load team activity
      const activityResponse = await fetch('/api/manage-teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        body: JSON.stringify({
          action: 'get_team_activity',
          team_id: teamId
        })
      });

      const activityResult = await activityResponse.json();
      if (activityResult.data) {
        setTeamActivity(activityResult.data);
      }
    } catch (error) {
      console.error('Error loading team details:', error);
      toast({
        title: 'Error',
        description: 'Failed to load team details',
        variant: 'destructive'
      });
    }
  };

  const handleCreateTeam = async () => {
    try {
      const response = await fetch('/api/manage-teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        body: JSON.stringify({
          action: 'create_team',
          ...newTeam
        })
      });

      const result = await response.json();
      if (result.data) {
        toast({
          title: 'Success',
          description: 'Team created successfully'
        });
        setCreateTeamDialog(false);
        setNewTeam({ name: '', description: '', slug: '' });
        loadUserTeams();
      } else {
        toast({
          title: 'Error',
          description: result.error || 'Failed to create team',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error creating team:', error);
      toast({
        title: 'Error',
        description: 'Failed to create team',
        variant: 'destructive'
      });
    }
  };

  const handleInviteMember = async () => {
    if (!selectedTeam) return;

    try {
      const response = await fetch('/api/manage-teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        body: JSON.stringify({
          action: 'invite_member',
          team_id: selectedTeam.id,
          ...newInvitation
        })
      });

      const result = await response.json();
      if (result.data) {
        toast({
          title: 'Success',
          description: 'Invitation sent successfully'
        });
        setInviteMemberDialog(false);
        setNewInvitation({ email: '', role_name: 'member' });
        loadTeamDetails(selectedTeam.id);
      } else {
        toast({
          title: 'Error',
          description: result.error || 'Failed to send invitation',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error inviting member:', error);
      toast({
        title: 'Error',
        description: 'Failed to send invitation',
        variant: 'destructive'
      });
    }
  };

  const handleShareResource = async () => {
    if (!selectedTeam) return;

    try {
      const response = await fetch('/api/manage-teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        body: JSON.stringify({
          action: 'share_resource',
          team_id: selectedTeam.id,
          ...newResource
        })
      });

      const result = await response.json();
      if (result.data) {
        toast({
          title: 'Success',
          description: 'Resource shared successfully'
        });
        setShareResourceDialog(false);
        setNewResource({
          resource_type: 'assistant',
          resource_id: '',
          resource_name: '',
          permissions: { read: true, write: false, delete: false },
          is_public: false
        });
        loadTeamDetails(selectedTeam.id);
      } else {
        toast({
          title: 'Error',
          description: result.error || 'Failed to share resource',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error sharing resource:', error);
      toast({
        title: 'Error',
        description: 'Failed to share resource',
        variant: 'destructive'
      });
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!selectedTeam) return;

    try {
      const response = await fetch('/api/manage-teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        body: JSON.stringify({
          action: 'remove_member',
          team_id: selectedTeam.id,
          member_user_id: userId
        })
      });

      const result = await response.json();
      if (result.message) {
        toast({
          title: 'Success',
          description: 'Member removed successfully'
        });
        loadTeamDetails(selectedTeam.id);
      } else {
        toast({
          title: 'Error',
          description: result.error || 'Failed to remove member',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error removing member:', error);
      toast({
        title: 'Error',
        description: 'Failed to remove member',
        variant: 'destructive'
      });
    }
  };

  const handleCancelInvitation = async (invitationId: string) => {
    if (!selectedTeam) return;

    try {
      const response = await fetch('/api/manage-teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        body: JSON.stringify({
          action: 'cancel_invitation',
          invitation_id: invitationId
        })
      });

      const result = await response.json();
      if (result.message) {
        toast({
          title: 'Success',
          description: 'Invitation cancelled successfully'
        });
        loadTeamDetails(selectedTeam.id);
      } else {
        toast({
          title: 'Error',
          description: result.error || 'Failed to cancel invitation',
          variant: 'destructive'
        });
      }
    } catch (error) {
      console.error('Error cancelling invitation:', error);
      toast({
        title: 'Error',
        description: 'Failed to cancel invitation',
        variant: 'destructive'
      });
    }
  };

  const getRoleIcon = (roleName: string) => {
    switch (roleName) {
      case 'owner':
        return <Crown className="h-4 w-4 text-yellow-500" />;
      case 'admin':
        return <Shield className="h-4 w-4 text-blue-500" />;
      case 'member':
        return <User className="h-4 w-4 text-green-500" />;
      case 'viewer':
        return <UserCheck className="h-4 w-4 text-gray-500" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'suspended':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <XCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-2 text-muted-foreground">Loading teams...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Team Management</h1>
          <p className="text-muted-foreground">Manage your teams, members, and resources</p>
        </div>
        <Dialog open={createTeamDialog} onOpenChange={setCreateTeamDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create Team
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Team</DialogTitle>
              <DialogDescription>
                Create a new team to collaborate with others
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="team-name">Team Name</Label>
                <Input
                  id="team-name"
                  value={newTeam.name}
                  onChange={(e) => setNewTeam({ ...newTeam, name: e.target.value })}
                  placeholder="Enter team name"
                />
              </div>
              <div>
                <Label htmlFor="team-slug">Team Slug</Label>
                <Input
                  id="team-slug"
                  value={newTeam.slug}
                  onChange={(e) => setNewTeam({ ...newTeam, slug: e.target.value })}
                  placeholder="team-slug"
                />
              </div>
              <div>
                <Label htmlFor="team-description">Description</Label>
                <Textarea
                  id="team-description"
                  value={newTeam.description}
                  onChange={(e) => setNewTeam({ ...newTeam, description: e.target.value })}
                  placeholder="Enter team description"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateTeamDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateTeam}>Create Team</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {teams.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Teams Yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first team to start collaborating with others
            </p>
            <Button onClick={() => setCreateTeamDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Team
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Team List */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Your Teams</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {teams.map((team) => (
                    <div
                      key={team.id}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedTeam?.id === team.id
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-primary/50'
                      }`}
                      onClick={() => setSelectedTeam(team)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{team.name}</h4>
                          <p className="text-sm text-muted-foreground">{team.slug}</p>
                        </div>
                        <Badge variant="secondary">{teamMembers.length}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Team Details */}
          {selectedTeam && (
            <div className="lg:col-span-3">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>{selectedTeam.name}</CardTitle>
                      <CardDescription>{selectedTeam.description}</CardDescription>
                    </div>
                    <div className="flex space-x-2">
                      <Dialog open={inviteMemberDialog} onOpenChange={setInviteMemberDialog}>
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm">
                            <UserPlus className="h-4 w-4 mr-2" />
                            Invite Member
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Invite Team Member</DialogTitle>
                            <DialogDescription>
                              Send an invitation to join your team
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4">
                            <div>
                              <Label htmlFor="invite-email">Email Address</Label>
                              <Input
                                id="invite-email"
                                type="email"
                                value={newInvitation.email}
                                onChange={(e) => setNewInvitation({ ...newInvitation, email: e.target.value })}
                                placeholder="colleague@example.com"
                              />
                            </div>
                            <div>
                              <Label htmlFor="invite-role">Role</Label>
                              <Select
                                value={newInvitation.role_name}
                                onValueChange={(value) => setNewInvitation({ ...newInvitation, role_name: value })}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="member">Member</SelectItem>
                                  <SelectItem value="admin">Admin</SelectItem>
                                  <SelectItem value="viewer">Viewer</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                          <DialogFooter>
                            <Button variant="outline" onClick={() => setInviteMemberDialog(false)}>
                              Cancel
                            </Button>
                            <Button onClick={handleInviteMember}>Send Invitation</Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                      <Dialog open={shareResourceDialog} onOpenChange={setShareResourceDialog}>
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm">
                            <Share2 className="h-4 w-4 mr-2" />
                            Share Resource
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Share Resource</DialogTitle>
                            <DialogDescription>
                              Share a resource with your team
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4">
                            <div>
                              <Label htmlFor="resource-type">Resource Type</Label>
                              <Select
                                value={newResource.resource_type}
                                onValueChange={(value) => setNewResource({ ...newResource, resource_type: value })}
                              >
                                <SelectTrigger>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="assistant">Assistant</SelectItem>
                                  <SelectItem value="template">Template</SelectItem>
                                  <SelectItem value="configuration">Configuration</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                            <div>
                              <Label htmlFor="resource-id">Resource ID</Label>
                              <Input
                                id="resource-id"
                                value={newResource.resource_id}
                                onChange={(e) => setNewResource({ ...newResource, resource_id: e.target.value })}
                                placeholder="Enter resource ID"
                              />
                            </div>
                            <div>
                              <Label htmlFor="resource-name">Resource Name</Label>
                              <Input
                                id="resource-name"
                                value={newResource.resource_name}
                                onChange={(e) => setNewResource({ ...newResource, resource_name: e.target.value })}
                                placeholder="Enter resource name"
                              />
                            </div>
                          </div>
                          <DialogFooter>
                            <Button variant="outline" onClick={() => setShareResourceDialog(false)}>
                              Cancel
                            </Button>
                            <Button onClick={handleShareResource}>Share Resource</Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsList className="grid w-full grid-cols-4">
                      <TabsTrigger value="overview">Overview</TabsTrigger>
                      <TabsTrigger value="members">Members</TabsTrigger>
                      <TabsTrigger value="invitations">Invitations</TabsTrigger>
                      <TabsTrigger value="resources">Resources</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Card>
                          <CardContent className="p-4">
                            <div className="flex items-center space-x-2">
                              <Users className="h-5 w-5 text-blue-500" />
                              <div>
                                <p className="text-sm font-medium">Total Members</p>
                                <p className="text-2xl font-bold">{teamMembers.length}</p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardContent className="p-4">
                            <div className="flex items-center space-x-2">
                              <Mail className="h-5 w-5 text-yellow-500" />
                              <div>
                                <p className="text-sm font-medium">Pending Invitations</p>
                                <p className="text-2xl font-bold">
                                  {teamInvitations.filter(inv => inv.status === 'pending').length}
                                </p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardContent className="p-4">
                            <div className="flex items-center space-x-2">
                              <Share2 className="h-5 w-5 text-green-500" />
                              <div>
                                <p className="text-sm font-medium">Shared Resources</p>
                                <p className="text-2xl font-bold">{teamResources.length}</p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </div>

                      <Card>
                        <CardHeader>
                          <CardTitle>Recent Activity</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            {teamActivity.slice(0, 5).map((activity) => (
                              <div key={activity.id} className="flex items-center space-x-3">
                                <Activity className="h-4 w-4 text-muted-foreground" />
                                <div className="flex-1">
                                  <p className="text-sm">
                                    <span className="font-medium">{activity.action}</span>
                                    {activity.resource_type && (
                                      <span className="text-muted-foreground">
                                        {' '}on {activity.resource_type}
                                      </span>
                                    )}
                                  </p>
                                  <p className="text-xs text-muted-foreground">
                                    {new Date(activity.created_at).toLocaleString()}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    </TabsContent>

                    <TabsContent value="members" className="space-y-4">
                      <div className="space-y-3">
                        {teamMembers.map((member) => (
                          <div key={member.user_id} className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="flex items-center space-x-3">
                              {getRoleIcon(member.role_name)}
                              <div>
                                <p className="font-medium">{member.full_name}</p>
                                <p className="text-sm text-muted-foreground">{member.email}</p>
                                <div className="flex items-center space-x-2 mt-1">
                                  <Badge variant="outline">{member.role_display_name}</Badge>
                                  <div className="flex items-center space-x-1">
                                    {getStatusIcon(member.status)}
                                    <span className="text-xs text-muted-foreground capitalize">{member.status}</span>
                                  </div>
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRemoveMember(member.user_id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </TabsContent>

                    <TabsContent value="invitations" className="space-y-4">
                      <div className="space-y-3">
                        {teamInvitations.map((invitation) => (
                          <div key={invitation.id} className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="flex items-center space-x-3">
                              <Mail className="h-4 w-4 text-muted-foreground" />
                              <div>
                                <p className="font-medium">{invitation.email}</p>
                                <div className="flex items-center space-x-2 mt-1">
                                  <Badge variant="outline">{invitation.team_roles.display_name}</Badge>
                                  <Badge variant={invitation.status === 'pending' ? 'default' : 'secondary'}>
                                    {invitation.status}
                                  </Badge>
                                </div>
                                <p className="text-xs text-muted-foreground">
                                  Expires: {new Date(invitation.expires_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            {invitation.status === 'pending' && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleCancelInvitation(invitation.id)}
                              >
                                <XCircle className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        ))}
                        {teamInvitations.length === 0 && (
                          <div className="text-center py-8">
                            <Mail className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                            <p className="text-muted-foreground">No invitations yet</p>
                          </div>
                        )}
                      </div>
                    </TabsContent>

                    <TabsContent value="resources" className="space-y-4">
                      <div className="space-y-3">
                        {teamResources.map((resource) => (
                          <div key={resource.id} className="flex items-center justify-between p-3 border rounded-lg">
                            <div className="flex items-center space-x-3">
                              <Share2 className="h-4 w-4 text-muted-foreground" />
                              <div>
                                <p className="font-medium">{resource.resource_name}</p>
                                <div className="flex items-center space-x-2 mt-1">
                                  <Badge variant="outline">{resource.resource_type}</Badge>
                                  {resource.is_public && (
                                    <Badge variant="secondary">Public</Badge>
                                  )}
                                </div>
                                <p className="text-xs text-muted-foreground">
                                  Shared: {new Date(resource.created_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Button variant="outline" size="sm">
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button variant="outline" size="sm">
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                        {teamResources.length === 0 && (
                          <div className="text-center py-8">
                            <Share2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                            <p className="text-muted-foreground">No shared resources yet</p>
                          </div>
                        )}
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TeamManagement;
