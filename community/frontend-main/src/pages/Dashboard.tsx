import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/lib/api";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { ProfileEditModal } from "@/components/ProfileEditModal";
import { ReportModal } from "@/components/ReportModal";
import { SubmissionEditModal } from "@/components/SubmissionEditModal";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Trophy,
  Upload,
  CheckCircle,
  Star,
  TrendingUp,
  Users,
  FileText,
  Volume2,
  Calendar,
  Target,
  Award,
  Activity,
  Loader2,
  Globe,
  Database,
  Link,
  Filter,
  ChevronLeft,
  ChevronRight,
  Flag,
  Edit,
  Trash2
} from "lucide-react";

const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

const Dashboard = () => {
  const { user, profile, loading: authLoading } = useAuth();

  // State management
  const [userStats, setUserStats] = useState<any>(null);
  const [recentActivities, setRecentActivities] = useState<any[]>([]);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [platformOverview, setPlatformOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isProfileEditOpen, setIsProfileEditOpen] = useState(false);

  // Submission history state
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [submissionsLoading, setSubmissionsLoading] = useState(false);
  const [totalSubmissions, setTotalSubmissions] = useState(0);
  const [submissionsPage, setSubmissionsPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  // Report modal state
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportEntity, setReportEntity] = useState<{ type: string; id: string; title?: string } | null>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState<any>(null);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Load initial data
  useEffect(() => {
    if (user && !authLoading) {
      loadDashboardData();
    }
  }, [user, authLoading]);

  const loadDashboardData = async () => {
    if (!user) return;

    try {
      setLoading(true);

      // Get real user statistics - use auth endpoint (no user ID param)
      const userStatistics = await apiClient.getUserStatistics().catch(err => {
        console.error("Failed to fetch user statistics:", err);
        return null;
      });

      // Get real user activities - use auth endpoint (no user ID param)
      const userActivities = await apiClient.getUserActivities(undefined, 1, 20).catch(err => {
        console.error("Failed to fetch user activities:", err);
        return [];
      });

      // Get real user achievements - use auth endpoint (no user ID param)
      const userAchievements = await apiClient.getUserAchievements().catch(err => {
        console.error("Failed to fetch user achievements:", err);
        return [];
      });

      // Get platform overview statistics from discovery endpoint
      const overviewResponse = await fetch(`${API_BASE}/discovery/overview`).catch(err => {
        console.error("Failed to fetch platform overview:", err);
        return null;
      });

      if (overviewResponse?.ok) {
        const overviewData = await overviewResponse.json();
        setPlatformOverview(overviewData);
      }

      // Set data from backend responses
      setUserStats(userStatistics);
      setRecentActivities(userActivities);
      setAchievements(userAchievements);

    } catch (error) {
      console.error("Failed to load dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  // Helper functions
  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));

    if (diffInMinutes < 60) {
      return `${diffInMinutes} minutes ago`;
    } else if (diffInMinutes < 1440) {
      const hours = Math.floor(diffInMinutes / 60);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      const days = Math.floor(diffInMinutes / 1440);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    }
  };

  const formatJoinDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' });
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "submission": return <Upload className="h-4 w-4" />;
      case "validation": return <CheckCircle className="h-4 w-4" />;
      case "achievement": return <Award className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const getAchievementIcon = (iconEmoji: string) => {
    return <span className="text-lg">{iconEmoji}</span>;
  };

  // Helper functions for submissions
  const getSubmissionTypeIcon = (type: string) => {
    const typeStr = type?.toLowerCase() || '';
    if (typeStr.includes('audio')) return <Volume2 className="h-4 w-4" />;
    if (typeStr.includes('text')) return <FileText className="h-4 w-4" />;
    if (typeStr.includes('link')) return <Link className="h-4 w-4" />;
    return <Upload className="h-4 w-4" />;
  };

  const getSubmissionStatusBadge = (status: string) => {
    const statusStr = status?.toLowerCase() || 'pending';
    if (statusStr === 'validated' || statusStr === 'approved') {
      return <Badge className="bg-green-100 text-green-800">Validated</Badge>;
    }
    if (statusStr === 'rejected') {
      return <Badge className="bg-red-100 text-red-800">Rejected</Badge>;
    }
    return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>;
  };

  // Load submission history
  const loadSubmissions = async () => {
    try {
      setSubmissionsLoading(true);
      const response = await apiClient.getUserSubmissions(submissionsPage, 20);

      // Apply client-side filters
      let filteredSubmissions = Array.isArray(response) ? response : (response?.items || []);

      if (statusFilter !== 'all') {
        filteredSubmissions = filteredSubmissions.filter((sub: any) =>
          sub.validation_status?.toLowerCase() === statusFilter.toLowerCase() ||
          sub.status?.toLowerCase() === statusFilter.toLowerCase()
        );
      }

      if (typeFilter !== 'all') {
        filteredSubmissions = filteredSubmissions.filter((sub: any) =>
          sub.type?.toLowerCase() === typeFilter.toLowerCase() ||
          sub.submission_type?.toLowerCase() === typeFilter.toLowerCase()
        );
      }

      setSubmissions(filteredSubmissions);
      setTotalSubmissions(response?.total_count || filteredSubmissions.length);
    } catch (error) {
      console.error('Failed to load submissions:', error);
      setSubmissions([]);
    } finally {
      setSubmissionsLoading(false);
    }
  };

  // Load submissions when filters or page changes
  useEffect(() => {
    if (user && !authLoading) {
      loadSubmissions();
    }
  }, [submissionsPage, statusFilter, typeFilter, user, authLoading]);

  // CRUD functions
  const handleNewContribution = () => {
    // In a real implementation, this would navigate to the submit page
    window.location.href = '/submit';
  };

  const handleUpdateGoals = async () => {
    if (!userStats?.weekly_goals) {
      alert('No goals data available to update.');
      return;
    }

    try {
      // Update goals via backend API
      const goals = {
        submissions: userStats.weekly_goals.submissions,
        validations: userStats.weekly_goals.validations
      };

      await apiClient.updateWeeklyGoals(goals);
      alert('Weekly goals updated successfully!');

      // Reload dashboard data to reflect changes
      await loadDashboardData();
    } catch (error) {
      console.error('Failed to update goals:', error);
      alert('Failed to update goals. Please try again.');
    }
  };

  const handleProfileEdit = () => {
    setIsProfileEditOpen(true);
  };

  const handleProfileSaved = async () => {
    // Reload dashboard data after profile update
    await loadDashboardData();
  };

  const handleEditSubmission = (submission: any) => {
    setSelectedSubmission(submission);
    setEditModalOpen(true);
  };

  const handleDeleteSubmission = async (submissionId: string) => {
    if (!window.confirm('Are you sure you want to delete this submission? This action cannot be undone.')) {
      return;
    }

    try {
      setDeletingId(submissionId);
      await apiClient.deleteSubmission(submissionId);

      // Reload submissions list
      await loadSubmissions();

      // Show success message
      alert('Submission deleted successfully');
    } catch (error) {
      console.error('Failed to delete submission:', error);
      alert('Failed to delete submission. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "validated": return "text-green-600";
      case "completed": return "text-blue-600";
      case "unlocked": return "text-purple-600";
      case "pending": return "text-orange-600";
      default: return "text-gray-600";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2 text-lg">Loading dashboard...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!user || !profile || !userStats) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-8">
            <h2 className="text-xl font-semibold mb-2">Unable to load dashboard</h2>
            <p className="text-muted-foreground">Please try refreshing the page.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-muted-foreground">Welcome back, {profile?.full_name || profile?.username || user?.email}!</p>
          </div>
          <Button className="flex items-center gap-2" onClick={handleNewContribution}>
            <Upload className="h-4 w-4" />
            New Contribution
          </Button>
        </div>

        {/* Profile Summary */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="flex items-center gap-6">
              <Avatar className="h-20 w-20">
                <AvatarImage src={profile?.avatar_url || undefined} alt={profile?.full_name || profile?.username || 'User'} />
                <AvatarFallback className="text-lg">
                  {profile?.full_name ? profile.full_name.split(' ').map(n => n[0]).join('').toUpperCase() : profile?.username?.slice(0, 2).toUpperCase() || user?.email?.slice(0, 2).toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-2xl font-semibold">{profile?.full_name || profile?.username || user?.email}</h2>
                  <Badge variant="secondary" className="capitalize">{profile?.level || 'member'}</Badge>
                </div>
                <div className="flex items-center gap-6 text-sm text-muted-foreground mb-3">
                  <span>@{profile?.username || 'user'}</span>
                  <span>Joined {profile?.created_at ? formatJoinDate(profile.created_at) : 'Recently'}</span>
                  <span>Streak: {userStats?.streak_days || 0} days</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Profile:</span>
                  <Badge variant="outline" className="text-xs">
                    {userStats?.submissions_count || 0} contributions
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {userStats?.validations_count || 0} validations
                  </Badge>
                </div>
              </div>
              <div className="text-center space-y-2">
                <div className="text-3xl font-bold text-primary">{(userStats?.submissions_count || 0) * 10}</div>
                <div className="text-sm text-muted-foreground">Total Points</div>
                <Button size="sm" variant="outline" onClick={handleProfileEdit}>
                  Edit Profile
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="contributions">Contributions</TabsTrigger>
            <TabsTrigger value="achievements">Achievements</TabsTrigger>
            <TabsTrigger value="goals">Goals</TabsTrigger>
            <TabsTrigger value="submissions">My Submissions</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* Platform Overview */}
            {platformOverview && (
              <Card className="bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="h-5 w-5 text-blue-600" />
                    Platform Overview
                  </CardTitle>
                  <CardDescription>Community-wide statistics and resources</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600">
                        {platformOverview.total_languages || 0}
                      </div>
                      <p className="text-sm text-muted-foreground">Languages</p>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-purple-600">
                        {platformOverview.total_models || 0}
                      </div>
                      <p className="text-sm text-muted-foreground">ML Models</p>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600">
                        {platformOverview.total_datasets || 0}
                      </div>
                      <p className="text-sm text-muted-foreground">Datasets</p>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-orange-600">
                        {platformOverview.active_contributors || 0}
                      </div>
                      <p className="text-sm text-muted-foreground">Contributors</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Upload className="h-5 w-5 text-blue-500" />
                    <div>
                      <p className="text-2xl font-bold">{userStats?.submissions_count || 0}</p>
                      <p className="text-sm text-muted-foreground">Total Submissions</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="text-2xl font-bold">{userStats?.validations_count || 0}</p>
                      <p className="text-sm text-muted-foreground">Validations Done</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Star className="h-5 w-5 text-yellow-500" />
                    <div>
                      <p className="text-2xl font-bold">{userStats?.average_quality?.toFixed(1) || '0.0'}</p>
                      <p className="text-sm text-muted-foreground">Avg Quality Score</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-purple-500" />
                    <div>
                      <p className="text-2xl font-bold">{userStats?.streak_days || 0}</p>
                      <p className="text-sm text-muted-foreground">Day Streak</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Your latest contributions and achievements</CardDescription>
              </CardHeader>
              <CardContent>
                {recentActivities && recentActivities.length > 0 ? (
                  <div className="space-y-4">
                    {recentActivities.map((activity) => (
                      <div key={activity.id} className="flex items-center gap-4 p-3 rounded-lg bg-muted/30">
                        <div className="flex-shrink-0">
                          {getActivityIcon(activity.type || activity.activity_type)}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium">{activity.title}</p>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>{formatTimeAgo(activity.created_at)}</span>
                            {activity.language_code && (
                              <>
                                <span>•</span>
                                <span>{activity.language_code}</span>
                              </>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="text-right">
                            <p className={`text-sm font-medium ${getStatusColor(activity.status)}`}>
                              {activity.status}
                            </p>
                            {activity.points_awarded > 0 && (
                              <p className="text-sm text-muted-foreground">+{activity.points_awarded} pts</p>
                            )}
                          </div>
                          {(activity.type === 'submission' || activity.activity_type === 'submission') && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setReportEntity({
                                  type: 'submission',
                                  id: activity.id || activity.submission_id,
                                  title: activity.title
                                });
                                setReportModalOpen(true);
                              }}
                            >
                              <Flag className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No recent activity yet.</p>
                    <p className="text-sm">Start contributing to see your activity here!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="contributions" className="space-y-6">
            {/* Contribution Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Volume2 className="h-5 w-5" />
                    Audio
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{userStats?.weekly_goals?.current_submissions || 0}</div>
                  <p className="text-sm text-muted-foreground">submissions</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Text
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{userStats?.submissions_count || 0}</div>
                  <p className="text-sm text-muted-foreground">submissions</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Star className="h-5 w-5" />
                    Translations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{userStats?.validations_count || 0}</div>
                  <p className="text-sm text-muted-foreground">submissions</p>
                </CardContent>
              </Card>
            </div>

            {/* Status Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Submission Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{userStats?.approved_submissions || 0}</div>
                    <p className="text-sm text-muted-foreground">Validated</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{userStats?.pending_submissions || 0}</div>
                    <p className="text-sm text-muted-foreground">Pending</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{userStats?.rejected_submissions || 0}</div>
                    <p className="text-sm text-muted-foreground">Rejected</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{userStats?.submissions_count || 0}</div>
                    <p className="text-sm text-muted-foreground">Total</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="achievements" className="space-y-4">
            {achievements && achievements.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {achievements.map((achievement) => (
                  <Card key={achievement.id} className={achievement.unlocked ? 'bg-green-50 border-green-200' : ''}>
                    <CardContent className="p-6">
                      <div className="flex items-start gap-4">
                        <div className={`p-2 rounded-lg ${achievement.unlocked ? 'bg-green-100' : 'bg-muted'}`}>
                          {getAchievementIcon(achievement.icon)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-semibold">{achievement.title}</h3>
                            {achievement.unlocked && (
                              <Badge variant="secondary" className="bg-green-100 text-green-800">
                                Unlocked
                              </Badge>
                            )}
                            <Badge variant="outline" className="text-xs capitalize">
                              {achievement.rarity}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">
                            {achievement.description}
                          </p>
                          {achievement.unlocked && achievement.awarded_at && (
                            <p className="text-xs text-green-600 mb-2">
                              Earned {formatTimeAgo(achievement.awarded_at)} • +{achievement.points_awarded} points
                            </p>
                          )}
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>Progress</span>
                              <span>{achievement.progress || 0}%</span>
                            </div>
                            <div className="w-full bg-muted rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${
                                  achievement.unlocked ? 'bg-green-500' : 'bg-primary'
                                }`}
                                style={{ width: `${achievement.progress || 0}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <Award className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
                <h3 className="text-lg font-semibold mb-2">No achievements yet</h3>
                <p className="text-muted-foreground mb-4">
                  Start contributing to unlock achievements and earn badges!
                </p>
                <Button onClick={handleNewContribution}>
                  <Upload className="h-4 w-4 mr-2" />
                  Make Your First Contribution
                </Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="goals" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5" />
                      Weekly Goals
                    </CardTitle>
                    <CardDescription>
                      Track your progress towards weekly contribution goals
                    </CardDescription>
                  </div>
                  <Button size="sm" variant="outline" onClick={handleUpdateGoals}>
                    Update Goals
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <h4 className="font-medium">Submit 5 Audio Files</h4>
                      <span className="text-sm text-muted-foreground">
                        {userStats?.weekly_goals?.current_submissions || 0}/{userStats?.weekly_goals?.submissions || 5}
                      </span>
                    </div>
                    <Progress
                      value={((userStats?.weekly_goals?.current_submissions || 0) / (userStats?.weekly_goals?.submissions || 5)) * 100}
                      className="h-2"
                    />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <h4 className="font-medium">Validate 20 Submissions</h4>
                      <span className="text-sm text-muted-foreground">
                        {userStats?.weekly_goals?.current_validations || 0}/{userStats?.weekly_goals?.validations || 10}
                      </span>
                    </div>
                    <Progress
                      value={((userStats?.weekly_goals?.current_validations || 0) / (userStats?.weekly_goals?.validations || 10)) * 100}
                      className="h-2"
                    />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <h4 className="font-medium">Maintain Daily Streak</h4>
                      <span className="text-sm text-muted-foreground">
                        {userStats?.streak_days || 0}/14 days
                      </span>
                    </div>
                    <Progress
                      value={((userStats?.streak_days || 0) / 14) * 100}
                      className="h-2"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>This Week's Focus</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
                    <h4 className="font-medium text-blue-900">Featured Language: Amharic</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      Help expand our Amharic dataset! Earn double points for Amharic contributions this week.
                    </p>
                  </div>
                  <div className="p-4 bg-purple-50 border-l-4 border-purple-500 rounded">
                    <h4 className="font-medium text-purple-900">Validation Drive</h4>
                    <p className="text-sm text-purple-700 mt-1">
                      We need more validators! Help review pending submissions and earn bonus achievements.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="submissions" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  My Submissions
                </CardTitle>
                <CardDescription>
                  Track all your contributions and their validation status
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Filters */}
                <div className="flex flex-wrap gap-4 mb-6">
                  <div className="flex items-center gap-2">
                    <Filter className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Filters:</span>
                  </div>

                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="validated">Validated</SelectItem>
                      <SelectItem value="rejected">Rejected</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={typeFilter} onValueChange={setTypeFilter}>
                    <SelectTrigger className="w-[180px]">
                      <SelectValue placeholder="Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="audio">Audio</SelectItem>
                      <SelectItem value="text">Text</SelectItem>
                      <SelectItem value="link">Link</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Submissions List */}
                {submissionsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div key={i} className="h-20 bg-muted animate-pulse rounded-lg" />
                    ))}
                  </div>
                ) : submissions.length > 0 ? (
                  <div className="space-y-3">
                    {submissions.map((submission, index) => (
                      <div
                        key={submission.id || submission._id || index}
                        className="flex items-center gap-4 p-4 border rounded-lg hover:bg-muted/30 transition-colors"
                      >
                        {/* Type Icon */}
                        <div className="flex-shrink-0">
                          <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                            {getSubmissionTypeIcon(submission.type || submission.submission_type)}
                          </div>
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium truncate">
                              {submission.title || submission.content?.substring(0, 50) || submission.file_name || 'Untitled'}
                            </p>
                            {submission.language_code && (
                              <Badge variant="outline" className="text-xs">
                                {submission.language_code}
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-3 text-sm text-muted-foreground">
                            <span>{new Date(submission.created_at).toLocaleDateString()}</span>
                            {submission.points_awarded && submission.points_awarded > 0 && (
                              <>
                                <span>•</span>
                                <span className="text-green-600">+{submission.points_awarded} pts</span>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Status */}
                        <div className="flex-shrink-0">
                          {getSubmissionStatusBadge(submission.validation_status || submission.status)}
                        </div>

                        {/* Action Buttons */}
                        {(submission.validation_status === 'pending' || submission.status === 'pending' ||
                          submission.validation_status === 'submitted' || submission.status === 'submitted') && (
                          <div className="flex-shrink-0 flex gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleEditSubmission(submission)}
                              title="Edit submission"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDeleteSubmission(submission.id || submission._id)}
                              disabled={deletingId === (submission.id || submission._id)}
                              title="Delete submission"
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              {deletingId === (submission.id || submission._id) ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Pagination */}
                    <div className="flex items-center justify-between pt-4 border-t">
                      <div className="text-sm text-muted-foreground">
                        Showing {Math.min((submissionsPage - 1) * 20 + 1, totalSubmissions)}-
                        {Math.min(submissionsPage * 20, totalSubmissions)} of {totalSubmissions} submissions
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSubmissionsPage(p => Math.max(1, p - 1))}
                          disabled={submissionsPage === 1}
                        >
                          <ChevronLeft className="h-4 w-4" />
                          Previous
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSubmissionsPage(p => p + 1)}
                          disabled={submissionsPage * 20 >= totalSubmissions}
                        >
                          Next
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Upload className="h-16 w-16 mx-auto mb-4 opacity-50 text-muted-foreground" />
                    <h3 className="text-lg font-medium mb-2">No submissions yet</h3>
                    <p className="text-muted-foreground mb-4">
                      Start contributing to see your submission history here
                    </p>
                    <Button onClick={handleNewContribution}>
                      Make Your First Submission
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
      <Footer />

      {/* Profile Edit Modal */}
      <ProfileEditModal
        isOpen={isProfileEditOpen}
        onClose={() => setIsProfileEditOpen(false)}
        onSave={handleProfileSaved}
      />

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

      {/* Submission Edit Modal */}
      {selectedSubmission && (
        <SubmissionEditModal
          open={editModalOpen}
          onOpenChange={setEditModalOpen}
          submission={selectedSubmission}
          onSuccess={loadSubmissions}
        />
      )}
    </div>
  );
};

export default Dashboard;