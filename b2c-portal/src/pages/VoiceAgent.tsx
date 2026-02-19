import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';

// Import our new components
import { AssistantList, Assistant } from '@/components/voice-agent/AssistantList';
import { AssistantHeader } from '@/components/voice-agent/AssistantHeader';
import { AssistantConfiguration } from '@/components/voice-agent/AssistantConfiguration';
import { VoiceConversationWS } from '@/components/voice-agent/VoiceConversationWS';
import { VoiceConversationRTC } from '@/components/voice-agent/VoiceConversationRTC';
import { CreateAssistantModal } from '@/components/voice-agent/CreateAssistantModal';
import { CreateVapiAgentModal } from '@/components/voice-agent/CreateVapiAgentModal';
import { CloneVoiceAgentModal } from '@/components/voice-agent/CloneVoiceAgentModal';
import { API_BASE_URL } from '@/config/api-config';
import { assistantApiClient } from '@/services/assistant-api-client';


const VoiceAgent: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // State management
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [assistantsLoading, setAssistantsLoading] = useState(true);
  const [currentUserId] = useState('user-123');
  
  const [selectedAssistant, setSelectedAssistant] = useState<Assistant | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  const [showConversation, setShowConversation] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCreateVapiModal, setShowCreateVapiModal] = useState(false);
  const [showCloneModal, setShowCloneModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showCodeModal, setShowCodeModal] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [transportMode, setTransportMode] = useState<'websocket' | 'webrtc'>('websocket');

  // Debounce timer for auto-save
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Function to fetch assistants
  const fetchAssistants = async () => {
    setAssistantsLoading(true);
    try {
      // Use the assistant API client
      const assistantsList = await assistantApiClient.fetchAssistants({
        activeOnly: false
      });

      console.log('[VoiceAgent] 📋 Fetched assistants:', assistantsList.length);
      console.log('[VoiceAgent] 🔍 First assistant:', assistantsList[0]);
      console.log('[VoiceAgent] 🆔 First assistant ID:', assistantsList[0]?.id);

      setAssistants(assistantsList);
      if (assistantsList.length > 0 && !selectedAssistant) {
        const firstAssistant = assistantsList[0];
        console.log('[VoiceAgent] ✅ Auto-selecting first assistant:', firstAssistant.id, firstAssistant.name);
        setSelectedAssistant(firstAssistant);
      }
    } catch (error) {
      console.error('[VoiceAgent] ❌ Error fetching assistants:', error);
      toast({
        title: "Failed to load assistants",
        description: "Please check your connection and try again.",
        variant: "destructive"
      });
    } finally {
      setAssistantsLoading(false);
    }
  };

  // Fetch assistants on mount
  useEffect(() => {
    console.log('[VoiceAgent] 🚀 Component mounted - fetching assistants...');
    console.log('[VoiceAgent] 📍 This log proves new code is loaded');
    fetchAssistants();
  }, [toast]);

  // Handle assistant selection
  const handleSelectAssistant = (assistant: Assistant) => {
    setSelectedAssistant(assistant);
  };

  // Handle configuration changes with debouncing
  const handleConfigurationChange = useCallback(async (config: Partial<Assistant>) => {
    if (!selectedAssistant) return;

    const updatedAssistant = { ...selectedAssistant, ...config };

    // Update UI immediately for responsive feel
    setSelectedAssistant(updatedAssistant);
    setAssistants(prev =>
      prev.map(a => a.id === selectedAssistant.id ? updatedAssistant : a)
    );

    // Debounce the API call to prevent race conditions
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    autoSaveTimerRef.current = setTimeout(async () => {
      try {
        await assistantApiClient.updateAssistant(selectedAssistant.id, config);
      } catch (error) {
        console.error('Error auto-saving configuration:', error);
        toast({
          title: "Auto-save failed",
          description: "Changes saved locally but not synced. Use 'Publish Changes' to retry.",
          variant: "destructive"
        });
      }
    }, 500); // 500ms debounce delay
  }, [selectedAssistant, toast]);

  // Handle publishing changes
  const handlePublish = async () => {
    if (!selectedAssistant) return;

    try {
      await assistantApiClient.publishAssistant(selectedAssistant.id, selectedAssistant);

      toast({
        title: "Assistant updated",
        description: "Your changes have been published successfully.",
      });
    } catch (error) {
      console.error('Error updating assistant:', error);
      toast({
        title: "Failed to update assistant",
        description: "Please try again later.",
        variant: "destructive"
      });
    }
  };

  // Handle starting conversation
  const handleStartConversation = () => {
    if (!selectedAssistant) {
      toast({
        title: "No assistant selected",
        description: "Please select an assistant before starting a conversation.",
        variant: "destructive"
      });
      return;
    }

    if (!selectedAssistant.id || selectedAssistant.id.trim() === '') {
      console.error('[VoiceAgent] ❌ Cannot start conversation - invalid assistant:', selectedAssistant);
      toast({
        title: "Invalid assistant",
        description: "The selected assistant has no ID. Please try reloading or selecting a different assistant.",
        variant: "destructive"
      });
      return;
    }

    // ✅ Log assistant data being passed to conversation
    console.log('[VoiceAgent] ✅ Starting conversation with assistant:', {
      id: selectedAssistant.id,
      name: selectedAssistant.name,
      llm_provider: selectedAssistant.llm_provider,
      llm_model: selectedAssistant.llm_model,
      tts_provider: selectedAssistant.tts_provider,
      stt_provider: selectedAssistant.stt_provider,
      system_prompt: selectedAssistant.system_prompt ? `${selectedAssistant.system_prompt.substring(0, 50)}...` : 'NOT SET'
    });

    setShowConversation(true);
  };

  // Handle delete assistant
  const handleDeleteAssistant = async () => {
    if (!selectedAssistant) return;

    try {
      await assistantApiClient.deleteAssistant(selectedAssistant.id);

      // Remove from local state
      setAssistants(prev => prev.filter(a => a.id !== selectedAssistant.id));
      setSelectedAssistant(assistants.length > 1 ? assistants[0] : null);
      setShowDeleteConfirm(false);

      toast({
        title: "Assistant deleted",
        description: "The assistant has been removed successfully.",
      });
    } catch (error) {
      console.error('Error deleting assistant:', error);
      toast({
        title: "Failed to delete assistant",
        description: "Please try again later.",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <DashboardSidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <AssistantHeader
          assistantName={selectedAssistant?.name || 'No Assistant Selected'}
          assistantId={selectedAssistant?.id || ''}
          onStartConversation={handleStartConversation}
          onShowCode={() => setShowCodeModal(true)}
          onDelete={() => setShowDeleteConfirm(true)}
          onClone={() => setShowCloneModal(true)}
          transportMode={transportMode}
          onTransportModeChange={setTransportMode}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col lg:flex-row relative">
          {/* Left Panel - Assistant List */}
          <div className={`transition-all duration-300 ${isSidebarCollapsed ? 'lg:w-0 lg:overflow-hidden' : 'lg:w-80'}`}>
            <AssistantList
              assistants={assistants}
              loading={assistantsLoading}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              selectedAssistant={selectedAssistant}
              onSelectAssistant={handleSelectAssistant}
              onCreateAssistant={() => setShowCreateModal(true)}
              onCreateVapiAgent={() => setShowCreateVapiModal(true)}
            />
          </div>

          {/* Collapse Toggle Button */}
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            className="hidden lg:flex absolute left-0 top-4 z-10 items-center justify-center w-6 h-12 bg-white border border-gray-200 rounded-r-lg hover:bg-gray-50 transition-colors shadow-sm"
            style={{ left: isSidebarCollapsed ? '0' : '20rem' }}
            title={isSidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'}
          >
            <svg
              className={`w-4 h-4 transition-transform ${isSidebarCollapsed ? 'rotate-0' : 'rotate-180'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          {/* Right Panel - Configuration */}
          <div className="flex-1">
            <AssistantConfiguration
              assistant={selectedAssistant}
              onConfigurationChange={handleConfigurationChange}
              onPublish={handlePublish}
            />
          </div>
        </div>
      </div>

      {/* Voice Conversation Modal - WebSocket or WebRTC */}
      {transportMode === 'websocket' ? (
        <VoiceConversationWS
          isOpen={showConversation && !!selectedAssistant?.id}
          onClose={() => setShowConversation(false)}
          assistantName={selectedAssistant?.name || 'Unknown'}
          assistantId={selectedAssistant?.id || ''}
          assistant={selectedAssistant}
        />
      ) : (
        <VoiceConversationRTC
          isOpen={showConversation && !!selectedAssistant?.id}
          onClose={() => setShowConversation(false)}
          assistantName={selectedAssistant?.name || 'Unknown'}
          assistantId={selectedAssistant?.id || ''}
          assistant={selectedAssistant}
        />
      )}

      {/* Create Assistant Modal */}
      <CreateAssistantModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onAssistantCreated={() => {
          setShowCreateModal(false);
          // Refresh assistants list
          fetchAssistants();
        }}
        apiBaseUrl={API_BASE_URL}
      />

      {/* Create VAPI Agent Modal */}
      <CreateVapiAgentModal
        isOpen={showCreateVapiModal}
        onClose={() => setShowCreateVapiModal(false)}
        onAgentCreated={() => {
          setShowCreateVapiModal(false);
          // Refresh assistants list
          fetchAssistants();
        }}
        apiBaseUrl={API_BASE_URL}
      />

      {/* Clone Voice Agent Modal */}
      <CloneVoiceAgentModal
        isOpen={showCloneModal}
        onClose={() => setShowCloneModal(false)}
        onAgentCloned={() => {
          setShowCloneModal(false);
          // Refresh assistants list
          fetchAssistants();
        }}
        sourceAgent={selectedAssistant}
        apiBaseUrl={API_BASE_URL}
      />

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-2 sm:p-4 z-50">
          <div className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full max-w-md mx-2">
            <h3 className="text-lg font-semibold mb-4">Delete Assistant</h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete "{selectedAssistant?.name}"? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-sm border border-border rounded-md hover:bg-accent"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAssistant}
                className="px-4 py-2 text-sm bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Code Modal */}
      {showCodeModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-2 sm:p-4 z-50">
          <div className="bg-card border border-border rounded-lg p-4 sm:p-6 w-full max-w-2xl mx-2">
            <h3 className="text-lg font-semibold mb-4">Embed Code</h3>
            <p className="text-gray-600 mb-4">
              Integration code for "{selectedAssistant?.name}" will be displayed here.
            </p>
            <div className="flex justify-end">
              <button
                onClick={() => setShowCodeModal(false)}
                className="px-4 py-2 text-sm bg-indigo-600 text-primary-foreground rounded-md hover:bg-primary/90"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceAgent;