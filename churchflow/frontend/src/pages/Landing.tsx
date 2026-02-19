import {
  Bus,
  Calendar,
  Users,
  Sparkles,
  Menu,
  X,
  MapPin,
  CheckCircle,
  XCircle,
  LogIn,
  FileText,
  Download,
  Clock,
  Mail,
  Phone,
  Globe,
  Heart,
  BookOpen,
  Music,
  Church,
  DollarSign,
  UserPlus,
  ArrowRight,
  Facebook,
  Instagram,
  Youtube,
  Twitter
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import axios from 'axios'
import { isAuthenticated } from '../lib/auth-utils'
import PublicFirstTimerModal from '../components/first-timers/PublicFirstTimerModal'
import AnnouncementCard from '../components/AnnouncementCard'
import { getApiUrl } from '../config/api-config'
import { normalizeAnnouncementImageUrl } from '../utils/imageUrl'

interface Conference {
  id: string;
  name: string;
  theme?: string;
  banner_url?: string;
  venue: string;
  start_date: string;
  end_date: string;
  expected_attendance?: number;
  current_attendees: number;
  registration_open: boolean;
  status: string;
  speakers?: any[];
}

interface Organization {
  name: string;
  tagline?: string;
  mission?: string;
  description?: string;
  logo_url?: string;
  contact_info?: {
    phone?: string;
    email?: string;
    address?: string;
    website?: string;
  };
}

interface Branch {
  id: string;
  name: string;
  location: string;
  service_times?: Array<{
    day_of_week: string;
    service_type: string;
    start_time: string;
    duration_minutes: number;
    is_active: boolean;
  }>;
  is_headquarters?: boolean;
}

export default function Landing() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [upcomingConferences, setUpcomingConferences] = useState<Conference[]>([])
  const [loadingConferences, setLoadingConferences] = useState(true)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [organization, setOrganization] = useState<Organization | null>(null)
  const [branches, setBranches] = useState<Branch[]>([])
  const [loadingOrg, setLoadingOrg] = useState(true)
  const [showFirstTimerModal, setShowFirstTimerModal] = useState(false)
  const [announcements, setAnnouncements] = useState<any[]>([])
  const [loadingAnnouncements, setLoadingAnnouncements] = useState(true)
  const [heroAnnouncement, setHeroAnnouncement] = useState<any | null>(null)
  const heroImageUrl = "https://actionchapel.net/wp-content/uploads/2025/07/WhatsApp-Image-2025-07-20-at-10.27.46.jpeg"

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen)
  }

  const closeMobileMenu = () => {
    setMobileMenuOpen(false)
  }

  useEffect(() => {
    setIsLoggedIn(isAuthenticated())
    loadOrganizationData()
    loadUpcomingConferences()
    loadAnnouncements()
  }, [])

  const loadOrganizationData = async () => {
    try {
      setLoadingOrg(true)
      // TODO: Replace with public API endpoint when available
      // Data sourced from https://actionchapel.net/
      setOrganization({
        name: "United Denominations of Action Chapel International",
        tagline: "One church in many locations worldwide, a place where Divinity meets Humanity",
        mission: "United Denominations of Action Chapel International was founded by Archbishop Nicholas Duncan-Williams, who is the founder and father of the Charismatic Movement in Ghana. UDACI, one church in many locations, has over 500 branch and affiliate churches located in Africa, Europe, and North America.",
        description: "United Denominations of Action Chapel International is one church in many locations worldwide, a place where Divinity meets Humanity. Founded by Archbishop Nicholas Duncan-Williams, who is the founder and father of the Charismatic Movement in Ghana. UDACI has over 500 branch and affiliate churches located in Africa, Europe, and North America, and since 1992 has met in the Prayer Cathedral near Accra airport.",
        contact_info: {
          phone: "+233 262626 906",
          email: "admin@actionchapel.net",
          address: "37 Spintex Rd. Accra, Ghana",
          website: "https://actionchapel.net"
        }
      })
      // Load branches if API available
      // const response = await axios.get('/api/v1/public/branches')
      // setBranches(response.data)
    } catch (err) {
      console.error('Error loading organization data:', err)
    } finally {
      setLoadingOrg(false)
    }
  }

  const loadUpcomingConferences = async () => {
    try {
      setLoadingConferences(true)
      const response = await axios.get('/api/v1/conferences')
      const upcoming = response.data
        .filter((conf: Conference) => conf.status === 'upcoming' || conf.status === 'ongoing')
        .slice(0, 6)
      setUpcomingConferences(upcoming)
    } catch (err) {
      console.error('Error loading conferences:', err)
    } finally {
      setLoadingConferences(false)
    }
  }

  const loadAnnouncements = async () => {
    try {
      setLoadingAnnouncements(true)
      const response = await fetch(getApiUrl('announcements/public'))
      if (response.ok) {
        const data = await response.json()
        // API returns array directly, not wrapped in object
        setAnnouncements(Array.isArray(data) ? data : (data.announcements || []))
      } else {
        console.error('Failed to load announcements:', response.status, response.statusText)
      }
    } catch (err) {
      console.error('Error loading announcements:', err)
    } finally {
      setLoadingAnnouncements(false)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const getDateRange = (start: string, end: string) => {
    const startDate = formatDate(start)
    const endDate = formatDate(end)
    if (startDate === endDate) return startDate
    return `${startDate} - ${endDate}`
  }

  const formatServiceTime = (time: string) => {
    // Convert 24-hour to 12-hour format
    const [hours, minutes] = time.split(':')
    const hour = parseInt(hours)
    const ampm = hour >= 12 ? 'PM' : 'AM'
    const hour12 = hour % 12 || 12
    return `${hour12}:${minutes} ${ampm}`
  }

  // Service times from https://actionchapel.net/
  const defaultServiceTimes = [
    { day: "Sunday", time: "8:00 AM", type: "Sunday Service" },
    { day: "Sunday", time: "10:00 AM", type: "Sunday Service" },
    { day: "Wednesday", time: "7:00 PM", type: "Midweek Service" },
    { day: "Thursday", time: "10:00 AM", type: "Dominion Hour" },
    { day: "Friday", time: "7:00 PM", type: "Prayer Encounter" },
    { day: "Monday - Friday", time: "5:30 AM", type: "Command Your Week" }
  ]

  // Ministries and programs based on ACI website structure
  const ministries = [
    { name: "Singles Network", icon: Users, description: "Connect and grow with other singles in our community" },
    { name: "Youth Ministry", icon: Users, description: "Empowering the next generation" },
    { name: "Children's Ministry", icon: Heart, description: "Nurturing young hearts" },
    { name: "Women's Ministry", icon: Users, description: "Building strong women of faith" },
    { name: "Men's Ministry", icon: Users, description: "Developing godly men" },
    { name: "Worship Ministry", icon: Music, description: "Leading in praise and worship" }
  ]

  // Featured sermons/topics from https://actionchapel.net/
  const featuredSermons = [
    { title: "Prayer Moves God", description: "Understanding the power of prayer in our daily lives" },
    { title: "Enforcing Prophetic Decrees", description: "Standing firm on God's promises" },
    { title: "Don't Fight The Process", description: "Embracing God's timing and plan for your life" },
    { title: "Binding The Strong Man", description: "Taking authority through prayer and faith" }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 z-50">
              <div className="w-9 h-9 bg-purple-600 rounded-lg flex items-center justify-center">
                <Church className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-gray-900">
                {organization?.name ? "Action Chapel" : "ChurchFlow"}
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-1">
              <Link to="#about" className="px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 font-medium rounded-lg transition-colors text-sm">
                About
              </Link>
              <Link to="#services" className="px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 font-medium rounded-lg transition-colors text-sm">
                Services
              </Link>
              <Link to="#ministries" className="px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 font-medium rounded-lg transition-colors text-sm">
                Ministries
              </Link>
              <Link to="/events" className="px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 font-medium rounded-lg transition-colors text-sm">
                Events
              </Link>
              <Link to="/giving" className="px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 font-medium rounded-lg transition-colors text-sm">
                Give
              </Link>
              <Link to="#contact" className="px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 font-medium rounded-lg transition-colors text-sm">
                Contact
              </Link>
              <div className="flex items-center gap-2 ml-4 pl-4 border-l border-gray-200">
                <Link to="/login" className="btn-secondary btn-sm flex items-center gap-1.5">
                  <LogIn className="w-4 h-4" />
                  Member Portal
                </Link>
              </div>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={toggleMobileMenu}
              className="lg:hidden p-2 min-h-[44px] min-w-[44px] hover:bg-gray-100 rounded-lg transition-colors z-50 touch-manipulation flex items-center justify-center"
              aria-label="Toggle mobile menu"
            >
              {mobileMenuOpen ? (
                <X className="w-5 h-5 text-gray-600" />
              ) : (
                <Menu className="w-5 h-5 text-gray-600" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu Overlay */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 bg-gray-900/50 z-30 lg:hidden animate-fade-in"
            onClick={closeMobileMenu}
          />
        )}

        {/* Mobile Navigation */}
        <div
          className={`fixed top-16 right-0 h-[calc(100vh-4rem)] bg-white shadow-xl transition-transform duration-300 ease-in-out z-40 lg:hidden w-72 max-w-[85vw] overflow-y-auto border-l border-gray-100 ${
            mobileMenuOpen ? 'translate-x-0' : 'translate-x-full'
          }`}
        >
          <div className="flex flex-col p-4 space-y-1">
            <Link
              to="#about"
              onClick={closeMobileMenu}
              className="text-gray-700 font-medium py-3 px-4 hover:bg-gray-50 rounded-lg transition-colors"
            >
              About
            </Link>
            <Link
              to="#services"
              onClick={closeMobileMenu}
              className="text-gray-700 font-medium py-3 px-4 hover:bg-gray-50 rounded-lg transition-colors"
            >
              Services
            </Link>
            <Link
              to="#ministries"
              onClick={closeMobileMenu}
              className="text-gray-700 font-medium py-3 px-4 hover:bg-gray-50 rounded-lg transition-colors"
            >
              Ministries
            </Link>
            <Link
              to="/events"
              onClick={closeMobileMenu}
              className="text-gray-700 font-medium py-3 px-4 hover:bg-gray-50 rounded-lg transition-colors"
            >
              Events
            </Link>
            <Link
              to="/giving"
              onClick={closeMobileMenu}
              className="text-gray-700 font-medium py-3 px-4 hover:bg-gray-50 rounded-lg transition-colors"
            >
              Give
            </Link>
            <Link
              to="#contact"
              onClick={closeMobileMenu}
              className="text-gray-700 font-medium py-3 px-4 hover:bg-gray-50 rounded-lg transition-colors"
            >
              Contact
            </Link>
            <div className="pt-4 mt-4 border-t border-gray-100">
              <Link
                to="/login"
                onClick={closeMobileMenu}
                className="btn-secondary w-full text-center flex items-center justify-center gap-2"
              >
                <LogIn className="w-4 h-4" />
                Member Portal
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-purple-700 via-purple-800 to-indigo-900 text-white overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
          <div className="grid lg:grid-cols-2 gap-6 items-center">
            {/* Left Side - Hero Announcement or Welcome Message */}
            <div className="text-left">
              {heroAnnouncement ? (
                <div className="space-y-6">
                  <div>
                    <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 leading-tight">
                      {heroAnnouncement.title}
                    </h1>
                    {heroAnnouncement.description && (
                      <p className="text-base md:text-lg text-purple-50 mb-6 leading-relaxed">
                        {heroAnnouncement.description}
                      </p>
                    )}
                  </div>
                  {heroAnnouncement.cta_text && heroAnnouncement.cta_link && (
                    <div className="flex flex-col sm:flex-row gap-4">
                      <Link
                        to={heroAnnouncement.cta_link}
                        className="bg-yellow-500 text-purple-900 border-2 border-yellow-400 hover:bg-yellow-400 hover:border-yellow-300 min-h-[48px] px-8 py-3 text-base font-bold rounded-lg transition-colors shadow-lg inline-flex items-center justify-center"
                      >
                        {heroAnnouncement.cta_text}
                        <ArrowRight className="w-5 h-5 ml-2" />
                      </Link>
                      <button
                        onClick={() => setShowFirstTimerModal(true)}
                        className="bg-yellow-500 text-purple-900 border-2 border-yellow-400 hover:bg-yellow-400 hover:border-yellow-300 min-h-[48px] px-8 py-3 text-base font-bold rounded-lg transition-colors shadow-lg"
                      >
                        I'm New Here
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-6">
                  <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold mb-3 leading-tight">
                    Welcome to {organization?.name ? "Action Chapel International" : "Our Church"}
                  </h1>
                  {organization?.tagline && (
                    <p className="text-lg md:text-xl text-purple-50 mb-4">
                      {organization.tagline}
                    </p>
                  )}
                  <p className="text-base md:text-lg text-white/90 mb-6">
                    One church in many locations worldwide, a place where Divinity meets Humanity
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4">
                    <button
                      onClick={() => setShowFirstTimerModal(true)}
                      className="bg-yellow-500 text-purple-900 border-2 border-yellow-400 hover:bg-yellow-400 hover:border-yellow-300 min-h-[48px] px-8 py-3 text-base font-bold rounded-lg transition-colors shadow-lg"
                    >
                      I'm New Here
                    </button>
                    <Link
                      to="/login"
                      className="bg-white/20 backdrop-blur-sm text-white border-2 border-white/40 hover:bg-white/30 hover:border-white/50 min-h-[48px] px-8 py-3 text-base font-semibold text-center rounded-lg transition-colors"
                    >
                      I'm a Member
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Right Side - Hero Image */}
            <div className="relative">
              <img
                src={heroImageUrl}
                alt="Action Chapel International"
                className="w-full h-auto max-h-[400px] rounded-lg shadow-2xl object-contain"
                onError={(e) => {
                  // Fallback if image fails to load
                  e.currentTarget.style.display = 'none'
                }}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Announcements Section - Right below hero */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 bg-gradient-to-br from-purple-50 to-blue-50">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">Latest Announcements</h2>
          <p className="text-gray-600 text-lg">Stay updated with what's happening</p>
        </div>

        {loadingAnnouncements ? (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-2 border-purple-600 border-t-transparent mx-auto mb-4"></div>
              <p className="text-gray-500 text-sm">Loading announcements...</p>
            </div>
          </div>
        ) : announcements.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {announcements.map((announcement) => (
              <AnnouncementCard key={announcement.id || announcement._id} announcement={announcement} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-gray-300" />
            </div>
            <p className="text-gray-500">No announcements at the moment. Check back soon!</p>
          </div>
        )}
      </section>

      {/* Service Times & Locations Section */}
      <section id="services" className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">Service Times & Location</h2>
            <p className="text-gray-600 text-lg">Join us for worship and fellowship</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Service Times */}
            <div className="card">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">Service Schedule</h3>
              </div>
              <div className="space-y-4">
                {defaultServiceTimes.map((service, index) => (
                  <div key={index} className="flex items-start justify-between pb-4 border-b border-gray-100 last:border-0 last:pb-0">
                    <div>
                      <p className="font-semibold text-gray-900">{service.day}</p>
                      <p className="text-sm text-gray-500">{service.type}</p>
                    </div>
                    <p className="font-medium text-purple-600">{service.time}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Location */}
            <div className="card">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <MapPin className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900">Location</h3>
              </div>
              <div className="space-y-4">
                {organization?.contact_info?.address && (
                  <div>
                    <p className="font-semibold text-gray-900 mb-2">Main Campus</p>
                    <p className="text-gray-600">{organization.contact_info.address}</p>
                  </div>
                )}
                {organization?.contact_info?.phone && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Phone className="w-4 h-4" />
                    <a href={`tel:${organization.contact_info.phone}`} className="hover:text-purple-600">
                      {organization.contact_info.phone}
                    </a>
                  </div>
                )}
                {organization?.contact_info?.email && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Mail className="w-4 h-4" />
                    <a href={`mailto:${organization.contact_info.email}`} className="hover:text-purple-600">
                      {organization.contact_info.email}
                    </a>
                  </div>
                )}
                {/* Map placeholder - can be replaced with actual map integration */}
                <div className="mt-4 h-48 bg-gray-100 rounded-lg flex items-center justify-center">
                  <MapPin className="w-8 h-8 text-gray-400" />
                  <span className="ml-2 text-gray-500">Map coming soon</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* About Us Section */}
      <section id="about" className="bg-white py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">About Us</h2>
            <p className="text-gray-600 text-lg">Who we are and what we believe</p>
          </div>
          <div className="prose prose-lg max-w-none text-center">
            {organization?.description && (
              <div className="text-gray-700 text-lg leading-relaxed mb-6 space-y-4">
                <p>
                  {organization.description}
                </p>
                <p className="text-base text-gray-600">
                  Archbishop Nicholas Duncan-Williams is the Presiding Archbishop and General Overseer of United Denominations of Action Chapel International, headquartered in Accra, Ghana. He is the founder and father of the Charismatic Movement in Ghana and other parts of West Africa.
                </p>
              </div>
            )}
            <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center items-center">
              <a 
                href="https://actionchapel.net/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-purple-600 hover:text-purple-700 font-semibold"
              >
                Visit Our Website
                <ArrowRight className="w-4 h-4" />
              </a>
              <Link 
                to="/events"
                className="inline-flex items-center gap-2 text-purple-600 hover:text-purple-700 font-semibold"
              >
                Find A Location
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Ministries Section */}
      <section id="ministries" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">Ministries</h2>
          <p className="text-gray-600 text-lg">Ways to get involved and grow</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {ministries.map((ministry, index) => {
            const Icon = ministry.icon
            return (
              <div key={index} className="card card-hover">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{ministry.name}</h3>
                <p className="text-gray-600">{ministry.description}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* Online Giving Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-gradient-to-r from-green-600 to-green-700 rounded-xl overflow-hidden shadow-lg">
          <div className="p-8 md:p-12 text-white text-center">
            <div className="w-16 h-16 bg-white/20 rounded-xl flex items-center justify-center mx-auto mb-6">
              <Heart className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Support Our Ministry</h2>
            <p className="text-green-100 text-lg mb-8 max-w-2xl mx-auto">
              Your giving enables us to reach more lives, build communities, and serve those in need.
            </p>
            <Link
              to="/giving"
              className="inline-block bg-white text-green-600 px-8 py-3 min-h-[48px] rounded-lg font-semibold hover:bg-green-50 transition-colors text-base"
            >
              Give Online
            </Link>
          </div>
        </div>
      </section>

      {/* Upcoming Events Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">Upcoming Events</h2>
          <p className="text-gray-600 text-lg">Join us for these special gatherings</p>
        </div>

        {loadingConferences ? (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-2 border-purple-600 border-t-transparent mx-auto mb-4"></div>
              <p className="text-gray-500 text-sm">Loading events...</p>
            </div>
          </div>
        ) : upcomingConferences.length > 0 ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {upcomingConferences.map((conference) => (
                <div key={conference.id} className="card card-hover overflow-hidden">
                  <div className="relative h-40 overflow-hidden -m-6 mb-4">
                    {conference.banner_url ? (
                      <img
                        src={conference.banner_url}
                        alt={conference.name}
                        loading="lazy"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-gradient-to-br from-purple-600 to-purple-700 flex items-center justify-center">
                        <Calendar className="w-10 h-10 text-white/40" />
                      </div>
                    )}
                  </div>
                  <div className="pt-2">
                    <h3 className="font-bold text-gray-900 mb-1 line-clamp-1 text-lg">
                      {conference.name}
                    </h3>
                    {conference.theme && (
                      <p className="text-sm text-purple-600 italic mb-3 line-clamp-1">
                        "{conference.theme}"
                      </p>
                    )}
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{getDateRange(conference.start_date, conference.end_date)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                      <MapPin className="w-3.5 h-3.5" />
                      <span className="line-clamp-1">{conference.venue}</span>
                    </div>
                    <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                      {conference.registration_open ? (
                        <span className="badge-green flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          Registration Open
                        </span>
                      ) : (
                        <span className="badge-gray flex items-center gap-1">
                          <XCircle className="w-3 h-3" />
                          Closed
                        </span>
                      )}
                      <Link
                        to={`/conference/${conference.id}`}
                        className="text-sm font-semibold text-purple-600 hover:text-purple-700 transition-colors flex items-center gap-1"
                      >
                        View Details
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="text-center">
              <Link to="/events" className="btn-primary">
                View All Events
              </Link>
            </div>
          </>
        ) : (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Calendar className="w-8 h-8 text-gray-300" />
            </div>
            <p className="text-gray-500">No upcoming events at the moment. Check back soon!</p>
          </div>
        )}
      </section>

      {/* New Christian / New Member Section */}
      <section className="bg-gradient-to-br from-purple-50 to-blue-50 py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="card max-w-2xl mx-auto bg-white">
            <div className="w-16 h-16 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-6">
              <UserPlus className="w-8 h-8 text-purple-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Are You a New Christian or a New Member?</h2>
            <p className="text-gray-600 text-lg mb-8">
              Welcome! We're excited to have you join our community. Get involved and connect with others as you grow in your faith journey.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register" className="btn-primary min-h-[48px]">
                Get Involved
              </Link>
              <Link to="/login" className="btn-secondary min-h-[48px]">
                Member Portal
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Sermons / Resources Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 bg-white">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">Get The Word On The Go</h2>
          <p className="text-gray-600 text-lg">Powerful teachings to transform your life</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {featuredSermons.map((sermon, index) => (
            <div key={index} className="card card-hover">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                <BookOpen className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">{sermon.title}</h3>
              <p className="text-sm text-gray-600">{sermon.description}</p>
            </div>
          ))}
        </div>
        <div className="text-center mt-8">
          <a 
            href="https://actionchapel.net/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-purple-600 hover:text-purple-700 font-semibold"
          >
            View More Sermons
            <ArrowRight className="w-4 h-4" />
          </a>
        </div>
      </section>

      {/* One Church in Many Locations Section */}
      <section className="bg-gradient-to-br from-blue-600 to-purple-700 py-16 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <div className="w-16 h-16 bg-white/20 rounded-xl flex items-center justify-center mx-auto mb-6">
              <Globe className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-3xl md:text-4xl font-bold mb-4">One Church in Many Locations</h2>
            <p className="text-xl text-white/90 max-w-3xl mx-auto mb-8">
              United Denominations of Action Chapel International has over 500 branch and affiliate churches located in Africa, Europe, and North America.
            </p>
            <Link
              to="/events"
              className="inline-block bg-white text-purple-600 px-8 py-3 min-h-[48px] rounded-lg font-semibold hover:bg-purple-50 transition-colors text-base"
            >
              Find A Location
            </Link>
          </div>
        </div>
      </section>

      {/* Connect Section */}
      <section id="contact" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">Connect With Us</h2>
          <p className="text-gray-600 text-lg mb-4">We'd love to hear from you</p>
          <p className="text-purple-600 font-medium">Find us on all social handles - Stay connected</p>
          {/* Social Media Links */}
          <div className="flex justify-center gap-3 mt-6">
            <a 
              href="https://www.facebook.com/ActionChapelgh/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="w-10 h-10 rounded-lg bg-purple-100 hover:bg-purple-200 flex items-center justify-center text-purple-600 hover:text-purple-700 transition-colors"
              aria-label="Facebook"
              title="Facebook"
            >
              <Facebook className="w-5 h-5" />
            </a>
            <a 
              href="https://www.instagram.com/actionchapelgh/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="w-10 h-10 rounded-lg bg-purple-100 hover:bg-purple-200 flex items-center justify-center text-purple-600 hover:text-purple-700 transition-colors"
              aria-label="Instagram"
              title="Instagram"
            >
              <Instagram className="w-5 h-5" />
            </a>
            <a 
              href="https://twitter.com/Actionchapelgh" 
              target="_blank" 
              rel="noopener noreferrer"
              className="w-10 h-10 rounded-lg bg-purple-100 hover:bg-purple-200 flex items-center justify-center text-purple-600 hover:text-purple-700 transition-colors"
              aria-label="Twitter"
              title="Twitter"
            >
              <Twitter className="w-5 h-5" />
            </a>
            <a 
              href="https://www.youtube.com/@actionchapelgh" 
              target="_blank" 
              rel="noopener noreferrer"
              className="w-10 h-10 rounded-lg bg-purple-100 hover:bg-purple-200 flex items-center justify-center text-purple-600 hover:text-purple-700 transition-colors"
              aria-label="YouTube"
              title="YouTube"
            >
              <Youtube className="w-5 h-5" />
            </a>
            <a 
              href="https://www.tiktok.com/@actionchapelgh" 
              target="_blank" 
              rel="noopener noreferrer"
              className="w-10 h-10 rounded-lg bg-purple-100 hover:bg-purple-200 flex items-center justify-center text-purple-600 hover:text-purple-700 transition-colors"
              aria-label="TikTok"
              title="TikTok"
            >
              <Music className="w-5 h-5" />
            </a>
          </div>
        </div>
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <div className="card text-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Phone className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Call Us</h3>
            {organization?.contact_info?.phone ? (
              <a href={`tel:${organization.contact_info.phone}`} className="text-purple-600 hover:text-purple-700">
                {organization.contact_info.phone}
              </a>
            ) : (
              <p className="text-gray-500">Contact information coming soon</p>
            )}
          </div>
          <div className="card text-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Mail className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Email Us</h3>
            {organization?.contact_info?.email ? (
              <a href={`mailto:${organization.contact_info.email}`} className="text-purple-600 hover:text-purple-700">
                {organization.contact_info.email}
              </a>
            ) : (
              <p className="text-gray-500">Contact information coming soon</p>
            )}
          </div>
          <div className="card text-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <MapPin className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Visit Us</h3>
            {organization?.contact_info?.address ? (
              <p className="text-gray-600">{organization.contact_info.address}</p>
            ) : (
              <p className="text-gray-500">Address coming soon</p>
            )}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            {/* Quick Links */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Quick Links</h4>
              <ul className="space-y-2">
                <li><Link to="#about" className="text-gray-600 hover:text-purple-600">About Us</Link></li>
                <li><Link to="#services" className="text-gray-600 hover:text-purple-600">Services & Times</Link></li>
                <li><Link to="#ministries" className="text-gray-600 hover:text-purple-600">Ministries</Link></li>
                <li><Link to="/events" className="text-gray-600 hover:text-purple-600">Events</Link></li>
                <li><Link to="#contact" className="text-gray-600 hover:text-purple-600">Contact</Link></li>
              </ul>
            </div>

            {/* Member Services */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Member Services</h4>
              <ul className="space-y-2">
                <li><Link to="/login" className="text-gray-600 hover:text-purple-600">Member Portal</Link></li>
                <li><Link to="/register" className="text-gray-600 hover:text-purple-600">Online Membership</Link></li>
                <li><Link to="/giving" className="text-gray-600 hover:text-purple-600">Online Giving</Link></li>
                <li><Link to="/members" className="text-gray-600 hover:text-purple-600">Self Check-In</Link></li>
                <li><Link to="/bus-booking" className="text-gray-600 hover:text-purple-600">Bus Booking</Link></li>
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Resources</h4>
              <ul className="space-y-2">
                <li><Link to="/events" className="text-gray-600 hover:text-purple-600">Events & Conferences</Link></li>
                <li><a href="https://actionchapel.net/" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-purple-600">Sermons & Messages</a></li>
                <li><a href="https://actionchapel.net/" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-purple-600">ACI Affiliate</a></li>
                <li><a href="https://actionchapel.net/" target="_blank" rel="noopener noreferrer" className="text-gray-600 hover:text-purple-600">Graphics & Forms</a></li>
                <li><Link to="/events" className="text-gray-600 hover:text-purple-600">Find A Location</Link></li>
              </ul>
            </div>

            {/* Contact Info */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Connect</h4>
              <p className="text-sm text-gray-500 mb-3">Find us on all social handles - Stay connected</p>
              {organization?.contact_info?.address && (
                <p className="text-gray-600 mb-3">{organization.contact_info.address}</p>
              )}
              {organization?.contact_info?.phone && (
                <p className="text-gray-600 mb-1">
                  <a href={`tel:${organization.contact_info.phone}`} className="hover:text-purple-600">
                    {organization.contact_info.phone}
                  </a>
                </p>
              )}
              {organization?.contact_info?.email && (
                <p className="text-gray-600 mb-4">
                  <a href={`mailto:${organization.contact_info.email}`} className="hover:text-purple-600">
                    {organization.contact_info.email}
                  </a>
                </p>
              )}
              <div className="flex gap-3 flex-wrap">
                <a 
                  href="https://www.facebook.com/ActionChapelgh/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="w-8 h-8 rounded-lg bg-gray-100 hover:bg-purple-100 flex items-center justify-center text-gray-600 hover:text-purple-600 transition-colors"
                  aria-label="Facebook"
                  title="Facebook"
                >
                  <Facebook className="w-4 h-4" />
                </a>
                <a 
                  href="https://www.instagram.com/actionchapelgh/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="w-8 h-8 rounded-lg bg-gray-100 hover:bg-purple-100 flex items-center justify-center text-gray-600 hover:text-purple-600 transition-colors"
                  aria-label="Instagram"
                  title="Instagram"
                >
                  <Instagram className="w-4 h-4" />
                </a>
                <a 
                  href="https://twitter.com/Actionchapelgh" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="w-8 h-8 rounded-lg bg-gray-100 hover:bg-purple-100 flex items-center justify-center text-gray-600 hover:text-purple-600 transition-colors"
                  aria-label="Twitter"
                  title="Twitter"
                >
                  <Twitter className="w-4 h-4" />
                </a>
                <a 
                  href="https://www.youtube.com/@actionchapelgh" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="w-8 h-8 rounded-lg bg-gray-100 hover:bg-purple-100 flex items-center justify-center text-gray-600 hover:text-purple-600 transition-colors"
                  aria-label="YouTube"
                  title="YouTube"
                >
                  <Youtube className="w-4 h-4" />
                </a>
                <a 
                  href="https://www.tiktok.com/@actionchapelgh" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="w-8 h-8 rounded-lg bg-gray-100 hover:bg-purple-100 flex items-center justify-center text-gray-600 hover:text-purple-600 transition-colors"
                  aria-label="TikTok"
                  title="TikTok"
                >
                  <Music className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-200 pt-8 text-center">
            <p className="text-sm text-gray-500">
              &copy; {new Date().getFullYear()} Action Chapel International. All rights reserved.
              {' '}Powered by{' '}
              <a href="https://ailabsafrica.com" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:text-purple-700 hover:underline">
                AI Labs Africa
              </a>
            </p>
          </div>
        </div>
      </footer>

      {/* First Timer Modal */}
      <PublicFirstTimerModal
        isOpen={showFirstTimerModal}
        onClose={() => setShowFirstTimerModal(false)}
        onSuccess={() => {
          setShowFirstTimerModal(false);
        }}
      />
    </div>
  )
}
