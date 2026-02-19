import React from 'react';
import { QrCode, Globe, Wrench } from 'lucide-react';
import { cn } from '@/lib/utils';

export type UtilityType = 'qr-generator' | 'web-scraper';

interface Utility {
  id: UtilityType;
  name: string;
  description: string;
  icon: React.ReactNode;
  emoji: string;
}

interface UtilitiesSidebarProps {
  selectedUtilityId: UtilityType | null;
  onSelectUtility: (utilityId: UtilityType) => void;
}

const utilities: Utility[] = [
  {
    id: 'qr-generator',
    name: 'QR Code Generator',
    description: 'Create branded QR codes with custom colors and logos',
    icon: <QrCode className="w-5 h-5" />,
    emoji: '📱'
  },
  {
    id: 'web-scraper',
    name: 'Web Content Scraper',
    description: 'Extract clean text content from web pages',
    icon: <Globe className="w-5 h-5" />,
    emoji: '🕷️'
  }
];

export function UtilitiesSidebar({ selectedUtilityId, onSelectUtility }: UtilitiesSidebarProps) {
  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Wrench className="w-5 h-5 text-primary" />
          <h2 className="text-lg font-semibold text-gray-900">Utilities</h2>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          {utilities.length} tools available
        </p>
      </div>

      {/* Utilities List */}
      <div className="flex-1 overflow-y-auto p-2">
        <div className="space-y-1">
          {utilities.map((utility) => (
            <button
              key={utility.id}
              onClick={() => onSelectUtility(utility.id)}
              className={cn(
                "w-full text-left px-3 py-3 rounded-lg transition-colors",
                selectedUtilityId === utility.id
                  ? "bg-primary/10 border-2 border-primary"
                  : "bg-white border-2 border-transparent hover:bg-gray-50"
              )}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center",
                    selectedUtilityId === utility.id
                      ? "bg-primary text-white"
                      : "bg-gray-100 text-gray-600"
                  )}>
                    {utility.icon}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{utility.emoji}</span>
                    <h3 className={cn(
                      "text-sm font-medium truncate",
                      selectedUtilityId === utility.id
                        ? "text-primary"
                        : "text-gray-900"
                    )}>
                      {utility.name}
                    </h3>
                  </div>
                  <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                    {utility.description}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
        <p className="text-xs text-gray-600">
          More utilities coming soon...
        </p>
      </div>
    </div>
  );
}
