import React, { useState, useEffect, useRef } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { getAuthHeaders } from '@/lib/auth-utils';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';

import {
  Users,
  Edit,
  AlertCircle,
  Upload,
  UserPlus,
  X,
  Download,
  FileText,
  CheckCircle
} from 'lucide-react';

interface Audience {
  id: string;
  name: string;
  description?: string;
  size: number;
  status: 'active' | 'draft' | 'archived';
  created_at: string;
  updated_at: string;
  tenant_id: string;
  source: 'csv_upload' | 'manual' | 'api' | 'crm_sync';
  tags?: string[];
  metadata?: {
    last_used?: string;
    campaign_count?: number;
    conversion_rate?: number;
  };
}

interface EditAudienceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  audience: Audience | null;
  onAudienceUpdated: () => void;
}

const EditAudienceDialog: React.FC<EditAudienceDialogProps> = ({
  open,
  onOpenChange,
  audience,
  onAudienceUpdated
}) => {
  const { toast } = useToast();
  const { user, getTenantId } = useMongoAuth();

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    tags: '',
    status: 'active' as 'active' | 'draft' | 'archived'
  });
  const [isUpdating, setIsUpdating] = useState(false);
  const [activeTab, setActiveTab] = useState('details');

  // Contact management state
  const [contacts, setContacts] = useState<Array<{phone: string, name?: string, email?: string}>>([]);
  const [newContacts, setNewContacts] = useState<Array<{phone: string, name?: string}>>([{ phone: '', name: '' }]);
  const [isLoadingContacts, setIsLoadingContacts] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [isUploadingCSV, setIsUploadingCSV] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Using API_BASE_URL from api-config;

  useEffect(() => {
    if (audience) {
      setFormData({
        name: audience.name || '',
        description: audience.description || '',
        tags: audience.tags ? audience.tags.join(', ') : '',
        status: audience.status
      });
    }
  }, [audience]);

  // Load contacts when tab is switched to contacts
  useEffect(() => {
    if (activeTab === 'contacts' && audience && contacts.length === 0) {
      loadContacts();
    }
  }, [activeTab, audience]);

  const resetDialog = () => {
    setFormData({
      name: '',
      description: '',
      tags: '',
      status: 'active'
    });
    setActiveTab('details');
    setContacts([]);
    setNewContacts([{ phone: '', name: '' }]);
    setCsvFile(null);
    setUploadProgress(0);
  };

  // Load contacts via export endpoint (workaround since no dedicated contacts API)
  const loadContacts = async () => {
    if (!audience) return;

    setIsLoadingContacts(true);
    try {
      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/audiences/${audience.id}/export`, {
        headers: authHeaders
      });

      if (response.ok) {
        const csvText = await response.text();
        const lines = csvText.split('\n').filter(line => line.trim());
        const headers = lines[0].split(',').map(h => h.trim().toLowerCase());

        const phoneIndex = headers.findIndex(h => h.includes('phone') || h.includes('mobile') || h.includes('number'));
        const nameIndex = headers.findIndex(h => h.includes('name'));
        const emailIndex = headers.findIndex(h => h.includes('email'));

        const contactsData = lines.slice(1).map(line => {
          const values = line.split(',').map(v => v.trim().replace(/"/g, ''));
          return {
            phone: phoneIndex >= 0 ? values[phoneIndex] || '' : '',
            name: nameIndex >= 0 ? values[nameIndex] || '' : '',
            email: emailIndex >= 0 ? values[emailIndex] || '' : ''
          };
        }).filter(contact => contact.phone);

        setContacts(contactsData);
      }
    } catch (error) {
      console.error('Error loading contacts:', error);
      toast({
        title: "Failed to load contacts",
        description: "Could not retrieve contact list.",
        variant: "destructive"
      });
    } finally {
      setIsLoadingContacts(false);
    }
  };

  // Add new contact manually
  const addNewContact = () => {
    setNewContacts([...newContacts, { phone: '', name: '' }]);
  };

  const removeNewContact = (index: number) => {
    setNewContacts(newContacts.filter((_, i) => i !== index));
  };

  const updateNewContact = (index: number, field: 'phone' | 'name', value: string) => {
    const updated = [...newContacts];
    updated[index][field] = value;
    setNewContacts(updated);
  };

  // Handle CSV upload for contact replacement
  const handleCSVUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      toast({
        title: "Invalid file type",
        description: "Please select a CSV file.",
        variant: "destructive"
      });
      return;
    }

    setCsvFile(file);
  };

  // Upload CSV to replace all contacts
  const uploadCSVContacts = async () => {
    if (!csvFile || !audience) return;

    setIsUploadingCSV(true);
    setUploadProgress(0);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('file', csvFile);
      formDataToSend.append('name', audience.name);
      formDataToSend.append('description', audience.description || '');
      formDataToSend.append('tags', audience.tags?.join(',') || '');
      formDataToSend.append('tenant_id', user?.user_metadata?.tenant_id || user?.id || '');
      formDataToSend.append('replace_contacts', 'true');

      const authHeaders = await getAuthHeaders();
      const response = await fetch(`${API_BASE_URL}/audiences/${audience.id}/upload-csv`, {
        method: 'POST',
        headers: {
          // Don't set Content-Type for FormData, let browser set it with boundary
          'Authorization': authHeaders['Authorization'],
          'x-service-token': authHeaders['x-service-token']
        },
        body: formDataToSend
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setUploadProgress(100);
      toast({
        title: "Contacts updated successfully",
        description: "All contacts have been replaced with the CSV data."
      });

      setCsvFile(null);
      setContacts([]);
      onAudienceUpdated();

      // Reload contacts to show updated list
      setTimeout(() => {
        loadContacts();
      }, 1000);

    } catch (error) {
      console.error('Error uploading CSV:', error);
      toast({
        title: "Failed to upload CSV",
        description: "Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsUploadingCSV(false);
      setUploadProgress(0);
    }
  };

  // Generate CSV for download (since API doesn't support direct contact addition)
  const generateContactsCSV = () => {
    if (!audience) return;

    const validNewContacts = newContacts.filter(contact =>
      contact.phone.trim() && /^[\+]?[0-9\s\-\(\)]{7,15}$/.test(contact.phone.trim())
    );

    if (validNewContacts.length === 0) {
      toast({
        title: "No valid contacts",
        description: "Please add at least one valid phone number.",
        variant: "destructive"
      });
      return;
    }

    try {
      // Create CSV content with existing + new contacts
      const allContacts = [...contacts, ...validNewContacts];
      const csvHeader = 'phone,name,email';
      const csvRows = allContacts.map(contact =>
        `"${contact.phone}","${contact.name || ''}","${contact.email || ''}"`
      );
      const csvContent = [csvHeader, ...csvRows].join('\n');

      // Download the CSV file
      const csvBlob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(csvBlob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${audience.name}_updated_contacts.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "CSV downloaded",
        description: "Upload this CSV file using the 'Replace All Contacts' option below to add your new contacts."
      });

      setNewContacts([{ phone: '', name: '' }]);

    } catch (error) {
      console.error('Error generating CSV:', error);
      toast({
        title: "Failed to generate CSV",
        description: "Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleUpdateAudience = async () => {
    if (!audience) {
      toast({
        title: "No audience selected",
        description: "Please select an audience to edit.",
        variant: "destructive"
      });
      return;
    }

    if (!formData.name.trim()) {
      toast({
        title: "Name required",
        description: "Please enter a name for your audience.",
        variant: "destructive"
      });
      return;
    }

    setIsUpdating(true);

    try {
      // Note: The API doesn't support audience updates yet
      // This is a placeholder implementation
      toast({
        title: "Feature not available",
        description: "Audience metadata editing is not supported by the current API. Only contact management is available.",
        variant: "destructive"
      });

      // For now, just close the dialog since updates aren't supported
      resetDialog();
      onOpenChange(false);

    } catch (error) {
      console.error('Error updating audience:', error);
      toast({
        title: "Failed to update audience",
        description: "Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsUpdating(false);
    }
  };

  if (!audience) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit className="h-5 w-5" />
            Edit Audience
          </DialogTitle>
          <DialogDescription>
            Update the details and manage contacts for "{audience.name}"
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="contacts">Contacts ({audience.size})</TabsTrigger>
          </TabsList>

          <TabsContent value="details" className="space-y-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-name">Audience Name *</Label>
                <Input
                  id="edit-name"
                  placeholder="e.g., Q1 Prospects"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="edit-description">Description</Label>
                <Textarea
                  id="edit-description"
                  placeholder="Describe this audience..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div>
                <Label htmlFor="edit-tags">Tags (comma-separated)</Label>
                <Input
                  id="edit-tags"
                  placeholder="e.g., prospects, q1, sales"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="edit-status">Status</Label>
                <select
                  id="edit-status"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as 'active' | 'draft' | 'archived' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="active">Active</option>
                  <option value="draft">Draft</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Users className="h-5 w-5 text-blue-600 mt-0.5" />
                <div className="text-sm">
                  <div className="font-medium text-blue-900">Audience Information</div>
                  <div className="text-blue-700 mt-1">
                    <p>Total contacts: {audience.size.toLocaleString()}</p>
                    <p>Source: {audience.source.replace('_', ' ')}</p>
                    <p>Created: {new Date(audience.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div className="text-sm text-yellow-800">
                  <div className="font-medium">Limited API Support</div>
                  <div className="mt-1">
                    The current API doesn't support updating audience details.
                    You can only manage contacts using the options in the Contacts tab.
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-between pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isUpdating}
              >
                Cancel
              </Button>

              <Button
                variant="outline"
                onClick={() => setActiveTab('contacts')}
                disabled={isUpdating}
              >
                Manage Contacts Instead
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="contacts" className="space-y-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Contact Management</h3>
                <Button
                  variant="outline"
                  onClick={loadContacts}
                  disabled={isLoadingContacts}
                  className="gap-2"
                >
                  <Download className="h-4 w-4" />
                  {isLoadingContacts ? 'Loading...' : 'Refresh Contacts'}
                </Button>
              </div>

              {/* Current Contacts Display */}
              <div className="border rounded-lg p-4 max-h-60 overflow-y-auto">
                <h4 className="font-medium mb-3">Current Contacts ({contacts.length})</h4>
                {isLoadingContacts ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                    <span className="ml-2">Loading contacts...</span>
                  </div>
                ) : contacts.length > 0 ? (
                  <div className="space-y-2">
                    {contacts.slice(0, 10).map((contact, index) => (
                      <div key={index} className="flex items-center gap-3 p-2 bg-gray-50 rounded text-sm">
                        <span className="font-mono">{contact.phone}</span>
                        {contact.name && <span className="text-gray-600">{contact.name}</span>}
                        {contact.email && <span className="text-gray-500">{contact.email}</span>}
                      </div>
                    ))}
                    {contacts.length > 10 && (
                      <p className="text-sm text-gray-500 text-center py-2">
                        ... and {contacts.length - 10} more contacts
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-4">
                    No contacts loaded. Click "Refresh Contacts" to view.
                  </p>
                )}
              </div>

              {/* Add New Contacts */}
              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-3">Add New Contacts</h4>
                <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
                  <div className="text-sm text-blue-800">
                    <div className="font-medium">How it works:</div>
                    <div className="mt-1">
                      1. Add new contacts below<br/>
                      2. Click "Generate Combined CSV" to download a file with existing + new contacts<br/>
                      3. Upload that CSV file in the "Replace All Contacts" section
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  {newContacts.map((contact, index) => (
                    <div key={index} className="flex gap-2">
                      <Input
                        placeholder="Phone number *"
                        value={contact.phone}
                        onChange={(e) => updateNewContact(index, 'phone', e.target.value)}
                        className="flex-1"
                      />
                      <Input
                        placeholder="Name (optional)"
                        value={contact.name}
                        onChange={(e) => updateNewContact(index, 'name', e.target.value)}
                        className="flex-1"
                      />
                      {newContacts.length > 1 && (
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          onClick={() => removeNewContact(index)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={addNewContact}
                      className="flex-1 gap-2"
                    >
                      <UserPlus className="h-4 w-4" />
                      Add Another Contact
                    </Button>
                    <Button
                      onClick={generateContactsCSV}
                      disabled={!newContacts.some(c => c.phone.trim())}
                      className="gap-2"
                    >
                      <Download className="h-4 w-4" />
                      Generate Combined CSV
                    </Button>
                  </div>
                </div>
              </div>

              {/* CSV Upload for Contact Replacement */}
              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-3">Replace All Contacts with CSV</h4>
                <div className="space-y-3">
                  {!csvFile ? (
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                      <Upload className="mx-auto h-8 w-8 text-gray-400 mb-2" />
                      <p className="text-sm text-gray-500 mb-2">
                        Upload a CSV file to replace all contacts
                      </p>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Choose CSV File
                      </Button>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".csv"
                        onChange={handleCSVUpload}
                        className="hidden"
                      />
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 p-3 bg-blue-50 rounded">
                        <FileText className="h-5 w-5 text-blue-600" />
                        <span className="font-medium">{csvFile.name}</span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => setCsvFile(null)}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>

                      {isUploadingCSV && (
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span>Replacing contacts...</span>
                            <span>{uploadProgress}%</span>
                          </div>
                          <Progress value={uploadProgress} className="h-2" />
                        </div>
                      )}

                      <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
                          <div className="text-sm text-yellow-800">
                            <div className="font-medium">Warning</div>
                            <div>This will replace ALL existing contacts with the contacts from the CSV file.</div>
                          </div>
                        </div>
                      </div>

                      <Button
                        onClick={uploadCSVContacts}
                        disabled={isUploadingCSV}
                        className="w-full gap-2"
                      >
                        <Upload className="h-4 w-4" />
                        {isUploadingCSV ? 'Uploading...' : 'Replace All Contacts'}
                      </Button>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-between pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => onOpenChange(false)}
                  disabled={isUpdating || isUploadingCSV}
                >
                  Cancel
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setActiveTab('details')}
                  disabled={isUpdating || isUploadingCSV}
                >
                  Back to Details
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};

export default EditAudienceDialog;