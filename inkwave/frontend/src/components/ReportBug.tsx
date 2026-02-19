import React, { useState } from 'react';
import { Bug, Send, X } from 'lucide-react';
import { useProfile } from '../hooks/useProfile';

interface BugReport {
  title: string;
  description: string;
  type: 'bug' | 'crash' | 'ui' | 'feature' | 'other';
  url: string;
  user_id?: string;
  user_email?: string;
  browser: string;
  timestamp: string;
}

const ReportBug: React.FC = () => {
  const { data: profileData } = useProfile();
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'bug' as BugReport['type'],
  });

  // Only show for admin users
  const isAdmin = profileData?.is_admin === true ||
                  profileData?.role === 'admin' ||
                  profileData?.role === 'superadmin' ||
                  profileData?.role === 'universal_admin';

  // Don't render anything if not admin
  if (!isAdmin) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim() || !formData.description.trim()) {
      alert('Please provide both a title and description for the bug report.');
      return;
    }

    setIsSubmitting(true);

    try {
      // Get browser info
      const browserInfo = `${navigator.userAgent}`;

      // Build bug report
      const bugReport: BugReport = {
        title: formData.title,
        description: formData.description,
        type: formData.type,
        url: window.location.href,
        browser: browserInfo,
        timestamp: new Date().toISOString(),
      };

      // Get API URL from environment or use default
      const apiUrl = import.meta.env.VITE_API_URL || 'https://inkwave-api.ailabsafrica.com';

      // Submit to backend API (which handles Slack and Linear)
      const response = await fetch(`${apiUrl}/api/v1/feedback/bug-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(bugReport),
      });

      if (response.ok) {
        const result = await response.json();
        let message = 'Thank you! Your report has been sent to our team.';
        if (result.linear_issue) {
          message += ` Track it at: ${result.linear_issue.identifier}`;
        }
        alert('Bug Report Sent! 🐛\n\n' + message);

        // Reset form and close
        setFormData({ title: '', description: '', type: 'bug' });
        setIsOpen(false);
      } else {
        throw new Error(`API returned ${response.status}`);
      }
    } catch (error) {
      console.error('Error submitting bug report:', error);
      alert('Submission Failed\n\nCould not send bug report. Please try again or contact support.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {/* Floating Bug Report Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 left-6 z-50 bg-red-500 hover:bg-red-600 text-white p-3 rounded-full shadow-lg transition-all duration-200 hover:scale-110 flex items-center justify-center group"
        aria-label="Report a bug"
        title="Report Bug"
        style={{
          position: 'fixed',
          bottom: '1.5rem',
          left: '1.5rem',
          zIndex: 9999,
        }}
      >
        <Bug className="w-5 h-5 flex-shrink-0" />
        <span className="ml-2 max-w-0 overflow-hidden group-hover:max-w-xs transition-all duration-300 whitespace-nowrap">
          Report Bug
        </span>
      </button>

      {/* Bug Report Modal */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9999 }}
          onClick={() => setIsOpen(false)}
        >
          <div
            className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Bug className="w-5 h-5 text-red-500" />
                <h2 className="text-xl font-semibold">Report a Bug</h2>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-gray-600 text-sm mb-6">
              Help us improve InkWave by reporting bugs and issues. Your feedback is valuable!
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Bug Type */}
              <div>
                <label className="block text-sm font-medium mb-2">Issue Type</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value as BugReport['type'] })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  <option value="bug">🐛 Bug</option>
                  <option value="crash">💥 Crash</option>
                  <option value="ui">🎨 UI Issue</option>
                  <option value="feature">💡 Feature Request</option>
                  <option value="other">❓ Other</option>
                </select>
              </div>

              {/* Bug Title */}
              <div>
                <label htmlFor="title" className="block text-sm font-medium mb-2">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  id="title"
                  type="text"
                  placeholder="Brief summary of the issue..."
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  maxLength={100}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>

              {/* Bug Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-medium mb-2">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="description"
                  placeholder="Please describe what happened, what you expected, and steps to reproduce..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  rows={6}
                  maxLength={1000}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {formData.description.length}/1000 characters
                </p>
              </div>

              {/* Auto-captured Info Notice */}
              <div className="bg-gray-50 p-3 rounded-lg text-xs text-gray-600">
                <p className="font-medium mb-1">Auto-captured info:</p>
                <ul className="list-disc list-inside space-y-0.5">
                  <li>Current page: {window.location.pathname}</li>
                  <li>Browser: {navigator.userAgent.split(' ').slice(0, 3).join(' ')}...</li>
                </ul>
              </div>

              {/* Submit Buttons */}
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  disabled={isSubmitting}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 disabled:opacity-50 flex items-center gap-2"
                >
                  {isSubmitting ? (
                    'Sending...'
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Send Report
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default ReportBug;
