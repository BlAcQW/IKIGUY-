/**
 * CollectionSidebar Component
 * Left sidebar for quick collection switching with search and statistics
 */

import React, { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import {
  Search,
  Plus,
  Database,
  FileText,
  Settings,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Collection {
  collection_id: string;
  name: string;
  company_name: string;
  display_name: string;
  description?: string;
  industry?: string;
  document_count: number;
  total_chunks: number;
  total_size_bytes: number;
  created_at?: string;
  last_updated?: string;
  total_queries: number;
  avg_confidence?: number;
}

interface CollectionSidebarProps {
  apiBaseUrl: string;
  selectedCollection: string;
  onSelectCollection: (companyName: string) => void;
  onManageCollections: () => void;
  onCreateCollection: () => void;
}

const CollectionSidebar: React.FC<CollectionSidebarProps> = ({
  apiBaseUrl,
  selectedCollection,
  onSelectCollection,
  onManageCollections,
  onCreateCollection,
}) => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [filteredCollections, setFilteredCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Fetch collections
  useEffect(() => {
    const fetchCollections = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/knowledge-base/collections`);
        const data = await response.json();

        if (data.success) {
          setCollections(data.collections || []);
          setFilteredCollections(data.collections || []);
        }
      } catch (error) {
        console.error('Error fetching collections:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCollections();
  }, [apiBaseUrl]);

  // Filter collections based on search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredCollections(collections);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = collections.filter(
        (c) =>
          c.display_name.toLowerCase().includes(query) ||
          c.company_name.toLowerCase().includes(query) ||
          c.description?.toLowerCase().includes(query) ||
          c.industry?.toLowerCase().includes(query)
      );
      setFilteredCollections(filtered);
    }
  }, [searchQuery, collections]);

  // Format file size
  const formatSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  // Format number with commas
  const formatNumber = (num: number): string => {
    return num.toLocaleString();
  };

  if (isCollapsed) {
    return (
      <div className="w-16 bg-sidebar border-r border-sidebar-border flex flex-col items-center py-4 space-y-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(false)}
          className="text-sidebar-foreground hover:bg-sidebar-accent"
        >
          <Database className="h-5 w-5" />
        </Button>
        <div className="flex-1" />
        <Button
          variant="ghost"
          size="icon"
          onClick={onCreateCollection}
          className="text-sidebar-foreground hover:bg-sidebar-accent"
          title="Create Collection"
        >
          <Plus className="h-5 w-5" />
        </Button>
      </div>
    );
  }

  return (
    <div className="w-72 bg-sidebar border-r border-sidebar-border flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-sidebar-border">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-sidebar-foreground" />
            <h3 className="font-semibold text-sidebar-foreground">Collections</h3>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onCreateCollection}
            className="h-8 w-8 text-sidebar-foreground hover:bg-sidebar-accent"
            title="Create Collection"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-sidebar-foreground/50" />
          <Input
            placeholder="Search collections..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 bg-sidebar-accent/50 border-sidebar-border text-sidebar-foreground placeholder:text-sidebar-foreground/50"
          />
        </div>
      </div>

      {/* Collections List */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-sidebar-foreground/50" />
          </div>
        ) : filteredCollections.length === 0 ? (
          <div className="text-center py-12 px-4">
            <Database className="h-12 w-12 text-sidebar-foreground/30 mx-auto mb-3" />
            <p className="text-sm text-sidebar-foreground/70 font-medium">
              {searchQuery ? 'No collections found' : 'No collections yet'}
            </p>
            <p className="text-xs text-sidebar-foreground/50 mt-1">
              {searchQuery ? 'Try a different search' : 'Create your first collection'}
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredCollections.map((collection) => {
              const isSelected = collection.company_name === selectedCollection.replace('helpdesk_', '');

              return (
                <Card
                  key={collection.collection_id}
                  className={cn(
                    'p-3 cursor-pointer transition-all hover:bg-sidebar-accent/80 border-sidebar-border',
                    isSelected && 'bg-sidebar-accent border-l-4 border-l-primary'
                  )}
                  onClick={() => onSelectCollection(collection.company_name)}
                >
                  <div className="space-y-2">
                    {/* Collection Name */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <h4 className={cn(
                          'text-sm font-semibold truncate',
                          isSelected ? 'text-primary' : 'text-sidebar-foreground'
                        )}>
                          {collection.display_name}
                        </h4>
                        {collection.industry && (
                          <p className="text-xs text-sidebar-foreground/60 truncate">
                            {collection.industry}
                          </p>
                        )}
                      </div>
                      {isSelected && (
                        <ChevronRight className="h-4 w-4 text-indigo-600 flex-shrink-0 mt-0.5" />
                      )}
                    </div>

                    {/* Stats */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        variant="secondary"
                        className="text-xs bg-sidebar-accent/80 text-sidebar-foreground/70 border-sidebar-border"
                      >
                        <FileText className="h-3 w-3 mr-1" />
                        {formatNumber(collection.document_count)}
                      </Badge>

                      {collection.total_chunks > 0 && (
                        <Badge
                          variant="secondary"
                          className="text-xs bg-sidebar-accent/80 text-sidebar-foreground/70 border-sidebar-border"
                        >
                          {formatNumber(collection.total_chunks)} chunks
                        </Badge>
                      )}
                    </div>

                    {/* Description */}
                    {collection.description && (
                      <p className="text-xs text-sidebar-foreground/60 line-clamp-2">
                        {collection.description}
                      </p>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-sidebar-border">
        <Button
          variant="outline"
          size="sm"
          onClick={onManageCollections}
          className="w-full justify-start text-sidebar-foreground border-sidebar-border hover:bg-sidebar-accent"
        >
          <Settings className="h-4 w-4 mr-2" />
          Manage Collections
        </Button>

        <div className="mt-2 text-xs text-sidebar-foreground/60 text-center">
          {collections.length} collection{collections.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
};

export default CollectionSidebar;
