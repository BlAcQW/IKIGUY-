import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { VoiceTemplate } from './VoiceAgentTemplates';
import { CustomTemplate } from './TemplateCustomization';
import { 
  Share2,
  Users,
  Globe,
  Lock,
  Copy,
  Link,
  Mail,
  MessageSquare,
  Download,
  Star,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  ExternalLink,
  Settings,
  Shield,
  Zap,
  Heart,
  Bookmark,
  Tag,
  Hash,
  Calendar,
  Clock,
  User,
  UserCheck,
  UserX,
  Send,
  Plus,
  Minus,
  Trash2,
  Edit3,
  MoreHorizontal
} from 'lucide-react';

interface SharedTemplate {
  id: string;
  templateId: string;
  templateName: string;
  sharedBy: string;
  sharedWith: string[];
  sharedAt: string;
  expiresAt?: string;
  accessLevel: 'view' | 'edit' | 'admin';
  isPublic: boolean;
  description?: string;
  tags: string[];
  category: string;
  difficulty: string;
  usageCount: number;
  rating: number;
  reviewCount: number;
  isFavorite: boolean;
  permissions: {
    canView: boolean;
    canEdit: boolean;
    canShare: boolean;
    canDelete: boolean;
  };
}

interface ShareSettings {
  accessLevel: 'view' | 'edit' | 'admin';
  expiresAt?: string;
  allowComments: boolean;
  allowRating: boolean;
  allowDownload: boolean;
  requireApproval: boolean;
  notifyOnUse: boolean;
}

interface TemplateSharingProps {
  template: VoiceTemplate | CustomTemplate;
  onClose: () => void;
  onShare?: (sharedTemplate: SharedTemplate) => void;
}

const TemplateSharing: React.FC<TemplateSharingProps> = ({ template, onClose, onShare }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('share');
  const [shareSettings, setShareSettings] = useState<ShareSettings>({
    accessLevel: 'view',
    allowComments: true,
    allowRating: true,
    allowDownload: true,
    requireApproval: false,
    notifyOnUse: true
  });
  const [shareWith, setShareWith] = useState<string>('');
  const [shareMessage, setShareMessage] = useState('');
  const [sharedTemplates, setSharedTemplates] = useState<SharedTemplate[]>([]);
  const [receivedTemplates, setReceivedTemplates] = useState<SharedTemplate[]>([]);
  const [publicTemplates, setPublicTemplates] = useState<SharedTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [showShareLink, setShowShareLink] = useState(false);
  const [shareLink, setShareLink] = useState('');
  const { toast } = useToast();

  // Generate mock shared templates data
  useEffect(() => {
    generateMockData();
  }, []);

  const generateMockData = () => {
    const mockSharedTemplates: SharedTemplate[] = [
      {
        id: '1',
        templateId: template.id,
        templateName: template.name,
        sharedBy: 'john.doe@example.com',
        sharedWith: ['jane.smith@example.com', 'bob.wilson@example.com'],
        sharedAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        accessLevel: 'view',
        isPublic: false,
        description: 'Custom customer service template for e-commerce',
        tags: ['customer-service', 'e-commerce', 'support'],
        category: 'Customer Service',
        difficulty: 'Intermediate',
        usageCount: 45,
        rating: 4.2,
        reviewCount: 12,
        isFavorite: false,
        permissions: {
          canView: true,
          canEdit: false,
          canShare: true,
          canDelete: false
        }
      },
      {
        id: '2',
        templateId: 'template-2',
        templateName: 'Sales Lead Qualification',
        sharedBy: 'sarah.jones@example.com',
        sharedWith: ['john.doe@example.com'],
        sharedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        accessLevel: 'edit',
        isPublic: false,
        description: 'Advanced sales qualification template',
        tags: ['sales', 'lead-qualification', 'b2b'],
        category: 'Sales',
        difficulty: 'Advanced',
        usageCount: 23,
        rating: 4.8,
        reviewCount: 8,
        isFavorite: true,
        permissions: {
          canView: true,
          canEdit: true,
          canShare: true,
          canDelete: false
        }
      }
    ];

    const mockReceivedTemplates: SharedTemplate[] = [
      {
        id: '3',
        templateId: 'template-3',
        templateName: 'Healthcare Appointment Bot',
        sharedBy: 'dr.brown@example.com',
        sharedWith: ['john.doe@example.com'],
        sharedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        accessLevel: 'view',
        isPublic: false,
        description: 'Medical appointment scheduling assistant',
        tags: ['healthcare', 'appointments', 'medical'],
        category: 'Healthcare',
        difficulty: 'Intermediate',
        usageCount: 67,
        rating: 4.5,
        reviewCount: 15,
        isFavorite: false,
        permissions: {
          canView: true,
          canEdit: false,
          canShare: false,
          canDelete: false
        }
      }
    ];

    const mockPublicTemplates: SharedTemplate[] = [
      {
        id: '4',
        templateId: 'template-4',
        templateName: 'Restaurant Reservation Assistant',
        sharedBy: 'chef.martinez@example.com',
        sharedWith: [],
        sharedAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
        accessLevel: 'view',
        isPublic: true,
        description: 'Public template for restaurant reservations',
        tags: ['restaurant', 'reservations', 'hospitality'],
        category: 'Scheduling',
        difficulty: 'Beginner',
        usageCount: 234,
        rating: 4.1,
        reviewCount: 45,
        isFavorite: false,
        permissions: {
          canView: true,
          canEdit: false,
          canShare: true,
          canDelete: false
        }
      }
    ];

    setSharedTemplates(mockSharedTemplates);
    setReceivedTemplates(mockReceivedTemplates);
    setPublicTemplates(mockPublicTemplates);
  };

  const handleShare = async () => {
    if (!shareWith.trim()) {
      toast({
        title: "Error",
        description: "Please enter an email address to share with",
        variant: "destructive"
      });
      return;
    }

    setSharing(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      const newSharedTemplate: SharedTemplate = {
        id: Date.now().toString(),
        templateId: template.id,
        templateName: template.name,
        sharedBy: 'current-user@example.com',
        sharedWith: [shareWith],
        sharedAt: new Date().toISOString(),
        accessLevel: shareSettings.accessLevel,
        isPublic: false,
        description: shareMessage || template.description,
        tags: template.tags,
        category: template.category,
        difficulty: template.difficulty,
        usageCount: 0,
        rating: 0,
        reviewCount: 0,
        isFavorite: false,
        permissions: {
          canView: true,
          canEdit: shareSettings.accessLevel === 'edit' || shareSettings.accessLevel === 'admin',
          canShare: true,
          canDelete: false
        }
      };

      setSharedTemplates(prev => [newSharedTemplate, ...prev]);
      setShareWith('');
      setShareMessage('');

      toast({
        title: "Template Shared",
        description: `Template shared successfully with ${shareWith}`,
      });

      if (onShare) {
        onShare(newSharedTemplate);
      }
    } catch (error) {
      toast({
        title: "Share Failed",
        description: "Failed to share template. Please try again.",
        variant: "destructive"
      });
    } finally {
      setSharing(false);
    }
  };

  const generateShareLink = () => {
    const link = `${window.location.origin}/templates/shared/${template.id}?access=${shareSettings.accessLevel}`;
    setShareLink(link);
    setShowShareLink(true);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast({
        title: "Copied",
        description: "Link copied to clipboard",
      });
    } catch (error) {
      toast({
        title: "Copy Failed",
        description: "Failed to copy link to clipboard",
        variant: "destructive"
      });
    }
  };

  const makePublic = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));

      const publicTemplate: SharedTemplate = {
        id: Date.now().toString(),
        templateId: template.id,
        templateName: template.name,
        sharedBy: 'current-user@example.com',
        sharedWith: [],
        sharedAt: new Date().toISOString(),
        accessLevel: 'view',
        isPublic: true,
        description: template.description,
        tags: template.tags,
        category: template.category,
        difficulty: template.difficulty,
        usageCount: 0,
        rating: 0,
        reviewCount: 0,
        isFavorite: false,
        permissions: {
          canView: true,
          canEdit: false,
          canShare: true,
          canDelete: true
        }
      };

      setPublicTemplates(prev => [publicTemplate, ...prev]);

      toast({
        title: "Template Made Public",
        description: "Template is now available to all users",
      });
    } catch (error) {
      toast({
        title: "Failed",
        description: "Failed to make template public",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const renderShareTab = () => (
    <div className="space-y-6">
      {/* Share with specific users */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Share with Users
          </CardTitle>
          <CardDescription>
            Share this template with specific users by email address
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="share-email">Email Address</Label>
            <Input
              id="share-email"
              type="email"
              placeholder="Enter email address"
              value={shareWith}
              onChange={(e) => setShareWith(e.target.value)}
            />
          </div>

          <div>
            <Label htmlFor="share-message">Message (Optional)</Label>
            <Textarea
              id="share-message"
              placeholder="Add a personal message..."
              value={shareMessage}
              onChange={(e) => setShareMessage(e.target.value)}
              rows={3}
            />
          </div>

          <div>
            <Label htmlFor="access-level">Access Level</Label>
            <Select
              value={shareSettings.accessLevel}
              onValueChange={(value) => setShareSettings(prev => ({ ...prev, accessLevel: value as any }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="view">View Only</SelectItem>
                <SelectItem value="edit">Can Edit</SelectItem>
                <SelectItem value="admin">Admin Access</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button onClick={handleShare} disabled={sharing || !shareWith.trim()}>
            {sharing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Sharing...
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Share Template
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Generate share link */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link className="h-5 w-5" />
            Generate Share Link
          </CardTitle>
          <CardDescription>
            Create a shareable link for this template
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="link-access-level">Access Level</Label>
            <Select
              value={shareSettings.accessLevel}
              onValueChange={(value) => setShareSettings(prev => ({ ...prev, accessLevel: value as any }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="view">View Only</SelectItem>
                <SelectItem value="edit">Can Edit</SelectItem>
                <SelectItem value="admin">Admin Access</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button onClick={generateShareLink} variant="outline">
            <Link className="h-4 w-4 mr-2" />
            Generate Link
          </Button>

          {showShareLink && (
            <div className="space-y-2">
              <Label>Share Link</Label>
              <div className="flex gap-2">
                <Input value={shareLink} readOnly />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => copyToClipboard(shareLink)}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Make public */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Make Public
          </CardTitle>
          <CardDescription>
            Make this template available to all users in the community
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={makePublic} disabled={loading} variant="outline">
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Making Public...
              </>
            ) : (
              <>
                <Globe className="h-4 w-4 mr-2" />
                Make Template Public
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  const renderSharedTab = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Templates You've Shared</h3>
        <Badge variant="outline">{sharedTemplates.length} shared</Badge>
      </div>

      <div className="space-y-3">
        {sharedTemplates.map((shared) => (
          <Card key={shared.id} className="hover:bg-muted/50 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium">{shared.templateName}</h4>
                    <Badge variant="outline">{shared.category}</Badge>
                    <Badge className={shared.isPublic ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}>
                      {shared.isPublic ? 'Public' : 'Private'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {shared.description}
                  </p>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>Shared with {shared.sharedWith.length} users</span>
                    <span>• {new Date(shared.sharedAt).toLocaleDateString()}</span>
                    <span>• {shared.accessLevel} access</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm">
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Edit3 className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderReceivedTab = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Templates Shared with You</h3>
        <Badge variant="outline">{receivedTemplates.length} received</Badge>
      </div>

      <div className="space-y-3">
        {receivedTemplates.map((received) => (
          <Card key={received.id} className="hover:bg-muted/50 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium">{received.templateName}</h4>
                    <Badge variant="outline">{received.category}</Badge>
                    <Badge className="bg-purple-100 text-purple-800">
                      {received.accessLevel} access
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {received.description}
                  </p>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>Shared by {received.sharedBy}</span>
                    <span>• {new Date(received.sharedAt).toLocaleDateString()}</span>
                    <span>• {received.usageCount} uses</span>
                    <span>• ⭐ {received.rating.toFixed(1)} ({received.reviewCount})</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm">
                    <Eye className="h-4 w-4" />
                  </Button>
                  {received.permissions.canEdit && (
                    <Button variant="ghost" size="sm">
                      <Edit3 className="h-4 w-4" />
                    </Button>
                  )}
                  <Button variant="ghost" size="sm">
                    <Heart className={`h-4 w-4 ${received.isFavorite ? 'fill-current text-red-500' : ''}`} />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderPublicTab = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Public Templates</h3>
        <Badge variant="outline">{publicTemplates.length} available</Badge>
      </div>

      <div className="space-y-3">
        {publicTemplates.map((publicTemplate) => (
          <Card key={publicTemplate.id} className="hover:bg-muted/50 transition-colors">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-medium">{publicTemplate.templateName}</h4>
                    <Badge variant="outline">{publicTemplate.category}</Badge>
                    <Badge className="bg-green-100 text-green-800">Public</Badge>
                    <Badge className={publicTemplate.difficulty === 'Beginner' ? 'bg-green-100 text-green-800' : 
                                     publicTemplate.difficulty === 'Intermediate' ? 'bg-yellow-100 text-yellow-800' : 
                                     'bg-red-100 text-red-800'}>
                      {publicTemplate.difficulty}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {publicTemplate.description}
                  </p>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>By {publicTemplate.sharedBy}</span>
                    <span>• {publicTemplate.usageCount} uses</span>
                    <span>• ⭐ {publicTemplate.rating.toFixed(1)} ({publicTemplate.reviewCount})</span>
                    <span>• {new Date(publicTemplate.sharedAt).toLocaleDateString()}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {publicTemplate.tags.slice(0, 3).map((tag, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        #{tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm">
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Heart className={`h-4 w-4 ${publicTemplate.isFavorite ? 'fill-current text-red-500' : ''}`} />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Share Template: {template.name}</DialogTitle>
          <DialogDescription>
            Share this template with other users or make it public
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="share">Share</TabsTrigger>
            <TabsTrigger value="shared">Shared</TabsTrigger>
            <TabsTrigger value="received">Received</TabsTrigger>
            <TabsTrigger value="public">Public</TabsTrigger>
          </TabsList>

          <TabsContent value="share" className="space-y-6">
            {renderShareTab()}
          </TabsContent>

          <TabsContent value="shared" className="space-y-6">
            {renderSharedTab()}
          </TabsContent>

          <TabsContent value="received" className="space-y-6">
            {renderReceivedTab()}
          </TabsContent>

          <TabsContent value="public" className="space-y-6">
            {renderPublicTab()}
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TemplateSharing;
