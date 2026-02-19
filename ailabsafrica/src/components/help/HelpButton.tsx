import React from 'react';
import { Button } from '@/components/ui/button';
import { HelpCircle } from 'lucide-react';
import { useHelp } from '@/contexts/HelpContext';

interface HelpButtonProps {
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  showText?: boolean;
}

const HelpButton: React.FC<HelpButtonProps> = ({ 
  variant = 'ghost', 
  size = 'sm', 
  className = '',
  showText = false 
}) => {
  const { showHelpSection } = useHelp();

  return (
    <Button
      variant={variant}
      size={size}
      onClick={showHelpSection}
      className={`flex items-center gap-2 ${className}`}
      aria-label="Get help and support"
    >
      <HelpCircle className="h-4 w-4" />
      {showText && 'Help'}
    </Button>
  );
};

export default HelpButton;
