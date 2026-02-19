import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  QrCode,
  Download,
  Plus,
  Trash2,
  Edit,
  Copy,
  Search,
  X
} from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { api } from '@/lib/api-client';

interface QRCode {
  id: string;
  name: string;
  url: string;
  fill_color: string;
  back_color: string;
  has_logo: boolean;
  logo_filename: string | null;
  file_size: number;
  image_format: string;
  size: number;
  data_url: string;
  created_at: string;
  updated_at: string;
  download_count: number;
  tags: string[];
  category: string | null;
  notes: string | null;
}

interface QRCodeListResponse {
  qr_codes: QRCode[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export function QRCodePanel() {
  const [qrCodes, setQrCodes] = useState<QRCode[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedQR, setSelectedQR] = useState<QRCode | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const { toast } = useToast();

  // Form state for creating QR code
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    fill_color: '#1A1D2E',
    back_color: '#FFFFFF',
    size: 500,
    tags: '',
    category: '',
    notes: ''
  });
  const [logoFile, setLogoFile] = useState<File | null>(null);

  // Statistics
  const [stats, setStats] = useState({
    total_qr_codes: 0,
    total_downloads: 0,
    total_file_size_mb: 0
  });

  useEffect(() => {
    loadQRCodes();
    loadStatistics();
  }, []);

  const loadQRCodes = async () => {
    setLoading(true);
    try {
      const response = await api.get<{ data: QRCodeListResponse }>('/api/qr-codes/');
      setQrCodes(response.data.qr_codes);
    } catch (error: any) {
      toast({
        title: "Error loading QR codes",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await api.get<{ data: any }>('/api/qr-codes/statistics/user');
      setStats(response.data);
    } catch (error: any) {
      console.error('Error loading statistics:', error);
    }
  };

  const createQRCode = async () => {
    if (!formData.name || !formData.url) {
      toast({
        title: "Validation Error",
        description: "Name and URL are required",
        variant: "destructive"
      });
      return;
    }

    setCreating(true);
    try {
      const formDataObj = new FormData();
      formDataObj.append('name', formData.name);
      formDataObj.append('url', formData.url);
      formDataObj.append('fill_color', formData.fill_color);
      formDataObj.append('back_color', formData.back_color);
      formDataObj.append('size', formData.size.toString());
      if (formData.tags) formDataObj.append('tags', formData.tags);
      if (formData.category) formDataObj.append('category', formData.category);
      if (formData.notes) formDataObj.append('notes', formData.notes);
      if (logoFile) formDataObj.append('logo', logoFile);

      await api.post('/api/qr-codes/', formDataObj);

      toast({
        title: "Success",
        description: "QR code created successfully"
      });

      setShowCreateDialog(false);
      resetForm();
      loadQRCodes();
      loadStatistics();
    } catch (error: any) {
      toast({
        title: "Error creating QR code",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setCreating(false);
    }
  };

  const downloadQRCode = async (qr: QRCode) => {
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/qr-codes/${qr.id}/download`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('mongo_access_token')}`
        }
      });

      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${qr.name.replace(/\s+/g, '_')}.${qr.image_format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      toast({
        title: "Downloaded",
        description: `${qr.name} downloaded successfully`
      });

      loadQRCodes(); // Refresh to update download count
    } catch (error: any) {
      toast({
        title: "Download failed",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const deleteQRCode = async (id: string) => {
    if (!confirm('Are you sure you want to delete this QR code?')) return;

    try {
      await api.delete(`/api/qr-codes/${id}`);

      toast({
        title: "Deleted",
        description: "QR code deleted successfully"
      });

      loadQRCodes();
      loadStatistics();
    } catch (error: any) {
      toast({
        title: "Error deleting QR code",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const updateQRCode = async () => {
    if (!selectedQR) return;

    try {
      await api.put(`/api/qr-codes/${selectedQR.id}`, {
        name: selectedQR.name,
        tags: selectedQR.tags,
        category: selectedQR.category,
        notes: selectedQR.notes
      });

      toast({
        title: "Updated",
        description: "QR code updated successfully"
      });

      setShowEditDialog(false);
      setSelectedQR(null);
      loadQRCodes();
    } catch (error: any) {
      toast({
        title: "Error updating QR code",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      url: '',
      fill_color: '#1A1D2E',
      back_color: '#FFFFFF',
      size: 500,
      tags: '',
      category: '',
      notes: ''
    });
    setLogoFile(null);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied",
      description: "URL copied to clipboard"
    });
  };

  const filteredQRCodes = qrCodes.filter(qr =>
    qr.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    qr.url.toLowerCase().includes(searchTerm.toLowerCase()) ||
    qr.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <QrCode className="w-8 h-8 text-primary" />
          <h2 className="text-2xl font-bold text-foreground">QR Code Generator</h2>
        </div>
        <p className="text-muted-foreground">
          Create branded QR codes with custom colors and logos for marketing materials, products, and events
        </p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total QR Codes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_qr_codes}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Downloads
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_downloads}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Storage Used
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.total_file_size_mb.toFixed(2)} MB
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Actions Bar */}
      <div className="flex items-center justify-between">
        <div className="flex-1 max-w-sm">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search QR codes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        <Button onClick={() => setShowCreateDialog(true)} className="ml-4">
          <Plus className="w-4 h-4 mr-2" />
          Create QR Code
        </Button>
      </div>

      {/* QR Codes Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <p className="mt-4 text-muted-foreground">Loading QR codes...</p>
        </div>
      ) : filteredQRCodes.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-muted-foreground">
              <QrCode className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No QR codes found</p>
              <p className="mt-2">
                {searchTerm ? 'Try a different search term' : 'Create your first QR code to get started'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredQRCodes.map((qr) => (
            <Card key={qr.id} className="overflow-hidden hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base font-semibold truncate">
                    {qr.name}
                  </CardTitle>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setSelectedQR(qr);
                        setShowPreviewDialog(true);
                      }}
                    >
                      <QrCode className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setSelectedQR(qr);
                        setShowEditDialog(true);
                      }}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => deleteQRCode(qr.id)}
                    >
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* QR Code Preview */}
                <div className="aspect-square bg-white rounded-lg p-4 flex items-center justify-center">
                  <img
                    src={qr.data_url}
                    alt={qr.name}
                    className="w-full h-full object-contain"
                  />
                </div>

                {/* URL */}
                <div className="flex items-center gap-2">
                  <p className="text-xs text-muted-foreground truncate flex-1">
                    {qr.url}
                  </p>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => copyToClipboard(qr.url)}
                    className="h-6 w-6 p-0"
                  >
                    <Copy className="w-3 h-3" />
                  </Button>
                </div>

                {/* Tags */}
                {qr.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {qr.tags.slice(0, 3).map((tag, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {qr.tags.length > 3 && (
                      <Badge variant="secondary" className="text-xs">
                        +{qr.tags.length - 3}
                      </Badge>
                    )}
                  </div>
                )}

                {/* Stats */}
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{qr.download_count} downloads</span>
                  <span>{(qr.file_size / 1024).toFixed(1)} KB</span>
                </div>

                {/* Download Button */}
                <Button
                  onClick={() => downloadQRCode(qr)}
                  className="w-full"
                  size="sm"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create QR Code Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create QR Code</DialogTitle>
            <DialogDescription>
              Generate a custom QR code with your branding
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  placeholder="My QR Code"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="category">Category</Label>
                <Input
                  id="category"
                  placeholder="Marketing"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="url">URL *</Label>
              <Input
                id="url"
                placeholder="https://example.com"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="fill_color">Foreground Color</Label>
                <div className="flex gap-2">
                  <Input
                    id="fill_color"
                    type="color"
                    value={formData.fill_color}
                    onChange={(e) => setFormData({ ...formData, fill_color: e.target.value })}
                    className="w-16 h-10 p-1 cursor-pointer"
                  />
                  <Input
                    value={formData.fill_color}
                    onChange={(e) => setFormData({ ...formData, fill_color: e.target.value })}
                    placeholder="#000000"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="back_color">Background Color</Label>
                <div className="flex gap-2">
                  <Input
                    id="back_color"
                    type="color"
                    value={formData.back_color}
                    onChange={(e) => setFormData({ ...formData, back_color: e.target.value })}
                    className="w-16 h-10 p-1 cursor-pointer"
                  />
                  <Input
                    value={formData.back_color}
                    onChange={(e) => setFormData({ ...formData, back_color: e.target.value })}
                    placeholder="#FFFFFF"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="logo">Logo (Optional)</Label>
              <div className="flex items-center gap-2">
                <Input
                  id="logo"
                  type="file"
                  accept="image/*"
                  onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
                />
                {logoFile && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setLogoFile(null)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Upload a logo to embed in the center of the QR code
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">Tags (comma-separated)</Label>
              <Input
                id="tags"
                placeholder="marketing, product, launch"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                placeholder="Additional notes about this QR code..."
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowCreateDialog(false);
              resetForm();
            }}>
              Cancel
            </Button>
            <Button onClick={createQRCode} disabled={creating}>
              {creating ? 'Creating...' : 'Create QR Code'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit QR Code Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit QR Code</DialogTitle>
            <DialogDescription>
              Update QR code metadata (URL cannot be changed)
            </DialogDescription>
          </DialogHeader>

          {selectedQR && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="edit_name">Name</Label>
                <Input
                  id="edit_name"
                  value={selectedQR.name}
                  onChange={(e) => setSelectedQR({ ...selectedQR, name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_category">Category</Label>
                <Input
                  id="edit_category"
                  value={selectedQR.category || ''}
                  onChange={(e) => setSelectedQR({ ...selectedQR, category: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_tags">Tags (comma-separated)</Label>
                <Input
                  id="edit_tags"
                  value={selectedQR.tags.join(', ')}
                  onChange={(e) => setSelectedQR({
                    ...selectedQR,
                    tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean)
                  })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit_notes">Notes</Label>
                <Textarea
                  id="edit_notes"
                  value={selectedQR.notes || ''}
                  onChange={(e) => setSelectedQR({ ...selectedQR, notes: e.target.value })}
                  rows={3}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowEditDialog(false);
              setSelectedQR(null);
            }}>
              Cancel
            </Button>
            <Button onClick={updateQRCode}>
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Preview QR Code Dialog */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{selectedQR?.name}</DialogTitle>
            <DialogDescription>QR Code Preview</DialogDescription>
          </DialogHeader>

          {selectedQR && (
            <div className="space-y-4">
              {/* Large QR Code */}
              <div className="bg-white rounded-lg p-8 flex items-center justify-center">
                <img
                  src={selectedQR.data_url}
                  alt={selectedQR.name}
                  className="w-full max-w-sm"
                />
              </div>

              {/* Details */}
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">URL:</span>{' '}
                  <span className="text-muted-foreground">{selectedQR.url}</span>
                </div>
                {selectedQR.category && (
                  <div>
                    <span className="font-medium">Category:</span>{' '}
                    <span className="text-muted-foreground">{selectedQR.category}</span>
                  </div>
                )}
                <div>
                  <span className="font-medium">Downloads:</span>{' '}
                  <span className="text-muted-foreground">{selectedQR.download_count}</span>
                </div>
                <div>
                  <span className="font-medium">Size:</span>{' '}
                  <span className="text-muted-foreground">
                    {(selectedQR.file_size / 1024).toFixed(1)} KB
                  </span>
                </div>
                {selectedQR.tags.length > 0 && (
                  <div>
                    <span className="font-medium">Tags:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedQR.tags.map((tag, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowPreviewDialog(false);
              setSelectedQR(null);
            }}>
              Close
            </Button>
            {selectedQR && (
              <Button onClick={() => downloadQRCode(selectedQR)}>
                <Download className="w-4 h-4 mr-2" />
                Download
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
