import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Play, Pause, Settings, Activity, DollarSign, Clock, Edit, Tag, Zap, Trash2, BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import AssistantConfiguration from './AssistantConfiguration';

interface Assistant {
  id: string;
  assistant_name: string;
  assistant_type: string;
  assistant_id: string;
  demo_url: string;
  created_at: string;
  status: string;
  voice_id?: string;
}

interface UsageStats {
  total_minutes: number;
  total_cost: number;
  sessions_count: number;
  today_minutes: number;
  today_cost: number;
}

interface AssistantManagerProps {
  assistant: Assistant;
  onStatusChange: (assistantId: string, newStatus: string, newType?: string) => void;
}

const AssistantManager = ({ assistant, onStatusChange }: AssistantManagerProps) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [pausing, setPausing] = useState(false);
  const [editingUrl, setEditingUrl] = useState(false);
  const [customUrl, setCustomUrl] = useState(assistant.demo_url || '');
  const [savingUrl, setSavingUrl] = useState(false);
  const [editingType, setEditingType] = useState(false);
  const [customType, setCustomType] = useState(assistant.assistant_type);
  const [savingType, setSavingType] = useState(false);
  const [showConfiguration, setShowConfiguration] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Assistant type options
  const ASSISTANT_TYPES = [
    { value: "sales_cold_call", label: "Sales - Cold Call" },
    { value: "help_desk", label: "Help Desk" },
    { value: "follow_up", label: "Follow-up (e.g. Church)" },
    { value: "survey", label: "Survey" },
    { value: "appointment_booking", label: "Appointment Booking" },
    { value: "customer_service", label: "Customer Service" },
    { value: "lead_qualification", label: "Lead Qualification" },
    { value: "product_support", label: "Product Support" },
    { value: "order_tracking", label: "Order Tracking" },
    { value: "feedback_collection", label: "Feedback Collection" },
    { value: "technical_support", label: "Technical Support" },
    { value: "consultation", label: "Consultation" },
    { value: "external", label: "External" },
  ];

  useEffect(() => {
    loadUsageStats();
  }, [assistant.assistant_id]);

  const loadUsageStats = async () => {
    if (!user || !assistant.assistant_id) return;

    try {
      // Get total usage stats
      const { data: totalUsage, error: totalError } = await supabase
        .from('usage_tracking')
        .select('duration_minutes, total_cost')
        .eq('user_id', user.id)
        .eq('assistant_id', assistant.assistant_id)
        .eq('status', 'completed');

      if (totalError) {
        console.error('Error loading total usage:', totalError);
        return;
      }

      // Get today's usage
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      const { data: todayUsage, error: todayError } = await supabase
        .from('usage_tracking')
        .select('duration_minutes, total_cost')
        .eq('user_id', user.id)
        .eq('assistant_id', assistant.assistant_id)
        .eq('status', 'completed')
        .gte('created_at', today.toISOString());

      if (todayError) {
        console.error('Error loading today usage:', todayError);
        return;
      }

      const stats: UsageStats = {
        total_minutes: totalUsage?.reduce((sum, record) => sum + (record.duration_minutes || 0), 0) || 0,
        total_cost: totalUsage?.reduce((sum, record) => sum + (record.total_cost || 0), 0) || 0,
        sessions_count: totalUsage?.length || 0,
        today_minutes: todayUsage?.reduce((sum, record) => sum + (record.duration_minutes || 0), 0) || 0,
        today_cost: todayUsage?.reduce((sum, record) => sum + (record.total_cost || 0), 0) || 0,
      };

      setUsageStats(stats);
    } catch (error) {
      console.error('Error loading usage stats:', error);
    }
  };

  const handleStatusToggle = async () => {
    if (!user) return;

    setPausing(true);
    try {
      const newStatus = assistant.status === 'active' ? 'paused' : 'active';
      
      // Update assistant status in VAPI
      const { error: vapiError } = await supabase.functions.invoke('manage-assistant', {
        body: {
          action: 'status',
          assistant_id: assistant.id,
          user_id: user.id,
          status: newStatus
        }
      });

      if (vapiError) throw vapiError;

      // Update local status
      onStatusChange(assistant.id, newStatus);

      toast({
        title: 'Success',
        description: `Assistant ${newStatus === 'paused' ? 'deactivated' : 'activated'} successfully`,
      });
    } catch (error: any) {
      console.error('Error toggling assistant status:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to update assistant status',
        variant: 'destructive'
      });
    } finally {
      setPausing(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default" className="bg-green-100 text-green-800">Active</Badge>;
      case 'paused':
        return <Badge variant="secondary">Deactivated</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const handleSaveUrl = async () => {
    if (!user) return;

    setSavingUrl(true);
    try {
      const { error } = await supabase
        .from('custom_demos')
        .update({
          demo_url: customUrl.trim() || '',
          website_url: customUrl.trim() || '',
          updated_at: new Date().toISOString(),
        })
        .eq('id', assistant.id);

      if (error) throw error;

      toast({
        title: 'URL Updated',
        description: 'Custom URL has been saved successfully',
      });

      setEditingUrl(false);
      // Trigger a refresh of the assistant data
      onStatusChange(assistant.id, assistant.status);
    } catch (error: any) {
      console.error('Error saving URL:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to save URL',
        variant: 'destructive'
      });
    } finally {
      setSavingUrl(false);
    }
  };

  const handleSaveType = async () => {
    if (!user) return;

    setSavingType(true);
    try {
      const { error } = await supabase
        .from('custom_demos')
        .update({
          assistant_type: customType.trim(),
          updated_at: new Date().toISOString(),
        })
        .eq('id', assistant.id);

      if (error) throw error;

      toast({
        title: 'Type Updated',
        description: 'Assistant type has been updated successfully',
      });

      setEditingType(false);
      // Trigger a refresh of the assistant data
      onStatusChange(assistant.id, assistant.status, customType.trim());
    } catch (error: any) {
      console.error('Error saving type:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to save assistant type',
        variant: 'destructive'
      });
    } finally {
      setSavingType(false);
    }
  };

  const handleConfigurationComplete = (assistantId: string, config: any) => {
    // Here you would save the configuration to your database
    console.log('Configuration saved for assistant:', assistantId, config);
    toast({
      title: 'Configuration Saved',
      description: 'Assistant integrations have been configured successfully.',
    });
  };

  const handleDelete = async () => {
    if (!user || !assistant.assistant_id) return;

    // Confirm deletion
    if (!confirm(`Are you sure you want to delete "${assistant.assistant_name}"? This action cannot be undone and will permanently delete the assistant from both the app and Vapi.`)) {
      return;
    }

    setDeleting(true);
    try {
      // First, delete from Vapi
      console.log('Deleting assistant from Vapi:', assistant.assistant_id);
      const { error: vapiError } = await supabase.functions.invoke('manage-assistant', {
        body: { 
          action: 'delete', 
          assistant_id: assistant.id,
          user_id: user.id
        }
      });

      if (vapiError) {
        console.error('Error deleting assistant:', vapiError);
        throw vapiError;
      }

      toast({
        title: 'Assistant Deleted',
        description: `"${assistant.assistant_name}" has been permanently deleted from both the app and Vapi.`,
      });

      // Trigger a refresh of the assistant list
      onStatusChange(assistant.id, 'deleted');
    } catch (error: any) {
      console.error('Error deleting assistant:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete assistant',
        variant: 'destructive'
      });
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="text-lg">{assistant.assistant_name}</CardTitle>
            {getStatusBadge(assistant.status)}
          </div>
          <div className="flex items-center gap-2">
            <Switch
              checked={assistant.status === 'active'}
              onCheckedChange={handleStatusToggle}
              disabled={pausing}
            />
                         <span className="text-sm text-muted-foreground">
               {assistant.status === 'active' ? 'Active' : 'Deactivated'}
             </span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
                 {/* Assistant Info */}
         <div className="grid grid-cols-2 gap-4 text-sm">
           <div>
             <span className="text-muted-foreground">Type:</span>
             <div className="font-medium capitalize flex items-center gap-2">
               {editingType ? (
                 <div className="flex items-center gap-2">
                   <select
                     value={customType}
                     onChange={(e) => setCustomType(e.target.value)}
                     className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                     disabled={savingType}
                   >
                     {ASSISTANT_TYPES.map((type) => (
                       <option key={type.value} value={type.value}>
                         {type.label}
                       </option>
                     ))}
                   </select>
                   <Button
                     size="sm"
                     onClick={handleSaveType}
                     disabled={savingType}
                     className="flex items-center gap-1 px-2 py-1 text-xs"
                   >
                     {savingType ? (
                       <>
                         <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div>
                         Saving...
                       </>
                     ) : (
                       'Save'
                     )}
                   </Button>
                   <Button
                     variant="outline"
                     size="sm"
                     onClick={() => {
                       setEditingType(false);
                       setCustomType(assistant.assistant_type);
                     }}
                     disabled={savingType}
                     className="px-2 py-1 text-xs"
                   >
                     Cancel
                   </Button>
                 </div>
               ) : (
                 <>
                   {assistant.assistant_type.replace('_', ' ')}
                   {assistant.assistant_type === 'external' && (
                     <Badge variant="outline" className="text-xs">External</Badge>
                   )}
                 </>
               )}
             </div>
             {!editingType && (
               <Button
                 variant="ghost"
                 size="sm"
                 onClick={() => setEditingType(true)}
                 className="flex items-center gap-1 px-2 py-1 text-xs mt-1"
               >
                 <Tag className="h-3 w-3" />
                 Edit Type
               </Button>
             )}
           </div>
           <div>
             <span className="text-muted-foreground">Created:</span>
             <div className="font-medium">
               {new Date(assistant.created_at).toLocaleDateString()}
             </div>
           </div>
         </div>

        {/* Usage Stats */}
        {usageStats && (
          <div className="border-t pt-4">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Usage Statistics
            </h4>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Total Usage:</span>
                  <span className="font-medium flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDuration(usageStats.total_minutes)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Total Cost:</span>
                  <span className="font-medium flex items-center gap-1">
                    <DollarSign className="h-3 w-3" />
                    ${usageStats.total_cost.toFixed(2)}
                  </span>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Today:</span>
                  <span className="font-medium flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDuration(usageStats.today_minutes)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Today Cost:</span>
                  <span className="font-medium flex items-center gap-1">
                    <DollarSign className="h-3 w-3" />
                    ${usageStats.today_cost.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="mt-3 text-xs text-muted-foreground">
              {usageStats.sessions_count} total sessions
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="border-t pt-4">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleStatusToggle}
              disabled={pausing}
              className="flex items-center gap-2"
            >
              {pausing ? (
                <>
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div>
                                     {assistant.status === 'active' ? 'Deactivating...' : 'Activating...'}
                </>
              ) : (
                <>
                                     {assistant.status === 'active' ? (
                     <>
                       <Pause className="h-3 w-3" />
                       Deactivate
                     </>
                   ) : (
                     <>
                       <Play className="h-3 w-3" />
                       Activate
                     </>
                   )}
                </>
              )}
            </Button>
            
            {assistant.assistant_type === 'external' ? (
              assistant.demo_url ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(assistant.demo_url, '_blank')}
                  className="flex items-center gap-2"
                >
                  <Settings className="h-3 w-3" />
                  Preview
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(`https://vapi.ai/dashboard/assistant/${assistant.assistant_id}`, '_blank')}
                  className="flex items-center gap-2"
                >
                  <Settings className="h-3 w-3" />
                  View in Vapi
                </Button>
              )
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(assistant.demo_url || `/demo-preview?id=${assistant.assistant_id}`, '_blank')}
                className="flex items-center gap-2"
              >
                <Settings className="h-3 w-3" />
                Preview
              </Button>
            )}

                         {/* View Details button */}
            <Button
              variant="outline"
              size="sm"
              asChild
              className="flex items-center gap-2"
            >
              <Link to={`/voice-agents/${assistant.id}`}>
                <BarChart3 className="h-3 w-3" />
                View Details
              </Link>
            </Button>

            {/* Configure button */}
             <Button
               variant="outline"
               size="sm"
               onClick={() => setShowConfiguration(true)}
               className="flex items-center gap-2"
             >
               <Zap className="h-3 w-3" />
               Configure
             </Button>

             {/* Edit URL button for external assistants */}
             {assistant.assistant_type === 'external' && (
               <Button
                 variant="outline"
                 size="sm"
                 onClick={() => setEditingUrl(!editingUrl)}
                 className="flex items-center gap-2"
               >
                 <Edit className="h-3 w-3" />
                 Edit URL
               </Button>
             )}

             {/* Delete button */}
             <Button
               variant="outline"
               size="sm"
               onClick={handleDelete}
               disabled={deleting}
               className="flex items-center gap-2 text-red-600 hover:text-red-700 hover:bg-red-50"
             >
               {deleting ? (
                 <>
                   <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div>
                   Deleting...
                 </>
               ) : (
                 <>
                   <Trash2 className="h-3 w-3" />
                   Delete
                 </>
               )}
             </Button>
          </div>

          {/* URL editing section for external assistants */}
          {assistant.assistant_type === 'external' && editingUrl && (
            <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Custom URL</label>
                <input
                  type="url"
                  value={customUrl}
                  onChange={(e) => setCustomUrl(e.target.value)}
                  placeholder="https://your-website.com/assistant"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={savingUrl}
                />
                <p className="text-xs text-gray-500">
                  Leave empty to remove the custom URL and use Vapi dashboard only
                </p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleSaveUrl}
                    disabled={savingUrl}
                    className="flex items-center gap-2"
                  >
                    {savingUrl ? (
                      <>
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div>
                        Saving...
                      </>
                    ) : (
                      'Save URL'
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditingUrl(false);
                      setCustomUrl(assistant.demo_url || '');
                    }}
                    disabled={savingUrl}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

                 {/* Status Note */}
         {assistant.status === 'paused' && (
           <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
             <div className="flex items-center gap-2 text-sm text-yellow-800">
               <Pause className="h-4 w-4" />
               <span className="font-medium">Assistant Deactivated</span>
             </div>
             <p className="text-xs text-yellow-700 mt-1">
               This assistant is deactivated and will not receive or take calls. It has been disabled in Vapi and cannot be used for conversations.
             </p>
           </div>
                  )}

         {/* Assistant Configuration Dialog */}
         {showConfiguration && (
           <AssistantConfiguration
             assistant={assistant}
             onConfigurationComplete={handleConfigurationComplete}
             onClose={() => setShowConfiguration(false)}
           />
         )}
       </CardContent>
     </Card>
   );
 };

export default AssistantManager;
