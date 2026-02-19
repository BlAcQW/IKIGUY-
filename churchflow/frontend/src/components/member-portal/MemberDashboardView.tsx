/**
 * Member Dashboard View Component
 *
 * Displays member activity summary, upcoming events, and recent donations.
 * Includes gamification dashboard and auto check-in widget.
 */

import React from 'react';
import { Calendar, DollarSign, Users, TrendingUp, Award, Clock } from 'lucide-react';
import { MemberDashboard } from '../../hooks/useMemberPortal';
import { GamificationDashboard } from './GamificationDashboard';
import { AutoCheckinWidget } from '../proximity-checkin/AutoCheckinWidget';

interface MemberDashboardViewProps {
  dashboard?: MemberDashboard;
  organizationId?: string;
  userId?: string;
}

export default function MemberDashboardView({
  dashboard,
  organizationId,
  userId
}: MemberDashboardViewProps) {
  if (!dashboard) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  const { profile, activity, upcoming_conferences, recent_donations } = dashboard;

  // Handle successful check-in
  const handleCheckinSuccess = (response: any) => {
    console.log('Check-in successful:', response);
    // TODO: Show toast notification with points earned
    // TODO: Refresh dashboard to show updated stats
  };

  return (
    <div className="space-y-6">
      {/* Auto Check-In Widget (floats over content) */}
      {organizationId && userId && (
        <AutoCheckinWidget
          organizationId={organizationId}
          userId={userId}
          onCheckinSuccess={handleCheckinSuccess}
        />
      )}
      {/* Activity Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Events Attended</p>
              <p className="text-3xl font-bold text-purple-600 mt-2">
                {activity.conferences_attended}
              </p>
            </div>
            <div className="bg-purple-100 p-3 rounded-lg">
              <Calendar className="h-8 w-8 text-purple-600" />
            </div>
          </div>
          {activity.last_attendance && (
            <p className="text-xs text-gray-500 mt-2">
              Last: {new Date(activity.last_attendance).toLocaleDateString()}
            </p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Donations Made</p>
              <p className="text-3xl font-bold text-green-600 mt-2">
                {activity.donations_made}
              </p>
            </div>
            <div className="bg-green-100 p-3 rounded-lg">
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </div>
          {activity.last_donation && (
            <p className="text-xs text-gray-500 mt-2">
              Last: {new Date(activity.last_donation).toLocaleDateString()}
            </p>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Volunteer Hours</p>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                {activity.volunteer_hours}
              </p>
            </div>
            <div className="bg-blue-100 p-3 rounded-lg">
              <Clock className="h-8 w-8 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Member Since</p>
              <p className="text-xl font-bold text-gray-800 mt-2">
                {activity.member_since
                  ? new Date(activity.member_since).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'short',
                    })
                  : 'N/A'}
              </p>
            </div>
            <div className="bg-gray-100 p-3 rounded-lg">
              <Award className="h-8 w-8 text-gray-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Gamification Dashboard Widget */}
      {organizationId && userId && (
        <GamificationDashboard
          organizationId={organizationId}
          userId={userId}
        />
      )}

      {/* Cell Group Info */}
      {activity.cell_group && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-3">
            <Users className="h-6 w-6 text-purple-600" />
            <div>
              <p className="text-sm text-gray-600">Cell Group</p>
              <p className="text-lg font-semibold text-gray-800">{activity.cell_group}</p>
            </div>
          </div>
        </div>
      )}

      {/* Two Column Layout for Events and Donations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Conferences */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <Calendar className="h-5 w-5 text-purple-600" />
              <h2 className="text-xl font-semibold">Upcoming Events</h2>
            </div>
          </div>

          <div className="p-6">
            {upcoming_conferences && upcoming_conferences.length > 0 ? (
              <div className="space-y-4">
                {upcoming_conferences.map((conf: any, index: number) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:border-purple-300 transition-colors"
                  >
                    <h3 className="font-semibold text-gray-800">{conf.name || conf.title}</h3>
                    {conf.start_date && (
                      <p className="text-sm text-gray-600 mt-1">
                        {new Date(conf.start_date).toLocaleDateString('en-US', {
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </p>
                    )}
                    {conf.location && (
                      <p className="text-sm text-gray-500 mt-1">{conf.location}</p>
                    )}
                    {conf.registration_status && (
                      <span className="inline-block mt-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                        Registered
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No upcoming events</p>
                <a
                  href="/conferences"
                  className="text-purple-600 hover:text-purple-700 text-sm mt-2 inline-block"
                >
                  Browse events →
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Recent Donations */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <DollarSign className="h-5 w-5 text-green-600" />
              <h2 className="text-xl font-semibold">Recent Donations</h2>
            </div>
          </div>

          <div className="p-6">
            {recent_donations && recent_donations.length > 0 ? (
              <div className="space-y-4">
                {recent_donations.map((donation: any, index: number) => (
                  <div
                    key={index}
                    className="border border-gray-200 rounded-lg p-4 hover:border-green-300 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-gray-800">
                          ${donation.amount?.toFixed(2) || '0.00'}
                        </p>
                        <p className="text-sm text-gray-600 mt-1">
                          {donation.category || 'General Fund'}
                        </p>
                        {donation.created_at && (
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(donation.created_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        {donation.status === 'completed' && (
                          <span className="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                            Completed
                          </span>
                        )}
                        {donation.is_recurring && (
                          <span className="inline-block mt-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            Recurring
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <DollarSign className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No recent donations</p>
                <a
                  href="/giving"
                  className="text-green-600 hover:text-green-700 text-sm mt-2 inline-block"
                >
                  Make a donation →
                </a>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Engagement Score (Future Enhancement) */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg shadow p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-2">Your Engagement</h3>
            <p className="text-purple-100">
              You've attended {activity.conferences_attended} events and made{' '}
              {activity.donations_made} donations. Thank you for being an active member!
            </p>
          </div>
          <TrendingUp className="h-16 w-16 text-purple-200 hidden md:block" />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a
          href="/conferences"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow text-center"
        >
          <Calendar className="h-8 w-8 text-purple-600 mx-auto mb-2" />
          <h3 className="font-semibold text-gray-800">Register for Event</h3>
          <p className="text-sm text-gray-600 mt-1">Browse upcoming conferences</p>
        </a>

        <a
          href="/giving"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow text-center"
        >
          <DollarSign className="h-8 w-8 text-green-600 mx-auto mb-2" />
          <h3 className="font-semibold text-gray-800">Give</h3>
          <p className="text-sm text-gray-600 mt-1">Make a donation</p>
        </a>

        <a
          href="/portal?tab=directory"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow text-center"
        >
          <Users className="h-8 w-8 text-blue-600 mx-auto mb-2" />
          <h3 className="font-semibold text-gray-800">Connect</h3>
          <p className="text-sm text-gray-600 mt-1">View member directory</p>
        </a>
      </div>
    </div>
  );
}
