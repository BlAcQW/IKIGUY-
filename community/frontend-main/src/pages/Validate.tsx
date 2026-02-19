import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import {
  CheckCircle,
  XCircle,
  Clock,
  Users,
  Star,
  Play,
  Volume2,
  FileText,
  AlertTriangle,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  Flag,
  Eye
} from "lucide-react";
import { apiClient, PendingValidation, ValidationHistory, ValidationStats, ValidationCreate } from "@/lib/api";
import { ReportModal } from "@/components/ReportModal";
import { ConsensusModal } from "@/components/ConsensusModal";
import { DisputeModal } from "@/components/DisputeModal";

const Validate = () => {
  // State management
  const [pendingSubmissions, setPendingSubmissions] = useState<PendingValidation[]>([]);
  const [validationHistory, setValidationHistory] = useState<ValidationHistory[]>([]);
  const [stats, setStats] = useState<ValidationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [queueSummary, setQueueSummary] = useState<any>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  // Validation modal state
  const [validationModalOpen, setValidationModalOpen] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState<PendingValidation | null>(null);
  const [validationForm, setValidationForm] = useState<Partial<ValidationCreate>>({
    action: 'approve',
    category: 'content_quality',
    quality_rating: 4,
    confidence_level: 0.8,
    comments: '',
    specific_issues: [],
    suggested_corrections: ''
  });
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportEntity, setReportEntity] = useState<{ type: string; id: string; title?: string } | null>(null);
  const [consensusModalOpen, setConsensusModalOpen] = useState(false);
  const [consensusSubmission, setConsensusSubmission] = useState<{ id: string; title: string } | null>(null);
  const [disputeModalOpen, setDisputeModalOpen] = useState(false);
  const [disputeValidation, setDisputeValidation] = useState<{ id: string; title: string } | null>(null);

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);

      // Make real API calls to backend
      const [pendingData, historyData, statsData] = await Promise.all([
        apiClient.getPendingValidations(1, 20).catch(err => {
          console.warn("Failed to fetch pending validations:", err);
          return [];
        }),
        apiClient.getValidationHistory(1, 20).catch(err => {
          console.warn("Failed to fetch validation history:", err);
          return [];
        }),
        apiClient.getValidationStats().catch(err => {
          console.warn("Failed to fetch validation stats:", err);
          return {
            total_pending: 0,
            total_validated: 0,
            total_points: 0,
            accuracy_rate: 0,
            validations_this_week: 0,
            streak_days: 0,
            rank_percentile: 0
          };
        })
      ]);

      setPendingSubmissions(pendingData);
      setValidationHistory(historyData);
      setStats(statsData);

    } catch (error) {
      console.error("Failed to load validation data:", error);

      // Set empty states on error
      setPendingSubmissions([]);
      setValidationHistory([]);
      setStats({
        total_pending: 0,
        total_validated: 0,
        total_points: 0,
        accuracy_rate: 0,
        validations_this_week: 0,
        streak_days: 0,
        rank_percentile: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const loadQueueSummary = async () => {
    try {
      setSummaryLoading(true);
      const summary = await apiClient.getValidationQueueSummary();
      setQueueSummary(summary);
    } catch (error) {
      console.warn('Failed to load queue summary:', error);
      setQueueSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  };

  // Load queue summary on mount and after validations
  useEffect(() => {
    loadQueueSummary();
  }, []);

  const handleStartValidation = (submissionId: string) => {
    const submission = pendingSubmissions.find(s => s.id === submissionId);
    if (submission) {
      setSelectedSubmission(submission);
      setValidationForm({
        action: 'approve',
        category: 'content_quality',
        quality_rating: 4,
        confidence_level: 0.8,
        comments: '',
        specific_issues: [],
        suggested_corrections: ''
      });
      setValidationModalOpen(true);
    }
  };

  const handlePreviewSubmission = (submissionId: string) => {
    // Open preview modal (would be implemented)
    console.log("Previewing submission:", submissionId);
  };

  const handleSubmitValidation = async () => {
    if (!selectedSubmission) return;

    try {
      setSubmitting(true);

      const validationData: ValidationCreate = {
        submission_id: selectedSubmission.id,
        submission_type: selectedSubmission.type,
        action: validationForm.action!,
        category: validationForm.category!,
        quality_rating: validationForm.quality_rating!,
        confidence_level: validationForm.confidence_level!,
        comments: validationForm.comments,
        specific_issues: validationForm.specific_issues,
        suggested_corrections: validationForm.suggested_corrections,
        time_spent_seconds: 300 // Default 5 minutes
      };

      // Submit validation to backend API
      await apiClient.submitValidation(validationData);

      // Refresh data after successful validation
      await loadData();
      await loadQueueSummary();

      // Close modal
      setValidationModalOpen(false);
      setSelectedSubmission(null);

      // Show success message
      alert('Validation submitted successfully! Thank you for your review.');

    } catch (error) {
      console.error("Validation submission failed:", error);
      alert(`Failed to submit validation: ${error.message || 'Please try again.'}`);
    } finally {
      setSubmitting(false);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "audio": return <Volume2 className="h-4 w-4" />;
      case "text": return <FileText className="h-4 w-4" />;
      case "translation": return <Star className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "bg-red-500";
      case "medium": return "bg-yellow-500";
      case "low": return "bg-green-500";
      default: return "bg-gray-500";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Validate Contributions</h1>
          <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
            Help ensure the quality of African language datasets by reviewing and validating
            community contributions. Your expert feedback helps improve AI models.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-orange-500" />
                <div>
                  {loading ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    <>
                      <p className="text-2xl font-bold">{stats?.total_pending || 0}</p>
                      <p className="text-sm text-muted-foreground">Pending Reviews</p>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div>
                  {loading ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    <>
                      <p className="text-2xl font-bold">{stats?.total_validated || 0}</p>
                      <p className="text-sm text-muted-foreground">Validated</p>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Star className="h-5 w-5 text-yellow-500" />
                <div>
                  {loading ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    <>
                      <p className="text-2xl font-bold">{stats?.total_points.toLocaleString() || 0}</p>
                      <p className="text-sm text-muted-foreground">Points Earned</p>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-blue-500" />
                <div>
                  {loading ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    <>
                      <p className="text-2xl font-bold">{Math.round((stats?.accuracy_rate || 0) * 100)}%</p>
                      <p className="text-sm text-muted-foreground">Accuracy Rate</p>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Queue Summary Widget */}
        {queueSummary && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Validation Queue Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Total Pending */}
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">
                    {queueSummary.total_pending || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Total Pending</div>
                </div>

                {/* Urgent Count */}
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <div className="text-3xl font-bold text-red-600">
                    {queueSummary.urgent_count || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Urgent</div>
                </div>

                {/* By Language (top 3) */}
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-2 text-sm">By Language</h4>
                  {queueSummary.by_language && queueSummary.by_language.length > 0 ? (
                    <div className="space-y-1">
                      {queueSummary.by_language.slice(0, 3).map((lang: any, idx: number) => (
                        <div key={idx} className="flex justify-between text-sm">
                          <span className="truncate">{lang.language || lang.language_code}</span>
                          <Badge variant="secondary" className="ml-2">{lang.count}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">No data</p>
                  )}
                </div>

                {/* By Type */}
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-2 text-sm">By Type</h4>
                  {queueSummary.by_type && queueSummary.by_type.length > 0 ? (
                    <div className="space-y-1">
                      {queueSummary.by_type.map((type: any, idx: number) => (
                        <div key={idx} className="flex justify-between text-sm">
                          <span className="capitalize">{type.type || type.submission_type}</span>
                          <Badge variant="secondary" className="ml-2">{type.count}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">No data</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs defaultValue="pending" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="pending">Pending Validation</TabsTrigger>
            <TabsTrigger value="history">My Reviews</TabsTrigger>
          </TabsList>

          <TabsContent value="pending" className="space-y-4">
            {pendingSubmissions.map((submission) => (
              <Card key={submission.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        {getTypeIcon(submission.type)}
                      </div>
                      <div className="space-y-1">
                        <CardTitle className="text-lg">{submission.title}</CardTitle>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span>by {submission.contributor}</span>
                          <span>•</span>
                          <span>{submission.submittedAt}</span>
                          <span>•</span>
                          <Badge variant="outline" className="text-xs">
                            {submission.language}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${getPriorityColor(submission.priority)}`} />
                      <Badge variant="secondary" className="text-xs">
                        {submission.type}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Quality Score */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>AI Quality Score</span>
                        <span>{submission.ai_quality_score}%</span>
                      </div>
                      <Progress value={submission.ai_quality_score} className="h-2" />
                    </div>

                    {/* Review Progress */}
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        <Users className="h-4 w-4" />
                        Reviews: {submission.current_validations}/{submission.validations_needed}
                      </span>
                      <span className="text-muted-foreground">
                        {submission.validations_needed - submission.current_validations} more needed
                      </span>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        className="flex-1"
                        onClick={() => handleStartValidation(submission.id)}
                        disabled={submitting}
                      >
                        <Play className="h-4 w-4 mr-2" />
                        Review Now
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePreviewSubmission(submission.id)}
                      >
                        Preview
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setReportEntity({
                            type: 'submission',
                            id: submission.id,
                            title: submission.title
                          });
                          setReportModalOpen(true);
                        }}
                      >
                        <Flag className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            <div className="text-center py-8">
              <Button variant="outline">Load More Submissions</Button>
            </div>
          </TabsContent>

          <TabsContent value="history" className="space-y-4">
            {loading ? (
              <div className="text-center py-8">
                <Loader2 className="h-8 w-8 animate-spin mx-auto" />
                <p className="text-muted-foreground mt-2">Loading validation history...</p>
              </div>
            ) : (
              validationHistory.map((review) => (
                <Card key={review.id}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1 flex-1">
                        <h3 className="font-semibold">{review.submission_title}</h3>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <span>Reviewed {review.reviewed_at}</span>
                          <span>•</span>
                          <Badge variant="outline" className="text-xs">
                            {review.language_code.toUpperCase()}
                          </Badge>
                          <span>•</span>
                          <Badge variant="outline" className="text-xs">
                            {review.submission_type}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">My Score</p>
                          <p className="font-semibold">{review.my_score}%</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">Consensus</p>
                          <p className="font-semibold">{review.consensus_score}%</p>
                        </div>
                        <div className="text-center">
                          <p className="text-sm text-muted-foreground">Points</p>
                          <p className="font-semibold text-yellow-600">+{review.points_awarded}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          {review.status === "approved" ? (
                            <CheckCircle className="h-6 w-6 text-green-500" />
                          ) : review.status === "rejected" ? (
                            <XCircle className="h-6 w-6 text-red-500" />
                          ) : review.status === "disputed" ? (
                            <Flag className="h-6 w-6 text-orange-500" />
                          ) : (
                            <AlertTriangle className="h-6 w-6 text-orange-500" />
                          )}
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setConsensusSubmission({
                                  id: review.submission_id,
                                  title: review.submission_title,
                                });
                                setConsensusModalOpen(true);
                              }}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              Details
                            </Button>
                            {review.status !== "disputed" && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-orange-600 hover:text-orange-700 hover:bg-orange-50"
                                onClick={() => {
                                  setDisputeValidation({
                                    id: review.id,
                                    title: review.submission_title,
                                  });
                                  setDisputeModalOpen(true);
                                }}
                              >
                                <Flag className="h-4 w-4 mr-1" />
                                Dispute
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>
        </Tabs>

        {/* Validation Guidelines */}
        <div className="mt-12 max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold mb-6">Validation Guidelines</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  Quality Criteria
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>• Accurate language identification</p>
                <p>• Clear audio quality (for recordings)</p>
                <p>• Proper grammar and spelling</p>
                <p>• Cultural appropriateness</p>
                <p>• No offensive content</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Star className="h-5 w-5 text-yellow-500" />
                  Scoring System
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>• 90-100: Excellent quality</p>
                <p>• 70-89: Good with minor issues</p>
                <p>• 50-69: Acceptable, needs work</p>
                <p>• Below 50: Requires rejection</p>
                <p>• Consensus determines final score</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  Red Flags
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>• Wrong language labeled</p>
                <p>• Machine-generated content</p>
                <p>• Copyright violations</p>
                <p>• Inappropriate material</p>
                <p>• Poor audio/text quality</p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Validation Modal */}
        <Dialog open={validationModalOpen} onOpenChange={setValidationModalOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Validate Submission</DialogTitle>
              <DialogDescription>
                Review and provide feedback for: {selectedSubmission?.title}
              </DialogDescription>
            </DialogHeader>

            {selectedSubmission && (
              <div className="space-y-6">
                {/* Submission Info */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3 mb-2">
                    {getTypeIcon(selectedSubmission.type)}
                    <span className="font-medium">{selectedSubmission.title}</span>
                    <Badge variant="outline">{selectedSubmission.language}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    By {selectedSubmission.contributor} • {selectedSubmission.submittedAt}
                  </p>
                </div>

                {/* Validation Form */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Action</Label>
                    <Select
                      value={validationForm.action}
                      onValueChange={(value: any) => setValidationForm(prev => ({ ...prev, action: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="approve">
                          <div className="flex items-center gap-2">
                            <ThumbsUp className="h-4 w-4 text-green-500" />
                            Approve
                          </div>
                        </SelectItem>
                        <SelectItem value="reject">
                          <div className="flex items-center gap-2">
                            <ThumbsDown className="h-4 w-4 text-red-500" />
                            Reject
                          </div>
                        </SelectItem>
                        <SelectItem value="flag">
                          <div className="flex items-center gap-2">
                            <Flag className="h-4 w-4 text-orange-500" />
                            Flag for Review
                          </div>
                        </SelectItem>
                        <SelectItem value="request_changes">Request Changes</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Category</Label>
                    <Select
                      value={validationForm.category}
                      onValueChange={(value: any) => setValidationForm(prev => ({ ...prev, category: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="content_quality">Content Quality</SelectItem>
                        <SelectItem value="linguistic_accuracy">Linguistic Accuracy</SelectItem>
                        <SelectItem value="cultural_appropriateness">Cultural Appropriateness</SelectItem>
                        <SelectItem value="technical_quality">Technical Quality</SelectItem>
                        <SelectItem value="audio_clarity">Audio Clarity</SelectItem>
                        <SelectItem value="pronunciation">Pronunciation</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Quality Rating (1-5)</Label>
                    <Select
                      value={validationForm.quality_rating?.toString()}
                      onValueChange={(value) => setValidationForm(prev => ({ ...prev, quality_rating: parseInt(value) }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1 - Poor</SelectItem>
                        <SelectItem value="2">2 - Below Average</SelectItem>
                        <SelectItem value="3">3 - Average</SelectItem>
                        <SelectItem value="4">4 - Good</SelectItem>
                        <SelectItem value="5">5 - Excellent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Confidence Level</Label>
                    <Select
                      value={validationForm.confidence_level?.toString()}
                      onValueChange={(value) => setValidationForm(prev => ({ ...prev, confidence_level: parseFloat(value) }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0.6">60% - Somewhat confident</SelectItem>
                        <SelectItem value="0.7">70% - Confident</SelectItem>
                        <SelectItem value="0.8">80% - Very confident</SelectItem>
                        <SelectItem value="0.9">90% - Highly confident</SelectItem>
                        <SelectItem value="1.0">100% - Absolutely certain</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Comments</Label>
                  <Textarea
                    placeholder="Provide detailed feedback about the submission..."
                    value={validationForm.comments}
                    onChange={(e) => setValidationForm(prev => ({ ...prev, comments: e.target.value }))}
                    className="min-h-[100px]"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Suggested Corrections (optional)</Label>
                  <Textarea
                    placeholder="If applicable, suggest specific corrections or improvements..."
                    value={validationForm.suggested_corrections}
                    onChange={(e) => setValidationForm(prev => ({ ...prev, suggested_corrections: e.target.value }))}
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <Button
                    variant="outline"
                    onClick={() => setValidationModalOpen(false)}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSubmitValidation}
                    disabled={submitting || !validationForm.action || !validationForm.category}
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      'Submit Validation'
                    )}
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Report Modal */}
        {reportEntity && (
          <ReportModal
            open={reportModalOpen}
            onOpenChange={setReportModalOpen}
            entityType={reportEntity.type as 'submission' | 'comment' | 'notebook'}
            entityId={reportEntity.id}
            entityTitle={reportEntity.title}
          />
        )}

        {/* Consensus Modal */}
        {consensusSubmission && (
          <ConsensusModal
            open={consensusModalOpen}
            onOpenChange={setConsensusModalOpen}
            submissionId={consensusSubmission.id}
            submissionTitle={consensusSubmission.title}
          />
        )}

        {/* Dispute Modal */}
        {disputeValidation && (
          <DisputeModal
            open={disputeModalOpen}
            onOpenChange={setDisputeModalOpen}
            validationId={disputeValidation.id}
            submissionTitle={disputeValidation.title}
            onSuccess={loadData}
          />
        )}
      </main>
      <Footer />
    </div>
  );
};

export default Validate;