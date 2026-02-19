/**
 * Book Invitation Modal
 *
 * Allows admins/authors to generate shareable invitation links
 * that grant book access to new users upon registration.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Link2, Copy, Check, Gift, Clock, Users, AlertCircle } from 'lucide-react';
import { api } from '../lib/api';
import toast from 'react-hot-toast';

interface BookInvitationModalProps {
  isOpen: boolean;
  onClose: () => void;
  book: {
    id: string;
    title: string;
    cover_url?: string;
  };
}

interface Invitation {
  invitation_id: string;
  invitation_url: string;
  max_uses: number | null;
  used_count: number;
  expires_at: string | null;
  status: string;
  welcome_message: string | null;
  created_at: string;
}

export function BookInvitationModal({ isOpen, onClose, book }: BookInvitationModalProps) {
  // Form state
  const [maxUses, setMaxUses] = useState<string>('');
  const [expiresInDays, setExpiresInDays] = useState<string>('');
  const [welcomeMessage, setWelcomeMessage] = useState('');

  // Generated invitation
  const [generatedInvitation, setGeneratedInvitation] = useState<Invitation | null>(null);
  const [copied, setCopied] = useState(false);

  // Existing invitations
  const [existingInvitations, setExistingInvitations] = useState<Invitation[]>([]);
  const [loadingInvitations, setLoadingInvitations] = useState(false);

  // Loading state
  const [generating, setGenerating] = useState(false);

  // Load existing invitations for this book
  useEffect(() => {
    if (isOpen && book.id) {
      loadExistingInvitations();
    }
  }, [isOpen, book.id]);

  const loadExistingInvitations = async () => {
    setLoadingInvitations(true);
    try {
      const response = await api.bookInvitations.list({
        book_id: book.id,
        include_inactive: true,
      });
      setExistingInvitations(response.data.invitations || []);
    } catch (error) {
      console.error('Failed to load invitations:', error);
    } finally {
      setLoadingInvitations(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const response = await api.bookInvitations.create({
        book_id: book.id,
        max_uses: maxUses ? parseInt(maxUses) : undefined,
        expires_in_days: expiresInDays ? parseInt(expiresInDays) : undefined,
        welcome_message: welcomeMessage || undefined,
      });

      setGeneratedInvitation(response.data);
      toast.success('Invitation link generated!');

      // Refresh the list
      loadExistingInvitations();

      // Reset form
      setMaxUses('');
      setExpiresInDays('');
      setWelcomeMessage('');
    } catch (error: any) {
      console.error('Failed to generate invitation:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate invitation');
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      toast.success('Link copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy link');
    }
  };

  const handleRevoke = async (invitationId: string) => {
    try {
      await api.bookInvitations.revoke(invitationId);
      toast.success('Invitation revoked');
      loadExistingInvitations();
      if (generatedInvitation?.invitation_id === invitationId) {
        setGeneratedInvitation(null);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to revoke invitation');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-400/10';
      case 'expired': return 'text-yellow-400 bg-yellow-400/10';
      case 'exhausted': return 'text-orange-400 bg-orange-400/10';
      case 'revoked': return 'text-red-400 bg-red-400/10';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/70 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative z-10 w-full max-w-lg bg-gray-800 rounded-2xl shadow-2xl border border-gray-700 max-h-[90vh] overflow-hidden flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Gift className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Share Book Access</h3>
                <p className="text-sm text-gray-400">{book.title}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Content - Scrollable */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Generated Invitation Display */}
            {generatedInvitation && (
              <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
                <div className="flex items-center space-x-2 text-green-400 mb-3">
                  <Check className="h-5 w-5" />
                  <span className="font-semibold">Invitation Link Ready!</span>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    readOnly
                    value={generatedInvitation.invitation_url}
                    className="flex-1 px-3 py-2 bg-gray-900/50 border border-gray-600 rounded-lg text-white text-sm"
                  />
                  <button
                    onClick={() => handleCopy(generatedInvitation.invitation_url)}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition flex items-center space-x-2"
                  >
                    {copied ? (
                      <Check className="h-4 w-4 text-white" />
                    ) : (
                      <Copy className="h-4 w-4 text-white" />
                    )}
                    <span className="text-white text-sm">{copied ? 'Copied!' : 'Copy'}</span>
                  </button>
                </div>
                <p className="text-gray-400 text-xs mt-2">
                  Share this link with users. They'll get access to this book when they register.
                </p>
              </div>
            )}

            {/* Create New Invitation Form */}
            <div className="space-y-4">
              <h4 className="text-white font-medium flex items-center space-x-2">
                <Link2 className="h-4 w-4 text-purple-400" />
                <span>Create New Invitation</span>
              </h4>

              {/* Max Uses */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  <Users className="h-4 w-4 inline mr-1" />
                  Maximum Uses (optional)
                </label>
                <input
                  type="number"
                  min="1"
                  placeholder="Unlimited"
                  value={maxUses}
                  onChange={(e) => setMaxUses(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Expires In Days */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  <Clock className="h-4 w-4 inline mr-1" />
                  Expires In (days, optional)
                </label>
                <input
                  type="number"
                  min="1"
                  max="365"
                  placeholder="Never expires"
                  value={expiresInDays}
                  onChange={(e) => setExpiresInDays(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* Welcome Message */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Welcome Message (optional)
                </label>
                <textarea
                  placeholder="A personal message shown on the signup page..."
                  value={welcomeMessage}
                  onChange={(e) => setWelcomeMessage(e.target.value)}
                  maxLength={500}
                  rows={2}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                />
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold rounded-lg transition disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {generating ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <Link2 className="h-4 w-4" />
                    <span>Generate Invitation Link</span>
                  </>
                )}
              </button>
            </div>

            {/* Existing Invitations */}
            <div className="space-y-3">
              <h4 className="text-white font-medium">Existing Invitations</h4>

              {loadingInvitations ? (
                <div className="text-center py-4 text-gray-400">
                  Loading...
                </div>
              ) : existingInvitations.length === 0 ? (
                <div className="text-center py-4 text-gray-500">
                  No invitations created yet
                </div>
              ) : (
                <div className="space-y-2">
                  {existingInvitations.map((inv) => (
                    <div
                      key={inv.invitation_id}
                      className="bg-gray-700/50 rounded-lg p-3 flex items-center justify-between"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(inv.status)}`}>
                            {inv.status}
                          </span>
                          <span className="text-gray-400 text-xs">
                            {inv.used_count}{inv.max_uses ? `/${inv.max_uses}` : ''} uses
                          </span>
                        </div>
                        <p className="text-gray-300 text-sm truncate mt-1">
                          {inv.invitation_url}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2 ml-2">
                        <button
                          onClick={() => handleCopy(inv.invitation_url)}
                          className="p-2 text-gray-400 hover:text-white hover:bg-gray-600 rounded-lg transition"
                          title="Copy link"
                        >
                          <Copy className="h-4 w-4" />
                        </button>
                        {inv.status === 'active' && (
                          <button
                            onClick={() => handleRevoke(inv.invitation_id)}
                            className="p-2 text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-lg transition"
                            title="Revoke invitation"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

export default BookInvitationModal;
