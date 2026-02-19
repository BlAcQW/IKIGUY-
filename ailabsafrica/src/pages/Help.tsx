import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import HelpSection from '@/components/help/HelpSection';

const Help: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState('pricing');

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && ['pricing', 'faq', 'features', 'support'].includes(tab)) {
      setActiveTab(tab);
    }
  }, [searchParams]);

  return <HelpSection defaultTab={activeTab} />;
};

export default Help;
