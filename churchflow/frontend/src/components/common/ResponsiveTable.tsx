/**
 * Responsive Table Component
 *
 * Converts to cards on mobile, horizontal scroll on tablet, full table on desktop
 */

import React from 'react';
import { useMediaQuery } from '../../hooks/useMediaQuery';

interface Column {
  key: string;
  label: string;
  className?: string;
  render?: (value: any, row: any) => React.ReactNode;
}

interface ResponsiveTableProps {
  columns: Column[];
  data: any[];
  keyField?: string;
  onRowClick?: (row: any) => void;
  emptyMessage?: string;
  className?: string;
}

export default function ResponsiveTable({
  columns,
  data,
  keyField = 'id',
  onRowClick,
  emptyMessage = 'No data available',
  className = '',
}: ResponsiveTableProps) {
  const isMobile = useMediaQuery('(max-width: 768px)');

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        {emptyMessage}
      </div>
    );
  }

  // Mobile: Card view
  if (isMobile) {
    return (
      <div className="space-y-4">
        {data.map((row) => (
          <div
            key={row[keyField]}
            onClick={() => onRowClick?.(row)}
            className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${
              onRowClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''
            }`}
          >
            {columns.map((col) => (
              <div key={col.key} className="flex justify-between py-2 border-b border-gray-100 last:border-0">
                <span className="font-medium text-gray-600 text-sm">{col.label}</span>
                <span className="text-gray-900 text-sm">
                  {col.render ? col.render(row[col.key], row) : row[col.key]}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  }

  // Desktop: Table view
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                  col.className || ''
                }`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row) => (
            <tr
              key={row[keyField]}
              onClick={() => onRowClick?.(row)}
              className={onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={`px-6 py-4 whitespace-nowrap text-sm ${col.className || ''}`}
                >
                  {col.render ? col.render(row[col.key], row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
