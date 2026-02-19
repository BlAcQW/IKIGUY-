/**
 * Contact Import Dialog
 *
 * Allows bulk import of contacts from CSV files.
 * Provides file upload, validation, and import progress tracking.
 */

import { useState, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Upload, FileText, CheckCircle, AlertCircle, Download, X } from 'lucide-react';
import { useImportContacts } from '@/hooks/use-campaigns';

interface ContactImportDialogProps {
  open: boolean;
  onClose: () => void;
}

export function ContactImportDialog({ open, onClose }: ContactImportDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const importMutation = useImportContacts();

  const handleFileSelect = (file: File) => {
    // Validate file type
    if (!file.name.endsWith('.csv')) {
      alert('Please select a CSV file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB');
      return;
    }

    setSelectedFile(file);
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleImport = () => {
    if (!selectedFile) return;

    importMutation.mutate(selectedFile, {
      onSuccess: () => {
        setSelectedFile(null);
        onClose();
      },
    });
  };

  const handleClose = () => {
    setSelectedFile(null);
    importMutation.reset();
    onClose();
  };

  const downloadTemplate = () => {
    const csvContent = `name,email,phone,property_type_preferences,location_preferences,budget_min,budget_max,bedrooms_min,bedrooms_max,interest_status,lead_status,tags,source,notes
John Doe,john@example.com,+233244123456,"apartment,villa","Accra,Kumasi",100000,500000,2,4,warm,new,first-time-buyer,website,Looking for family home
Sarah Smith,sarah@example.com,+233244234567,penthouse,"Airport Residential",500000,2000000,3,5,hot,qualified,"investor,high-value",referral,Investment property`;

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'contact_import_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Import Contacts</DialogTitle>
          <DialogDescription>
            Upload a CSV file to import multiple contacts at once
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Template Download */}
          <Alert>
            <Download className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
              <span>Download our CSV template to get started</span>
              <Button
                variant="outline"
                size="sm"
                onClick={downloadTemplate}
                className="gap-2"
              >
                <Download className="h-4 w-4" />
                Download Template
              </Button>
            </AlertDescription>
          </Alert>

          {/* File Upload Area */}
          <div
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
              ${selectedFile ? 'bg-green-50 border-green-500' : ''}
            `}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {selectedFile ? (
              <div className="space-y-4">
                <div className="flex items-center justify-center">
                  <CheckCircle className="h-12 w-12 text-green-500" />
                </div>
                <div>
                  <div className="flex items-center justify-center gap-2">
                    <FileText className="h-5 w-5 text-gray-500" />
                    <span className="font-medium">{selectedFile.name}</span>
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedFile(null)}
                  className="gap-2"
                >
                  <X className="h-4 w-4" />
                  Remove
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-center">
                  <Upload className="h-12 w-12 text-gray-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700">
                    Drag and drop your CSV file here
                  </p>
                  <p className="text-xs text-gray-500 mt-1">or</p>
                </div>
                <label htmlFor="file-upload">
                  <Button variant="outline" asChild>
                    <span className="cursor-pointer">Browse Files</span>
                  </Button>
                  <input
                    id="file-upload"
                    type="file"
                    accept=".csv"
                    onChange={handleFileInput}
                    className="hidden"
                  />
                </label>
                <p className="text-xs text-gray-500 mt-2">
                  Maximum file size: 5MB
                </p>
              </div>
            )}
          </div>

          {/* CSV Format Instructions */}
          <div className="bg-gray-50 rounded-lg p-4 text-sm">
            <h4 className="font-medium mb-2">CSV Format Requirements:</h4>
            <ul className="space-y-1 text-gray-600">
              <li>• <strong>Required fields:</strong> name, email or phone</li>
              <li>• <strong>Optional fields:</strong> property_type_preferences, location_preferences, budget_min, budget_max, bedrooms_min, bedrooms_max, interest_status, lead_status, tags, source, notes</li>
              <li>• <strong>Multiple values:</strong> Separate with commas (e.g., "apartment,villa")</li>
              <li>• <strong>Interest status:</strong> hot, warm, cold, or unqualified</li>
              <li>• <strong>Lead status:</strong> new, contacted, qualified, negotiating, converted, or lost</li>
            </ul>
          </div>

          {/* Error Display */}
          {importMutation.isError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {importMutation.error?.message || 'Failed to import contacts'}
              </AlertDescription>
            </Alert>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              onClick={handleImport}
              disabled={!selectedFile || importMutation.isPending}
            >
              {importMutation.isPending ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Importing...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Import Contacts
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
