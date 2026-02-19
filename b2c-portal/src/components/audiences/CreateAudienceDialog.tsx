import React, { useState, useRef } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';
import { 
  formatPhoneNumberWithCountryCode,
  isValidPhoneNumber,
  COUNTRY_CODES,
  DEFAULT_COUNTRY_CODE,
  type CountryCode
} from '@/lib/phone-utils';

import { 
  Upload,
  FileText,
  Users,
  AlertCircle,
  CheckCircle,
  X,
  Download,
  Database,
  UserPlus
} from 'lucide-react';

interface CreateAudienceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAudienceCreated: () => void;
}

interface CSVValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  preview: any[];
  totalRows: number;
  validRows: number;
}

const CreateAudienceDialog: React.FC<CreateAudienceDialogProps> = ({
  open,
  onOpenChange,
  onAudienceCreated
}) => {
  const { toast } = useToast();
  const { user, getTenantId, getAccessToken } = useMongoAuth();
  const { currentOrganization } = useOrganization();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [step, setStep] = useState(1);
  const [creationMethod, setCreationMethod] = useState<'csv' | 'manual' | 'api'>('csv');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    tags: ''
  });
  
  // CSV Upload state
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvValidation, setCsvValidation] = useState<CSVValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  // Manual creation state
  const [manualContacts, setManualContacts] = useState<Array<{phone: string, name?: string}>>([
    { phone: '', name: '' }
  ]);

  // Country code selection for phone number formatting
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>(DEFAULT_COUNTRY_CODE);

  // Using API_BASE_URL from api-config;

  const resetDialog = () => {
    setStep(1);
    setCreationMethod('csv');
    setFormData({ name: '', description: '', tags: '' });
    setCsvFile(null);
    setCsvValidation(null);
    setIsValidating(false);
    setUploadProgress(0);
    setIsUploading(false);
    setManualContacts([{ phone: '', name: '' }]);
    setSelectedCountryCode(DEFAULT_COUNTRY_CODE);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const lowerName = file.name.toLowerCase();
    const isCsv = lowerName.endsWith('.csv');
    const isExcel = lowerName.endsWith('.xlsx') || lowerName.endsWith('.xls');

    if (!isCsv && !isExcel) {
      toast({
        title: "Invalid file type",
        description: "Please select a CSV or Excel file (.csv, .xlsx, .xls).",
        variant: "destructive"
      });
      return;
    }

    setCsvFile(file);

    // For CSV files, run client-side validation and preview.
    // For Excel files, skip CSV parsing and let the backend handle normalization.
    if (isCsv) {
      validateCSV(file);
    } else {
      setCsvValidation({
        isValid: true,
        errors: [],
        warnings: [],
        preview: [],
        totalRows: 0,
        validRows: 0
      });
    }
  };

  const validateCSV = async (file: File) => {
    setIsValidating(true);
    
    try {
      const text = await file.text();
      const lines = text.split('\n').filter(line => line.trim());
      
      if (lines.length === 0) {
        setCsvValidation({
          isValid: false,
          errors: ['File is empty'],
          warnings: [],
          preview: [],
          totalRows: 0,
          validRows: 0
        });
        return;
      }

      const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
      const hasPhoneHeader = headers.some(h => 
        h.includes('phone') || h.includes('mobile') || h.includes('number') || h.includes('cell')
      );

      const errors: string[] = [];
      const warnings: string[] = [];
      const preview: any[] = [];
      let validRows = 0;

      if (!hasPhoneHeader) {
        errors.push('No phone number column found. Expected columns: phone, mobile, number, or cell');
      }

      // Validate first 10 rows for preview
      const dataLines = lines.slice(1, Math.min(11, lines.length));
      
      for (let i = 0; i < dataLines.length; i++) {
        const row = dataLines[i].split(',').map(cell => cell.trim());
        const rowData: any = {};
        
        headers.forEach((header, index) => {
          rowData[header] = row[index] || '';
        });

        // Find phone number field
        const phoneField = headers.find(h => 
          h.includes('phone') || h.includes('mobile') || h.includes('number') || h.includes('cell')
        );
        
        if (phoneField) {
          const phone = rowData[phoneField];
          if (phone) {
            // Format phone number with country code
            const formattedPhone = formatPhoneNumberWithCountryCode(phone, selectedCountryCode);
            rowData[phoneField] = formattedPhone;
            
            // Validate formatted phone number
            if (isValidPhoneNumber(formattedPhone)) {
              validRows++;
            } else {
              warnings.push(`Row ${i + 2}: Invalid phone format "${phone}" -> "${formattedPhone}"`);
            }
          }
        }

        preview.push(rowData);
      }

      if (lines.length > 1000) {
        warnings.push(`Large file detected (${lines.length - 1} rows). Processing may take longer.`);
      }

      setCsvValidation({
        isValid: errors.length === 0 && validRows > 0,
        errors,
        warnings,
        preview,
        totalRows: lines.length - 1,
        validRows: validRows
      });

    } catch (error) {
      setCsvValidation({
        isValid: false,
        errors: ['Failed to parse CSV file. Please check the file format.'],
        warnings: [],
        preview: [],
        totalRows: 0,
        validRows: 0
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleCreateAudience = async () => {
    if (!formData.name.trim()) {
      toast({
        title: "Name required",
        description: "Please enter a name for your audience.",
        variant: "destructive"
      });
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      let audienceData: any = {
        name: formData.name,
        description: formData.description,
        tags: formData.tags.split(',').map(tag => tag.trim()).filter(Boolean),
        source: creationMethod
      };

      if (creationMethod === 'csv' && csvFile) {
        const formDataToSend = new FormData();
        formDataToSend.append('file', csvFile);
        formDataToSend.append('name', formData.name);
        formDataToSend.append('description', formData.description);
        formDataToSend.append('tags', formData.tags);
        formDataToSend.append('country_code', selectedCountryCode);
        formDataToSend.append('tenant_id', user?.user_metadata?.tenant_id || user?.id || '');

        const token = getAccessToken();
        const headers: HeadersInit = {
          'Authorization': `Bearer ${token}`
        };

        // Add organization header if available
        const currentOrgId = localStorage.getItem('kasaai_current_organization_id');
        if (currentOrgId) {
          headers['X-Organization-ID'] = currentOrgId;
        }

        const response = await fetch(`${API_BASE_URL}/audiences/upload-csv`, {
          method: 'POST',
          headers,
          body: formDataToSend
        });

        if (!response.ok) {
          const errorData = await response.text();
          throw new Error(`HTTP error! status: ${response.status}, details: ${errorData}`);
        }

        setUploadProgress(100);
      } else if (creationMethod === 'manual') {
        // Format phone numbers with country code
        const formattedContacts = manualContacts
          .map(contact => ({
            ...contact,
            phone: formatPhoneNumberWithCountryCode(contact.phone.trim(), selectedCountryCode)
          }))
          .filter(contact => contact.phone && isValidPhoneNumber(contact.phone));

        if (formattedContacts.length === 0) {
          toast({
            title: "No valid contacts",
            description: "Please add at least one valid phone number.",
            variant: "destructive"
          });
          setIsUploading(false);
          return;
        }

        audienceData.contacts = formattedContacts;
        audienceData.size = formattedContacts.length;
        audienceData.tenant_id = user?.user_metadata?.tenant_id || user?.id || '';

        const response = await fetch(`${API_BASE_URL}/audiences/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(audienceData)
        });

        if (!response.ok) {
          const errorData = await response.text();
          throw new Error(`HTTP error! status: ${response.status}, details: ${errorData}`);
        }
      }

      toast({
        title: "Audience created successfully",
        description: `Your audience "${formData.name}" has been created.`
      });

      resetDialog();
      onOpenChange(false);
      onAudienceCreated();

    } catch (error) {
      console.error('Error creating audience:', error);
      toast({
        title: "Failed to create audience",
        description: "Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const addManualContact = () => {
    setManualContacts([...manualContacts, { phone: '', name: '' }]);
  };

  const removeManualContact = (index: number) => {
    setManualContacts(manualContacts.filter((_, i) => i !== index));
  };

  const updateManualContact = (index: number, field: 'phone' | 'name', value: string) => {
    const updated = [...manualContacts];
    if (field === 'phone') {
      // Format phone number as user types (but don't force format until blur/submit)
      updated[index][field] = value;
    } else {
      updated[index][field] = value;
    }
    setManualContacts(updated);
  };

  const formatManualContactPhone = (index: number) => {
    const updated = [...manualContacts];
    const phone = updated[index].phone.trim();
    if (phone) {
      updated[index].phone = formatPhoneNumberWithCountryCode(phone, selectedCountryCode);
      setManualContacts(updated);
    }
  };

  const downloadSampleCSV = () => {
    const csvContent = "phone,name,email\n+234 123 456 7890,John Doe,john@example.com\n+234 987 654 3210,Jane Smith,jane@example.com";
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_audience.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const renderStep1 = () => (
    <div className="space-y-6">
      <div className="text-center">
        <Users className="mx-auto h-12 w-12 text-indigo-600 mb-4" />
        <h3 className="text-lg font-semibold mb-2">How do you want to create your audience?</h3>
        <p className="text-gray-600">
          Choose the method that works best for your contacts.
        </p>
      </div>

      <RadioGroup value={creationMethod} onValueChange={(value: 'csv' | 'manual' | 'api') => setCreationMethod(value)}>
        <div className="space-y-3">
          <div className="flex items-center space-x-3 p-4 border rounded-lg">
            <RadioGroupItem value="csv" id="csv" />
            <Label htmlFor="csv" className="flex-1 cursor-pointer">
              <div className="flex items-center gap-3">
                <Upload className="h-5 w-5 text-indigo-600" />
                <div>
                  <div className="font-medium">Upload CSV File</div>
                  <div className="text-sm text-gray-600">
                    Import contacts from a CSV file (recommended for large lists)
                  </div>
                </div>
              </div>
            </Label>
          </div>

          <div className="flex items-center space-x-3 p-4 border rounded-lg">
            <RadioGroupItem value="manual" id="manual" />
            <Label htmlFor="manual" className="flex-1 cursor-pointer">
              <div className="flex items-center gap-3">
                <UserPlus className="h-5 w-5 text-indigo-600" />
                <div>
                  <div className="font-medium">Add Manually</div>
                  <div className="text-sm text-gray-600">
                    Enter contacts one by one (good for small lists)
                  </div>
                </div>
              </div>
            </Label>
          </div>

          <div className="flex items-center space-x-3 p-4 border rounded-lg opacity-50">
            <RadioGroupItem value="api" id="api" disabled />
            <Label htmlFor="api" className="flex-1 cursor-pointer">
              <div className="flex items-center gap-3">
                <Database className="h-5 w-5 text-gray-600" />
                <div>
                  <div className="font-medium text-gray-600">CRM Integration</div>
                  <div className="text-sm text-gray-600">
                    Connect with your CRM system (coming soon)
                  </div>
                </div>
              </div>
            </Label>
          </div>
        </div>
      </RadioGroup>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Audience Details</h3>
        <div className="space-y-4">
          <div>
            <Label htmlFor="name">Audience Name *</Label>
            <Input
              id="name"
              placeholder="e.g., Q1 Prospects"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>
          
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe this audience..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>
          
          <div>
            <Label htmlFor="tags">Tags (comma-separated)</Label>
            <Input
              id="tags"
              placeholder="e.g., prospects, q1, sales"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            />
          </div>
        </div>
      </div>

      {creationMethod === 'csv' && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium">Upload CSV/Excel File</h4>
            <div className="flex items-center gap-2">
              <Label htmlFor="country-code" className="text-sm text-gray-600">
                Country Code:
              </Label>
              <Select value={selectedCountryCode} onValueChange={setSelectedCountryCode}>
                <SelectTrigger id="country-code" className="w-[200px]">
                  <SelectValue placeholder="Select country" />
                </SelectTrigger>
                <SelectContent>
                  {COUNTRY_CODES.map((country) => (
                    <SelectItem key={country.code} value={country.dialCode}>
                      <div className="flex items-center gap-2">
                        <span>{country.flag}</span>
                        <span>{country.country}</span>
                        <span className="text-gray-500">({country.dialCode})</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-3">
            Phone numbers will be automatically formatted with the selected country code if missing.
          </p>
          
          <div className="border-2 border-dashed border-muted rounded-lg p-6">
            {!csvFile ? (
              <div className="text-center">
                <Upload className="mx-auto h-8 w-8 text-gray-600 mb-2" />
                <p className="text-sm text-gray-600 mb-2">
                  Click to upload or drag and drop your CSV file
                </p>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Choose File
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <div className="mt-4">
                  <Button
                    type="button"
                    variant="link"
                    size="sm"
                    onClick={downloadSampleCSV}
                    className="text-xs"
                  >
                    <Download className="h-3 w-3 mr-1" />
                    Download Sample CSV
                  </Button>
                </div>
              </div>
            ) : (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="h-5 w-5 text-indigo-600" />
                  <span className="font-medium">{csvFile.name}</span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setCsvFile(null);
                      setCsvValidation(null);
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {isValidating && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary" />
                    Validating CSV...
                  </div>
                )}

                {csvValidation && (
                  <div className="space-y-3">
                    {csvValidation.errors.length > 0 && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded">
                        <div className="flex items-center gap-2 text-red-800 mb-2">
                          <AlertCircle className="h-4 w-4" />
                          <span className="font-medium">Errors found:</span>
                        </div>
                        <ul className="text-sm text-red-700 space-y-1">
                          {csvValidation.errors.map((error, index) => (
                            <li key={index}>• {error}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {csvValidation.warnings.length > 0 && (
                      <div className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                        <div className="flex items-center gap-2 text-yellow-800 mb-2">
                          <AlertCircle className="h-4 w-4" />
                          <span className="font-medium">Warnings:</span>
                        </div>
                        <ul className="text-sm text-yellow-700 space-y-1">
                          {csvValidation.warnings.slice(0, 3).map((warning, index) => (
                            <li key={index}>• {warning}</li>
                          ))}
                          {csvValidation.warnings.length > 3 && (
                            <li>• And {csvValidation.warnings.length - 3} more...</li>
                          )}
                        </ul>
                      </div>
                    )}

                    <div className="p-3 bg-green-50 border border-green-200 rounded">
                      <div className="flex items-center gap-2 text-green-800 mb-2">
                        <CheckCircle className="h-4 w-4" />
                        <span className="font-medium">File summary:</span>
                      </div>
                      <div className="text-sm text-green-700">
                        <p>Total rows: {csvValidation.totalRows}</p>
                        <p>Valid contacts: {csvValidation.validRows}</p>
                      </div>
                    </div>

                    {csvValidation.preview.length > 0 && (
                      <div className="p-3 border rounded">
                        <h5 className="font-medium mb-2">Preview (first 5 rows):</h5>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b">
                                {Object.keys(csvValidation.preview[0]).map(header => (
                                  <th key={header} className="text-left p-1 font-medium">
                                    {header}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {csvValidation.preview.slice(0, 5).map((row, index) => (
                                <tr key={index} className="border-b">
                                  {Object.values(row).map((cell: any, cellIndex) => (
                                    <td key={cellIndex} className="p-1 truncate max-w-[100px]">
                                      {cell}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {creationMethod === 'manual' && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium">Add Contacts</h4>
            <div className="flex items-center gap-2">
              <Label htmlFor="country-code-manual" className="text-sm text-gray-600">
                Country Code:
              </Label>
              <Select value={selectedCountryCode} onValueChange={setSelectedCountryCode}>
                <SelectTrigger id="country-code-manual" className="w-[200px]">
                  <SelectValue placeholder="Select country" />
                </SelectTrigger>
                <SelectContent>
                  {COUNTRY_CODES.map((country) => (
                    <SelectItem key={country.code} value={country.dialCode}>
                      <div className="flex items-center gap-2">
                        <span>{country.flag}</span>
                        <span>{country.country}</span>
                        <span className="text-gray-500">({country.dialCode})</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-3">
            Enter phone numbers (with or without country code). They will be formatted as {selectedCountryCode}XXXXXXXXX.
          </p>
          <div className="space-y-3">
            {manualContacts.map((contact, index) => (
              <div key={index} className="flex gap-2">
                <Input
                  placeholder="Phone number * (e.g., 0500603563 or 233500603563)"
                  value={contact.phone}
                  onChange={(e) => updateManualContact(index, 'phone', e.target.value)}
                  onBlur={() => formatManualContactPhone(index)}
                  className="flex-1"
                />
                <Input
                  placeholder="Name (optional)"
                  value={contact.name}
                  onChange={(e) => updateManualContact(index, 'name', e.target.value)}
                  className="flex-1"
                />
                {manualContacts.length > 1 && (
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={() => removeManualContact(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              onClick={addManualContact}
              className="w-full"
            >
              <UserPlus className="h-4 w-4 mr-2" />
              Add Another Contact
            </Button>
          </div>
        </div>
      )}
    </div>
  );

  const canProceedToStep2 = () => {
    return creationMethod !== '';
  };

  const canCreateAudience = () => {
    if (!formData.name.trim()) return false;

    if (creationMethod === 'csv') {
      if (!csvFile) return false;

      const lowerName = csvFile.name.toLowerCase();
      const isCsv = lowerName.endsWith('.csv');
      const isExcel = lowerName.endsWith('.xlsx') || lowerName.endsWith('.xls');

      if (isCsv) {
        return !!(csvValidation && csvValidation.validRows > 0);
      }

      if (isExcel) {
        // Excel files are parsed and validated on the backend.
        return true;
      }

      return false;
    } else if (creationMethod === 'manual') {
      return manualContacts.some(contact => contact.phone.trim());
    }

    return false;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Audience</DialogTitle>
          <DialogDescription>
            Step {step} of 2 - {step === 1 ? 'Choose creation method' : 'Configure audience'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <Progress value={(step / 2) * 100} className="h-2" />

          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}

          {isUploading && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Creating audience...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="h-2" />
            </div>
          )}

          <div className="flex justify-between pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => step > 1 ? setStep(step - 1) : onOpenChange(false)}
            >
              {step === 1 ? 'Cancel' : 'Back'}
            </Button>
            
            {step === 1 ? (
              <Button
                onClick={() => setStep(2)}
                disabled={!canProceedToStep2()}
              >
                Next
              </Button>
            ) : (
              <Button
                onClick={handleCreateAudience}
                disabled={!canCreateAudience() || isUploading}
              >
                {isUploading ? 'Creating...' : 'Create Audience'}
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CreateAudienceDialog;