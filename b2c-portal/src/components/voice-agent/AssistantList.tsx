import React from 'react';
import { Search, Plus, Phone, ChevronDown } from 'lucide-react';

export interface Assistant {
  id: string;
  name: string;
  description: string;
  user_id: string;
  template_id: string;
  status: 'draft' | 'published';
  llm_provider: string;
  llm_model: string;
  first_message_mode: string;
  first_message: string;
  system_prompt: string;
  tts_provider: string;
  tts_model: string;
  tts_voice: string;
  language: string;
  country: string;
  stt_provider: string;
  stt_model: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
  speed?: number; // TTS speed: 0.5-2.0, default 1.0
  pitch?: number; // TTS pitch: -20 to +20, default 0
  voice_description?: string; // Parler-TTS voice description
}

interface AssistantListProps {
  assistants: Assistant[];
  loading: boolean;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedAssistant: Assistant | null;
  onSelectAssistant: (assistant: Assistant) => void;
  onCreateAssistant: () => void;
  onCreateVapiAgent?: () => void;
}

export const AssistantList: React.FC<AssistantListProps> = ({
  assistants,
  loading,
  searchQuery,
  onSearchChange,
  selectedAssistant,
  onSelectAssistant,
  onCreateAssistant,
  onCreateVapiAgent
}) => {
  const [showCreateMenu, setShowCreateMenu] = React.useState(false);
  const filteredAssistants = assistants.filter(assistant =>
    assistant.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    assistant.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    assistant.language.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full lg:w-80 bg-card border-b lg:border-b-0 lg:border-r border-border p-3 sm:p-4 lg:p-6 flex-shrink-0 overflow-y-auto lg:h-full">
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <h2 className="text-base sm:text-lg font-semibold">Assistants</h2>
      </div>
      
      <div className="relative mb-3 sm:mb-4">
        {onCreateVapiAgent ? (
          // Dropdown for multiple creation options
          <div>
            <button
              onClick={() => setShowCreateMenu(!showCreateMenu)}
              className="w-full bg-indigo-600 hover:bg-primary/90 text-primary-foreground py-2 px-3 sm:px-4 rounded-md text-xs sm:text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create Agent
              <ChevronDown className={`w-4 h-4 transition-transform ${showCreateMenu ? 'rotate-180' : ''}`} />
            </button>
            
            {showCreateMenu && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-card border border-border rounded-md shadow-lg z-10 overflow-hidden">
                <button
                  onClick={() => {
                    onCreateAssistant();
                    setShowCreateMenu(false);
                  }}
                  className="w-full px-3 py-2 text-left hover:bg-accent transition-colors flex items-center gap-2 text-xs sm:text-sm"
                >
                  <Plus className="w-4 h-4" />
                  <div>
                    <div className="font-medium">KasaAI Agent</div>
                    <div className="text-gray-600 text-xs">Using our infrastructure</div>
                  </div>
                </button>
                <button
                  onClick={() => {
                    onCreateVapiAgent();
                    setShowCreateMenu(false);
                  }}
                  className="w-full px-3 py-2 text-left hover:bg-accent transition-colors flex items-center gap-2 text-xs sm:text-sm border-t border-border"
                >
                  <Phone className="w-4 h-4" />
                  <div>
                    <div className="font-medium">VAPI Agent</div>
                    <div className="text-gray-600 text-xs">Advanced phone integration</div>
                  </div>
                </button>
              </div>
            )}
          </div>
        ) : (
          // Single create button
          <button 
            onClick={onCreateAssistant}
            className="w-full bg-indigo-600 hover:bg-primary/90 text-primary-foreground py-2 px-3 sm:px-4 rounded-md text-xs sm:text-sm font-medium transition-colors flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create Assistant
          </button>
        )}
      </div>
      
      <div className="space-y-2 sm:space-y-3 mb-3 sm:mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-600" />
          <input 
            type="text" 
            placeholder="Search Assistants" 
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full bg-background border border-border rounded-md pl-9 sm:pl-10 pr-3 sm:pr-4 py-1.5 sm:py-2 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        
        {/* African Languages Quick Filter */}
        <div className="flex flex-wrap gap-2">
          <button 
            onClick={() => onSearchChange('')}
            className="px-2 py-1 text-xs bg-muted hover:bg-muted/80 rounded-md transition-colors"
          >
            All
          </button>
          <button 
            onClick={() => onSearchChange('twi')}
            className="px-2 py-1 text-xs bg-orange-600 hover:bg-orange-500 text-white rounded-md transition-colors"
          >
            🇬🇭 Twi
          </button>
          <button 
            onClick={() => onSearchChange('yoruba')}
            className="px-2 py-1 text-xs bg-green-600 hover:bg-green-500 text-white rounded-md transition-colors"
          >
            🇳🇬 Yorùbá
          </button>
          <button 
            onClick={() => onSearchChange('swahili')}
            className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-500 text-white rounded-md transition-colors"
          >
            🇰🇪 Swahili
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div className="text-xs sm:text-sm text-gray-600 mb-3 sm:mb-4">
        {loading ? (
          <div className="animate-pulse">Loading assistants...</div>
        ) : (
          `${filteredAssistants.length} assistant${filteredAssistants.length !== 1 ? 's' : ''} found`
        )}
      </div>

      {/* Assistant List */}
      <div className="space-y-2 max-h-64 lg:max-h-96 overflow-y-auto">
        {loading ? (
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-16 bg-muted rounded-md"></div>
              </div>
            ))}
          </div>
        ) : filteredAssistants.length > 0 ? (
          filteredAssistants.map((assistant) => (
            <div 
              key={assistant.id}
              className={`p-2 sm:p-3 rounded-md border cursor-pointer transition-colors ${
                selectedAssistant?.id === assistant.id 
                  ? 'bg-primary/10 border-primary text-primary' 
                  : 'bg-card border-border hover:bg-accent'
              }`}
              onClick={() => onSelectAssistant(assistant)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-xs sm:text-sm truncate">{assistant.name}</div>
                  <div className="text-xs text-gray-600 truncate mt-0.5 sm:mt-1">
                    {assistant.description}
                  </div>
                  <div className="flex items-center gap-1 sm:gap-2 mt-1 sm:mt-2">
                    <span className={`px-1.5 sm:px-2 py-0.5 sm:py-1 text-xs rounded-full ${
                      assistant.status === 'published' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300' 
                        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                    }`}>
                      {assistant.status}
                    </span>
                    <span className="text-xs text-gray-600 capitalize">
                      {assistant.language}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-600">
            <div className="text-sm">No assistants found</div>
            <div className="text-xs mt-1">Try adjusting your search</div>
          </div>
        )}
      </div>
    </div>
  );
};