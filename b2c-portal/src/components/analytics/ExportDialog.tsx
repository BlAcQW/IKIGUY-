import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Download, FileText, FileSpreadsheet, Loader2, Info } from 'lucide-react';
import { API_BASE_URL } from '@/config/api-config';
import { cn } from '@/lib/utils';

interface ExportDialogProps {
  startDate?: Date | null;
  endDate?: Date | null;
  providers?: string[];
  trigger?: React.ReactNode;
}

interface ExportPreview {
  total_records: number;
  date_range: {
    start: string;
    end: string;
  } | null;
  summary: {
    total_revenue: number;
    total_costs: number;
    total_profit: number;
    estimated_size_kb: number;
  };
}

export default function ExportDialog({
  startDate,
  endDate,
  providers: initialProviders = [],
  trigger,
}: ExportDialogProps) {
  const [open, setOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<'csv' | 'pdf'>('csv');
  const [selectedProviders, setSelectedProviders] = useState<string[]>(initialProviders);
  const [includeSummary, setIncludeSummary] = useState(true);
  const [includeDetails, setIncludeDetails] = useState(true);
  const [preview, setPreview] = useState<ExportPreview | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Available providers
  const availableProviders = ['vapi', 'twilio', 'n8n', 'openai', 'anthropic', 'elevenlabs'];

  // Load preview when dialog opens or filters change
  useEffect(() => {
    if (open) {
      loadPreview();
    }
  }, [open, startDate, endDate, selectedProviders]);

  const loadPreview = async () => {
    setIsLoadingPreview(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (startDate) {
        params.append('start_date', startDate.toISOString());
      }
      if (endDate) {
        params.append('end_date', endDate.toISOString());
      }
      if (selectedProviders.length > 0) {
        params.append('providers', selectedProviders.join(','));
      }

      const response = await fetch(
        `${API_BASE_URL}/api/export/preview?${params.toString()}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to load preview');
      }

      const data = await response.json();
      setPreview(data.preview);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (startDate) {
        params.append('start_date', startDate.toISOString());
      }
      if (endDate) {
        params.append('end_date', endDate.toISOString());
      }
      if (selectedProviders.length > 0) {
        params.append('providers', selectedProviders.join(','));
      }

      if (exportFormat === 'csv') {
        params.append('include_summary', includeSummary.toString());
      } else {
        params.append('include_details', includeDetails.toString());
      }

      const endpoint = exportFormat === 'csv' ? 'csv' : 'pdf';
      const response = await fetch(
        `${API_BASE_URL}/api/export/${endpoint}?${params.toString()}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Failed to export data');
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `analytics_export.${exportFormat}`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Download file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsExporting(false);
    }
  };

  const toggleProvider = (provider: string) => {
    setSelectedProviders(prev =>
      prev.includes(provider)
        ? prev.filter(p => p !== provider)
        : [...prev, provider]
    );
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-GH', {
      style: 'currency',
      currency: 'GHS',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Export Analytics Data</DialogTitle>
          <DialogDescription>
            Download profit margin analytics in CSV or PDF format
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Export Format Selection */}
          <div>
            <Label className="text-base">Export Format</Label>
            <div className="grid grid-cols-2 gap-4 mt-2">
              <button
                onClick={() => setExportFormat('csv')}
                className={cn(
                  "flex items-center gap-3 p-4 border-2 rounded-lg transition-all",
                  exportFormat === 'csv'
                    ? "border-indigo-600 bg-indigo-50"
                    : "border-gray-200 hover:border-gray-300"
                )}
              >
                <FileSpreadsheet className={cn(
                  "h-8 w-8",
                  exportFormat === 'csv' ? "text-indigo-600" : "text-gray-400"
                )} />
                <div className="text-left">
                  <div className="font-semibold">CSV File</div>
                  <div className="text-xs text-gray-600">Excel compatible</div>
                </div>
              </button>

              <button
                onClick={() => setExportFormat('pdf')}
                className={cn(
                  "flex items-center gap-3 p-4 border-2 rounded-lg transition-all",
                  exportFormat === 'pdf'
                    ? "border-indigo-600 bg-indigo-50"
                    : "border-gray-200 hover:border-gray-300"
                )}
              >
                <FileText className={cn(
                  "h-8 w-8",
                  exportFormat === 'pdf' ? "text-indigo-600" : "text-gray-400"
                )} />
                <div className="text-left">
                  <div className="font-semibold">PDF Report</div>
                  <div className="text-xs text-gray-600">Professional format</div>
                </div>
              </button>
            </div>
          </div>

          {/* Provider Filter */}
          <div>
            <Label className="text-base">Include Providers</Label>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {availableProviders.map((provider) => (
                <div key={provider} className="flex items-center space-x-2">
                  <Checkbox
                    id={provider}
                    checked={selectedProviders.includes(provider)}
                    onCheckedChange={() => toggleProvider(provider)}
                  />
                  <label
                    htmlFor={provider}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 capitalize cursor-pointer"
                  >
                    {provider}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Export Options */}
          <div>
            <Label className="text-base">Options</Label>
            <div className="space-y-2 mt-2">
              {exportFormat === 'csv' && (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="summary"
                    checked={includeSummary}
                    onCheckedChange={(checked) => setIncludeSummary(checked as boolean)}
                  />
                  <label
                    htmlFor="summary"
                    className="text-sm font-medium leading-none cursor-pointer"
                  >
                    Include summary statistics
                  </label>
                </div>
              )}

              {exportFormat === 'pdf' && (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="details"
                    checked={includeDetails}
                    onCheckedChange={(checked) => setIncludeDetails(checked as boolean)}
                  />
                  <label
                    htmlFor="details"
                    className="text-sm font-medium leading-none cursor-pointer"
                  >
                    Include detailed transactions
                  </label>
                </div>
              )}
            </div>
          </div>

          {/* Preview Section */}
          {isLoadingPreview ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
            </div>
          ) : preview ? (
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                <Info className="h-4 w-4" />
                Export Preview
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-gray-600">Records</div>
                  <div className="font-semibold">{preview.total_records.toLocaleString()}</div>
                </div>

                <div>
                  <div className="text-gray-600">Est. Size</div>
                  <div className="font-semibold">{preview.summary.estimated_size_kb.toFixed(1)} KB</div>
                </div>

                {preview.date_range && (
                  <>
                    <div>
                      <div className="text-gray-600">Start Date</div>
                      <div className="font-semibold">{formatDate(preview.date_range.start)}</div>
                    </div>

                    <div>
                      <div className="text-gray-600">End Date</div>
                      <div className="font-semibold">{formatDate(preview.date_range.end)}</div>
                    </div>
                  </>
                )}

                <div>
                  <div className="text-gray-600">Total Revenue</div>
                  <div className="font-semibold text-green-600">
                    {formatCurrency(preview.summary.total_revenue)}
                  </div>
                </div>

                <div>
                  <div className="text-gray-600">Total Profit</div>
                  <div className={cn(
                    "font-semibold",
                    preview.summary.total_profit >= 0
                      ? "text-green-600"
                      : "text-red-600"
                  )}>
                    {formatCurrency(preview.summary.total_profit)}
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
              {error}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleExport}
              disabled={isExporting || !preview || preview.total_records === 0}
            >
              {isExporting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Export {exportFormat.toUpperCase()}
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
