import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { affiliateApi, ReferralLink } from '@/lib/core-api';
import {
  Copy,
  Check,
  ExternalLink,
  Share2,
  Facebook,
  Twitter,
  Linkedin,
  Mail,
  Plus,
  Link2,
  TrendingUp
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui/dialog';

interface ReferralLinkGeneratorProps {
  referralCode: string;
  baseUrl: string;
}

const ReferralLinkGenerator: React.FC<ReferralLinkGeneratorProps> = ({ referralCode, baseUrl }) => {
  const [copied, setCopied] = useState(false);
  const [customLinkDialog, setCustomLinkDialog] = useState(false);
  const [utmSource, setUtmSource] = useState('');
  const [utmCampaign, setUtmCampaign] = useState('');
  const [utmMedium, setUtmMedium] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [referralLinks, setReferralLinks] = useState<ReferralLink[]>([]);
  const [isLoadingLinks, setIsLoadingLinks] = useState(false);
  const { toast } = useToast();

  const fullUrl = `${baseUrl}?ref=${referralCode}`;

  // Fetch existing referral links
  useEffect(() => {
    loadReferralLinks();
  }, []);

  const loadReferralLinks = async () => {
    setIsLoadingLinks(true);
    try {
      const links = await affiliateApi.getReferralLinks();
      setReferralLinks(links);
    } catch (error) {
      console.error('Failed to load referral links:', error);
    } finally {
      setIsLoadingLinks(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      toast({
        title: 'Copied!',
        description: 'Referral link copied to clipboard',
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        title: 'Failed to copy',
        description: 'Please try again',
        variant: 'destructive'
      });
    }
  };

  const createCustomLink = async () => {
    if (!utmSource && !utmCampaign) {
      toast({
        title: 'Missing information',
        description: 'Please provide at least a source or campaign name',
        variant: 'destructive'
      });
      return;
    }

    setIsCreating(true);
    try {
      const newLink = await affiliateApi.createReferralLink({
        utm_source: utmSource || undefined,
        utm_campaign: utmCampaign || undefined,
        utm_medium: utmMedium || undefined
      });

      toast({
        title: 'Link created!',
        description: 'Your custom referral link has been created',
      });

      // Reload links
      await loadReferralLinks();

      // Reset form
      setUtmSource('');
      setUtmCampaign('');
      setUtmMedium('');
      setCustomLinkDialog(false);
    } catch (error) {
      toast({
        title: 'Failed to create link',
        description: error instanceof Error ? error.message : 'Please try again',
        variant: 'destructive'
      });
    } finally {
      setIsCreating(false);
    }
  };

  const shareOnSocial = (platform: string) => {
    const encodedUrl = encodeURIComponent(fullUrl);
    const message = encodeURIComponent('Join me on KasaAI and start building AI voice assistants!');

    const urls = {
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`,
      twitter: `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${message}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`,
      email: `mailto:?subject=Join KasaAI&body=${message}%0A%0A${encodedUrl}`
    };

    window.open(urls[platform as keyof typeof urls], '_blank', 'width=600,height=400');
  };

  const formatConversionRate = (link: ReferralLink) => {
    return link.conversion_rate.toFixed(2) + '%';
  };

  return (
    <div className="space-y-4">
      {/* Primary Referral Link */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link2 className="h-5 w-5 text-blue-600" />
            Your Referral Link
          </CardTitle>
          <CardDescription>
            Share this link to earn commissions when people sign up
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="flex-1">
              <div className="flex items-center gap-2 p-3 bg-gray-100 rounded-lg border">
                <code className="flex-1 text-sm font-mono text-blue-600 truncate">
                  {fullUrl}
                </code>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => copyToClipboard(fullUrl)}
                  className="shrink-0"
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-green-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Label className="text-sm font-medium">Your Referral Code:</Label>
            <Badge variant="default" className="font-mono text-lg">
              {referralCode}
            </Badge>
          </div>

          {/* Social Share Buttons */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Share on social media</Label>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => shareOnSocial('facebook')}
                className="flex items-center gap-2"
              >
                <Facebook className="h-4 w-4" />
                Facebook
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => shareOnSocial('twitter')}
                className="flex items-center gap-2"
              >
                <Twitter className="h-4 w-4" />
                Twitter
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => shareOnSocial('linkedin')}
                className="flex items-center gap-2"
              >
                <Linkedin className="h-4 w-4" />
                LinkedIn
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => shareOnSocial('email')}
                className="flex items-center gap-2"
              >
                <Mail className="h-4 w-4" />
                Email
              </Button>
            </div>
          </div>

          {/* Create Custom Link */}
          <Dialog open={customLinkDialog} onOpenChange={setCustomLinkDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" className="w-full flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Create Custom Tracking Link
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Custom Tracking Link</DialogTitle>
                <DialogDescription>
                  Add UTM parameters to track which campaigns perform best
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="utm_source">Source (e.g., instagram, email)</Label>
                  <Input
                    id="utm_source"
                    value={utmSource}
                    onChange={(e) => setUtmSource(e.target.value)}
                    placeholder="instagram"
                  />
                </div>
                <div>
                  <Label htmlFor="utm_campaign">Campaign (e.g., q1_2025, launch)</Label>
                  <Input
                    id="utm_campaign"
                    value={utmCampaign}
                    onChange={(e) => setUtmCampaign(e.target.value)}
                    placeholder="q1_2025"
                  />
                </div>
                <div>
                  <Label htmlFor="utm_medium">Medium (optional, e.g., social, cpc)</Label>
                  <Input
                    id="utm_medium"
                    value={utmMedium}
                    onChange={(e) => setUtmMedium(e.target.value)}
                    placeholder="social"
                  />
                </div>
                <Button
                  onClick={createCustomLink}
                  disabled={isCreating}
                  className="w-full"
                >
                  {isCreating ? 'Creating...' : 'Create Link'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>

      {/* Custom Links List */}
      {referralLinks.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-green-600" />
              Your Tracking Links ({referralLinks.length})
            </CardTitle>
            <CardDescription>
              Track performance across different channels
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingLinks ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {referralLinks.map((link) => (
                  <div
                    key={link.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
                  >
                    <div className="flex-1 min-w-0">
                      <code className="text-xs font-mono text-blue-600 truncate block">
                        {link.url}
                      </code>
                      <div className="flex items-center gap-2 mt-1">
                        {link.utm_source && (
                          <Badge variant="secondary" className="text-xs">
                            {link.utm_source}
                          </Badge>
                        )}
                        {link.utm_campaign && (
                          <Badge variant="outline" className="text-xs">
                            {link.utm_campaign}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3 ml-4">
                      <div className="text-right">
                        <div className="text-sm font-semibold">
                          {link.click_count} clicks
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {link.conversion_count} conversions ({formatConversionRate(link)})
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => copyToClipboard(link.url)}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ReferralLinkGenerator;
