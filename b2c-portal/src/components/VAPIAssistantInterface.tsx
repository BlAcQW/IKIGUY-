import React, { useState } from 'react';
import { 
  Phone, 
  MessageSquare, 
  Settings, 
  BarChart3, 
  Users, 
  FileText,
  CreditCard,
  Plus,
  Search,
  MoreVertical,
  Copy,
  Trash2,
  Edit2,
  Play,
  Globe,
  Mic,
  Brain,
  Zap,
  ChevronDown
} from 'lucide-react';

interface Assistant {
  id: string;
  name: string;
  description: string;
  status: 'online' | 'busy' | 'offline';
  model: string;
  voice: string;
  transcriber: string;
  language: string;
  cost: number;
  latency: number;
}

export const VAPIAssistantInterface: React.FC = () => {
  const [selectedAssistant, setSelectedAssistant] = useState<Assistant | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  const assistants: Assistant[] = [
    {
      id: '1',
      name: 'John from Stanton Engineering Group',
      description: 'Paige',
      status: 'online',
      model: 'gpt-4o',
      voice: 'deepgram',
      transcriber: 'deepgram',
      language: 'en',
      cost: 0.12,
      latency: 1050
    },
    {
      id: '2',
      name: 'Kofi from Mr. Wu',
      description: 'Elliot',
      status: 'online',
      model: 'gpt-4o',
      voice: 'vapi',
      transcriber: 'deepgram',
      language: 'en',
      cost: 0.15,
      latency: 950
    }
  ];

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-64 bg-sidebar-background border-r border-sidebar-border flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-sidebar-border">
          <h1 className="text-2xl font-bold text-sidebar-foreground">VAPI</h1>
        </div>
        
        {/* User Info */}
        <div className="px-4 py-3 border-b border-sidebar-border">
          <div className="flex items-center gap-2 text-sm text-sidebar-foreground">
            <span className="truncate">alfred.anyan@gmail.com's Org</span>
            <ChevronDown className="w-4 h-4 text-gray-600" />
          </div>
        </div>
        
        {/* Search */}
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-600" />
            <input
              type="text"
              placeholder="Search"
              className="search-input w-full pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 px-2">
          <div className="space-y-1">
            <div className="nav-item">
              <Users className="w-4 h-4" />
              <span>Overview</span>
            </div>
            
            <div className="nav-item active">
              <Users className="w-4 h-4" />
              <span>Assistants</span>
            </div>
            
            <div className="nav-item">
              <Brain className="w-4 h-4" />
              <span>Tools</span>
            </div>
            
            <div className="nav-item">
              <Phone className="w-4 h-4" />
              <span>Phone Numbers</span>
            </div>
            
            <div className="nav-item">
              <Mic className="w-4 h-4" />
              <span>Voice Library</span>
            </div>
            
            <div className="nav-item">
              <Settings className="w-4 h-4" />
              <span>API Keys</span>
            </div>
          </div>
        </nav>
        
        {/* Credits */}
        <div className="p-4 border-t border-sidebar-border">
          <div className="credits-display">
            <CreditCard className="w-4 h-4" />
            <span>PAYG</span>
            <span className="credits-amount">12.15</span>
            <span>Credits</span>
          </div>
          <button className="btn-vapi w-full mt-2">
            Buy Credits
          </button>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-card border-b border-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button className="nav-item px-3 py-1.5">
                <Users className="w-4 h-4" />
                <span>Assistants</span>
              </button>
              <button className="nav-item px-3 py-1.5">
                <FileText className="w-4 h-4" />
                <span>Docs</span>
              </button>
            </div>
            
            <button className="btn-vapi-primary">
              <Plus className="w-4 h-4 mr-2" />
              Create Assistant
            </button>
          </div>
        </div>
        
        {/* Content Area */}
        <div className="flex-1 flex">
          {/* Assistant List */}
          <div className="w-96 border-r border-border overflow-y-auto">
            <div className="p-4">
              <input
                type="text"
                placeholder="Search Assistants"
                className="search-input w-full"
              />
            </div>
            
            <div className="px-4 pb-4 space-y-2">
              {assistants.map((assistant) => (
                <div
                  key={assistant.id}
                  className="assistant-card cursor-pointer"
                  onClick={() => setSelectedAssistant(assistant)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`status-dot ${assistant.status}`} />
                        <h3 className="font-medium text-foreground">{assistant.name}</h3>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{assistant.description}</p>
                    </div>
                    <button className="text-gray-600 hover:text-foreground">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Assistant Details */}
          {selectedAssistant && (
            <div className="flex-1 p-6 overflow-y-auto">
              <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-bold text-foreground">{selectedAssistant.name}</h2>
                    <p className="text-gray-600 mt-1">ecdSb-f6e-1982-4edb-9478...</p>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button className="btn-talk">
                      <Phone className="w-4 h-4 mr-2" />
                      Talk to Assistant
                    </button>
                    <button className="btn-publish">
                      Publish
                    </button>
                  </div>
                </div>
                
                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="metric-card">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Cost</span>
                      <span className="text-sm font-medium">~${selectedAssistant.cost}/min</span>
                    </div>
                    <div className="metric-bar">
                      <div className="metric-bar-fill" style={{ width: '60%' }} />
                    </div>
                  </div>
                  
                  <div className="metric-card">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Latency</span>
                      <span className="text-sm font-medium">~{selectedAssistant.latency} ms</span>
                    </div>
                    <div className="metric-bar">
                      <div className="metric-bar-fill" style={{ width: '70%' }} />
                    </div>
                  </div>
                </div>
                
                {/* Tags */}
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="tag-badge model">
                      <span className="w-2 h-2 rounded-full bg-current mr-1" />
                      {selectedAssistant.model}
                    </span>
                    <span className="tag-badge voice">
                      <span className="w-2 h-2 rounded-full bg-current mr-1" />
                      {selectedAssistant.voice}
                    </span>
                    <span className="tag-badge transcriber">
                      <span className="w-2 h-2 rounded-full bg-current mr-1" />
                      {selectedAssistant.transcriber}
                    </span>
                    <span className="tag-badge">
                      <Globe className="w-3 h-3 mr-1" />
                      web
                    </span>
                  </div>
                </div>
                
                {/* Configuration Sections */}
                <div className="space-y-4">
                  <div className="config-section">
                    <div className="config-header">
                      <h3 className="config-title">MODEL</h3>
                      <ChevronDown className="w-5 h-5 text-gray-600" />
                    </div>
                    <p className="text-sm text-gray-600">
                      Configure the behavior of the assistant.
                    </p>
                  </div>
                  
                  <div className="config-section">
                    <div className="config-header">
                      <h3 className="config-title">VOICE</h3>
                      <ChevronDown className="w-5 h-5 text-gray-600" />
                    </div>
                    <p className="text-sm text-gray-600">
                      Select a voice from the list, or sync your voice library if it's missing.
                      If errors persist, enable custom voice and add a voice ID.
                    </p>
                  </div>
                  
                  <div className="config-section">
                    <div className="config-header">
                      <h3 className="config-title">Additional Configuration</h3>
                      <ChevronDown className="w-5 h-5 text-gray-600" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};