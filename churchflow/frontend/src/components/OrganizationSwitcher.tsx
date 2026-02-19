/**
 * Organization Switcher Component
 *
 * Dropdown selector for switching between organizations.
 * Shows current organization and allows quick switching.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Building2, ChevronDown, Check, Crown } from 'lucide-react';
import { useOrganization } from '../contexts/OrganizationContext';

interface OrganizationSwitcherProps {
  className?: string;
  showLabel?: boolean;
}

export default function OrganizationSwitcher({
  className = '',
  showLabel = true
}: OrganizationSwitcherProps) {
  const {
    organizations,
    currentOrganization,
    currentRole,
    isUniversalAdmin,
    setCurrentOrganization
  } = useOrganization();

  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  if (!currentOrganization || organizations.length === 0) {
    return null;
  }

  // Don't show switcher if only one organization
  if (organizations.length === 1) {
    return (
      <div className={`flex items-center gap-2 px-3 py-2 bg-white rounded-lg border border-gray-200 ${className}`}>
        <Building2 className="w-5 h-5 text-gray-600" />
        {showLabel && (
          <span className="text-sm font-medium text-gray-900">
            {currentOrganization.display_name}
          </span>
        )}
      </div>
    );
  }

  const getRoleBadge = (role: string, isUniversal?: boolean) => {
    if (isUniversal) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-800 rounded">
          <Crown className="w-3 h-3" />
          Universal Admin
        </span>
      );
    }

    switch (role.toLowerCase()) {
      case 'admin':
        return (
          <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
            Admin
          </span>
        );
      case 'owner':
        return (
          <span className="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 rounded">
            Owner
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded">
            Member
          </span>
        );
    }
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between gap-2 w-full px-3 py-2 bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <div className="flex items-center gap-2 min-w-0">
          <Building2 className="w-5 h-5 text-gray-600 flex-shrink-0" />
          {showLabel && (
            <span className="text-sm font-medium text-gray-900 truncate">
              {currentOrganization.display_name}
            </span>
          )}
        </div>
        <ChevronDown
          className={`w-4 h-4 text-gray-500 flex-shrink-0 transition-transform ${
            isOpen ? 'transform rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-96 overflow-y-auto">
          <div className="py-2">
            {/* Header */}
            <div className="px-4 py-2 border-b border-gray-100">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Your Organizations
              </p>
            </div>

            {/* Organization List */}
            {organizations.map((membership) => {
              const org = membership.organization;
              const isActive = currentOrganization.id === org.id;

              return (
                <button
                  key={org.id}
                  onClick={() => {
                    if (!isActive) {
                      setCurrentOrganization(org.id);
                    }
                    setIsOpen(false);
                  }}
                  className={`w-full px-4 py-3 flex items-center justify-between gap-3 hover:bg-gray-50 transition-colors ${
                    isActive ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    {/* Organization Icon/Logo */}
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0">
                      {org.logo_url ? (
                        <img
                          src={org.logo_url}
                          alt={org.display_name}
                          className="w-full h-full object-cover rounded-lg"
                        />
                      ) : (
                        <Building2 className="w-5 h-5 text-white" />
                      )}
                    </div>

                    {/* Organization Info */}
                    <div className="text-left min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {org.display_name}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        {getRoleBadge(membership.role, membership.is_universal_admin)}
                      </div>
                    </div>
                  </div>

                  {/* Active Indicator */}
                  {isActive && (
                    <Check className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  )}
                </button>
              );
            })}

            {/* Universal Admin Notice */}
            {isUniversalAdmin && (
              <div className="px-4 py-3 mt-2 border-t border-gray-100">
                <div className="flex items-start gap-2 p-2 bg-purple-50 rounded-lg">
                  <Crown className="w-4 h-4 text-purple-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-medium text-purple-900">
                      Universal Admin Access
                    </p>
                    <p className="text-xs text-purple-700 mt-0.5">
                      You have access to all organizations
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
