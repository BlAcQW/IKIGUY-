import React from 'react';
import {
  Code,
  Play,
  MessageCircle,
  Smartphone,
  MoreVertical,
  Trash2,
  Copy,
  Radio,
  Wifi
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface AssistantHeaderProps {
  assistantName: string;
  assistantId: string;
  onStartConversation: () => void;
  onShowCode: () => void;
  onDelete: () => void;
  onClone: () => void;
  transportMode?: 'websocket' | 'webrtc';
  onTransportModeChange?: (mode: 'websocket' | 'webrtc') => void;
}

export const AssistantHeader: React.FC<AssistantHeaderProps> = ({
  assistantName,
  assistantId,
  onStartConversation,
  onShowCode,
  onDelete,
  onClone,
  transportMode = 'websocket',
  onTransportModeChange
}) => {
  return (
    <div className="bg-card border-b border-border px-3 sm:px-4 lg:px-6 py-3 sm:py-4">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 sm:gap-4">
        <div className="flex items-center justify-between lg:justify-start">
          <div className="flex items-center space-x-3 sm:space-x-4 lg:space-x-6">
            <div className="text-lg sm:text-xl lg:text-2xl font-bold text-indigo-600">Kasa AI</div>
            <button className="text-gray-600 hover:text-foreground text-xs sm:text-sm">
              Docs
            </button>
          </div>
        </div>
        
        <div className="flex flex-col lg:flex-row items-center gap-2 sm:gap-4">
          <div className="text-center lg:text-left">
            <div className="text-sm sm:text-base lg:text-lg font-semibold">{assistantName}</div>
            <div className="text-xs text-gray-600 hidden lg:block">{assistantId}</div>
          </div>
          
          <div className="flex flex-wrap items-center gap-1 sm:gap-2">
            <button className="flex items-center space-x-1 px-2 sm:px-3 py-1 text-gray-600 hover:text-foreground text-xs sm:text-sm">
              <Code className="w-3 h-3 sm:w-4 sm:h-4" />
              <span>Code</span>
            </button>
            <button className="flex items-center space-x-1 px-2 sm:px-3 py-1 text-gray-600 hover:text-foreground text-xs sm:text-sm">
              <Play className="w-3 h-3 sm:w-4 sm:h-4" />
              <span>Test</span>
            </button>

            {/* Transport Mode Toggle */}
            {onTransportModeChange && (
              <div className="flex items-center bg-muted rounded-md p-0.5 text-xs">
                <button
                  onClick={() => onTransportModeChange('websocket')}
                  className={`flex items-center gap-1 px-2 py-1 rounded transition-all ${
                    transportMode === 'websocket'
                      ? 'bg-background shadow-sm font-medium'
                      : 'text-gray-600 hover:text-foreground'
                  }`}
                  title="WebSocket (traditional)"
                >
                  <Wifi className="w-3 h-3" />
                  <span className="hidden sm:inline">WS</span>
                </button>
                <button
                  onClick={() => onTransportModeChange('webrtc')}
                  className={`flex items-center gap-1 px-2 py-1 rounded transition-all ${
                    transportMode === 'webrtc'
                      ? 'bg-background shadow-sm font-medium'
                      : 'text-gray-600 hover:text-foreground'
                  }`}
                  title="WebRTC (low latency)"
                >
                  <Radio className="w-3 h-3" />
                  <span className="hidden sm:inline">RTC</span>
                </button>
              </div>
            )}

            <button
              onClick={onStartConversation}
              className="flex items-center space-x-1 px-2 sm:px-3 py-1 bg-indigo-600 hover:bg-primary/90 text-primary-foreground text-xs sm:text-sm rounded-md transition-colors"
            >
              <MessageCircle className="w-3 h-3 sm:w-4 sm:h-4" />
              <span>Talk to Assistant</span>
            </button>
            <button className="flex items-center space-x-1 px-2 sm:px-3 py-1 text-gray-600 hover:text-foreground text-xs sm:text-sm">
              <Smartphone className="w-3 h-3 sm:w-4 sm:h-4" />
              <span>Call</span>
            </button>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center space-x-1 px-2 sm:px-3 py-1 text-gray-600 hover:text-foreground text-xs sm:text-sm">
                  <MoreVertical className="w-3 h-3 sm:w-4 sm:h-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="bg-popover border-border">
                <DropdownMenuItem
                  className="flex items-center gap-2 text-popover-foreground focus:text-foreground focus:bg-accent"
                  onClick={onShowCode}
                >
                  <Code className="w-3 h-3 sm:w-4 sm:h-4" />
                  Embed Code
                </DropdownMenuItem>
                <DropdownMenuItem
                  className="flex items-center gap-2 text-popover-foreground focus:text-foreground focus:bg-accent"
                  onClick={onClone}
                >
                  <Copy className="w-3 h-3 sm:w-4 sm:h-4" />
                  Clone Voice Agent
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-border" />
                <DropdownMenuItem
                  className="flex items-center gap-2 text-destructive focus:text-destructive"
                  onClick={onDelete}
                >
                  <Trash2 className="w-3 h-3 sm:w-4 sm:h-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>
    </div>
  );
};