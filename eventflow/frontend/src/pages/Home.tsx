import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, CheckCircle, Clock, AlertTriangle, Plus, TrendingUp, DollarSign } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/Card';
import { Button } from '../components/Button';
import { useStore } from '../lib/store';
import api from '../lib/api';
import { formatDate, formatCurrency, daysUntil, getTaskStatusColor } from '../lib/utils';
import type { Event, Task, UsageStats } from '../types';

export const Home: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load events and tasks (wallet stats removed for public demo)
      const [eventsResponse, tasksResponse] = await Promise.all([
        api.events.getAll({ status: ['planning', 'active'] }),
        api.tasks.getAll(undefined, { status: ['pending', 'in_progress'] }),
      ]);

      // Extract data from paginated responses
      const eventsData = Array.isArray(eventsResponse?.data) ? eventsResponse.data : [];
      const tasksData = Array.isArray(tasksResponse?.data) ? tasksResponse.data : [];

      console.log('Events loaded:', eventsData);
      console.log('Tasks loaded:', tasksData);

      // Set state with extracted data
      setEvents(eventsData);
      setTasks(tasksData.slice(0, 5)); // Top 5 tasks

      // Try to load wallet stats but don't fail if not available
      // Skip if not authenticated (403 errors expected)
      try {
        const statsRes = await api.wallet.getUsageStats('week');
        setStats(statsRes);
      } catch (err: any) {
        // Expected for unauthenticated users - just log and continue
        if (err?.response?.status === 403) {
          console.log('Wallet stats not available - authentication required');
        } else {
          console.log('Wallet stats not available:', err.message);
        }
      }
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setError(error instanceof Error ? error.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // Defensive filtering - ensure arrays exist before filtering
  const safeEvents = Array.isArray(events) ? events : [];
  const safeTasks = Array.isArray(tasks) ? tasks : [];

  const upcomingEvents = safeEvents.filter(e => daysUntil(e.date) >= 0 && daysUntil(e.date) <= 30);
  const overdueTasks = safeTasks.filter(t => new Date(t.deadline) < new Date());

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error loading dashboard: {error}</p>
          <Button onClick={loadDashboardData}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Event Dashboard 📅
          </h1>
          <p className="text-gray-600 mt-1">
            Manage and track all your events in one place
          </p>
        </div>
        <Link to="/events/new">
          <Button icon={<Plus size={20} />}>Create Event</Button>
        </Link>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-emerald-50 border-emerald-200">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-emerald-600 rounded-lg">
              <Calendar className="text-white" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Active Events</p>
              <p className="text-2xl font-bold text-gray-900">{safeEvents.length}</p>
            </div>
          </div>
        </Card>

        <Card className="bg-blue-50 border-blue-200">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-600 rounded-lg">
              <CheckCircle className="text-white" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Pending Tasks</p>
              <p className="text-2xl font-bold text-gray-900">{safeTasks.length}</p>
            </div>
          </div>
        </Card>

        <Card className="bg-orange-50 border-orange-200">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-orange-600 rounded-lg">
              <AlertTriangle className="text-white" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Overdue Tasks</p>
              <p className="text-2xl font-bold text-gray-900">{overdueTasks.length}</p>
            </div>
          </div>
        </Card>

        <Card className="bg-purple-50 border-purple-200">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-600 rounded-lg">
              <TrendingUp className="text-white" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Budget</p>
              <p className="text-2xl font-bold text-gray-900">
                {safeEvents.length > 0 && safeEvents[0].budget_max
                  ? formatCurrency(safeEvents[0].budget_max, 'GHS')
                  : '₵0.00'}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Events */}
        <Card>
          <CardHeader
            title="🎉 Upcoming Events"
            subtitle={`${upcomingEvents.length} event(s) in the next 30 days`}
            action={
              <Link to="/events" className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
                View all →
              </Link>
            }
          />
          <CardContent>
            {upcomingEvents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Calendar size={48} className="mx-auto mb-3 text-gray-300" />
                <p>No upcoming events</p>
                <Link to="/events/new">
                  <Button variant="outline" className="mt-3" size="sm">
                    Create your first event
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {upcomingEvents.slice(0, 3).map((event) => {
                  const eventDaysLeft = daysUntil(event.date);
                  const isComingSoon = eventDaysLeft <= 7;

                  return (
                    <Link
                      key={event.id}
                      to={`/events/${event.id}`}
                      className="block p-4 rounded-lg border-2 border-emerald-200 bg-gradient-to-br from-emerald-50 to-white hover:border-emerald-400 hover:shadow-lg transition-all"
                    >
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2">
                            <h4 className="font-bold text-lg text-gray-900">{event.name}</h4>
                            {isComingSoon && (
                              <span className="px-2 py-1 text-xs font-bold bg-red-500 text-white rounded-full animate-pulse">
                                SOON!
                              </span>
                            )}
                          </div>
                          <div className="space-y-1 text-sm">
                            <div className="flex items-center gap-2 text-gray-700">
                              <span>📍</span>
                              <span className="truncate">{event.location}</span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-700">
                              <span>📅</span>
                              <span>{formatDate(event.date)}</span>
                            </div>
                            <div className="flex items-center gap-2 text-gray-700">
                              <span>👥</span>
                              <span className="font-semibold">{event.num_guests.toLocaleString()} expected guests</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right flex-shrink-0">
                          <div className={`px-4 py-2 rounded-lg ${
                            isComingSoon ? 'bg-red-500 text-white' : 'bg-emerald-500 text-white'
                          }`}>
                            <p className="text-2xl font-bold">
                              {eventDaysLeft}
                            </p>
                            <p className="text-xs font-medium">days</p>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center justify-between pt-3 border-t border-emerald-200">
                        <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">
                          {event.type}
                        </span>
                        <span className="text-sm font-bold text-emerald-600">
                          View Details →
                        </span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Priority Tasks */}
        <Card>
          <CardHeader
            title="🎯 Top Priority Tasks"
            subtitle={`${safeTasks.length} tasks need attention`}
            action={
              <Link to="/tasks" className="text-sm text-emerald-600 hover:text-emerald-700 font-medium">
                View all →
              </Link>
            }
          />
          <CardContent>
            {safeTasks.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle size={48} className="mx-auto mb-3 text-gray-300" />
                <p>No pending tasks</p>
              </div>
            ) : (
              <div className="space-y-4">
                {safeTasks.map((task) => {
                  const daysLeft = Math.ceil((new Date(task.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));
                  const isOverdue = daysLeft < 0;
                  const isUrgent = daysLeft <= 7 && daysLeft >= 0;

                  return (
                    <div
                      key={task.id}
                      className={`p-4 rounded-lg border-l-4 ${
                        task.priority === 'critical' ? 'border-l-red-500 bg-red-50' :
                        task.priority === 'high' ? 'border-l-orange-500 bg-orange-50' :
                        task.priority === 'medium' ? 'border-l-yellow-500 bg-yellow-50' :
                        'border-l-blue-500 bg-blue-50'
                      } hover:shadow-md transition-all`}
                    >
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-gray-900">{task.title}</h4>
                            <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${
                              task.priority === 'critical' ? 'bg-red-600 text-white' :
                              task.priority === 'high' ? 'bg-orange-600 text-white' :
                              task.priority === 'medium' ? 'bg-yellow-600 text-white' :
                              'bg-blue-600 text-white'
                            }`}>
                              {task.priority.toUpperCase()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 line-clamp-2">{task.description || task.category}</p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200">
                        <div className="flex items-center gap-4 text-sm">
                          {task.assigned_person && (
                            <div className="flex items-center gap-1 text-gray-700">
                              <span className="font-medium">👤</span>
                              <span>{task.assigned_person.name}</span>
                            </div>
                          )}
                          <div className="flex items-center gap-1 text-gray-700">
                            <span>📁</span>
                            <span className="capitalize">{task.category}</span>
                          </div>
                          {task.cost_estimate && (
                            <div className="flex items-center gap-1 text-gray-700 font-semibold">
                              <span>💰</span>
                              <span>{formatCurrency(task.cost_estimate, 'GHS')}</span>
                            </div>
                          )}
                        </div>

                        <div className="flex flex-col items-end gap-1">
                          <span className={`px-3 py-1 text-xs font-bold rounded-full ${getTaskStatusColor(task.status)}`}>
                            {task.status.replace('_', ' ').toUpperCase()}
                          </span>
                          <span className={`text-xs font-semibold ${
                            isOverdue ? 'text-red-600' :
                            isUrgent ? 'text-orange-600' :
                            'text-emerald-600'
                          }`}>
                            {isOverdue ? `${Math.abs(daysLeft)} days overdue!` :
                             isUrgent ? `⚠️ ${daysLeft} days left` :
                             `${daysLeft} days left`}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Usage Stats */}
      {stats && (
        <Card>
          <CardHeader
            title="Weekly Usage"
            subtitle="Your activity this week"
          />
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-blue-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Voice Calls</span>
                  <TrendingUp size={16} className="text-blue-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900">{stats.voice_calls.count}</p>
                <p className="text-xs text-gray-600 mt-1">
                  {stats.voice_calls.duration_minutes.toFixed(1)} minutes
                </p>
              </div>

              <div className="p-4 rounded-lg bg-green-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Messages Sent</span>
                  <TrendingUp size={16} className="text-green-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.messages.sms + stats.messages.whatsapp}
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  SMS: {stats.messages.sms}, WhatsApp: {stats.messages.whatsapp}
                </p>
              </div>

              <div className="p-4 rounded-lg bg-purple-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Total Spent</span>
                  <DollarSign size={16} className="text-purple-600" />
                </div>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(stats.total_cost)}
                </p>
                <p className="text-xs text-gray-600 mt-1">This week</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
