import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Phone, Sparkles, Mail } from 'lucide-react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { useStore } from '../lib/store';
import api from '../lib/api';
import { supabase } from '../lib/supabase';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { setUser } = useStore();
  const [authMethod, setAuthMethod] = useState<'phone' | 'email'>('email'); // Default to email for admin
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [step, setStep] = useState<'phone' | 'otp'>('phone');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSendOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.auth.sendOTP(phone);
      setStep('otp');
    } catch (err: any) {
      setError(err.message || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.auth.verifyOTP(phone, otp);
      // Store access token
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      navigate('/home');
    } catch (err: any) {
      setError(err.message || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Call backend login endpoint
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();

      // Store Supabase access token
      localStorage.setItem('access_token', data.access_token);

      // Set user in store
      setUser(data.user);

      // Navigate to admin page
      navigate('/admin/organizations');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-green-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-2 rounded-full text-sm font-medium mb-4">
            <Sparkles size={16} />
            <span>AI-Powered Event Management</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">EventFlow</h1>
          <p className="text-gray-600">Plan less. Celebrate more.</p>
        </div>

        {/* Login Card */}
        <Card>
          <div className="p-6">
            {/* Auth Method Tabs */}
            <div className="flex gap-2 mb-6 bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setAuthMethod('email')}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${
                  authMethod === 'email'
                    ? 'bg-white text-emerald-600 shadow-sm font-medium'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Mail size={18} />
                <span>Email</span>
              </button>
              <button
                onClick={() => setAuthMethod('phone')}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${
                  authMethod === 'phone'
                    ? 'bg-white text-emerald-600 shadow-sm font-medium'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Phone size={18} />
                <span>Phone</span>
              </button>
            </div>

            <h2 className="text-2xl font-semibold text-gray-900 mb-6 text-center">
              {authMethod === 'email' ? 'Admin Sign In' : (step === 'phone' ? 'Sign In' : 'Verify OTP')}
            </h2>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                {error}
              </div>
            )}

            {authMethod === 'email' ? (
              <form onSubmit={handleEmailLogin} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Mail size={20} className="text-gray-400" />
                    </div>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="admin@ailabsafrica.com"
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    required
                  />
                </div>

                <Button type="submit" className="w-full" loading={loading}>
                  Sign In
                </Button>
              </form>
            ) : step === 'phone' ? (
              <form onSubmit={handleSendOTP} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Phone size={20} className="text-gray-400" />
                    </div>
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+233 XX XXX XXXX"
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <p className="mt-2 text-xs text-gray-500">
                    We'll send you a verification code
                  </p>
                </div>

                <Button type="submit" className="w-full" loading={loading}>
                  Send OTP
                </Button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOTP} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Verification Code
                  </label>
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="Enter 6-digit code"
                    maxLength={6}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-center text-2xl tracking-widest"
                    required
                  />
                  <p className="mt-2 text-xs text-gray-500 text-center">
                    Sent to {phone}
                  </p>
                </div>

                <Button type="submit" className="w-full" loading={loading}>
                  Verify & Sign In
                </Button>

                <button
                  type="button"
                  onClick={() => {
                    setStep('phone');
                    setOtp('');
                    setError('');
                  }}
                  className="w-full text-sm text-emerald-600 hover:text-emerald-700 font-medium"
                >
                  Change phone number
                </button>
              </form>
            )}
          </div>
        </Card>

        {/* Footer */}
        <p className="text-center text-sm text-gray-500 mt-6">
          New to EventFlow?{' '}
          <span className="text-emerald-600 font-medium">
            Get ₵50 credit on signup
          </span>
        </p>
      </div>
    </div>
  );
};
