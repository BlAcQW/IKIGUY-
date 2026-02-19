/**
 * Organization Switcher Component
 * Enhanced dropdown for switching between organizations with advanced search
 */

import React, { useState, useMemo } from 'react';
import { Building2, Check, ChevronDown, Shield, Search, Users, X } from 'lucide-react';
import { useOrganization } from '@/contexts/OrganizationContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface OrganizationSwitcherProps {
  className?: string;
  variant?: 'default' | 'compact' | 'prominent';
  showSearch?: boolean;
}

const roleLabels: Record<string, string> = {
  UNIVERSAL_ADMIN: 'Universal Admin',
  OWNER: 'Owner',
  ADMIN: 'Admin',
  MANAGER: 'Manager',
  MEMBER: 'Member',
  VIEWER: 'Viewer',
};

const roleBadgeColors: Record<string, string> = {
  UNIVERSAL_ADMIN: 'bg-purple-100 text-purple-700 border-purple-300',
  OWNER: 'bg-blue-100 text-blue-700 border-blue-300',
  ADMIN: 'bg-green-100 text-green-700 border-green-300',
  MANAGER: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  MEMBER: 'bg-gray-100 text-gray-700 border-gray-300',
  VIEWER: 'bg-slate-100 text-slate-700 border-slate-300',
};

export function OrganizationSwitcher({
  className,
  variant = 'default',
  showSearch = true
}: OrganizationSwitcherProps) {
  const {
    currentOrganization,
    organizations,
    allOrganizations,
    isLoading,
    isLoadingAll,
    isUniversalAdmin,
    currentRole,
    switchOrganization,
  } = useOrganization();

  const [searchQuery, setSearchQuery] = useState('');
  const [industryFilter, setIndustryFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Get unique industries from all organizations
  const industries = useMemo(() => {
    const allOrgs = [...organizations.map(o => o.organization), ...allOrganizations];
    const uniqueIndustries = new Set(allOrgs.map(o => o.industry).filter(Boolean));
    return Array.from(uniqueIndustries).sort();
  }, [organizations, allOrganizations]);

  // Filter organizations based on search and filters
  const filteredMemberOrgs = useMemo(() => {
    let filtered = organizations;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(org =>
        org.organization.name.toLowerCase().includes(query) ||
        org.organization.display_name.toLowerCase().includes(query) ||
        org.organization.description?.toLowerCase().includes(query)
      );
    }

    // Industry filter
    if (industryFilter !== 'all') {
      filtered = filtered.filter(org => org.organization.industry === industryFilter);
    }

    // Status filter
    if (statusFilter !== 'all') {
      const isActive = statusFilter === 'active';
      filtered = filtered.filter(org => org.organization.is_active === isActive);
    }

    return filtered;
  }, [organizations, searchQuery, industryFilter, statusFilter]);

  // Filter all organizations (universal admin only)
  const filteredAllOrgs = useMemo(() => {
    if (!isUniversalAdmin) return [];

    let filtered = allOrganizations;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(org =>
        org.name.toLowerCase().includes(query) ||
        org.display_name.toLowerCase().includes(query) ||
        org.description?.toLowerCase().includes(query)
      );
    }

    // Industry filter
    if (industryFilter !== 'all') {
      filtered = filtered.filter(org => org.industry === industryFilter);
    }

    // Status filter
    if (statusFilter !== 'all') {
      const isActive = statusFilter === 'active';
      filtered = filtered.filter(org => org.is_active === isActive);
    }

    // Exclude organizations user is already a member of
    const memberOrgIds = new Set(organizations.map(o => o.organization_id));
    filtered = filtered.filter(org => !memberOrgIds.has(org.id));

    return filtered;
  }, [allOrganizations, searchQuery, industryFilter, statusFilter, isUniversalAdmin, organizations]);

  if (isLoading) {
    return (
      <div className={cn("animate-pulse", className)}>
        <div className="h-10 bg-muted rounded-md"></div>
      </div>
    );
  }

  // Show for universal admins even if no memberships (they can access all orgs)
  if (!currentOrganization || (organizations.length === 0 && !isUniversalAdmin)) {
    return null;
  }

  const handleSwitch = async (orgId: string) => {
    if (orgId !== currentOrganization?.id) {
      await switchOrganization(orgId);
      // Note: Page reload removed - using state updates for smooth transition
      // If needed for specific pages, can call with forceReload: true
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setIndustryFilter('all');
    setStatusFilter('all');
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "w-full justify-between",
            variant === 'compact' && "h-9",
            variant === 'prominent' && "h-12 text-base",
            className
          )}
        >
          <div className="flex items-center gap-2 min-w-0">
            <Building2 className={cn(
              "flex-shrink-0 text-gray-600",
              variant === 'prominent' ? "h-5 w-5" : "h-4 w-4"
            )} />
            <span className="truncate text-sm">
              {currentOrganization?.display_name || currentOrganization?.name || 'Select Organization'}
            </span>
          </div>
          <ChevronDown className="h-4 w-4 opacity-50 flex-shrink-0" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="w-96">
        <DropdownMenuLabel>
          <div className="flex flex-col">
            <span className="text-xs text-gray-600">
              {currentOrganization ? 'Current Organization' : 'Select Organization'}
            </span>
            {currentOrganization && (
              <span className="font-medium">
                {currentOrganization.display_name || currentOrganization.name}
              </span>
            )}
            {currentRole && (
              <div className="mt-1">
                <span
                  className={cn(
                    "text-xs px-2 py-0.5 rounded-full border inline-flex items-center gap-1",
                    roleBadgeColors[currentRole] || roleBadgeColors.VIEWER
                  )}
                >
                  {currentRole === 'UNIVERSAL_ADMIN' && <Shield className="h-3 w-3" />}
                  {roleLabels[currentRole] || currentRole}
                </span>
              </div>
            )}
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        {/* Search and Filters */}
        {showSearch && (organizations.length > 3 || (isUniversalAdmin && allOrganizations.length > 0)) && (
          <div className="px-2 py-2 space-y-2">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search organizations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9 text-sm"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                >
                  <X className="h-3 w-3 text-gray-400" />
                </button>
              )}
            </div>

            {/* Filters */}
            {isUniversalAdmin && industries.length > 0 && (
              <div className="flex gap-2">
                <Select value={industryFilter} onValueChange={setIndustryFilter}>
                  <SelectTrigger className="h-8 text-xs flex-1">
                    <SelectValue placeholder="Industry" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Industries</SelectItem>
                    {industries.map((industry) => (
                      <SelectItem key={industry} value={industry}>
                        {industry}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="h-8 text-xs w-24">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>

                {(searchQuery || industryFilter !== 'all' || statusFilter !== 'all') && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearFilters}
                    className="h-8 px-2"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            )}
          </div>
        )}

        <DropdownMenuSeparator />

        <div className="max-h-[400px] overflow-y-auto">
          {/* User's Organizations */}
          {filteredMemberOrgs.length > 0 && (
            <>
              <div className="px-2 py-1.5">
                <span className="text-xs font-medium text-gray-600 flex items-center gap-1">
                  <Users className="h-3 w-3" />
                  My Organizations ({filteredMemberOrgs.length})
                </span>
              </div>

              {filteredMemberOrgs.map((membership) => {
                const isActive = membership.organization_id === currentOrganization?.id;
                const org = membership.organization;

                return (
                  <DropdownMenuItem
                    key={membership.id}
                    onClick={() => handleSwitch(membership.organization_id)}
                    className={cn(
                      "flex items-start gap-2 p-3 cursor-pointer",
                      isActive && "bg-accent"
                    )}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium truncate">
                          {org.display_name || org.name}
                        </span>
                        {isActive && <Check className="h-4 w-4 text-indigo-600 flex-shrink-0" />}
                      </div>

                      {org.description && (
                        <p className="text-xs text-gray-600 mt-0.5 truncate">
                          {org.description}
                        </p>
                      )}

                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <span
                          className={cn(
                            "text-xs px-1.5 py-0.5 rounded border",
                            roleBadgeColors[membership.role] || roleBadgeColors.VIEWER
                          )}
                        >
                          {roleLabels[membership.role] || membership.role}
                        </span>

                        {org.industry && (
                          <span className="text-xs text-gray-600">
                            {org.industry}
                          </span>
                        )}

                        {!org.is_active && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                            Inactive
                          </span>
                        )}
                      </div>
                    </div>
                  </DropdownMenuItem>
                );
              })}
            </>
          )}

          {/* All Organizations (Universal Admin Only) */}
          {isUniversalAdmin && filteredAllOrgs.length > 0 && (
            <>
              <DropdownMenuSeparator />
              <div className="px-2 py-1.5 bg-purple-50">
                <span className="text-xs font-medium text-purple-700 flex items-center gap-1">
                  <Shield className="h-3 w-3" />
                  All Organizations ({filteredAllOrgs.length})
                  {isLoadingAll && <span className="text-xs ml-1">(Loading...)</span>}
                </span>
              </div>

              {filteredAllOrgs.map((org) => (
                <DropdownMenuItem
                  key={org.id}
                  onClick={() => handleSwitch(org.id)}
                  className="flex items-start gap-2 p-3 cursor-pointer bg-purple-50/50 hover:bg-purple-100/50"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">
                        {org.display_name || org.name}
                      </span>
                    </div>

                    {org.description && (
                      <p className="text-xs text-gray-600 mt-0.5 truncate">
                        {org.description}
                      </p>
                    )}

                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      <span className="text-xs px-1.5 py-0.5 rounded border bg-purple-100 text-purple-700 border-purple-300">
                        Universal Access
                      </span>

                      {org.industry && (
                        <span className="text-xs text-gray-600">
                          {org.industry}
                        </span>
                      )}

                      {!org.is_active && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">
                          Inactive
                        </span>
                      )}
                    </div>
                  </div>
                </DropdownMenuItem>
              ))}
            </>
          )}

          {/* No Results */}
          {filteredMemberOrgs.length === 0 && filteredAllOrgs.length === 0 && (searchQuery || industryFilter !== 'all' || statusFilter !== 'all') && (
            <div className="px-4 py-6 text-center text-sm text-gray-500">
              No organizations found matching your filters.
              <button
                onClick={clearFilters}
                className="block mx-auto mt-2 text-indigo-600 hover:text-indigo-700 underline"
              >
                Clear filters
              </button>
            </div>
          )}
        </div>

        {isUniversalAdmin && (
          <>
            <DropdownMenuSeparator />
            <div className="px-2 py-2 bg-purple-50/50">
              <div className="flex items-center gap-2 text-xs">
                <Shield className="h-3 w-3 text-purple-600" />
                <span className="text-gray-600">
                  Universal Admin: Access to {allOrganizations.length} total organizations
                </span>
              </div>
            </div>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
