/**
 * Enhanced Time Picker Component
 *
 * Provides an improved time selection experience with:
 * - Quick preset times
 * - 12/24 hour format support
 * - Custom time input
 * - Better accessibility
 */

import { useState, useRef, useEffect } from 'react'
import { Clock, ChevronDown } from 'lucide-react'

interface TimePickerProps {
  value: string // HH:mm format (24-hour)
  onChange: (value: string) => void
  label?: string
  disabled?: boolean
  required?: boolean
  className?: string
  minTime?: string // Optional minimum time constraint
  maxTime?: string // Optional maximum time constraint
}

// Common preset times for quick selection
const PRESET_TIMES = [
  { label: '6:00 AM', value: '06:00' },
  { label: '7:00 AM', value: '07:00' },
  { label: '8:00 AM', value: '08:00' },
  { label: '9:00 AM', value: '09:00' },
  { label: '10:00 AM', value: '10:00' },
  { label: '11:00 AM', value: '11:00' },
  { label: '12:00 PM', value: '12:00' },
  { label: '1:00 PM', value: '13:00' },
  { label: '2:00 PM', value: '14:00' },
  { label: '3:00 PM', value: '15:00' },
  { label: '4:00 PM', value: '16:00' },
  { label: '5:00 PM', value: '17:00' },
  { label: '6:00 PM', value: '18:00' },
  { label: '7:00 PM', value: '19:00' },
  { label: '8:00 PM', value: '20:00' },
  { label: '9:00 PM', value: '21:00' },
  { label: '10:00 PM', value: '22:00' }
]

export default function TimePicker({
  value,
  onChange,
  label,
  disabled = false,
  required = false,
  className = '',
  minTime,
  maxTime
}: TimePickerProps) {
  const [showDropdown, setShowDropdown] = useState(false)
  const [use24Hour, setUse24Hour] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showDropdown])

  // Convert 24-hour format to 12-hour format for display
  const formatTime12Hour = (time24: string): string => {
    if (!time24) return ''
    const [hours, minutes] = time24.split(':').map(Number)
    const period = hours >= 12 ? 'PM' : 'AM'
    const hours12 = hours % 12 || 12
    return `${hours12}:${minutes.toString().padStart(2, '0')} ${period}`
  }

  // Get display value
  const displayValue = use24Hour ? value : formatTime12Hour(value)

  // Filter preset times based on min/max constraints
  const getFilteredPresets = () => {
    return PRESET_TIMES.filter(preset => {
      if (minTime && preset.value < minTime) return false
      if (maxTime && preset.value > maxTime) return false
      return true
    })
  }

  // Handle preset selection
  const handlePresetSelect = (presetValue: string) => {
    onChange(presetValue)
    setShowDropdown(false)
  }

  // Handle custom time input
  const handleCustomInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value

    // Validate against min/max if provided
    if (minTime && newValue < minTime) return
    if (maxTime && newValue > maxTime) return

    onChange(newValue)
  }

  return (
    <div className={`relative ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label} {required && <span className="text-red-500">*</span>}
        </label>
      )}

      <div className="relative" ref={dropdownRef}>
        {/* Main Input Display */}
        <div
          onClick={() => !disabled && setShowDropdown(!showDropdown)}
          className={`
            w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg
            focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent
            flex items-center justify-between cursor-pointer
            ${disabled ? 'bg-gray-100 cursor-not-allowed' : 'bg-white hover:border-gray-400'}
            transition-colors
          `}
        >
          <div className="flex items-center gap-2 flex-1">
            <Clock className="w-4 h-4 text-gray-400" />
            <span className={value ? 'text-gray-900' : 'text-gray-400'}>
              {displayValue || 'Select time'}
            </span>
          </div>
          <ChevronDown
            className={`w-4 h-4 text-gray-400 transition-transform ${
              showDropdown ? 'rotate-180' : ''
            }`}
          />
        </div>

        {/* Dropdown Menu */}
        {showDropdown && (
          <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-auto">
            {/* Format Toggle */}
            <div className="p-2 border-b border-gray-100 bg-gray-50">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600">Time Format:</span>
                <div className="flex gap-1">
                  <button
                    type="button"
                    onClick={() => setUse24Hour(false)}
                    className={`px-3 py-1 rounded ${
                      !use24Hour
                        ? 'bg-blue-500 text-white'
                        : 'bg-white text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    12h
                  </button>
                  <button
                    type="button"
                    onClick={() => setUse24Hour(true)}
                    className={`px-3 py-1 rounded ${
                      use24Hour
                        ? 'bg-blue-500 text-white'
                        : 'bg-white text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    24h
                  </button>
                </div>
              </div>
            </div>

            {/* Custom Time Input */}
            <div className="p-2 border-b border-gray-100">
              <label className="text-xs text-gray-600 mb-1 block">Custom Time</label>
              <input
                type="time"
                value={value}
                onChange={handleCustomInput}
                min={minTime}
                max={maxTime}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Preset Times */}
            <div className="p-2">
              <div className="text-xs text-gray-600 mb-2 px-2">Quick Select</div>
              <div className="grid grid-cols-2 gap-1">
                {getFilteredPresets().map(preset => (
                  <button
                    key={preset.value}
                    type="button"
                    onClick={() => handlePresetSelect(preset.value)}
                    className={`
                      px-3 py-2 text-sm rounded text-left
                      ${
                        value === preset.value
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                      }
                      transition-colors
                    `}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Validation Messages */}
      {minTime && value && value < minTime && (
        <p className="text-xs text-red-500 mt-1">
          Time must be at or after {use24Hour ? minTime : formatTime12Hour(minTime)}
        </p>
      )}
      {maxTime && value && value > maxTime && (
        <p className="text-xs text-red-500 mt-1">
          Time must be at or before {use24Hour ? maxTime : formatTime12Hour(maxTime)}
        </p>
      )}
    </div>
  )
}
