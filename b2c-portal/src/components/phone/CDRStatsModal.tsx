/**
 * CDR Stats Modal Component
 * Displays detailed call statistics for a phone number
 */

import React, { useState, useEffect } from 'react';
import {
  X,
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  Clock,
  DollarSign,
  TrendingUp,
  Calendar,
  Users,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { api } from '@/lib/api-client';

interface CDRStats {
  success: boolean;
  phone_number: string;
  phone_id: string;
  period_days: number;
  summary: {
    total_calls: number;
    total_minutes: number;
    total_cost: number;
  };
  outbound_calls: Array<{
    number: string;
    direction: string;
    call_count: number;
    total_minutes: number;
    total_cost: number;
    last_call?: string;
  }>;
  inbound_calls: Array<{
    number: string;
    direction: string;
    call_count: number;
    total_minutes: number;
    total_cost: number;
    last_call?: string;
  }>;
  daily_usage: Array<{
    date: string;
    call_count: number;
    total_minutes: number;
    total_cost: number;
  }>;
  recent_calls: Array<{
    call_id: string;
    source: string;
    destination: string;
    direction: 'inbound' | 'outbound' | 'unknown';
    duration_seconds: number;
    disposition: string;
    cost: number;
    timestamp: string;
  }>;
  recent_calls_total: number;
  recent_calls_page: number;
  recent_calls_per_page: number;
  credit_balance: number;
  remaining_minutes: number;
}

interface CDRStatsModalProps {
  isOpen: boolean;
  onClose: () => void;
  phoneNumber: string;
  phoneName?: string;
}

export const CDRStatsModal: React.FC<CDRStatsModalProps> = ({
  isOpen,
  onClose,
  phoneNumber,
  phoneName
}) => {
  const [stats, setStats] = useState<CDRStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  const fetchStats = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<CDRStats>(`/asterisk/cdr/stats/${encodeURIComponent(phoneNumber)}?days=${days}`);
      setStats(response);
    } catch (err: any) {
      setError(err.message || 'Failed to load CDR stats');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && phoneNumber) {
      fetchStats();
    }
  }, [isOpen, phoneNumber, days]);

  if (!isOpen) return null;

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    if (mins < 60) return `${mins}m ${secs}s`;
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    return `${hours}h ${remainingMins}m`;
  };

  const formatMinutes = (minutes: number): string => {
    if (minutes < 1) return `${Math.round(minutes * 60)}s`;
    if (minutes < 60) return `${minutes.toFixed(1)}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMins = Math.round(minutes % 60);
    return `${hours}h ${remainingMins}m`;
  };

  // Helper to get total values from stats
  const getTotalCalls = () => stats?.summary?.total_calls || 0;
  const getTotalMinutes = () => stats?.summary?.total_minutes || 0;
  const getTotalCost = () => stats?.summary?.total_cost || 0;
  const getTotalBillsec = () => (stats?.summary?.total_minutes || 0) * 60;

  const formatDateTime = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const getDispositionColor = (disposition: string): string => {
    switch (disposition?.toUpperCase()) {
      case 'ANSWERED':
        return 'text-green-600 bg-green-100';
      case 'NO ANSWER':
        return 'text-yellow-600 bg-yellow-100';
      case 'BUSY':
        return 'text-orange-600 bg-orange-100';
      case 'FAILED':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop */}
        <div className="fixed inset-0 transition-opacity bg-black/50" onClick={onClose} />

        {/* Modal */}
        <div className="inline-block w-full max-w-4xl my-8 overflow-hidden text-left align-middle transition-all transform bg-background border border-border rounded-xl shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-border">
            <div className="flex items-center gap-3">
              <Phone className="w-5 h-5 text-primary" />
              <div>
                <h2 className="text-lg font-semibold">Call Statistics</h2>
                <p className="text-sm text-muted-foreground">{phoneNumber}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="px-3 py-1 text-sm border border-border rounded-md bg-background"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
              </select>
              <button
                onClick={fetchStats}
                className="p-2 hover:bg-accent rounded-md"
                title="Refresh"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <button onClick={onClose} className="p-2 hover:bg-accent rounded-md">
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  <p className="mt-2 text-sm text-muted-foreground">Loading call statistics...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex flex-col items-center justify-center h-64">
                <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
                <p className="text-lg font-medium text-red-500">{error}</p>
                <button
                  onClick={fetchStats}
                  className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  Retry
                </button>
              </div>
            ) : stats ? (
              <div className="space-y-6">
                {/* Summary Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Total Calls</p>
                        <p className="text-2xl font-bold mt-1">{getTotalCalls()}</p>
                      </div>
                      <Phone className="h-8 w-8 text-blue-500" />
                    </div>
                  </div>

                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Total Duration</p>
                        <p className="text-2xl font-bold mt-1">{formatMinutes(getTotalMinutes())}</p>
                      </div>
                      <Clock className="h-8 w-8 text-green-500" />
                    </div>
                  </div>

                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Total Cost</p>
                        <p className="text-2xl font-bold mt-1">GHC {getTotalCost().toFixed(2)}</p>
                      </div>
                      <DollarSign className="h-8 w-8 text-purple-500" />
                    </div>
                  </div>

                  <div className="bg-card border border-border rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Avg Call</p>
                        <p className="text-2xl font-bold mt-1">
                          {getTotalCalls() > 0
                            ? formatMinutes(getTotalMinutes() / getTotalCalls())
                            : '0s'}
                        </p>
                      </div>
                      <TrendingUp className="h-8 w-8 text-orange-500" />
                    </div>
                  </div>
                </div>

                {/* Outbound Calls Breakdown */}
                {stats.outbound_calls && stats.outbound_calls.length > 0 && (
                  <div>
                    <h3 className="text-md font-semibold mb-3 flex items-center gap-2">
                      <PhoneOutgoing className="w-4 h-4 text-blue-500" />
                      Outbound Calls (Numbers Called)
                    </h3>
                    <div className="bg-card border border-border rounded-lg overflow-hidden">
                      <table className="w-full">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase">Destination</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Calls</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Duration</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Cost</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {stats.outbound_calls.slice(0, 10).map((call, idx) => (
                            <tr key={idx} className="hover:bg-muted/50">
                              <td className="px-4 py-2 font-medium">{call.number}</td>
                              <td className="px-4 py-2 text-right">{call.call_count}</td>
                              <td className="px-4 py-2 text-right">{formatMinutes(call.total_minutes)}</td>
                              <td className="px-4 py-2 text-right text-green-600">GHC {call.total_cost.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Inbound Calls Breakdown */}
                {stats.inbound_calls && stats.inbound_calls.length > 0 && (
                  <div>
                    <h3 className="text-md font-semibold mb-3 flex items-center gap-2">
                      <PhoneIncoming className="w-4 h-4 text-green-500" />
                      Inbound Calls (Callers)
                    </h3>
                    <div className="bg-card border border-border rounded-lg overflow-hidden">
                      <table className="w-full">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase">Source</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Calls</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Duration</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Cost</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {stats.inbound_calls.slice(0, 10).map((call, idx) => (
                            <tr key={idx} className="hover:bg-muted/50">
                              <td className="px-4 py-2 font-medium">{call.number}</td>
                              <td className="px-4 py-2 text-right">{call.call_count}</td>
                              <td className="px-4 py-2 text-right">{formatMinutes(call.total_minutes)}</td>
                              <td className="px-4 py-2 text-right text-green-600">GHC {call.total_cost.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Daily Usage */}
                {stats.daily_usage && stats.daily_usage.length > 0 && (
                  <div>
                    <h3 className="text-md font-semibold mb-3 flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-purple-500" />
                      Daily Usage
                    </h3>
                    <div className="bg-card border border-border rounded-lg overflow-hidden">
                      <table className="w-full">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase">Date</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Calls</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Duration</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Cost</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {stats.daily_usage.slice(0, 14).map((day, idx) => (
                            <tr key={idx} className="hover:bg-muted/50">
                              <td className="px-4 py-2 font-medium">{day.date}</td>
                              <td className="px-4 py-2 text-right">{day.call_count}</td>
                              <td className="px-4 py-2 text-right">{formatMinutes(day.total_minutes)}</td>
                              <td className="px-4 py-2 text-right text-green-600">GHC {day.total_cost.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Recent Calls */}
                {stats.recent_calls && stats.recent_calls.length > 0 && (
                  <div>
                    <h3 className="text-md font-semibold mb-3 flex items-center gap-2">
                      <Clock className="w-4 h-4 text-blue-500" />
                      Recent Calls
                      {stats.recent_calls_total > 0 && (
                        <span className="text-xs text-muted-foreground font-normal">
                          ({stats.recent_calls_total} total)
                        </span>
                      )}
                    </h3>
                    <div className="bg-card border border-border rounded-lg overflow-hidden">
                      <table className="w-full">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase">Time</th>
                            <th className="px-4 py-2 text-center text-xs font-medium text-muted-foreground uppercase">Dir</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase">From</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-muted-foreground uppercase">To</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Duration</th>
                            <th className="px-4 py-2 text-center text-xs font-medium text-muted-foreground uppercase">Status</th>
                            <th className="px-4 py-2 text-right text-xs font-medium text-muted-foreground uppercase">Cost</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                          {stats.recent_calls.slice(0, 20).map((call, idx) => (
                            <tr key={idx} className="hover:bg-muted/50">
                              <td className="px-4 py-2 text-sm">{call.timestamp ? formatDateTime(call.timestamp) : '-'}</td>
                              <td className="px-4 py-2 text-center">
                                {call.direction === 'inbound' ? (
                                  <PhoneIncoming className="w-4 h-4 text-green-500 inline" title="Inbound" />
                                ) : call.direction === 'outbound' ? (
                                  <PhoneOutgoing className="w-4 h-4 text-blue-500 inline" title="Outbound" />
                                ) : (
                                  <Phone className="w-4 h-4 text-gray-400 inline" title="Unknown" />
                                )}
                              </td>
                              <td className="px-4 py-2 font-medium text-sm">{call.source}</td>
                              <td className="px-4 py-2 font-medium text-sm">{call.destination}</td>
                              <td className="px-4 py-2 text-right text-sm">{formatDuration(call.duration_seconds)}</td>
                              <td className="px-4 py-2 text-center">
                                <span className={`px-2 py-1 text-xs rounded-full ${getDispositionColor(call.disposition)}`}>
                                  {call.disposition}
                                </span>
                              </td>
                              <td className="px-4 py-2 text-right text-sm text-green-600">
                                {call.cost ? `GHC ${call.cost.toFixed(2)}` : '-'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* No data message */}
                {getTotalCalls() === 0 && (
                  <div className="text-center py-12">
                    <Phone className="mx-auto h-12 w-12 text-muted-foreground" />
                    <p className="mt-4 text-lg font-medium">No call records found</p>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Call records will appear here once calls are made through this number
                    </p>
                  </div>
                )}

                {/* Credit Balance Info */}
                {stats.credit_balance !== undefined && (
                  <div className="bg-card border border-border rounded-lg p-4 mt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Credit Balance</p>
                        <p className="text-xl font-bold mt-1">GHC {stats.credit_balance.toFixed(2)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-muted-foreground">Remaining Minutes</p>
                        <p className="text-xl font-bold mt-1 text-primary">{stats.remaining_minutes.toFixed(1)} min</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CDRStatsModal;
