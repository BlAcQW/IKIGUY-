import { useState } from "react";
import {
  Phone,
  PhoneCall,
  PhoneOff,
  Volume2,
  VolumeX,
  Settings,
  Clock,
  Users,
  CheckCircle,
  XCircle,
  Calendar,
  TrendingUp,
  Loader2,
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  useVoiceCalls,
  useCallStats,
  useVoiceConfig,
  useUpdateVoiceConfig,
  formatDuration,
  formatTimeAgo,
  getOutcomeLabel,
} from "@/lib/api/voice-api";

const capabilities = [
  "Answer property inquiries 24/7",
  "Schedule property tours automatically",
  "Provide listing details and pricing",
  "Collect buyer requirements",
  "Follow up with leads via callback",
  "Transfer to human agents when needed",
  "Support multiple languages",
  "Handle objections professionally",
];

export default function VoiceAgent() {
  const [isMuted, setIsMuted] = useState(false);

  const { data: callsData, isLoading: callsLoading } = useVoiceCalls({ limit: 10 });
  const { data: stats, isLoading: statsLoading } = useCallStats();
  const { data: config } = useVoiceConfig();
  const updateConfig = useUpdateVoiceConfig();

  const isActive = config?.is_active ?? false;

  const toggleActive = () => {
    updateConfig.mutate({ is_active: !isActive });
  };

  const recentCalls = callsData?.calls ?? [];

  const statCards = [
    { name: "Calls Today", value: statsLoading ? "..." : String(stats?.calls_today ?? 0), icon: Phone },
    { name: "Avg Duration", value: statsLoading ? "..." : formatDuration(stats?.avg_duration_seconds ?? 0), icon: Clock },
    { name: "Tours Scheduled", value: statsLoading ? "..." : String(stats?.tours_scheduled ?? 0), icon: Calendar },
    { name: "Success Rate", value: statsLoading ? "..." : `${stats?.satisfaction_rate ?? 0}%`, icon: TrendingUp },
  ];

  return (
    <div className="min-h-screen">
      <Header
        title="Voice AI Agent"
        subtitle="24/7 automated phone support for inquiries"
        actions={
          <Button variant="outline" className="gap-2">
            <Settings className="h-4 w-4" />
            Configure
          </Button>
        }
      />

      <div className="p-6 space-y-6">
        {/* Agent Status */}
        <Card className={`overflow-hidden ${isActive ? 'border-success/50' : 'border-destructive/50'}`}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className={`relative flex h-20 w-20 items-center justify-center rounded-full ${
                  isActive ? 'bg-success/10' : 'bg-destructive/10'
                }`}>
                  <Phone className={`h-10 w-10 ${isActive ? 'text-success' : 'text-destructive'}`} />
                  {isActive && (
                    <span className="absolute -top-1 -right-1 flex h-5 w-5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-5 w-5 bg-success"></span>
                    </span>
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-3">
                    <h3 className="text-2xl font-bold text-foreground">Voice Agent</h3>
                    <Badge variant={isActive ? "success" : "destructive"}>
                      {isActive ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <p className="text-muted-foreground mt-1">
                    {isActive
                      ? "Ready to handle incoming calls and schedule tours"
                      : "Agent is currently offline. Enable to start receiving calls."
                    }
                  </p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Phone: <span className="font-mono text-foreground">{config?.phone_number || "+1 (800) 555-PROP"}</span>
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="icon-lg"
                  onClick={() => setIsMuted(!isMuted)}
                >
                  {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                </Button>
                <Button
                  variant={isActive ? "destructive" : "success"}
                  size="lg"
                  className="gap-2"
                  onClick={toggleActive}
                  disabled={updateConfig.isPending}
                >
                  {updateConfig.isPending ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : isActive ? (
                    <>
                      <PhoneOff className="h-5 w-5" />
                      Deactivate
                    </>
                  ) : (
                    <>
                      <PhoneCall className="h-5 w-5" />
                      Activate
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {statCards.map((stat) => (
            <Card key={stat.name}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <stat.icon className="h-8 w-8 text-accent" />
                </div>
                <p className="text-2xl font-bold text-foreground mt-4">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.name}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Calls */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Recent Calls</CardTitle>
                <CardDescription>Latest interactions handled by the AI agent</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {callsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : recentCalls.length > 0 ? (
                  recentCalls.map((call) => (
                    <div
                      key={call.id}
                      className="flex items-center gap-4 p-4 rounded-xl bg-secondary/50 hover:bg-secondary transition-colors"
                    >
                      <div className={`flex h-12 w-12 items-center justify-center rounded-full ${
                        call.status === "completed" ? "bg-success/10" :
                        call.outcome === "transferred" ? "bg-info/10" :
                        "bg-destructive/10"
                      }`}>
                        {call.status === "completed" ? (
                          <CheckCircle className="h-6 w-6 text-success" />
                        ) : call.outcome === "transferred" ? (
                          <Users className="h-6 w-6 text-info" />
                        ) : (
                          <XCircle className="h-6 w-6 text-destructive" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-foreground">{call.caller_name}</p>
                          <span className="text-sm text-muted-foreground">{call.caller_phone}</span>
                        </div>
                        <p className="text-sm text-muted-foreground truncate">
                          {call.property_name ? `Property: ${call.property_name}` : "No property selected"}
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge variant={
                          call.status === "completed" ? "success" :
                          call.outcome === "transferred" ? "info" :
                          "destructive"
                        }>
                          {getOutcomeLabel(call.outcome)}
                        </Badge>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatDuration(call.duration_seconds)} - {formatTimeAgo(call.created_at)}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Phone className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No calls recorded yet</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Capabilities */}
          <Card>
            <CardHeader>
              <CardTitle>AI Capabilities</CardTitle>
              <CardDescription>What the voice agent can do</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {capabilities.map((cap, index) => (
                <div
                  key={index}
                  className="flex items-center gap-3 p-2"
                >
                  <CheckCircle className="h-4 w-4 text-success flex-shrink-0" />
                  <span className="text-sm text-foreground">{cap}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
