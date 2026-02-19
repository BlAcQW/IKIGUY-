/**
 * Mobile-Optimized Card Component
 *
 * Touch-friendly card with proper padding and shadows
 */

import React from 'react';

interface MobileCardProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  border?: boolean;
  hover?: boolean;
}

export default function MobileCard({
  children,
  onClick,
  className = '',
  padding = 'md',
  shadow = 'md',
  border = true,
  hover = false,
}: MobileCardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-3 sm:p-4',
    md: 'p-4 sm:p-6',
    lg: 'p-6 sm:p-8',
  }[padding];

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg',
  }[shadow];

  const borderClass = border ? 'border border-gray-200' : '';
  const hoverClass = hover ? 'hover:shadow-lg hover:border-gray-300 transition-all' : '';
  const clickableClass = onClick ? 'cursor-pointer active:scale-98' : '';

  return (
    <div
      onClick={onClick}
      className={`
        bg-white rounded-lg
        ${paddingClasses}
        ${shadowClasses}
        ${borderClass}
        ${hoverClass}
        ${clickableClass}
        ${className}
      `.trim().replace(/\s+/g, ' ')}
    >
      {children}
    </div>
  );
}
