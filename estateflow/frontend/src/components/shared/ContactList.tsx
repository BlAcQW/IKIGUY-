/**
 * Contact List Component
 *
 * Contact/lead management for campaign targeting.
 * Works with the centralized campaign router.
 *
 * Usage:
 * ```tsx
 * import { ContactList } from '@shared/frontend/campaigns/ContactList';
 *
 * <ContactList
 *   apiBaseUrl="https://api.example.com"
 *   authToken={token}
 *   onContactClick={(contact) => handleView(contact)}
 *   onImportSuccess={() => handleImport()}
 * />
 * ```
 */

import React, { useState, useEffect } from 'react';
import {
  Users,
  Mail,
  Phone,
  Tag,
  Upload,
  Plus,
  Search,
  Filter,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';

// Types
export interface Contact {
  id: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  contact_type: 'lead' | 'customer' | 'prospect' | 'member' | 'student' | 'attendee';
  interest_level: 'hot' | 'warm' | 'cold' | 'unqualified';
  tags: string[];
  segments: string[];
  opt_out_channels: string[];
  total_campaigns_sent: number;
  total_campaigns_opened: number;
  created_at: string;
}

export interface ContactStats {
  total_contacts: number;
  leads: number;
  customers: number;
  prospects: number;
  hot: number;
  warm: number;
  cold: number;
  with_email: number;
  with_phone: number;
  created_this_week: number;
  created_this_month: number;
}

export interface ContactListProps {
  apiBaseUrl: string;
  authToken: string;
  onContactClick?: (contact: Contact) => void;
  onCreateNew?: () => void;
  onImportSuccess?: () => void;
}

export const ContactList: React.FC<ContactListProps> = ({
  apiBaseUrl,
  authToken,
  onContactClick,
  onCreateNew,
  onImportSuccess
}) => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [stats, setStats] = useState<ContactStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterLevel, setFilterLevel] = useState<string>('all');

  useEffect(() => {
    fetchContacts();
    fetchStats();
  }, [filterType, filterLevel, searchTerm]);

  const fetchContacts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterType !== 'all') params.append('contact_type', filterType);
      if (filterLevel !== 'all') params.append('interest_level', filterLevel);
      if (searchTerm) params.append('search', searchTerm);
      params.append('limit', '50');

      const response = await fetch(
        `${apiBaseUrl}/api/v1/campaigns/contacts?${params.toString()}`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setContacts(data.contacts || []);
      }
    } catch (error) {
      console.error('Error fetching contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/campaigns/contacts/stats`,
        {
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleFileImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/campaigns/contacts/import`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`
          },
          body: formData
        }
      );

      if (response.ok) {
        const result = await response.json();
        alert(`Imported ${result.imported} contacts successfully!`);
        fetchContacts();
        fetchStats();
        if (onImportSuccess) onImportSuccess();
      }
    } catch (error) {
      console.error('Error importing contacts:', error);
      alert('Failed to import contacts');
    }
  };

  const getInterestLevelBadge = (level: string) => {
    const colors = {
      hot: 'bg-red-100 text-red-800',
      warm: 'bg-yellow-100 text-yellow-800',
      cold: 'bg-blue-100 text-blue-800',
      unqualified: 'bg-gray-100 text-gray-800'
    };

    const icons = {
      hot: <TrendingUp className="h-3 w-3" />,
      warm: <Minus className="h-3 w-3" />,
      cold: <TrendingDown className="h-3 w-3" />,
      unqualified: <Minus className="h-3 w-3" />
    };

    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${colors[level as keyof typeof colors]}`}>
        {icons[level as keyof typeof icons]}
        {level}
      </span>
    );
  };

  if (loading && !contacts.length) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            icon={<Users className="h-5 w-5" />}
            label="Total Contacts"
            value={stats.total_contacts}
            color="bg-blue-500"
          />
          <StatCard
            icon={<TrendingUp className="h-5 w-5" />}
            label="Hot Leads"
            value={stats.hot}
            color="bg-red-500"
          />
          <StatCard
            icon={<Mail className="h-5 w-5" />}
            label="With Email"
            value={stats.with_email}
            color="bg-green-500"
          />
          <StatCard
            icon={<Phone className="h-5 w-5" />}
            label="With Phone"
            value={stats.with_phone}
            color="bg-purple-500"
          />
        </div>
      )}

      {/* Header with Search and Filters */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex-1 flex items-center gap-4 w-full">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name, email, or phone..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* Type Filter */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="all">All Types</option>
            <option value="lead">Leads</option>
            <option value="customer">Customers</option>
            <option value="prospect">Prospects</option>
          </select>

          {/* Interest Level Filter */}
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="all">All Levels</option>
            <option value="hot">Hot</option>
            <option value="warm">Warm</option>
            <option value="cold">Cold</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 cursor-pointer">
            <Upload className="h-4 w-4" />
            Import CSV
            <input
              type="file"
              accept=".csv"
              onChange={handleFileImport}
              className="hidden"
            />
          </label>

          {onCreateNew && (
            <button
              onClick={onCreateNew}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              <Plus className="h-4 w-4" />
              Add Contact
            </button>
          )}
        </div>
      </div>

      {/* Contact List */}
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        {contacts.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No contacts found. Add contacts or import from CSV to get started!
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Interest
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact Info
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tags
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Engagement
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {contacts.map((contact) => (
                <tr
                  key={contact.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onContactClick?.(contact)}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                        <span className="text-indigo-600 font-medium">
                          {contact.first_name[0]}{contact.last_name[0]}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {contact.first_name} {contact.last_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(contact.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                      {contact.contact_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getInterestLevelBadge(contact.interest_level)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col gap-1">
                      {contact.email && (
                        <div className="flex items-center gap-1 text-sm text-gray-600">
                          <Mail className="h-3 w-3" />
                          {contact.email}
                        </div>
                      )}
                      {contact.phone && (
                        <div className="flex items-center gap-1 text-sm text-gray-600">
                          <Phone className="h-3 w-3" />
                          {contact.phone}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {contact.tags.slice(0, 3).map((tag, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-gray-100 text-gray-700"
                        >
                          <Tag className="h-3 w-3" />
                          {tag}
                        </span>
                      ))}
                      {contact.tags.length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{contact.tags.length - 3} more
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex flex-col">
                      <span>{contact.total_campaigns_sent} campaigns</span>
                      <span className="text-xs text-gray-400">
                        {contact.total_campaigns_opened} opened
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// Helper component for stat cards
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ icon, label, value, color }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center gap-3">
        <div className={`${color} text-white p-3 rounded-lg`}>
          {icon}
        </div>
        <div>
          <p className="text-sm text-gray-600">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value.toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
};

export default ContactList;
