import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Play, Pause, MoreHorizontal, Users, Phone, Clock, Loader2, Activity, Shield } from 'lucide-react';
import { campaignApi, assistantApi } from '@/lib/core-api';
import { useToast } from '@/hooks/use-toast';
import AutomationHealthCard from '@/components/analytics/AutomationHealthCard';

interface CampaignTilesProps {
  tenantId: string;
}

interface CampaignWithAssistant extends any {
  assistant_name?: string;
  progress?: number;
  contacted?: number;
  total?: number;
  successRate?: number;
  startedAt?: string;
  automation_id?: string;
  has_automation?: boolean;
}

export function CampaignTiles({ tenantId }: CampaignTilesProps) {
  const [campaigns, setCampaigns] = useState<CampaignWithAssistant[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('campaigns');
  const { toast } = useToast();

  useEffect(() => {
    loadCampaigns();
  }, [tenantId]);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const campaignsData = await campaignApi.list();
      
      // Get assistant names for each campaign
      const campaignsWithAssistants = await Promise.all(
        campaignsData.map(async (campaign) => {
          let assistantName = 'Unknown Assistant';
          if (campaign.assistant_id) {
            try {
              const assistant = await assistantApi.get(campaign.assistant_id);
              assistantName = assistant.name;
            } catch (error) {
              console.error('Failed to load assistant:', error);
            }
          }
          
          // Calculate progress and stats (mock for now since we don't have real campaign progress data)
          const progress = campaign.status === 'completed' ? 100 : 
                          campaign.status === 'active' ? 65 : 
                          campaign.status === 'paused' ? 45 : 0;
          
          // Mock automation ID for campaigns that would have automation
          const hasAutomation = Math.random() > 0.3; // 70% chance of having automation
          const automationId = hasAutomation ? `automation-${campaign.id}-${Math.random().toString(36).substr(2, 9)}` : undefined;

          return {
            ...campaign,
            assistant_name: assistantName,
            progress,
            contacted: Math.floor(Math.random() * 1000) + 100, // Mock data
            total: Math.floor(Math.random() * 2000) + 500, // Mock data
            successRate: Math.floor(Math.random() * 50) + 20, // Mock data
            startedAt: campaign.created_at ? new Date(campaign.created_at).toRelativeTimeString() : 'Unknown',
            automation_id: automationId,
            has_automation: hasAutomation
          };
        })
      );
      
      setCampaigns(campaignsWithAssistants);
    } catch (error) {
      console.error('Failed to load campaigns:', error);
      toast({
        title: "Error",
        description: "Failed to load campaigns.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleViewHealthDetails = (automationId: string) => {
    // This would typically open a modal or navigate to a detailed health view
    toast({
      title: "Health Details",
      description: `Opening health details for automation ${automationId.slice(-8)}...`,
    });
    // TODO: Implement navigation to detailed health monitoring view
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'paused': return 'bg-yellow-500';
      case 'completed': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'running': return 'default';
      case 'paused': return 'secondary';
      case 'completed': return 'outline';
      default: return 'secondary';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Campaigns & Automations</h2>
        <Button className="gap-2">
          <Play className="h-4 w-4" />
          New Campaign
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="campaigns" className="gap-2">
            <Users className="h-4 w-4" />
            Campaigns
          </TabsTrigger>
          <TabsTrigger value="health" className="gap-2">
            <Shield className="h-4 w-4" />
            Health Monitor
          </TabsTrigger>
        </TabsList>

        <TabsContent value="campaigns" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {campaigns.map((campaign) => (
              <Card key={campaign.id} className="relative">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{campaign.name}</CardTitle>
                      <CardDescription className="mt-1">
                        Using {campaign.assistant_name}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={getStatusVariant(campaign.status)}>
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(campaign.status)} mr-1`}></div>
                        {campaign.status}
                      </Badge>
                      {campaign.has_automation && (
                        <Badge variant="outline" className="gap-1">
                          <Activity className="h-3 w-3" />
                          Auto
                        </Badge>
                      )}
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Progress */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Progress</span>
                      <span className="font-medium">{campaign.progress}%</span>
                    </div>
                    <Progress value={campaign.progress} className="h-2" />
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div className="space-y-1">
                      <div className="flex items-center justify-center gap-1">
                        <Users className="h-3 w-3 text-gray-600" />
                      </div>
                      <p className="text-sm font-medium">{campaign.contacted}</p>
                      <p className="text-xs text-gray-600">Contacted</p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center justify-center gap-1">
                        <Phone className="h-3 w-3 text-gray-600" />
                      </div>
                      <p className="text-sm font-medium">{campaign.successRate}%</p>
                      <p className="text-xs text-gray-600">Success</p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center justify-center gap-1">
                        <Clock className="h-3 w-3 text-gray-600" />
                      </div>
                      <p className="text-sm font-medium">{campaign.startedAt}</p>
                      <p className="text-xs text-gray-600">Started</p>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2">
                    {campaign.status === 'running' ? (
                      <Button variant="outline" size="sm" className="flex-1 gap-1">
                        <Pause className="h-3 w-3" />
                        Pause
                      </Button>
                    ) : campaign.status === 'paused' ? (
                      <Button size="sm" className="flex-1 gap-1">
                        <Play className="h-3 w-3" />
                        Resume
                      </Button>
                    ) : null}
                    <Button variant="outline" size="sm" className="flex-1">
                      View Details
                    </Button>
                    {campaign.has_automation && campaign.automation_id && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewHealthDetails(campaign.automation_id!)}
                        className="gap-1"
                      >
                        <Shield className="h-3 w-3" />
                        Health
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="health" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {campaigns
              .filter(campaign => campaign.has_automation && campaign.automation_id)
              .map((campaign) => (
                <AutomationHealthCard
                  key={campaign.automation_id}
                  automationId={campaign.automation_id!}
                  automationName={campaign.name}
                  onViewDetails={handleViewHealthDetails}
                  size="md"
                  showActions={true}
                />
              ))}

            {campaigns.filter(campaign => campaign.has_automation).length === 0 && (
              <div className="col-span-full text-center py-12">
                <Shield className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Automated Campaigns</h3>
                <p className="text-gray-600">
                  Campaigns with automation will appear here for health monitoring
                </p>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}