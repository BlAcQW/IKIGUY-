import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "@/hooks/use-toast";
import {
  Shield,
  AlertTriangle,
  MessageSquare,
  Ban,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Users,
  TrendingUp,
  FileText,
  Gavel,
  Loader2
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://language-community-api.ailabsafrica.com/api/v1';

const Moderation = () => {
  const [loading, setLoading] = useState(true);
  const [moderationStats, setModerationStats] = useState({
    pendingReports: 0,
    activeDisputes: 0,
    actionsToday: 0,
    responseTime: "0 hours"
  });
  const [disputes, setDisputes] = useState<any[]>([]);
  const [guidelines, setGuidelines] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [actions, setActions] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState("reports");

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === "reports") {
        await Promise.all([loadModerationData(), loadReports()]);
      } else if (activeTab === "actions") {
        await Promise.all([loadModerationData(), loadActions()]);
      } else if (activeTab === "disputes") {
        await loadDisputes();
      } else if (activeTab === "guidelines") {
        await loadGuidelines();
      }
    } catch (error) {
      console.error("Failed to load moderation data:", error);
      toast({
        title: "Error",
        description: "Failed to load moderation data.",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadModerationData = async () => {
    try {
      const [statsResponse, dashboardResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/governance/moderation/stats`),
        fetch(`${API_BASE_URL}/governance/moderation/dashboard`)
      ]);

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setModerationStats(statsData.data || moderationStats);
      }
    } catch (error) {
      console.error("Error loading moderation data:", error);
    }
  };

  const loadDisputes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/governance/disputes`);
      if (response.ok) {
        const data = await response.json();
        setDisputes(data.data || []);
      }
    } catch (error) {
      console.error("Error loading disputes:", error);
      setDisputes([]);
    }
  };

  const loadGuidelines = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/governance/guidelines`);
      if (response.ok) {
        const data = await response.json();
        setGuidelines(data.data || []);
      }
    } catch (error) {
      console.error("Error loading guidelines:", error);
      setGuidelines([]);
    }
  };

  const loadReports = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/governance/reports?status=pending&page=1&page_size=20`);
      if (response.ok) {
        const data = await response.json();
        setReports(data.data || []);
      }
    } catch (error) {
      console.error("Error loading reports:", error);
      setReports([]);
    }
  };

  const loadActions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/governance/moderation/actions?page=1&page_size=20`);
      if (response.ok) {
        const data = await response.json();
        setActions(data.data || []);
      }
    } catch (error) {
      console.error("Error loading actions:", error);
      setActions([]);
    }
  };

  const handleModerationAction = async (action: string, contentId: string, reason: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/governance/moderation/actions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action,
          content_id: contentId,
          reason
        })
      });

      if (response.ok) {
        toast({
          title: "Action Completed",
          description: `Moderation action "${action}" has been applied.`
        });
        await loadData();
      } else {
        throw new Error("Failed to perform action");
      }
    } catch (error) {
      console.error("Error performing moderation action:", error);
      toast({
        title: "Error",
        description: "Failed to perform moderation action.",
        variant: "destructive"
      });
    }
  };

  const handleVoteOnDispute = async (disputeId: string, vote: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/governance/disputes/${disputeId}/vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ vote })
      });

      if (response.ok) {
        toast({
          title: "Vote Recorded",
          description: "Your vote has been recorded."
        });
        await loadDisputes();
      }
    } catch (error) {
      console.error("Error voting on dispute:", error);
      toast({
        title: "Error",
        description: "Failed to record vote.",
        variant: "destructive"
      });
    }
  };


  const getSeverityColor = (severity: number) => {
    if (severity >= 4) return "bg-red-100 text-red-800 border-red-200";
    if (severity >= 3) return "bg-orange-100 text-orange-800 border-orange-200";
    if (severity >= 2) return "bg-yellow-100 text-yellow-800 border-yellow-200";
    return "bg-blue-100 text-blue-800 border-blue-200";
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "open": return "text-blue-600";
      case "under_review": return "text-orange-600";
      case "resolved": return "text-green-600";
      case "escalated": return "text-red-600";
      default: return "text-gray-600";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Shield className="h-8 w-8 text-primary" />
              Moderation Dashboard
            </h1>
            <p className="text-muted-foreground">Manage community governance and content moderation</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <FileText className="h-4 w-4 mr-2" />
              Guidelines
            </Button>
            <Button>
              <Gavel className="h-4 w-4 mr-2" />
              New Action
            </Button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-500" />
                <div>
                  <p className="text-2xl font-bold">{moderationStats.pendingReports}</p>
                  <p className="text-sm text-muted-foreground">Pending Reports</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-blue-500" />
                <div>
                  <p className="text-2xl font-bold">{moderationStats.activeDisputes}</p>
                  <p className="text-sm text-muted-foreground">Active Disputes</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-green-500" />
                <div>
                  <p className="text-2xl font-bold">{moderationStats.actionsToday}</p>
                  <p className="text-sm text-muted-foreground">Actions Today</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-purple-500" />
                <div>
                  <p className="text-2xl font-bold">{moderationStats.responseTime}</p>
                  <p className="text-sm text-muted-foreground">Avg Response</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="reports">Content Reports</TabsTrigger>
            <TabsTrigger value="disputes">Disputes</TabsTrigger>
            <TabsTrigger value="actions">Recent Actions</TabsTrigger>
            <TabsTrigger value="guidelines">Guidelines</TabsTrigger>
          </TabsList>

          <TabsContent value="reports" className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Pending Content Reports</h2>
              <Select defaultValue="all">
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filter by category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="inappropriate">Inappropriate</SelectItem>
                  <SelectItem value="spam">Spam</SelectItem>
                  <SelectItem value="quality">Quality Issues</SelectItem>
                  <SelectItem value="copyright">Copyright</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {loading ? (
              <div className="flex justify-center items-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : reports.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-muted-foreground">No pending reports found.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {reports.map((report) => (
                <Card key={report._id || report.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge className={getSeverityColor(report.severity || 2)}>
                            Severity {report.severity || 2}
                          </Badge>
                          <Badge variant="outline">{report.category || 'general'}</Badge>
                          <Badge className={report.status === 'pending' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'}>
                            {report.status}
                          </Badge>
                        </div>

                        <h3 className="font-semibold mb-2">
                          {(report.content_type || 'Content').charAt(0).toUpperCase() + (report.content_type || 'Content').slice(1)} Report
                        </h3>
                        <p className="text-sm text-muted-foreground mb-3">
                          {report.report_reason || report.reason}
                        </p>
                        <div className="text-xs text-muted-foreground">
                          Content ID: {report.content_id} • {report.created_at ? new Date(report.created_at).toLocaleString() : 'N/A'}
                        </div>
                      </div>

                      <div className="flex gap-2 ml-4">
                        <Button variant="outline" size="sm">
                          <Eye className="h-4 w-4 mr-1" />
                          Review
                        </Button>
                        <Button variant="outline" size="sm" className="text-green-600 hover:text-green-700">
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Approve
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-600 hover:text-red-700"
                          onClick={() => handleModerationAction("remove", report.content_id, report.report_reason || report.reason)}
                        >
                          <XCircle className="h-4 w-4 mr-1" />
                          Remove
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="disputes" className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Active Disputes</h2>
              <Select defaultValue="all">
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="under_review">Under Review</SelectItem>
                  <SelectItem value="escalated">Escalated</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {loading ? (
              <div className="flex justify-center items-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : disputes.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-muted-foreground">No active disputes found.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {disputes.map((dispute) => (
                <Card key={dispute.dispute_uuid || dispute.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge variant="outline">{(dispute.dispute_type || dispute.type || '').replace('_', ' ')}</Badge>
                          <Badge className={getStatusColor(dispute.status)}>
                            {dispute.status.replace('_', ' ')}
                          </Badge>
                          {dispute.language && <Badge variant="secondary">{dispute.language}</Badge>}
                        </div>

                        <h3 className="font-semibold mb-2">{dispute.title || dispute.subject || 'Dispute'}</h3>
                        <div className="text-sm text-muted-foreground mb-3">
                          {dispute.description && <p className="mb-2">{dispute.description}</p>}
                          {dispute.reportedBy && <span>Reported by {dispute.reportedBy}</span>}
                          {dispute.created_at && <span> • {new Date(dispute.created_at).toLocaleDateString()}</span>}
                        </div>

                        {/* Community Voting */}
                        {dispute.communityVotes && (
                          <div className="flex items-center gap-4 text-xs">
                            <span className="text-green-600">👍 {dispute.communityVotes.agree || 0}</span>
                            <span className="text-red-600">👎 {dispute.communityVotes.disagree || 0}</span>
                            <span className="text-gray-600">➖ {dispute.communityVotes.neutral || 0}</span>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col gap-2 ml-4">
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4 mr-1" />
                            Review
                          </Button>
                          <Button size="sm">
                            Resolve
                          </Button>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-green-600 hover:text-green-700"
                            onClick={() => handleVoteOnDispute(dispute.dispute_uuid || dispute.id, "agree")}
                          >
                            👍 Agree
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:text-red-700"
                            onClick={() => handleVoteOnDispute(dispute.dispute_uuid || dispute.id, "disagree")}
                          >
                            👎 Disagree
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="actions" className="space-y-4">
            <h2 className="text-xl font-semibold">Recent Moderation Actions</h2>

            {loading ? (
              <div className="flex justify-center items-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : actions.length === 0 ? (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-muted-foreground">No recent moderation actions found.</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {actions.map((action) => (
                <Card key={action._id || action.id}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">
                            {(action.action || 'action').replace('_', ' ')}
                          </Badge>
                          <span className="text-sm">→ {action.target_user_id || 'User'}</span>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {action.reason || 'N/A'}
                        </span>
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        <div>by Moderator</div>
                        <div>{action.action_timestamp ? new Date(action.action_timestamp).toLocaleString() : 'N/A'}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="guidelines" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Community Guidelines</h2>
              <Button>
                <FileText className="h-4 w-4 mr-2" />
                Add Guideline
              </Button>
            </div>

            {loading ? (
              <div className="flex justify-center items-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : guidelines.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {guidelines.map((guideline) => (
                  <Card key={guideline.guideline_uuid || guideline.id}>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5" />
                        {guideline.title || guideline.category}
                      </CardTitle>
                      <CardDescription>
                        {guideline.description || guideline.summary}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {guideline.content && (
                          <div>
                            <h4 className="font-medium text-sm mb-1">Content:</h4>
                            <p className="text-sm text-muted-foreground">{guideline.content}</p>
                          </div>
                        )}
                        {guideline.examples && guideline.examples.length > 0 && (
                          <div>
                            <h4 className="font-medium text-sm mb-1">Examples:</h4>
                            <ul className="text-sm text-muted-foreground space-y-1">
                              {guideline.examples.map((example: string, idx: number) => (
                                <li key={idx}>• {example}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Respectful Communication
                  </CardTitle>
                  <CardDescription>
                    Guidelines for community interaction and feedback
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <h4 className="font-medium text-sm mb-1">Examples:</h4>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• Use constructive feedback</li>
                        <li>• Avoid personal attacks</li>
                        <li>• Be culturally sensitive</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-sm mb-1">Consequences:</h4>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• 1st: Warning</li>
                        <li>• 2nd: Temporary suspension</li>
                        <li>• 3rd: Permanent ban</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    Quality Standards
                  </CardTitle>
                  <CardDescription>
                    Standards for submission quality and accuracy
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <h4 className="font-medium text-sm mb-1">Requirements:</h4>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• Clear audio without noise</li>
                        <li>• Accurate transcriptions</li>
                        <li>• Culturally appropriate content</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-medium text-sm mb-1">Consequences:</h4>
                      <ul className="text-sm text-muted-foreground space-y-1">
                        <li>• Low quality: Content removal</li>
                        <li>• Repeated: Points deduction</li>
                        <li>• Spam: Account suspension</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
              </div>
            )}

            {/* Quick Action Panel */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Moderation Action</CardTitle>
                <CardDescription>
                  Take immediate action on content or users
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Action Type</label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select action" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="warning">Issue Warning</SelectItem>
                        <SelectItem value="content_removal">Remove Content</SelectItem>
                        <SelectItem value="points_deduction">Deduct Points</SelectItem>
                        <SelectItem value="temporary_suspension">Temporary Suspension</SelectItem>
                        <SelectItem value="permanent_ban">Permanent Ban</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Target User/Content</label>
                    <Input placeholder="User ID or Content ID" />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Reason</label>
                  <Textarea placeholder="Explain the reason for this action..." />
                </div>

                <div className="flex gap-2">
                  <Button variant="outline">Preview Action</Button>
                  <Button>Execute Action</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
      <Footer />
    </div>
  );
};

export default Moderation;