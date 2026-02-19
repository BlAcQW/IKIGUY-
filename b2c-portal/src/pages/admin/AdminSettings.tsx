import React from 'react';
import AppSettings from '@/components/settings/AppSettings';

/**
 * Admin System Settings Page
 *
 * This page wraps the AppSettings component for admin-specific system configuration.
 * It provides access to global application settings that affect all users.
 */
export default function AdminSettings() {
  return (
    <div className="p-8 pb-12">
      <AppSettings />
    </div>
  );
}
