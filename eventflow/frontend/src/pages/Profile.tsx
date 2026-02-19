import React from 'react';
import { User, Phone, Mail, Building, CreditCard } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../components/Card';
import { useStore } from '../lib/store';

export const Profile: React.FC = () => {
  const { user } = useStore();

  if (!user) {
    return (
      <Card className="text-center py-12">
        <p className="text-gray-600">Please log in to view your profile</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
        <p className="text-gray-600 mt-1">Manage your account settings</p>
      </div>

      {/* Profile Info */}
      <Card>
        <CardHeader title="Personal Information" subtitle="Your account details" />
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-20 h-20 rounded-full bg-emerald-100 flex items-center justify-center">
                <span className="text-3xl font-semibold text-emerald-600">
                  {user.name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">{user.name}</h3>
                <p className="text-gray-600">{user.email || 'No email provided'}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <Phone className="text-gray-600" size={20} />
                <div>
                  <p className="text-xs text-gray-600">Phone</p>
                  <p className="font-medium text-gray-900">{user.phone}</p>
                </div>
              </div>

              {user.email && (
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <Mail className="text-gray-600" size={20} />
                  <div>
                    <p className="text-xs text-gray-600">Email</p>
                    <p className="font-medium text-gray-900">{user.email}</p>
                  </div>
                </div>
              )}

              {user.organization && (
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <Building className="text-gray-600" size={20} />
                  <div>
                    <p className="text-xs text-gray-600">Organization</p>
                    <p className="font-medium text-gray-900">{user.organization}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <CreditCard className="text-gray-600" size={20} />
                <div>
                  <p className="text-xs text-gray-600">Plan</p>
                  <p className="font-medium text-gray-900 capitalize">{user.pricing_tier}</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* App Settings */}
      <Card>
        <CardHeader title="App Settings" subtitle="Configure your preferences" />
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <div>
                <p className="font-medium text-gray-900">Push Notifications</p>
                <p className="text-sm text-gray-600">Receive alerts for tasks and events</p>
              </div>
              <input type="checkbox" className="w-5 h-5 text-emerald-600 rounded" defaultChecked />
            </div>
            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <div>
                <p className="font-medium text-gray-900">Email Notifications</p>
                <p className="text-sm text-gray-600">Get email summaries</p>
              </div>
              <input type="checkbox" className="w-5 h-5 text-emerald-600 rounded" defaultChecked />
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium text-gray-900">SMS Notifications</p>
                <p className="text-sm text-gray-600">Receive SMS updates</p>
              </div>
              <input type="checkbox" className="w-5 h-5 text-emerald-600 rounded" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* About */}
      <Card>
        <CardContent>
          <div className="text-center text-sm text-gray-600">
            <p>EventFlow v0.1.0</p>
            <p className="mt-1">Plan less. Celebrate more.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
