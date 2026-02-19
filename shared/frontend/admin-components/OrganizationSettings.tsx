/**
 * Organization Settings Page
 *
 * Configure organization profile, branding, and preferences.
 */

import React, { useState, useEffect } from 'react';
import {
  Save,
  Upload,
  Image as ImageIcon,
  Globe,
  Mail,
  Phone,
  MapPin,
  Palette,
  Key,
  Shield,
  Trash2,
  AlertCircle,
  CheckCircle,
  Building2
} from 'lucide-react';

interface OrganizationSettingsProps {
  organizationId: string;
  apiBaseUrl: string;
  onError?: (error: string) => void;
  onSuccess?: (message: string) => void;
}

export default function OrganizationSettings({
  organizationId,
  apiBaseUrl,
  onError,
  onSuccess
}: OrganizationSettingsProps) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'general' | 'branding' | 'integrations' | 'security'>('general');

  const [generalSettings, setGeneralSettings] = useState({
    name: '',
    display_name: '',
    description: '',
    industry: '',
    website: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    country: ''
  });

  const [brandingSettings, setBrandingSettings] = useState({
    logo_url: '',
    primary_color: '#3B82F6',
    secondary_color: '#8B5CF6',
    accent_color: '#10B981'
  });

  const [integrationSettings, setIntegrationSettings] = useState({
    api_key: '',
    webhook_url: '',
    slack_webhook: '',
    email_notifications_enabled: true,
    sms_notifications_enabled: false
  });

  useEffect(() => {
    loadOrganizationSettings();
  }, [organizationId]);

  const loadOrganizationSettings = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${apiBaseUrl}/api/v1/organizations/${organizationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to load organization settings');

      const data = await response.json();
      setGeneralSettings({
        name: data.name || '',
        display_name: data.display_name || '',
        description: data.description || '',
        industry: data.industry || '',
        website: data.website || '',
        email: data.email || '',
        phone: data.phone || '',
        address: data.address || '',
        city: data.city || '',
        country: data.country || ''
      });

      // Load branding settings if available
      if (data.branding) {
        setBrandingSettings(data.branding);
      }

      // Load integration settings if available
      if (data.integrations) {
        setIntegrationSettings(data.integrations);
      }
    } catch (error) {
      onError?.('Failed to load organization settings');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveGeneral = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${apiBaseUrl}/api/v1/organizations/${organizationId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(generalSettings)
      });

      if (!response.ok) throw new Error('Failed to update settings');

      onSuccess?.('Organization settings updated successfully');
    } catch (error) {
      onError?.('Failed to update organization settings');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveBranding = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${apiBaseUrl}/api/v1/organizations/${organizationId}/branding`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(brandingSettings)
      });

      if (!response.ok) throw new Error('Failed to update branding');

      onSuccess?.('Branding settings updated successfully');
    } catch (error) {
      onError?.('Failed to update branding settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Organization Settings</h1>
        <p className="text-gray-600 mt-1">Configure your organization profile and preferences</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <div className="flex">
            <button
              onClick={() => setActiveTab('general')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'general'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              General
            </button>
            <button
              onClick={() => setActiveTab('branding')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'branding'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Branding
            </button>
            <button
              onClick={() => setActiveTab('integrations')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'integrations'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Integrations
            </button>
            <button
              onClick={() => setActiveTab('security')}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === 'security'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Security
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* General Settings */}
          {activeTab === 'general' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Organization Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Organization Name
                    </label>
                    <input
                      type="text"
                      value={generalSettings.name}
                      disabled
                      className="w-full px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-600"
                    />
                    <p className="text-xs text-gray-500 mt-1">Cannot be changed</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Display Name
                    </label>
                    <input
                      type="text"
                      value={generalSettings.display_name}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, display_name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Description
                    </label>
                    <textarea
                      value={generalSettings.description}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, description: e.target.value })}
                      rows={3}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Globe className="w-4 h-4 inline mr-2" />
                      Industry
                    </label>
                    <input
                      type="text"
                      value={generalSettings.industry}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, industry: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Globe className="w-4 h-4 inline mr-2" />
                      Website
                    </label>
                    <input
                      type="url"
                      value={generalSettings.website}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, website: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Mail className="w-4 h-4 inline mr-2" />
                      Email
                    </label>
                    <input
                      type="email"
                      value={generalSettings.email}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, email: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <Phone className="w-4 h-4 inline mr-2" />
                      Phone
                    </label>
                    <input
                      type="tel"
                      value={generalSettings.phone}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, phone: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      <MapPin className="w-4 h-4 inline mr-2" />
                      Address
                    </label>
                    <input
                      type="text"
                      value={generalSettings.address}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, address: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      City
                    </label>
                    <input
                      type="text"
                      value={generalSettings.city}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, city: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Country
                    </label>
                    <input
                      type="text"
                      value={generalSettings.country}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, country: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  onClick={handleSaveGeneral}
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          )}

          {/* Branding Settings */}
          {activeTab === 'branding' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Logo</h3>
                <div className="flex items-center gap-6">
                  <div className="w-32 h-32 bg-gray-100 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
                    {brandingSettings.logo_url ? (
                      <img src={brandingSettings.logo_url} alt="Logo" className="w-full h-full object-contain rounded-lg" />
                    ) : (
                      <ImageIcon className="w-12 h-12 text-gray-400" />
                    )}
                  </div>
                  <div>
                    <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                      <Upload className="w-4 h-4" />
                      Upload Logo
                    </button>
                    <p className="text-sm text-gray-600 mt-2">PNG, JPG up to 2MB</p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <Palette className="w-5 h-5 inline mr-2" />
                  Brand Colors
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Primary Color
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={brandingSettings.primary_color}
                        onChange={(e) => setBrandingSettings({ ...brandingSettings, primary_color: e.target.value })}
                        className="w-16 h-10 rounded border border-gray-300 cursor-pointer"
                      />
                      <input
                        type="text"
                        value={brandingSettings.primary_color}
                        onChange={(e) => setBrandingSettings({ ...brandingSettings, primary_color: e.target.value })}
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Secondary Color
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={brandingSettings.secondary_color}
                        onChange={(e) => setBrandingSettings({ ...brandingSettings, secondary_color: e.target.value })}
                        className="w-16 h-10 rounded border border-gray-300 cursor-pointer"
                      />
                      <input
                        type="text"
                        value={brandingSettings.secondary_color}
                        onChange={(e) => setBrandingSettings({ ...brandingSettings, secondary_color: e.target.value })}
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Accent Color
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={brandingSettings.accent_color}
                        onChange={(e) => setBrandingSettings({ ...brandingSettings, accent_color: e.target.value })}
                        className="w-16 h-10 rounded border border-gray-300 cursor-pointer"
                      />
                      <input
                        type="text"
                        value={brandingSettings.accent_color}
                        onChange={(e) => setBrandingSettings({ ...brandingSettings, accent_color: e.target.value })}
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>

                {/* Color Preview */}
                <div className="mt-6 p-6 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-700 mb-3">Preview</p>
                  <div className="flex gap-3">
                    <div
                      className="w-20 h-20 rounded-lg shadow-md"
                      style={{ backgroundColor: brandingSettings.primary_color }}
                    />
                    <div
                      className="w-20 h-20 rounded-lg shadow-md"
                      style={{ backgroundColor: brandingSettings.secondary_color }}
                    />
                    <div
                      className="w-20 h-20 rounded-lg shadow-md"
                      style={{ backgroundColor: brandingSettings.accent_color }}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  onClick={handleSaveBranding}
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'Saving...' : 'Save Branding'}
                </button>
              </div>
            </div>
          )}

          {/* Integrations */}
          {activeTab === 'integrations' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <Key className="w-5 h-5 inline mr-2" />
                  API Access
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      API Key
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="password"
                        value={integrationSettings.api_key}
                        readOnly
                        className="flex-1 px-4 py-2 bg-gray-100 border border-gray-300 rounded-lg"
                      />
                      <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                        Regenerate
                      </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">Use this key for API authentication</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Webhook URL
                    </label>
                    <input
                      type="url"
                      value={integrationSettings.webhook_url}
                      onChange={(e) => setIntegrationSettings({ ...integrationSettings, webhook_url: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="https://your-domain.com/webhook"
                    />
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Notification Settings</h3>
                <div className="space-y-3">
                  <label className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer">
                    <div>
                      <p className="font-medium text-gray-900">Email Notifications</p>
                      <p className="text-sm text-gray-600">Receive email alerts for important events</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={integrationSettings.email_notifications_enabled}
                      onChange={(e) => setIntegrationSettings({ ...integrationSettings, email_notifications_enabled: e.target.checked })}
                      className="w-5 h-5 text-blue-600 rounded"
                    />
                  </label>

                  <label className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer">
                    <div>
                      <p className="font-medium text-gray-900">SMS Notifications</p>
                      <p className="text-sm text-gray-600">Get SMS alerts for critical updates</p>
                    </div>
                    <input
                      type="checkbox"
                      checked={integrationSettings.sms_notifications_enabled}
                      onChange={(e) => setIntegrationSettings({ ...integrationSettings, sms_notifications_enabled: e.target.checked })}
                      className="w-5 h-5 text-blue-600 rounded"
                    />
                  </label>
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  onClick={() => {/* Save integrations */}}
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="w-4 h-4" />
                  {saving ? 'Saving...' : 'Save Integrations'}
                </button>
              </div>
            </div>
          )}

          {/* Security */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  <Shield className="w-5 h-5 inline mr-2" />
                  Security Settings
                </h3>
                <div className="space-y-4">
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex gap-3">
                      <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="font-medium text-yellow-900">Two-Factor Authentication</p>
                        <p className="text-sm text-yellow-700 mt-1">
                          Enable 2FA for enhanced security (coming soon)
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">Session Timeout</p>
                        <p className="text-sm text-gray-600">Automatically log out inactive users</p>
                      </div>
                      <select className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        <option value="30">30 minutes</option>
                        <option value="60">1 hour</option>
                        <option value="120">2 hours</option>
                        <option value="240">4 hours</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-red-600 mb-4">
                  <Trash2 className="w-5 h-5 inline mr-2" />
                  Danger Zone
                </h3>
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-red-900">Delete Organization</p>
                      <p className="text-sm text-red-700 mt-1">
                        Permanently delete this organization and all associated data
                      </p>
                    </div>
                    <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
