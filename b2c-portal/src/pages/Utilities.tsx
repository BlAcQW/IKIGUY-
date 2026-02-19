/**
 * Utilities Page
 *
 * Main interface for various utility tools including QR code generation and web scraping.
 * Layout inspired by TTSLab.tsx with sidebar for utility selection.
 */

import React, { useState } from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { UtilitiesSidebar, type UtilityType } from '@/components/utilities/UtilitiesSidebar';
import { QRCodePanel } from '@/components/utilities/QRCodePanel';
import { WebScraperPanel } from '@/components/utilities/WebScraperPanel';
import { Wrench } from 'lucide-react';

export const Utilities: React.FC = () => {
  const [selectedUtility, setSelectedUtility] = useState<UtilityType>('qr-generator');

  const renderUtilityContent = () => {
    switch (selectedUtility) {
      case 'qr-generator':
        return <QRCodePanel />;

      case 'web-scraper':
        return <WebScraperPanel />;

      default:
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-6xl mb-4">🛠️</div>
              <h3 className="text-xl font-semibold text-foreground">No Utility Selected</h3>
              <p className="text-muted-foreground mt-2">
                Please select a utility from the sidebar to get started
              </p>
            </div>
          </div>
        );
    }
  };

  const getUtilityInfo = () => {
    switch (selectedUtility) {
      case 'qr-generator':
        return {
          name: 'QR Code Generator',
          description: 'Create branded QR codes with custom colors and logos',
          emoji: '📱'
        };
      case 'web-scraper':
        return {
          name: 'Web Content Scraper',
          description: 'Extract clean text from web pages',
          emoji: '🕷️'
        };
      default:
        return {
          name: 'Utilities',
          description: 'Select a utility to get started',
          emoji: '🛠️'
        };
    }
  };

  const utilityInfo = getUtilityInfo();

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Main Sidebar */}
      <DashboardSidebar />

      {/* Secondary Sidebar - Utilities */}
      <UtilitiesSidebar
        selectedUtilityId={selectedUtility}
        onSelectUtility={setSelectedUtility}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <Wrench className="w-6 h-6 text-primary" />
                <div>
                  <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
                    <span>{utilityInfo.emoji}</span>
                    <span>{utilityInfo.name}</span>
                  </h1>
                  <p className="text-sm text-muted-foreground mt-1">
                    {utilityInfo.description}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-100">
                🟢 Online
              </span>
            </div>
          </div>
        </div>

        {/* Utility Content */}
        <div className="flex-1 overflow-y-auto bg-background">
          {renderUtilityContent()}
        </div>
      </div>
    </div>
  );
};

export default Utilities;
