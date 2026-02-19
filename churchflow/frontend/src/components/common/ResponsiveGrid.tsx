/**
 * Responsive Grid Component
 *
 * Auto-responsive grid that adapts to screen size
 */

import React from 'react';

interface ResponsiveGridProps {
  children: React.ReactNode;
  cols?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  gap?: number;
  className?: string;
}

export default function ResponsiveGrid({
  children,
  cols = { default: 1, md: 2, lg: 3 },
  gap = 4,
  className = '',
}: ResponsiveGridProps) {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    5: 'grid-cols-5',
    6: 'grid-cols-6',
  };

  const gapClass = `gap-${gap}`;

  const colsClass = `
    ${gridCols[cols.default || 1]}
    ${cols.sm ? `sm:${gridCols[cols.sm]}` : ''}
    ${cols.md ? `md:${gridCols[cols.md]}` : ''}
    ${cols.lg ? `lg:${gridCols[cols.lg]}` : ''}
    ${cols.xl ? `xl:${gridCols[cols.xl]}` : ''}
  `.trim().replace(/\s+/g, ' ');

  return (
    <div className={`grid ${colsClass} ${gapClass} ${className}`}>
      {children}
    </div>
  );
}
