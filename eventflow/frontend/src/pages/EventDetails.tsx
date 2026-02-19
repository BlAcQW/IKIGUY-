import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Calendar, MapPin, Users, Phone, Mail, CheckCircle, Clock, AlertTriangle, ArrowLeft, Edit } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/Card';
import { Button } from '../components/Button';
import api from '../lib/api';
import { formatDate, formatCurrency, daysUntil, getTaskStatusColor, getTaskPriorityColor } from '../lib/utils';
import type { Event, Task, ResponsiblePerson, DashboardData } from '../types';

export const EventDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [event, setEvent] = useState<Event | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [persons, setPersons] = useState<ResponsiblePerson[]>([]);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) loadEventDetails();
  }, [id]);

  const loadEventDetails = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [eventRes, tasksRes, personsRes, dashboardRes] = await Promise.all([
        api.events.getById(id),
        api.tasks.getAll(id),
        api.persons.getAll(id),
        api.events.getDashboard(id),
      ]);
      setEvent(eventRes);
      // Ensure data is always an array
      setTasks(Array.isArray(tasksRes?.data) ? tasksRes.data : []);
      setPersons(Array.isArray(personsRes) ? personsRes : []);
      setDashboard(dashboardRes);
    } catch (error) {
      console.error('Error loading event:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (!event) {
    return (
      <Card className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Event not found</h3>
        <Link to="/events">
          <Button variant="outline">Back to Events</Button>
        </Link>
      </Card>
    );
  }

  // Ensure arrays are safe before processing
  const safeTasks = Array.isArray(tasks) ? tasks : [];
  const safePersons = Array.isArray(persons) ? persons : [];

  const tasksByCategory = safeTasks.reduce((acc, task) => {
    if (!acc[task.category]) acc[task.category] = [];
    acc[task.category].push(task);
    return acc;
  }, {} as Record<string, Task[]>);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/events">
          <Button variant="ghost" size="sm" icon={<ArrowLeft size={20} />} />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{event.name}</h1>
          <p className="text-gray-600 mt-1">{event.description}</p>
        </div>
        <Link to={`/events/${id}/edit`}>
          <Button variant="outline" icon={<Edit size={20} />}>
            Edit Event
          </Button>
        </Link>
      </div>

      {/* Event Info Card */}
      <Card>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-3">
            <Calendar className="text-emerald-600" size={24} />
            <div>
              <p className="text-sm text-gray-600">Date</p>
              <p className="font-medium text-gray-900">{formatDate(event.date)}</p>
              <p className="text-xs text-emerald-600 font-medium">{daysUntil(event.date)} days away</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <MapPin className="text-blue-600" size={24} />
            <div>
              <p className="text-sm text-gray-600">Location</p>
              <p className="font-medium text-gray-900">{event.location}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Users className="text-purple-600" size={24} />
            <div>
              <p className="text-sm text-gray-600">Guests</p>
              <p className="font-medium text-gray-900">{event.num_guests}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <CheckCircle className="text-green-600" size={24} />
            <div>
              <p className="text-sm text-gray-600">Progress</p>
              <p className="font-medium text-gray-900">{dashboard?.tasks.completion_rate.toFixed(0)}%</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Dashboard Metrics */}
      {dashboard && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-green-50">
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{dashboard.tasks.completed}</p>
              <p className="text-sm text-gray-600 mt-1">Completed</p>
            </div>
          </Card>
          <Card className="bg-blue-50">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">{dashboard.tasks.in_progress}</p>
              <p className="text-sm text-gray-600 mt-1">In Progress</p>
            </div>
          </Card>
          <Card className="bg-gray-50">
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-600">{dashboard.tasks.pending}</p>
              <p className="text-sm text-gray-600 mt-1">Pending</p>
            </div>
          </Card>
          <Card className="bg-red-50">
            <div className="text-center">
              <p className="text-3xl font-bold text-red-600">{dashboard.tasks.overdue}</p>
              <p className="text-sm text-gray-600 mt-1">Overdue</p>
            </div>
          </Card>
        </div>
      )}

      {/* Tasks by Category */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900">Tasks by Department</h2>
        {Object.entries(tasksByCategory).map(([category, categoryTasks]) => (
          <Card key={category}>
            <CardHeader
              title={category.charAt(0).toUpperCase() + category.slice(1)}
              subtitle={`${categoryTasks.filter(t => t.status === 'completed').length}/${categoryTasks.length} completed`}
            />
            <CardContent>
              <div className="space-y-2">
                {categoryTasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900 truncate">{task.title}</h4>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded ${getTaskPriorityColor(task.priority)}`}>
                          {task.priority}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        Due: {formatDate(task.deadline)}
                      </p>
                    </div>
                    <span className={`px-3 py-1 text-xs font-medium rounded ${getTaskStatusColor(task.status)}`}>
                      {task.status.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Team Directory */}
      <Card>
        <CardHeader
          title="Team Directory"
          subtitle={`${safePersons.length} responsible person(s)`}
        />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {safePersons.map((person) => (
              <div key={person.id} className="p-3 rounded-lg border border-gray-200">
                <h4 className="font-medium text-gray-900">{person.name}</h4>
                <p className="text-sm text-emerald-600 font-medium mt-1">{person.role}</p>
                <div className="flex items-center gap-3 mt-2 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <Phone size={14} />
                    <span>{person.phone}</span>
                  </div>
                  {person.email && (
                    <div className="flex items-center gap-1">
                      <Mail size={14} />
                      <span>{person.email}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
