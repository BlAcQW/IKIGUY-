/**
 * Member Directory Page Component
 *
 * Searchable member directory with infinite scroll, respecting privacy settings.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Users, Mail, Phone, MapPin, Shield, Loader, Trash2, X, Eye, Edit } from 'lucide-react';
import { useOrganization } from '../../contexts/OrganizationContext';
import { useInfiniteScroll } from '../../hooks/useInfiniteScroll';
import { encodeHeaderValue } from '../../lib/header-utils';
import { visitorApi } from '../../services/visitorApi';
import type { MemberDirectoryEntry } from '../../hooks/useMemberPortal';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:30030';
const PAGE_SIZE = 50;

export default function MemberDirectoryPage() {
	const navigate = useNavigate();
	const token = localStorage.getItem('access_token');
	const { currentOrganization, loading: orgLoading, currentRole, isUniversalAdmin } = useOrganization();
	const organizationId = currentOrganization?.id || localStorage.getItem('current_organization_id');

	// Check if current user is admin
	const isAdmin = currentRole === 'admin' || currentRole === 'owner' || isUniversalAdmin;

	const [searchTerm, setSearchTerm] = useState('');
	const [debouncedSearch, setDebouncedSearch] = useState('');
	const [members, setMembers] = useState<MemberDirectoryEntry[]>([]);
	const [total, setTotal] = useState(0);
	const [currentPage, setCurrentPage] = useState(1);
	const [isLoading, setIsLoading] = useState(false);
	const [isLoadingMore, setIsLoadingMore] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [hasMore, setHasMore] = useState(true);

	// Selection state for bulk operations (admin only)
	const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
	const [showDeleteModal, setShowDeleteModal] = useState(false);
	const [isDeleting, setIsDeleting] = useState(false);

	// Debounce search input
	useEffect(() => {
		const timer = setTimeout(() => {
			setDebouncedSearch(searchTerm);
		}, 500);

		return () => clearTimeout(timer);
	}, [searchTerm]);

	// Fetch members - stable function reference using refs
	const fetchMembers = useCallback(async (page: number, append: boolean = false, search: string = '') => {
		if (!token || !organizationId) return;

		try {
			if (append) {
				setIsLoadingMore(true);
			} else {
				setIsLoading(true);
			}
			setError(null);

			const params = new URLSearchParams({
				page: page.toString(),
				page_size: PAGE_SIZE.toString(),
			});
			if (search) {
				params.append('search', search);
			}

			const encodedOrgId = encodeHeaderValue(organizationId);
			if (!encodedOrgId) {
				throw new Error('Invalid organization ID');
			}

			const response = await fetch(
				`${API_BASE_URL}/api/v1/member-portal/directory?${params}`,
				{
					headers: {
						'Authorization': `Bearer ${token}`,
						'X-Organization-ID': encodedOrgId,
					},
				}
			);

			if (!response.ok) {
				throw new Error('Failed to fetch member directory');
			}

			const data = await response.json();
			const newMembers = data.members || [];
			const totalCount = data.total || 0;

			if (append) {
				setMembers(prev => [...prev, ...newMembers]);
			} else {
				setMembers(newMembers);
			}

			setTotal(totalCount);
			setHasMore(data.has_more || (page * PAGE_SIZE < totalCount));
		} catch (err) {
			console.error('Error fetching members:', err);
			setError(err instanceof Error ? err.message : 'Failed to load members');
		} finally {
			setIsLoading(false);
			setIsLoadingMore(false);
		}
	}, [token, organizationId]);

	// Reset and fetch when search changes
	useEffect(() => {
		if (organizationId && token) {
			setMembers([]);
			setCurrentPage(1);
			setHasMore(true);
			fetchMembers(1, false, debouncedSearch);
		}
	}, [organizationId, token, debouncedSearch, fetchMembers]);

	// Load more handler
	const handleLoadMore = useCallback(() => {
		if (!isLoadingMore && hasMore) {
			const nextPage = currentPage + 1;
			setCurrentPage(nextPage);
			fetchMembers(nextPage, true, debouncedSearch);
		}
	}, [currentPage, fetchMembers, hasMore, isLoadingMore, debouncedSearch]);

	// Infinite scroll hook
	const { sentinelRef } = useInfiniteScroll({
		onLoadMore: handleLoadMore,
		hasMore,
		isLoading: isLoading || isLoadingMore,
	});

	// Selection handlers (admin only)
	const handleSelectAll = useCallback((checked: boolean) => {
		if (checked) {
			setSelectedIds(new Set(members.map(m => m._id)));
		} else {
			setSelectedIds(new Set());
		}
	}, [members]);

	const handleSelectOne = useCallback((id: string, checked: boolean) => {
		setSelectedIds(prev => {
			const newSet = new Set(prev);
			if (checked) {
				newSet.add(id);
			} else {
				newSet.delete(id);
			}
			return newSet;
		});
	}, []);

	const handleRefresh = useCallback(() => {
		setMembers([]);
		setCurrentPage(1);
		setHasMore(true);
		setSelectedIds(new Set());
		fetchMembers(1, false, debouncedSearch);
	}, [fetchMembers, debouncedSearch]);

	const handleBulkDelete = async () => {
		if (selectedIds.size === 0) return;

		setIsDeleting(true);
		try {
			const result = await visitorApi.bulkDeleteVisitors(Array.from(selectedIds));
			alert(`Successfully deleted ${result.deleted_count} members`);
			setSelectedIds(new Set());
			setShowDeleteModal(false);
			handleRefresh();
		} catch (err: any) {
			console.error('Failed to delete members:', err);
			alert(err.response?.data?.detail || 'Failed to delete members');
		} finally {
			setIsDeleting(false);
		}
	};

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="bg-white rounded-lg shadow p-6">
				<div className="flex items-center justify-between mb-4">
					<div className="flex items-center space-x-2">
						<Users className="h-6 w-6 text-purple-600" />
						<h2 className="text-2xl font-semibold">Member Directory</h2>
					</div>
					<div className="flex items-center gap-4">
						{isAdmin && selectedIds.size > 0 && (
							<button
								onClick={() => setShowDeleteModal(true)}
								className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-all duration-200"
							>
								<Trash2 className="w-4 h-4" />
								Delete ({selectedIds.size})
							</button>
						)}
						<div className="text-sm text-gray-600">
							{selectedIds.size > 0 ? (
								<span className="text-purple-600 font-medium">{selectedIds.size} selected</span>
							) : (
								`${members.length} of ${total} ${total === 1 ? 'member' : 'members'}`
							)}
						</div>
					</div>
				</div>

				{/* Search Bar */}
				<div className="relative">
					<Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
					<input
						type="text"
						placeholder="Search members by name..."
						value={searchTerm}
						onChange={(e) => setSearchTerm(e.target.value)}
						className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
					/>
				</div>

				<p className="text-sm text-gray-500 mt-2">
					Only members who have opted into the directory are shown. Contact information is only
					visible if members have chosen to share it.
				</p>
			</div>

			{/* Initial Loading State */}
			{isLoading && members.length === 0 && (
				<div className="flex items-center justify-center py-12">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
				</div>
			)}

			{/* Error State */}
			{error && (
				<div className="bg-red-50 border border-red-200 rounded-lg p-4">
					<p className="text-red-800">Failed to load member directory. Please try again.</p>
				</div>
			)}

			{/* Member List */}
			{!orgLoading && !isLoading && !error && organizationId && (
				<>
					{members.length === 0 ? (
						<div className="bg-white rounded-lg shadow p-12 text-center">
							<Users className="h-16 w-16 text-gray-300 mx-auto mb-4" />
							<p className="text-gray-600 text-lg mb-2">
								{searchTerm ? 'No members found' : 'No members in directory'}
							</p>
							<p className="text-gray-500 text-sm">
								{searchTerm
									? 'Try adjusting your search terms'
									: 'Members who opt into the directory will appear here'}
							</p>
						</div>
					) : (
						<div className="bg-white rounded-lg shadow overflow-hidden">
							<div className="overflow-x-auto">
								<table className="w-full">
									<thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
										<tr>
											{isAdmin && (
												<th className="px-4 py-3 text-left">
													<input
														type="checkbox"
														checked={members.length > 0 && selectedIds.size === members.length}
														onChange={(e) => handleSelectAll(e.target.checked)}
														className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
													/>
												</th>
											)}
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
												Member
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
												Role
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
												Contact
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
												Cell Group
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
												Volunteer Roles
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
												Member Since
											</th>
											{isAdmin && (
												<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
													Actions
												</th>
											)}
										</tr>
									</thead>
									<tbody className="divide-y divide-gray-200">
										{members.map((member) => (
											<tr
												key={member._id}
												className={`hover:bg-gray-50 transition-colors cursor-pointer ${selectedIds.has(member._id) ? 'bg-purple-50' : ''}`}
												onClick={() => isAdmin && navigate(`/visitors/${member._id}`)}
											>
												{isAdmin && (
													<td className="px-4 py-4 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
														<input
															type="checkbox"
															checked={selectedIds.has(member._id)}
															onChange={(e) => handleSelectOne(member._id, e.target.checked)}
															className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
														/>
													</td>
												)}
												<td className="px-6 py-4">
													<div className="flex items-center space-x-3">
														{member.profile_picture_url ? (
															<img
																src={member.profile_picture_url}
																alt={member.full_name}
																className="w-10 h-10 rounded-full object-cover flex-shrink-0"
															/>
														) : (
															<div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
																<span className="text-sm font-semibold text-purple-600">
																	{member.full_name
																		?.split(' ')
																		.map((n) => n[0])
																		.join('')
																		.toUpperCase()
																		.slice(0, 2) || '??'}
																</span>
															</div>
														)}
														<div className="flex-1 min-w-0">
															<h3 className="font-medium text-gray-800 truncate">
																{member.full_name}
															</h3>
														</div>
													</div>
												</td>
												<td className="px-6 py-4">
													{member.roles && member.roles.length > 0 ? (
														<div className="flex flex-wrap gap-1">
															{member.roles.map((role, index) => {
																const roleColors: Record<string, string> = {
																	admin: 'bg-red-100 text-red-800',
																	coordinator: 'bg-orange-100 text-orange-800',
																	UNIVERSAL_ADMIN: 'bg-purple-100 text-purple-800',
																	member: 'bg-green-100 text-green-800',
																	user: 'bg-gray-100 text-gray-800',
																};
																const colorClass = roleColors[role] || 'bg-gray-100 text-gray-800';
																const displayName = role === 'UNIVERSAL_ADMIN' ? 'Super Admin' : role.charAt(0).toUpperCase() + role.slice(1);
																return (
																	<span
																		key={index}
																		className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded ${colorClass}`}
																	>
																		<Shield className="h-3 w-3" />
																		{displayName}
																	</span>
																);
															})}
														</div>
													) : (
														<span className="text-sm text-gray-400">-</span>
													)}
												</td>
												<td className="px-6 py-4">
													<div className="space-y-1">
														{member.email && (
															<div className="flex items-center space-x-2 text-sm">
																<Mail className="h-4 w-4 text-gray-400 flex-shrink-0" />
																<a
																	href={`mailto:${member.email}`}
																	className="text-purple-600 hover:text-purple-700 truncate max-w-xs"
																>
																	{member.email}
																</a>
															</div>
														)}
														{member.phone && (
															<div className="flex items-center space-x-2 text-sm">
																<Phone className="h-4 w-4 text-gray-400 flex-shrink-0" />
																<a
																	href={`tel:${member.phone}`}
																	className="text-purple-600 hover:text-purple-700"
																>
																	{member.phone}
																</a>
															</div>
														)}
														{!member.email && !member.phone && (
															<p className="text-sm text-gray-500 italic">Contact info not shared</p>
														)}
													</div>
												</td>
												<td className="px-6 py-4 whitespace-nowrap">
													{member.cell_group ? (
														<div className="flex items-center space-x-2 text-sm">
															<Users className="h-4 w-4 text-gray-400 flex-shrink-0" />
															<span className="font-medium text-gray-800">{member.cell_group}</span>
														</div>
													) : (
														<span className="text-sm text-gray-400">-</span>
													)}
												</td>
												<td className="px-6 py-4">
													{member.volunteer_roles && member.volunteer_roles.length > 0 ? (
														<div className="flex flex-wrap gap-1">
															{member.volunteer_roles.map((role, index) => (
																<span
																	key={index}
																	className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
																>
																	{role}
																</span>
															))}
														</div>
													) : (
														<span className="text-sm text-gray-400">-</span>
													)}
												</td>
												<td className="px-6 py-4 whitespace-nowrap">
													{member.joined_at ? (
														<p className="text-sm text-gray-700">
															{new Date(member.joined_at).toLocaleDateString('en-US', {
																year: 'numeric',
																month: 'short',
															})}
														</p>
													) : (
														<span className="text-sm text-gray-400">-</span>
													)}
												</td>
												{isAdmin && (
													<td className="px-6 py-4 whitespace-nowrap">
														<div className="flex items-center gap-2">
															<button
																onClick={(e) => {
																	e.stopPropagation();
																	navigate(`/visitors/${member._id}`);
																}}
																className="p-2 text-gray-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-all"
																title="View Details"
															>
																<Eye className="w-4 h-4" />
															</button>
															<button
																onClick={(e) => {
																	e.stopPropagation();
																	navigate(`/visitors/${member._id}/edit`);
																}}
																className="p-2 text-gray-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-all"
																title="Edit Member"
															>
																<Edit className="w-4 h-4" />
															</button>
														</div>
													</td>
												)}
											</tr>
										))}
									</tbody>
								</table>
							</div>

							{/* Infinite scroll sentinel and loading indicator */}
							<div ref={sentinelRef} className="py-4">
								{isLoadingMore && (
									<div className="flex items-center justify-center gap-2 text-gray-500">
										<Loader className="h-5 w-5 animate-spin" />
										<span>Loading more members...</span>
									</div>
								)}
								{!hasMore && members.length > 0 && (
									<p className="text-center text-gray-500 text-sm">
										All {total} members loaded
									</p>
								)}
							</div>
						</div>
					)}
				</>
			)}

			{/* Privacy Notice */}
			<div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
				<div className="flex items-start space-x-2">
					<MapPin className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
					<div className="text-sm text-blue-800">
						<p className="font-medium mb-1">Privacy Notice</p>
						<p>
							You can control your own directory visibility and what information you share in the{' '}
							<a href="/portal?tab=settings" className="underline hover:text-blue-900">
								Settings
							</a>{' '}
							tab. Your privacy is important to us.
						</p>
					</div>
				</div>
			</div>

			{/* Delete Confirmation Modal (Admin only) */}
			{showDeleteModal && (
				<div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
					<div className="bg-white rounded-2xl shadow-xl max-w-md w-full">
						<div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4 flex items-center justify-between rounded-t-2xl">
							<div className="flex items-center gap-3">
								<Trash2 className="w-6 h-6 text-white" />
								<h2 className="text-xl font-semibold text-white">Delete Members</h2>
							</div>
							<button
								onClick={() => setShowDeleteModal(false)}
								className="p-2 hover:bg-white/20 rounded-lg transition-colors"
							>
								<X className="w-5 h-5 text-white" />
							</button>
						</div>

						<div className="p-6">
							<p className="text-gray-700 mb-4">
								Are you sure you want to delete <span className="font-bold text-red-600">{selectedIds.size}</span> selected member{selectedIds.size > 1 ? 's' : ''}?
							</p>
							<p className="text-sm text-gray-500 mb-6">
								This action cannot be undone. All data associated with these members will be permanently removed.
							</p>

							<div className="flex gap-3">
								<button
									onClick={() => setShowDeleteModal(false)}
									disabled={isDeleting}
									className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
								>
									Cancel
								</button>
								<button
									onClick={handleBulkDelete}
									disabled={isDeleting}
									className="flex-1 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
								>
									{isDeleting ? (
										<>
											<Loader className="w-5 h-5 animate-spin" />
											<span>Deleting...</span>
										</>
									) : (
										<>
											<Trash2 className="w-5 h-5" />
											<span>Delete</span>
										</>
									)}
								</button>
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
