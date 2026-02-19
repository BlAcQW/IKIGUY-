import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Calendar, MapPin, Users, Filter } from 'lucide-react';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import api from '../lib/api';
import { formatDate, daysUntil, getEventStatusColor } from '../lib/utils';
import type { Event, EventFilters } from '../types';

export const Events: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'active' | 'past'>('all');

  useEffect(() => {
    loadEvents();
  }, [filter]);

  const loadEvents = async () => {
    try {
      setLoading(true);

      // Fetch all events from the backend
      const response = await api.events.getAll({});

      // Extract events array from paginated response
      // Response structure: { data: Event[], total: number, page: number, page_size: number }
      const allEvents = Array.isArray(response?.data) ? response.data : [];

      console.log('Events loaded:', allEvents);

      // Apply client-side filtering based on selected filter
      let filteredEvents = allEvents;

      if (filter === 'upcoming') {
        // Upcoming: Events that are in the future and within 30 days
        filteredEvents = allEvents.filter(e => {
          const days = daysUntil(e.date);
          return days >= 0 && days <= 30;
        });
      } else if (filter === 'active') {
        // Active: Events with status 'planning' or 'active'
        filteredEvents = allEvents.filter(e =>
          e.status === 'planning' || e.status === 'active'
        );
      } else if (filter === 'past') {
        // Past: Events that have already occurred (date is in the past)
        // OR events with status 'completed' or 'cancelled'
        filteredEvents = allEvents.filter(e => {
          const days = daysUntil(e.date);
          return days < 0 || e.status === 'completed' || e.status === 'cancelled';
        });
      }
      // else 'all' - show all events (no filtering)

      console.log(`Filter: ${filter}, Showing ${filteredEvents.length} of ${allEvents.length} events`);
      setEvents(filteredEvents);
    } catch (error) {
      console.error('Error loading events:', error);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  // Ensure events is always an array
  const safeEvents = Array.isArray(events) ? events : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Events</h1>
          <p className="text-gray-600 mt-1">Manage your events and celebrations</p>
        </div>
        <Link to="/events/new">
          <Button icon={<Plus size={20} />}>Create Event</Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {['all', 'upcoming', 'active', 'past'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f as any)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === f
                ? 'bg-emerald-600 text-white'
                : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Events Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
        </div>
      ) : safeEvents.length === 0 ? (
        <Card className="text-center py-12">
          <Calendar size={64} className="mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No events found</h3>
          <p className="text-gray-600 mb-6">Get started by creating your first event</p>
          <Link to="/events/new">
            <Button icon={<Plus size={20} />}>Create Event</Button>
          </Link>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {safeEvents.map((event) => (
            <Link key={event.id} to={`/events/${event.id}`}>
              <Card hover className="h-full">
                <div className="space-y-3">
                  {/* Event Header */}
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-gray-900 text-lg flex-1">{event.name}</h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getEventStatusColor(event.status)}`}>
                      {event.status}
                    </span>
                  </div>

                  {/* Event Info */}
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <Calendar size={16} className="flex-shrink-0" />
                      <span>{formatDate(event.date)}</span>
                      {daysUntil(event.date) >= 0 && (
                        <span className="ml-auto text-emerald-600 font-medium">
                          {daysUntil(event.date)} days
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin size={16} className="flex-shrink-0" />
                      <span className="truncate">{event.location}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Users size={16} className="flex-shrink-0" />
                      <span>{event.num_guests} guests</span>
                    </div>
                  </div>

                  {/* Event Type */}
                  <div className="pt-3 border-t border-gray-200">
                    <span className="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">
                      {event.type}
                    </span>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};
