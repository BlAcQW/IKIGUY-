import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface AssistantData {
  id: string;
  assistant_name: string;
  assistant_type: string;
  assistant_id: string | null;
  demo_url: string | null;
  created_at: string;
  status: string;
}

const DataChecker = () => {
  const [assistants, setAssistants] = useState<AssistantData[]>([]);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const checkData = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke("list-custom-demos");
      if (error) throw error;
      
      const demos = (data?.demos as AssistantData[]) || [];
      setAssistants(demos);
      
      // Check for issues
      const issues = demos.filter(demo => !demo.assistant_id);
      if (issues.length > 0) {
        toast({
          title: "Data Issues Found",
          description: `${issues.length} assistants are missing assistant_id`,
          variant: "destructive"
        });
      } else {
        toast({
          title: "Data Check Complete",
          description: "All assistants have valid assistant_id values"
        });
      }
    } catch (error: any) {
      console.error('Data check error:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to check data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Assistant Data Checker</CardTitle>
      </CardHeader>
      <CardContent>
        <Button onClick={checkData} disabled={loading}>
          {loading ? "Checking..." : "Check Assistant Data"}
        </Button>
        
        {assistants.length > 0 && (
          <div className="mt-4">
            <h4 className="font-semibold mb-2">Assistant Data:</h4>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {assistants.map((assistant, index) => (
                <div 
                  key={assistant.id} 
                  className={`p-2 rounded border ${
                    !assistant.assistant_id ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'
                  }`}
                >
                  <div className="text-sm">
                    <strong>{assistant.assistant_name}</strong>
                    <br />
                    <span className="text-muted-foreground">
                      ID: {assistant.assistant_id || 'MISSING'} | 
                      Type: {assistant.assistant_type} | 
                      Status: {assistant.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DataChecker;
