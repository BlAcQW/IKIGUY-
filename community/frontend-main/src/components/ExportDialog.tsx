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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Download, FileText, Database, Settings, CheckCircle, Loader2 } from 'lucide-react';
import { dataExporter, ExportFormat, ExportOptions } from '@/lib/exportUtils';
import { useNotification } from '@/contexts/NotificationContext';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  data: any[];
  title?: string;
  description?: string;
  defaultFilename?: string;
  dataType?: 'user' | 'contributions' | 'language' | 'general';
}

export default function ExportDialog({
  isOpen,
  onClose,
  data,
  title = 'Export Data',
  description = 'Choose your export format and options',
  defaultFilename,
  dataType = 'general',
}: ExportDialogProps) {
  const { showSuccess, showError, showLoading, updateNotification } = useNotification();
  const [format, setFormat] = useState<ExportFormat>('json');
  const [filename, setFilename] = useState(defaultFilename || '');
  const [includeHeaders, setIncludeHeaders] = useState(true);
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [dateFormat, setDateFormat] = useState('YYYY-MM-DD HH:mm:ss');
  const [delimiter, setDelimiter] = useState(',');
  const [isExporting, setIsExporting] = useState(false);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [showPreview, setShowPreview] = useState(false);

  const formatOptions: { value: ExportFormat; label: string; description: string; icon: React.ReactNode }[] = [
    {
      value: 'json',
      label: 'JSON',
      description: 'JavaScript Object Notation - best for data interchange',
      icon: <FileText className="w-4 h-4" />,
    },
    {
      value: 'csv',
      label: 'CSV',
      description: 'Comma Separated Values - best for spreadsheets',
      icon: <Database className="w-4 h-4" />,
    },
    {
      value: 'xlsx',
      label: 'Excel',
      description: 'Microsoft Excel format',
      icon: <FileText className="w-4 h-4" />,
    },
    {
      value: 'xml',
      label: 'XML',
      description: 'Extensible Markup Language',
      icon: <FileText className="w-4 h-4" />,
    },
    {
      value: 'txt',
      label: 'Text',
      description: 'Plain text format',
      icon: <FileText className="w-4 h-4" />,
    },
  ];

  const handleExport = async () => {
    if (!data.length) {
      showError('No Data', 'There is no data to export');
      return;
    }

    setIsExporting(true);
    const loadingId = showLoading('Exporting Data', `Preparing ${format.toUpperCase()} export...`);

    try {
      const exportOptions: ExportOptions = {
        filename,
        format,
        includeHeaders,
        dateFormat,
        delimiter: format === 'csv' ? delimiter : undefined,
      };

      const exportData = {
        data,
        metadata: includeMetadata ? {
          title: title,
          description: description,
          exportDate: new Date(),
          totalRecords: data.length,
          source: 'AfriLang Community Platform',
        } : undefined,
      };

      // Use specific export method based on data type
      switch (dataType) {
        case 'user':
          await dataExporter.exportUserData(data, exportOptions);
          break;
        case 'contributions':
          await dataExporter.exportContributions(data, exportOptions);
          break;
        case 'language':
          await dataExporter.exportLanguageData(data, exportOptions);
          break;
        default:
          await dataExporter.exportData(exportData, exportOptions);
      }

      updateNotification(loadingId, {
        type: 'success',
        title: 'Export Complete',
        message: `Successfully exported ${data.length} records as ${format.toUpperCase()}`,
        persistent: false,
        duration: 4000,
      });

      onClose();
    } catch (error) {
      console.error('Export failed:', error);
      updateNotification(loadingId, {
        type: 'error',
        title: 'Export Failed',
        message: error.message || 'An error occurred during export',
        persistent: false,
        duration: 6000,
      });
    } finally {
      setIsExporting(false);
    }
  };

  const generatePreview = () => {
    if (data.length === 0) return;

    // Show first 5 records for preview
    const preview = data.slice(0, 5);
    setPreviewData(preview);
    setShowPreview(true);
  };

  const estimateFileSize = (): string => {
    if (!data.length) return '0 B';

    const sampleSize = JSON.stringify(data.slice(0, Math.min(10, data.length))).length;
    const estimatedTotal = (sampleSize / Math.min(10, data.length)) * data.length;

    if (estimatedTotal < 1024) return `${Math.round(estimatedTotal)} B`;
    if (estimatedTotal < 1024 * 1024) return `${Math.round(estimatedTotal / 1024)} KB`;
    return `${Math.round(estimatedTotal / (1024 * 1024))} MB`;
  };

  const getRecordCount = (): number => data.length;

  const renderFormatSpecificOptions = () => {
    switch (format) {
      case 'csv':
        return (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="delimiter">Delimiter</Label>
              <Select value={delimiter} onValueChange={setDelimiter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value=",">,  (Comma)</SelectItem>
                  <SelectItem value=";">; (Semicolon)</SelectItem>
                  <SelectItem value="\t">⇥ (Tab)</SelectItem>
                  <SelectItem value="|">| (Pipe)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="includeHeaders"
                checked={includeHeaders}
                onCheckedChange={setIncludeHeaders}
              />
              <Label htmlFor="includeHeaders">Include column headers</Label>
            </div>
          </div>
        );
      case 'json':
      case 'xml':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              id="includeMetadata"
              checked={includeMetadata}
              onCheckedChange={setIncludeMetadata}
            />
            <Label htmlFor="includeMetadata">Include export metadata</Label>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="w-5 h-5" />
            {title}
          </DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Export Summary */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Export Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Total Records:</span>
                <Badge variant="secondary">{getRecordCount().toLocaleString()}</Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span>Estimated Size:</span>
                <span className="font-mono">{estimateFileSize()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Data Type:</span>
                <span className="capitalize">{dataType}</span>
              </div>
            </CardContent>
          </Card>

          {/* Format Selection */}
          <div className="space-y-3">
            <Label className="text-base font-medium">Export Format</Label>
            <div className="grid grid-cols-1 gap-2">
              {formatOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setFormat(option.value)}
                  className={`flex items-center gap-3 p-3 text-left border rounded-lg transition-colors ${
                    format === option.value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/50'
                  }`}
                >
                  {option.icon}
                  <div className="flex-1">
                    <div className="font-medium">{option.label}</div>
                    <div className="text-sm text-muted-foreground">{option.description}</div>
                  </div>
                  {format === option.value && (
                    <CheckCircle className="w-5 h-5 text-primary" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* File Options */}
          <div className="space-y-4">
            <Label className="text-base font-medium">File Options</Label>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="filename">Filename (optional)</Label>
                <Input
                  id="filename"
                  value={filename}
                  onChange={(e) => setFilename(e.target.value)}
                  placeholder={`export_${new Date().toISOString().split('T')[0]}.${format}`}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="dateFormat">Date Format</Label>
                <Select value={dateFormat} onValueChange={setDateFormat}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="YYYY-MM-DD HH:mm:ss">2024-03-15 14:30:00</SelectItem>
                    <SelectItem value="YYYY-MM-DD">2024-03-15</SelectItem>
                    <SelectItem value="MM/DD/YYYY">03/15/2024</SelectItem>
                    <SelectItem value="DD/MM/YYYY">15/03/2024</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Format-specific Options */}
          {renderFormatSpecificOptions() && (
            <>
              <Separator />
              <div className="space-y-4">
                <Label className="text-base font-medium flex items-center gap-2">
                  <Settings className="w-4 h-4" />
                  Format Options
                </Label>
                {renderFormatSpecificOptions()}
              </div>
            </>
          )}

          {/* Preview */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-base font-medium">Data Preview</Label>
              <Button
                variant="outline"
                size="sm"
                onClick={generatePreview}
                disabled={!data.length}
              >
                Generate Preview
              </Button>
            </div>

            {showPreview && previewData.length > 0 && (
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm font-mono bg-muted p-3 rounded overflow-x-auto max-h-40">
                    <pre>
                      {format === 'json'
                        ? JSON.stringify(previewData, null, 2)
                        : `First ${previewData.length} records will be exported...`}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} disabled={isExporting}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={isExporting || !data.length}>
            {isExporting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Export {format.toUpperCase()}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}