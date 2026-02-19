import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ArrowLeft, Calendar, MapPin, Users, DollarSign, Tag } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/Card';
import { Button } from '../components/Button';
import api from '../lib/api';
import type { Event, EventFormData } from '../types';

export const EventForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = id && id !== 'new';

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<EventFormData>({
    name: '',
    type: 'conference',
    date: '',
    location: '',
    num_guests: 50,
    budget_min: undefined,
    budget_max: undefined,
    description: '',
    tags: [],
  });

  useEffect(() => {
    if (isEdit) {
      loadEvent();
    }
  }, [id]);

  const loadEvent = async () => {
    if (!id || id === 'new') return;
    try {
      setLoading(true);
      const event = await api.events.getById(id);
      setFormData({
        name: event.name,
        type: event.type,
        date: event.date.split('T')[0], // Convert ISO to YYYY-MM-DD
        location: event.location,
        num_guests: event.num_guests,
        budget_min: event.budget_min,
        budget_max: event.budget_max,
        description: event.description || '',
        tags: event.tags || [],
      });
    } catch (error) {
      console.error('Error loading event:', error);
      setError('Failed to load event');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      setSubmitting(true);

      // Convert date to ISO string
      const submitData = {
        ...formData,
        date: new Date(formData.date).toISOString(),
      };

      if (isEdit && id) {
        await api.events.update(id, submitData);
      } else {
        const newEvent = await api.events.create(submitData);
        navigate(`/events/${newEvent.id}`);
        return;
      }

      navigate(`/events/${id}`);
    } catch (error: any) {
      console.error('Error saving event:', error);
      setError(error.message || 'Failed to save event');
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value ? Number(value) : undefined) : value,
    }));
  };

  const handleTagsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const tags = e.target.value.split(',').map((tag) => tag.trim()).filter(Boolean);
    setFormData((prev) => ({ ...prev, tags }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to={isEdit ? `/events/${id}` : '/events'}>
          <Button variant="ghost" size="sm" icon={<ArrowLeft size={20} />} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {isEdit ? 'Edit Event' : 'Create New Event'}
          </h1>
          <p className="text-gray-600 mt-1">
            {isEdit ? 'Update event details' : 'Plan your next great event'}
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="bg-red-50 border-red-200">
          <p className="text-red-800">{error}</p>
        </Card>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader
            title="Event Details"
            subtitle="Enter the basic information about your event"
          />
          <CardContent>
            <div className="space-y-6">
              {/* Event Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                  Event Name *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="e.g., Impact 2025 Conference"
                />
              </div>

              {/* Event Type */}
              <div>
                <label htmlFor="type" className="block text-sm font-medium text-gray-700 mb-2">
                  Event Type *
                </label>
                <select
                  id="type"
                  name="type"
                  required
                  value={formData.type}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                >
                  <option value="conference">Conference</option>
                  <option value="wedding">Wedding</option>
                  <option value="concert">Concert</option>
                  <option value="outreach">Outreach</option>
                  <option value="corporate">Corporate</option>
                  <option value="meeting">Meeting</option>
                  <option value="workshop">Workshop</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Date and Location Row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Date */}
                <div>
                  <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-2">
                    <Calendar size={16} className="inline mr-1" />
                    Event Date *
                  </label>
                  <input
                    type="date"
                    id="date"
                    name="date"
                    required
                    value={formData.date}
                    onChange={handleChange}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>

                {/* Number of Guests */}
                <div>
                  <label htmlFor="num_guests" className="block text-sm font-medium text-gray-700 mb-2">
                    <Users size={16} className="inline mr-1" />
                    Expected Guests *
                  </label>
                  <input
                    type="number"
                    id="num_guests"
                    name="num_guests"
                    required
                    min="1"
                    value={formData.num_guests}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Location */}
              <div>
                <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
                  <MapPin size={16} className="inline mr-1" />
                  Location *
                </label>
                <input
                  type="text"
                  id="location"
                  name="location"
                  required
                  value={formData.location}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="e.g., Accra International Conference Centre"
                />
              </div>

              {/* Budget Range */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="budget_min" className="block text-sm font-medium text-gray-700 mb-2">
                    <DollarSign size={16} className="inline mr-1" />
                    Minimum Budget (GHS)
                  </label>
                  <input
                    type="number"
                    id="budget_min"
                    name="budget_min"
                    min="0"
                    value={formData.budget_min || ''}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    placeholder="e.g., 50000"
                  />
                </div>

                <div>
                  <label htmlFor="budget_max" className="block text-sm font-medium text-gray-700 mb-2">
                    <DollarSign size={16} className="inline mr-1" />
                    Maximum Budget (GHS)
                  </label>
                  <input
                    type="number"
                    id="budget_max"
                    name="budget_max"
                    min="0"
                    value={formData.budget_max || ''}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    placeholder="e.g., 100000"
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows={4}
                  value={formData.description}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="Tell us more about your event..."
                />
              </div>

              {/* Tags */}
              <div>
                <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-2">
                  <Tag size={16} className="inline mr-1" />
                  Tags (comma-separated)
                </label>
                <input
                  type="text"
                  id="tags"
                  name="tags"
                  value={formData.tags.join(', ')}
                  onChange={handleTagsChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="e.g., youth, conference, public"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Separate multiple tags with commas
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 mt-6">
          <Link to={isEdit ? `/events/${id}` : '/events'}>
            <Button type="button" variant="outline">
              Cancel
            </Button>
          </Link>
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Saving...' : isEdit ? 'Update Event' : 'Create Event'}
          </Button>
        </div>
      </form>
    </div>
  );
};
