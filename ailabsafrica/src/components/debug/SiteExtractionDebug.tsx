import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/components/ui/use-toast";

interface SiteInfo {
  title: string;
  description: string;
  content: string;
}

const SiteExtractionDebug = () => {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SiteInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<string>("");
  const { toast } = useToast();

  const testExtraction = async () => {
    if (!url) {
      toast({
        title: "Error",
        description: "Please enter a URL",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setDebugInfo("");

    try {
      console.log("[SiteExtractionDebug] Testing extraction for:", url);
      setDebugInfo("Starting extraction...");
      
      // Validate URL format
      let validUrl = url;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        validUrl = 'https://' + url;
        console.log("[SiteExtractionDebug] Added https:// prefix:", validUrl);
        setDebugInfo(prev => prev + "\nAdded https:// prefix: " + validUrl);
      }

      setDebugInfo(prev => prev + "\nCalling extract-site-info edge function...");
      
      const { data, error } = await supabase.functions.invoke('extract-site-info', {
        body: { url: validUrl }
      });
      
      if (error) {
        console.error("[SiteExtractionDebug] Edge function error:", error);
        setError(`Edge function error: ${error.message || 'Unknown error'}`);
        setDebugInfo(prev => prev + `\nError: ${error.message}`);
        return;
      }
      
      if (!data) {
        setError('No data returned from site extraction');
        setDebugInfo(prev => prev + "\nNo data returned");
        return;
      }
      
      console.log("[SiteExtractionDebug] Extraction successful:", data);
      setResult(data);
      setDebugInfo(prev => prev + `\nSuccess! Title: ${data.title}, Content length: ${data.content?.length || 0}`);
      
      toast({
        title: "Success",
        description: "Site extraction completed successfully",
      });
      
    } catch (e: unknown) {
      console.error("[SiteExtractionDebug] Extraction error:", e);
      const error = e as Error;
      setError(`Extraction failed: ${error.message}`);
      setDebugInfo(prev => prev + `\nException: ${error.message}`);
      
      toast({
        title: "Error",
        description: `Extraction failed: ${error.message}`,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const testDirectFetch = async () => {
    if (!url) return;
    
    setDebugInfo("Testing direct fetch...");
    try {
      let validUrl = url;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        validUrl = 'https://' + url;
      }
      
      const response = await fetch(validUrl);
      setDebugInfo(prev => prev + `\nDirect fetch status: ${response.status} ${response.statusText}`);
      
      if (response.ok) {
        const text = await response.text();
        setDebugInfo(prev => prev + `\nDirect fetch content length: ${text.length}`);
      }
    } catch (e) {
      setDebugInfo(prev => prev + `\nDirect fetch error: ${(e as Error).message}`);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Site Extraction Debug Tool</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="url">Website URL</Label>
            <Input
              id="url"
              type="url"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>
          
          <div className="flex space-x-2">
            <Button onClick={testExtraction} disabled={loading}>
              {loading ? "Testing..." : "Test Extraction"}
            </Button>
            <Button onClick={testDirectFetch} variant="outline">
              Test Direct Fetch
            </Button>
          </div>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-md">
              <h3 className="font-semibold text-red-800">Error:</h3>
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <div>
                <Label>Title</Label>
                <Input value={result.title} readOnly />
              </div>
              <div>
                <Label>Description</Label>
                <Input value={result.description} readOnly />
              </div>
              <div>
                <Label>Content</Label>
                <Textarea 
                  value={result.content} 
                  readOnly 
                  rows={10}
                  className="font-mono text-sm"
                />
              </div>
            </div>
          )}

          {debugInfo && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
              <h3 className="font-semibold text-gray-800">Debug Info:</h3>
              <pre className="text-sm text-gray-700 whitespace-pre-wrap">{debugInfo}</pre>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SiteExtractionDebug;
