/**
 * Phone Numbers Management Page
 * Main orchestrator using smaller focused components
 * Real API integration with backend
 */

import React, { useState, useEffect } from 'react';
import { Phone, Plus, Upload, Globe, Check, Zap, AlertCircle } from 'lucide-react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { useToast } from '@/hooks/use-toast';
import { PhoneNumbersList } from '@/components/phone/PhoneNumbersList';
import { ImportModal } from '@/components/phone/ImportModal';
import { ProvisionModal } from '@/components/phone/ProvisionModal';
import { TestCallModal } from '@/components/phone/TestCallModal';
import { VAPICostMonitoring } from '@/components/phone/VAPICostMonitoring';
import { AddCreditModal } from '@/components/phone/AddCreditModal';
import { CDRStatsModal } from '@/components/phone/CDRStatsModal';
import {
  getPhoneNumbers,
  assignPhoneToAssistant,
  deletePhoneNumber,
  importPhoneNumbers,
  provisionPhoneNumber,
  ImportRequest,
  ProvisionRequest,
  PhoneNumber
} from '@/lib/phone-api-client';
import { assistantApiClient } from '@/services/assistant-api-client';

interface Assistant {
  id: string;
  name: string;
  system_prompt?: string;
  llm_provider?: string;
  llm_model?: string;
  tts_provider?: string;
  stt_provider?: string;
}

const PhoneNumbers: React.FC = () => {
  const { toast } = useToast();

  // State
  const [activeTab, setActiveTab] = useState<'phones' | 'cost-monitoring'>('cost-monitoring');
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([]);
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showProvisionModal, setShowProvisionModal] = useState(false);
  const [showTestCallModal, setShowTestCallModal] = useState(false);
  const [selectedPhoneForTest, setSelectedPhoneForTest] = useState<PhoneNumber | null>(null);
  const [copiedNumber, setCopiedNumber] = useState<string | null>(null);

  // Cost monitoring state
  const [showAddCreditModal, setShowAddCreditModal] = useState(false);
  const [selectedPhoneForCredit, setSelectedPhoneForCredit] = useState<PhoneNumber | null>(null);
  const [costMonitoringRefresh, setCostMonitoringRefresh] = useState(0);

  // CDR Stats modal state
  const [showCDRStatsModal, setShowCDRStatsModal] = useState(false);
  const [selectedPhoneForStats, setSelectedPhoneForStats] = useState<PhoneNumber | null>(null);

  // Load phone numbers and assistants on mount
  useEffect(() => {
    loadPhoneNumbers();
    loadAssistants();
  }, []);

  const loadPhoneNumbers = async () => {
    try {
      setIsLoading(true);
      const response = await getPhoneNumbers();
      setPhoneNumbers(response.numbers || []);
    } catch (error: any) {
      toast({
        title: 'Error loading phone numbers',
        description: error.message,
        variant: 'destructive'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const loadAssistants = async () => {
    try {
      const assistantsList = await assistantApiClient.fetchAssistants({
        activeOnly: false
      });
      console.log('[PhoneNumbers] Loaded assistants:', assistantsList.length);
      setAssistants(assistantsList);
    } catch (error: any) {
      console.error('[PhoneNumbers] Error loading assistants:', error);
      toast({
        title: 'Error loading assistants',
        description: error.message,
        variant: 'destructive'
      });
    }
  };

  const handleImport = async (request: ImportRequest) => {
    try {
      const response = await importPhoneNumbers(request);

      toast({
        title: 'Import successful',
        description: `Imported ${response.numbers?.length || 0} phone numbers from ${request.provider}`
      });

      // Reload phone numbers
      await loadPhoneNumbers();
    } catch (error: any) {
      throw error; // Let modal handle the error
    }
  };

  const handleProvision = async (request: ProvisionRequest) => {
    try {
      const response = await provisionPhoneNumber(request);

      toast({
        title: 'Phone number provisioned',
        description: `Successfully provisioned ${response.number.number}`
      });

      // Reload phone numbers
      await loadPhoneNumbers();
    } catch (error: any) {
      throw error; // Let modal handle the error
    }
  };

  const handleAssign = async (phoneId: string, assistantId: string) => {
    try {
      console.log('[PhoneNumbers] Assigning phone:', phoneId, 'to assistant:', assistantId);
      const response = await assignPhoneToAssistant(phoneId, assistantId);
      console.log('[PhoneNumbers] Assignment response:', response);

      // Update local state with the full updated number from backend
      setPhoneNumbers(prev =>
        prev.map(phone =>
          phone.id === phoneId ? response.number : phone
        )
      );

      toast({
        title: response.action === 'assigned' ? 'Phone assigned' : 'Phone unassigned',
        description: response.message
      });
    } catch (error: any) {
      console.error('[PhoneNumbers] Assignment error:', error);
      toast({
        title: 'Assignment failed',
        description: error.message,
        variant: 'destructive'
      });
    }
  };

  const handleDelete = async (phoneId: string) => {
    if (!confirm('Are you sure you want to delete this phone number?')) {
      return;
    }

    try {
      await deletePhoneNumber(phoneId);

      // Update local state
      setPhoneNumbers(prev => prev.filter(phone => phone.id !== phoneId));

      toast({
        title: 'Phone number deleted',
        description: 'Phone number has been removed'
      });
    } catch (error: any) {
      toast({
        title: 'Delete failed',
        description: error.message,
        variant: 'destructive'
      });
    }
  };

  const handleCopy = (number: string) => {
    navigator.clipboard.writeText(number);
    setCopiedNumber(number);
    setTimeout(() => setCopiedNumber(null), 2000);

    toast({
      title: 'Copied',
      description: 'Phone number copied to clipboard'
    });
  };

  const handleTestCall = (phoneNumber: string) => {
    // Find the phone object
    const phone = phoneNumbers.find(p => p.number === phoneNumber);
    if (phone) {
      setSelectedPhoneForTest(phone);
      setShowTestCallModal(true);
    } else {
      toast({
        title: 'Phone not found',
        description: 'Could not find phone number details',
        variant: 'destructive'
      });
    }
  };

  const handleAddCredit = (phone: PhoneNumber) => {
    setSelectedPhoneForCredit(phone);
    setShowAddCreditModal(true);
  };

  const handleViewDetails = (phone: PhoneNumber) => {
    setSelectedPhoneForStats(phone);
    setShowCDRStatsModal(true);
  };

  // Calculate stats
  const stats = {
    total: phoneNumbers.length,
    active: phoneNumbers.filter(p => p.status === 'active').length,
    countries: new Set(phoneNumbers.map(p => p.country)).size,
    monthlyСost: phoneNumbers.reduce((sum, p) => sum + (p.monthly_cost || 0), 0)
  };

  return (
    <div className="flex h-screen bg-background text-foreground">
      <DashboardSidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-card border-b border-border">
          <div className="px-4 lg:px-6 py-4">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-bold">Phone Numbers</h1>
                <p className="mt-1 text-sm text-muted-foreground">
                  Manage phone numbers and assign them to voice assistants
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowImportModal(true)}
                  className="inline-flex items-center px-4 py-2 border border-border rounded-md text-sm font-medium hover:bg-accent transition-colors"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Import
                </button>
                <button
                  onClick={() => setShowProvisionModal(true)}
                  className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Get Number
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="mt-4 border-b border-border">
              <div className="flex gap-4">
                <button
                  onClick={() => setActiveTab('phones')}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'phones'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Phone Numbers
                </button>
                <button
                  onClick={() => setActiveTab('cost-monitoring')}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'cost-monitoring'
                      ? 'border-primary text-primary'
                      : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Cost Monitoring
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards - Only show for phones tab */}
        {activeTab === 'phones' && (
          <div className="bg-background border-b border-border">
            <div className="px-4 lg:px-6 py-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center">
                  <Phone className="h-8 w-8 text-muted-foreground" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground">Total Numbers</p>
                    <p className="text-2xl font-semibold">{stats.total}</p>
                  </div>
                </div>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center">
                  <Check className="h-8 w-8 text-green-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground">Active</p>
                    <p className="text-2xl font-semibold">{stats.active}</p>
                  </div>
                </div>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center">
                  <Globe className="h-8 w-8 text-primary" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground">Countries</p>
                    <p className="text-2xl font-semibold">{stats.countries}</p>
                  </div>
                </div>
              </div>

              <div className="bg-card border border-border rounded-lg p-4">
                <div className="flex items-center">
                  <Zap className="h-8 w-8 text-yellow-500" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-muted-foreground">Monthly Cost</p>
                    <p className="text-2xl font-semibold">${stats.monthlyСost.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        )}

        {/* Main Content */}
        <div className="flex-1 overflow-auto p-4 lg:p-6">
          {activeTab === 'phones' ? (
            isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  <p className="mt-2 text-sm text-muted-foreground">Loading phone numbers...</p>
                </div>
              </div>
            ) : (
              <PhoneNumbersList
                phoneNumbers={phoneNumbers}
                assistants={assistants}
                onAssign={handleAssign}
                onDelete={handleDelete}
                onCopy={handleCopy}
                onTestCall={handleTestCall}
                copiedNumber={copiedNumber}
              />
            )
          ) : (
            <VAPICostMonitoring
              onAddCredit={handleAddCredit}
              onViewDetails={handleViewDetails}
              refreshTrigger={costMonitoringRefresh}
            />
          )}
        </div>
      </div>

      {/* Modals */}
      <ImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImport={handleImport}
      />

      <ProvisionModal
        isOpen={showProvisionModal}
        onClose={() => setShowProvisionModal(false)}
        onProvision={handleProvision}
      />

      <TestCallModal
        isOpen={showTestCallModal}
        onClose={() => {
          setShowTestCallModal(false);
          setSelectedPhoneForTest(null);
        }}
        phone={selectedPhoneForTest || undefined}
        assistants={assistants}
      />

      <AddCreditModal
        isOpen={showAddCreditModal}
        onClose={() => {
          setShowAddCreditModal(false);
          setSelectedPhoneForCredit(null);
        }}
        phone={selectedPhoneForCredit}
        onSuccess={() => {
          // Reload phone numbers and trigger cost monitoring refresh
          loadPhoneNumbers();
          setCostMonitoringRefresh(prev => prev + 1);
        }}
      />

      <CDRStatsModal
        isOpen={showCDRStatsModal}
        onClose={() => {
          setShowCDRStatsModal(false);
          setSelectedPhoneForStats(null);
        }}
        phoneNumber={selectedPhoneForStats?.number || ''}
        phoneName={selectedPhoneForStats?.name}
      />
    </div>
  );
};

export default PhoneNumbers;
