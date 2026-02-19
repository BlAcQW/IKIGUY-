import { useState, useEffect } from "react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import RealTimeChat from "@/components/RealTimeChat";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Trophy,
  Crown,
  Medal,
  Star,
  Users,
  MessageCircle,
  Calendar,
  TrendingUp,
  Hash,
  Loader2
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { useWebSocket } from "@/contexts/WebSocketContext";

const Community = () => {
  // State management
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [validatorLeaderboard, setValidatorLeaderboard] = useState<any[]>([]);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [languageChannels, setLanguageChannels] = useState<any[]>([]);
  const [communityStats, setCommunityStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [validatorsLoading, setValidatorsLoading] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState("Yoruba");
  const [validatorTimeframe, setValidatorTimeframe] = useState('monthly');
  const { isConnected, onlineUsers } = useWebSocket();

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);

      // Make real API calls to backend
      const [leaderboardData, activityData, achievementsData, channelsData, statsData] = await Promise.all([
        apiClient.getLeaderboard('monthly', undefined, 1, 50).catch(err => {
          console.warn("Failed to fetch leaderboard:", err);
          return [] as any[];
        }),
        apiClient.getCommunityActivityFeed(undefined, 1, 20).catch(err => {
          console.warn("Failed to fetch activity feed:", err);
          return [] as any[];
        }),
        apiClient.getAllAchievements().catch(err => {
          console.warn("Failed to fetch achievements:", err);
          return [] as any[];
        }),
        apiClient.getLanguageChannels().catch(err => {
          console.warn("Failed to fetch language channels:", err);
          return [] as any[];
        }),
        apiClient.getCommunityStats().catch(err => {
          console.warn("Failed to fetch community stats:", err);
          return {
            active_members: 0,
            total_contributions: 0,
            total_languages: 0,
            average_quality_score: 0,
            daily_active_users: 0,
            weekly_active_users: 0,
            monthly_active_users: 0
          };
        })
      ]);

      setLeaderboard(leaderboardData);
      setRecentActivity(activityData);
      setAchievements(achievementsData);
      setLanguageChannels(channelsData);
      setCommunityStats(statsData);

    } catch (error) {
      console.error("Failed to load community data:", error);

      // Set empty states on error
      setLeaderboard([]);
      setRecentActivity([]);
      setAchievements([]);
      setLanguageChannels([]);
      setCommunityStats({
        active_members: 0,
        total_contributions: 0,
        total_languages: 0,
        average_quality_score: 0,
        daily_active_users: 0,
        weekly_active_users: 0,
        monthly_active_users: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const loadValidatorLeaderboard = async (timeframe: string = 'monthly') => {
    try {
      setValidatorsLoading(true);
      const data = await apiClient.getValidatorLeaderboard(timeframe, 1, 50);
      setValidatorLeaderboard(Array.isArray(data) ? data : (data?.items || []));
    } catch (error) {
      console.warn("Failed to fetch validator leaderboard:", error);
      setValidatorLeaderboard([]);
    } finally {
      setValidatorsLoading(false);
    }
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

  const getAchievementIcon = (iconName: string) => {
    switch (iconName) {
      case "star": return <Star className="h-5 w-5" />;
      case "trending-up": return <TrendingUp className="h-5 w-5" />;
      case "users": return <Users className="h-5 w-5" />;
      case "crown": return <Crown className="h-5 w-5" />;
      default: return <Star className="h-5 w-5" />;
    }
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1: return <Crown className="h-5 w-5 text-yellow-500" />;
      case 2: return <Trophy className="h-5 w-5 text-gray-400" />;
      case 3: return <Medal className="h-5 w-5 text-amber-600" />;
      default: return <span className="text-muted-foreground">#{rank}</span>;
    }
  };

  const handleChannelSelect = (channelName: string) => {
    setSelectedChannel(channelName);
  };

  const handleJoinChannel = (channelId: string) => {
    console.log(`Joining channel: ${channelId}`);
  };

  const getSelectedChannelData = () => {
    return languageChannels.find(c => c.name === selectedChannel) || languageChannels[0];
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">AfriLang Community</h1>
          <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
            Connect with fellow language enthusiasts, compete in challenges,
            and collaborate to preserve African languages for future generations.
          </p>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="leaderboard">Leaderboard</TabsTrigger>
            <TabsTrigger value="validators" onClick={() => loadValidatorLeaderboard(validatorTimeframe)}>
              Validators
            </TabsTrigger>
            <TabsTrigger value="chat">Language Channels</TabsTrigger>
            <TabsTrigger value="achievements">Achievements</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Community Stats */}
              <div className="lg:col-span-2 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Community Stats</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin" />
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <p className="text-2xl font-bold text-blue-600">{communityStats?.active_members.toLocaleString()}</p>
                          <p className="text-sm text-muted-foreground">Active Members</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-green-600">{communityStats?.total_contributions.toLocaleString()}</p>
                          <p className="text-sm text-muted-foreground">Contributions</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-purple-600">{communityStats?.total_languages}</p>
                          <p className="text-sm text-muted-foreground">Languages</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-orange-600">{Math.round((communityStats?.average_quality_score || 0) * 100)}%</p>
                          <p className="text-sm text-muted-foreground">Quality Score</p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Recent Activity</CardTitle>
                    <CardDescription>
                      Latest contributions and achievements from the community
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin" />
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {(recentActivity || []).map((activity) => (
                          <div key={activity.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                            <div className="flex items-center gap-3">
                              <Avatar className="h-8 w-8">
                                <AvatarFallback className="text-xs">
                                  {(activity.user_name || '').split(' ').filter(n => n).map(n => n[0]).join('') || 'U'}
                                </AvatarFallback>
                              </Avatar>
                              <div>
                                <p className="text-sm">
                                  <span className="font-medium">{activity.user_name}</span> {activity.action} {activity.item}
                                </p>
                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                  <span>{formatTimeAgo(activity.timestamp)}</span>
                                  <span>•</span>
                                  <Badge variant="outline" className="text-xs">
                                    {activity.language_name}
                                  </Badge>
                                </div>
                              </div>
                            </div>
                            <Badge variant="secondary" className="text-green-600">
                              +{activity.points_awarded}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Top Contributors */}
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Top Contributors</CardTitle>
                    <CardDescription>This week's champions</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin" />
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {(leaderboard || []).slice(0, 3).map((user) => (
                          <div key={user.rank} className="flex items-center gap-3 p-2 rounded-lg">
                            <div className="flex-shrink-0">
                              {getRankIcon(user.rank)}
                            </div>
                            <Avatar className="h-8 w-8">
                              <AvatarFallback className="text-xs">
                                {user.full_name ? (user.full_name.split(' ') || []).map(n => n[0]).join('') : (user.username || '').slice(0, 2).toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium truncate">{user.full_name || user.username}</p>
                              <p className="text-xs text-muted-foreground">{user.total_points.toLocaleString()} pts</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Language Spotlight</CardTitle>
                    <CardDescription>Featured this week</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center space-y-3">
                      <div className="text-4xl">🏛️</div>
                      <h3 className="font-semibold">Amharic</h3>
                      <p className="text-sm text-muted-foreground">
                        Help preserve Ethiopia's ancient language with special bonus points this week!
                      </p>
                      <Button size="sm" className="w-full">
                        Contribute Now
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="leaderboard" className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Community Leaderboard</h2>
              <Badge variant="secondary">This Month</Badge>
            </div>

            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              <div className="space-y-2">
                {(leaderboard || []).map((user) => (
                  <Card key={user.rank} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center justify-center w-12 h-12">
                          {getRankIcon(user.rank)}
                        </div>
                        <Avatar className="h-12 w-12">
                          <AvatarFallback>
                            {user.full_name ? (user.full_name.split(' ') || []).map(n => n[0]).join('') : (user.username || '').slice(0, 2).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">{user.full_name || user.username}</h3>
                            <Badge variant="outline" className="text-xs">
                              {user.badge}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            Specializes in {user.specialization}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-lg">{user.total_points.toLocaleString()}</p>
                          <p className="text-sm text-muted-foreground">{user.total_contributions} contributions</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="validators" className="space-y-4">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold">Validator Leaderboard</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Top contributors helping maintain data quality through validation
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant={validatorTimeframe === 'weekly' ? 'default' : 'outline'}
                  onClick={() => {
                    setValidatorTimeframe('weekly');
                    loadValidatorLeaderboard('weekly');
                  }}
                >
                  Weekly
                </Button>
                <Button
                  size="sm"
                  variant={validatorTimeframe === 'monthly' ? 'default' : 'outline'}
                  onClick={() => {
                    setValidatorTimeframe('monthly');
                    loadValidatorLeaderboard('monthly');
                  }}
                >
                  Monthly
                </Button>
                <Button
                  size="sm"
                  variant={validatorTimeframe === 'all_time' ? 'default' : 'outline'}
                  onClick={() => {
                    setValidatorTimeframe('all_time');
                    loadValidatorLeaderboard('all_time');
                  }}
                >
                  All Time
                </Button>
              </div>
            </div>

            {validatorsLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : validatorLeaderboard.length > 0 ? (
              <div className="space-y-2">
                {validatorLeaderboard.map((validator, index) => (
                  <Card key={validator.user_id || index} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-4">
                        {/* Rank */}
                        <div className="flex items-center justify-center w-12 h-12">
                          {getRankIcon(index + 1)}
                        </div>

                        {/* Avatar */}
                        <Avatar className="h-12 w-12">
                          <AvatarFallback>
                            {(validator.username || validator.full_name || 'V')
                              .split(' ')
                              .map(n => n[0])
                              .join('')
                              .toUpperCase()
                              .slice(0, 2)}
                          </AvatarFallback>
                        </Avatar>

                        {/* User Info */}
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">
                              {validator.full_name || validator.username || 'Anonymous'}
                            </h3>
                            {(index + 1) <= 3 && (
                              <Badge className="bg-gradient-to-r from-yellow-400 to-yellow-600 text-white">
                                Top {index + 1}
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                            <span>{validator.total_reviews || validator.total_validations || 0} reviews</span>
                            {validator.accuracy_percentage !== undefined && (
                              <>
                                <span>•</span>
                                <span className={validator.accuracy_percentage >= 90 ? 'text-green-600 font-medium' : ''}>
                                  {Math.round(validator.accuracy_percentage)}% accuracy
                                </span>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Stats */}
                        <div className="text-right">
                          <p className="font-bold text-lg text-blue-600">
                            {(validator.total_points || validator.points || 0).toLocaleString()} pts
                          </p>
                          {validator.avg_review_time && (
                            <p className="text-xs text-muted-foreground">
                              Avg: {Math.round(validator.avg_review_time)}s
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="p-12 text-center">
                  <Trophy className="h-16 w-16 mx-auto mb-4 opacity-30 text-muted-foreground" />
                  <h3 className="text-lg font-medium mb-2">No Validators Yet</h3>
                  <p className="text-sm text-muted-foreground">
                    Be the first to contribute by validating submissions
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="chat" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Channel List */}
              <div className="lg:col-span-1">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      Language Channels
                      <Badge variant="outline" className="text-xs">
                        {onlineUsers.length} online
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-2">
                    {loading ? (
                      <div className="flex justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin" />
                      </div>
                    ) : (
                      <ScrollArea className="h-80">
                        <div className="space-y-1">
                          {(languageChannels || []).map((channel) => (
                            <div
                              key={channel.id}
                              className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-muted transition-colors ${
                                selectedChannel === channel.name ? 'bg-primary/10 border border-primary/20' : ''
                              }`}
                              onClick={() => handleChannelSelect(channel.name)}
                            >
                              <Hash className="h-4 w-4 text-muted-foreground" />
                              <div className="flex-1">
                                <p className="text-sm font-medium">{channel.name}</p>
                                <p className="text-xs text-muted-foreground">{channel.member_count} members</p>
                              </div>
                              <div className="flex items-center gap-1">
                                {channel.is_active && (
                                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                                )}
                                {isConnected && (
                                  <Badge variant="outline" className="text-xs px-1">
                                    Live
                                  </Badge>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Real-time Chat Area */}
              <div className="lg:col-span-3">
                {getSelectedChannelData() && (
                  <RealTimeChat
                    channelId={getSelectedChannelData()?.id || selectedChannel}
                    channelName={selectedChannel}
                    className="h-full"
                  />
                )}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="achievements" className="space-y-4">
            {loading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(achievements || []).map((achievement) => (
                  <Card key={achievement.achievement_id} className={achievement.unlocked ? 'bg-green-50 border-green-200' : ''}>
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
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">
                            {achievement.description}
                          </p>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span>Progress</span>
                              <span>{achievement.progress}%</span>
                            </div>
                            <div className="w-full bg-muted rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${
                                  achievement.unlocked ? 'bg-green-500' : 'bg-primary'
                                }`}
                                style={{ width: `${achievement.progress}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>
      <Footer />
    </div>
  );
};

export default Community;