/**
 * WhatsApp Button Editor Component
 *
 * Allows configuration of interactive buttons for WhatsApp messages
 * Supports reply buttons, URL buttons, and phone number buttons (max 3)
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Plus, X, MessageSquare, ExternalLink, Phone, AlertCircle } from 'lucide-react';
import { WhatsAppButton } from '@/lib/whatsapp-campaigns-api';

interface WhatsAppButtonEditorProps {
  buttons: WhatsAppButton[];
  onChange: (buttons: WhatsAppButton[]) => void;
  maxButtons?: number;
}

const BUTTON_TYPES = [
  {
    id: 'reply' as const,
    name: 'Quick Reply',
    icon: MessageSquare,
    description: 'User can reply with predefined text',
    fields: ['title', 'payload']
  },
  {
    id: 'url' as const,
    name: 'URL',
    icon: ExternalLink,
    description: 'Opens a web link',
    fields: ['title', 'url']
  },
  {
    id: 'phone_number' as const,
    name: 'Phone Call',
    icon: Phone,
    description: 'Initiates a phone call',
    fields: ['title', 'phone_number']
  }
];

export const WhatsAppButtonEditor: React.FC<WhatsAppButtonEditorProps> = ({
  buttons,
  onChange,
  maxButtons = 3
}) => {
  const handleAddButton = () => {
    if (buttons.length >= maxButtons) return;

    const newButton: WhatsAppButton = {
      type: 'reply',
      title: '',
      payload: ''
    };

    onChange([...buttons, newButton]);
  };

  const handleRemoveButton = (index: number) => {
    onChange(buttons.filter((_, i) => i !== index));
  };

  const handleButtonChange = (index: number, field: keyof WhatsAppButton, value: string) => {
    const updatedButtons = buttons.map((button, i) => {
      if (i !== index) return button;

      const updated = { ...button, [field]: value };

      // Clear fields that don't apply to the new type
      if (field === 'type') {
        const buttonType = BUTTON_TYPES.find(t => t.id === value);
        if (buttonType) {
          // Keep only title and the relevant field for the new type
          const newButton: WhatsAppButton = {
            type: value as WhatsAppButton['type'],
            title: button.title
          };

          // Add the appropriate field based on type
          if (value === 'reply') {
            newButton.payload = '';
          } else if (value === 'url') {
            newButton.url = '';
          } else if (value === 'phone_number') {
            newButton.phone_number = '';
          }

          return newButton;
        }
      }

      return updated;
    });

    onChange(updatedButtons);
  };

  const getButtonTypeConfig = (type: WhatsAppButton['type']) => {
    return BUTTON_TYPES.find(t => t.id === type) || BUTTON_TYPES[0];
  };

  const validateButton = (button: WhatsAppButton): string | null => {
    if (!button.title || button.title.trim().length === 0) {
      return 'Button title is required';
    }

    if (button.title.length > 20) {
      return 'Button title must be 20 characters or less';
    }

    if (button.type === 'reply' && !button.payload) {
      return 'Payload is required for reply buttons';
    }

    if (button.type === 'url') {
      if (!button.url) {
        return 'URL is required';
      }
      try {
        new URL(button.url);
      } catch {
        return 'Invalid URL format';
      }
    }

    if (button.type === 'phone_number') {
      if (!button.phone_number) {
        return 'Phone number is required';
      }
      if (!/^\+?[1-9]\d{1,14}$/.test(button.phone_number.replace(/[\s-]/g, ''))) {
        return 'Invalid phone number format';
      }
    }

    return null;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium">Interactive Buttons</h3>
        <p className="text-sm text-gray-600">
          Add up to {maxButtons} interactive buttons to your message
        </p>
      </div>

      {/* Buttons List */}
      <div className="space-y-4">
        {buttons.map((button, index) => {
          const typeConfig = getButtonTypeConfig(button.type);
          const ButtonIcon = typeConfig.icon;
          const validationError = validateButton(button);

          return (
            <Card key={index}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ButtonIcon className="h-4 w-4" />
                    <CardTitle className="text-base">
                      Button {index + 1}
                    </CardTitle>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveButton(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                {validationError && (
                  <Alert variant="destructive" className="mt-2">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-xs">
                      {validationError}
                    </AlertDescription>
                  </Alert>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Button Type */}
                <div className="space-y-2">
                  <Label>Button Type</Label>
                  <Select
                    value={button.type}
                    onValueChange={(value) => handleButtonChange(index, 'type', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {BUTTON_TYPES.map((type) => {
                        const Icon = type.icon;
                        return (
                          <SelectItem key={type.id} value={type.id}>
                            <div className="flex items-center gap-2">
                              <Icon className="h-4 w-4" />
                              <div>
                                <div className="font-medium">{type.name}</div>
                                <div className="text-xs text-gray-500">{type.description}</div>
                              </div>
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>

                {/* Button Title */}
                <div className="space-y-2">
                  <Label>Button Text *</Label>
                  <Input
                    placeholder="e.g., Learn More, Call Us, Yes"
                    value={button.title}
                    onChange={(e) => handleButtonChange(index, 'title', e.target.value)}
                    maxLength={20}
                  />
                  <p className="text-xs text-gray-500">
                    {button.title.length}/20 characters
                  </p>
                </div>

                {/* Type-specific Fields */}
                {button.type === 'reply' && (
                  <div className="space-y-2">
                    <Label>Payload *</Label>
                    <Input
                      placeholder="e.g., REPLY_YES, SUBSCRIBE"
                      value={button.payload || ''}
                      onChange={(e) => handleButtonChange(index, 'payload', e.target.value)}
                      maxLength={256}
                    />
                    <p className="text-xs text-gray-500">
                      Data sent back when button is clicked (not visible to user)
                    </p>
                  </div>
                )}

                {button.type === 'url' && (
                  <div className="space-y-2">
                    <Label>URL *</Label>
                    <Input
                      placeholder="https://example.com"
                      value={button.url || ''}
                      onChange={(e) => handleButtonChange(index, 'url', e.target.value)}
                    />
                    <p className="text-xs text-gray-500">
                      The web page to open when button is clicked
                    </p>
                  </div>
                )}

                {button.type === 'phone_number' && (
                  <div className="space-y-2">
                    <Label>Phone Number *</Label>
                    <Input
                      placeholder="+1234567890"
                      value={button.phone_number || ''}
                      onChange={(e) => handleButtonChange(index, 'phone_number', e.target.value)}
                    />
                    <p className="text-xs text-gray-500">
                      Include country code (e.g., +1 for US, +233 for Ghana)
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Add Button */}
      {buttons.length < maxButtons && (
        <Button
          variant="outline"
          onClick={handleAddButton}
          className="w-full gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Button ({buttons.length}/{maxButtons})
        </Button>
      )}

      {buttons.length === 0 && (
        <Alert>
          <MessageSquare className="h-4 w-4" />
          <AlertDescription className="text-xs">
            Interactive buttons are optional. They allow recipients to quickly respond or take action
            directly from your message.
          </AlertDescription>
        </Alert>
      )}

      {/* Guidelines */}
      {buttons.length > 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-xs">
            <strong>Button Guidelines:</strong>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>Maximum {maxButtons} buttons per message</li>
              <li>Button text must be 20 characters or less</li>
              <li>URLs must be HTTPS and publicly accessible</li>
              <li>Phone numbers must include country code</li>
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* Preview */}
      {buttons.length > 0 && (
        <Card className="bg-gray-50">
          <CardHeader>
            <CardTitle className="text-sm">Button Preview</CardTitle>
            <CardDescription className="text-xs">
              How your buttons will appear to recipients
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {buttons.map((button, index) => {
                const typeConfig = getButtonTypeConfig(button.type);
                const ButtonIcon = typeConfig.icon;
                return (
                  <div
                    key={index}
                    className="flex items-center justify-center gap-2 py-2 px-4 bg-white border rounded-lg"
                  >
                    <ButtonIcon className="h-4 w-4 text-blue-600" />
                    <span className="text-sm font-medium">
                      {button.title || `Button ${index + 1}`}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
