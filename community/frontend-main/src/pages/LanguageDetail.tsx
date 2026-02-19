import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Users,
  BookOpen,
  Globe,
  Mic,
  FileText,
  TrendingUp,
  MapPin,
  Calendar,
  Award,
  ExternalLink,
  ArrowLeft,
  Download,
  Play,
  Loader2,
  Target,
  Link as LinkIcon
} from "lucide-react";

interface LanguageDetail {
  code: string;
  name: string;
  native_name: string;
  family: string;
  subfamily?: string;
  iso639_1?: string;
  iso639_2?: string;
  iso639_3: string;
  speakers: number;
  countries: string[];
  regions: string[];
  writing_systems: string[];
  status: 'thriving' | 'stable' | 'endangered' | 'severely_endangered' | 'critically_endangered';
  description: string;
  cultural_significance: string;
  linguistic_features: string[];
}

interface LanguageStats {
  total_submissions: number;
  text_submissions: number;
  audio_submissions: number;
  validated_submissions: number;
  contributors: number;
  total_hours: number;
  quality_score: number;
  recent_activity: Array<{
    id: string;
    type: 'submission' | 'validation' | 'translation';
    user: string;
    timestamp: string;
    title: string;
  }>;
  top_contributors: Array<{
    username: string;
    contributions: number;
    points: number;
  }>;
}

const LanguageDetail = () => {
  const { languageCode } = useParams<{ languageCode: string }>();
  const navigate = useNavigate();

  const [language, setLanguage] = useState<LanguageDetail | null>(null);
  const [stats, setStats] = useState<LanguageStats | null>(null);
  const [notebooks, setNotebooks] = useState<any[]>([]);
  const [languageModels, setLanguageModels] = useState<any[]>([]);
  const [languageDatasets, setLanguageDatasets] = useState<any[]>([]);
  const [languageResources, setLanguageResources] = useState<any[]>([]);
  const [trendingModels, setTrendingModels] = useState<any[]>([]);
  const [trendingDatasets, setTrendingDatasets] = useState<any[]>([]);
  const [trendingResources, setTrendingResources] = useState<any[]>([]);
  const [taskDiscovery, setTaskDiscovery] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [discoveryLoading, setDiscoveryLoading] = useState(false);
  const [contributors, setContributors] = useState<any[]>([]);
  const [contributorsLoading, setContributorsLoading] = useState(false);

  useEffect(() => {
    if (languageCode) {
      loadLanguageData();
      loadDiscoveryData();
      loadContributors();
    }
  }, [languageCode]);

  const loadContributors = async () => {
    if (!languageCode) return;

    try {
      setContributorsLoading(true);
      const response = await fetch(`https://language-community-api.ailabsafrica.com/api/v1/community/languages/${languageCode}/contributors?page=1&page_size=20`);

      if (response.ok) {
        const data = await response.json();
        setContributors(data.items || []);
      } else {
        console.warn("Failed to load contributors");
        setContributors([]);
      }
    } catch (error) {
      console.error("Error loading contributors:", error);
      setContributors([]);
    } finally {
      setContributorsLoading(false);
    }
  };

  const loadLanguageData = async () => {
    try {
      setLoading(true);

      // Fetch real language data from community API
      const response = await fetch(`https://language-community-api.ailabsafrica.com/api/v1/languages/${languageCode}`);
      if (!response.ok) {
        throw new Error(`Language not found: ${languageCode}`);
      }

      const languageData = await response.json();

      // Transform API data to match component interface
      const apiLanguage: LanguageDetail = {
        code: languageData.code,
        name: languageData.name,
        native_name: languageData.native_name,
        family: languageData.family,
        subfamily: languageData.subfamily || 'Unknown',
        iso639_1: languageData.code.length === 2 ? languageData.code : '',
        iso639_2: languageData.code.length === 3 ? languageData.code : '',
        iso639_3: languageData.code,
        speakers: languageData.speakers,
        countries: languageData.countries || [],
        regions: languageData.regions || [],
        writing_systems: ['Latin script'], // Default for African languages
        status: languageData.development_status === 'active' ? 'thriving' : 'stable',
        description: `${languageData.name} is an African language with ${languageData.speakers ? languageData.speakers.toLocaleString() + ' speakers' : 'speakers'} across ${languageData.countries?.length || 0} countries.`,
        cultural_significance: `${languageData.name} plays an important role in preserving cultural identity and traditional knowledge in its speaking communities.`,
        linguistic_features: ['Oral tradition', 'Cultural significance', 'Community language']
      };

      const mockStats: LanguageStats = {
        total_submissions: 2450,
        text_submissions: 1680,
        audio_submissions: 770,
        validated_submissions: 2100,
        contributors: 125,
        total_hours: 45.7,
        quality_score: 92,
        recent_activity: [
          {
            id: '1',
            type: 'submission',
            user: 'adebayo_o',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            title: 'Traditional proverbs collection'
          },
          {
            id: '2',
            type: 'validation',
            user: 'fatima_k',
            timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            title: 'Validated audio pronunciation guide'
          },
          {
            id: '3',
            type: 'translation',
            user: 'kwame_a',
            timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
            title: 'News article translation'
          }
        ],
        top_contributors: [
          { username: 'adebayo_o', contributions: 145, points: 2890 },
          { username: 'fatima_k', contributions: 112, points: 2340 },
          { username: 'kwame_a', contributions: 98, points: 2100 }
        ]
      };

      // Create stats from API data
      const apiStats: LanguageStats = {
        total_submissions: languageData.total_contributions || 0,
        text_submissions: Math.floor((languageData.total_contributions || 0) * 0.7),
        audio_submissions: Math.floor((languageData.total_contributions || 0) * 0.3),
        validated_submissions: Math.floor((languageData.total_contributions || 0) * 0.85),
        contributors: languageData.active_contributors || 0,
        total_hours: Math.round((languageData.total_contributions || 0) * 0.02),
        quality_score: languageData.progress || 0,
        recent_activity: [
          {
            id: '1',
            type: 'submission',
            user: 'contributor',
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            title: `Recent ${languageData.name} submission`
          },
          {
            id: '2',
            type: 'validation',
            user: 'validator',
            timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            title: `Validated ${languageData.name} content`
          },
          {
            id: '3',
            type: 'contribution',
            user: 'expert',
            timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
            title: `Added ${languageData.name} cultural context`
          }
        ],
        top_contributors: [
          { username: 'contributor1', contributions: languageData.active_contributors || 5, points: (languageData.active_contributors || 5) * 20 },
          { username: 'contributor2', contributions: Math.floor((languageData.active_contributors || 5) * 0.8), points: Math.floor((languageData.active_contributors || 5) * 16) },
          { username: 'contributor3', contributions: Math.floor((languageData.active_contributors || 5) * 0.6), points: Math.floor((languageData.active_contributors || 5) * 12) }
        ]
      };

      setLanguage(apiLanguage);
      setStats(apiStats);

      // Fetch notebooks for this language
      try {
        const notebooksResponse = await fetch(`https://language-community-api.ailabsafrica.com/api/v1/languages/${languageCode}/notebooks`);
        if (notebooksResponse.ok) {
          const notebooksData = await notebooksResponse.json();
          setNotebooks(notebooksData);
        }
      } catch (notebookError) {
        console.error('Failed to load notebooks:', notebookError);
      }

    } catch (error) {
      console.error('Failed to load language data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDiscoveryData = async () => {
    if (!languageCode) return;

    try {
      setDiscoveryLoading(true);
      const API_BASE = 'https://language-community-api.ailabsafrica.com/api/v1';

      // Load language-specific resources in parallel
      const [modelsRes, datasetsRes, resourcesRes, trendingModelsRes, trendingDatasetsRes, trendingResourcesRes, taskDiscoveryRes] = await Promise.all([
        fetch(`${API_BASE}/discovery/languages/${languageCode}/models`).catch(() => null),
        fetch(`${API_BASE}/discovery/languages/${languageCode}/datasets`).catch(() => null),
        fetch(`${API_BASE}/discovery/languages/${languageCode}/resources`).catch(() => null),
        fetch(`${API_BASE}/discovery/trending/models?limit=6`).catch(() => null),
        fetch(`${API_BASE}/discovery/trending/datasets?limit=6`).catch(() => null),
        fetch(`${API_BASE}/discovery/trending/resources?limit=8`).catch(() => null),
        fetch(`${API_BASE}/discovery/tasks/speech_recognition?language=${languageCode}&limit=5`).catch(() => null)
      ]);

      // Process language-specific models
      if (modelsRes?.ok) {
        const data = await modelsRes.json();
        setLanguageModels(data.data || []);
      }

      // Process language-specific datasets
      if (datasetsRes?.ok) {
        const data = await datasetsRes.json();
        setLanguageDatasets(data.data || []);
      }

      // Process language-specific resources
      if (resourcesRes?.ok) {
        const data = await resourcesRes.json();
        setLanguageResources(data.data || []);
      }

      // Process trending models
      if (trendingModelsRes?.ok) {
        const data = await trendingModelsRes.json();
        setTrendingModels(data.data || []);
      }

      // Process trending datasets
      if (trendingDatasetsRes?.ok) {
        const data = await trendingDatasetsRes.json();
        setTrendingDatasets(data.data || []);
      }

      // Process trending resources
      if (trendingResourcesRes?.ok) {
        const data = await trendingResourcesRes.json();
        setTrendingResources(data || []);
      }

      // Process task-based discovery
      if (taskDiscoveryRes?.ok) {
        const data = await taskDiscoveryRes.json();
        setTaskDiscovery(data);
      }

    } catch (error) {
      console.error('Failed to load discovery data:', error);
    } finally {
      setDiscoveryLoading(false);
    }
  };

  const handleContribute = () => {
    navigate(`/submit?language=${languageCode}`);
  };

  const handleValidate = () => {
    navigate(`/validate?language=${languageCode}`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'thriving': return 'bg-green-100 text-green-800';
      case 'stable': return 'bg-blue-100 text-blue-800';
      case 'endangered': return 'bg-yellow-100 text-yellow-800';
      case 'severely_endangered': return 'bg-orange-100 text-orange-800';
      case 'critically_endangered': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const past = new Date(timestamp);
    const diffInHours = Math.floor((now.getTime() - past.getTime()) / (1000 * 60 * 60));

    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d ago`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!language) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Language Not Found</h1>
            <p className="text-muted-foreground mb-6">
              The language "{languageCode}" could not be found.
            </p>
            <Button onClick={() => navigate('/languages')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Languages
            </Button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/languages')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            <h1 className="text-3xl font-bold">{language.name}</h1>
            <p className="text-lg text-muted-foreground">{language.native_name}</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleContribute}>
              <FileText className="h-4 w-4 mr-2" />
              Contribute
            </Button>
            <Button variant="outline" onClick={handleValidate}>
              <Award className="h-4 w-4 mr-2" />
              Validate
            </Button>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-primary">{stats?.total_submissions || 0}</div>
              <div className="text-xs text-muted-foreground">Submissions</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-primary">{stats?.contributors || 0}</div>
              <div className="text-xs text-muted-foreground">Contributors</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-primary">{stats?.total_hours || 0}h</div>
              <div className="text-xs text-muted-foreground">Audio Hours</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-primary">{stats?.quality_score || 0}%</div>
              <div className="text-xs text-muted-foreground">Quality Score</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-2xl font-bold text-primary">{formatNumber(language.speakers)}</div>
              <div className="text-xs text-muted-foreground">Speakers</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <Badge className={`text-xs ${getStatusColor(language.status)}`}>
                {language.status.replace('_', ' ')}
              </Badge>
              <div className="text-xs text-muted-foreground mt-1">Status</div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="data">Data & Stats</TabsTrigger>
            <TabsTrigger value="community">Community</TabsTrigger>
            <TabsTrigger value="contributors">Contributors</TabsTrigger>
            <TabsTrigger value="resources">Resources</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>About {language.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-muted-foreground">{language.description}</p>
                    <div>
                      <h4 className="font-medium mb-2">Cultural Significance</h4>
                      <p className="text-sm text-muted-foreground">{language.cultural_significance}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Linguistic Features</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {language.linguistic_features.map((feature, index) => (
                        <Badge key={index} variant="secondary">{feature}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Globe className="h-4 w-4" />
                      Language Info
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <div className="text-sm font-medium">Family</div>
                      <div className="text-sm text-muted-foreground">{language.family}</div>
                    </div>
                    {language.subfamily && (
                      <div>
                        <div className="text-sm font-medium">Subfamily</div>
                        <div className="text-sm text-muted-foreground">{language.subfamily}</div>
                      </div>
                    )}
                    <div>
                      <div className="text-sm font-medium">ISO Codes</div>
                      <div className="text-sm text-muted-foreground">
                        {language.iso639_1 && `${language.iso639_1} • `}
                        {language.iso639_2} • {language.iso639_3}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium">Writing Systems</div>
                      <div className="text-sm text-muted-foreground">
                        {language.writing_systems.join(', ')}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      Geographic Distribution
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <div className="text-sm font-medium">Countries</div>
                      <div className="text-sm text-muted-foreground">
                        {language.countries.join(', ')}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium">Regions</div>
                      <div className="text-sm text-muted-foreground">
                        {language.regions.join(', ')}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="data" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Data Distribution</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Text Submissions</span>
                      <span>{stats?.text_submissions || 0}</span>
                    </div>
                    <Progress value={((stats?.text_submissions || 0) / (stats?.total_submissions || 1)) * 100} />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Audio Submissions</span>
                      <span>{stats?.audio_submissions || 0}</span>
                    </div>
                    <Progress value={((stats?.audio_submissions || 0) / (stats?.total_submissions || 1)) * 100} />
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Validated</span>
                      <span>{stats?.validated_submissions || 0}</span>
                    </div>
                    <Progress value={((stats?.validated_submissions || 0) / (stats?.total_submissions || 1)) * 100} />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {stats?.recent_activity.map((activity) => (
                      <div key={activity.id} className="flex items-center gap-3 p-2 rounded-lg bg-muted/30">
                        <div className="flex-shrink-0">
                          {activity.type === 'submission' && <FileText className="h-4 w-4" />}
                          {activity.type === 'validation' && <Award className="h-4 w-4" />}
                          {activity.type === 'translation' && <Globe className="h-4 w-4" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{activity.title}</p>
                          <p className="text-xs text-muted-foreground">
                            by {activity.user} • {formatTimeAgo(activity.timestamp)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="community" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Top Contributors</CardTitle>
                <CardDescription>
                  Most active contributors for {language.name}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats?.top_contributors.map((contributor, index) => (
                    <div key={contributor.username} className="flex items-center gap-4 p-3 rounded-lg bg-muted/30">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground text-sm font-bold">
                        #{index + 1}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{contributor.username}</p>
                        <p className="text-sm text-muted-foreground">
                          {contributor.contributions} contributions • {contributor.points} points
                        </p>
                      </div>
                      <Button size="sm" variant="outline">
                        View Profile
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="contributors" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Top Contributors for {language?.name}
                </CardTitle>
                <CardDescription>
                  Community members contributing to {language?.name} language data
                </CardDescription>
              </CardHeader>
              <CardContent>
                {contributorsLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                    <span className="ml-2">Loading contributors...</span>
                  </div>
                ) : contributors.length === 0 ? (
                  <div className="text-center py-12">
                    <Users className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium mb-2">No contributors yet</h3>
                    <p className="text-gray-600 mb-4">
                      Be the first to contribute to {language?.name}!
                    </p>
                    <Button onClick={() => navigate('/submit')}>
                      Start Contributing
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {contributors.map((contributor, index) => (
                      <div
                        key={contributor.user_id || index}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100 text-blue-600 font-bold">
                            #{index + 1}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">
                              {contributor.username || contributor.display_name || 'Anonymous'}
                            </p>
                            <p className="text-sm text-gray-600">
                              {contributor.total_contributions || 0} contributions
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="flex items-center gap-2">
                            <Award className="h-4 w-4 text-yellow-500" />
                            <span className="font-bold text-lg text-gray-900">
                              {contributor.total_points || 0}
                            </span>
                            <span className="text-sm text-gray-600">points</span>
                          </div>
                          {contributor.quality_rating && (
                            <p className="text-xs text-gray-500 mt-1">
                              Quality: {(contributor.quality_rating * 100).toFixed(0)}%
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {contributors.length > 0 && (
                  <div className="mt-6 text-center">
                    <p className="text-sm text-gray-600">
                      Showing top {contributors.length} contributors
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="resources" className="space-y-6">
            {/* Language-Specific Models */}
            {languageModels.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Play className="h-5 w-5 text-primary" />
                    {language?.name} Models
                  </CardTitle>
                  <CardDescription>
                    Pre-trained models specifically for {language?.name}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {languageModels.map((model) => (
                      <div key={model.model_uuid} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-sm">{model.name}</h3>
                          <Badge variant="outline" className="text-xs">
                            {model.model_type}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mb-3">
                          {model.architecture} • v{model.version}
                        </p>
                        <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                          <span>{model.download_count || 0} downloads</span>
                          <Badge className={model.deployment_status === 'production' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>
                            {model.deployment_status}
                          </Badge>
                        </div>
                        <Button variant="outline" size="sm" className="w-full">
                          <Download className="h-3 w-3 mr-2" />
                          Download
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Language-Specific Datasets */}
            {languageDatasets.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-primary" />
                    {language?.name} Datasets
                  </CardTitle>
                  <CardDescription>
                    Training datasets for {language?.name}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {languageDatasets.map((dataset) => (
                      <div key={dataset.dataset_uuid} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-sm">{dataset.name}</h3>
                          <Badge variant="outline" className="text-xs">
                            {dataset.source_type}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
                          {dataset.description}
                        </p>
                        <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                          <span>{dataset.total_size_gb?.toFixed(2) || 0} GB</span>
                          <span>{dataset.file_count || 0} files</span>
                        </div>
                        <Button variant="outline" size="sm" className="w-full">
                          <Download className="h-3 w-3 mr-2" />
                          Export
                        </Button>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Language-Specific Resources */}
            {languageResources.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BookOpen className="h-5 w-5 text-primary" />
                    {language?.name} Resources
                  </CardTitle>
                  <CardDescription>
                    External resources and links for {language?.name}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {languageResources.map((resource) => (
                      <a
                        key={resource.link_uuid}
                        href={resource.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-sm">{resource.title}</h3>
                          <ExternalLink className="h-3 w-3 text-muted-foreground" />
                        </div>
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline" className="text-xs">{resource.platform}</Badge>
                          <Badge variant="outline" className="text-xs">{resource.resource_type}</Badge>
                        </div>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>👁️ {resource.click_count || 0} views</span>
                          <span>👍 {resource.upvotes || 0} upvotes</span>
                        </div>
                      </a>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Trending Models */}
            {trendingModels.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    Trending Models
                  </CardTitle>
                  <CardDescription>
                    Most popular models across all African languages
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {trendingModels.map((model) => (
                      <div key={model.model_uuid} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-sm">{model.name}</h3>
                          <Badge variant="outline" className="text-xs">
                            {model.model_type}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2">
                          {model.languages?.slice(0, 3).join(', ')}
                        </p>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>🔥 {model.download_count || 0} downloads</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Trending Datasets */}
            {trendingDatasets.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    Trending Datasets
                  </CardTitle>
                  <CardDescription>
                    Most accessed datasets across the platform
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {trendingDatasets.map((dataset) => (
                      <div key={dataset.dataset_uuid} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-sm">{dataset.name}</h3>
                          <Badge variant="outline" className="text-xs">
                            {dataset.source_type}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                          {dataset.description}
                        </p>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>📊 {dataset.total_size_gb?.toFixed(1) || 0} GB</span>
                          <span>🔥 Trending</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Task-Based Discovery */}
            {taskDiscovery && taskDiscovery.models && taskDiscovery.models.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5 text-primary" />
                    Speech Recognition for {language?.name}
                  </CardTitle>
                  <CardDescription>
                    Models and datasets optimized for speech recognition tasks in {language?.name}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Task Models */}
                    {taskDiscovery.models.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold mb-2">Recommended Models</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                          {taskDiscovery.models.slice(0, 3).map((model: any) => (
                            <div key={model.model_uuid} className="p-3 border rounded-lg hover:shadow-md transition-shadow">
                              <div className="flex items-start justify-between mb-2">
                                <h5 className="font-semibold text-xs">{model.name}</h5>
                                <Badge variant="outline" className="text-xs">
                                  {model.model_type}
                                </Badge>
                              </div>
                              <p className="text-xs text-muted-foreground">
                                {model.architecture} • v{model.version}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Task Datasets */}
                    {taskDiscovery.datasets && taskDiscovery.datasets.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold mb-2">Training Datasets</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {taskDiscovery.datasets.slice(0, 2).map((dataset: any) => (
                            <div key={dataset.dataset_uuid} className="p-3 border rounded-lg hover:shadow-md transition-shadow">
                              <div className="flex items-start justify-between mb-2">
                                <h5 className="font-semibold text-xs">{dataset.name}</h5>
                                <Badge variant="outline" className="text-xs">
                                  {dataset.source_type}
                                </Badge>
                              </div>
                              <p className="text-xs text-muted-foreground">
                                {dataset.total_size_gb?.toFixed(1) || 0} GB • {dataset.file_count || 0} files
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Trending Resources */}
            {trendingResources.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <LinkIcon className="h-5 w-5 text-primary" />
                    Trending Resources
                  </CardTitle>
                  <CardDescription>
                    Most popular external resources across African languages
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {trendingResources.map((resource: any) => (
                      <a
                        key={resource.link_uuid}
                        href={resource.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-sm">{resource.title}</h3>
                          <ExternalLink className="h-3 w-3 text-muted-foreground flex-shrink-0 ml-2" />
                        </div>
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline" className="text-xs">{resource.platform}</Badge>
                          <Badge variant="outline" className="text-xs">{resource.resource_type}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2 line-clamp-1">
                          {resource.description || 'No description available'}
                        </p>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>👁️ {resource.click_count || 0} views</span>
                          <span className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3" />
                            {resource.upvotes || 0} upvotes
                          </span>
                        </div>
                      </a>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Show loading state */}
            {discoveryLoading && (
              <Card>
                <CardContent className="flex justify-center items-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </CardContent>
              </Card>
            )}

            {/* Show message if no discovery data */}
            {!discoveryLoading && languageModels.length === 0 && languageDatasets.length === 0 &&
             languageResources.length === 0 && trendingModels.length === 0 && trendingDatasets.length === 0 &&
             trendingResources.length === 0 && !taskDiscovery && (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-muted-foreground">No resources available yet for this language.</p>
                  <Button variant="outline" className="mt-4" onClick={handleContribute}>
                    Contribute Resources
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Notebooks Section */}
            {notebooks.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Training Notebooks & Data Sources</CardTitle>
                  <CardDescription>
                    Jupyter notebooks for data processing, model training, and analysis
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {notebooks.map((notebook, index) => (
                      <div key={notebook.id || index} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-sm">{notebook.name}</h3>
                          <Badge variant="outline" className="text-xs">
                            {notebook.type?.replace('_', ' ')}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
                          {notebook.description}
                        </p>
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <span>v{notebook.version}</span>
                          <span>{notebook.model_type}</span>
                        </div>
                        <div className="flex gap-2 mt-3">
                          <Button
                            variant="outline"
                            size="sm"
                            className="flex-1"
                            onClick={() => {
                              const filename = notebook.file_url.split('/').pop();
                              const downloadUrl = `https://language-community-api.ailabsafrica.com/api/v1/languages/notebooks/file/${languageCode}/${filename}`;
                              window.open(downloadUrl, '_blank');
                            }}
                          >
                            <FileText className="h-3 w-3 mr-2" />
                            Download
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </main>
      <Footer />
    </div>
  );
};

export default LanguageDetail;