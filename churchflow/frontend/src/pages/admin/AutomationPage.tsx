/**
 * Automation Page - Phase 7 Week 5-6
 *
 * Main page for managing automated workflows and reminder sequences
 */

import React, { useState, useEffect } from 'react';
import { encodeHeaderValue } from '../../lib/header-utils';
import {
  BoltIcon,
  CheckCircleIcon,
  PauseCircleIcon,
  ClockIcon,
  ChartBarIcon,
  PlusIcon,
  PlayCircleIcon,
  TrashIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';
import {
  useAutomationDashboard,
  useWorkflows,
  useCreateDefaultEventReminderWorkflow,
  useUpdateWorkflowStatus,
  useDeleteWorkflow,
  AutomationWorkflow,
  AutomationStatus,
} from '../../hooks/useAutomation';

const AutomationPage: React.FC = () => {
  const [token, setToken] = useState<string | null>(null);
  const [organizationId, setOrganizationId] = useState<string | null>(null);
  const [selectedConference, setSelectedConference] = useState<string>('');
  const [conferences, setConferences] = useState<any[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    const accessToken = localStorage.getItem('access_token');
    const orgId = localStorage.getItem('current_organization_id');
    setToken(accessToken);
    setOrganizationId(orgId);

    // Fetch conferences for workflow creation
    if (accessToken && orgId) {
      fetchConferences(accessToken, orgId);
    }
  }, []);

  const fetchConferences = async (token: string, orgId: string) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'https://churchflow-api.ailabsafrica.com/api/v1'}/conferences`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Organization-ID': encodeHeaderValue(orgId) || '',
          },
        }
      );
      const data = await response.json();
      setConferences(data);
    } catch (error) {
      console.error('Error fetching conferences:', error);
    }
  };

  const {
    data: dashboard,
    isLoading: isDashboardLoading,
    error: dashboardError,
    refetch: refetchDashboard,
  } = useAutomationDashboard(token, organizationId);

  const {
    data: workflows,
    isLoading: isWorkflowsLoading,
    error: workflowsError,
    refetch: refetchWorkflows,
  } = useWorkflows(token, organizationId);

  const createDefaultWorkflow = useCreateDefaultEventReminderWorkflow(token, organizationId);
  const updateStatus = useUpdateWorkflowStatus(token, organizationId);
  const deleteWorkflow = useDeleteWorkflow(token, organizationId);

  const handleCreateDefaultWorkflow = async () => {
    if (!selectedConference) {
      alert('Please select a conference');
      return;
    }

    try {
      await createDefaultWorkflow.mutateAsync(selectedConference);
      alert('Event reminder workflow created and scheduled successfully!');
      setShowCreateModal(false);
      setSelectedConference('');
    } catch (error: any) {
      alert(`Failed to create workflow: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handlePauseWorkflow = async (workflowId: string) => {
    try {
      await updateStatus.mutateAsync({ workflowId, status: 'paused' });
      alert('Workflow paused successfully');
    } catch (error: any) {
      alert(`Failed to pause workflow: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleActivateWorkflow = async (workflowId: string) => {
    try {
      await updateStatus.mutateAsync({ workflowId, status: 'active' });
      alert('Workflow activated successfully');
    } catch (error: any) {
      alert(`Failed to activate workflow: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteWorkflow = async (workflowId: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"? This will also delete all scheduled reminders.`)) {
      return;
    }

    try {
      await deleteWorkflow.mutateAsync(workflowId);
      alert('Workflow deleted successfully');
    } catch (error: any) {
      alert(`Failed to delete workflow: ${error.response?.data?.detail || error.message}`);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'paused':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-blue-100 text-blue-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
      case 'paused':
        return <PauseCircleIcon className="w-5 h-5 text-yellow-600" />;
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-600" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-600" />;
    }
  };

  // Loading state
  if (isDashboardLoading || isWorkflowsLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (dashboardError || workflowsError) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-900 mb-2">Error Loading Automation</h2>
          <p className="text-red-700 mb-4">
            {dashboardError?.message || workflowsError?.message || 'Unknown error'}
          </p>
          <button
            onClick={() => {
              refetchDashboard();
              refetchWorkflows();
            }}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <BoltIcon className="w-8 h-8 text-purple-600" />
            Automation & Workflows
          </h1>
          <p className="text-gray-600 mt-1">Automate reminders and streamline church operations</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          <PlusIcon className="w-5 h-5" />
          Create Workflow
        </button>
      </div>

      {/* Dashboard Statistics */}
      {dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {/* Total Workflows */}
          <div className="bg-white border rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm text-gray-600">Total Workflows</h3>
              <BoltIcon className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{dashboard.total_workflows}</p>
            <p className="text-sm text-gray-500 mt-1">
              {dashboard.active_workflows} active, {dashboard.paused_workflows} paused
            </p>
          </div>

          {/* Pending Reminders */}
          <div className="bg-white border rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm text-gray-600">Pending Reminders</h3>
              <ClockIcon className="w-5 h-5 text-yellow-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{dashboard.pending_reminders}</p>
            <p className="text-sm text-gray-500 mt-1">{dashboard.upcoming_reminders_24h} in next 24h</p>
          </div>

          {/* Success Rate */}
          <div className="bg-white border rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm text-gray-600">Success Rate (30d)</h3>
              <ChartBarIcon className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{(dashboard.success_rate * 100).toFixed(1)}%</p>
            <p className="text-sm text-gray-500 mt-1">
              {dashboard.successful_executions_30d} of {dashboard.total_executions_30d} successful
            </p>
          </div>

          {/* Total Executions */}
          <div className="bg-white border rounded-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm text-gray-600">Executions (30d)</h3>
              <CheckCircleIcon className="w-5 h-5 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{dashboard.total_executions_30d}</p>
            <p className="text-sm text-gray-500 mt-1">{dashboard.failed_executions_30d} failed</p>
          </div>
        </div>
      )}

      {/* Workflows List */}
      <div className="bg-white border rounded-lg">
        <div className="p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">All Workflows</h2>
          <p className="text-sm text-gray-600 mt-1">Manage your automation workflows</p>
        </div>

        {workflows && workflows.length > 0 ? (
          <div className="divide-y">
            {workflows.map((workflow) => (
              <div key={workflow._id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{workflow.name}</h3>
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(workflow.status)}`}>
                        {getStatusIcon(workflow.status)}
                        {workflow.status}
                      </span>
                    </div>
                    {workflow.description && <p className="text-sm text-gray-600 mb-3">{workflow.description}</p>}

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500">Type</p>
                        <p className="font-medium text-gray-900 capitalize">
                          {workflow.automation_type.replace('_', ' ')}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Executions</p>
                        <p className="font-medium text-gray-900">
                          {workflow.total_executions} ({workflow.successful_executions} successful)
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500">Last Execution</p>
                        <p className="font-medium text-gray-900">{formatDate(workflow.last_execution_at)}</p>
                      </div>
                      <div>
                        <p className="text-gray-500">Next Execution</p>
                        <p className="font-medium text-gray-900">{formatDate(workflow.next_execution_at)}</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    {workflow.status === 'active' ? (
                      <button
                        onClick={() => handlePauseWorkflow(workflow._id)}
                        disabled={updateStatus.isPending}
                        className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Pause workflow"
                      >
                        <PauseCircleIcon className="w-5 h-5" />
                      </button>
                    ) : workflow.status === 'paused' ? (
                      <button
                        onClick={() => handleActivateWorkflow(workflow._id)}
                        disabled={updateStatus.isPending}
                        className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Activate workflow"
                      >
                        <PlayCircleIcon className="w-5 h-5" />
                      </button>
                    ) : null}
                    <button
                      onClick={() => handleDeleteWorkflow(workflow._id, workflow.name)}
                      disabled={deleteWorkflow.isPending}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                      title="Delete workflow"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <BoltIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No workflows yet</h3>
            <p className="text-gray-600 mb-4">Create your first automation workflow to get started</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <PlusIcon className="w-5 h-5" />
              Create Workflow
            </button>
          </div>
        )}
      </div>

      {/* Create Workflow Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Create Event Reminder Workflow</h2>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>

            <p className="text-sm text-gray-600 mb-6">
              This will create a default workflow that sends reminders 7, 3, and 1 day before the conference.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Select Conference</label>
                <select
                  value={selectedConference}
                  onChange={(e) => setSelectedConference(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="">Choose a conference...</option>
                  {conferences.map((conf) => (
                    <option key={conf._id} value={conf._id}>
                      {conf.name} - {new Date(conf.start_date).toLocaleDateString()}
                    </option>
                  ))}
                </select>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h4 className="font-semibold text-purple-900 mb-2">Default Reminders:</h4>
                <ul className="space-y-1 text-sm text-purple-800">
                  <li>📅 7 days before: "Coming up next week!"</li>
                  <li>📅 3 days before: "This weekend!"</li>
                  <li>📅 1 day before: "Tomorrow! Save your QR code"</li>
                </ul>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateDefaultWorkflow}
                  disabled={createDefaultWorkflow.isPending || !selectedConference}
                  className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                >
                  {createDefaultWorkflow.isPending ? 'Creating...' : 'Create Workflow'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutomationPage;
