import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { Globe, Loader2, Download, Copy } from 'lucide-react';
import { api } from '@/lib/api-client';

interface ScraperResult {
  url: string;
  title: string;
  content: string;
  metadata: {
    word_count: number;
    char_count: number;
    extraction_time: number;
  };
}

export function WebScraperPanel() {
  const [url, setUrl] = useState('');
  const [extractionMode, setExtractionMode] = useState('main-content');
  const [removeAds, setRemoveAds] = useState(true);
  const [waitForJs, setWaitForJs] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [result, setResult] = useState<ScraperResult | null>(null);
  const { toast } = useToast();

  const handleExtract = async () => {
    if (!url) {
      toast({
        title: "URL Required",
        description: "Please enter a URL to scrape",
        variant: "destructive"
      });
      return;
    }

    setIsExtracting(true);
    try {
      // Call the scraper API endpoint
      const response = await api.post('/scraper/extract', {
        url,
        mode: extractionMode,
        remove_ads: removeAds,
        wait_for_js: waitForJs
      });

      setResult(response.data);
      toast({
        title: "Success",
        description: "Content extracted successfully"
      });
    } catch (error: any) {
      toast({
        title: "Extraction Failed",
        description: error.message || "Failed to extract content from URL",
        variant: "destructive"
      });
    } finally {
      setIsExtracting(false);
    }
  };

  const copyToClipboard = () => {
    if (result?.content) {
      navigator.clipboard.writeText(result.content);
      toast({
        title: "Copied",
        description: "Content copied to clipboard"
      });
    }
  };

  const downloadAsText = () => {
    if (result?.content) {
      const blob = new Blob([result.content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `scraped_content_${Date.now()}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast({
        title: "Downloaded",
        description: "Content downloaded as text file"
      });
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Globe className="w-8 h-8 text-primary" />
          <h2 className="text-2xl font-bold text-foreground">Web Content Scraper</h2>
        </div>
        <p className="text-muted-foreground">
          Extract clean text content from web pages. Handles JavaScript rendering, DOM parsing, and content extraction.
        </p>
      </div>

      {/* Configuration Card */}
      <Card>
        <CardHeader>
          <CardTitle>Extraction Settings</CardTitle>
          <CardDescription>
            Configure how content should be extracted from the web page
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* URL Input */}
          <div className="space-y-2">
            <Label htmlFor="scraper-url">URL to Scrape *</Label>
            <Input
              id="scraper-url"
              type="url"
              placeholder="https://example.com/article"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>

          {/* Extraction Mode */}
          <div className="space-y-2">
            <Label htmlFor="extraction-mode">Content Extraction Mode</Label>
            <Select value={extractionMode} onValueChange={setExtractionMode}>
              <SelectTrigger id="extraction-mode">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="main-content">Main Content Only</SelectItem>
                <SelectItem value="full-page">Full Page Text</SelectItem>
                <SelectItem value="article-body">Article Body</SelectItem>
                <SelectItem value="custom-selector">Custom Selector</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Choose how to identify and extract the main content
            </p>
          </div>

          {/* Options */}
          <div className="space-y-3 pt-2">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="remove-ads"
                checked={removeAds}
                onCheckedChange={(checked) => setRemoveAds(checked as boolean)}
              />
              <Label
                htmlFor="remove-ads"
                className="text-sm font-normal cursor-pointer"
              >
                Remove advertisements and popups
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="wait-js"
                checked={waitForJs}
                onCheckedChange={(checked) => setWaitForJs(checked as boolean)}
              />
              <Label
                htmlFor="wait-js"
                className="text-sm font-normal cursor-pointer"
              >
                Wait for JavaScript to load (slower but more complete)
              </Label>
            </div>
          </div>

          {/* Extract Button */}
          <Button
            onClick={handleExtract}
            disabled={isExtracting || !url}
            className="w-full"
          >
            {isExtracting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Extracting Content...
              </>
            ) : (
              <>
                <Globe className="w-4 h-4 mr-2" />
                Extract Content
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results Card */}
      {result && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Extracted Content</CardTitle>
                <CardDescription>{result.title || result.url}</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={copyToClipboard}>
                  <Copy className="w-4 h-4 mr-2" />
                  Copy
                </Button>
                <Button variant="outline" size="sm" onClick={downloadAsText}>
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Metadata */}
            <div className="grid grid-cols-3 gap-4 p-4 bg-muted rounded-lg">
              <div>
                <p className="text-xs text-muted-foreground">Words</p>
                <p className="text-lg font-semibold">{result.metadata.word_count.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Characters</p>
                <p className="text-lg font-semibold">{result.metadata.char_count.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Extraction Time</p>
                <p className="text-lg font-semibold">{result.metadata.extraction_time.toFixed(2)}s</p>
              </div>
            </div>

            {/* Content */}
            <div className="space-y-2">
              <Label>Content Preview</Label>
              <Textarea
                value={result.content}
                readOnly
                className="min-h-[400px] font-mono text-sm"
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tips Card */}
      <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <CardHeader>
          <CardTitle className="text-blue-900 dark:text-blue-100">💡 Usage Tips</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
          <ul className="list-disc list-inside space-y-1">
            <li>Use "Main Content Only" for articles and blog posts</li>
            <li>Use "Full Page Text" for documentation or reference pages</li>
            <li>Enable "Wait for JavaScript" for dynamic content (React, Vue, etc.)</li>
            <li>Extracted content can be used for TTS, translation, or analysis</li>
            <li>Large pages may take longer to process</li>
          </ul>
        </CardContent>
      </Card>

      {/* Features Card */}
      <Card>
        <CardHeader>
          <CardTitle>Scraper Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <span className="text-green-600 dark:text-green-400">✓</span>
              </div>
              <div>
                <h4 className="font-medium text-sm">JavaScript Rendering</h4>
                <p className="text-xs text-muted-foreground">
                  Handles dynamic content loaded via JavaScript
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <span className="text-green-600 dark:text-green-400">✓</span>
              </div>
              <div>
                <h4 className="font-medium text-sm">Smart Content Detection</h4>
                <p className="text-xs text-muted-foreground">
                  Automatically identifies main content area
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <span className="text-green-600 dark:text-green-400">✓</span>
              </div>
              <div>
                <h4 className="font-medium text-sm">Ad & Popup Removal</h4>
                <p className="text-xs text-muted-foreground">
                  Filters out advertisements and distractions
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                <span className="text-green-600 dark:text-green-400">✓</span>
              </div>
              <div>
                <h4 className="font-medium text-sm">Clean Text Output</h4>
                <p className="text-xs text-muted-foreground">
                  Returns formatted, readable text content
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
