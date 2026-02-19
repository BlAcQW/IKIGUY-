/**
 * Visitor Capture Page
 *
 * Allows church staff to capture first-timers and new converts during service.
 * Features phone validation, immediate welcome messages, and cell assignment.
 *
 * URL: /visitors/capture
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UserPlus,
  Phone,
  Mail,
  User,
  MessageSquare,
  CheckCircle,
  AlertCircle,
  Loader,
  MapPin,
  ArrowLeft,
  Send,
} from 'lucide-react';
import { visitorApi, type Visitor } from '../services/visitorApi';
import PhoneInput from 'react-phone-number-input';
import { isValidPhoneNumber, parsePhoneNumber } from 'libphonenumber-js';
import 'react-phone-number-input/style.css';

interface FormData {
  phone: string;
  name: string;
  email: string;
  first_visit_source: string;
  send_immediate_welcome: boolean;
}

interface FormErrors {
  phone?: string;
  name?: string;
  email?: string;
  first_visit_source?: string;
}

export default function VisitorCapture() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<FormData>({
    phone: '',
    name: '',
    email: '',
    first_visit_source: '',
    send_immediate_welcome: true,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [capturedVisitor, setCapturedVisitor] = useState<Visitor | null>(null);

  const visitSources = [
    'Friend/Family Invitation',
    'Social Media',
    'Google Search',
    'Drove/Walked Past',
    'Event/Conference',
    'Church Website',
    'Other',
  ];

  // Validation
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Phone validation
    if (!formData.phone) {
      newErrors.phone = 'Phone number is required';
    } else if (!isValidPhoneNumber(formData.phone)) {
      newErrors.phone = 'Invalid phone number format';
    }

    // Name validation (optional but recommended)
    if (formData.name && formData.name.trim().length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    }

    // Email validation (optional)
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(false);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Format phone number to E.164 format
      const parsedPhone = parsePhoneNumber(formData.phone);
      const formattedPhone = parsedPhone?.format('E.164') || formData.phone;

      const visitor = await visitorApi.captureVisitor({
        phone: formattedPhone,
        name: formData.name || undefined,
        email: formData.email || undefined,
        first_visit_source: formData.first_visit_source || undefined,
        send_immediate_welcome: formData.send_immediate_welcome,
      });

      setCapturedVisitor(visitor);
      setSubmitSuccess(true);

      // Reset form after 3 seconds
      setTimeout(() => {
        setFormData({
          phone: '',
          name: '',
          email: '',
          first_visit_source: '',
          send_immediate_welcome: true,
        });
        setSubmitSuccess(false);
        setCapturedVisitor(null);
      }, 5000);
    } catch (error: any) {
      console.error('Failed to capture visitor:', error);
      setSubmitError(
        error.response?.data?.detail || 'Failed to capture visitor. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // View visitor details
  const handleViewVisitor = () => {
    if (capturedVisitor) {
      navigate(`/visitors/${capturedVisitor.id}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/visitors')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-500"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                  <UserPlus className="w-6 h-6 text-purple-600" />
                  Capture Visitor
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  Register first-time visitors and new converts
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Success Message */}
        {submitSuccess && capturedVisitor && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-green-900">Visitor Captured Successfully!</h3>
                <p className="text-sm text-green-700 mt-1">
                  {capturedVisitor.name} has been registered.
                  {formData.send_immediate_welcome && ' Welcome message sent!'}
                </p>
                <div className="mt-3 flex gap-3">
                  <button
                    onClick={handleViewVisitor}
                    className="text-sm font-medium text-green-700 hover:text-green-800 underline"
                  >
                    View Visitor Profile
                  </button>
                  <button
                    onClick={() => {
                      setSubmitSuccess(false);
                      setCapturedVisitor(null);
                    }}
                    className="text-sm font-medium text-green-700 hover:text-green-800"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {submitError && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-red-900">Error</h3>
                <p className="text-sm text-red-700 mt-1">{submitError}</p>
              </div>
              <button
                onClick={() => setSubmitError(null)}
                className="text-red-600 hover:text-red-800"
              >
                <span className="sr-only">Dismiss</span>
                ×
              </button>
            </div>
          </div>
        )}

        {/* Capture Form */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Phone Number (Required) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Phone className="w-4 h-4 inline mr-1" />
                Phone Number <span className="text-red-500">*</span>
              </label>
              <PhoneInput
                international
                defaultCountry="GH"
                value={formData.phone}
                onChange={(value) =>
                  setFormData({ ...formData, phone: value || '' })
                }
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent ${
                  errors.phone ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="+233 20 123 4567"
              />
              {errors.phone && (
                <p className="mt-1 text-sm text-red-600">{errors.phone}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">
                Primary contact number for follow-ups
              </p>
            </div>

            {/* Name (Optional but recommended) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <User className="w-4 h-4 inline mr-1" />
                Full Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent ${
                  errors.name ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="John Doe"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}
            </div>

            {/* Email (Optional) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Mail className="w-4 h-4 inline mr-1" />
                Email Address
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent ${
                  errors.email ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="john@example.com"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
              )}
            </div>

            {/* First Visit Source */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                How did you hear about us?
              </label>
              <select
                value={formData.first_visit_source}
                onChange={(e) =>
                  setFormData({ ...formData, first_visit_source: e.target.value })
                }
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">Select a source</option>
                {visitSources.map((source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                ))}
              </select>
            </div>

            {/* Send Welcome Toggle */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-start gap-3">
                  <MessageSquare className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="font-medium text-gray-900">Send Welcome Message</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Automatically send a welcome message via SMS/WhatsApp immediately after
                      capture
                    </p>
                  </div>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.send_immediate_welcome}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        send_immediate_welcome: e.target.checked,
                      })
                    }
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={() => navigate('/visitors')}
                className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:bg-purple-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <Loader className="w-5 h-5 animate-spin" />
                    Capturing...
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    Capture Visitor
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Help Text */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-800">
              <p className="font-medium">Quick Capture Tips:</p>
              <ul className="mt-2 space-y-1 list-disc list-inside">
                <li>Phone number is the only required field</li>
                <li>If visitor returns, their visit count will be incremented</li>
                <li>Welcome messages are sent via SMS/WhatsApp based on preferences</li>
                <li>You can assign visitors to cell groups from their profile page</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
