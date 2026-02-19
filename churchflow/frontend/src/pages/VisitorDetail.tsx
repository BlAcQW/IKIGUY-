/**
 * Visitor Detail Page
 *
 * Comprehensive view of visitor information including:
 * - Contact details and profile
 * - Journey stage history
 * - Visit tracking
 * - Cell/Zone assignments
 * - Enrichment history (audit trail)
 * - Life events
 *
 * URL: /visitors/:id
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  User,
  Phone,
  Mail,
  Calendar,
  MapPin,
  Users,
  TrendingUp,
  Edit,
  Send,
  Heart,
  Briefcase,
  Home,
  Clock,
  Activity,
  AlertCircle,
  Loader,
  CheckCircle,
  History,
  UserCheck,
  Building,
  X,
  } from 'lucide-react';
import { visitorApi, journeyApi, enrichmentApi, type Visitor, type StageTransition, type DataEnrichment, type LifeEvent } from '../services/visitorApi';
import { format, formatDistanceToNow } from 'date-fns';

export default function VisitorDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [visitor, setVisitor] = useState<Visitor | null>(null);
  const [journeyHistory, setJourneyHistory] = useState<StageTransition[]>([]);
  const [enrichmentHistory, setEnrichmentHistory] = useState<DataEnrichment[]>([]);
  const [lifeEvents, setLifeEvents] = useState<LifeEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'journey' | 'enrichment' | 'events' | 'departments'>('overview');

  // Department assignment state
  const [showDepartmentModal, setShowDepartmentModal] = useState(false);
  const [assigningDepartment, setAssigningDepartment] = useState(false);

  // Member transition state
  const [showTransitionModal, setShowTransitionModal] = useState(false);
  const [transitioning, setTransitioning] = useState(false);
  const [branches, setBranches] = useState<any[]>([]);
  const [selectedBranch, setSelectedBranch] = useState('');

  useEffect(() => {
    if (id) {
      loadVisitorData();
    }
  }, [id]);

  const loadVisitorData = async () => {
    if (!id) return;

    setIsLoading(true);
    setError(null);

    try {
      // Load all data in parallel
      const [visitorData, journeyData, enrichmentData, lifeEventsData] = await Promise.all([
        visitorApi.getVisitorById(id),
        journeyApi.getJourneyHistory(id).catch(() => ({ stage_history: [] })),
        enrichmentApi.getEnrichmentHistory(id).catch(() => ({ enrichment_history: [] })),
        enrichmentApi.getLifeEvents(id).catch(() => ({ life_events: [] })),
      ]);

      setVisitor(visitorData);
      setJourneyHistory(journeyData.stage_history || visitorData.stage_history || []);
      setEnrichmentHistory(enrichmentData.enrichment_history || visitorData.enrichment_history || []);
      setLifeEvents(lifeEventsData.life_events || visitorData.life_events || []);
    } catch (err: any) {
      console.error('Failed to load visitor:', err);
      setError(err.response?.data?.detail || 'Failed to load visitor details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendWelcome = async () => {
    if (!id) return;

    try {
      await visitorApi.resendWelcome(id);
      alert('Welcome message sent successfully!');
    } catch (err: any) {
      console.error('Failed to resend welcome:', err);
      alert(err.response?.data?.detail || 'Failed to send welcome message');
    }
  };

  const handleAssignDepartment = async (departmentName: string) => {
    if (!id) return;

    setAssigningDepartment(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/users/${id}/departments`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          department_name: departmentName,
          action: 'assign'
        })
      });

      if (response.ok) {
        alert('Department assigned successfully!');
        await loadVisitorData(); // Reload to show updated department status
      } else {
        const data = await response.json();
        alert(data.detail || 'Failed to assign department');
      }
    } catch (err) {
      console.error('Failed to assign department:', err);
      alert('Network error. Please try again.');
    } finally {
      setAssigningDepartment(false);
    }
  };

  const handleTransitionToMember = async () => {
    if (!id || !selectedBranch) {
      alert('Please select a branch');
      return;
    }

    setTransitioning(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/users/${id}/transition-to-member`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          branch_id: selectedBranch
        })
      });

      if (response.ok) {
        alert('Visitor successfully transitioned to member!');
        setShowTransitionModal(false);
        await loadVisitorData(); // Reload to show updated member status
        navigate(`/visitors/${id}`); // Refresh page
      } else {
        const data = await response.json();
        alert(data.detail || 'Failed to transition to member');
      }
    } catch (err) {
      console.error('Failed to transition:', err);
      alert('Network error. Please try again.');
    } finally {
      setTransitioning(false);
    }
  };

  const fetchBranches = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const orgId = localStorage.getItem('current_organization_id');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/organizations/${orgId}/branches`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setBranches(data.branches || []);
      }
    } catch (err) {
      console.error('Failed to fetch branches:', err);
    }
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'N/A';
    try {
      return format(new Date(dateString), 'MMM d, yyyy h:mm a');
    } catch {
      return dateString;
    }
  };

  const formatRelativeDate = (dateString: string | undefined) => {
    if (!dateString) return 'N/A';
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return dateString;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      visitor: 'bg-blue-100 text-blue-800',
      active_member: 'bg-green-100 text-green-800',
      inactive_member: 'bg-gray-100 text-gray-800',
      alumni: 'bg-purple-100 text-purple-800',
    };
    return styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800';
  };

  const getStatusLabel = (status: string) => {
    const labels = {
      visitor: 'Visitor',
      active_member: 'Active Member',
      inactive_member: 'Inactive',
      alumni: 'Alumni',
    };
    return labels[status as keyof typeof labels] || status;
  };

  const getJourneyIcon = (type: string) => {
    switch (type) {
      case 'spiritual':
        return <Heart className="w-4 h-4" />;
      case 'cell':
        return <Users className="w-4 h-4" />;
      case 'ministry':
        return <Briefcase className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader className="w-8 h-8 text-purple-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading visitor details...</p>
        </div>
      </div>
    );
  }

  if (error || !visitor) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Error Loading Visitor</h2>
          <p className="text-gray-600 mb-6">{error || 'Visitor not found'}</p>
          <button
            onClick={() => navigate('/visitors')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            Back to Visitors
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={() => navigate('/visitors')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">
                {visitor.name || visitor.full_name || 'Unnamed Visitor'}
              </h1>
              <div className="flex items-center gap-3 mt-2">
                <span className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${getStatusBadge(visitor.member_status)}`}>
                  {getStatusLabel(visitor.member_status)}
                </span>
                {visitor.current_spiritual_stage && (
                  <span className="text-sm text-gray-600">
                    Stage: <span className="font-medium capitalize">{visitor.current_spiritual_stage.replace(/_/g, ' ')}</span>
                  </span>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleResendWelcome}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium flex items-center gap-2"
              >
                <Send className="w-4 h-4" />
                Resend Welcome
              </button>
              {visitor.member_status === 'visitor' && (
                <button
                  onClick={() => {
                    fetchBranches();
                    setShowTransitionModal(true);
                  }}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center gap-2"
                >
                  <UserCheck className="w-4 h-4" />
                  Make Member
                </button>
              )}
              <button
                onClick={() => navigate(`/visitors/${id}/edit`)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center gap-2"
              >
                <Edit className="w-4 h-4" />
                Edit Profile
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Profile Info */}
          <div className="lg:col-span-1 space-y-6">
            {/* Contact Information */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h2>
              <div className="space-y-3">
                <div className="flex items-center gap-3 text-sm">
                  <Phone className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <span className="text-gray-900">{visitor.phone}</span>
                </div>
                {visitor.email && (
                  <div className="flex items-center gap-3 text-sm">
                    <Mail className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <span className="text-gray-900">{visitor.email}</span>
                  </div>
                )}
                {visitor.address && (
                  <div className="flex items-start gap-3 text-sm">
                    <Home className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-900">{visitor.address}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Personal Details */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Personal Details</h2>
              <div className="space-y-3">
                {visitor.gender && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Gender:</span>
                    <span className="text-gray-900 capitalize">{visitor.gender}</span>
                  </div>
                )}
                {visitor.date_of_birth && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Date of Birth:</span>
                    <span className="text-gray-900">{formatDate(visitor.date_of_birth)}</span>
                  </div>
                )}
                {visitor.marital_status && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Marital Status:</span>
                    <span className="text-gray-900 capitalize">{visitor.marital_status}</span>
                  </div>
                )}
                {visitor.occupation && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Occupation:</span>
                    <span className="text-gray-900">{visitor.occupation}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Visit Statistics */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Visit Statistics</h2>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Total Visits:</span>
                  <span className="text-gray-900 font-semibold">{visitor.visit_count}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">First Visit:</span>
                  <span className="text-gray-900">{formatRelativeDate(visitor.first_visit_date)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Last Visit:</span>
                  <span className="text-gray-900">{formatRelativeDate(visitor.last_visit_date)}</span>
                </div>
                {visitor.first_visit_source && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Source:</span>
                    <span className="text-gray-900">{visitor.first_visit_source}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column - Tabs */}
          <div className="lg:col-span-2">
            {/* Tab Navigation */}
            <div className="bg-white rounded-t-lg border-b border-gray-200">
              <div className="flex space-x-8 px-6">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'overview'
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Overview
                </button>
                <button
                  onClick={() => setActiveTab('journey')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                    activeTab === 'journey'
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <TrendingUp className="w-4 h-4" />
                  Journey ({journeyHistory.length})
                </button>
                <button
                  onClick={() => setActiveTab('enrichment')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                    activeTab === 'enrichment'
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <History className="w-4 h-4" />
                  Enrichment ({enrichmentHistory.length})
                </button>
                <button
                  onClick={() => setActiveTab('events')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                    activeTab === 'events'
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Calendar className="w-4 h-4" />
                  Life Events ({lifeEvents.length})
                </button>
                <button
                  onClick={() => setActiveTab('departments')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                    activeTab === 'departments'
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Briefcase className="w-4 h-4" />
                  Departments
                </button>
              </div>
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-b-lg shadow-sm border border-t-0 border-gray-200 p-6">
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Journey Stages</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {visitor.current_spiritual_stage && (
                        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                          <div className="flex items-center gap-2 text-purple-700 mb-2">
                            <Heart className="w-4 h-4" />
                            <span className="text-xs font-semibold uppercase">Spiritual</span>
                          </div>
                          <p className="text-sm font-medium text-gray-900 capitalize">
                            {visitor.current_spiritual_stage.replace(/_/g, ' ')}
                          </p>
                        </div>
                      )}
                      {visitor.current_cell_stage && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <div className="flex items-center gap-2 text-green-700 mb-2">
                            <Users className="w-4 h-4" />
                            <span className="text-xs font-semibold uppercase">Cell</span>
                          </div>
                          <p className="text-sm font-medium text-gray-900 capitalize">
                            {visitor.current_cell_stage.replace(/_/g, ' ')}
                          </p>
                        </div>
                      )}
                      {visitor.current_ministry_stage && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <div className="flex items-center gap-2 text-blue-700 mb-2">
                            <Briefcase className="w-4 h-4" />
                            <span className="text-xs font-semibold uppercase">Ministry</span>
                          </div>
                          <p className="text-sm font-medium text-gray-900 capitalize">
                            {visitor.current_ministry_stage.replace(/_/g, ' ')}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Assignments</h3>
                    <div className="space-y-3">
                      {visitor.cell_group_id && (
                        <div className="flex items-center justify-between py-2 border-b border-gray-100">
                          <span className="text-sm text-gray-500">Cell Group:</span>
                          <span className="text-sm font-medium text-gray-900">{visitor.cell_group_id}</span>
                        </div>
                      )}
                      {visitor.assigned_cell_leader_id && (
                        <div className="flex items-center justify-between py-2 border-b border-gray-100">
                          <span className="text-sm text-gray-500">Cell Leader:</span>
                          <span className="text-sm font-medium text-gray-900">{visitor.assigned_cell_leader_id}</span>
                        </div>
                      )}
                      {visitor.zone_id && (
                        <div className="flex items-center justify-between py-2">
                          <span className="text-sm text-gray-500">Zone:</span>
                          <span className="text-sm font-medium text-gray-900">{visitor.zone_id}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Journey History Tab */}
              {activeTab === 'journey' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Journey Progression</h3>
                  {journeyHistory.length === 0 ? (
                    <div className="text-center py-12">
                      <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">No journey transitions recorded yet</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {journeyHistory.map((transition, index) => (
                        <div key={index} className="flex gap-4 pb-4 border-b border-gray-100 last:border-0">
                          <div className="flex-shrink-0 mt-1">
                            <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">
                              {getJourneyIcon(transition.journey_type)}
                            </div>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs font-semibold text-gray-500 uppercase">{transition.journey_type}</span>
                              <span className="text-xs text-gray-500">{formatRelativeDate(transition.transitioned_at)}</span>
                            </div>
                            <p className="text-sm font-medium text-gray-900">
                              {transition.previous_stage && (
                                <span className="text-gray-500 capitalize">{transition.previous_stage.replace(/_/g, ' ')} → </span>
                              )}
                              <span className="capitalize">{transition.new_stage.replace(/_/g, ' ')}</span>
                            </p>
                            {transition.notes && (
                              <p className="text-sm text-gray-600 mt-1">{transition.notes}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Enrichment History Tab */}
              {activeTab === 'enrichment' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Enrichment History</h3>
                  {enrichmentHistory.length === 0 ? (
                    <div className="text-center py-12">
                      <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">No data enrichments recorded yet</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {enrichmentHistory.map((enrichment, index) => (
                        <div key={index} className="pb-4 border-b border-gray-100 last:border-0">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium text-gray-900 capitalize">{enrichment.field_name.replace(/_/g, ' ')}</span>
                            <span className="text-xs text-gray-500">{formatRelativeDate(enrichment.enriched_at)}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                            {enrichment.previous_value !== undefined && enrichment.previous_value !== null && (
                              <>
                                <span className="line-through">{String(enrichment.previous_value)}</span>
                                <span>→</span>
                              </>
                            )}
                            <span className="font-medium text-gray-900">{String(enrichment.new_value)}</span>
                          </div>
                          <div className="text-xs text-gray-500">
                            By: {enrichment.enriched_by_role}
                            {enrichment.notes && <span className="ml-2">• {enrichment.notes}</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Life Events Tab */}
              {activeTab === 'events' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Life Events</h3>
                  {lifeEvents.length === 0 ? (
                    <div className="text-center py-12">
                      <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">No life events recorded yet</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {lifeEvents.map((event, index) => (
                        <div key={index} className="pb-4 border-b border-gray-100 last:border-0">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 capitalize">
                                {event.event_type.replace(/_/g, ' ')}
                              </span>
                              {event.requires_followup && (
                                <span className={`inline-block px-2 py-1 text-xs font-semibold rounded-full ${
                                  event.followup_completed ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'
                                }`}>
                                  {event.followup_completed ? 'Follow-up Complete' : 'Needs Follow-up'}
                                </span>
                              )}
                            </div>
                            <span className="text-xs text-gray-500">{formatDate(event.event_date)}</span>
                          </div>
                          <p className="text-sm text-gray-900 mb-1">{event.description}</p>
                          <p className="text-xs text-gray-500">Recorded {formatRelativeDate(event.recorded_at)}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Departments Tab */}
              {activeTab === 'departments' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Department Interests & Assignments</h3>

                  {/* Interested Departments */}
                  {visitor.departments && visitor.departments.some((d: any) => d.status === 'interested') && (
                    <div className="mb-6">
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Interested In:</h4>
                      <div className="grid grid-cols-2 gap-3">
                        {visitor.departments
                          .filter((d: any) => d.status === 'interested')
                          .map((dept: any, index: number) => (
                            <div key={index} className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                              <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-900 capitalize">
                                  {dept.name?.replace(/_/g, ' ')}
                                </span>
                                <button
                                  onClick={() => handleAssignDepartment(dept.name)}
                                  disabled={assigningDepartment}
                                  className="text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                                >
                                  Assign
                                </button>
                              </div>
                              <p className="text-xs text-gray-500 mt-1">
                                Expressed interest {formatRelativeDate(dept.created_at)}
                              </p>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Assigned Departments */}
                  {visitor.departments && visitor.departments.some((d: any) => d.status === 'assigned') && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-3">Assigned To:</h4>
                      <div className="grid grid-cols-2 gap-3">
                        {visitor.departments
                          .filter((d: any) => d.status === 'assigned')
                          .map((dept: any, index: number) => (
                            <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-3">
                              <div className="flex items-center gap-2 mb-1">
                                <CheckCircle className="w-4 h-4 text-green-600" />
                                <span className="text-sm font-medium text-gray-900 capitalize">
                                  {dept.name?.replace(/_/g, ' ')}
                                </span>
                              </div>
                              <p className="text-xs text-gray-500">
                                Assigned {formatRelativeDate(dept.assigned_at)}
                              </p>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* No Departments */}
                  {(!visitor.departments || visitor.departments.length === 0) && (
                    <div className="text-center py-12">
                      <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">No department interests or assignments yet</p>
                      <p className="text-sm text-gray-500 mt-2">
                        Department interests are captured during visitor registration
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Transition to Member Modal */}
        {showTransitionModal && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl max-w-md w-full">
              <div className="bg-gradient-to-r from-green-600 to-green-700 px-6 py-4 flex items-center justify-between rounded-t-2xl">
                <div className="flex items-center gap-3">
                  <UserCheck className="w-6 h-6 text-white" />
                  <h2 className="text-xl font-semibold text-white">Transition to Member</h2>
                </div>
                <button
                  onClick={() => setShowTransitionModal(false)}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-white" />
                </button>
              </div>

              <div className="p-6">
                <p className="text-sm text-gray-600 mb-4">
                  Convert <span className="font-semibold">{visitor?.name || visitor?.full_name}</span> from a visitor to an active member.
                </p>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Branch <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedBranch}
                    onChange={(e) => setSelectedBranch(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="">-- Select a branch --</option>
                    {branches.map((branch) => (
                      <option key={branch.id} value={branch.id}>
                        {branch.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-6">
                  <p className="text-xs text-blue-800">
                    <strong>Note:</strong> This will change their status from "Visitor" to "Active Member" and assign them to the selected branch. This action can be reversed later if needed.
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setShowTransitionModal(false)}
                    disabled={transitioning}
                    className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleTransitionToMember}
                    disabled={!selectedBranch || transitioning}
                    className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {transitioning ? (
                      <>
                        <Loader className="w-5 h-5 animate-spin" />
                        <span>Processing...</span>
                      </>
                    ) : (
                      <span>Confirm Transition</span>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
