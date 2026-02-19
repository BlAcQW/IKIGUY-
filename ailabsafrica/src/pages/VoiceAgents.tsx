import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, } from "@/components/ui/alert-dialog";
import { useToast } from "@/components/ui/use-toast";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Eye, Edit, Play, Pause, Trash2, Copy, Wallet, CheckCircle, RefreshCw, Plus, Download, Search, Filter } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import CloneAssistantDialog from "@/components/CloneAssistantDialog";
import DataChecker from "@/components/debug/DataChecker";
import AssistantManager from "@/components/assistant/AssistantManager";
import ImportAssistant from "@/components/dashboard/ImportAssistant";

interface DemoRow {
  id: string;
  assistant_name: string;
  assistant_type: string;
  description?: string;
  demo_url: string;
  created_at: string;
  status: string;
  assistant_id: string;
  voice_id?: string;
  external?: boolean;
  custom_url?: string;
}

interface VoiceOption { id: string; name: string }

const VoiceAgents = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchParams] = useSearchParams();

  const [demos, setDemos] = useState<DemoRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Edit state
  const [editOpen, setEditOpen] = useState(false);
  const [current, setCurrent] = useState<DemoRow | null>(null);
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [voiceId, setVoiceId] = useState("");
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [deleting, setDeleting] = useState<DemoRow | null>(null);
  
  // Clone state
  const [cloneOpen, setCloneOpen] = useState(false);
  const [cloning, setCloning] = useState<DemoRow | null>(null);
  
  // Import state
  const [showImportDialog, setShowImportDialog] = useState(false);
  
  // Search and filter state
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState<string>("all");

  useEffect(() => {
    document.title = "Voice Agents & Demos | AI Labs Africa";
  }, []);

  useEffect(() => {
    if (!loading && !user) navigate("/auth");
  }, [user, loading, navigate]);

  const load = async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      console.log("Loading voice agents for user:", user.id);
      const { data, error } = await supabase
        .from("custom_demos")
        .select("*")
        .eq("user_id", user.id)
        .or("status.is.null,status.neq.deleted")
        .order("created_at", { ascending: false });

      if (error) {
        console.error("Database error:", error);
        // If unauthorized, redirect to auth
        if (error.message?.includes("Unauthorized") || error.message?.includes("session_not_found")) {
          toast({ title: "Session expired", description: "Please sign in again", variant: "destructive" });
          navigate("/auth");
          return;
        }
        throw error;
      }
      console.log("Loaded demos:", data);
      console.log("Number of demos loaded:", data?.length || 0);
      console.log("Demo details:", data?.map(d => ({ 
        id: d.id, 
        name: d.assistant_name, 
        type: d.assistant_type, 
        external: d.external,
        user_id: d.user_id 
      })));
      setDemos(data || []);
    } catch (e: any) {
      console.error("Error loading demos:", e);
      toast({ title: "Failed to load", description: e.message, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, [user]);

  // Filter demos based on search term and type
  const filteredDemos = useMemo(() => {
    return demos.filter(demo => {
      const matchesSearch = demo.assistant_name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = filterType === "all" || demo.assistant_type === filterType;
      return matchesSearch && matchesType;
    });
  }, [demos, searchTerm, filterType]);

  // Get unique assistant types for filter dropdown
  const assistantTypes = useMemo(() => {
    const types = demos.map(demo => demo.assistant_type).filter(Boolean);
    return ["all", ...Array.from(new Set(types))];
  }, [demos]);

  const openEdit = async (row: DemoRow) => {
    setCurrent(row);
    setName(row.assistant_name);
    setPrompt("");
    setVoiceId(row.voice_id || "");
    setEditOpen(true);
    try {
      const [voicesRes, detailsRes] = await Promise.all([
        supabase.functions.invoke("list-vapi-voices"),
        supabase.functions.invoke("manage-assistant", { body: { action: "get", assistantId: row.assistant_id } })
      ]);
      const v = (voicesRes.data?.voices as VoiceOption[]) || [];
      setVoices(v);
      if (!voiceId && v.length) setVoiceId(v[0].id);
      const sysPrompt = detailsRes.data?.assistant?.systemPrompt as string | undefined;
      if (sysPrompt) setPrompt(sysPrompt);
    } catch (e: any) {
      console.warn("Edit preload failed", e);
    }
  };

  const saveEdit = async () => {
    if (!current) return;
    try {
      const { error } = await supabase.functions.invoke("manage-assistant", {
        body: { action: "update", assistantId: current.assistant_id, name, prompt, voiceId }
      });
      if (error) throw error;
      toast({ title: "Assistant updated" });
      setEditOpen(false);
      await load();
    } catch (e: any) {
      toast({ title: "Update failed", description: e.message, variant: "destructive" });
    }
  };

  const toggleStatus = async (row: DemoRow) => {
    const next = row.status === "paused" ? "active" : "paused";
    try {
      const { error } = await supabase.functions.invoke("manage-assistant", {
        body: { action: "status", assistantId: row.assistant_id, status: next }
      });
      if (error) throw error;
      toast({ title: next === "paused" ? "Assistant paused" : "Assistant resumed" });
      await load();
    } catch (e: any) {
      toast({ title: "Failed", description: e.message, variant: "destructive" });
    }
  };

  const confirmDelete = (row: DemoRow) => setDeleting(row);
  const doDelete = async () => {
    if (!deleting) return;
    try {
      const { error } = await supabase.functions.invoke("manage-assistant", {
        body: { action: "delete", assistantId: deleting.assistant_id }
      });
      if (error) throw error;
      toast({ title: "Assistant deleted" });
      setDeleting(null);
      await load();
    } catch (e: any) {
      toast({ title: "Delete failed", description: e.message, variant: "destructive" });
    }
  };

  const openClone = (row: DemoRow) => {
    setCloning(row);
    setCloneOpen(true);
  };

  useEffect(() => {
    const success = searchParams.get("success");
    const newDemo = searchParams.get("newDemo");
    if (success === "true" && newDemo) {
      toast({
        title: "Demo created successfully!",
        description: "Your new demo has been created and opened in a new tab for testing!",
      });
      // Clear the URL parameters
      navigate("/voice-agents", { replace: true });
      load(); // Reload to show the new demo in the list
    }
  }, [searchParams, toast, navigate, load]);

  return (
    <div>
      <div>
        {/* Page Title - Separate row above buttons, right-aligned */}
        <div className="flex justify-end mb-4">
          <div className="text-right">
            <h1 className="text-xl font-semibold">Voice Agents & Demos</h1>
            <p className="text-xs text-muted-foreground">
              Manage all your voice agents and interactive demos in one place
            </p>
          </div>
        </div>

        {/* Search, Filter, and Action Buttons */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            {/* Search and Filter */}
            <div className="flex items-center gap-2 mr-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-40">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  {assistantTypes.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type === "all" ? "All Types" : type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <Button onClick={() => navigate("/create-assistant")} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Create New Agent
            </Button>
            <Button variant="outline" onClick={() => setShowImportDialog(true)} className="flex items-center gap-2">
              <Download className="h-4 w-4" />
              Import Agent
            </Button>
            <Button 
              variant="outline" 
              onClick={() => navigate("/wallet")}
              className="flex items-center gap-2"
            >
              <Wallet className="h-4 w-4" />
              Manage Wallet & Usage
            </Button>
            <Button 
              onClick={load} 
              disabled={isLoading}
              variant="outline"
              className="flex items-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                  Loading...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4" />
                  Refresh
                </>
              )}
            </Button>
          </div>
        </div>

        <Tabs defaultValue="assistants">
          <TabsList>
            <TabsTrigger value="assistants">Assistants</TabsTrigger>
            <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
          </TabsList>

          <TabsContent value="assistants" className="mt-6">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin mr-2" />
                <p>Loading assistants...</p>
              </div>
            ) : demos.length === 0 ? (
              <Card>
                <CardHeader>
                  <CardTitle>No assistants yet</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground mb-4">Create your first assistant to get started.</p>
                  <Button onClick={() => navigate("/create-assistant")}>
                    Create First Assistant
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                <div className="text-sm text-muted-foreground">
                  Found {filteredDemos.length} assistant{filteredDemos.length !== 1 ? 's' : ''}
                  {searchTerm && ` matching "${searchTerm}"`}
                  {filterType !== "all" && ` of type "${filterType}"`}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {filteredDemos.map((d) => (
                    <AssistantManager
                      key={d.id}
                      assistant={d}
                      onStatusChange={(assistantId, newStatus, newType) => {
                        if (newStatus === 'deleted') {
                          // Remove the assistant from the list when deleted
                          setDemos(prev => prev.filter(demo => demo.id !== assistantId));
                        } else {
                          // Update the assistant status/type
                          setDemos(prev => prev.map(demo => 
                            demo.id === assistantId ? { 
                              ...demo, 
                              status: newStatus,
                              ...(newType && { assistant_type: newType })
                            } : demo
                          ));
                        }
                      }}
                    />
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="campaigns" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Campaigns</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Coming soon.</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">Coming soon.</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Assistant</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>System Prompt</Label>
              <Textarea rows={5} value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Describe behavior, tone, and goals..." />
            </div>
            <div className="space-y-2">
              <Label>Voice</Label>
              <Select value={voiceId} onValueChange={setVoiceId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select voice" />
                </SelectTrigger>
                <SelectContent>
                  {voices.map((v) => (
                    <SelectItem key={v.id} value={v.id}>{v.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={saveEdit}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleting} onOpenChange={(o) => !o && setDeleting(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete assistant?</AlertDialogTitle>
            <AlertDialogDescription>This action cannot be undone.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={doDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <CloneAssistantDialog
        open={cloneOpen}
        onOpenChange={setCloneOpen}
        assistant={cloning}
        onSuccess={load}
      />

      {/* Import Assistant Dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Import Assistant</DialogTitle>
          </DialogHeader>
          <ImportAssistant 
            onImportSuccess={() => {
              setShowImportDialog(false);
              console.log("Import successful, reloading data...");
              // Add a small delay to ensure the database write is complete
              setTimeout(() => {
                load(); // Reload to show the imported assistant
              }, 500);
              toast({
                title: "Import Successful!",
                description: "Your assistant has been imported and is now available in the list.",
                variant: "default",
              });
            }} 
          />
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default VoiceAgents;
