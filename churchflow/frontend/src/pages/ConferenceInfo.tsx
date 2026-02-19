import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Calendar, MapPin, Users, Phone, Mail, ExternalLink } from 'lucide-react';
import SessionSchedule from '../components/SessionSchedule';

interface Speaker {
  name: string;
  image_url?: string;
  title?: string;
  bio?: string;
}

interface Conference {
  id: string;
  name: string;
  description?: string;
  theme?: string;
  banner_url?: string;
  venue: string;
  venue_latitude?: number;
  venue_longitude?: number;
  start_date: string;
  end_date: string;
  expected_attendance?: number;
  registration_open: boolean;
  speakers?: Speaker[];
  contact_phone?: string;
  contact_email?: string;
  website?: string;
}

export default function ConferenceInfo() {
  const { conferenceId } = useParams<{ conferenceId?: string }>();
  const navigate = useNavigate();

  const [conference, setConference] = useState<Conference | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConference();
  }, [conferenceId]);

  const loadConference = async () => {
    try {
      setLoading(true);

      if (conferenceId) {
        const response = await axios.get(`/api/v1/conferences/${conferenceId}`);
        setConference(response.data);
      } else {
        // Load latest conference
        const response = await axios.get(`/api/v1/conferences`);
        if (response.data.length > 0) {
          setConference(response.data[0]);
        }
      }
    } catch (err: any) {
      console.error('Error loading conference:', err);
      setError(err.response?.data?.detail || 'Failed to load conference');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading conference details...</p>
        </div>
      </div>
    );
  }

  if (error || !conference) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50 flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-gray-600 mb-4">{error || 'Conference not found'}</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Go Home
          </button>
        </div>
      </div>
    );
  }

  const speakers = conference.speakers || [];
  const hasContact = conference.contact_phone || conference.contact_email;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-indigo-50">
      {/* Hero Section with Banner */}
      <div className="relative h-64 sm:h-80 md:h-96 lg:h-[500px] overflow-hidden">
        <img
          src={conference.banner_url}
          alt={conference.name}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent"></div>
        <div className="absolute bottom-0 left-0 right-0 p-8 text-white">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-4xl md:text-6xl font-bold mb-2">{conference.name}</h1>
            {conference.theme && (
              <p className="text-xl md:text-2xl text-purple-200 italic">"{conference.theme}"</p>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Quick Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12 -mt-20 relative z-10">
          <div className="bg-white rounded-lg shadow-md hover:shadow-lg border border-gray-200 border-l-4 border-l-purple-500 p-5 transition-all duration-200 hover:-translate-y-1">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm text-gray-600 uppercase tracking-wider">Dates</h3>
              <div className="p-2 bg-purple-50 rounded-md">
                <Calendar className="w-5 h-5 text-purple-600" />
              </div>
            </div>
            <p className="text-gray-900 text-sm font-medium">
              {new Date(conference.start_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
              {' - '}
              {new Date(conference.end_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-md hover:shadow-lg border border-gray-200 border-l-4 border-l-blue-500 p-5 transition-all duration-200 hover:-translate-y-1">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm text-gray-600 uppercase tracking-wider">Venue</h3>
              <div className="p-2 bg-blue-50 rounded-md">
                <MapPin className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <p className="text-gray-900 text-sm font-medium">{conference.venue}</p>
          </div>

          <div className="bg-white rounded-lg shadow-md hover:shadow-lg border border-gray-200 border-l-4 border-l-pink-500 p-5 transition-all duration-200 hover:-translate-y-1">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm text-gray-600 uppercase tracking-wider">Expected Attendance</h3>
              <div className="p-2 bg-pink-50 rounded-md">
                <Users className="w-5 h-5 text-pink-600" />
              </div>
            </div>
            <p className="text-gray-900 text-2xl font-bold">{conference.expected_attendance?.toLocaleString() || 'TBA'}</p>
            <p className="text-gray-500 text-xs mt-1">people gathering</p>
          </div>
        </div>

        {/* About Section */}
        <div className="bg-white rounded-2xl shadow-xl p-8 md:p-10 mb-12 border-l-8 border-purple-500">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-pink-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent mb-6">About the Conference</h2>
          <p className="text-gray-700 leading-relaxed text-lg whitespace-pre-line break-words">{conference.description}</p>

          {/* Registration Button */}
          {conference.registration_open && (
            <div className="mt-8 flex flex-wrap gap-4">
              <button
                onClick={() => navigate(`/register/${conference.id}`)}
                className="px-6 sm:px-8 md:px-10 py-3 sm:py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-bold rounded-xl hover:from-purple-700 hover:to-indigo-700 transition-all shadow-xl hover:shadow-2xl transform hover:scale-105 duration-300"
              >
                🎯 Register Now
              </button>
            </div>
          )}
        </div>

        {/* Session Schedule Section */}
        <SessionSchedule conferenceId={conference.id} />

        {/* Speakers Section */}
        {speakers.length > 0 && (
          <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-3xl shadow-2xl p-8 md:p-12 mb-12 border-2 border-purple-200">
            <div className="text-center mb-10">
              <div className="inline-block bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-2 rounded-full text-sm font-bold mb-4">
                ✨ FEATURED SPEAKERS
              </div>
              <h2 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent mb-2">
                Powerful Ministry Lineup
              </h2>
              <p className="text-gray-600 text-lg">Leading voices in spiritual transformation</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 md:gap-6 lg:gap-8">
              {speakers.map((speaker, index) => (
                <div key={index} className="group">
                  <div className="relative w-full aspect-square mb-4 rounded-2xl overflow-hidden shadow-xl ring-4 ring-white transform transition-all duration-300 group-hover:scale-105 group-hover:shadow-2xl group-hover:ring-purple-300">
                    <img
                      src={speaker.image_url || '/placeholder-speaker.jpg'}
                      alt={speaker.name}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-purple-900/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </div>
                  <div className="text-center">
                    <p className="font-bold text-gray-900 text-sm md:text-base mb-1 group-hover:text-purple-600 transition-colors">{speaker.name}</p>
                    <p className="text-gray-600 text-xs leading-tight">{speaker.title}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Contact & Info Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {hasContact && (
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl shadow-xl p-8 border-2 border-blue-200">
              <div className="flex items-center gap-3 mb-6">
                <Phone className="w-8 h-8 text-blue-600" />
                <h2 className="text-2xl font-bold text-blue-900">Contact Us</h2>
              </div>
              <div className="space-y-4">
                {conference.contact_phone && (
                  <div className="flex items-center gap-3 p-3 bg-white rounded-lg hover:shadow-md transition-shadow">
                    <Phone className="w-5 h-5 text-blue-600" />
                    <a href={`tel:${conference.contact_phone}`} className="text-gray-700 hover:text-blue-600 font-medium">
                      {conference.contact_phone}
                    </a>
                  </div>
                )}
                {conference.contact_email && (
                  <div className="flex items-center gap-3 p-3 bg-white rounded-lg hover:shadow-md transition-shadow">
                    <Mail className="w-5 h-5 text-blue-600" />
                    <a href={`mailto:${conference.contact_email}`} className="text-gray-700 hover:text-blue-600 font-medium">
                      {conference.contact_email}
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}

          {conference.website && (
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl shadow-xl p-8 border-2 border-green-200">
              <div className="flex items-center gap-3 mb-6">
                <ExternalLink className="w-8 h-8 text-green-600" />
                <h2 className="text-2xl font-bold text-green-900">More Information</h2>
              </div>
              <div className="space-y-4">
                <a
                  href={conference.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-3 bg-white rounded-lg hover:shadow-md transition-shadow text-green-600 hover:text-green-700 font-medium"
                >
                  <ExternalLink className="w-5 h-5" />
                  Visit Conference Website
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
