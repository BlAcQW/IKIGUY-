/**
 * Mobile-Optimized Form Field Component
 *
 * Single-column layout with proper spacing and touch-friendly inputs
 */

import React from 'react';

interface MobileFormFieldProps {
  label: string;
  name: string;
  type?: string;
  value: string | number;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  required?: boolean;
  placeholder?: string;
  error?: string;
  helpText?: string;
  disabled?: boolean;
  as?: 'input' | 'textarea' | 'select';
  options?: { value: string; label: string }[];
  rows?: number;
  className?: string;
}

export default function MobileFormField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  required = false,
  placeholder,
  error,
  helpText,
  disabled = false,
  as = 'input',
  options = [],
  rows = 4,
  className = '',
}: MobileFormFieldProps) {
  const inputClasses = `
    w-full px-4 py-3 text-base
    border rounded-lg
    focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500
    disabled:bg-gray-100 disabled:cursor-not-allowed
    ${error ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : 'border-gray-300'}
    transition-colors
  `.trim().replace(/\s+/g, ' ');

  return (
    <div className={`space-y-1 ${className}`}>
      <label htmlFor={name} className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>

      {as === 'input' && (
        <input
          type={type}
          id={name}
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          placeholder={placeholder}
          disabled={disabled}
          className={inputClasses}
        />
      )}

      {as === 'textarea' && (
        <textarea
          id={name}
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          placeholder={placeholder}
          disabled={disabled}
          rows={rows}
          className={inputClasses}
        />
      )}

      {as === 'select' && (
        <select
          id={name}
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          disabled={disabled}
          className={inputClasses}
        >
          <option value="">Select {label}</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      )}

      {helpText && !error && (
        <p className="text-xs text-gray-500 mt-1">{helpText}</p>
      )}

      {error && (
        <p className="text-xs text-red-600 mt-1">{error}</p>
      )}
    </div>
  );
}
