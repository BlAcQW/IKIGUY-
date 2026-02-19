import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import {
  Users,
  ThumbsUp,
  ThumbsDown,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  TrendingUp,
  UserCheck,
} from "lucide-react";

interface ConsensusData {
  submission_id: string;
  total_validations: number;
  approval_count: number;
  rejection_count: number;
  flagged_count: number;
  average_quality_score: number;
  consensus_decision: "approved" | "rejected" | "pending";
  validators: Array<{
    validator_id: string;
    validator_username: string;
    action: string;
    quality_rating: number;
    confidence_level: number;
    validated_at: string;
    agreed_with_consensus: boolean;
  }>;
  agreement_percentage: number;
  submission_title?: string;
  language_code?: string;
}

interface ConsensusModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  submissionId: string;
  submissionTitle?: string;
}

export function ConsensusModal({
  open,
  onOpenChange,
  submissionId,
  submissionTitle,
}: ConsensusModalProps) {
  const [consensusData, setConsensusData] = useState<ConsensusData | null>(null);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (open && submissionId) {
      loadConsensusData();
    }
  }, [open, submissionId]);

  const loadConsensusData = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getValidationConsensus(submissionId);
      setConsensusData(data);
    } catch (error: any) {
      console.error("Failed to load consensus data:", error);
      toast({
        title: "Failed to Load Consensus",
        description: error.message || "Could not load validation consensus details.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const getDecisionIcon = (decision: string) => {
    switch (decision?.toLowerCase()) {
      case "approved":
        return <CheckCircle className="h-6 w-6 text-green-500" />;
      case "rejected":
        return <XCircle className="h-6 w-6 text-red-500" />;
      default:
        return <AlertCircle className="h-6 w-6 text-yellow-500" />;
    }
  };

  const getDecisionBadge = (decision: string) => {
    switch (decision?.toLowerCase()) {
      case "approved":
        return (
          <Badge className="bg-green-100 text-green-800">
            <CheckCircle className="h-3 w-3 mr-1" />
            Approved
          </Badge>
        );
      case "rejected":
        return (
          <Badge className="bg-red-100 text-red-800">
            <XCircle className="h-3 w-3 mr-1" />
            Rejected
          </Badge>
        );
      default:
        return (
          <Badge className="bg-yellow-100 text-yellow-800">
            <AlertCircle className="h-3 w-3 mr-1" />
            Pending
          </Badge>
        );
    }
  };

  const getActionIcon = (action: string) => {
    switch (action?.toLowerCase()) {
      case "approve":
        return <ThumbsUp className="h-4 w-4 text-green-600" />;
      case "reject":
        return <ThumbsDown className="h-4 w-4 text-red-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getApprovalPercentage = () => {
    if (!consensusData || consensusData.total_validations === 0) return 0;
    return Math.round(
      (consensusData.approval_count / consensusData.total_validations) * 100
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getInitials = (username: string) => {
    return username
      .split("_")
      .map((part) => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl">Validation Consensus</DialogTitle>
          <DialogDescription>
            {submissionTitle || consensusData?.submission_title
              ? `${submissionTitle || consensusData?.submission_title}`
              : "View how validators voted on this submission"}
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        ) : consensusData ? (
          <div className="space-y-6">
            {/* Overall Consensus */}
            <Card>
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Consensus Decision */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      {getDecisionIcon(consensusData.consensus_decision)}
                      <div>
                        <p className="text-sm text-gray-600">Consensus Decision</p>
                        <div className="mt-1">
                          {getDecisionBadge(consensusData.consensus_decision)}
                        </div>
                      </div>
                    </div>

                    <div className="pt-2">
                      <div className="flex items-center justify-between text-sm mb-2">
                        <span className="text-gray-600">Approval Rate</span>
                        <span className="font-medium">{getApprovalPercentage()}%</span>
                      </div>
                      <Progress value={getApprovalPercentage()} className="h-2" />
                    </div>
                  </div>

                  {/* Statistics */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <p className="text-sm text-gray-600 flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        Total Validators
                      </p>
                      <p className="text-2xl font-bold">
                        {consensusData.total_validations}
                      </p>
                    </div>

                    <div className="space-y-1">
                      <p className="text-sm text-gray-600 flex items-center gap-1">
                        <UserCheck className="h-4 w-4" />
                        Agreement
                      </p>
                      <p className="text-2xl font-bold text-green-600">
                        {consensusData.agreement_percentage}%
                      </p>
                    </div>

                    <div className="space-y-1">
                      <p className="text-sm text-gray-600 flex items-center gap-1">
                        <TrendingUp className="h-4 w-4" />
                        Avg Quality
                      </p>
                      <p className="text-2xl font-bold">
                        {consensusData.average_quality_score.toFixed(1)}
                      </p>
                    </div>

                    <div className="space-y-1">
                      <p className="text-sm text-gray-600">Flagged</p>
                      <p className="text-2xl font-bold text-red-600">
                        {consensusData.flagged_count}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Vote Breakdown */}
                <div className="mt-6 pt-6 border-t">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <ThumbsUp className="h-5 w-5 text-green-600" />
                        <span className="text-sm font-medium text-gray-600">
                          Approved
                        </span>
                      </div>
                      <p className="text-3xl font-bold text-green-600">
                        {consensusData.approval_count}
                      </p>
                    </div>

                    <div className="text-center">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <ThumbsDown className="h-5 w-5 text-red-600" />
                        <span className="text-sm font-medium text-gray-600">
                          Rejected
                        </span>
                      </div>
                      <p className="text-3xl font-bold text-red-600">
                        {consensusData.rejection_count}
                      </p>
                    </div>

                    <div className="text-center">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                        <span className="text-sm font-medium text-gray-600">
                          Flagged
                        </span>
                      </div>
                      <p className="text-3xl font-bold text-yellow-600">
                        {consensusData.flagged_count}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Individual Validator Votes */}
            <div>
              <h3 className="font-semibold text-lg mb-4">
                Individual Validator Decisions ({consensusData.validators.length})
              </h3>
              <div className="space-y-3">
                {consensusData.validators.map((validator) => (
                  <Card
                    key={validator.validator_id}
                    className={
                      validator.agreed_with_consensus
                        ? "border-green-200 bg-green-50/30"
                        : "border-orange-200 bg-orange-50/30"
                    }
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1">
                          <Avatar className="h-10 w-10">
                            <AvatarFallback className="bg-primary/10 text-primary">
                              {getInitials(validator.validator_username)}
                            </AvatarFallback>
                          </Avatar>

                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <p className="font-medium">
                                {validator.validator_username}
                              </p>
                              {validator.agreed_with_consensus && (
                                <Badge
                                  variant="outline"
                                  className="text-xs bg-green-100 text-green-800 border-green-300"
                                >
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                  Agreed
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-gray-500">
                              {formatDate(validator.validated_at)}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-6">
                          <div className="text-center">
                            <p className="text-xs text-gray-600 mb-1">Action</p>
                            <div className="flex items-center gap-1">
                              {getActionIcon(validator.action)}
                              <span className="text-sm font-medium capitalize">
                                {validator.action}
                              </span>
                            </div>
                          </div>

                          <div className="text-center">
                            <p className="text-xs text-gray-600 mb-1">Quality</p>
                            <p className="text-sm font-medium">
                              {validator.quality_rating}/5
                            </p>
                          </div>

                          <div className="text-center">
                            <p className="text-xs text-gray-600 mb-1">Confidence</p>
                            <p className="text-sm font-medium">
                              {Math.round(validator.confidence_level * 100)}%
                            </p>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Agreement Summary */}
            <Card className="bg-blue-50/50 border-blue-200">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <UserCheck className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-blue-900">
                      {consensusData.agreement_percentage}% Validator Agreement
                    </p>
                    <p className="text-sm text-blue-700 mt-1">
                      {Math.round(
                        (consensusData.agreement_percentage / 100) *
                          consensusData.total_validations
                      )}{" "}
                      out of {consensusData.total_validations} validators agreed with
                      the final consensus decision.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="text-center py-12">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">No consensus data available</p>
            <p className="text-sm text-gray-500 mt-2">
              This submission may not have been validated yet.
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
