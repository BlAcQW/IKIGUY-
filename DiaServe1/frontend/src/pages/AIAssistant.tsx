import { useState } from "react";
import {
  Sparkles,
  FileText,
  PenTool,
  Share2,
  FileCheck,
  MessageSquare,
  Zap,
  Loader2,
  Copy,
  Check,
  BarChart3,
  Clock,
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Link } from "react-router-dom";
import {
  useGenerateListing,
  useGenerateSocialPost,
  useGenerateEmail,
  useAnalyzeContract,
  useGenerations,
  useAIStats,
  type GenerationResponse,
  type GenerationType,
} from "@/lib/api/ai-tools-api";

const generationTypeLabels: Record<GenerationType, string> = {
  listing: "Listing",
  social_media: "Social Media",
  email: "Email",
  contract_analysis: "Contract Analysis",
};

const generationTypeColors: Record<GenerationType, string> = {
  listing: "text-accent",
  social_media: "text-pink-500",
  email: "text-blue-500",
  contract_analysis: "text-amber-500",
};

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
}

function GenerationForm({
  title,
  description,
  icon: Icon,
  iconColor,
  iconBg,
  placeholder,
  mutation,
  generationType,
}: {
  title: string;
  description: string;
  icon: React.ElementType;
  iconColor: string;
  iconBg: string;
  placeholder: string;
  mutation: ReturnType<typeof useGenerateListing>;
  generationType: GenerationType;
}) {
  const [prompt, setPrompt] = useState("");
  const [propertyId, setPropertyId] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const latestResult = mutation.data as GenerationResponse | undefined;

  const handleSubmit = () => {
    if (!prompt.trim()) return;
    mutation.mutate({
      generation_type: generationType,
      prompt: prompt.trim(),
      property_id: propertyId.trim() || undefined,
    });
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${iconBg}`}>
          <Icon className={`h-5 w-5 ${iconColor}`} />
        </div>
        <div>
          <h3 className="font-semibold text-foreground">{title}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>

      <Textarea
        placeholder={placeholder}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        className="min-h-[120px] resize-y"
      />

      {(generationType === "listing" || generationType === "social_media") && (
        <input
          type="text"
          placeholder="Property ID (optional)"
          value={propertyId}
          onChange={(e) => setPropertyId(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      )}

      <Button
        onClick={handleSubmit}
        disabled={!prompt.trim() || mutation.isPending}
        className="w-full"
      >
        {mutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4 mr-2" />
            Generate
          </>
        )}
      </Button>

      {latestResult && (
        <Card className="border-accent/20 bg-accent/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <Badge variant="outline" className="text-xs">
                {latestResult.model_used}
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleCopy(latestResult.result, latestResult.id)}
              >
                {copiedId === latestResult.id ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
            <pre className="whitespace-pre-wrap text-sm font-sans text-foreground bg-transparent p-0 m-0">
              {latestResult.result}
            </pre>
            {latestResult.tokens_used != null && latestResult.tokens_used > 0 && (
              <p className="text-xs text-muted-foreground mt-2">
                Tokens used: {latestResult.tokens_used}
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function AIAssistant() {
  const listingMutation = useGenerateListing();
  const socialMutation = useGenerateSocialPost();
  const emailMutation = useGenerateEmail();
  const contractMutation = useAnalyzeContract();
  const { data: generationsData, isLoading: generationsLoading } = useGenerations({ limit: 10 });
  const { data: stats, isLoading: statsLoading } = useAIStats();

  return (
    <div className="min-h-screen">
      <Header
        title="AI Assistant"
        subtitle="Powerful AI tools for property management"
        showSearch={false}
      />

      <div className="p-6 space-y-6">
        {/* Hero Section */}
        <Card className="gradient-primary text-white overflow-hidden relative">
          <div className="absolute inset-0 opacity-50" style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='30' height='30' viewBox='0 0 30 30' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='1.5' cy='1.5' r='1.5' fill='rgba(255,255,255,0.07)'/%3E%3C/svg%3E\")" }} />
          <CardContent className="p-8 relative">
            <div className="flex items-center gap-6">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10 backdrop-blur-sm">
                <Sparkles className="h-8 w-8" />
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-bold">AI-Powered Property Management</h2>
                <p className="text-white/80 mt-1 max-w-xl">
                  Save hours every week with intelligent automation. Generate content,
                  manage documents, and streamline operations with AI.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link to="/ai-chat">
                  <Button variant="glass" size="lg" className="gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Open AI Chat
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
                <BarChart3 className="h-5 w-5 text-accent" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">
                  {statsLoading ? "..." : stats?.total_generations ?? 0}
                </p>
                <p className="text-xs text-muted-foreground">Total Generations</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                <Clock className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">
                  {statsLoading ? "..." : stats?.generations_today ?? 0}
                </p>
                <p className="text-xs text-muted-foreground">Today</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10">
                <Zap className="h-5 w-5 text-emerald-500" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">
                  {statsLoading ? "..." : (stats?.tokens_used_total ?? 0).toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground">Tokens Used</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10">
                <Sparkles className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground capitalize">
                  {statsLoading ? "..." : stats?.most_used_type?.replace("_", " ") ?? "N/A"}
                </p>
                <p className="text-xs text-muted-foreground">Most Used Tool</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* AI Tools Tabs */}
        <Tabs defaultValue="listing" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="listing" className="gap-2">
              <PenTool className="h-4 w-4" />
              <span className="hidden sm:inline">Listing</span>
            </TabsTrigger>
            <TabsTrigger value="social" className="gap-2">
              <Share2 className="h-4 w-4" />
              <span className="hidden sm:inline">Social</span>
            </TabsTrigger>
            <TabsTrigger value="email" className="gap-2">
              <FileText className="h-4 w-4" />
              <span className="hidden sm:inline">Email</span>
            </TabsTrigger>
            <TabsTrigger value="contract" className="gap-2">
              <FileCheck className="h-4 w-4" />
              <span className="hidden sm:inline">Contract</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="listing">
            <Card>
              <CardContent className="p-6">
                <GenerationForm
                  title="AI Listing Enhancer"
                  description="Generate high-performing property descriptions, titles, and marketing copy."
                  icon={PenTool}
                  iconColor="text-accent"
                  iconBg="bg-accent/10"
                  placeholder="Describe the property you want to create a listing for. E.g., 'Write a compelling listing for a 3-bedroom luxury apartment in downtown Accra with city views.'"
                  mutation={listingMutation}
                  generationType="listing"
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="social">
            <Card>
              <CardContent className="p-6">
                <GenerationForm
                  title="Social Content Generator"
                  description="Create engaging social media posts and ad campaigns for your listings."
                  icon={Share2}
                  iconColor="text-pink-500"
                  iconBg="bg-pink-500/10"
                  placeholder="Describe the social media content you need. E.g., 'Create an Instagram post for a newly listed waterfront villa with 5 bedrooms and infinity pool.'"
                  mutation={socialMutation}
                  generationType="social_media"
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="email">
            <Card>
              <CardContent className="p-6">
                <GenerationForm
                  title="Email Campaign Generator"
                  description="Generate professional email campaigns for property marketing."
                  icon={FileText}
                  iconColor="text-blue-500"
                  iconBg="bg-blue-500/10"
                  placeholder="Describe the email you want to generate. E.g., 'Write a marketing email for our new luxury condo development launching next month.'"
                  mutation={emailMutation}
                  generationType="email"
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="contract">
            <Card>
              <CardContent className="p-6">
                <GenerationForm
                  title="Contract Analyzer"
                  description="AI-powered contract review and risk identification."
                  icon={FileCheck}
                  iconColor="text-amber-500"
                  iconBg="bg-amber-500/10"
                  placeholder="Paste contract text or describe what you need analyzed. E.g., 'Analyze this lease clause: The tenant shall be responsible for all maintenance costs exceeding $500 per incident...'"
                  mutation={contractMutation}
                  generationType="contract_analysis"
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Generation History */}
        <Card>
          <CardHeader>
            <CardTitle>Recent AI Activity</CardTitle>
            <CardDescription>Latest content generated by AI tools</CardDescription>
          </CardHeader>
          <CardContent>
            {generationsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : generationsData && generationsData.generations.length > 0 ? (
              <div className="space-y-4">
                {generationsData.generations.map((gen) => (
                  <div
                    key={gen.id}
                    className="flex items-center gap-4 p-3 rounded-xl bg-secondary/50"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/10">
                      <Sparkles className={`h-5 w-5 ${generationTypeColors[gen.generation_type] || "text-accent"}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">
                        {gen.prompt.length > 80 ? gen.prompt.slice(0, 80) + "..." : gen.prompt}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatTimeAgo(gen.created_at)}
                      </p>
                    </div>
                    <Badge variant="muted">
                      {generationTypeLabels[gen.generation_type] || gen.generation_type}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No generations yet. Try one of the AI tools above!</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
