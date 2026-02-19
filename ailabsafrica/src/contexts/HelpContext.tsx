import React, { createContext, useContext, useState, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

interface HelpContextType {
  showHelpSection: () => void;
  showPricingHelp: () => void;
  showFeatureHelp: (feature: string) => void;
  isHelpOpen: boolean;
  closeHelp: () => void;
}

const HelpContext = createContext<HelpContextType | undefined>(undefined);

interface HelpProviderProps {
  children: ReactNode;
}

export const HelpProvider: React.FC<HelpProviderProps> = ({ children }) => {
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const navigate = useNavigate();

  const showHelpSection = () => {
    navigate('/help');
    setIsHelpOpen(true);
  };

  const showPricingHelp = () => {
    navigate('/help?tab=pricing');
    setIsHelpOpen(true);
  };

  const showFeatureHelp = (feature: string) => {
    navigate(`/help?tab=features&feature=${feature}`);
    setIsHelpOpen(true);
  };

  const closeHelp = () => {
    setIsHelpOpen(false);
  };

  const value: HelpContextType = {
    showHelpSection,
    showPricingHelp,
    showFeatureHelp,
    isHelpOpen,
    closeHelp,
  };

  return (
    <HelpContext.Provider value={value}>
      {children}
    </HelpContext.Provider>
  );
};

export const useHelp = (): HelpContextType => {
  const context = useContext(HelpContext);
  if (context === undefined) {
    throw new Error('useHelp must be used within a HelpProvider');
  }
  return context;
};
