/**
 * Phone Numbers List Component
 * Displays phone numbers with assignment dropdown (following Vapi's UX pattern)
 */

import React, { useState } from 'react';
import { Phone, Copy, Check, Edit, Trash2, User, PhoneCall } from 'lucide-react';
import { PhoneNumber } from '@/lib/phone-api-client';

interface PhoneNumbersListProps {
  phoneNumbers: PhoneNumber[];
  assistants: Array<{ id: string; name: string }>;
  onAssign: (phoneId: string, assistantId: string) => Promise<void>;
  onDelete: (phoneId: string) => Promise<void>;
  onCopy: (number: string) => void;
  onTestCall?: (phoneNumber: string) => void;
  copiedNumber: string | null;
}

export const PhoneNumbersList: React.FC<PhoneNumbersListProps> = ({
  phoneNumbers,
  assistants,
  onAssign,
  onDelete,
  onCopy,
  onTestCall,
  copiedNumber
}) => {
  const [assigningPhone, setAssigningPhone] = useState<string | null>(null);

  const handleAssignment = async (phoneId: string, assistantId: string) => {
    setAssigningPhone(phoneId);
    try {
      await onAssign(phoneId, assistantId);
    } finally {
      setAssigningPhone(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500/10 text-green-500';
      case 'pending':
        return 'bg-yellow-500/10 text-yellow-500';
      case 'porting':
        return 'bg-blue-500/10 text-blue-500';
      case 'failed':
        return 'bg-red-500/10 text-red-500';
      default:
        return 'bg-gray-500/10 text-gray-500';
    }
  };

  const getProviderColor = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'kasaai':
        return 'bg-indigo-500/10 text-indigo-600';
      case 'twilio':
        return 'bg-red-500/10 text-red-600';
      case 'vonage':
        return 'bg-purple-500/10 text-purple-600';
      case 'telnyx':
        return 'bg-blue-500/10 text-blue-600';
      default:
        return 'bg-gray-500/10 text-gray-600';
    }
  };

  if (phoneNumbers.length === 0) {
    return (
      <div className="text-center py-12">
        <Phone className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">No phone numbers</h3>
        <p className="mt-1 text-sm text-gray-500">
          Get started by importing or provisioning a phone number.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg">
      <div className="px-4 lg:px-6 py-4 border-b border-border">
        <h3 className="text-lg font-semibold">Your Phone Numbers</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage phone numbers and assign them to assistants
        </p>
      </div>

      <ul className="divide-y divide-border">
        {phoneNumbers.map((phone) => (
          <li key={phone.id} className="px-4 lg:px-6 py-4 hover:bg-accent/50 transition-colors">
            <div className="flex items-start justify-between gap-4">
              {/* Left side - Phone info */}
              <div className="flex items-start gap-4 flex-1 min-w-0">
                <div className="flex-shrink-0 mt-1">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Phone className="h-5 w-5 text-primary" />
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  {/* Number and status */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-semibold text-foreground">{phone.number}</p>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(phone.status)}`}>
                      {phone.status}
                    </span>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getProviderColor(phone.provider)}`}>
                      {phone.provider}
                    </span>
                  </div>

                  {/* Details */}
                  <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                    <span className="capitalize">{phone.type}</span>
                    <span>•</span>
                    <span>{phone.country}</span>
                    {phone.monthly_cost && (
                      <>
                        <span>•</span>
                        <span>${phone.monthly_cost}/month</span>
                      </>
                    )}
                  </div>

                  {/* Capabilities */}
                  <div className="mt-2 flex items-center gap-2 flex-wrap">
                    {phone.capabilities.map((capability) => (
                      <span
                        key={capability}
                        className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-secondary text-secondary-foreground"
                      >
                        {capability}
                      </span>
                    ))}
                  </div>

                  {/* Assignment Dropdown (Vapi-style) */}
                  <div className="mt-3 max-w-xs">
                    <label className="block text-xs font-medium text-muted-foreground mb-1">
                      Inbound Settings
                    </label>
                    <div className="relative">
                      <select
                        value={phone.assigned_assistant_id || ''}
                        onChange={(e) => handleAssignment(phone.id, e.target.value)}
                        disabled={assigningPhone === phone.id}
                        className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md focus:border-primary focus:ring-1 focus:ring-primary outline-none appearance-none pr-10 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <option value="">No Assistant</option>
                        {assistants.map((assistant) => (
                          <option key={assistant.id} value={assistant.id}>
                            {assistant.name}
                          </option>
                        ))}
                      </select>
                      <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                        <User className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </div>
                    {phone.assigned_assistant_id && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Assigned: {assistants.find(a => a.id === phone.assigned_assistant_id)?.name || 'Unknown'}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Right side - Actions */}
              <div className="flex items-center gap-1 flex-shrink-0">
                {onTestCall && (
                  <button
                    onClick={() => onTestCall(phone.number)}
                    className="p-2 rounded-md hover:bg-green-500/10 transition-colors"
                    title={phone.assigned_assistant_id ? "Test call with assistant" : "Test call"}
                  >
                    <PhoneCall className={`h-4 w-4 ${phone.assigned_assistant_id ? 'text-green-600 hover:text-green-700' : 'text-gray-400 hover:text-gray-500'}`} />
                  </button>
                )}
                <button
                  onClick={() => onCopy(phone.number)}
                  className="p-2 rounded-md hover:bg-accent transition-colors"
                  title="Copy number"
                >
                  {copiedNumber === phone.number ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <Copy className="h-4 w-4 text-muted-foreground" />
                  )}
                </button>
                <button
                  className="p-2 rounded-md hover:bg-accent transition-colors"
                  title="Edit configuration"
                >
                  <Edit className="h-4 w-4 text-muted-foreground" />
                </button>
                <button
                  onClick={() => onDelete(phone.id)}
                  className="p-2 rounded-md hover:bg-destructive/10 transition-colors"
                  title="Delete phone number"
                >
                  <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};
