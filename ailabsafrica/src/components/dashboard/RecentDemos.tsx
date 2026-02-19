import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Eye, ExternalLink, Bot, Plus, Share2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/components/ui/use-toast";
import DemoSharing from "@/components/DemoSharing";
import DemoEmbedding from "@/components/DemoEmbedding";
import DemoVersioning from "@/components/DemoVersioning";
import DemoComments from "@/components/DemoComments";

interface DemoRow {
  id: string;
  assistant_name: string;
  assistant_type: string;
  demo_url: string;
  created_at: string;
  status: string;
  assistant_id: string;
  description?: string;
  current_version?: number;
}

const RecentDemos = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [demos, setDemos] = useState<DemoRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecentDemos();
  }, []);

  const loadRecentDemos = async () => {
    try {
      const { data, error } = await supabase
        .from("custom_demos")
        .select("*")
        .order("created_at", { ascending: false })
        .limit(3);

      if (error) throw error;
      setDemos(data || []);
    } catch (error: any) {
      console.error("Error loading recent demos:", error);
      toast({
        title: "Error loading demos",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Recent Demos
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Recent Demos
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => navigate("/voice-agents")}
          >
            View All
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {demos.length === 0 ? (
          <div className="text-center py-8">
            <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No demos yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first AI assistant demo to get started.
            </p>
            <Button onClick={() => navigate("/create-assistant")} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Create First Demo
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {demos.map((demo) => (
              <div
                key={demo.id}
                className="flex items-start justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors gap-3 overflow-hidden"
              >
                <div className="flex-1 min-w-0 max-w-[70%] sm:max-w-[60%]">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-semibold truncate">{demo.assistant_name}</h4>
                    <Badge 
                      variant={demo.status === 'active' ? 'default' : 'secondary'}
                      className="text-xs flex-shrink-0"
                    >
                      {demo.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground truncate">
                    {demo.assistant_type.replace(/_/g, ' ')} • {new Date(demo.created_at).toLocaleDateString()}
                  </p>
                  {demo.description && (
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
                      {demo.description}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-1 flex-shrink-0 flex-wrap max-w-[200px] sm:max-w-xs">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => window.open(demo.demo_url, '_blank')}
                    className="flex items-center gap-1 px-2 py-1 text-xs"
                  >
                    <Eye className="h-3 w-3" />
                    <span className="hidden sm:inline">Preview</span>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    asChild
                    className="flex items-center gap-1 px-2 py-1"
                  >
                    <a href={demo.demo_url} target="_blank" rel="noreferrer">
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </Button>
                  <DemoSharing
                    demoId={demo.id}
                    assistantName={demo.assistant_name}
                    assistantType={demo.assistant_type}
                    demoUrl={demo.demo_url}
                    description={demo.description}
                  />
                  <DemoEmbedding
                    demoId={demo.id}
                    assistantName={demo.assistant_name}
                    assistantType={demo.assistant_type}
                    assistantId={demo.assistant_id}
                    description={demo.description}
                  />
                  <DemoVersioning
                    demoId={demo.id}
                    assistantName={demo.assistant_name}
                    assistantType={demo.assistant_type}
                    currentVersion={demo.current_version || 1}
                  />
                  <DemoComments
                    demoId={demo.id}
                    assistantName={demo.assistant_name}
                    assistantType={demo.assistant_type}
                  />
                </div>
              </div>
            ))}
            <div className="pt-2">
              <Button 
                variant="secondary" 
                onClick={() => navigate("/create-assistant")} 
                className="w-full flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Create New Demo
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentDemos;