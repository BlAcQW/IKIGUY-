import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Keyboard, X } from 'lucide-react';

interface Shortcut {
  key: string;
  description: string;
  category: string;
}

const shortcuts: Shortcut[] = [
  { key: 'Alt + 1', description: 'Go to Home page', category: 'Navigation' },
  { key: 'Alt + 2', description: 'Go to Demos page', category: 'Navigation' },
  { key: 'Alt + 3', description: 'Go to Contact page', category: 'Navigation' },
  { key: 'Alt + 4', description: 'Go to Create Assistant page', category: 'Navigation' },
  { key: 'Alt + H', description: 'Show keyboard shortcuts help', category: 'Help' },
  { key: 'Tab', description: 'Navigate between interactive elements', category: 'Navigation' },
  { key: 'Shift + Tab', description: 'Navigate backwards between elements', category: 'Navigation' },
  { key: 'Enter', description: 'Activate buttons and links', category: 'Interaction' },
  { key: 'Space', description: 'Activate buttons and checkboxes', category: 'Interaction' },
  { key: 'Escape', description: 'Close dialogs and menus', category: 'Interaction' },
];

const KeyboardShortcutsHelp: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string>('All');

  const categories = ['All', ...Array.from(new Set(shortcuts.map(s => s.category)))];

  const filteredShortcuts = activeCategory === 'All' 
    ? shortcuts 
    : shortcuts.filter(s => s.category === activeCategory);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.altKey && event.key === 'h') {
        event.preventDefault();
        setIsOpen(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
          aria-label="Show keyboard shortcuts help"
        >
          <Keyboard className="h-4 w-4" />
          <span className="hidden sm:inline">Shortcuts</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Keyboard className="h-5 w-5" />
            Keyboard Shortcuts
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Category Filter */}
          <div className="flex flex-wrap gap-2">
            {categories.map(category => (
              <Badge
                key={category}
                variant={activeCategory === category ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => setActiveCategory(category)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setActiveCategory(category);
                  }
                }}
              >
                {category}
              </Badge>
            ))}
          </div>

          {/* Shortcuts List */}
          <div className="space-y-3">
            {filteredShortcuts.map((shortcut, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <kbd className="px-2 py-1 text-sm font-mono bg-muted border rounded">
                    {shortcut.key}
                  </kbd>
                  <span className="text-sm">{shortcut.description}</span>
                </div>
                <Badge variant="secondary" className="text-xs">
                  {shortcut.category}
                </Badge>
              </div>
            ))}
          </div>

          {/* Accessibility Note */}
          <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
            <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
              Accessibility Features
            </h4>
            <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
              <li>• All interactive elements are keyboard accessible</li>
              <li>• Screen reader announcements for important actions</li>
              <li>• High contrast mode support</li>
              <li>• Focus indicators for all interactive elements</li>
              <li>• Semantic HTML structure for better navigation</li>
            </ul>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default KeyboardShortcutsHelp;
