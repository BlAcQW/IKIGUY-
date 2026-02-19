/**
 * Member Preferences Page Component
 *
 * Allows members to manage notification and privacy preferences.
 */

import React, { useState } from 'react';
import { Bell, Lock, Globe, Save, AlertCircle } from 'lucide-react';
import {
  useMyPreferences,
  useUpdateMyPreferences,
  NotificationPreferences,
  PrivacyPreferences,
} from '../../hooks/useMemberPortal';

export default function MemberPreferencesPage() {
  const token = localStorage.getItem('access_token');
  const { data: preferences, isLoading, error } = useMyPreferences(token);
  const updateMutation = useUpdateMyPreferences(token);

  const [notificationPrefs, setNotificationPrefs] = useState<NotificationPreferences>({
    email_notifications: true,
    sms_notifications: true,
    push_notifications: true,
    event_reminders: true,
    giving_receipts: true,
    newsletter: true,
    prayer_requests: true,
  });

  const [privacyPrefs, setPrivacyPrefs] = useState<PrivacyPreferences>({
    show_profile_in_directory: true,
    show_phone_number: false,
    show_email: false,
    show_address: false,
    allow_contact_from_members: true,
  });

  const [language, setLanguage] = useState('en');
  const [timezone, setTimezone] = useState('UTC');
  const [hasChanges, setHasChanges] = useState(false);

  // Update state when preferences load
  React.useEffect(() => {
    if (preferences) {
      setNotificationPrefs(preferences.notifications);
      setPrivacyPrefs(preferences.privacy);
      setLanguage(preferences.language);
      setTimezone(preferences.timezone);
    }
  }, [preferences]);

  const handleNotificationChange = (field: keyof NotificationPreferences) => {
    setNotificationPrefs({ ...notificationPrefs, [field]: !notificationPrefs[field] });
    setHasChanges(true);
  };

  const handlePrivacyChange = (field: keyof PrivacyPreferences) => {
    setPrivacyPrefs({ ...privacyPrefs, [field]: !privacyPrefs[field] });
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await updateMutation.mutateAsync({
        notifications: notificationPrefs,
        privacy: privacyPrefs,
        language,
        timezone,
      });
      setHasChanges(false);
      alert('Preferences saved successfully!');
    } catch (err) {
      alert('Failed to save preferences. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 text-red-800">
          <AlertCircle className="h-5 w-5" />
          <span>Failed to load preferences. Please try again.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Notification Preferences */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-6">
          <Bell className="h-5 w-5 text-purple-600" />
          <h2 className="text-xl font-semibold">Notification Preferences</h2>
        </div>

        <p className="text-sm text-gray-600 mb-6">
          Choose how you'd like to receive notifications and updates from us.
        </p>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-800">Email Notifications</p>
              <p className="text-sm text-gray-600">Receive notifications via email</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationPrefs.email_notifications}
                onChange={() => handleNotificationChange('email_notifications')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-800">SMS Notifications</p>
              <p className="text-sm text-gray-600">Receive notifications via text message</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationPrefs.sms_notifications}
                onChange={() => handleNotificationChange('sms_notifications')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-800">Push Notifications</p>
              <p className="text-sm text-gray-600">Receive browser push notifications</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationPrefs.push_notifications}
                onChange={() => handleNotificationChange('push_notifications')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-800">Event Reminders</p>
              <p className="text-sm text-gray-600">Get reminders for upcoming events</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationPrefs.event_reminders}
                onChange={() => handleNotificationChange('event_reminders')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-800">Giving Receipts</p>
              <p className="text-sm text-gray-600">Receive donation receipts and summaries</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationPrefs.giving_receipts}
                onChange={() => handleNotificationChange('giving_receipts')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-800">Newsletter</p>
              <p className="text-sm text-gray-600">Receive church newsletter and updates</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationPrefs.newsletter}
                onChange={() => handleNotificationChange('newsletter')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-800">Prayer Requests</p>
              <p className="text-sm text-gray-600">Get notified about prayer requests</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationPrefs.prayer_requests}
                onChange={() => handleNotificationChange('prayer_requests')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Privacy Preferences */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-6">
          <Lock className="h-5 w-5 text-purple-600" />
          <h2 className="text-xl font-semibold">Privacy Preferences</h2>
        </div>

        <p className="text-sm text-gray-600 mb-6">
          Control what information is visible to other members in the directory.
        </p>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <p className="font-medium text-gray-800">Show Profile in Directory</p>
              <p className="text-sm text-gray-600">
                Make your profile visible in the member directory
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={privacyPrefs.show_profile_in_directory}
                onChange={() => handlePrivacyChange('show_profile_in_directory')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </label>
          </div>

          {privacyPrefs.show_profile_in_directory && (
            <>
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-800">Show Phone Number</p>
                  <p className="text-sm text-gray-600">
                    Display your phone number in the directory
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={privacyPrefs.show_phone_number}
                    onChange={() => handlePrivacyChange('show_phone_number')}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-800">Show Email</p>
                  <p className="text-sm text-gray-600">Display your email in the directory</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={privacyPrefs.show_email}
                    onChange={() => handlePrivacyChange('show_email')}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-800">Show Address</p>
                  <p className="text-sm text-gray-600">Display your address in the directory</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={privacyPrefs.show_address}
                    onChange={() => handlePrivacyChange('show_address')}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-800">Allow Contact from Members</p>
                  <p className="text-sm text-gray-600">
                    Let other members contact you directly
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={privacyPrefs.allow_contact_from_members}
                    onChange={() => handlePrivacyChange('allow_contact_from_members')}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Language and Timezone */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-6">
          <Globe className="h-5 w-5 text-purple-600" />
          <h2 className="text-xl font-semibold">Language & Timezone</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Language</label>
            <select
              value={language}
              onChange={(e) => {
                setLanguage(e.target.value);
                setHasChanges(true);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Timezone</label>
            <select
              value={timezone}
              onChange={(e) => {
                setTimezone(e.target.value);
                setHasChanges(true);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">Eastern Time (US)</option>
              <option value="America/Chicago">Central Time (US)</option>
              <option value="America/Denver">Mountain Time (US)</option>
              <option value="America/Los_Angeles">Pacific Time (US)</option>
              <option value="Europe/London">London</option>
              <option value="Europe/Paris">Paris</option>
              <option value="Asia/Tokyo">Tokyo</option>
            </select>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-end space-x-4">
        {hasChanges && (
          <span className="text-sm text-gray-600">You have unsaved changes</span>
        )}
        <button
          onClick={handleSave}
          disabled={!hasChanges || updateMutation.isPending}
          className="flex items-center space-x-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <Save className="h-5 w-5" />
          <span>{updateMutation.isPending ? 'Saving...' : 'Save Preferences'}</span>
        </button>
      </div>
    </div>
  );
}
