/**
 * Group Detail Page
 * View group details, members, messages, and manage group
 */

import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Users,
  MessageCircle,
  Settings,
  UserPlus,
  LogOut,
  Globe,
  Lock,
  Trash2,
  Edit,
  Send,
  Mail,
  Copy,
  Check,
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { MainNavigation } from '@/components/navigation/MainNavigation';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface Group {
  id: string;
  name: string;
  description?: string;
  is_public: boolean;
  creator_id: string;
  creator_name: string;
  devotional_id?: string;
  discussion_topic?: string;
  members_count: number;
  messages_count: number;
  members: Array<{
    user_id: string;
    name: string;
    avatar_url?: string;
    role: string;
    joined_at: string;
  }>;
  created_at: string;
}

interface GroupMessage {
  id: string;
  user_id: string;
  user_name: string;
  user_avatar_url?: string;
  text: string;
  devotional_id?: string;
  created_at: string;
}

export default function GroupDetail() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [newMessage, setNewMessage] = useState('');
  const [copiedInviteLink, setCopiedInviteLink] = useState(false);

  // Fetch group
  const { data: group, isLoading } = useQuery({
    queryKey: ['group', id],
    queryFn: async () => {
      if (!id) throw new Error('No group ID');
      return await apiClient.getGroup(id);
    },
    enabled: !!id,
  });

  // Fetch messages
  const { data: messages = [] } = useQuery({
    queryKey: ['group-messages', id],
    queryFn: async () => {
      if (!id) return [];
      const response = await apiClient.getGroupMessages(id, { page: 1, page_size: 50 });
      return Array.isArray(response) ? response : [];
    },
    enabled: !!id,
  });

  // Check if user is member
  const isMember = group && user
    ? group.members.some(m => m.user_id === user.id)
    : false;

  const isCreator = group && user
    ? group.creator_id === user.id
    : false;

  const isAdmin = group && user
    ? group.members.some(m => m.user_id === user.id && m.role === 'admin')
    : false;

  // Join mutation
  const joinMutation = useMutation({
    mutationFn: async () => {
      if (!id) return;
      return await apiClient.joinGroup(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['group', id] });
      toast({
        title: "Joined group!",
        description: "You're now a member",
      });
    },
    onError: (error: any) => {
      const errorDetail = error.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'string'
        ? errorDetail
        : Array.isArray(errorDetail)
          ? errorDetail.map((e: any) => e.msg || String(e)).join(', ')
          : "Failed to join group";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    },
  });

  // Leave mutation
  const leaveMutation = useMutation({
    mutationFn: async () => {
      if (!id) return;
      return await apiClient.leaveGroup(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['group', id] });
      toast({
        title: "Left group",
        description: "You've left this group",
      });
      navigate('/groups');
    },
    onError: (error: any) => {
      const errorDetail = error.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'string'
        ? errorDetail
        : Array.isArray(errorDetail)
          ? errorDetail.map((e: any) => e.msg || String(e)).join(', ')
          : "Failed to leave group";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!id) return;
      return await apiClient.deleteGroup(id);
    },
    onSuccess: () => {
      toast({
        title: "Group deleted",
        description: "The group has been deleted",
      });
      navigate('/groups');
    },
    onError: (error: any) => {
      const errorDetail = error.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'string'
        ? errorDetail
        : Array.isArray(errorDetail)
          ? errorDetail.map((e: any) => e.msg || String(e)).join(', ')
          : "Failed to delete group";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    },
  });

  // Fetch invites
  const { data: invitesData } = useQuery({
    queryKey: ['group-invites', id],
    queryFn: async () => {
      if (!id) return { items: [] };
      try {
        const response = await apiClient.listGroupInvites(id, { status: 'pending' });
        return response;
      } catch (error) {
        return { items: [] };
      }
    },
    enabled: !!id && (isCreator || isAdmin),
  });

  // Invite mutation
  const inviteMutation = useMutation({
    mutationFn: async (email: string) => {
      if (!id) return;
      return await apiClient.createGroupInvite(id, { invitee_email: email });
    },
    onSuccess: (data) => {
      toast({
        title: "Invite sent!",
        description: "Invitation has been sent",
      });
      setShowInviteDialog(false);
      setInviteEmail('');
      queryClient.invalidateQueries({ queryKey: ['group-invites', id] });
      // Generate invite link
      if (data.invite_token) {
        const inviteLink = `${window.location.origin}/invite/${data.invite_token}`;
        navigator.clipboard.writeText(inviteLink);
        setCopiedInviteLink(true);
        setTimeout(() => setCopiedInviteLink(false), 2000);
      }
    },
    onError: (error: any) => {
      const errorDetail = error.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'string'
        ? errorDetail
        : Array.isArray(errorDetail)
          ? errorDetail.map((e: any) => e.msg || String(e)).join(', ')
          : "Failed to send invite";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    },
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (text: string) => {
      if (!id) return;
      return await apiClient.createGroupMessage(id, { text });
    },
    onSuccess: () => {
      setNewMessage('');
      queryClient.invalidateQueries({ queryKey: ['group-messages', id] });
    },
    onError: (error: any) => {
      const errorDetail = error.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'string'
        ? errorDetail
        : Array.isArray(errorDetail)
          ? errorDetail.map((e: any) => e.msg || String(e)).join(', ')
          : "Failed to send message";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
    },
  });

  const handleInvite = () => {
    if (!inviteEmail.trim()) {
      toast({
        title: "Email required",
        description: "Please enter an email address",
        variant: "destructive"
      });
      return;
    }
    inviteMutation.mutate(inviteEmail);
  };

  const handleSendMessage = () => {
    if (!newMessage.trim()) return;
    sendMessageMutation.mutate(newMessage);
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  if (isLoading || !group) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-4 border-secondary border-t-transparent rounded-full animate-spin" />
          <p className="mt-4 text-muted-foreground">Loading group...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      <MainNavigation />

      <div className="container mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="icon" onClick={() => navigate('/groups')}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              {group.is_public ? (
                <Globe className="w-4 h-4 text-muted-foreground" />
              ) : (
                <Lock className="w-4 h-4 text-muted-foreground" />
              )}
              <span className="text-xs text-muted-foreground">
                {group.is_public ? 'Public' : 'Private'}
              </span>
            </div>
            <h1 className="font-serif text-2xl font-bold text-foreground">
              {group.name}
            </h1>
          </div>
          {(isCreator || isAdmin) && (
            <Button
              variant="outline"
              size="icon"
              onClick={() => navigate(`/groups/${id}/settings`)}
            >
              <Settings className="w-5 h-5" />
            </Button>
          )}
        </div>

        {/* Description */}
        {group.description && (
          <p className="text-muted-foreground mb-6">{group.description}</p>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-card rounded-xl p-4 border border-border">
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-5 h-5 text-secondary" />
              <span className="font-semibold text-foreground">{group.members_count}</span>
            </div>
            <p className="text-sm text-muted-foreground">Members</p>
          </div>
          <div className="bg-card rounded-xl p-4 border border-border">
            <div className="flex items-center gap-2 mb-2">
              <MessageCircle className="w-5 h-5 text-secondary" />
              <span className="font-semibold text-foreground">{group.messages_count}</span>
            </div>
            <p className="text-sm text-muted-foreground">Messages</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 mb-6">
          {!isMember && user && (
            <Button
              onClick={() => joinMutation.mutate()}
              disabled={joinMutation.isPending}
              className="gap-2"
            >
              <UserPlus className="w-4 h-4" />
              Join Group
            </Button>
          )}
          {isMember && (
            <>
              <Button
                variant="outline"
                onClick={() => setShowInviteDialog(true)}
                className="gap-2"
              >
                <Mail className="w-4 h-4" />
                Invite
              </Button>
              {!isCreator && (
                <Button
                  variant="outline"
                  onClick={() => leaveMutation.mutate()}
                  disabled={leaveMutation.isPending}
                  className="gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  Leave
                </Button>
              )}
            </>
          )}
          {isCreator && (
            <Button
              variant="destructive"
              onClick={() => setShowDeleteDialog(true)}
              className="gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Delete Group
            </Button>
          )}
        </div>

        {/* Pending Invites */}
        {(isCreator || isAdmin) && invitesData && invitesData.items && invitesData.items.length > 0 && (
          <div className="mb-6">
            <h2 className="font-serif text-lg font-semibold text-foreground mb-4">
              Pending Invites ({invitesData.items.length})
            </h2>
            <div className="space-y-2">
              {invitesData.items.map((invite: any) => {
                const inviteLink = `${window.location.origin}/invite/${invite.invite_token}`;
                return (
                  <div
                    key={invite.id}
                    className="flex items-center justify-between p-3 bg-card rounded-lg border border-border"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-medium text-foreground">
                        {invite.invitee_email || 'User'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Invited by {invite.inviter_name}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(inviteLink);
                          toast({
                            title: "Link copied!",
                            description: "Invite link copied to clipboard",
                          });
                        }}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={async () => {
                          try {
                            await apiClient.revokeInvite(invite.id);
                            queryClient.invalidateQueries({ queryKey: ['group-invites', id] });
                            toast({
                              title: "Invite revoked",
                              description: "The invite has been cancelled",
                            });
                          } catch (error: any) {
                            const errorDetail = error.response?.data?.detail;
                            const errorMessage = typeof errorDetail === 'string'
                              ? errorDetail
                              : Array.isArray(errorDetail)
                                ? errorDetail.map((e: any) => e.msg || String(e)).join(', ')
                                : "Failed to revoke invite";
                            toast({
                              title: "Error",
                              description: errorMessage,
                              variant: "destructive"
                            });
                          }
                        }}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Members */}
        <div className="mb-6">
          <h2 className="font-serif text-lg font-semibold text-foreground mb-4">
            Members ({group.members.length})
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {group.members.map((member) => (
              <div
                key={member.user_id}
                className="flex items-center gap-2 p-3 bg-card rounded-lg border border-border"
              >
                <div className="w-10 h-10 rounded-full bg-secondary/20 flex items-center justify-center">
                  <span className="text-sm font-semibold text-secondary">
                    {getInitials(member.name)}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">
                    {member.name}
                  </p>
                  <p className="text-xs text-muted-foreground capitalize">
                    {member.role}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Messages */}
        {isMember && (
          <div className="mb-6">
            <h2 className="font-serif text-lg font-semibold text-foreground mb-4">
              Group Chat
            </h2>
            <div className="bg-card rounded-xl border border-border p-4 mb-4 max-h-96 overflow-y-auto">
              {messages.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No messages yet. Start the conversation!
                </p>
              ) : (
                <div className="space-y-4">
                  {messages.map((message: GroupMessage) => (
                    <div key={message.id} className="flex gap-3">
                      <div className="w-8 h-8 rounded-full bg-secondary/20 flex items-center justify-center shrink-0">
                        <span className="text-xs font-semibold text-secondary">
                          {getInitials(message.user_name)}
                        </span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-foreground">
                            {message.user_name}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {formatTime(message.created_at)}
                          </span>
                        </div>
                        <p className="text-sm text-foreground/90">{message.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <Textarea
                placeholder="Type a message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                className="min-h-[60px] resize-none"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!newMessage.trim() || sendMessageMutation.isPending}
                size="icon"
                className="h-[60px]"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Invite Dialog */}
        <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Invite to Group</DialogTitle>
              <DialogDescription>
                Send an invitation to join this group
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Email Address</label>
                <Input
                  type="email"
                  placeholder="friend@example.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                />
              </div>
              {copiedInviteLink && (
                <div className="flex items-center gap-2 text-sm text-secondary">
                  <Check className="w-4 h-4" />
                  Invite link copied to clipboard!
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowInviteDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleInvite} disabled={inviteMutation.isPending}>
                Send Invite
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Dialog */}
        <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Group</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this group? This action cannot be undone.
                All messages and invites will be deleted.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => {
                  deleteMutation.mutate();
                  setShowDeleteDialog(false);
                }}
                disabled={deleteMutation.isPending}
              >
                Delete Group
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

    </div>
  );
}

