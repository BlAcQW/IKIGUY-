/**
 * Organization Switcher Component
 *
 * Dropdown to view and switch between organizations.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Building2, Check, ChevronDown } from 'lucide-react';
import { useOrganization } from '../lib/organization-context';

export default function OrganizationSwitcher() {
  const { currentOrganization, organizations, loading, switchOrganization } = useOrganization();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  if (loading || organizations.length === 0) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg animate-pulse">
        <Building2 className="w-5 h-5 text-gray-400" />
        <div className="h-4 w-32 bg-gray-300 rounded"></div>
      </div>
    );
  }

  const handleSwitchOrganization = (orgId: string) => {
    switchOrganization(orgId);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-4 py-2.5 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-md transition-all duration-200 min-w-[200px]"
      >
        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <Building2 className="w-5 h-5 text-white" />
        </div>
        <div className="flex-1 text-left">
          <p className="text-sm font-semibold text-gray-900 truncate">
            {currentOrganization?.display_name || 'No Organization'}
          </p>
          <p className="text-xs text-gray-500 truncate">
            {currentOrganization?.industry || 'Select organization'}
          </p>
        </div>
        <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-full min-w-[280px] bg-white border border-gray-200 rounded-xl shadow-xl z-50 overflow-hidden">
          <div className="p-2 border-b border-gray-100 bg-gray-50">
            <p className="text-xs font-semibold text-gray-500 px-3 py-1">
              Switch Organization ({organizations.length})
            </p>
          </div>
          <div className="max-h-[400px] overflow-y-auto">
            {organizations.map((membership) => {
              const isSelected = currentOrganization?.id === membership.organization.id;
              return (
                <button
                  key={membership.organization.id}
                  onClick={() => handleSwitchOrganization(membership.organization.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-blue-50 transition-colors ${
                    isSelected ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    isSelected
                      ? 'bg-gradient-to-br from-blue-500 to-indigo-600'
                      : 'bg-gray-200'
                  }`}>
                    <Building2 className={`w-5 h-5 ${isSelected ? 'text-white' : 'text-gray-600'}`} />
                  </div>
                  <div className="flex-1 text-left min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">
                      {membership.organization.display_name}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {membership.organization.industry || 'No industry'}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        membership.role === 'owner' ? 'bg-yellow-100 text-yellow-800' :
                        membership.role === 'admin' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {membership.role}
                      </span>
                    </div>
                  </div>
                  {isSelected && (
                    <Check className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
