/**
 * ExportDialog Component
 * Dialog for exporting documents in various formats (JSON, CSV, PDF, Original)
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  FileJson,
  FileSpreadsheet,
  FileText,
  Download,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export type ExportFormat = 'json' | 'csv' | 'pdf' | 'original';

export type ExportScope = 'selected' | 'filtered' | 'all';

interface ExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  apiBaseUrl: string;
  companyName: string;
  selectedDocumentIds: string[];
  currentFilters?: {
    category?: string;
    tags?: string;
    status?: string;
    searchQuery?: string;
  };
  totalDocuments?: number;
  filteredDocuments?: number;
}

const ExportDialog: React.FC<ExportDialogProps> = ({
  open,
  onOpenChange,
  apiBaseUrl,
  companyName,
  selectedDocumentIds,
  currentFilters,
  totalDocuments = 0,
  filteredDocuments = 0,
}) => {
  const [format, setFormat] = useState<ExportFormat>('json');
  const [scope, setScope] = useState<ExportScope>('selected');
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [includeVersions, setIncludeVersions] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const { toast } = useToast();

  // Determine available scopes
  const hasSelectedDocs = selectedDocumentIds.length > 0;
  const hasFilters = !!(
    currentFilters?.category ||
    currentFilters?.tags ||
    currentFilters?.status ||
    currentFilters?.searchQuery
  );

  // Reset scope if selected option becomes invalid
  React.useEffect(() => {
    if (scope === 'selected' && !hasSelectedDocs) {
      setScope(hasFilters ? 'filtered' : 'all');
    }
  }, [scope, hasSelectedDocs, hasFilters]);

  // Get format icon
  const getFormatIcon = (fmt: ExportFormat) => {
    switch (fmt) {
      case 'json':
        return <FileJson className="h-4 w-4" />;
      case 'csv':
        return <FileSpreadsheet className="h-4 w-4" />;
      case 'pdf':
        return <FileText className="h-4 w-4" />;
      case 'original':
        return <Download className="h-4 w-4" />;
    }
  };

  // Get export description
  const getExportDescription = () => {
    const count =
      scope === 'selected'
        ? selectedDocumentIds.length
        : scope === 'filtered'
        ? filteredDocuments
        : totalDocuments;

    return `Export ${count} document${count !== 1 ? 's' : ''} as ${format.toUpperCase()}`;
  };

  // Handle export
  const handleExport = async () => {
    setIsExporting(true);

    try {
      let url: string;
      let params: URLSearchParams;

      // Single document export (PDF or Original)
      if (scope === 'selected' && selectedDocumentIds.length === 1 && (format === 'pdf' || format === 'original')) {
        const documentId = selectedDocumentIds[0];
        params = new URLSearchParams({
          format,
          include_metadata: includeMetadata.toString(),
        });

        url = `${apiBaseUrl}/knowledge-base/documents/${documentId}/export?${params}`;

        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Export failed: ${response.statusText}`);
        }

        // Download file
        const blob = await response.blob();
        const filename =
          response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') ||
          `document.${format}`;

        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
      }
      // Bulk export
      else {
        // Build params
        params = new URLSearchParams({
          company_name: companyName,
          format: format === 'pdf' || format === 'original' ? 'json' : format,
          include_metadata: includeMetadata.toString(),
          include_versions: includeVersions.toString(),
        });

        // Add document IDs for selected scope
        let requestBody: any = {};

        if (scope === 'selected' && selectedDocumentIds.length > 0) {
          requestBody.document_ids = selectedDocumentIds;
        }

        // Add filters for filtered/all scope
        if (scope === 'filtered' || scope === 'all') {
          if (currentFilters?.category) requestBody.category = currentFilters.category;
          if (currentFilters?.tags) requestBody.tags = currentFilters.tags;
          if (currentFilters?.status) requestBody.status = currentFilters.status;
          if (currentFilters?.searchQuery) requestBody.search_query = currentFilters.searchQuery;
        }

        url = `${apiBaseUrl}/knowledge-base/documents/export?${params}`;

        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(error.detail || `Export failed: ${response.statusText}`);
        }

        // Download file
        const blob = await response.blob();
        const filename =
          response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') ||
          `documents_export.${format}`;

        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
      }

      toast({
        title: 'Export Successful',
        description: getExportDescription(),
      });

      onOpenChange(false);
    } catch (error) {
      console.error('Export error:', error);
      toast({
        title: 'Export Failed',
        description: error instanceof Error ? error.message : 'Could not export documents',
        variant: 'destructive',
      });
    } finally {
      setIsExporting(false);
    }
  };

  // Validate format for scope
  const isPdfOriginalValid =
    (format === 'pdf' || format === 'original') &&
    scope === 'selected' &&
    selectedDocumentIds.length === 1;

  const canExport =
    (format === 'json' || format === 'csv' || isPdfOriginalValid) &&
    ((scope === 'selected' && selectedDocumentIds.length > 0) ||
      scope === 'filtered' ||
      scope === 'all');

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Export Documents</DialogTitle>
          <DialogDescription>Choose format and scope for exporting documents</DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Export Format */}
          <div className="space-y-3">
            <Label>Export Format</Label>
            <RadioGroup value={format} onValueChange={(v) => setFormat(v as ExportFormat)}>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="json" id="format-json" />
                <Label htmlFor="format-json" className="flex items-center gap-2 cursor-pointer">
                  {getFormatIcon('json')}
                  <div>
                    <div className="font-medium">JSON</div>
                    <div className="text-xs text-gray-600">
                      Full document data with metadata
                    </div>
                  </div>
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <RadioGroupItem value="csv" id="format-csv" />
                <Label htmlFor="format-csv" className="flex items-center gap-2 cursor-pointer">
                  {getFormatIcon('csv')}
                  <div>
                    <div className="font-medium">CSV</div>
                    <div className="text-xs text-gray-600">
                      Tabular format for spreadsheets
                    </div>
                  </div>
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <RadioGroupItem value="pdf" id="format-pdf" />
                <Label htmlFor="format-pdf" className="flex items-center gap-2 cursor-pointer">
                  {getFormatIcon('pdf')}
                  <div>
                    <div className="font-medium">PDF</div>
                    <div className="text-xs text-gray-600">
                      Formatted document (single document only)
                    </div>
                  </div>
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <RadioGroupItem value="original" id="format-original" />
                <Label htmlFor="format-original" className="flex items-center gap-2 cursor-pointer">
                  {getFormatIcon('original')}
                  <div>
                    <div className="font-medium">Original File</div>
                    <div className="text-xs text-gray-600">
                      Original uploaded file (single document only)
                    </div>
                  </div>
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Export Scope */}
          <div className="space-y-3">
            <Label>Export Scope</Label>
            <Select value={scope} onValueChange={(v) => setScope(v as ExportScope)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {hasSelectedDocs && (
                  <SelectItem value="selected">
                    Selected Documents ({selectedDocumentIds.length})
                  </SelectItem>
                )}
                {hasFilters && (
                  <SelectItem value="filtered">
                    Filtered Documents ({filteredDocuments})
                  </SelectItem>
                )}
                <SelectItem value="all">All Documents ({totalDocuments})</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Options */}
          <div className="space-y-3">
            <Label>Options</Label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="include-metadata"
                  checked={includeMetadata}
                  onCheckedChange={(checked) => setIncludeMetadata(checked as boolean)}
                />
                <Label
                  htmlFor="include-metadata"
                  className="text-sm font-normal cursor-pointer"
                >
                  Include metadata
                </Label>
              </div>

              {format === 'json' && (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="include-versions"
                    checked={includeVersions}
                    onCheckedChange={(checked) => setIncludeVersions(checked as boolean)}
                  />
                  <Label
                    htmlFor="include-versions"
                    className="text-sm font-normal cursor-pointer"
                  >
                    Include version history
                  </Label>
                </div>
              )}
            </div>
          </div>

          {/* Warnings */}
          {(format === 'pdf' || format === 'original') &&
            (scope !== 'selected' || selectedDocumentIds.length !== 1) && (
              <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-amber-900">
                  <p className="font-medium">PDF and Original formats are only available for single documents.</p>
                  <p className="mt-1">Please select exactly one document to export in this format.</p>
                </div>
              </div>
            )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isExporting}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={!canExport || isExporting}>
            {isExporting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Export
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default ExportDialog;
