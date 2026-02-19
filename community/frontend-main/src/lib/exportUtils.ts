import { saveAs } from 'file-saver';

export type ExportFormat = 'json' | 'csv' | 'xlsx' | 'xml' | 'pdf' | 'txt';

export interface ExportOptions {
  filename?: string;
  format: ExportFormat;
  includeHeaders?: boolean;
  dateFormat?: string;
  delimiter?: string; // For CSV
  encoding?: string;
  compression?: boolean;
}

export interface ExportData {
  data: any[];
  metadata?: {
    title?: string;
    description?: string;
    exportDate?: Date;
    totalRecords?: number;
    columns?: string[];
    source?: string;
  };
}

class DataExporter {
  private static instance: DataExporter;

  public static getInstance(): DataExporter {
    if (!DataExporter.instance) {
      DataExporter.instance = new DataExporter();
    }
    return DataExporter.instance;
  }

  public async exportData(exportData: ExportData, options: ExportOptions): Promise<void> {
    const { data, metadata } = exportData;
    const filename = this.generateFilename(options.filename, options.format, metadata?.title);

    try {
      let fileContent: string | Blob;
      let mimeType: string;

      switch (options.format) {
        case 'json':
          fileContent = this.exportToJSON(data, metadata);
          mimeType = 'application/json';
          break;
        case 'csv':
          fileContent = this.exportToCSV(data, options);
          mimeType = 'text/csv';
          break;
        case 'xlsx':
          fileContent = await this.exportToExcel(data, metadata, options);
          mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
          break;
        case 'xml':
          fileContent = this.exportToXML(data, metadata);
          mimeType = 'application/xml';
          break;
        case 'txt':
          fileContent = this.exportToText(data, options);
          mimeType = 'text/plain';
          break;
        case 'pdf':
          fileContent = await this.exportToPDF(data, metadata, options);
          mimeType = 'application/pdf';
          break;
        default:
          throw new Error(`Unsupported export format: ${options.format}`);
      }

      // Create blob and trigger download
      const blob = fileContent instanceof Blob
        ? fileContent
        : new Blob([fileContent], { type: mimeType });

      saveAs(blob, filename);
    } catch (error) {
      console.error('Export failed:', error);
      throw new Error(`Failed to export data as ${options.format.toUpperCase()}: ${error.message}`);
    }
  }

  private generateFilename(customFilename?: string, format: ExportFormat, title?: string): string {
    if (customFilename) {
      return customFilename.endsWith(`.${format}`) ? customFilename : `${customFilename}.${format}`;
    }

    const timestamp = new Date().toISOString().split('T')[0];
    const baseName = title ? this.sanitizeFilename(title) : 'export';
    return `${baseName}_${timestamp}.${format}`;
  }

  private sanitizeFilename(filename: string): string {
    return filename
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '_')
      .replace(/_{2,}/g, '_')
      .replace(/^_|_$/g, '');
  }

  private exportToJSON(data: any[], metadata?: any): string {
    const exportObject = {
      metadata: {
        exportDate: new Date().toISOString(),
        totalRecords: data.length,
        ...metadata,
      },
      data,
    };

    return JSON.stringify(exportObject, null, 2);
  }

  private exportToCSV(data: any[], options: ExportOptions): string {
    if (!data.length) return '';

    const delimiter = options.delimiter || ',';
    const includeHeaders = options.includeHeaders !== false;

    // Get all unique keys from the data
    const keys = [...new Set(data.flatMap(item => Object.keys(item)))];

    let csv = '';

    // Add headers if requested
    if (includeHeaders) {
      csv += keys.map(key => this.escapeCSVValue(key)).join(delimiter) + '\n';
    }

    // Add data rows
    data.forEach(item => {
      const row = keys.map(key => {
        const value = item[key];
        return this.escapeCSVValue(this.formatValueForCSV(value, options));
      });
      csv += row.join(delimiter) + '\n';
    });

    return csv;
  }

  private escapeCSVValue(value: string): string {
    if (value.includes(',') || value.includes('"') || value.includes('\n')) {
      return `"${value.replace(/"/g, '""')}"`;
    }
    return value;
  }

  private formatValueForCSV(value: any, options: ExportOptions): string {
    if (value === null || value === undefined) return '';
    if (value instanceof Date) {
      return options.dateFormat ? this.formatDate(value, options.dateFormat) : value.toISOString();
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  }

  private formatDate(date: Date, format: string): string {
    // Simple date formatting - in a real app you might use a library like date-fns
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return format
      .replace('YYYY', String(year))
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds);
  }

  private async exportToExcel(data: any[], metadata?: any, options?: ExportOptions): Promise<Blob> {
    // For a production app, you would use a library like xlsx or exceljs
    // For now, we'll create a simple Excel-compatible CSV
    const csvContent = this.exportToCSV(data, { ...options, format: 'csv' });
    const blob = new Blob([csvContent], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    return blob;
  }

  private exportToXML(data: any[], metadata?: any): string {
    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += '<export>\n';

    if (metadata) {
      xml += '  <metadata>\n';
      Object.entries(metadata).forEach(([key, value]) => {
        xml += `    <${key}>${this.escapeXML(String(value))}</${key}>\n`;
      });
      xml += '  </metadata>\n';
    }

    xml += '  <data>\n';
    data.forEach((item, index) => {
      xml += `    <record id="${index + 1}">\n`;
      Object.entries(item).forEach(([key, value]) => {
        xml += `      <${key}>${this.escapeXML(this.formatValueForXML(value))}</${key}>\n`;
      });
      xml += '    </record>\n';
    });
    xml += '  </data>\n';
    xml += '</export>';

    return xml;
  }

  private escapeXML(value: string): string {
    return value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  private formatValueForXML(value: any): string {
    if (value === null || value === undefined) return '';
    if (value instanceof Date) return value.toISOString();
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  }

  private exportToText(data: any[], options: ExportOptions): string {
    let text = '';

    data.forEach((item, index) => {
      text += `Record ${index + 1}:\n`;
      Object.entries(item).forEach(([key, value]) => {
        text += `  ${key}: ${this.formatValueForText(value)}\n`;
      });
      text += '\n';
    });

    return text;
  }

  private formatValueForText(value: any): string {
    if (value === null || value === undefined) return '(empty)';
    if (value instanceof Date) return value.toLocaleString();
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  }

  private async exportToPDF(data: any[], metadata?: any, options?: ExportOptions): Promise<Blob> {
    // For PDF export, you would typically use a library like jsPDF or Puppeteer
    // For this implementation, we'll create a simple HTML representation
    // and let the browser handle PDF generation

    let html = `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>${metadata?.title || 'Data Export'}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .metadata { margin-bottom: 20px; }
        </style>
    </head>
    <body>
    `;

    if (metadata) {
      html += '<div class="metadata">';
      html += `<h1>${metadata.title || 'Data Export'}</h1>`;
      if (metadata.description) html += `<p>${metadata.description}</p>`;
      html += `<p>Export Date: ${new Date().toLocaleString()}</p>`;
      html += `<p>Total Records: ${data.length}</p>`;
      html += '</div>';
    }

    if (data.length > 0) {
      const keys = Object.keys(data[0]);
      html += '<table>';
      html += '<thead><tr>';
      keys.forEach(key => {
        html += `<th>${key}</th>`;
      });
      html += '</tr></thead>';
      html += '<tbody>';

      data.forEach(item => {
        html += '<tr>';
        keys.forEach(key => {
          html += `<td>${this.escapeHTML(this.formatValueForText(item[key]))}</td>`;
        });
        html += '</tr>';
      });

      html += '</tbody></table>';
    }

    html += '</body></html>';

    const blob = new Blob([html], { type: 'text/html' });
    return blob;
  }

  private escapeHTML(value: string): string {
    const div = document.createElement('div');
    div.textContent = value;
    return div.innerHTML;
  }

  // Utility methods for specific data types
  public async exportUserData(userData: any[], options?: Partial<ExportOptions>): Promise<void> {
    const exportData: ExportData = {
      data: userData,
      metadata: {
        title: 'User Data Export',
        description: 'Exported user data from AfriLang Community Platform',
        exportDate: new Date(),
        totalRecords: userData.length,
        source: 'AfriLang Community Platform',
      },
    };

    await this.exportData(exportData, {
      format: 'json',
      includeHeaders: true,
      dateFormat: 'YYYY-MM-DD HH:mm:ss',
      ...options,
    });
  }

  public async exportContributions(contributions: any[], options?: Partial<ExportOptions>): Promise<void> {
    const exportData: ExportData = {
      data: contributions,
      metadata: {
        title: 'Contributions Export',
        description: 'Language contributions and validation data',
        exportDate: new Date(),
        totalRecords: contributions.length,
        source: 'AfriLang Community Platform',
      },
    };

    await this.exportData(exportData, {
      format: 'csv',
      includeHeaders: true,
      dateFormat: 'YYYY-MM-DD',
      ...options,
    });
  }

  public async exportLanguageData(languageData: any[], options?: Partial<ExportOptions>): Promise<void> {
    const exportData: ExportData = {
      data: languageData,
      metadata: {
        title: 'Language Data Export',
        description: 'African language datasets and resources',
        exportDate: new Date(),
        totalRecords: languageData.length,
        source: 'AfriLang Community Platform',
      },
    };

    await this.exportData(exportData, {
      format: 'json',
      includeHeaders: true,
      ...options,
    });
  }
}

// Create and export singleton instance
export const dataExporter = DataExporter.getInstance();

// Helper function to prepare data for export
export function prepareDataForExport(
  data: any[],
  options?: {
    excludeFields?: string[];
    includeFields?: string[];
    transformers?: Record<string, (value: any) => any>;
  }
): any[] {
  return data.map(item => {
    let processedItem = { ...item };

    // Apply field filtering
    if (options?.includeFields) {
      const filtered: any = {};
      options.includeFields.forEach(field => {
        if (field in processedItem) {
          filtered[field] = processedItem[field];
        }
      });
      processedItem = filtered;
    }

    if (options?.excludeFields) {
      options.excludeFields.forEach(field => {
        delete processedItem[field];
      });
    }

    // Apply transformers
    if (options?.transformers) {
      Object.entries(options.transformers).forEach(([field, transformer]) => {
        if (field in processedItem) {
          processedItem[field] = transformer(processedItem[field]);
        }
      });
    }

    return processedItem;
  });
}

export default DataExporter;