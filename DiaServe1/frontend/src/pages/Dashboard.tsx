import {
  Building2,
  Users,
  Calendar,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Plus,
  Sparkles,
  MessageSquare,
  Phone,
  Mail,
  Banknote,
  DollarSign,
  Loader2
} from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { updateExchangeRate } from "@/lib/api/currency-api";
import { useToast } from "@/components/ui/use-toast";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { usePropertyStats, useProperties } from "@/hooks/use-properties";
import { useAuth } from "@/contexts/AuthContext";
import { useCallStats } from "@/lib/api/voice-api";
import { useAIStats } from "@/lib/api/ai-tools-api";
import { useBookings } from "@/hooks/use-bookings";
import { AddPropertyDialog } from "@/components/AddPropertyDialog";
import { ContactFormDialog, type ContactFormData } from "@/components/ContactFormDialog";
import { CampaignWizard } from "@/components/CampaignWizard";
import { AdminBookingDialog } from "@/components/admin/AdminBookingDialog";
import { useCreateContact } from "@/hooks/use-campaigns";

export default function Dashboard() {
  const { user } = useAuth();

  // Fetch real data
  const { data: statsData, isLoading: statsLoading } = usePropertyStats();
  const { data: propertiesData, isLoading: propertiesLoading } = useProperties({ limit: 3, sort_by: 'created_at', sort_order: 'desc' });
  const { data: allPropertiesData } = useProperties({ limit: 100 });
  const { data: callStatsData } = useCallStats();
  const { data: aiStatsData } = useAIStats();
  const { data: bookingsData } = useBookings({ limit: 5 });

  // Format currency
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Build stats array from real data
  const stats = statsData ? [
    {
      name: "Total Properties",
      value: statsData.total.toString(),
      icon: Building2,
      trend: "up" as const,
      change: `${statsData.active} available`,
    },
    {
      name: "Total Rental Value",
      value: formatCurrency(statsData.total_value),
      icon: Banknote,
      trend: "up" as const,
      change: "Monthly",
    },
    {
      name: "Avg Rent",
      value: formatCurrency(statsData.average_price),
      icon: Calendar,
      trend: "up" as const,
      change: "Monthly",
    },
  ] : [];

  // Get recent properties from real data
  const recentProperties = propertiesData?.properties || [];

  // Get time of day for greeting
  const getTimeOfDay = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "morning";
    if (hour < 18) return "afternoon";
    return "evening";
  };

  const timeOfDay = getTimeOfDay();
  const userName = user?.first_name || "there";

  // Build AI features from real stats
  const aiFeatures = [
    {
      name: "Voice Agent",
      icon: Phone,
      calls: callStatsData ? `${callStatsData.calls_today} calls today` : "Loading...",
    },
    {
      name: "Chat Assistant",
      icon: MessageSquare,
      calls: aiStatsData ? `${aiStatsData.generations_today} generations today` : "Loading...",
    },
    {
      name: "Smart Search",
      icon: Sparkles,
      calls: aiStatsData ? `${aiStatsData.total_generations} total` : "Loading...",
    },
  ];

  // Build upcoming tasks from real bookings
  const upcomingTasks = (bookingsData?.bookings || [])
    .filter(b => b.status !== 'cancelled' && b.status !== 'completed' && b.status !== 'no_show')
    .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())
    .slice(0, 4)
    .map(b => ({
      id: b.id,
      title: `${b.booking_type === 'tour' ? 'Property tour' : b.booking_type} - ${b.contact_name || 'Guest'}`,
      time: new Date(b.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      type: b.booking_type || 'tour',
    }));

  const { toast } = useToast();
  const [isRateDialogOpen, setIsRateDialogOpen] = useState(false);
  const [newRate, setNewRate] = useState("12.5"); // Default
  const [isUpdatingRate, setIsUpdatingRate] = useState(false);

  const navigate = useNavigate();
  const [showAddPropertyDialog, setShowAddPropertyDialog] = useState(false);
  const [showContactDialog, setShowContactDialog] = useState(false);
  const [showCampaignWizard, setShowCampaignWizard] = useState(false);
  const [showBookingDialog, setShowBookingDialog] = useState(false);
  const createContactMutation = useCreateContact();

  const handleUpdateRate = async () => {
    try {
      setIsUpdatingRate(true);
      await updateExchangeRate("GHS", parseFloat(newRate));
      toast({
        title: "Exchange Rate Updated",
        description: `USD to GHS rate set to ${newRate}`,
      });
      setIsRateDialogOpen(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update exchange rate",
        variant: "destructive",
      });
    } finally {
      setIsUpdatingRate(false);
    }
  };

  const handleCreateContact = async (data: ContactFormData) => {
    await createContactMutation.mutateAsync({
      name: `${data.first_name} ${data.last_name}`.trim(),
      email: data.email,
      phone: data.phone,
      tags: data.tags,
      source: data.source,
      notes: data.notes,
      interest_status: data.interest_level as "hot" | "warm" | "cold",
      property_type_preferences: data.property_type_preferences,
      location_preferences: data.location_preferences,
      budget_min: data.budget_min,
      budget_max: data.budget_max,
    });
  };

  return (
    <div className="min-h-screen">
      <div className="p-4 md:p-6 space-y-6">
        {/* Hero Header with Gradient */}
        <div className="bg-gradient-to-r from-primary via-primary/90 to-secondary rounded-2xl p-6 md:p-8 text-white shadow-premium animate-slide-up-fade">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold mb-2">
                Good {timeOfDay}, {userName}! 👋
              </h1>
              <p className="text-white/90 text-sm md:text-base">
                Here's what's happening with your real estate portfolio
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="glass"
                size="lg"
                className="gap-2 text-white"
                onClick={() => setIsRateDialogOpen(true)}
              >
                <DollarSign className="h-5 w-5" />
                Set Dollar Rate
              </Button>
              <Button variant="glass" size="lg" className="gap-2 text-white" onClick={() => setShowAddPropertyDialog(true)}>
                <Plus className="h-5 w-5" />
                Add Property
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Grid with Enhanced Cards */}
        {statsLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i} variant="elevated" className="overflow-hidden animate-scale-in">
                <CardContent className="p-6">
                  <div className="flex items-center justify-center h-24">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            {stats.map((stat, index) => (
              <Card
                key={stat.name}
                variant="elevated"
                className="group overflow-hidden animate-scale-in hover:border-primary/30"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 group-hover:from-primary/30 group-hover:to-secondary/30 transition-all duration-200 shadow-inner-soft">
                      <stat.icon className="h-6 w-6 text-primary" />
                    </div>
                    <Badge
                      variant={stat.trend === "up" ? "soft-success" : "soft-destructive"}
                      className="gap-1"
                    >
                      {stat.trend === "up" ? (
                        <ArrowUpRight className="h-3 w-3" />
                      ) : (
                        <ArrowDownRight className="h-3 w-3" />
                      )}
                      {stat.change}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-2xl md:text-3xl font-bold text-foreground mb-1">
                      {stat.value}
                    </p>
                    <p className="text-sm text-muted-foreground">{stat.name}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Properties */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Recent Properties</CardTitle>
                  <CardDescription>Your latest property listings</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={() => navigate("/my-properties")}>View All</Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {propertiesLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : recentProperties.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No properties found. Add your first property to get started!
                  </div>
                ) : (
                  recentProperties.map((property) => (
                    <div
                      key={property.id}
                      className="flex items-center gap-4 p-3 rounded-xl bg-secondary/50 hover:bg-secondary transition-colors cursor-pointer"
                    >
                      <img
                        src={property.images?.[0] || "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=400&h=300&fit=crop"}
                        alt={property.name}
                        className="h-16 w-24 rounded-lg object-cover"
                      />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-foreground truncate">{property.name}</h4>
                        <p className="text-sm text-muted-foreground truncate">
                          {property.location.address}, {property.location.city}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-foreground">
                          {formatCurrency(property.financial.price_usd)}
                        </p>
                        <p className="text-sm text-muted-foreground capitalize">
                          {property.property_type}
                        </p>
                      </div>
                      <Badge variant={property.status === "active" ? "success" : property.status === "pending" ? "warning" : "muted"}>
                        {property.status === "active" ? "Available" : property.status}
                      </Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* AI Features Status */}
          <div>
            <Card variant="premium">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-accent/20 to-warning/20">
                    <Sparkles className="h-5 w-5 text-accent" />
                  </div>
                  AI Tools Status
                </CardTitle>
                <CardDescription>Real-time AI agent performance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {aiFeatures.map((feature, index) => (
                  <div
                    key={feature.name}
                    className="flex items-center gap-3 p-4 rounded-xl bg-gradient-to-r from-muted/50 to-transparent border border-border/50 hover:border-accent/30 transition-all duration-200 group"
                  >
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-accent/20 to-warning/20 group-hover:from-accent/30 group-hover:to-warning/30 transition-all duration-200 shadow-sm">
                      <feature.icon className="h-6 w-6 text-accent" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-foreground">{feature.name}</h4>
                        <span className="flex h-2 w-2 rounded-full bg-success animate-pulse shadow-glow" />
                      </div>
                      <p className="text-xs text-muted-foreground font-medium">
                        {feature.calls}
                      </p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upcoming Tasks */}
          <Card>
            <CardHeader>
              <CardTitle>Today's Schedule</CardTitle>
              <CardDescription>Your upcoming tasks and appointments</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {upcomingTasks.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No upcoming bookings. Schedule a property tour to get started!
                </div>
              ) : (
                upcomingTasks.map((task) => (
                  <div
                    key={task.id}
                    className="flex items-center gap-4 p-3 rounded-xl border border-border hover:bg-secondary/50 transition-colors"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-sm font-medium text-primary">
                      {task.time.split(' ')[0]}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-foreground">{task.title}</p>
                      <p className="text-sm text-muted-foreground">{task.time}</p>
                    </div>
                    <Badge variant="muted">{task.type}</Badge>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card className="overflow-hidden relative">
            <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary/90 to-secondary opacity-100" />
            <div className="relative">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-white/20 backdrop-blur-sm">
                    <Sparkles className="h-5 w-5" />
                  </div>
                  Quick Actions
                </CardTitle>
                <CardDescription className="text-white/80">Common tasks at your fingertips</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Button variant="glass" className="h-auto flex-col gap-3 py-6 text-white hover:bg-white/30 group" onClick={() => setShowAddPropertyDialog(true)}>
                  <Building2 className="h-7 w-7 group-hover:scale-110 transition-transform" />
                  <span className="font-semibold">Add Property</span>
                </Button>
                <Button variant="glass" className="h-auto flex-col gap-3 py-6 text-white hover:bg-white/30 group" onClick={() => setShowContactDialog(true)}>
                  <Users className="h-7 w-7 group-hover:scale-110 transition-transform" />
                  <span className="font-semibold">New Contact</span>
                </Button>
                <Button variant="glass" className="h-auto flex-col gap-3 py-6 text-white hover:bg-white/30 group" onClick={() => setShowCampaignWizard(true)}>
                  <Mail className="h-7 w-7 group-hover:scale-110 transition-transform" />
                  <span className="font-semibold">Send Campaign</span>
                </Button>
                <Button variant="glass" className="h-auto flex-col gap-3 py-6 text-white hover:bg-white/30 group" onClick={() => setShowBookingDialog(true)}>
                  <Calendar className="h-7 w-7 group-hover:scale-110 transition-transform" />
                  <span className="font-semibold">Schedule Tour</span>
                </Button>
              </CardContent>
            </div>
          </Card>
        </div>
        {/* Rate Dialog */}
        <Dialog open={isRateDialogOpen} onOpenChange={setIsRateDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Set Exchange Rate</DialogTitle>
              <DialogDescription>
                Update the USD to GHS exchange rate. This will affect all property listings.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="rate" className="text-right">
                  Rate (GHS)
                </Label>
                <Input
                  id="rate"
                  value={newRate}
                  onChange={(e) => setNewRate(e.target.value)}
                  className="col-span-3"
                  type="number"
                  step="0.01"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsRateDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleUpdateRate} disabled={isUpdatingRate}>
                {isUpdatingRate ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Updating...
                  </>
                ) : (
                  "Save Changes"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <AddPropertyDialog
          open={showAddPropertyDialog}
          onOpenChange={setShowAddPropertyDialog}
        />

        <ContactFormDialog
          open={showContactDialog}
          onClose={() => setShowContactDialog(false)}
          onSubmit={handleCreateContact}
        />

        <CampaignWizard
          open={showCampaignWizard}
          onClose={() => setShowCampaignWizard(false)}
        />

        <AdminBookingDialog
          open={showBookingDialog}
          onOpenChange={setShowBookingDialog}
          properties={(allPropertiesData?.properties || []).map(p => ({ id: p.id, name: p.name }))}
        />
      </div>
    </div>
  );
}
