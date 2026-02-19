import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { 
  Download, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  ExternalLink
} from 'lucide-react';

interface AssistantDetails {
  id: string;
  name: string;
  description?: string;
  model: string;
  voice: string;
  firstMessage?: string;
  systemPrompt?: string;
  createdAt: string;
  updatedAt: string;
  status: string;
  phoneNumberId?: string;
  phoneNumber?: string;
  serverUrl?: string;
  clientMessages?: string[];
  metadata?: Record<string, any>;
}

interface ImportAssistantProps {
  onImportSuccess?: () => void;
}

const ImportAssistant = ({ onImportSuccess }: ImportAssistantProps) => {
  const { toast } = useToast();
  const [assistantId, setAssistantId] = useState('');
  const [customUrl, setCustomUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [assistantDetails, setAssistantDetails] = useState<AssistantDetails | null>(null);
  const [importStatus, setImportStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleImport = async () => {
    if (!assistantId.trim()) {
      toast({
        title: "Error",
        description: "Please enter an assistant ID",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setImportStatus('idle');
    setAssistantDetails(null);

    try {
      const { data, error } = await supabase.functions.invoke('fetch-assistant-details', {
        body: { 
          assistantId: assistantId.trim(),
          customUrl: customUrl.trim() || undefined
        }
      });

      if (error) throw error;

      setAssistantDetails(data.assistant);
      setImportStatus(data.import.success ? 'success' : 'error');

      toast({
        title: data.import.success ? "Assistant Imported!" : "Assistant Already Exists",
        description: data.import.message,
        variant: data.import.success ? "default" : "secondary",
      });

      // Call the success callback if provided
      if (data.import.success && onImportSuccess) {
        onImportSuccess();
      }

    } catch (error: any) {
      console.error('Error importing assistant:', error);
      setImportStatus('error');
      
      toast({
        title: "Import Failed",
        description: error.message || "Failed to import assistant. Please check the assistant ID and try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Import External Assistant</h2>
        <p className="text-muted-foreground">
          Import assistants created directly on Vapi into your dashboard for management
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Import Assistant
          </CardTitle>
          <CardDescription>
            Enter the assistant ID from Vapi to import it into your dashboard
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="assistantId">Assistant ID</Label>
            <Input
              id="assistantId"
              placeholder="e.g., 96037449-9dd1-49d9-a092-b8d088d2b5c9"
              value={assistantId}
              onChange={(e) => setAssistantId(e.target.value)}
              disabled={loading}
            />
            <p className="text-sm text-muted-foreground">
              You can find the assistant ID in your Vapi dashboard or from the assistant's URL
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="customUrl">Custom URL (Optional)</Label>
            <Input
              id="customUrl"
              placeholder="e.g., https://your-website.com/assistant"
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              disabled={loading}
            />
            <p className="text-sm text-muted-foreground">
              Optional: Provide a custom URL for previewing this assistant. If not provided, you can only view it in Vapi.
            </p>
          </div>

          <div className="flex justify-end pt-4">
            <Button 
              onClick={handleImport} 
              disabled={loading || !assistantId.trim()}
              className="min-w-[120px]"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Import
                </>
              )}
            </Button>
          </div>

          {importStatus === 'success' && (
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Assistant imported successfully!</span>
            </div>
          )}

          {importStatus === 'error' && (
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm font-medium">Failed to import assistant</span>
            </div>
          )}
        </CardContent>
      </Card>

      {assistantDetails && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ExternalLink className="h-5 w-5" />
              Assistant Details
            </CardTitle>
            <CardDescription>
              Details of the imported assistant from Vapi
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Name</Label>
                  <p className="text-lg font-semibold">{assistantDetails.name}</p>
                </div>
                
                {assistantDetails.description && (
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Description</Label>
                    <p className="text-sm">{assistantDetails.description}</p>
                  </div>
                )}

                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Model</Label>
                  <p className="text-sm">{assistantDetails.model}</p>
                </div>

                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Voice</Label>
                  <p className="text-sm">{assistantDetails.voice}</p>
                </div>

                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Status</Label>
                  <p className="text-sm capitalize">{assistantDetails.status}</p>
                </div>
              </div>

              <div className="space-y-4">
                {assistantDetails.firstMessage && (
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">First Message</Label>
                    <p className="text-sm bg-muted p-2 rounded">{assistantDetails.firstMessage}</p>
                  </div>
                )}

                {assistantDetails.systemPrompt && (
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">System Prompt</Label>
                    <p className="text-sm bg-muted p-2 rounded max-h-32 overflow-y-auto">
                      {assistantDetails.systemPrompt}
                    </p>
                  </div>
                )}

                {assistantDetails.phoneNumber && (
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Phone Number</Label>
                    <p className="text-sm">{assistantDetails.phoneNumber}</p>
                  </div>
                )}

                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Created</Label>
                  <p className="text-sm">{formatDate(assistantDetails.createdAt)}</p>
                </div>

                <div>
                  <Label className="text-sm font-medium text-muted-foreground">Last Updated</Label>
                  <p className="text-sm">{formatDate(assistantDetails.updatedAt)}</p>
                </div>
              </div>
            </div>

            {assistantDetails.metadata && Object.keys(assistantDetails.metadata).length > 0 && (
              <div className="mt-6">
                <Label className="text-sm font-medium text-muted-foreground">Metadata</Label>
                <pre className="text-xs bg-muted p-3 rounded overflow-x-auto">
                  {JSON.stringify(assistantDetails.metadata, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ImportAssistant;
