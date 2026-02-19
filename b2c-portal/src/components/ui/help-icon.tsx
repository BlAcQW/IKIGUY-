import React, { useState } from 'react';
import { HelpCircle, ExternalLink, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { HelpContent } from '@/lib/help-content';

interface HelpIconProps {
  content: HelpContent;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'tooltip' | 'modal' | 'both';
  className?: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export const HelpIcon: React.FC<HelpIconProps> = ({
  content,
  size = 'md',
  variant = 'both',
  className = '',
  position = 'top'
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6'
  };

  const handleClick = () => {
    if (variant === 'modal' || variant === 'both') {
      setIsModalOpen(true);
    }
  };

  const tooltipContent = (
    <div className="max-w-xs space-y-2">
      <div className="font-medium">{content.title}</div>
      <p className="text-sm text-gray-600">{content.description}</p>
      {variant === 'both' && (
        <div className="pt-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={(e) => {
              e.stopPropagation();
              setIsModalOpen(true);
            }}
          >
            <BookOpen className="mr-1 h-3 w-3" />
            Learn more
          </Button>
        </div>
      )}
    </div>
  );

  const modalContent = (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">{content.title}</h3>
        <p className="text-gray-600 mt-1">{content.description}</p>
      </div>

      {content.details && (
        <div>
          <h4 className="font-medium mb-2">Details</h4>
          <p className="text-sm text-gray-600">{content.details}</p>
        </div>
      )}

      {content.examples && content.examples.length > 0 && (
        <div>
          <h4 className="font-medium mb-2">Examples</h4>
          <div className="space-y-2">
            {content.examples.map((example, index) => (
              <div key={index} className="bg-muted p-3 rounded-md">
                <code className="text-sm">{example}</code>
              </div>
            ))}
          </div>
        </div>
      )}

      {content.links && content.links.length > 0 && (
        <div>
          <h4 className="font-medium mb-2">Related Resources</h4>
          <div className="space-y-2">
            {content.links.map((link, index) => (
              <a
                key={index}
                href={link.url}
                target={link.external ? '_blank' : undefined}
                rel={link.external ? 'noopener noreferrer' : undefined}
                className="flex items-center gap-2 text-sm text-indigo-600 hover:underline"
              >
                <ExternalLink className="h-3 w-3" />
                {link.label}
              </a>
            ))}
          </div>
        </div>
      )}

      {content.relatedTopics && content.relatedTopics.length > 0 && (
        <div>
          <h4 className="font-medium mb-2">Related Topics</h4>
          <div className="flex flex-wrap gap-2">
            {content.relatedTopics.map((topic, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {topic}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <TooltipProvider>
      <div className={`inline-flex items-center ${className}`}>
        {variant === 'tooltip' || variant === 'both' ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className={`h-auto p-1 ${sizeClasses[size]} text-gray-600 hover:text-foreground`}
                onClick={handleClick}
              >
                <HelpCircle className={sizeClasses[size]} />
              </Button>
            </TooltipTrigger>
            <TooltipContent side={position} className="max-w-xs">
              {tooltipContent}
            </TooltipContent>
          </Tooltip>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            className={`h-auto p-1 ${sizeClasses[size]} text-gray-600 hover:text-foreground`}
            onClick={handleClick}
          >
            <HelpCircle className={sizeClasses[size]} />
          </Button>
        )}

        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <HelpCircle className="h-5 w-5" />
                Help & Documentation
              </DialogTitle>
              <DialogDescription>
                Detailed information and resources
              </DialogDescription>
            </DialogHeader>
            {modalContent}
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  );
};
