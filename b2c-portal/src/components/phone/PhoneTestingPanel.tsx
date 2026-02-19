/**
 * Phone Testing Panel Component
 * Generate test phone numbers and shareable UI links
 * Uses FastRTC .fastphone() and .ui.launch() features
 * Widget-style UI following Vapi's pattern
 */

import React, { useState } from 'react';
import { Phone, ExternalLink, Copy, Check, AlertCircle, Loader2, Zap, Link as LinkIcon } from 'lucide-react';
import { generateTestPhone, launchShareableUI } from '@/lib/phone-api-client';
import { useToast } from '@/hooks/use-toast';

interface PhoneTestingPanelProps {
  assistantId: string;
  assistantName: string;
}

export const PhoneTestingPanel: React.FC<PhoneTestingPanelProps> = ({
  assistantId,
  assistantName
}) => {
  const { toast } = useToast();

  // Phone testing state
  const [testPhone, setTestPhone] = useState<{
    number: string;
    country: string;
    expires_at: string;
  } | null>(null);
  const [isGeneratingPhone, setIsGeneratingPhone] = useState(false);
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [copiedPhone, setCopiedPhone] = useState(false);

  // UI testing state
  const [shareableLink, setShareableLink] = useState<{
    url: string;
    expires_in_hours: number | null;
  } | null>(null);
  const [isLaunchingUI, setIsLaunchingUI] = useState(false);
  const [uiError, setUiError] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  const handleGeneratePhone = async () => {
    setIsGeneratingPhone(true);
    setPhoneError(null);

    try {
      const result = await generateTestPhone({
        assistant_id: assistantId,
        ui_title: `Test ${assistantName}`,
        ui_subtitle: 'Call to test this assistant'
      });

      setTestPhone({
        number: result.number,
        country: result.country,
        expires_at: result.expires_at
      });

      toast({
        title: 'Test phone generated',
        description: `Call ${result.number} to test your assistant`
      });
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to generate test phone';
      setPhoneError(errorMessage);
      toast({
        title: 'Generation failed',
        description: errorMessage,
        variant: 'destructive'
      });
    } finally {
      setIsGeneratingPhone(false);
    }
  };

  const handleLaunchUI = async () => {
    setIsLaunchingUI(true);
    setUiError(null);

    try {
      const result = await launchShareableUI({
        assistant_id: assistantId,
        ui_title: `Test ${assistantName}`,
        ui_subtitle: 'Click Start to test this assistant',
        share: true
      });

      setShareableLink({
        url: result.url,
        expires_in_hours: result.expires_in_hours || null
      });

      toast({
        title: 'Shareable link created',
        description: 'Share this link to test your assistant'
      });
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to launch UI';
      setUiError(errorMessage);
      toast({
        title: 'Launch failed',
        description: errorMessage,
        variant: 'destructive'
      });
    } finally {
      setIsLaunchingUI(false);
    }
  };

  const copyToClipboard = (text: string, type: 'phone' | 'link') => {
    navigator.clipboard.writeText(text);

    if (type === 'phone') {
      setCopiedPhone(true);
      setTimeout(() => setCopiedPhone(false), 2000);
    } else {
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    }

    toast({
      title: 'Copied',
      description: `${type === 'phone' ? 'Phone number' : 'Link'} copied to clipboard`
    });
  };

  const formatExpiresAt = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) {
      return `Expires in ${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `Expires in ${minutes} minutes`;
    } else {
      return 'Expired';
    }
  };

  return (
    <div className="space-y-6">
      {/* Test Phone Number Section */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-border bg-muted/30">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Phone className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h3 className="text-base font-semibold">Test Phone Number</h3>
              <p className="text-xs text-muted-foreground">Generate a temporary number to call and test</p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {!testPhone ? (
            <>
              <p className="text-sm text-muted-foreground">
                Generate a free temporary phone number powered by HuggingFace.
                Perfect for quick testing without setting up Twilio or Vonage.
              </p>

              {phoneError && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-destructive">{phoneError}</p>
                </div>
              )}

              <button
                onClick={handleGeneratePhone}
                disabled={isGeneratingPhone}
                className="w-full px-4 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {isGeneratingPhone ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4" />
                    Generate Test Phone
                  </>
                )}
              </button>

              <div className="p-3 bg-primary/10 border border-primary/20 rounded-lg">
                <p className="text-xs text-primary">
                  <strong>Note:</strong> Numbers expire after a few hours and are only for testing.
                  For production, use the Phone Numbers page to provision permanent numbers.
                </p>
              </div>
            </>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-green-700 dark:text-green-400">Active Test Number</span>
                  <span className="text-xs text-green-600 dark:text-green-500">
                    {formatExpiresAt(testPhone.expires_at)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-2xl font-bold text-foreground">{testPhone.number}</p>
                    <p className="text-xs text-muted-foreground mt-1">{testPhone.country}</p>
                  </div>
                  <button
                    onClick={() => copyToClipboard(testPhone.number, 'phone')}
                    className="p-2 hover:bg-accent rounded-md transition-colors"
                  >
                    {copiedPhone ? (
                      <Check className="h-5 w-5 text-green-500" />
                    ) : (
                      <Copy className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleGeneratePhone}
                  disabled={isGeneratingPhone}
                  className="flex-1 px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors text-sm"
                >
                  Generate New
                </button>
                <button
                  onClick={() => setTestPhone(null)}
                  className="px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors text-sm"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Shareable UI Link Section */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-border bg-muted/30">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <LinkIcon className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h3 className="text-base font-semibold">Shareable Testing Link</h3>
              <p className="text-xs text-muted-foreground">Create a public link for browser testing</p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {!shareableLink ? (
            <>
              <p className="text-sm text-muted-foreground">
                Launch a shareable Gradio UI that anyone can use to test your assistant.
                Perfect for sharing with team members or clients.
              </p>

              {uiError && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-destructive">{uiError}</p>
                </div>
              )}

              <button
                onClick={handleLaunchUI}
                disabled={isLaunchingUI}
                className="w-full px-4 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {isLaunchingUI ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Launching...
                  </>
                ) : (
                  <>
                    <ExternalLink className="h-4 w-4" />
                    Launch Shareable UI
                  </>
                )}
              </button>

              <div className="p-3 bg-primary/10 border border-primary/20 rounded-lg">
                <p className="text-xs text-primary">
                  <strong>Note:</strong> Links expire in 72 hours. No authentication required.
                  Anyone with the link can test your assistant.
                </p>
              </div>
            </>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-blue-700 dark:text-blue-400">Active Link</span>
                  {shareableLink.expires_in_hours && (
                    <span className="text-xs text-blue-600 dark:text-blue-500">
                      Expires in {shareableLink.expires_in_hours} hours
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={shareableLink.url}
                    readOnly
                    className="flex-1 px-3 py-2 bg-background border border-border rounded-md text-sm"
                  />
                  <button
                    onClick={() => copyToClipboard(shareableLink.url, 'link')}
                    className="p-2 hover:bg-accent rounded-md transition-colors"
                  >
                    {copiedLink ? (
                      <Check className="h-5 w-5 text-green-500" />
                    ) : (
                      <Copy className="h-5 w-5" />
                    )}
                  </button>
                  <a
                    href={shareableLink.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 hover:bg-accent rounded-md transition-colors"
                  >
                    <ExternalLink className="h-5 w-5" />
                  </a>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleLaunchUI}
                  disabled={isLaunchingUI}
                  className="flex-1 px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors text-sm"
                >
                  Generate New
                </button>
                <button
                  onClick={() => setShareableLink(null)}
                  className="px-4 py-2 border border-border rounded-md hover:bg-accent transition-colors text-sm"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
