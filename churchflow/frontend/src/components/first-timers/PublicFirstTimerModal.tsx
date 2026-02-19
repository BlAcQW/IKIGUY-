/**
 * Public First Timer Modal Component
 * 
 * An attractive, user-friendly modal for first-time visitors to register.
 * Works for both authenticated and unauthenticated users.
 */

import React, { useState, useEffect } from 'react';
import { X, UserPlus, CheckCircle, Sparkles, Heart, BookOpen, AlertCircle, Loader2, Calendar, MapPin, Phone, Mail, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../../config/api-config';
import { isAuthenticated } from '../../lib/auth-utils';

interface PublicFirstTimerFormData {
  first_name: string;
  last_name: string;
  phone: string;
  email?: string;
  visit_date?: string;
  interest_type: 'visitor' | 'new_convert' | 'existing_member' | 'discipleship';
  wants_membership: boolean;
  wants_discipleship: boolean;
  how_heard_about_us?: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const PublicFirstTimerModal: React.FC<Props> = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState<PublicFirstTimerFormData>({
    first_name: '',
    last_name: '',
    phone: '',
    email: '',
    visit_date: new Date().toISOString().split('T')[0],
    interest_type: 'visitor',
    wants_membership: false,
    wants_discipleship: false,
    how_heard_about_us: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;

  const isLoggedIn = isAuthenticated();

  useEffect(() => {
    if (isOpen && !success) {
      // Reset form when modal opens
      setFormData({
        first_name: '',
        last_name: '',
        phone: '',
        email: '',
        visit_date: new Date().toISOString().split('T')[0],
        interest_type: 'visitor',
        wants_membership: false,
        wants_discipleship: false,
        how_heard_about_us: '',
      });
      setCurrentStep(1);
      setError(null);
      setSuccess(false);
    }
  }, [isOpen, success]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Prepare data
      const dataToSend: any = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        phone: formData.phone.trim(),
        visit_type: 'first_time',
        interest_type: formData.interest_type,
        wants_membership: formData.wants_membership,
        wants_discipleship: formData.wants_discipleship,
      };

      if (formData.email?.trim()) {
        dataToSend.email = formData.email.trim();
      }
      if (formData.visit_date) {
        dataToSend.visit_date = new Date(formData.visit_date).toISOString();
      }
      if (formData.how_heard_about_us?.trim()) {
        dataToSend.how_heard_about_us = formData.how_heard_about_us.trim();
      }

      // Use public endpoint for unauthenticated users, regular endpoint for authenticated users
      const endpoint = isLoggedIn ? API_ENDPOINTS.FIRST_TIMERS.BASE : `${API_ENDPOINTS.FIRST_TIMERS.BASE}/public`;
      
      // Build headers - only include auth token if logged in
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      
      if (isLoggedIn) {
        const token = localStorage.getItem('access_token');
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify(dataToSend),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to submit your information' }));
        throw new Error(errorData.detail || 'Failed to submit your information');
      }

      setSuccess(true);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      console.error('Error submitting first timer form:', err);
      setError(err instanceof Error ? err.message : 'An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
      setError(null);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      setError(null);
    }
  };

  if (!isOpen) return null;

  // Success screen
  if (success) {
    return (
      <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden transform transition-all duration-300">
          {/* Success gradient bar */}
          <div className="h-2 bg-gradient-to-r from-green-500 to-emerald-600" />
          
          <div className="p-8 text-center">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 ring-8 ring-green-100/50">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Thank You!</h2>
            <p className="text-gray-600 mb-6">
              We're excited to have you! Your information has been received and someone from our team will reach out to you soon.
            </p>
            
            <div className="space-y-3">
              <button
                onClick={() => {
                  setSuccess(false);
                  onClose();
                }}
                className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all shadow-lg hover:shadow-xl"
              >
                Close
              </button>
              <Link
                to="/login"
                onClick={onClose}
                className="block w-full px-6 py-3 border-2 border-purple-600 text-purple-600 font-semibold rounded-lg hover:bg-purple-50 transition-all"
              >
                Go to Member Portal
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto"
      onClick={(e) => e.target === e.currentTarget && !loading && onClose()}
    >
      <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full my-8 overflow-hidden transform transition-all duration-200">
        {/* Header with gradient */}
        <div className="relative bg-gradient-to-r from-purple-600 via-purple-700 to-blue-700 px-8 py-6">
          <button
            onClick={onClose}
            disabled={loading}
            className="absolute top-4 right-4 p-2 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-all disabled:opacity-50"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
          
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center ring-4 ring-white/20">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white mb-1">Welcome! We're Glad You're Here</h2>
              <p className="text-purple-100 text-sm">Let us know a bit about you so we can connect</p>
            </div>
          </div>

          {/* Progress steps */}
          <div className="mt-6 flex items-center gap-2">
            {[1, 2, 3].map((step) => (
              <React.Fragment key={step}>
                <div className={`flex-1 h-1.5 rounded-full transition-all ${
                  step <= currentStep ? 'bg-white' : 'bg-white/30'
                }`} />
                {step < totalSteps && (
                  <div className={`w-1.5 h-1.5 rounded-full ${
                    step < currentStep ? 'bg-white' : 'bg-white/30'
                  }`} />
                )}
              </React.Fragment>
            ))}
          </div>
          <div className="mt-2 flex justify-between text-xs text-white/80">
            <span className={currentStep >= 1 ? 'font-semibold' : ''}>Personal Info</span>
            <span className={currentStep >= 2 ? 'font-semibold' : ''}>Visit Details</span>
            <span className={currentStep >= 3 ? 'font-semibold' : ''}>Interests</span>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="p-8 max-h-[calc(100vh-300px)] overflow-y-auto">
            {error && (
              <div className="mb-6 bg-red-50 border-l-4 border-red-500 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-red-800 font-medium">{error}</p>
                </div>
              </div>
            )}

            {/* Step 1: Personal Information */}
            {currentStep === 1 && (
              <div className="space-y-6 animate-fade-in">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <UserPlus className="w-5 h-5 text-purple-600" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900">Personal Information</h3>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      First Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                      placeholder="John"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Last Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                      placeholder="Doe"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Phone Number <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="tel"
                        required
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                        placeholder="+233 24 123 4567"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                      <input
                        type="email"
                        value={formData.email || ''}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                        placeholder="john.doe@example.com"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Visit Details */}
            {currentStep === 2 && (
              <div className="space-y-6 animate-fade-in">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-blue-600" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900">Visit Details</h3>
                </div>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Visit Date
                    </label>
                    <input
                      type="date"
                      value={formData.visit_date || ''}
                      onChange={(e) => setFormData({ ...formData, visit_date: e.target.value })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      How did you hear about us?
                    </label>
                    <input
                      type="text"
                      value={formData.how_heard_about_us || ''}
                      onChange={(e) => setFormData({ ...formData, how_heard_about_us: e.target.value })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                      placeholder="Friend, Social Media, Website, etc."
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Interests */}
            {currentStep === 3 && (
              <div className="space-y-6 animate-fade-in">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Heart className="w-5 h-5 text-green-600" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900">Tell Us Your Interests</h3>
                </div>

                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      What brings you here? <span className="text-red-500">*</span>
                    </label>
                    <div className="grid gap-3">
                      {[
                        { value: 'visitor', label: 'Just Visiting', icon: MapPin, desc: 'I\'m just checking things out' },
                        { value: 'new_convert', label: 'New Believer', icon: Sparkles, desc: 'I recently accepted Christ' },
                        { value: 'existing_member', label: 'Returning Member', icon: UserPlus, desc: 'I\'m a member returning' },
                        { value: 'discipleship', label: 'Want to Grow', icon: BookOpen, desc: 'I want discipleship classes' },
                      ].map((option) => {
                        const Icon = option.icon;
                        return (
                          <label
                            key={option.value}
                            className={`flex items-start gap-4 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                              formData.interest_type === option.value
                                ? 'border-purple-500 bg-purple-50'
                                : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                            }`}
                          >
                            <input
                              type="radio"
                              name="interest_type"
                              value={option.value}
                              checked={formData.interest_type === option.value}
                              onChange={(e) => setFormData({ ...formData, interest_type: e.target.value as any })}
                              className="mt-1 w-4 h-4 text-purple-600 focus:ring-purple-500"
                            />
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <Icon className="w-4 h-4 text-purple-600" />
                                <span className="font-semibold text-gray-900">{option.label}</span>
                              </div>
                              <p className="text-sm text-gray-600 mt-1">{option.desc}</p>
                            </div>
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  <div className="space-y-4 pt-4 border-t border-gray-200">
                    <label className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-purple-300 hover:bg-gray-50 transition-all">
                      <input
                        type="checkbox"
                        checked={formData.wants_membership}
                        onChange={(e) => setFormData({ ...formData, wants_membership: e.target.checked })}
                        className="w-5 h-5 text-purple-600 rounded border-gray-300 focus:ring-purple-500"
                      />
                      <span className="font-medium text-gray-900">I'm interested in becoming a member</span>
                    </label>

                    <label className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-purple-300 hover:bg-gray-50 transition-all">
                      <input
                        type="checkbox"
                        checked={formData.wants_discipleship}
                        onChange={(e) => setFormData({ ...formData, wants_discipleship: e.target.checked })}
                        className="w-5 h-5 text-purple-600 rounded border-gray-300 focus:ring-purple-500"
                      />
                      <span className="font-medium text-gray-900">I'm interested in discipleship classes</span>
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-8 py-6 bg-gray-50 border-t border-gray-200 flex items-center justify-between gap-4">
            <button
              type="button"
              onClick={currentStep === 1 ? onClose : prevStep}
              disabled={loading}
              className="px-6 py-3 text-gray-700 font-medium border-2 border-gray-300 rounded-lg hover:bg-gray-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {currentStep === 1 ? 'Cancel' : 'Back'}
            </button>

            {currentStep < totalSteps ? (
              <button
                type="button"
                onClick={nextStep}
                className="px-8 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
              >
                Continue
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={loading}
                className="px-8 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white font-semibold rounded-lg hover:from-green-700 hover:to-green-800 transition-all shadow-lg hover:shadow-xl disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    Submit
                    <CheckCircle className="w-4 h-4" />
                  </>
                )}
              </button>
            )}
          </div>
        </form>
      </div>

      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default PublicFirstTimerModal;

