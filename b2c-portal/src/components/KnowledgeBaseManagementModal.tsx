/**
 * Knowledge Base Management Modal
 * Allows linking and unlinking knowledge base collections to automations
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { Database, Loader2, X, Plus, CheckCircle } from 'lucide-react';
import { getAuthHeaders } from '@/lib/auth-utils';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://flow-api.ailabsafrica.com';

interface Collection {
  name: string;
  display_name: string;
  document_count: number;
}

interface KnowledgeBaseManagementModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  automationId: string;
  automationName: string;
}

const KnowledgeBaseManagementModal: React.FC<KnowledgeBaseManagementModalProps> = ({
  open,
  onOpenChange,
  automationId,
  automationName,
}) => {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [linkedCollections, setLinkedCollections] = useState<string[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [isLinking, setIsLinking] = useState(false);
  const [isUnlinking, setIsUnlinking] = useState<string | null>(null);

  // Fetch available collections and linked collections
  useEffect(() => {
    if (open) {
      fetchData();
    }
  }, [open, automationId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch all available collections
      const collectionsResponse = await fetch(`${API_BASE_URL}/knowledge-base/collections`);
      if (!collectionsResponse.ok) throw new Error('Failed to fetch collections');
      const collectionsData = await collectionsResponse.json();
      setCollections(collectionsData.collections || []);

      // Fetch linked collections for this automation
      const linkedResponse = await fetch(
        `${API_BASE_URL}/automation-configs/${automationId}/knowledge-bases`,
        {
          headers: await getAuthHeaders(),
        }
      );
      if (!linkedResponse.ok) throw new Error('Failed to fetch linked collections');
      const linkedData = await linkedResponse.json();
      setLinkedCollections(linkedData.knowledge_bases || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast({
        title: 'Failed to Load Data',
        description: error instanceof Error ? error.message : 'Could not fetch knowledge base data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLinkCollection = async () => {
    if (!selectedCollection) return;

    setIsLinking(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/automation-configs/${automationId}/knowledge-bases`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(await getAuthHeaders()),
          },
          body: JSON.stringify({
            collection_name: selectedCollection,
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to link collection');

      const data = await response.json();

      toast({
        title: 'Collection Linked',
        description: `Successfully linked ${getCollectionDisplayName(selectedCollection)} to ${automationName}`,
      });

      // Refresh linked collections
      await fetchData();
      setSelectedCollection('');
    } catch (error) {
      console.error('Error linking collection:', error);
      toast({
        title: 'Failed to Link Collection',
        description: error instanceof Error ? error.message : 'Could not link knowledge base',
        variant: 'destructive',
      });
    } finally {
      setIsLinking(false);
    }
  };

  const handleUnlinkCollection = async (collectionName: string) => {
    setIsUnlinking(collectionName);
    try {
      const response = await fetch(
        `${API_BASE_URL}/automation-configs/${automationId}/knowledge-bases/${encodeURIComponent(collectionName)}`,
        {
          method: 'DELETE',
          headers: await getAuthHeaders(),
        }
      );

      if (!response.ok) throw new Error('Failed to unlink collection');

      toast({
        title: 'Collection Unlinked',
        description: `Removed ${getCollectionDisplayName(collectionName)} from ${automationName}`,
      });

      // Refresh linked collections
      await fetchData();
    } catch (error) {
      console.error('Error unlinking collection:', error);
      toast({
        title: 'Failed to Unlink Collection',
        description: error instanceof Error ? error.message : 'Could not unlink knowledge base',
        variant: 'destructive',
      });
    } finally {
      setIsUnlinking(null);
    }
  };

  const getCollectionDisplayName = (collectionName: string) => {
    const collection = collections.find((c) => c.name === collectionName);
    return collection?.display_name || collectionName.replace('helpdesk_', '').replace(/_/g, ' ');
  };

  const availableCollections = collections.filter(
    (c) => !linkedCollections.includes(c.name)
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Database className="h-5 w-5 text-blue-600" />
            Manage Knowledge Bases
          </DialogTitle>
          <DialogDescription>
            Link knowledge base collections to "{automationName}" for enhanced AI responses
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Linked Collections */}
            <div>
              <Label className="text-sm font-medium mb-2 block">Linked Collections</Label>
              {linkedCollections.length === 0 ? (
                <div className="text-sm text-gray-500 py-4 text-center border-2 border-dashed rounded-lg">
                  No knowledge bases linked yet
                </div>
              ) : (
                <div className="space-y-2">
                  {linkedCollections.map((collectionName) => {
                    const collection = collections.find((c) => c.name === collectionName);
                    return (
                      <div
                        key={collectionName}
                        className="flex items-center justify-between p-3 border rounded-lg bg-green-50 border-green-200"
                      >
                        <div className="flex items-center gap-3">
                          <CheckCircle className="h-5 w-5 text-green-600" />
                          <div>
                            <p className="font-medium text-sm">{getCollectionDisplayName(collectionName)}</p>
                            {collection && (
                              <p className="text-xs text-gray-500">
                                {collection.document_count} documents
                              </p>
                            )}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleUnlinkCollection(collectionName)}
                          disabled={isUnlinking === collectionName}
                        >
                          {isUnlinking === collectionName ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <X className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Add New Collection */}
            <div>
              <Label className="text-sm font-medium mb-2 block">Add Knowledge Base</Label>
              <div className="flex gap-2">
                <Select
                  value={selectedCollection}
                  onValueChange={setSelectedCollection}
                  disabled={availableCollections.length === 0}
                >
                  <SelectTrigger className="flex-1">
                    <SelectValue
                      placeholder={
                        availableCollections.length === 0
                          ? 'All collections linked'
                          : 'Select a collection...'
                      }
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {availableCollections.map((collection) => (
                      <SelectItem key={collection.name} value={collection.name}>
                        <div className="flex items-center justify-between w-full">
                          <span>{collection.display_name}</span>
                          <Badge variant="secondary" className="ml-2">
                            {collection.document_count} docs
                          </Badge>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  onClick={handleLinkCollection}
                  disabled={!selectedCollection || isLinking}
                  size="icon"
                >
                  {isLinking ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default KnowledgeBaseManagementModal;
