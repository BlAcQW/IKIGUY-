import React, { useState, useMemo } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  HelpCircle, 
  Search, 
  ExternalLink, 
  BookOpen, 
  Clock, 
  X,
  ArrowLeft,
  ArrowRight
} from 'lucide-react';
import { HelpContent, getHelpContent, searchHelpContent, getHelpContentKeys } from '@/lib/help-content';

interface HelpModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialContent?: HelpContent;
  initialKey?: string;
  recentHelp?: string[];
  onHelpClick?: (key: string) => void;
}

export const HelpModal: React.FC<HelpModalProps> = ({
  isOpen,
  onClose,
  initialContent,
  initialKey,
  recentHelp = [],
  onHelpClick
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentContent, setCurrentContent] = useState<HelpContent | null>(initialContent || null);
  const [activeTab, setActiveTab] = useState('content');

  // Get all help content for browsing
  const allHelpContent = useMemo(() => {
    return getHelpContentKeys().map(key => ({
      key,
      content: getHelpContent(key)!
    }));
  }, []);

  // Search results
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    return searchHelpContent(searchQuery);
  }, [searchQuery]);

  // Recent help content
  const recentHelpContent = useMemo(() => {
    return recentHelp
      .map(key => ({ key, content: getHelpContent(key) }))
      .filter(item => item.content !== null) as Array<{ key: string; content: HelpContent }>;
  }, [recentHelp]);

  const handleContentClick = (content: HelpContent, key?: string) => {
    setCurrentContent(content);
    setActiveTab('content');
    if (key && onHelpClick) {
      onHelpClick(key);
    }
  };

  const handleSearchResultClick = (content: HelpContent) => {
    handleContentClick(content);
    setSearchQuery('');
  };

  const handleRecentClick = (key: string, content: HelpContent) => {
    handleContentClick(content, key);
  };

  const handleClose = () => {
    setCurrentContent(null);
    setSearchQuery('');
    setActiveTab('content');
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <HelpCircle className="h-5 w-5" />
            Help & Documentation
          </DialogTitle>
        </DialogHeader>

        <div className="flex h-full gap-4">
          {/* Sidebar */}
          <div className="w-80 border-r pr-4">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="content">Content</TabsTrigger>
                <TabsTrigger value="search">Search</TabsTrigger>
                <TabsTrigger value="recent">Recent</TabsTrigger>
              </TabsList>

              <TabsContent value="content" className="mt-4 h-[calc(100vh-200px)]">
                <ScrollArea className="h-full">
                  <div className="space-y-2">
                    {allHelpContent.map(({ key, content }) => (
                      <Button
                        key={key}
                        variant={currentContent?.title === content.title ? "secondary" : "ghost"}
                        className="w-full justify-start text-left h-auto p-3"
                        onClick={() => handleContentClick(content, key)}
                      >
                        <div className="space-y-1">
                          <div className="font-medium text-sm">{content.title}</div>
                          <div className="text-xs text-gray-600 line-clamp-2">
                            {content.description}
                          </div>
                        </div>
                      </Button>
                    ))}
                  </div>
                </ScrollArea>
              </TabsContent>

              <TabsContent value="search" className="mt-4 h-[calc(100vh-200px)]">
                <div className="space-y-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
                    <Input
                      placeholder="Search help content..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>

                  <ScrollArea className="h-[calc(100vh-280px)]">
                    <div className="space-y-2">
                      {searchResults.map((content, index) => (
                        <Button
                          key={index}
                          variant="ghost"
                          className="w-full justify-start text-left h-auto p-3"
                          onClick={() => handleSearchResultClick(content)}
                        >
                          <div className="space-y-1">
                            <div className="font-medium text-sm">{content.title}</div>
                            <div className="text-xs text-gray-600 line-clamp-2">
                              {content.description}
                            </div>
                          </div>
                        </Button>
                      ))}
                      {searchQuery && searchResults.length === 0 && (
                        <div className="text-center text-gray-600 py-8">
                          No results found for "{searchQuery}"
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </div>
              </TabsContent>

              <TabsContent value="recent" className="mt-4 h-[calc(100vh-200px)]">
                <ScrollArea className="h-full">
                  <div className="space-y-2">
                    {recentHelpContent.length > 0 ? (
                      recentHelpContent.map(({ key, content }) => (
                        <Button
                          key={key}
                          variant="ghost"
                          className="w-full justify-start text-left h-auto p-3"
                          onClick={() => handleRecentClick(key, content)}
                        >
                          <div className="space-y-1">
                            <div className="font-medium text-sm">{content.title}</div>
                            <div className="text-xs text-gray-600 line-clamp-2">
                              {content.description}
                            </div>
                          </div>
                        </Button>
                      ))
                    ) : (
                      <div className="text-center text-gray-600 py-8">
                        No recent help topics
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {currentContent ? (
              <ScrollArea className="h-[calc(100vh-200px)]">
                <div className="space-y-6">
                  {/* Header */}
                  <div>
                    <h2 className="text-xl font-semibold">{currentContent.title}</h2>
                    <p className="text-gray-600 mt-1">{currentContent.description}</p>
                  </div>

                  {/* Details */}
                  {currentContent.details && (
                    <div>
                      <h3 className="font-medium mb-2">Details</h3>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {currentContent.details}
                      </p>
                    </div>
                  )}

                  {/* Examples */}
                  {currentContent.examples && currentContent.examples.length > 0 && (
                    <div>
                      <h3 className="font-medium mb-3">Examples</h3>
                      <div className="space-y-2">
                        {currentContent.examples.map((example, index) => (
                          <div key={index} className="bg-muted p-3 rounded-md">
                            <code className="text-sm">{example}</code>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Related Resources */}
                  {currentContent.links && currentContent.links.length > 0 && (
                    <div>
                      <h3 className="font-medium mb-3">Related Resources</h3>
                      <div className="space-y-2">
                        {currentContent.links.map((link, index) => (
                          <a
                            key={index}
                            href={link.url}
                            target={link.external ? '_blank' : undefined}
                            rel={link.external ? 'noopener noreferrer' : undefined}
                            className="flex items-center gap-2 text-sm text-indigo-600 hover:underline p-2 rounded-md hover:bg-muted transition-colors"
                          >
                            <ExternalLink className="h-3 w-3" />
                            {link.label}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Related Topics */}
                  {currentContent.relatedTopics && currentContent.relatedTopics.length > 0 && (
                    <div>
                      <h3 className="font-medium mb-3">Related Topics</h3>
                      <div className="flex flex-wrap gap-2">
                        {currentContent.relatedTopics.map((topic, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
            ) : (
              <div className="flex items-center justify-center h-[calc(100vh-200px)]">
                <div className="text-center text-gray-600">
                  <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Select a help topic from the sidebar</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
