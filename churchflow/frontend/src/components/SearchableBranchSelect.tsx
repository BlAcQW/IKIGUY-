import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, ChevronDown, X, MapPin, Building2 } from 'lucide-react';

interface Branch {
  id: string;
  name: string;
  location: string;
  capacity: number;
}

interface SearchableBranchSelectProps {
  branches: Branch[];
  value: string;
  onChange: (branchId: string) => void;
  disabled?: boolean;
  required?: boolean;
}

export default function SearchableBranchSelect({
  branches,
  value,
  onChange,
  disabled = false,
  required = false
}: SearchableBranchSelectProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter branches based on search term
  const filteredBranches = useMemo(() => {
    if (!searchTerm.trim()) return branches;

    const lowerQuery = searchTerm.toLowerCase();
    return branches.filter(branch =>
      branch.name.toLowerCase().includes(lowerQuery) ||
      (branch.location?.toLowerCase() || '').includes(lowerQuery)
    );
  }, [branches, searchTerm]);

  // Find selected branch for display
  const selectedBranch = branches.find(b => b.id === value);

  // Handle selection
  const handleSelect = (branchId: string) => {
    onChange(branchId);
    setIsOpen(false);
    setSearchTerm('');
    setFocusedIndex(-1);
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex(prev =>
          Math.min(prev + 1, filteredBranches.length - 1)
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (focusedIndex >= 0 && focusedIndex < filteredBranches.length) {
          handleSelect(filteredBranches[focusedIndex].id);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        inputRef.current?.blur();
        break;
    }
  };

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Auto-focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  return (
    <div ref={dropdownRef} className="relative">
      {/* Closed State - Display Selected */}
      {!isOpen && (
        <div
          className="w-full px-4 py-2 border border-gray-300 rounded-lg
                     focus-within:ring-2 focus-within:ring-indigo-500
                     bg-white cursor-pointer flex items-center justify-between
                     min-h-[44px] hover:border-gray-400 transition-colors"
          onClick={() => !disabled && setIsOpen(true)}
        >
          {selectedBranch ? (
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <span className="font-medium">{selectedBranch.name}</span>
              {selectedBranch.location && (
                <span className="text-sm text-gray-500">- {selectedBranch.location}</span>
              )}
            </div>
          ) : (
            <span className="text-gray-400">Select your branch</span>
          )}
          <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
        </div>
      )}

      {/* Open State - Search Input + Results */}
      {isOpen && (
        <div className="absolute z-50 w-full bg-white border border-gray-300 rounded-lg shadow-lg">
          {/* Search Input */}
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search branches..."
                className="w-full pl-10 pr-8 py-2 border border-gray-300 rounded-lg outline-none
                         focus:ring-2 focus:ring-indigo-500"
                autoComplete="off"
                autoCapitalize="none"
                autoCorrect="off"
                style={{ fontSize: '16px' }} // Prevent iOS zoom
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              )}
            </div>
          </div>

          {/* Results Dropdown */}
          <div className="max-h-64 overflow-y-auto overscroll-contain"
               style={{ WebkitOverflowScrolling: 'touch' }}>
            {filteredBranches.length > 0 ? (
              <ul className="py-1">
                {filteredBranches.map((branch, index) => (
                  <li
                    key={branch.id}
                    onClick={() => handleSelect(branch.id)}
                    className={`flex items-start gap-3 px-4 py-3 cursor-pointer
                               hover:bg-gray-50 transition-colors min-h-[44px]
                               ${focusedIndex === index ? 'bg-indigo-50' : ''}
                               ${value === branch.id ? 'bg-indigo-50 border-l-4 border-indigo-600' : ''}`}
                    style={{ touchAction: 'manipulation' }}
                  >
                    <MapPin className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-gray-900">{branch.name}</div>
                      {branch.location && (
                        <div className="text-sm text-gray-500">{branch.location}</div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p className="text-sm">No branches found matching "{searchTerm}"</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
