import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { AlertTriangle, Loader2, Flag, MessageSquare } from "lucide-react";

interface DisputeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  validationId: string;
  submissionTitle?: string;
  onSuccess?: () => void;
}

const DISPUTE_CATEGORIES = [
  { value: "incorrect_assessment", label: "Incorrect Quality Assessment" },
  { value: "bias_detected", label: "Bias or Unfair Judgment" },
  { value: "technical_error", label: "Technical Error in Validation" },
  { value: "guideline_violation", label: "Validation Guidelines Not Followed" },
  { value: "language_expertise", label: "Lack of Language Expertise" },
  { value: "other", label: "Other Reason" },
];

export function DisputeModal({
  open,
  onOpenChange,
  validationId,
  submissionTitle,
  onSuccess,
}: DisputeModalProps) {
  const [category, setCategory] = useState<string>("");
  const [reason, setReason] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async () => {
    // Validation
    if (!category) {
      toast({
        title: "Category Required",
        description: "Please select a dispute category.",
        variant: "destructive",
      });
      return;
    }

    if (!reason.trim()) {
      toast({
        title: "Reason Required",
        description: "Please provide a detailed reason for your dispute.",
        variant: "destructive",
      });
      return;
    }

    if (reason.trim().length < 20) {
      toast({
        title: "Reason Too Short",
        description: "Please provide at least 20 characters explaining your dispute.",
        variant: "destructive",
      });
      return;
    }

    if (reason.trim().length > 1000) {
      toast({
        title: "Reason Too Long",
        description: "Please limit your dispute reason to 1000 characters.",
        variant: "destructive",
      });
      return;
    }

    try {
      setSubmitting(true);

      // Combine category and reason
      const fullReason = `[${category}] ${reason.trim()}`;

      await apiClient.disputeValidation(validationId, fullReason);

      toast({
        title: "Dispute Submitted",
        description:
          "Your dispute has been submitted successfully. A moderator will review it shortly.",
      });

      // Reset form
      setCategory("");
      setReason("");

      // Call success callback
      if (onSuccess) {
        onSuccess();
      }

      // Close modal
      onOpenChange(false);
    } catch (error: any) {
      console.error("Failed to submit dispute:", error);
      toast({
        title: "Dispute Submission Failed",
        description: error.message || "Failed to submit your dispute. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!submitting) {
      setCategory("");
      setReason("");
      onOpenChange(false);
    }
  };

  const characterCount = reason.length;
  const isReasonValid = characterCount >= 20 && characterCount <= 1000;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Flag className="h-5 w-5 text-orange-600" />
            Dispute Validation
          </DialogTitle>
          <DialogDescription>
            {submissionTitle
              ? `Submit a dispute for the validation of "${submissionTitle}"`
              : "Submit a dispute if you believe this validation was incorrect or unfair"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Warning Alert */}
          <Alert className="bg-yellow-50 border-yellow-200">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertDescription className="text-yellow-800">
              <strong>Important:</strong> Disputes should only be filed for legitimate
              concerns about validation quality. Frivolous disputes may affect your
              validator reputation.
            </AlertDescription>
          </Alert>

          {/* Dispute Category */}
          <div className="space-y-2">
            <Label htmlFor="category">
              Dispute Category <span className="text-red-500">*</span>
            </Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger id="category">
                <SelectValue placeholder="Select dispute category" />
              </SelectTrigger>
              <SelectContent>
                {DISPUTE_CATEGORIES.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500">
              Choose the category that best describes your dispute
            </p>
          </div>

          {/* Detailed Reason */}
          <div className="space-y-2">
            <Label htmlFor="reason">
              Detailed Explanation <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="reason"
              placeholder="Provide a clear and detailed explanation of why you're disputing this validation. Include specific examples and evidence if possible..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={8}
              className={
                characterCount > 0 && !isReasonValid
                  ? "border-red-300 focus:border-red-500"
                  : ""
              }
            />
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">
                Minimum 20 characters, maximum 1000 characters
              </span>
              <span
                className={
                  characterCount < 20
                    ? "text-red-600"
                    : characterCount > 1000
                    ? "text-red-600"
                    : isReasonValid
                    ? "text-green-600"
                    : "text-gray-600"
                }
              >
                {characterCount} / 1000
              </span>
            </div>
          </div>

          {/* Guidelines */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <MessageSquare className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <p className="font-medium text-blue-900 mb-2">
                  Dispute Resolution Process
                </p>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Your dispute will be reviewed by a moderator within 48 hours</li>
                  <li>
                    • The validator will be notified and may provide a response
                  </li>
                  <li>
                    • If the dispute is upheld, the validation will be re-evaluated
                  </li>
                  <li>
                    • You'll be notified of the decision via notifications
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitting || !isReasonValid || !category}>
            {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Submit Dispute
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
