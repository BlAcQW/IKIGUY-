/**
 * Announcement Management Page
 * 
 * Admin interface for managing announcements displayed on the landing page.
 */

import { useState, useEffect } from 'react';
import { 
  Plus, 
  Edit, 
  Trash2, 
  X, 
  Image as ImageIcon, 
  Eye, 
  EyeOff,
  ExternalLink,
  Loader2,
  AlertCircle,
  CheckCircle,
  Calendar,
  Link as LinkIcon
} from 'lucide-react';
import { getApiUrl } from '../../config/api-config';
import ConfirmDialog from '../../components/ConfirmDialog';
import { normalizeAnnouncementImageUrl } from '../../utils/imageUrl';

interface Announcement {
  id: string;
  title: string;
  description?: string;
  image_url?: string;
  cta_text?: string;
  cta_link?: string;
  event_id?: string;
  is_active: boolean;
  is_hero: boolean;
  display_order: number;
  start_date?: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
}

export default function AnnouncementManagement() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    image_url: '',
    cta_text: '',
    cta_link: '',
    event_id: '',
    is_active: true,
    is_hero: false,
    display_order: 0,
    start_date: '',
    end_date: ''
  });
  const [editingAnnouncement, setEditingAnnouncement] = useState<Announcement | null>(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    announcementId: string | null;
    announcementTitle: string;
    isLoading: boolean;
  }>({ isOpen: false, announcementId: null, announcementTitle: '', isLoading: false });
  const [successDialog, setSuccessDialog] = useState<{
    isOpen: boolean;
    message: string;
    title: string;
  }>({ isOpen: false, message: '', title: '' });

  useEffect(() => {
    fetchAnnouncements();
  }, []);

  const fetchAnnouncements = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(getApiUrl('announcements'), {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setAnnouncements(data.announcements || []);
      }
    } catch (error) {
      console.error('Error fetching announcements:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingImage(true);
    try {
      const token = localStorage.getItem('access_token');
      const uploadFormData = new FormData();
      uploadFormData.append('file', file);

      const response = await fetch(getApiUrl('announcements/upload-image'), {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: uploadFormData
      });

      if (response.ok) {
        const data = await response.json();
        setFormData((prev) => ({ ...prev, image_url: data.image_url }));
      } else {
        const error = await response.json();
        const errorMessage = Array.isArray(error.detail) 
          ? error.detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ')
          : (typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail));
        alert(errorMessage || 'Failed to upload image');
      }
    } catch (error) {
      console.error('Error uploading image:', error);
      alert('Failed to upload image');
    } finally {
      setUploadingImage(false);
    }
  };

  const handleCreateAnnouncement = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    try {
      const payload: any = {
        title: formData.title,
        description: formData.description?.trim() || undefined,
        image_url: formData.image_url?.trim() || undefined,
        cta_text: formData.cta_text?.trim() || undefined,
        cta_link: formData.cta_link?.trim() || undefined,
        event_id: formData.event_id?.trim() || undefined,
        is_active: formData.is_active,
        is_hero: formData.is_hero,
        display_order: parseInt(String(formData.display_order)) || 0,
      };

      if (formData.start_date) {
        payload.start_date = new Date(formData.start_date).toISOString();
      }
      if (formData.end_date) {
        payload.end_date = new Date(formData.end_date).toISOString();
      }

      const response = await fetch(getApiUrl('announcements'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setShowCreateModal(false);
        resetForm();
        setSuccessDialog({
          isOpen: true,
          title: 'Announcement Created Successfully!',
          message: `"${formData.title}" has been created successfully.`,
        });
        fetchAnnouncements();
      } else {
        const error = await response.json();
        const errorMessage = Array.isArray(error.detail) 
          ? error.detail.map((e: any) => e.msg || `${e.loc?.join('.')}: ${e.msg || JSON.stringify(e)}`).join(', ')
          : (typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail));
        setSuccessDialog({
          isOpen: true,
          title: 'Error Creating Announcement',
          message: errorMessage || 'Failed to create announcement. Please try again.',
        });
      }
    } catch (error) {
      console.error('Error:', error);
      setSuccessDialog({
        isOpen: true,
        title: 'Error Creating Announcement',
        message: 'Failed to create announcement. Please try again.',
      });
    }
  };

  const handleUpdateAnnouncement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAnnouncement) return;

    const token = localStorage.getItem('access_token');
    try {
      const payload: any = {};

      if (formData.title) payload.title = formData.title;
      if (formData.description !== undefined) payload.description = formData.description || undefined;
      if (formData.image_url !== undefined) payload.image_url = formData.image_url || undefined;
      if (formData.cta_text !== undefined) payload.cta_text = formData.cta_text || undefined;
      if (formData.cta_link !== undefined) payload.cta_link = formData.cta_link || undefined;
      if (formData.event_id !== undefined) payload.event_id = formData.event_id || undefined;
      if (formData.is_active !== undefined) payload.is_active = formData.is_active;
      if (formData.is_hero !== undefined) payload.is_hero = formData.is_hero;
      if (formData.display_order !== undefined) payload.display_order = parseInt(String(formData.display_order)) || 0;

      if (formData.start_date) {
        payload.start_date = new Date(formData.start_date).toISOString();
      } else if (formData.start_date === '') {
        payload.start_date = null;
      }

      if (formData.end_date) {
        payload.end_date = new Date(formData.end_date).toISOString();
      } else if (formData.end_date === '') {
        payload.end_date = null;
      }

      const response = await fetch(getApiUrl(`announcements/${editingAnnouncement.id}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setShowEditModal(false);
        setEditingAnnouncement(null);
        resetForm();
        setSuccessDialog({
          isOpen: true,
          title: 'Announcement Updated Successfully!',
          message: `"${formData.title}" has been updated successfully.`,
        });
        fetchAnnouncements();
      } else {
        const error = await response.json();
        const errorMessage = Array.isArray(error.detail) 
          ? error.detail.map((e: any) => e.msg || `${e.loc?.join('.')}: ${e.msg || JSON.stringify(e)}`).join(', ')
          : (typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail));
        setSuccessDialog({
          isOpen: true,
          title: 'Error Updating Announcement',
          message: errorMessage || 'Failed to update announcement. Please try again.',
        });
      }
    } catch (error) {
      console.error('Error:', error);
      setSuccessDialog({
        isOpen: true,
        title: 'Error Updating Announcement',
        message: 'Failed to update announcement. Please try again.',
      });
    }
  };

  const openEditModal = (announcement: Announcement) => {
    setEditingAnnouncement(announcement);
    // Normalize image URL when opening edit modal to ensure it works
    const normalizedImageUrl = normalizeAnnouncementImageUrl(announcement.image_url || '') || announcement.image_url || '';
    setFormData({
      title: announcement.title,
      description: announcement.description || '',
      image_url: normalizedImageUrl,
      cta_text: announcement.cta_text || '',
      cta_link: announcement.cta_link || '',
      event_id: announcement.event_id || '',
      is_active: announcement.is_active,
      is_hero: announcement.is_hero,
      display_order: announcement.display_order,
      start_date: announcement.start_date ? announcement.start_date.split('T')[0] : '',
      end_date: announcement.end_date ? announcement.end_date.split('T')[0] : ''
    });
    setShowEditModal(true);
  };

  const openDeleteDialog = (announcement: Announcement) => {
    setDeleteDialog({
      isOpen: true,
      announcementId: announcement.id,
      announcementTitle: announcement.title,
      isLoading: false
    });
  };

  const handleDeleteAnnouncement = async () => {
    if (!deleteDialog.announcementId) return;

    setDeleteDialog(prev => ({ ...prev, isLoading: true }));
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(getApiUrl(`announcements/${deleteDialog.announcementId}`), {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setSuccessDialog({
          isOpen: true,
          title: 'Announcement Deleted Successfully!',
          message: `"${deleteDialog.announcementTitle}" has been deleted successfully.`,
        });
        setDeleteDialog({ isOpen: false, announcementId: null, announcementTitle: '', isLoading: false });
        fetchAnnouncements();
      } else {
        setSuccessDialog({
          isOpen: true,
          title: 'Error Deleting Announcement',
          message: 'Failed to delete announcement. Please try again.',
        });
        setDeleteDialog(prev => ({ ...prev, isLoading: false }));
      }
    } catch (error) {
      console.error('Error:', error);
      setSuccessDialog({
        isOpen: true,
        title: 'Error Deleting Announcement',
        message: 'Failed to delete announcement. Please try again.',
      });
      setDeleteDialog(prev => ({ ...prev, isLoading: false }));
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      image_url: '',
      cta_text: '',
      cta_link: '',
      event_id: '',
      is_active: true,
      is_hero: false,
      display_order: 0,
      start_date: '',
      end_date: ''
    });
  };

  const toggleActive = async (announcement: Announcement) => {
    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch(getApiUrl(`announcements/${announcement.id}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_active: !announcement.is_active })
      });

      if (response.ok) {
        fetchAnnouncements();
      }
    } catch (error) {
      console.error('Error toggling active status:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Announcement Management</h1>
          <p className="text-sm text-gray-600 mt-1">Manage announcements displayed on the landing page</p>
        </div>
        <button
          onClick={() => {
            resetForm();
            setShowCreateModal(true);
          }}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Create Announcement
        </button>
      </div>

      {/* Announcements Grid */}
      {announcements.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-500">No announcements created yet.</p>
          <button
            onClick={() => {
              resetForm();
              setShowCreateModal(true);
            }}
            className="mt-4 text-purple-600 hover:underline"
          >
            Create your first announcement
          </button>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {announcements.map(announcement => (
            <div key={announcement.id} className="bg-white rounded-lg shadow overflow-hidden hover:shadow-lg transition-shadow">
              {/* Image */}
              {announcement.image_url && (
                <div className="relative h-48 overflow-hidden bg-gray-100">
                  <img
                    src={normalizeAnnouncementImageUrl(announcement.image_url) || announcement.image_url}
                    alt={announcement.title}
                    className="w-full h-full object-cover"
                  />
                  {!announcement.is_active && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                      <span className="text-white font-semibold">Inactive</span>
                    </div>
                  )}
                </div>
              )}
              
              {/* Content */}
              <div className="p-4">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">{announcement.title}</h3>
                      {announcement.is_hero && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-yellow-100 text-yellow-800 border border-yellow-200">
                          Hero
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => toggleActive(announcement)}
                      className={`p-1.5 rounded-lg transition-colors ${
                        announcement.is_active
                          ? 'text-green-600 hover:bg-green-50'
                          : 'text-gray-400 hover:bg-gray-100'
                      }`}
                      title={announcement.is_active ? 'Hide announcement' : 'Show announcement'}
                    >
                      {announcement.is_active ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                
                {announcement.description && (
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">{announcement.description}</p>
                )}

                {(announcement.cta_text || announcement.start_date || announcement.end_date) && (
                  <div className="space-y-1 mb-3 text-xs text-gray-500">
                    {announcement.cta_text && announcement.cta_link && (
                      <div className="flex items-center gap-1">
                        <LinkIcon className="w-3 h-3" />
                        <span>{announcement.cta_text} → {announcement.cta_link}</span>
                      </div>
                    )}
                    {announcement.start_date && (
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        <span>Starts: {new Date(announcement.start_date).toLocaleDateString()}</span>
                      </div>
                    )}
                    {announcement.end_date && (
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        <span>Ends: {new Date(announcement.end_date).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex items-center gap-2 pt-3 border-t border-gray-200">
                  <button
                    onClick={() => openEditModal(announcement)}
                    className="btn-icon-sm"
                    title="Edit announcement"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => openDeleteDialog(announcement)}
                    className="btn-icon-sm text-red-600 hover:bg-red-50"
                    title="Delete announcement"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <span className="ml-auto text-xs text-gray-500">Order: {announcement.display_order}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <AnnouncementFormModal
          isOpen={showCreateModal}
          onClose={() => {
            setShowCreateModal(false);
            resetForm();
          }}
          onSubmit={handleCreateAnnouncement}
          formData={formData}
          setFormData={setFormData}
          onImageUpload={handleImageUpload}
          uploadingImage={uploadingImage}
          mode="create"
        />
      )}

      {/* Edit Modal */}
      {showEditModal && editingAnnouncement && (
        <AnnouncementFormModal
          isOpen={showEditModal}
          onClose={() => {
            setShowEditModal(false);
            setEditingAnnouncement(null);
            resetForm();
          }}
          onSubmit={handleUpdateAnnouncement}
          formData={formData}
          setFormData={setFormData}
          onImageUpload={handleImageUpload}
          uploadingImage={uploadingImage}
          mode="edit"
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, announcementId: null, announcementTitle: '', isLoading: false })}
        onConfirm={handleDeleteAnnouncement}
        title="Delete Announcement"
        message="Are you sure you want to delete this announcement?"
        itemName={deleteDialog.announcementTitle}
        confirmText="Delete Announcement"
        cancelText="Keep Announcement"
        variant="danger"
        isLoading={deleteDialog.isLoading}
      />

      {/* Success Dialog */}
      {successDialog.isOpen && (
        <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden transform transition-all duration-200">
            <div className="h-2 bg-gradient-to-r from-green-500 to-emerald-600" />
            <div className="p-8">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 ring-4 ring-green-100/50">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{successDialog.title}</h3>
                  <p className="text-gray-600 mb-6">{successDialog.message}</p>
                  <button
                    onClick={() => setSuccessDialog({ isOpen: false, message: '', title: '' })}
                    className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all shadow-lg hover:shadow-xl"
                  >
                    Got it
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Announcement Form Modal Component
interface AnnouncementFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => void;
  formData: any;
  setFormData: (data: any) => void;
  onImageUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  uploadingImage: boolean;
  mode: 'create' | 'edit';
}

function AnnouncementFormModal({
  isOpen,
  onClose,
  onSubmit,
  formData,
  setFormData,
  onImageUpload,
  uploadingImage,
  mode
}: AnnouncementFormModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in"
         onClick={onClose}>
      <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
        <div className="bg-white w-full sm:max-w-2xl rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden transform transition-all duration-200"
             onClick={(e) => e.stopPropagation()}>
          {/* Header */}
          <div className={`bg-gradient-to-r ${mode === 'create' ? 'from-purple-600 via-purple-700 to-blue-700' : 'from-blue-600 via-blue-700 to-indigo-700'} px-6 py-5`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center">
                  <Plus className="w-5 h-5 text-white" />
                </div>
                <h2 className="text-xl font-bold text-white">
                  {mode === 'create' ? 'Create New Announcement' : 'Edit Announcement'}
                </h2>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={onSubmit}>
            <div className="p-6 space-y-5 max-h-[calc(90vh-180px)] overflow-y-auto">
              {/* Title */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  placeholder="Announcement title"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all resize-none"
                  rows={3}
                  placeholder="Announcement description (optional)"
                />
              </div>

              {/* Image Upload */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Image
                </label>
                {formData.image_url ? (
                  <div className="space-y-2">
                    <div className="relative w-full h-48 rounded-lg border-2 border-gray-200 overflow-hidden bg-gray-50 flex items-center justify-center">
                      <img 
                        src={normalizeAnnouncementImageUrl(formData.image_url) || formData.image_url} 
                        alt="Preview" 
                        className="max-w-full max-h-full object-contain"
                        onError={(e) => {
                          console.error('Error loading image preview:', formData.image_url);
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => setFormData((prev) => ({ ...prev, image_url: '' }))}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Remove Image
                    </button>
                  </div>
                ) : (
                  <div>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={onImageUpload}
                      className="hidden"
                      id="image-upload"
                      disabled={uploadingImage}
                    />
                    <label
                      htmlFor="image-upload"
                      className={`flex items-center justify-center gap-2 w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:border-purple-500 transition-all ${uploadingImage ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {uploadingImage ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin text-purple-600" />
                          <span className="text-gray-600">Uploading...</span>
                        </>
                      ) : (
                        <>
                          <ImageIcon className="w-5 h-5 text-gray-400" />
                          <span className="text-gray-600">Click to upload image</span>
                        </>
                      )}
                    </label>
                  </div>
                )}
              </div>

              {/* CTA Text and Link */}
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    CTA Button Text
                  </label>
                  <input
                    type="text"
                    value={formData.cta_text}
                    onChange={(e) => setFormData({ ...formData, cta_text: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    placeholder="e.g., Register Now"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    CTA Button Link
                  </label>
                  <input
                    type="text"
                    value={formData.cta_link}
                    onChange={(e) => setFormData({ ...formData, cta_link: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    placeholder="e.g., /events/conference-2025"
                  />
                </div>
              </div>

              {/* Event ID */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Event ID (Optional)
                </label>
                <input
                  type="text"
                  value={formData.event_id}
                  onChange={(e) => setFormData({ ...formData, event_id: e.target.value })}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  placeholder="Link to specific event/conference"
                />
              </div>

              {/* Date Range */}
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Start Date (Optional)
                  </label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    End Date (Optional)
                  </label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  />
                </div>
              </div>

              {/* Display Order and Status Options */}
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Display Order
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.display_order}
                    onChange={(e) => setFormData({ ...formData, display_order: parseInt(e.target.value) || 0 })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  />
                  <p className="mt-1 text-xs text-gray-500">Lower numbers appear first</p>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Status
                    </label>
                    <label className="flex items-center gap-3 p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-purple-300 hover:bg-gray-50 transition-all">
                      <input
                        type="checkbox"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                        className="w-5 h-5 text-purple-600 rounded border-gray-300 focus:ring-purple-500"
                      />
                      <span className="font-medium text-gray-900">Active (visible on landing page)</span>
                    </label>
                  </div>
                  <div>
                    <label className="flex items-center gap-3 p-4 border-2 border-yellow-200 bg-yellow-50 rounded-lg cursor-pointer hover:border-yellow-300 hover:bg-yellow-100 transition-all">
                      <input
                        type="checkbox"
                        checked={formData.is_hero}
                        onChange={(e) => setFormData({ ...formData, is_hero: e.target.checked })}
                        className="w-5 h-5 text-yellow-600 rounded border-gray-300 focus:ring-yellow-500"
                      />
                      <div>
                        <span className="font-medium text-gray-900 block">Hero Announcement</span>
                        <span className="text-xs text-gray-600">Show prominently on left side of hero section</span>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2.5 text-gray-700 font-medium border-2 border-gray-300 rounded-lg hover:bg-gray-100 transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                className={`flex-1 px-4 py-2.5 bg-gradient-to-r text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl ${
                  mode === 'create'
                    ? 'from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800'
                    : 'from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800'
                }`}
              >
                {mode === 'create' ? 'Create Announcement' : 'Update Announcement'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

