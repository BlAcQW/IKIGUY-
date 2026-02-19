import React, { useState } from 'react';
import { Bug, Send } from 'lucide-react';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { useMongoAuth } from './auth/MongoAuthContext';
import { useToast } from '@/hooks/use-toast';

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
  const { user } = useMongoAuth();
  const { toast } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'bug' as BugReport['type'],
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim() || !formData.description.trim()) {
      toast({
        title: "Missing Information",
        description: "Please provide both a title and description for the bug report.",
        variant: "destructive",
        duration: 3000,
      });
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
        user_id: user?.id,
        user_email: user?.email,
        browser: browserInfo,
        timestamp: new Date().toISOString(),
      };

      // Get API URL from environment or use default
      const apiUrl = import.meta.env.VITE_API_URL || 'https://api.ailabsafrica.com';

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

        let description = "Thank you! Your report has been sent to our team.";
        if (result.linear_issue) {
          description += ` Track it at: ${result.linear_issue.identifier}`;
        }

        toast({
          title: "Bug Report Sent! 🐛",
          description,
          duration: 4000,
        });

        // Reset form and close
        setFormData({ title: '', description: '', type: 'bug' });
        setIsOpen(false);
      } else {
        throw new Error(`API returned ${response.status}`);
      }
    } catch (error) {
      console.error('Error submitting bug report:', error);
      toast({
        title: "Submission Failed",
        description: "Could not send bug report. Please try again or contact support.",
        variant: "destructive",
        duration: 5000,
      });
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
      >
        <Bug className="w-5 h-5 flex-shrink-0" />
        <span className="ml-2 max-w-0 overflow-hidden group-hover:max-w-xs transition-all duration-300 whitespace-nowrap">
          Report Bug
        </span>
      </button>

      {/* Bug Report Dialog */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bug className="w-5 h-5 text-red-500" />
              Report a Bug
            </DialogTitle>
            <DialogDescription>
              Help us improve KasaAI by reporting bugs and issues. Your feedback is valuable!
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            {/* Bug Type */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Issue Type</label>
              <Select
                value={formData.type}
                onValueChange={(value) => setFormData({ ...formData, type: value as BugReport['type'] })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bug">🐛 Bug</SelectItem>
                  <SelectItem value="crash">💥 Crash</SelectItem>
                  <SelectItem value="ui">🎨 UI Issue</SelectItem>
                  <SelectItem value="feature">💡 Feature Request</SelectItem>
                  <SelectItem value="other">❓ Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Bug Title */}
            <div className="space-y-2">
              <label htmlFor="title" className="text-sm font-medium">
                Title <span className="text-red-500">*</span>
              </label>
              <Input
                id="title"
                placeholder="Brief summary of the issue..."
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
                maxLength={100}
              />
            </div>

            {/* Bug Description */}
            <div className="space-y-2">
              <label htmlFor="description" className="text-sm font-medium">
                Description <span className="text-red-500">*</span>
              </label>
              <Textarea
                id="description"
                placeholder="Please describe what happened, what you expected, and steps to reproduce..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                required
                rows={6}
                maxLength={1000}
              />
              <p className="text-xs text-muted-foreground">
                {formData.description.length}/1000 characters
              </p>
            </div>

            {/* Auto-captured Info Notice */}
            <div className="bg-muted/50 p-3 rounded-lg text-xs text-muted-foreground">
              <p className="font-medium mb-1">Auto-captured info:</p>
              <ul className="list-disc list-inside space-y-0.5">
                <li>Current page: {window.location.pathname}</li>
                <li>Browser: {navigator.userAgent.split(' ').slice(0, 3).join(' ')}...</li>
                {user?.email && <li>Your email: {user.email}</li>}
              </ul>
            </div>

            {/* Submit Buttons */}
            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="bg-red-500 hover:bg-red-600"
              >
                {isSubmitting ? (
                  <>Sending...</>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Send Report
                  </>
                )}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ReportBug;
