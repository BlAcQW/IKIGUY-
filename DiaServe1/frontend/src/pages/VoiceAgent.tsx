import { useState } from "react";
import { 
  Phone, 
  PhoneCall, 
  PhoneOff, 
  Mic, 
  MicOff, 
  Volume2, 
  VolumeX,
  Settings,
  BarChart3,
  Clock,
  Users,
  CheckCircle,
  XCircle,
  Calendar,
  TrendingUp
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const recentCalls = [
  {
    id: 1,
    caller: "Sarah Mitchell",
    phone: "+1 (555) 123-4567",
    duration: "4:32",
    outcome: "Tour Scheduled",
    property: "Luxury Penthouse Suite",
    time: "10 min ago",
    status: "success",
  },
  {
    id: 2,
    caller: "Mike Johnson",
    phone: "+1 (555) 234-5678",
    duration: "2:15",
    outcome: "Information Provided",
    property: "Modern Beach Villa",
    time: "25 min ago",
    status: "success",
  },
  {
    id: 3,
    caller: "Emily Chen",
    phone: "+1 (555) 345-6789",
    duration: "1:45",
    outcome: "Transferred to Agent",
    property: "Downtown Loft",
    time: "1 hour ago",
    status: "transferred",
  },
  {
    id: 4,
    caller: "Unknown",
    phone: "+1 (555) 456-7890",
    duration: "0:30",
    outcome: "Missed Call",
    property: null,
    time: "2 hours ago",
    status: "missed",
  },
];

const stats = [
  { name: "Calls Today", value: "127", icon: Phone, change: "+15%" },
  { name: "Avg Duration", value: "3:24", icon: Clock, change: "+8%" },
  { name: "Tours Scheduled", value: "34", icon: Calendar, change: "+23%" },
  { name: "Satisfaction", value: "94%", icon: TrendingUp, change: "+2%" },
];

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
  const [isActive, setIsActive] = useState(true);
  const [isMuted, setIsMuted] = useState(false);

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
                    Phone: <span className="font-mono text-foreground">+1 (800) 555-PROP</span>
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
                  onClick={() => setIsActive(!isActive)}
                >
                  {isActive ? (
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
          {stats.map((stat) => (
            <Card key={stat.name}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <stat.icon className="h-8 w-8 text-accent" />
                  <Badge variant="success">{stat.change}</Badge>
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
                {recentCalls.map((call) => (
                  <div
                    key={call.id}
                    className="flex items-center gap-4 p-4 rounded-xl bg-secondary/50 hover:bg-secondary transition-colors"
                  >
                    <div className={`flex h-12 w-12 items-center justify-center rounded-full ${
                      call.status === "success" ? "bg-success/10" :
                      call.status === "transferred" ? "bg-info/10" :
                      "bg-destructive/10"
                    }`}>
                      {call.status === "success" ? (
                        <CheckCircle className="h-6 w-6 text-success" />
                      ) : call.status === "transferred" ? (
                        <Users className="h-6 w-6 text-info" />
                      ) : (
                        <XCircle className="h-6 w-6 text-destructive" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-foreground">{call.caller}</p>
                        <span className="text-sm text-muted-foreground">{call.phone}</span>
                      </div>
                      <p className="text-sm text-muted-foreground truncate">
                        {call.property ? `Property: ${call.property}` : "No property selected"}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge variant={
                        call.status === "success" ? "success" :
                        call.status === "transferred" ? "info" :
                        "destructive"
                      }>
                        {call.outcome}
                      </Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        {call.duration} • {call.time}
                      </p>
                    </div>
                  </div>
                ))}
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
