/**
 * Settings Page - Application Configuration & User Preferences
 *
 * Comprehensive settings page for managing app configuration, user preferences, and system settings
 */

import React, { useState } from 'react';
import {
  User,
  Bell,
  Lock,
  Globe,
  Palette,
  Shield,
  Database,
  Mail,
  Phone,
  Key,
  Save,
  AlertCircle,
  CheckCircle,
  Settings as SettingsIcon,
  Smartphone,
  Monitor,
  Moon,
  Sun,
  Volume2,
  Eye,
  EyeOff
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Settings() {
  const navigate = useNavigate();

  const [profile, setProfile] = useState({
    name: 'Admin User',
    email: 'admin@shield.edu.gh',
    phone: '+233 XX XXX XXXX',
    role: 'School Administrator'
  });

  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    pushNotifications: true,
    smsNotifications: false,
    weeklyReports: true,
    materialUploads: true,
    systemAlerts: true
  });

  const [preferences, setPreferences] = useState({
    language: 'en',
    theme: 'light',
    timezone: 'Africa/Accra',
    dateFormat: 'DD/MM/YYYY',
    currency: 'GHS'
  });

  const [security, setSecurity] = useState({
    twoFactorEnabled: false,
    sessionTimeout: 30,
    passwordLastChanged: '2025-09-15'
  });

  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');

  const handleSave = async () => {
    setSaveStatus('saving');
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaveStatus('success');
    setTimeout(() => setSaveStatus('idle'), 3000);
  };

  const SettingSection = ({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white rounded-lg shadow-sm">
            <Icon className="w-5 h-5 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
      </div>
      <div className="p-6">
        {children}
      </div>
    </div>
  );

  const Toggle = ({ enabled, onChange }: { enabled: boolean; onChange: (value: boolean) => void }) => (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        enabled ? 'bg-blue-600' : 'bg-gray-300'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          enabled ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
              <p className="text-gray-600 mt-1">Manage your account and application preferences</p>
            </div>
            <div className="flex items-center gap-3">
              {saveStatus === 'success' && (
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle className="w-5 h-5" />
                  <span className="text-sm font-medium">Saved successfully!</span>
                </div>
              )}
              <button
                onClick={handleSave}
                disabled={saveStatus === 'saving'}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-4 h-4" />
                {saveStatus === 'saving' ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                onClick={() => navigate('/dashboard')}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="space-y-6">
          {/* Profile Settings */}
          <SettingSection title="Profile Information" icon={User}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                <input
                  type="text"
                  value={profile.name}
                  onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                <input
                  type="email"
                  value={profile.email}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
                <input
                  type="tel"
                  value={profile.phone}
                  onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
                <input
                  type="text"
                  value={profile.role}
                  disabled
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
                />
              </div>
            </div>
          </SettingSection>

          {/* Notification Settings */}
          <SettingSection title="Notification Preferences" icon={Bell}>
            <div className="space-y-4">
              {Object.entries(notifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-900 capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {key === 'emailNotifications' && 'Receive email notifications for important updates'}
                      {key === 'pushNotifications' && 'Get push notifications on your device'}
                      {key === 'smsNotifications' && 'Receive SMS alerts for critical events'}
                      {key === 'weeklyReports' && 'Get weekly summary reports via email'}
                      {key === 'materialUploads' && 'Notify when new materials are uploaded'}
                      {key === 'systemAlerts' && 'Receive system maintenance and update alerts'}
                    </p>
                  </div>
                  <Toggle
                    enabled={value}
                    onChange={(newValue) => setNotifications({ ...notifications, [key]: newValue })}
                  />
                </div>
              ))}
            </div>
          </SettingSection>

          {/* Preferences */}
          <SettingSection title="Application Preferences" icon={Palette}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
                <select
                  value={preferences.language}
                  onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="en">English</option>
                  <option value="tw">Twi</option>
                  <option value="fr">French</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
                <select
                  value={preferences.theme}
                  onChange={(e) => setPreferences({ ...preferences, theme: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto (System)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Timezone</label>
                <select
                  value={preferences.timezone}
                  onChange={(e) => setPreferences({ ...preferences, timezone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="Africa/Accra">Ghana (GMT)</option>
                  <option value="Africa/Lagos">Nigeria (WAT)</option>
                  <option value="Africa/Nairobi">Kenya (EAT)</option>
                  <option value="Africa/Johannesburg">South Africa (SAST)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Currency</label>
                <select
                  value={preferences.currency}
                  onChange={(e) => setPreferences({ ...preferences, currency: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="GHS">GHS (₵)</option>
                  <option value="NGN">NGN (₦)</option>
                  <option value="KES">KES (KSh)</option>
                  <option value="USD">USD ($)</option>
                </select>
              </div>
            </div>
          </SettingSection>

          {/* Security Settings */}
          <SettingSection title="Security & Privacy" icon={Shield}>
            <div className="space-y-6">
              <div className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">Two-Factor Authentication</p>
                  <p className="text-xs text-gray-500 mt-1">Add an extra layer of security to your account</p>
                </div>
                <Toggle
                  enabled={security.twoFactorEnabled}
                  onChange={(value) => setSecurity({ ...security, twoFactorEnabled: value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Session Timeout (minutes)</label>
                <select
                  value={security.sessionTimeout}
                  onChange={(e) => setSecurity({ ...security, sessionTimeout: Number(e.target.value) })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={60}>1 hour</option>
                  <option value={120}>2 hours</option>
                </select>
              </div>

              <div className="flex items-center justify-between py-3 bg-gray-50 rounded-lg px-4">
                <div>
                  <p className="text-sm font-medium text-gray-900">Password</p>
                  <p className="text-xs text-gray-500 mt-1">Last changed: {security.passwordLastChanged}</p>
                </div>
                <button className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                  Change Password
                </button>
              </div>
            </div>
          </SettingSection>

          {/* Danger Zone */}
          <div className="bg-red-50 border border-red-200 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-red-900 mb-2">Danger Zone</h4>
                <p className="text-sm text-red-700 mb-4">
                  These actions are irreversible. Please proceed with caution.
                </p>
                <div className="flex gap-3">
                  <button className="px-4 py-2 text-sm font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-100 transition-colors">
                    Deactivate Account
                  </button>
                  <button className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors">
                    Delete Account
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
