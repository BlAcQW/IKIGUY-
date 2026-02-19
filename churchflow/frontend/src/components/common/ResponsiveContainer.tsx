/**
 * Responsive Container Component
 *
 * Provides consistent responsive padding and max-width across all pages
 */

import React from 'react';

interface ResponsiveContainerProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  noPadding?: boolean;
}

export default function ResponsiveContainer({
  children,
  className = '',
  maxWidth = '7xl',
  noPadding = false,
}: ResponsiveContainerProps) {
  const maxWidthClass = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    '2xl': 'max-w-2xl',
    '7xl': 'max-w-7xl',
    full: 'max-w-full',
  }[maxWidth] || 'max-w-7xl';

  const paddingClass = noPadding ? '' : 'px-4 sm:px-6 lg:px-8';

  return (
    <div className={`container mx-auto ${paddingClass} ${className}`}>
      <div className={`${maxWidthClass} mx-auto`}>
        {children}
      </div>
    </div>
  );
}
