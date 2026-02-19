/**
 * WhatsApp Template Selector Component
 *
 * Displays and allows selection of approved WhatsApp templates
 * with preview and placeholder mapping capabilities.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { RefreshCw, CheckCircle2, AlertCircle, FileText } from 'lucide-react';
import { WhatsAppTemplate } from '@/lib/whatsapp-campaigns-api';
import { useToast } from '@/hooks/use-toast';
import { getWhatsAppTemplates, syncWhatsAppTemplates } from '@/lib/whatsapp-campaigns-api';

interface WhatsAppTemplateSelectorProps {
  selectedTemplate: WhatsAppTemplate | null;
  onSelect: (template: WhatsAppTemplate) => void;
  variableValues?: Record<string, string>;
  onVariableChange?: (variables: Record<string, string>) => void;
}

export const WhatsAppTemplateSelector: React.FC<WhatsAppTemplateSelectorProps> = ({
  selectedTemplate,
  onSelect,
  variableValues = {},
  onVariableChange
}) => {
  const { toast } = useToast();
  const [templates, setTemplates] = useState<WhatsAppTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const response = await getWhatsAppTemplates();
      setTemplates(response.templates || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      toast({
        title: "Failed to load templates",
        description: "Please try again or sync templates from WhatsApp.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const response = await syncWhatsAppTemplates();
      toast({
        title: "Templates synced",
        description: `${response.count} templates synced from WhatsApp Business API.`
      });
      loadTemplates();
    } catch (error) {
      console.error('Error syncing templates:', error);
      toast({
        title: "Sync failed",
        description: "Failed to sync templates from WhatsApp.",
        variant: "destructive"
      });
    } finally {
      setSyncing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'bg-green-100 text-green-800';
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800';
      case 'REJECTED':
        return 'bg-red-100 text-red-800';
      case 'DISABLED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTemplatePreview = (template: WhatsAppTemplate): string => {
    let preview = '';

    // Extract body text from components
    const bodyComponent = template.components.find((c: any) => c.type === 'BODY');
    if (bodyComponent) {
      preview = bodyComponent.text || '';

      // Replace placeholders with variable values
      template.placeholders.forEach((placeholder, index) => {
        const varName = placeholder.replace(/[{}]/g, '');
        const value = variableValues[varName] || `{{${index + 1}}}`;
        preview = preview.replace(`{{${index + 1}}}`, value);
      });
    }

    return preview;
  };

  const filteredTemplates = templates.filter(template =>
    template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    template.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const approvedTemplates = filteredTemplates.filter(t => t.status === 'APPROVED');

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-gray-600">Loading templates...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Select WhatsApp Template</h3>
          <p className="text-sm text-gray-600">
            Choose an approved template for your campaign
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleSync}
          disabled={syncing}
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing...' : 'Sync Templates'}
        </Button>
      </div>

      {/* Search */}
      <div>
        <Input
          placeholder="Search templates by name or category..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* No templates alert */}
      {templates.length === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No templates found. Sync templates from WhatsApp Business API or create templates in Meta Business Suite.
          </AlertDescription>
        </Alert>
      )}

      {/* No approved templates alert */}
      {templates.length > 0 && approvedTemplates.length === 0 && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            No approved templates found. Please wait for WhatsApp to approve your templates or create new ones.
          </AlertDescription>
        </Alert>
      )}

      {/* Templates Grid */}
      <div className="grid grid-cols-1 gap-4 max-h-96 overflow-y-auto">
        {approvedTemplates.map((template) => (
          <Card
            key={template.id}
            className={`cursor-pointer transition-colors ${
              selectedTemplate?.id === template.id
                ? 'ring-2 ring-primary'
                : 'hover:bg-muted/50'
            }`}
            onClick={() => onSelect(template)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-base flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    {template.name}
                  </CardTitle>
                  <CardDescription className="mt-1">
                    {template.category} • {template.language}
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Badge className={getStatusColor(template.status)}>
                    {template.status === 'APPROVED' && <CheckCircle2 className="h-3 w-3 mr-1" />}
                    {template.status}
                  </Badge>
                  {selectedTemplate?.id === template.id && (
                    <Badge className="bg-primary text-primary-foreground">
                      Selected
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="bg-gray-50 rounded p-3 text-sm">
                <p className="whitespace-pre-wrap">
                  {getTemplatePreview(template)}
                </p>
              </div>
              {template.placeholders.length > 0 && (
                <div className="mt-3 text-xs text-gray-600">
                  <span className="font-medium">Variables:</span> {template.placeholders.join(', ')}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Variable Mapping Section */}
      {selectedTemplate && selectedTemplate.placeholders.length > 0 && onVariableChange && (
        <div className="mt-6 space-y-4">
          <div>
            <h4 className="text-sm font-medium mb-2">Template Variables</h4>
            <p className="text-xs text-gray-600 mb-4">
              Map placeholders to recipient data fields. Use column names from your audience data.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {selectedTemplate.placeholders.map((placeholder, index) => {
              const varName = placeholder.replace(/[{}]/g, '');
              return (
                <div key={placeholder} className="space-y-2">
                  <Label htmlFor={`var-${index}`}>
                    {placeholder}
                  </Label>
                  <Input
                    id={`var-${index}`}
                    placeholder={`e.g., name, phone, email`}
                    value={variableValues[varName] || ''}
                    onChange={(e) => {
                      onVariableChange({
                        ...variableValues,
                        [varName]: e.target.value
                      });
                    }}
                  />
                  <p className="text-xs text-gray-500">
                    Field name from your audience data
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Template Stats */}
      {templates.length > 0 && (
        <div className="pt-4 border-t">
          <div className="flex gap-4 text-sm text-gray-600">
            <span>Total: {templates.length}</span>
            <span className="text-green-600">
              Approved: {templates.filter(t => t.status === 'APPROVED').length}
            </span>
            <span className="text-yellow-600">
              Pending: {templates.filter(t => t.status === 'PENDING').length}
            </span>
            {templates.filter(t => t.status === 'REJECTED').length > 0 && (
              <span className="text-red-600">
                Rejected: {templates.filter(t => t.status === 'REJECTED').length}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
