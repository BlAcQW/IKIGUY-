import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Search, ChevronDown, X, Bus, MapPin, Clock } from 'lucide-react';

interface BusRoute {
  id: string;
  name?: string;
  route_name?: string;
  departure_location: string;
  departure_time: string;
}

interface SearchableBusRouteSelectProps {
  busRoutes: BusRoute[];
  value: string;
  onChange: (routeId: string) => void;
  disabled?: boolean;
  required?: boolean;
}

export default function SearchableBusRouteSelect({
  busRoutes,
  value,
  onChange,
  disabled = false,
  required = false
}: SearchableBusRouteSelectProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Helper function to get route display name
  const getRouteName = (route: BusRoute) => route.name || route.route_name || 'Unnamed Route';

  // Filter bus routes based on search term
  const filteredRoutes = useMemo(() => {
    if (!searchTerm.trim()) return busRoutes;

    const lowerQuery = searchTerm.toLowerCase();
    return busRoutes.filter(route => {
      const routeName = getRouteName(route).toLowerCase();
      const departureLocation = (route.departure_location?.toLowerCase() || '');
      const departureTime = (route.departure_time?.toLowerCase() || '');

      return routeName.includes(lowerQuery) ||
             departureLocation.includes(lowerQuery) ||
             departureTime.includes(lowerQuery);
    });
  }, [busRoutes, searchTerm]);

  // Find selected route for display
  const selectedRoute = busRoutes.find(r => r.id === value);

  // Handle selection
  const handleSelect = (routeId: string) => {
    onChange(routeId);
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
          Math.min(prev + 1, filteredRoutes.length - 1)
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (focusedIndex >= 0 && focusedIndex < filteredRoutes.length) {
          handleSelect(filteredRoutes[focusedIndex].id);
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
          {selectedRoute ? (
            <div className="flex items-center gap-2">
              <Bus className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <div>
                <span className="font-medium">{getRouteName(selectedRoute)}</span>
                <div className="text-xs text-gray-500">
                  {selectedRoute.departure_location} • {selectedRoute.departure_time}
                </div>
              </div>
            </div>
          ) : (
            <span className="text-gray-400">Select a bus route</span>
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
                placeholder="Search bus routes..."
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
            {filteredRoutes.length > 0 ? (
              <ul className="py-1">
                {filteredRoutes.map((route, index) => (
                  <li
                    key={route.id}
                    onClick={() => handleSelect(route.id)}
                    className={`flex items-start gap-3 px-4 py-3 cursor-pointer
                               hover:bg-gray-50 transition-colors min-h-[44px]
                               ${focusedIndex === index ? 'bg-indigo-50' : ''}
                               ${value === route.id ? 'bg-indigo-50 border-l-4 border-indigo-600' : ''}`}
                    style={{ touchAction: 'manipulation' }}
                  >
                    <Bus className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{getRouteName(route)}</div>
                      <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {route.departure_location}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {route.departure_time}
                        </span>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p className="text-sm mb-2">No bus routes found matching "{searchTerm}"</p>
                <p className="text-xs text-gray-400">Try a different search term</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
