import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { 
  Share2, 
  Users, 
  TrendingUp, 
  Plus, 
  Copy, 
  ExternalLink, 
  Mail, 
  Phone, 
  Building, 
  Calendar,
  Target,
  BarChart3,
  Activity,
  DollarSign,
  UserPlus,
  ClipboardList
} from 'lucide-react';

// Types
interface ReferralProgram {
  id: string;
  name: string;
  description: string;
  reward_type: string;
  reward_value: number;
  reward_currency: string;
  max_rewards_per_user: number;
}

interface UserReferral {
  id: string;
  referral_code: string;
  referral_link: string;
  status: string;
  conversion_date: string;
  created_at: string;
  referral_programs: ReferralProgram;
  referred_user?: { email: string };
}

interface ReferralReward {
  id: string;
  reward_type: string;
  reward_value: number;
  reward_currency: string;
  status: string;
  created_at: string;
  referral_programs: ReferralProgram;
}

interface LeadCampaign {
  id: string;
  name: string;
  description: string;
  campaign_type: string;
  status: string;
  budget: number;
  start_date: string;
  end_date: string;
  created_at: string;
}

interface LeadSource {
  id: string;
  name: string;
  source_type: string;
  utm_source: string;
  utm_medium: string;
  utm_campaign: string;
  conversion_rate: number;
  cost_per_lead: number;
  created_at: string;
}

interface LeadContact {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  company: string;
  job_title: string;
  status: string;
  lead_score: number;
  tags: string[];
  notes: string;
  assigned_to: string;
  last_contact_date: string;
  next_follow_up: string;
  created_at: string;
  lead_sources: LeadSource;
  lead_campaigns: LeadCampaign;
}

interface LeadActivity {
  id: string;
  activity_type: string;
  subject: string;
  description: string;
  activity_date: string;
  duration_minutes: number;
  outcome: string;
  next_action: string;
  created_at: string;
}

const MarketingFeatures: React.FC = () => {
  const [activeTab, setActiveTab] = useState('referrals');
  const [loading, setLoading] = useState(false);
  const [referralStats, setReferralStats] = useState<any>(null);
  const [userReferrals, setUserReferrals] = useState<UserReferral[]>([]);
  const [referralRewards, setReferralRewards] = useState<ReferralReward[]>([]);
  const [leadCampaigns, setLeadCampaigns] = useState<LeadCampaign[]>([]);
  const [leadContacts, setLeadContacts] = useState<LeadContact[]>([]);
  const [leadActivities, setLeadActivities] = useState<LeadActivity[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<LeadCampaign | null>(null);
  const [selectedContact, setSelectedContact] = useState<LeadContact | null>(null);
  
  // Dialog states
  const [showCreateReferral, setShowCreateReferral] = useState(false);
  const [showCreateCampaign, setShowCreateCampaign] = useState(false);
  const [showCreateContact, setShowCreateContact] = useState(false);
  const [showCreateActivity, setShowCreateActivity] = useState(false);
  
  // Form states
  const [newCampaign, setNewCampaign] = useState({
    name: '',
    description: '',
    campaignType: '',
    budget: 0
  });
  
  const [newContact, setNewContact] = useState({
    email: '',
    firstName: '',
    lastName: '',
    phone: '',
    company: '',
    jobTitle: '',
    sourceId: '',
    campaignId: '',
    notes: ''
  });
  
  const [newActivity, setNewActivity] = useState({
    activityType: '',
    subject: '',
    description: '',
    durationMinutes: 0,
    outcome: '',
    nextAction: ''
  });

  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadReferralStats(),
        loadUserReferrals(),
        loadReferralRewards(),
        loadLeadCampaigns(),
        loadLeadContacts()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
      toast({
        title: "Error",
        description: "Failed to load marketing data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadReferralStats = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    const response = await fetch('/api/supabase/functions/manage-marketing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        action: 'get_referral_stats'
      })
    });

    if (response.ok) {
      const { data } = await response.json();
      setReferralStats(data);
    }
  };

  const loadUserReferrals = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    const response = await fetch('/api/supabase/functions/manage-marketing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        action: 'get_user_referrals',
        limit: 20
      })
    });

    if (response.ok) {
      const { data } = await response.json();
      setUserReferrals(data);
    }
  };

  const loadReferralRewards = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    const response = await fetch('/api/supabase/functions/manage-marketing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        action: 'get_referral_rewards',
        limit: 20
      })
    });

    if (response.ok) {
      const { data } = await response.json();
      setReferralRewards(data);
    }
  };

  const loadLeadCampaigns = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    const response = await fetch('/api/supabase/functions/manage-marketing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        action: 'get_lead_campaigns',
        limit: 20
      })
    });

    if (response.ok) {
      const { data } = await response.json();
      setLeadCampaigns(data);
    }
  };

  const loadLeadContacts = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    const response = await fetch('/api/supabase/functions/manage-marketing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        action: 'get_lead_contacts',
        limit: 20
      })
    });

    if (response.ok) {
      const { data } = await response.json();
      setLeadContacts(data);
    }
  };

  const handleCreateReferralLink = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    const response = await fetch('/api/supabase/functions/manage-marketing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        action: 'create_referral_link'
      })
    });

    if (response.ok) {
      const { data } = await response.json();
      setUserReferrals(prev => [data, ...prev]);
      setShowCreateReferral(false);
      toast({
        title: "Success",
        description: "Referral link created successfully"
      });
      await loadReferralStats();
    } else {
      toast({
        title: "Error",
        description: "Failed to create referral link",
        variant: "destructive"
      });
    }
  };

  const handleCreateCampaign = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    const response = await fetch('/api/supabase/functions/manage-marketing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        action: 'create_lead_campaign',
        ...newCampaign
      })
    });

    if (response.ok) {
      const { data } = await response.json();
      setLeadCampaigns(prev => [data, ...prev]);
      setShowCreateCampaign(false);
      setNewCampaign({ name: '', description: '', campaignType: '', budget: 0 });
      toast({
        title: "Success",
        description: "Campaign created successfully"
      });
    } else {
      toast({
        title: "Error",
        description: "Failed to create campaign",
        variant: "destructive"
      });
    }
  };

  const handleCreateContact = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    const response = await fetch('/api/supabase/functions/manage-marketing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        action: 'create_lead_contact',
        ...newContact
      })
    });

    if (response.ok) {
      const { data } = await response.json();
      setLeadContacts(prev => [data, ...prev]);
      setShowCreateContact(false);
      setNewContact({
        email: '', firstName: '', lastName: '', phone: '', company: '',
        jobTitle: '', sourceId: '', campaignId: '', notes: ''
      });
      toast({
        title: "Success",
        description: "Lead contact created successfully"
      });
    } else {
      toast({
        title: "Error",
        description: "Failed to create lead contact",
        variant: "destructive"
      });
    }
  };

  const handleCreateActivity = async () => {
    if (!selectedContact) return;

    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;

    const response = await fetch('/api/supabase/functions/manage-marketing', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify({
        action: 'create_lead_activity',
        leadId: selectedContact.id,
        ...newActivity
      })
    });

    if (response.ok) {
      const { data } = await response.json();
      setLeadActivities(prev => [data, ...prev]);
      setShowCreateActivity(false);
      setNewActivity({
        activityType: '', subject: '', description: '', durationMinutes: 0,
        outcome: '', nextAction: ''
      });
      toast({
        title: "Success",
        description: "Activity logged successfully"
      });
    } else {
      toast({
        title: "Error",
        description: "Failed to log activity",
        variant: "destructive"
      });
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: "Copied!",
        description: "Link copied to clipboard"
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to copy to clipboard",
        variant: "destructive"
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-100 text-yellow-800', label: 'Pending' },
      converted: { color: 'bg-green-100 text-green-800', label: 'Converted' },
      expired: { color: 'bg-red-100 text-red-800', label: 'Expired' },
      new: { color: 'bg-blue-100 text-blue-800', label: 'New' },
      contacted: { color: 'bg-purple-100 text-purple-800', label: 'Contacted' },
      qualified: { color: 'bg-orange-100 text-orange-800', label: 'Qualified' },
      proposal: { color: 'bg-indigo-100 text-indigo-800', label: 'Proposal' },
      closed_won: { color: 'bg-green-100 text-green-800', label: 'Closed Won' },
      closed_lost: { color: 'bg-red-100 text-red-800', label: 'Closed Lost' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    return <Badge className={config.color}>{config.label}</Badge>;
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading marketing data...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Marketing Features</h1>
          <p className="text-gray-600">Manage referrals, leads, and campaigns</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="referrals" className="flex items-center gap-2">
            <Share2 className="h-4 w-4" />
            Referrals
          </TabsTrigger>
          <TabsTrigger value="leads" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Lead Management
          </TabsTrigger>
          <TabsTrigger value="campaigns" className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            Campaigns
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        {/* Referrals Tab */}
        <TabsContent value="referrals" className="space-y-6">
          {/* Referral Stats */}
          {referralStats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Referrals</CardTitle>
                  <Share2 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{referralStats.total_referrals || 0}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Converted</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{referralStats.converted_referrals || 0}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Rewards</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">${referralStats.total_rewards || 0}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Pending Rewards</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">${referralStats.pending_rewards || 0}</div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Create Referral Link */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Share2 className="h-5 w-5" />
                Create Referral Link
              </CardTitle>
              <CardDescription>
                Generate a unique referral link to share with others
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setShowCreateReferral(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create New Referral Link
              </Button>
            </CardContent>
          </Card>

          {/* Referral Links List */}
          <Card>
            <CardHeader>
              <CardTitle>Your Referral Links</CardTitle>
              <CardDescription>
                Track your referral links and their performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {userReferrals.map((referral) => (
                  <div key={referral.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                          {referral.referral_code}
                        </code>
                        {getStatusBadge(referral.status)}
                      </div>
                      <p className="text-sm text-gray-600">
                        Created: {new Date(referral.created_at).toLocaleDateString()}
                      </p>
                      {referral.conversion_date && (
                        <p className="text-sm text-green-600">
                          Converted: {new Date(referral.conversion_date).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(referral.referral_link)}
                      >
                        <Copy className="h-4 w-4 mr-1" />
                        Copy
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(referral.referral_link, '_blank')}
                      >
                        <ExternalLink className="h-4 w-4 mr-1" />
                        Open
                      </Button>
                    </div>
                  </div>
                ))}
                {userReferrals.length === 0 && (
                  <p className="text-center text-gray-500 py-8">
                    No referral links created yet. Create your first one above!
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Referral Rewards */}
          <Card>
            <CardHeader>
              <CardTitle>Referral Rewards</CardTitle>
              <CardDescription>
                Track your earned rewards from successful referrals
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {referralRewards.map((reward) => (
                  <div key={reward.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium">
                          ${reward.reward_value} {reward.reward_currency}
                        </span>
                        {getStatusBadge(reward.status)}
                      </div>
                      <p className="text-sm text-gray-600">
                        {reward.referral_programs.name} • {new Date(reward.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
                {referralRewards.length === 0 && (
                  <p className="text-center text-gray-500 py-8">
                    No rewards earned yet. Start referring people to earn rewards!
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Lead Management Tab */}
        <TabsContent value="leads" className="space-y-6">
          {/* Create Lead Contact */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserPlus className="h-5 w-5" />
                Add New Lead
              </CardTitle>
              <CardDescription>
                Create a new lead contact to track in your campaigns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setShowCreateContact(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add New Lead
              </Button>
            </CardContent>
          </Card>

          {/* Lead Contacts List */}
          <Card>
            <CardHeader>
              <CardTitle>Lead Contacts</CardTitle>
              <CardDescription>
                Manage and track your lead contacts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {leadContacts.map((contact) => (
                  <div key={contact.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-medium">
                          {contact.first_name} {contact.last_name}
                        </h4>
                        {getStatusBadge(contact.status)}
                        <Badge variant="outline">Score: {contact.lead_score}</Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          {contact.email}
                        </span>
                        {contact.phone && (
                          <span className="flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {contact.phone}
                          </span>
                        )}
                        {contact.company && (
                          <span className="flex items-center gap-1">
                            <Building className="h-3 w-3" />
                            {contact.company}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        Added: {new Date(contact.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedContact(contact);
                          setShowCreateActivity(true);
                        }}
                      >
                        <Activity className="h-4 w-4 mr-1" />
                        Log Activity
                      </Button>
                    </div>
                  </div>
                ))}
                {leadContacts.length === 0 && (
                  <p className="text-center text-gray-500 py-8">
                    No lead contacts yet. Add your first lead above!
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Campaigns Tab */}
        <TabsContent value="campaigns" className="space-y-6">
          {/* Create Campaign */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Create Campaign
              </CardTitle>
              <CardDescription>
                Set up a new marketing campaign to track leads
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setShowCreateCampaign(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create New Campaign
              </Button>
            </CardContent>
          </Card>

          {/* Campaigns List */}
          <Card>
            <CardHeader>
              <CardTitle>Marketing Campaigns</CardTitle>
              <CardDescription>
                Manage your marketing campaigns and track performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {leadCampaigns.map((campaign) => (
                  <div key={campaign.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-medium">{campaign.name}</h4>
                        {getStatusBadge(campaign.status)}
                        <Badge variant="outline">{campaign.campaign_type}</Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{campaign.description}</p>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        {campaign.budget && (
                          <span className="flex items-center gap-1">
                            <DollarSign className="h-3 w-3" />
                            Budget: ${campaign.budget}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          Started: {new Date(campaign.start_date).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedCampaign(campaign)}
                    >
                      <BarChart3 className="h-4 w-4 mr-1" />
                      View Analytics
                    </Button>
                  </div>
                ))}
                {leadCampaigns.length === 0 && (
                  <p className="text-center text-gray-500 py-8">
                    No campaigns created yet. Create your first campaign above!
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Marketing Analytics
              </CardTitle>
              <CardDescription>
                View performance metrics and insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Analytics Coming Soon</h3>
                <p className="text-gray-600">
                  Detailed analytics and reporting features will be available soon.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Referral Link Dialog */}
      <Dialog open={showCreateReferral} onOpenChange={setShowCreateReferral}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Referral Link</DialogTitle>
            <DialogDescription>
              Generate a new referral link to share with potential users
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              This will create a unique referral link that you can share with others.
              When they sign up using your link, you'll earn rewards!
            </p>
            <div className="flex gap-2">
              <Button onClick={handleCreateReferralLink}>
                Create Referral Link
              </Button>
              <Button variant="outline" onClick={() => setShowCreateReferral(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Campaign Dialog */}
      <Dialog open={showCreateCampaign} onOpenChange={setShowCreateCampaign}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Marketing Campaign</DialogTitle>
            <DialogDescription>
              Set up a new marketing campaign to track leads and performance
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="campaign-name">Campaign Name</Label>
              <Input
                id="campaign-name"
                value={newCampaign.name}
                onChange={(e) => setNewCampaign(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Enter campaign name"
              />
            </div>
            <div>
              <Label htmlFor="campaign-description">Description</Label>
              <Textarea
                id="campaign-description"
                value={newCampaign.description}
                onChange={(e) => setNewCampaign(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe your campaign"
              />
            </div>
            <div>
              <Label htmlFor="campaign-type">Campaign Type</Label>
              <Select
                value={newCampaign.campaignType}
                onValueChange={(value) => setNewCampaign(prev => ({ ...prev, campaignType: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select campaign type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="referral">Referral</SelectItem>
                  <SelectItem value="social_media">Social Media</SelectItem>
                  <SelectItem value="email">Email</SelectItem>
                  <SelectItem value="content">Content</SelectItem>
                  <SelectItem value="paid_ads">Paid Ads</SelectItem>
                  <SelectItem value="organic">Organic</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="campaign-budget">Budget (USD)</Label>
              <Input
                id="campaign-budget"
                type="number"
                value={newCampaign.budget}
                onChange={(e) => setNewCampaign(prev => ({ ...prev, budget: parseFloat(e.target.value) || 0 }))}
                placeholder="0.00"
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreateCampaign}>
                Create Campaign
              </Button>
              <Button variant="outline" onClick={() => setShowCreateCampaign(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Contact Dialog */}
      <Dialog open={showCreateContact} onOpenChange={setShowCreateContact}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Lead Contact</DialogTitle>
            <DialogDescription>
              Add a new lead contact to your marketing database
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="contact-first-name">First Name</Label>
                <Input
                  id="contact-first-name"
                  value={newContact.firstName}
                  onChange={(e) => setNewContact(prev => ({ ...prev, firstName: e.target.value }))}
                  placeholder="First name"
                />
              </div>
              <div>
                <Label htmlFor="contact-last-name">Last Name</Label>
                <Input
                  id="contact-last-name"
                  value={newContact.lastName}
                  onChange={(e) => setNewContact(prev => ({ ...prev, lastName: e.target.value }))}
                  placeholder="Last name"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="contact-email">Email *</Label>
              <Input
                id="contact-email"
                type="email"
                value={newContact.email}
                onChange={(e) => setNewContact(prev => ({ ...prev, email: e.target.value }))}
                placeholder="email@example.com"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="contact-phone">Phone</Label>
                <Input
                  id="contact-phone"
                  value={newContact.phone}
                  onChange={(e) => setNewContact(prev => ({ ...prev, phone: e.target.value }))}
                  placeholder="Phone number"
                />
              </div>
              <div>
                <Label htmlFor="contact-company">Company</Label>
                <Input
                  id="contact-company"
                  value={newContact.company}
                  onChange={(e) => setNewContact(prev => ({ ...prev, company: e.target.value }))}
                  placeholder="Company name"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="contact-job-title">Job Title</Label>
              <Input
                id="contact-job-title"
                value={newContact.jobTitle}
                onChange={(e) => setNewContact(prev => ({ ...prev, jobTitle: e.target.value }))}
                placeholder="Job title"
              />
            </div>
            <div>
              <Label htmlFor="contact-notes">Notes</Label>
              <Textarea
                id="contact-notes"
                value={newContact.notes}
                onChange={(e) => setNewContact(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Additional notes about this lead"
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreateContact}>
                Add Lead Contact
              </Button>
              <Button variant="outline" onClick={() => setShowCreateContact(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Create Activity Dialog */}
      <Dialog open={showCreateActivity} onOpenChange={setShowCreateActivity}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Log Activity</DialogTitle>
            <DialogDescription>
              Log an activity for {selectedContact?.first_name} {selectedContact?.last_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="activity-type">Activity Type</Label>
              <Select
                value={newActivity.activityType}
                onValueChange={(value) => setNewActivity(prev => ({ ...prev, activityType: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select activity type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="email_sent">Email Sent</SelectItem>
                  <SelectItem value="email_opened">Email Opened</SelectItem>
                  <SelectItem value="email_clicked">Email Clicked</SelectItem>
                  <SelectItem value="call_made">Call Made</SelectItem>
                  <SelectItem value="meeting_scheduled">Meeting Scheduled</SelectItem>
                  <SelectItem value="proposal_sent">Proposal Sent</SelectItem>
                  <SelectItem value="status_changed">Status Changed</SelectItem>
                  <SelectItem value="note_added">Note Added</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="activity-subject">Subject</Label>
              <Input
                id="activity-subject"
                value={newActivity.subject}
                onChange={(e) => setNewActivity(prev => ({ ...prev, subject: e.target.value }))}
                placeholder="Activity subject"
              />
            </div>
            <div>
              <Label htmlFor="activity-description">Description</Label>
              <Textarea
                id="activity-description"
                value={newActivity.description}
                onChange={(e) => setNewActivity(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe the activity"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="activity-duration">Duration (minutes)</Label>
                <Input
                  id="activity-duration"
                  type="number"
                  value={newActivity.durationMinutes}
                  onChange={(e) => setNewActivity(prev => ({ ...prev, durationMinutes: parseInt(e.target.value) || 0 }))}
                  placeholder="0"
                />
              </div>
              <div>
                <Label htmlFor="activity-outcome">Outcome</Label>
                <Input
                  id="activity-outcome"
                  value={newActivity.outcome}
                  onChange={(e) => setNewActivity(prev => ({ ...prev, outcome: e.target.value }))}
                  placeholder="Activity outcome"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="activity-next-action">Next Action</Label>
              <Input
                id="activity-next-action"
                value={newActivity.nextAction}
                onChange={(e) => setNewActivity(prev => ({ ...prev, nextAction: e.target.value }))}
                placeholder="What's the next step?"
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleCreateActivity}>
                Log Activity
              </Button>
              <Button variant="outline" onClick={() => setShowCreateActivity(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default MarketingFeatures;
