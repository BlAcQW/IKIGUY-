import React, { useEffect, useState } from 'react';
import { CheckCircle, Clock, AlertCircle, Filter } from 'lucide-react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import api from '../lib/api';
import { formatDate, getTaskStatusColor, getTaskPriorityColor } from '../lib/utils';
import type { Task, TaskFilters } from '../types';

export const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    loadTasks();
  }, [statusFilter]);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const filters: TaskFilters = {};
      if (statusFilter !== 'all') {
        filters.status = [statusFilter as any];
      }
      const res = await api.tasks.getAll(undefined, filters);
      // Ensure data is always an array
      setTasks(Array.isArray(res?.data) ? res.data : []);
    } catch (error) {
      console.error('Error loading tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (taskId: string, newStatus: string) => {
    try {
      await api.tasks.updateStatus(taskId, newStatus);
      loadTasks();
    } catch (error) {
      console.error('Error updating task:', error);
    }
  };

  // Ensure tasks is always an array
  const safeTasks = Array.isArray(tasks) ? tasks : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
        <p className="text-gray-600 mt-1">Manage and track your event tasks</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {['all', 'pending', 'in_progress', 'completed', 'blocked'].map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === status
                ? 'bg-emerald-600 text-white'
                : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {status === 'all' ? 'All Tasks' : status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Tasks List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
        </div>
      ) : safeTasks.length === 0 ? (
        <Card className="text-center py-12">
          <CheckCircle size={64} className="mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No tasks found</h3>
          <p className="text-gray-600">Tasks will appear here when you create events</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {safeTasks.map((task) => (
            <Card key={task.id} hover>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold text-gray-900">{task.title}</h3>
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${getTaskPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
                    <span className="inline-flex items-center gap-1">
                      <Clock size={14} />
                      Due: {formatDate(task.deadline)}
                    </span>
                    <span>Category: {task.category}</span>
                    {task.assigned_person && (
                      <span>Assigned to: {task.assigned_person.name}</span>
                    )}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className={`px-3 py-1 text-xs font-medium rounded ${getTaskStatusColor(task.status)}`}>
                    {task.status.replace('_', ' ')}
                  </span>
                  {task.status !== 'completed' && (
                    <select
                      value={task.status}
                      onChange={(e) => handleStatusUpdate(task.id, e.target.value)}
                      className="text-xs border border-gray-200 rounded px-2 py-1"
                    >
                      <option value="pending">Pending</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                      <option value="blocked">Blocked</option>
                    </select>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
