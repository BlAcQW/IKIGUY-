import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, ExternalLink, Copy, Check } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { useDemoAnalytics } from "@/hooks/useDemoAnalytics";
import DemoSharing from "@/components/DemoSharing";
import DemoEmbedding from "@/components/DemoEmbedding";
import DemoVersioning from "@/components/DemoVersioning";
import DemoComments from "@/components/DemoComments";

const DemoPreview = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [htmlContent, setHtmlContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [assistantName, setAssistantName] = useState("");
  const [copied, setCopied] = useState(false);
  const [demoId, setDemoId] = useState<string>("");
  const [demoData, setDemoData] = useState<{
    assistant_type: string;
    description?: string;
    demo_url: string;
    current_version?: number;
  } | null>(null);

  const assistantId = searchParams.get("id");
  const html = searchParams.get("html");

  // Initialize analytics tracking
  const analytics = useDemoAnalytics(demoId, assistantId || "");

  useEffect(() => {
    console.log("DemoPreview: assistantId =", assistantId, "html =", html ? "present" : "not present");
    
    if (html) {
      try {
        const decodedHtml = decodeURIComponent(html);
        setHtmlContent(decodedHtml);
        
        // Extract assistant name from HTML title
        const titleMatch = decodedHtml.match(/<title>(.*?)<\/title>/);
        if (titleMatch) {
          setAssistantName(titleMatch[1].split(' - ')[0]);
        }
        
        setLoading(false);
      } catch (error) {
        console.error("Error decoding HTML:", error);
        toast({
          title: "Error",
          description: "Failed to load demo content",
          variant: "destructive"
        });
        setLoading(false);
      }
    } else if (assistantId && assistantId !== "undefined") {
      // Fetch from database if only ID is provided
      console.log("DemoPreview: Fetching demo data for assistant ID:", assistantId);
      fetchDemoData();
    } else {
      console.log("DemoPreview: No valid assistantId or html provided");
      setLoading(false);
    }
  }, [assistantId, html]);

  // Start analytics tracking when demo is loaded
  useEffect(() => {
    if (demoId && assistantId && !loading) {
      analytics.startSession();
    }
  }, [demoId, assistantId, loading, analytics]);

  const fetchDemoData = async () => {
    try {
      const { data, error } = await supabase
        .from("custom_demos")
        .select("id, assistant_name, assistant_type, description, demo_url")
        .eq("assistant_id", assistantId)
        .maybeSingle();

      if (error) throw error;

      if (data?.demo_url) {
        setAssistantName(data.assistant_name);
        setDemoId(data.id);
        setDemoData({
          assistant_type: data.assistant_type,
          description: data.description,
          demo_url: data.demo_url,
          current_version: data.current_version || 1,
        });

        // Check if this is a database-stored demo (demo-preview URL)
        if (data.demo_url.includes('/demo-preview?id=')) {
          // Fetch HTML content from the demo_html_storage table
          try {
            const demoIdFromUrl = data.demo_url.split('id=')[1];
            const { data: htmlData, error: htmlError } = await supabase
              .from('demo_html_storage')
              .select('html_content')
              .eq('demo_id', demoIdFromUrl)
              .maybeSingle();

            if (htmlError) throw htmlError;

            if (htmlData?.html_content) {
              setHtmlContent(htmlData.html_content);
            } else {
              toast({
                title: "Demo content not found",
                description: "The demo HTML content could not be retrieved",
                variant: "destructive"
              });
            }
          } catch (error) {
            console.error("Error fetching demo HTML from database:", error);
            toast({
              title: "Demo load error",
              description: "Failed to load the demo content from database",
              variant: "destructive"
            });
          }
        } else {
          // Fetch the HTML content from the demo URL (file-based demo)
          try {
            const response = await fetch(data.demo_url);
            if (response.ok) {
              const htmlContent = await response.text();
              setHtmlContent(htmlContent);
            } else {
              toast({
                title: "Demo not accessible",
                description: "The demo page could not be loaded",
                variant: "destructive"
              });
            }
          } catch (error) {
            console.error("Error fetching demo HTML:", error);
            toast({
              title: "Demo load error",
              description: "Failed to load the demo content",
              variant: "destructive"
            });
          }
        }
      } else {
        toast({
          title: "No demo found",
          description: "This assistant doesn't have a demo page yet",
          variant: "destructive"
        });
      }
    } catch (error: any) {
      console.error("Error fetching demo:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to load demo",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const copyHtml = async () => {
    try {
      await navigator.clipboard.writeText(htmlContent);
      setCopied(true);
      
      // Track copy interaction
      if (analytics.trackInteraction) {
        analytics.trackInteraction('copy_html', { demo_id: demoId });
      }
      
      toast({
        title: "Copied!",
        description: "HTML code copied to clipboard"
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: "Failed to copy",
        description: "Could not copy HTML to clipboard",
        variant: "destructive"
      });
    }
  };

  const openInNewTab = () => {
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
    
    // Track open in new tab interaction
    if (analytics.trackInteraction) {
      analytics.trackInteraction('open_new_tab', { demo_id: demoId });
    }
    
    // Clean up the URL after a delay
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  const handleShare = (platform: string, url: string) => {
    // Track share event
    if (analytics.trackShare) {
      analytics.trackShare(platform, { demo_id: demoId, platform, url });
    }
  };

  const handleVersionChange = (versionNumber: number) => {
    // Update the current version in demo data
    if (demoData) {
      setDemoData({
        ...demoData,
        current_version: versionNumber,
      });
    }
  };

  const handleEmbed = (embedType: string, code: string) => {
    // Track embed event
    if (analytics.trackEmbed) {
      analytics.trackEmbed(embedType, { demo_id: demoId, embed_type: embedType, code_length: code.length });
    }
  };

  const handleCommentChange = () => {
    // Track comment event
    if (analytics.trackComment) {
      analytics.trackComment({
        demo_id: demoId,
        assistant_id: assistantId || "",
      });
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading demo...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!htmlContent) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <Button variant="outline" onClick={() => navigate(-1)} className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
        </div>
        
        <Card>
          <CardContent className="p-8 text-center">
            <h2 className="text-xl font-semibold mb-4">Demo Not Found</h2>
            <p className="text-muted-foreground mb-6">
              The requested demo could not be loaded. It may have been deleted or the link is invalid.
            </p>
            <Button onClick={() => navigate("/voice-agents")}>
              View All Assistants
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <Button variant="outline" onClick={() => navigate(-1)} className="flex items-center gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={copyHtml} className="flex items-center gap-2">
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? "Copied!" : "Copy HTML"}
          </Button>
          
          <Button onClick={openInNewTab} className="flex items-center gap-2">
            <ExternalLink className="h-4 w-4" />
            Open in New Tab
          </Button>

          {demoData && (
            <>
              <DemoSharing
                demoId={demoId}
                assistantName={assistantName}
                assistantType={demoData.assistant_type}
                demoUrl={demoData.demo_url}
                description={demoData.description}
                onShare={handleShare}
              />
              <DemoEmbedding
                demoId={demoId}
                assistantName={assistantName}
                assistantType={demoData.assistant_type}
                assistantId={assistantId || ""}
                description={demoData.description}
                onEmbed={handleEmbed}
              />
              <DemoVersioning
                demoId={demoId}
                assistantName={assistantName}
                assistantType={demoData.assistant_type}
                currentVersion={demoData.current_version}
                onVersionChange={handleVersionChange}
              />
            </>
          )}
        </div>
      </div>

      {/* Demo Comments Section */}
      {demoData && (
        <div className="mb-6">
          <DemoComments
            demoId={demoId}
            assistantName={assistantName}
            assistantType={demoData.assistant_type}
            onCommentChange={handleCommentChange}
          />
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Demo Preview: {assistantName}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="border rounded-lg overflow-hidden bg-muted p-8">
            <div className="text-center space-y-4">
              <div className="text-6xl">🎉</div>
              <h3 className="text-xl font-semibold">Your Demo is Ready!</h3>
              <p className="text-muted-foreground">
                Your AI assistant demo has been successfully deployed and is ready to use.
              </p>
              
              {demoData?.demo_url && (
                <div className="space-y-4">
                  <div className="p-4 bg-background rounded-lg border">
                    <p className="text-sm font-medium mb-2">Demo URL:</p>
                    <p className="text-sm text-muted-foreground break-all">
                      {demoData.demo_url}
                    </p>
                  </div>
                  
                  <Button 
                    onClick={() => window.open(demoData.demo_url, '_blank')}
                    className="w-full"
                    size="lg"
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Open Demo in New Tab
                  </Button>
                </div>
              )}
              
              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  <strong>Note:</strong> Your demo has been deployed to our server and is accessible via the URL above. 
                  The email with the demo link has been sent to your email address.
                </p>
              </div>
            </div>
          </div>
          
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <p className="text-sm text-muted-foreground mb-2">
              <strong>What's Next:</strong>
            </p>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Click "Open Demo in New Tab" to test your assistant</li>
              <li>• Share the demo URL with others</li>
              <li>• Check your email for the demo link</li>
              <li>• Access all your demos from your dashboard</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DemoPreview;