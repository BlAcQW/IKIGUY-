/**
 * Member Portal Page - Main member self-service portal
 *
 * Provides member dashboard, profile editing, preferences, and directory.
 */

import React, { useState } from 'react';
import { User, Settings, Activity, Users, Calendar, Heart, Shield } from 'lucide-react';
import { useMemberDashboard } from '../hooks/useMemberPortal';
import { useOrganization } from '../contexts/OrganizationContext';
import MemberProfileEditor from '../components/member-portal/MemberProfileEditor';
import MemberDashboardView from '../components/member-portal/MemberDashboardView';
import MemberPreferencesPage from '../components/member-portal/MemberPreferencesPage';
import MemberDirectoryPage from '../components/member-portal/MemberDirectoryPage';
import MembersDashboardPage from './admin/MembersDashboardPage';

type TabType = 'dashboard' | 'profile' | 'directory' | 'settings' | 'admin';

export default function MemberPortalPage() {
	const [activeTab, setActiveTab] = useState<TabType>('dashboard');
	const token = localStorage.getItem('access_token');
	const { currentOrganization, currentRole, isUniversalAdmin, loading: orgLoading } = useOrganization();
	const organizationId = currentOrganization?.id || localStorage.getItem('current_organization_id');

	const { data: dashboard, isLoading, error } = useMemberDashboard(token, organizationId);

	// Get user ID from token or dashboard
	const userId = dashboard?.profile?.supabase_id || dashboard?.profile?._id || null;

	// Check if user is admin
	const isAdmin = currentRole === 'admin' || currentRole === 'owner' || isUniversalAdmin;

	const tabs = [
		{ id: 'dashboard', label: 'Dashboard', icon: Activity },
		{ id: 'profile', label: 'My Profile', icon: User },
		{ id: 'directory', label: 'Directory', icon: Users },
		...(isAdmin ? [{ id: 'admin' as const, label: 'Member Admin', icon: Shield }] : []),
		{ id: 'settings', label: 'Settings', icon: Settings },
	];

	return (
		<div className="min-h-screen bg-gray-50">
			{/* Header */}
			<div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
					<div className="flex items-center justify-between">
						<div>
							<h1 className="text-3xl font-bold">Member Portal</h1>
							<p className="mt-2 text-purple-100">
								Welcome back, {dashboard?.profile?.full_name || dashboard?.profile?.name || 'Member'}!
							</p>
						</div>
						<div className="hidden md:flex items-center space-x-6">
							<div className="text-center">
								<div className="text-2xl font-bold">{dashboard?.activity?.conferences_attended || 0}</div>
								<div className="text-xs text-purple-100">Events Attended</div>
							</div>
							<div className="text-center">
								<div className="text-2xl font-bold">{dashboard?.activity?.donations_made || 0}</div>
								<div className="text-xs text-purple-100">Donations</div>
							</div>
							<div className="text-center">
								<div className="text-2xl font-bold">{dashboard?.activity?.volunteer_hours || 0}</div>
								<div className="text-xs text-purple-100">Volunteer Hours</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			{/* Navigation Tabs */}
			<div className="bg-white border-b border-gray-200">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<nav className="flex space-x-8" aria-label="Tabs">
						{tabs.map((tab) => {
							const Icon = tab.icon;
							const isActive = activeTab === tab.id;
							return (
								<button
									key={tab.id}
									onClick={() => setActiveTab(tab.id as TabType)}
									className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm
                    ${isActive
											? 'border-purple-500 text-purple-600'
											: 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
										}
                  `}
								>
									<Icon className="h-5 w-5" />
									<span>{tab.label}</span>
								</button>
							);
						})}
					</nav>
				</div>
			</div>

			{/* Content Area */}
			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				{orgLoading || isLoading ? (
					<div className="flex items-center justify-center py-12">
						<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
						<p className="ml-4 text-gray-600">Loading dashboard...</p>
					</div>
				) : error ? (
					<div className="bg-red-50 border border-red-200 rounded-lg p-6">
						<h3 className="text-lg font-semibold text-red-800 mb-2">Error Loading Dashboard</h3>
						<p className="text-red-600">
							{error instanceof Error ? error.message : 'Failed to load member dashboard. Please try refreshing the page.'}
						</p>
						{!organizationId && (
							<p className="text-red-600 mt-2">
								No organization selected. Please select an organization from the settings.
							</p>
						)}
					</div>
				) : !organizationId ? (
					<div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
						<h3 className="text-lg font-semibold text-yellow-800 mb-2">Organization Required</h3>
						<p className="text-yellow-600">
							Please select an organization to view your member dashboard.
						</p>
					</div>
				) : (
					<>
						{activeTab === 'dashboard' && (
							<MemberDashboardView
								dashboard={dashboard}
								organizationId={organizationId}
								userId={userId}
							/>
						)}
						{activeTab === 'profile' && <MemberProfileEditor />}
						{activeTab === 'directory' && <MemberDirectoryPage />}
						{activeTab === 'admin' && isAdmin && <MembersDashboardPage />}
						{activeTab === 'settings' && <MemberPreferencesPage />}
					</>
				)}
			</div>

			{/* Quick Actions FAB (Mobile) */}
			<div className="fixed bottom-20 md:bottom-6 right-6 flex flex-col space-y-3">
				<a
					href="/giving"
					className="bg-green-600 text-white p-4 rounded-full shadow-lg hover:bg-green-700 transition-colors"
					title="Give"
				>
					<Heart className="h-6 w-6" />
				</a>
				<a
					href="/register"
					className="bg-blue-600 text-white p-4 rounded-full shadow-lg hover:bg-blue-700 transition-colors"
					title="Register for Event"
				>
					<Calendar className="h-6 w-6" />
				</a>
			</div>
		</div>
	);
}
