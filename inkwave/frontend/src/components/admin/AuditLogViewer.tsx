/**
 * AuditLogViewer Component
 *
 * Displays audit logs of admin moderation actions with filtering.
 * Shows who did what, when, and why.
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Search,
  Filter,
  Download,
  Loader,
  EyeOff,
  Eye,
  Trash2,
  Calendar,
  User,
  FileText,
} from 'lucide-react';
import { api } from '../../lib/api';
import toast from 'react-hot-toast';
import type { AuditLogEntry } from '../../types/book';

interface AuditLogViewerProps {
  bookId?: string;
  adminId?: string;
  limit?: number;
}

export default function AuditLogViewer({
  bookId,
  adminId,
  limit = 50,
}: AuditLogViewerProps) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadAuditLogs();
  }, [bookId, adminId, actionFilter]);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      const response = await api.admin.getAuditLog({
        book_id: bookId,
        admin_id: adminId,
        action: actionFilter || undefined,
        limit,
      });
      setLogs(response.data.logs || []);
    } catch (error: any) {
      console.error('Failed to load audit logs:', error);
      toast.error('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (action: string) => {
    if (action.includes('HIDDEN')) return <EyeOff className="w-4 h-4" />;
    if (action.includes('UNHIDDEN')) return <Eye className="w-4 h-4" />;
    if (action.includes('DELETED')) return <Trash2 className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  const getActionColor = (action: string) => {
    if (action.includes('HIDDEN')) return 'text-red-400 bg-red-500/20';
    if (action.includes('UNHIDDEN')) return 'text-green-400 bg-green-500/20';
    if (action.includes('DELETED')) return 'text-red-600 bg-red-600/20';
    return 'text-gray-400 bg-gray-500/20';
  };

  const exportToCSV = () => {
    const headers = ['Timestamp', 'Action', 'Book ID', 'Actor', 'Reason'];
    const rows = filteredLogs.map((log) => [
      new Date(log.created_at).toLocaleString(),
      log.action,
      log.entity_id,
      log.actor_email,
      log.reason || '',
    ]);

    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-log-${new Date().toISOString()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Audit log exported');
  };

  const filteredLogs = logs.filter((log) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      log.entity_id.toLowerCase().includes(query) ||
      log.actor_email.toLowerCase().includes(query) ||
      log.reason?.toLowerCase().includes(query) ||
      log.action.toLowerCase().includes(query)
    );
  });

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search logs..."
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
          />
        </div>

        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="pl-10 pr-8 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500 appearance-none cursor-pointer"
          >
            <option value="">All Actions</option>
            <option value="BOOK_HIDDEN">Hidden</option>
            <option value="BOOK_UNHIDDEN">Unhidden</option>
            <option value="BOOK_PERMANENTLY_DELETED">Deleted</option>
          </select>
        </div>

        <button
          onClick={exportToCSV}
          disabled={filteredLogs.length === 0}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total Logs</p>
              <p className="text-2xl font-bold text-white">{logs.length}</p>
            </div>
            <FileText className="w-8 h-8 text-blue-400" />
          </div>
        </div>
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Hidden</p>
              <p className="text-2xl font-bold text-white">
                {logs.filter((l) => l.action.includes('HIDDEN')).length}
              </p>
            </div>
            <EyeOff className="w-8 h-8 text-red-400" />
          </div>
        </div>
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Unhidden</p>
              <p className="text-2xl font-bold text-white">
                {logs.filter((l) => l.action.includes('UNHIDDEN')).length}
              </p>
            </div>
            <Eye className="w-8 h-8 text-green-400" />
          </div>
        </div>
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Deleted</p>
              <p className="text-2xl font-bold text-white">
                {logs.filter((l) => l.action.includes('DELETED')).length}
              </p>
            </div>
            <Trash2 className="w-8 h-8 text-red-600" />
          </div>
        </div>
      </div>

      {/* Logs Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader className="w-8 h-8 text-purple-400 animate-spin" />
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="text-center py-20 bg-gray-800/50 border border-gray-700 rounded-lg">
          <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">No audit logs</h2>
          <p className="text-gray-400">
            {searchQuery || actionFilter
              ? 'No logs match your filters'
              : 'No moderation actions recorded yet'}
          </p>
        </div>
      ) : (
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700/50">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                    Timestamp
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                    Action
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                    Book ID
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                    Actor
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                    Reason
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredLogs.map((log) => (
                  <motion.tr
                    key={log.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="hover:bg-gray-700/30 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-gray-300">
                        <Calendar className="w-4 h-4 text-gray-500" />
                        <span className="text-sm">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div
                        className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-semibold ${getActionColor(
                          log.action
                        )}`}
                      >
                        {getActionIcon(log.action)}
                        {log.action.replace('BOOK_', '').replace(/_/g, ' ')}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <code className="text-xs text-purple-400 bg-purple-500/10 px-2 py-1 rounded">
                        {log.entity_id}
                      </code>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-gray-500" />
                        <div>
                          <p className="text-sm text-gray-300">{log.actor_email}</p>
                          <p className="text-xs text-gray-500">{log.actor_role}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm text-gray-400 max-w-xs truncate">
                        {log.reason || '-'}
                      </p>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
