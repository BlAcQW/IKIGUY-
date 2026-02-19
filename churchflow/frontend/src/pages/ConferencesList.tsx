import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Calendar, MapPin, Users, Search, Filter, CheckCircle, XCircle, Clock, Sparkles } from 'lucide-react';

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
  start_date: string;
  end_date: string;
  expected_attendance?: number;
  current_attendees: number;
  registration_open: boolean;
  status: 'upcoming' | 'ongoing' | 'completed' | 'cancelled';
  speakers?: Speaker[];
}

export default function ConferencesList() {
  const navigate = useNavigate();

  const [conferences, setConferences] = useState<Conference[]>([]);
  const [filteredConferences, setFilteredConferences] = useState<Conference[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showOnlyOpen, setShowOnlyOpen] = useState(false);

  useEffect(() => {
    loadConferences();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [conferences, searchQuery, statusFilter, showOnlyOpen]);

  const loadConferences = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get('/api/v1/conferences');
      setConferences(response.data);
    } catch (err: any) {
      console.error('Error loading conferences:', err);
      setError(err.response?.data?.detail || 'Failed to load conferences');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...conferences];

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(conf =>
        conf.name.toLowerCase().includes(query) ||
        conf.theme?.toLowerCase().includes(query) ||
        conf.venue.toLowerCase().includes(query)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(conf => conf.status === statusFilter);
    }

    // Registration open filter
    if (showOnlyOpen) {
      filtered = filtered.filter(conf => conf.registration_open);
    }

    // Sort by date (upcoming first)
    filtered.sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime());

    setFilteredConferences(filtered);
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      upcoming: 'bg-blue-100 text-blue-700 border-blue-200',
      ongoing: 'bg-green-100 text-green-700 border-green-200',
      completed: 'bg-gray-100 text-gray-700 border-gray-200',
      cancelled: 'bg-red-100 text-red-700 border-red-200',
    };

    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded border ${styles[status as keyof typeof styles] || styles.upcoming}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const getDateRange = (start: string, end: string) => {
    return `${formatDate(start)} - ${formatDate(end)}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
        {/* Navigation Bar */}
        <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              <button onClick={() => navigate('/')} className="flex items-center gap-2">
                <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-gray-900">ChurchFlow</span>
              </button>
            </div>
          </div>
        </nav>

        <div className="container mx-auto px-4 py-16">
          <div className="flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading conferences...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
        {/* Navigation Bar */}
        <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              <button onClick={() => navigate('/')} className="flex items-center gap-2">
                <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-gray-900">ChurchFlow</span>
              </button>
            </div>
          </div>
        </nav>

        <div className="container mx-auto px-4 py-16">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={loadConferences}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
      {/* Navigation Bar */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <button onClick={() => navigate('/')} className="flex items-center gap-2">
              <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">ChurchFlow</span>
            </button>
            <button
              onClick={() => navigate('/')}
              className="text-gray-600 hover:text-purple-600 font-medium transition-colors"
            >
              Back to Home
            </button>
          </div>
        </div>
      </nav>

      {/* Header Section */}
      <section className="container mx-auto px-4 py-8 md:py-12">
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">Browse Conferences</h1>
          <p className="text-lg text-gray-600">Discover upcoming events and register to attend</p>
        </div>

        {/* Filters Section */}
        <div className="bg-white rounded-lg shadow-md p-4 md:p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            {/* Search Box */}
            <div className="md:col-span-5">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name, theme, or venue..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Status Filter */}
            <div className="md:col-span-3">
              <div className="relative">
                <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white"
                >
                  <option value="all">All Status</option>
                  <option value="upcoming">Upcoming</option>
                  <option value="ongoing">Ongoing</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>

            {/* Registration Open Toggle */}
            <div className="md:col-span-4">
              <label className="flex items-center gap-3 p-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showOnlyOpen}
                  onChange={(e) => setShowOnlyOpen(e.target.checked)}
                  className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  Show only accepting registrations
                </span>
              </label>
            </div>
          </div>

          {/* Results Count */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              Showing <span className="font-semibold text-gray-900">{filteredConferences.length}</span> of <span className="font-semibold">{conferences.length}</span> conferences
            </p>
          </div>
        </div>

        {/* Conferences Grid */}
        {filteredConferences.length === 0 ? (
          <div className="text-center py-16">
            <Calendar className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No conferences found</h3>
            <p className="text-gray-600 mb-6">
              {searchQuery || statusFilter !== 'all' || showOnlyOpen
                ? 'Try adjusting your filters to see more results'
                : 'No conferences are currently available'}
            </p>
            {(searchQuery || statusFilter !== 'all' || showOnlyOpen) && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setStatusFilter('all');
                  setShowOnlyOpen(false);
                }}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredConferences.map((conference) => (
              <div
                key={conference.id}
                className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-all duration-300 cursor-pointer group"
                onClick={() => navigate(`/conference/${conference.id}`)}
              >
                {/* Conference Banner */}
                <div className="relative h-48 overflow-hidden">
                  {conference.banner_url ? (
                    <img
                      src={conference.banner_url}
                      alt={conference.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center">
                      <Calendar className="w-16 h-16 text-white opacity-50" />
                    </div>
                  )}

                  {/* Status Badge Overlay */}
                  <div className="absolute top-3 right-3">
                    {getStatusBadge(conference.status)}
                  </div>
                </div>

                {/* Conference Info */}
                <div className="p-5">
                  {/* Name and Theme */}
                  <h3 className="text-lg font-bold text-gray-900 mb-1 line-clamp-1">
                    {conference.name}
                  </h3>
                  {conference.theme && (
                    <p className="text-sm text-purple-600 italic mb-3 line-clamp-1">
                      "{conference.theme}"
                    </p>
                  )}

                  {/* Date */}
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                    <Calendar className="w-4 h-4" />
                    <span>{getDateRange(conference.start_date, conference.end_date)}</span>
                  </div>

                  {/* Venue */}
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                    <MapPin className="w-4 h-4" />
                    <span className="line-clamp-1">{conference.venue}</span>
                  </div>

                  {/* Attendance */}
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
                    <Users className="w-4 h-4" />
                    <span>
                      {conference.current_attendees} registered
                      {conference.expected_attendance && ` / ${conference.expected_attendance} expected`}
                    </span>
                  </div>

                  {/* Speakers Count */}
                  {conference.speakers && conference.speakers.length > 0 && (
                    <p className="text-xs text-gray-500 mb-4">
                      {conference.speakers.length} speaker{conference.speakers.length !== 1 ? 's' : ''}
                    </p>
                  )}

                  {/* Registration Status */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                    {conference.registration_open ? (
                      <>
                        <div className="flex items-center gap-2 text-sm text-green-600">
                          <CheckCircle className="w-4 h-4" />
                          <span className="font-medium">Registration Open</span>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/register/${conference.id}`);
                          }}
                          className="px-4 py-2 bg-purple-600 text-white text-sm font-semibold rounded-lg hover:bg-purple-700 transition-colors"
                        >
                          Register Now
                        </button>
                      </>
                    ) : (
                      <>
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <XCircle className="w-4 h-4" />
                          <span className="font-medium">Registration Closed</span>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/conference/${conference.id}`);
                          }}
                          className="px-4 py-2 bg-gray-200 text-gray-700 text-sm font-semibold rounded-lg hover:bg-gray-300 transition-colors"
                        >
                          Learn More
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
