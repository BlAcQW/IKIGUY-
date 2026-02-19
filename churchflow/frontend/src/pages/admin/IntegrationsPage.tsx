/**
 * Integrations Page - Phase 7 Week 3-4
 *
 * Main page for managing external integrations
 */

import React, { useState, useEffect } from 'react';
import { useIntegrationDashboard, IntegrationType } from '../../hooks/useIntegrations';
import IntegrationDashboard from '../../components/admin/IntegrationDashboard';
import GoogleCalendarSettings from '../../components/admin/GoogleCalendarSettings';
import ZapierWebhookSettings from '../../components/admin/ZapierWebhookSettings';

const IntegrationsPage: React.FC = () => {
  const [token, setToken] = useState<string | null>(null);
  const [organizationId, setOrganizationId] = useState<string | null>(null);
  const [activeModal, setActiveModal] = useState<IntegrationType | null>(null);

  useEffect(() => {
    const accessToken = localStorage.getItem('access_token');
    const orgId = localStorage.getItem('current_organization_id');
    setToken(accessToken);
    setOrganizationId(orgId);
  }, []);

  const {
    data: dashboard,
    isLoading,
    error,
    refetch,
  } = useIntegrationDashboard(token, organizationId);

  const handleConfigure = (integrationType: IntegrationType) => {
    setActiveModal(integrationType);
  };

  const handleCloseModal = () => {
    setActiveModal(null);
    refetch(); // Refresh dashboard after closing modal
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-64 bg-gray-200 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-900 mb-2">Error Loading Integrations</h2>
          <p className="text-red-700 mb-4">{error.message}</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // No data state
  if (!dashboard) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <p className="text-gray-600">No integration data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Integrations</h1>
        <p className="text-gray-600 mt-1">
          Connect ChurchFlow with external services to automate workflows
        </p>
      </div>

      {/* Dashboard */}
      <IntegrationDashboard dashboard={dashboard} onConfigure={handleConfigure} />

      {/* Modals */}
      {activeModal === 'google_calendar' && token && organizationId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <GoogleCalendarSettings
              token={token}
              organizationId={organizationId}
              onClose={handleCloseModal}
            />
          </div>
        </div>
      )}

      {activeModal === 'zapier' && token && organizationId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <ZapierWebhookSettings
              token={token}
              organizationId={organizationId}
              onClose={handleCloseModal}
            />
          </div>
        </div>
      )}

      {activeModal === 'email_campaign' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Email Campaign Integration</h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <p className="text-gray-600 mb-4">
              Email campaign integration is coming soon!
            </p>
            <button
              onClick={handleCloseModal}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      {activeModal === 'stripe_billing' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Stripe Billing Integration</h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <p className="text-gray-600 mb-4">
              Stripe billing integration is coming soon!
            </p>
            <button
              onClick={handleCloseModal}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationsPage;
