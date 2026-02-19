import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ExportDialog from '@/components/ExportDialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  User,
  MapPin,
  Globe,
  Calendar,
  Trophy,
  Star,
  FileText,
  Music,
  Award,
  TrendingUp,
  Users,
  Settings,
  Loader2,
  Mail,
  Lock,
  Download
} from 'lucide-react';
import { useBackendAuth } from '@/contexts/BackendAuthContext';
import { useNotification } from '@/contexts/NotificationContext';
import { prepareDataForExport } from '@/lib/exportUtils';
import ProfileEditModal from '@/components/ProfileEditModal';

const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

const Profile = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const { user } = useBackendAuth();
  const { showSuccess, showError } = useNotification();

  const [profileData, setProfileData] = useState<any>(null);
  const [userStats, setUserStats] = useState<any>(null);
  const [userActivities, setUserActivities] = useState<any[]>([]);
  const [userAchievements, setUserAchievements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const [exportType, setExportType] = useState<'profile' | 'activities' | 'achievements' | 'full'>('full');

  const isOwnProfile = !userId || userId === user?.id;

  useEffect(() => {
    loadProfileData();
  }, [userId, user]);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      const targetUserId = userId || user?.id;

      if (!targetUserId) {
        navigate('/');
        return;
      }

      // Fetch profile data from backend API
      const headers: Record<string, string> = {
        'Content-Type': 'application/json'
      };

      // Add auth token for own profile or if logged in
      if (user) {
        const token = localStorage.getItem('auth_access_token');
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      // Fetch all data in parallel
      const [profileRes, statsRes, activitiesRes] = await Promise.all([
        fetch(`${API_BASE}/auth/profile/${targetUserId}`, { headers }).catch(() => null),
        fetch(`${API_BASE}/auth/statistics`, { headers }).catch(() => null),
        fetch(`${API_BASE}/auth/activities`, { headers }).catch(() => null)
      ]);

      if (profileRes?.ok) {
        const profileData = await profileRes.json();
        setProfileData(profileData.data || profileData);
      }

      if (statsRes?.ok) {
        const statsData = await statsRes.json();
        setUserStats(statsData.data || statsData);
      }

      if (activitiesRes?.ok) {
        const activitiesData = await activitiesRes.json();
        setUserActivities(activitiesData.data || activitiesData.activities || []);
      }

      // Fetch achievements from backend
      if (isOwnProfile && user) {
        const achievementsRes = await fetch(`${API_BASE}/community/achievements/user`, { headers }).catch(() => null);
        if (achievementsRes?.ok) {
          const achievementsData = await achievementsRes.json();
          setUserAchievements(achievementsData.data || achievementsData || []);
        }
      }

    } catch (error) {
      console.error('Failed to load profile data:', error);

      // Fallback to mock data for development
      const mockProfile = {
        id: userId || user?.id,
        username: 'johndoe',
        full_name: 'John Doe',
        bio: 'Passionate about preserving African languages and cultures. Native Yoruba speaker with expertise in linguistic validation.',
        location: 'Lagos, Nigeria',
        website: 'https://johndoe.dev',
        avatar_url: '/api/placeholder/120/120',
        created_at: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
        languages_spoken: ['yo', 'ig', 'en'],
        language_expertise: [
          {
            language_code: 'yo',
            language_name: 'Yoruba',
            proficiency: 'native',
            specialization: 'cultural_context'
          },
          {
            language_code: 'ig',
            language_name: 'Igbo',
            proficiency: 'fluent',
            specialization: 'pronunciation'
          }
        ],
        verified_languages: ['yo', 'ig'],
        level: 'expert',
        preferences: {
          privacy: {
            profile_visibility: 'public',
            show_email: false,
            show_location: true,
            show_activity: true
          }
        }
      };

      const mockStats = {
        submissions_count: 48,
        validations_count: 156,
        approved_submissions: 42,
        average_quality: 87.5,
        streak_days: 12,
        weekly_goals: {
          submissions: 5,
          validations: 10,
          current_submissions: 3,
          current_validations: 8
        }
      };

      const mockActivities = [
        {
          id: '1',
          activity_type: 'submission',
          title: 'Traditional Yoruba Greetings',
          details: 'audio submission',
          status: 'approved',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
        },
        {
          id: '2',
          activity_type: 'validation',
          title: 'Igbo Proverbs Collection',
          details: 'approve validation',
          status: 'completed',
          timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString()
        }
      ];

      const mockAchievements = [
        {
          id: 'first_submission',
          achievement_type: 'milestone',
          title: 'First Submission',
          description: 'Submit your first contribution',
          icon: '🎯',
          progress: 100,
          unlocked: true,
          unlocked_at: new Date().toISOString()
        },
        {
          id: 'quality_validator',
          achievement_type: 'quality',
          title: 'Quality Validator',
          description: 'Validate 100 submissions',
          icon: '✅',
          progress: 100,
          unlocked: true,
          unlocked_at: new Date().toISOString()
        }
      ];

      setProfileData(mockProfile);
      setUserStats(mockStats);
      setUserActivities(mockActivities);
      setUserAchievements(mockAchievements);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long'
    });
  };

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

  const handleExportProfile = (type: 'profile' | 'activities' | 'achievements' | 'full') => {
    setExportType(type);
    setIsExportDialogOpen(true);
  };

  const getExportData = () => {
    switch (exportType) {
      case 'profile':
        return prepareDataForExport([profileData], {
          excludeFields: ['preferences', 'verified_languages'],
          transformers: {
            created_at: (date) => new Date(date).toLocaleDateString()
          }
        });
      case 'activities':
        return prepareDataForExport(userActivities, {
          transformers: {
            timestamp: (date) => new Date(date).toLocaleString()
          }
        });
      case 'achievements':
        return prepareDataForExport(userAchievements, {
          transformers: {
            unlocked_at: (date) => date ? new Date(date).toLocaleString() : null
          }
        });
      case 'full':
        return prepareDataForExport([{
          profile: profileData,
          statistics: userStats,
          activities: userActivities,
          achievements: userAchievements,
          export_metadata: {
            exported_at: new Date().toISOString(),
            user_id: profileData?.id,
            export_type: 'full_profile_data'
          }
        }]);
      default:
        return [];
    }
  };

  const getExportTitle = () => {
    const username = profileData?.username || profileData?.full_name || 'User';
    switch (exportType) {
      case 'profile':
        return `${username} - Profile Data`;
      case 'activities':
        return `${username} - Activity History`;
      case 'achievements':
        return `${username} - Achievements`;
      case 'full':
        return `${username} - Complete Profile Export`;
      default:
        return 'Profile Export';
    }
  };

  const getExportFilename = () => {
    const username = profileData?.username || 'user';
    const date = new Date().toISOString().split('T')[0];
    return `afrilang_${username}_${exportType}_${date}`;
  };

  const checkPrivacySetting = (setting: string) => {
    if (isOwnProfile) return true;
    return profileData?.preferences?.privacy?.[setting] !== false;
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'submission': return <FileText className="h-4 w-4 text-blue-500" />;
      case 'validation': return <Award className="h-4 w-4 text-green-500" />;
      case 'achievement': return <Trophy className="h-4 w-4 text-yellow-500" />;
      default: return <TrendingUp className="h-4 w-4 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-2 text-lg">Loading profile...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!profileData) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-8">
            <h2 className="text-xl font-semibold mb-2">Profile not found</h2>
            <p className="text-muted-foreground">The requested profile could not be found.</p>
            <Button className="mt-4" onClick={() => navigate('/')}>
              Go Home
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Check if profile is private
  const isPrivateProfile = profileData.preferences?.privacy?.profile_visibility === 'private' && !isOwnProfile;

  if (isPrivateProfile) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-8">
            <Lock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">Private Profile</h2>
            <p className="text-muted-foreground">This profile is set to private.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-4 py-8">
        {/* Profile Header */}
        <Card className="mb-8">
          <CardContent className="p-8">
            <div className="flex flex-col md:flex-row items-start gap-6">
              <Avatar className="h-32 w-32">
                <AvatarImage src={profileData.avatar_url} alt={profileData.full_name} />
                <AvatarFallback className="text-2xl">
                  {profileData.full_name?.split(' ').map((n: string) => n[0]).join('') || 'U'}
                </AvatarFallback>
              </Avatar>

              <div className="flex-1 space-y-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-3xl font-bold">{profileData.full_name}</h1>
                    <Badge variant="secondary" className="capitalize">
                      {profileData.level || 'member'}
                    </Badge>
                  </div>
                  <p className="text-lg text-muted-foreground">@{profileData.username}</p>
                </div>

                {profileData.bio && (
                  <p className="text-muted-foreground">{profileData.bio}</p>
                )}

                <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                  {checkPrivacySetting('show_location') && profileData.location && (
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {profileData.location}
                    </div>
                  )}

                  {profileData.website && (
                    <div className="flex items-center gap-1">
                      <Globe className="h-4 w-4" />
                      <a
                        href={profileData.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        Website
                      </a>
                    </div>
                  )}

                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    Joined {formatDate(profileData.created_at)}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {profileData.verified_languages?.map((langCode: string) => {
                    const expertise = profileData.language_expertise?.find(
                      (e: any) => e.language_code === langCode
                    );
                    return (
                      <Badge key={langCode} variant="outline" className="text-xs">
                        {expertise?.language_name || langCode.toUpperCase()}
                        {expertise?.proficiency === 'native' && ' (Native)'}
                      </Badge>
                    );
                  })}
                </div>

                {isOwnProfile && (
                  <div className="flex gap-2 mt-4">
                    <Button onClick={() => setIsEditModalOpen(true)}>
                      <Settings className="h-4 w-4 mr-2" />
                      Edit Profile
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleExportProfile('full')}
                      className="flex items-center gap-2"
                    >
                      <Download className="h-4 w-4" />
                      Export Data
                    </Button>
                  </div>
                )}
              </div>

              <div className="text-center space-y-4">
                <div>
                  <div className="text-3xl font-bold text-primary">
                    {(userStats?.submissions_count || 0) * 10}
                  </div>
                  <div className="text-sm text-muted-foreground">Total Points</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Profile Content */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="contributions">Contributions</TabsTrigger>
            <TabsTrigger value="achievements">Achievements</TabsTrigger>
            {(checkPrivacySetting('show_activity') || isOwnProfile) && (
              <TabsTrigger value="activity">Activity</TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-blue-500" />
                    <div>
                      <p className="text-2xl font-bold">{userStats?.submissions_count || 0}</p>
                      <p className="text-sm text-muted-foreground">Submissions</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Award className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="text-2xl font-bold">{userStats?.validations_count || 0}</p>
                      <p className="text-sm text-muted-foreground">Validations</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2">
                    <Star className="h-5 w-5 text-yellow-500" />
                    <div>
                      <p className="text-2xl font-bold">
                        {userStats?.average_quality?.toFixed(1) || '0.0'}%
                      </p>
                      <p className="text-sm text-muted-foreground">Quality Score</p>
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

            {/* Weekly Goals (only for own profile) */}
            {isOwnProfile && userStats?.weekly_goals && (
              <Card>
                <CardHeader>
                  <CardTitle>Weekly Goals</CardTitle>
                  <CardDescription>Your progress this week</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Submissions</span>
                      <span>
                        {userStats.weekly_goals.current_submissions || 0}/
                        {userStats.weekly_goals.submissions || 5}
                      </span>
                    </div>
                    <Progress
                      value={
                        ((userStats.weekly_goals.current_submissions || 0) /
                          (userStats.weekly_goals.submissions || 5)) *
                        100
                      }
                      className="h-2"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Validations</span>
                      <span>
                        {userStats.weekly_goals.current_validations || 0}/
                        {userStats.weekly_goals.validations || 10}
                      </span>
                    </div>
                    <Progress
                      value={
                        ((userStats.weekly_goals.current_validations || 0) /
                          (userStats.weekly_goals.validations || 10)) *
                        100
                      }
                      className="h-2"
                    />
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="contributions" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Contribution Stats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {userStats?.approved_submissions || 0}
                    </div>
                    <p className="text-sm text-muted-foreground">Approved</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {(userStats?.submissions_count || 0) - (userStats?.approved_submissions || 0)}
                    </div>
                    <p className="text-sm text-muted-foreground">Pending</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {userStats?.submissions_count || 0}
                    </div>
                    <p className="text-sm text-muted-foreground">Total</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="achievements" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {userAchievements.map((achievement) => (
                <Card
                  key={achievement.id}
                  className={achievement.unlocked ? 'bg-green-50 border-green-200' : ''}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div
                        className={`p-2 rounded-lg ${
                          achievement.unlocked ? 'bg-green-100' : 'bg-muted'
                        }`}
                      >
                        <span className="text-lg">{achievement.icon}</span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold">{achievement.title}</h3>
                          {achievement.unlocked && (
                            <Badge variant="secondary" className="bg-green-100 text-green-800">
                              Unlocked
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">
                          {achievement.description}
                        </p>
                        {achievement.unlocked && achievement.unlocked_at && (
                          <p className="text-xs text-green-600">
                            Earned {formatTimeAgo(achievement.unlocked_at)}
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {(checkPrivacySetting('show_activity') || isOwnProfile) && (
            <TabsContent value="activity" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {userActivities.map((activity) => (
                      <div
                        key={activity.id}
                        className="flex items-center gap-4 p-3 rounded-lg bg-muted/30"
                      >
                        <div className="flex-shrink-0">
                          {getActivityIcon(activity.activity_type)}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium">{activity.title}</p>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>{formatTimeAgo(activity.timestamp)}</span>
                            <span>•</span>
                            <span className="capitalize">{activity.details}</span>
                          </div>
                        </div>
                        <Badge
                          variant={
                            activity.status === 'approved' ? 'default' : 'secondary'
                          }
                          className="text-xs"
                        >
                          {activity.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>
      </main>

      <Footer />

      <ProfileEditModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSave={() => {
          setIsEditModalOpen(false);
          loadProfileData();
        }}
      />

      <ExportDialog
        isOpen={isExportDialogOpen}
        onClose={() => setIsExportDialogOpen(false)}
        data={getExportData()}
        title={getExportTitle()}
        description={`Export your ${exportType === 'full' ? 'complete profile' : exportType} data from AfriLang Community Platform`}
        defaultFilename={getExportFilename()}
        dataType="user"
      />
    </div>
  );
};

export default Profile;