import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import { 
  GitBranch, 
  History, 
  RotateCcw, 
  Plus,
  Calendar,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  User
} from "lucide-react";
import { supabase } from "@/integrations/supabase/client";

interface DemoVersion {
  version_number: number;
  assistant_name: string;
  assistant_type: string;
  description: string;
  version_notes: string;
  created_at: string;
  is_current: boolean;
}

interface DemoVersioningProps {
  demoId: string;
  assistantName: string;
  assistantType: string;
  currentVersion?: number;
  onVersionChange?: (versionNumber: number) => void;
}

const DemoVersioning = ({ 
  demoId, 
  assistantName, 
  assistantType, 
  currentVersion = 1,
  onVersionChange 
}: DemoVersioningProps) => {
  const { toast } = useToast();
  const [versionDialogOpen, setVersionDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [rollbackDialogOpen, setRollbackDialogOpen] = useState(false);
  const [versions, setVersions] = useState<DemoVersion[]>([]);
  const [loading, setLoading] = useState(false);
  const [creatingVersion, setCreatingVersion] = useState(false);
  const [rollingBack, setRollingBack] = useState(false);
  const [versionNotes, setVersionNotes] = useState("");
  const [selectedVersion, setSelectedVersion] = useState<DemoVersion | null>(null);

  // Fetch version history
  const fetchVersionHistory = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('demo-versioning?action=get_version_history', {
        body: { demo_id: demoId }
      });

      if (error) {
        throw error;
      }

      if (data.success) {
        setVersions(data.versions || []);
      }
    } catch (error) {
      console.error('Error fetching version history:', error);
      toast({
        title: "Error",
        description: "Failed to fetch version history",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  // Create new version
  const createVersion = async () => {
    if (!versionNotes.trim()) {
      toast({
        title: "Version notes required",
        description: "Please provide notes for this version",
        variant: "destructive"
      });
      return;
    }

    setCreatingVersion(true);
    try {
      const { data, error } = await supabase.functions.invoke('demo-versioning?action=create_version', {
        body: { 
          demo_id: demoId,
          version_notes: versionNotes.trim()
        }
      });

      if (error) {
        throw error;
      }

      if (data.success) {
        toast({
          title: "Version created!",
          description: `Version ${data.version_number} created successfully`,
        });
        
        setVersionNotes("");
        setVersionDialogOpen(false);
        
        // Refresh version history
        await fetchVersionHistory();
        
        // Notify parent of version change
        if (onVersionChange) {
          onVersionChange(data.version_number);
        }
      }
    } catch (error) {
      console.error('Error creating version:', error);
      toast({
        title: "Error",
        description: "Failed to create version",
        variant: "destructive"
      });
    } finally {
      setCreatingVersion(false);
    }
  };

  // Rollback to version
  const rollbackToVersion = async () => {
    if (!selectedVersion) return;

    setRollingBack(true);
    try {
      const { data, error } = await supabase.functions.invoke('demo-versioning?action=rollback_version', {
        body: { 
          demo_id: demoId,
          version_number: selectedVersion.version_number
        }
      });

      if (error) {
        throw error;
      }

      if (data.success) {
        toast({
          title: "Rollback successful!",
          description: `Rolled back to version ${selectedVersion.version_number}`,
        });
        
        setRollbackDialogOpen(false);
        setSelectedVersion(null);
        
        // Refresh version history
        await fetchVersionHistory();
        
        // Notify parent of version change
        if (onVersionChange) {
          onVersionChange(selectedVersion.version_number);
        }
      }
    } catch (error) {
      console.error('Error rolling back version:', error);
      toast({
        title: "Error",
        description: "Failed to rollback version",
        variant: "destructive"
      });
    } finally {
      setRollingBack(false);
    }
  };

  // Load version history when component mounts or demoId changes
  useEffect(() => {
    if (demoId) {
      fetchVersionHistory();
    }
  }, [demoId]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getVersionBadgeVariant = (version: DemoVersion) => {
    if (version.is_current) return "default";
    return "secondary";
  };

  return (
    <>
      {/* Version Management Buttons */}
      <div className="flex items-center gap-2">
        <Button 
          variant="outline" 
          onClick={() => setVersionDialogOpen(true)}
          className="flex items-center gap-1 px-2 py-1 text-xs"
        >
          <Plus className="h-3 w-3" />
          <span className="hidden sm:inline">New Version</span>
        </Button>
        
        <Button 
          variant="outline" 
          onClick={() => setHistoryDialogOpen(true)}
          className="flex items-center gap-1 px-2 py-1 text-xs"
        >
          <History className="h-3 w-3" />
          <span className="hidden sm:inline">Version History</span>
          {versions.length > 0 && (
            <Badge variant="secondary" className="ml-1">
              {versions.length}
            </Badge>
          )}
        </Button>
      </div>

      {/* Create New Version Dialog */}
      <Dialog open={versionDialogOpen} onOpenChange={setVersionDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              Create New Version
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <Card>
              <CardContent className="p-4">
                <h3 className="font-semibold text-lg mb-1">{assistantName}</h3>
                <p className="text-sm text-muted-foreground capitalize mb-2">
                  {assistantType.replace(/_/g, ' ')}
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">v{currentVersion}</Badge>
                  <span className="text-sm text-muted-foreground">Current Version</span>
                </div>
              </CardContent>
            </Card>

            <div className="space-y-2">
              <Label htmlFor="version-notes">Version Notes</Label>
              <Textarea
                id="version-notes"
                value={versionNotes}
                onChange={(e) => setVersionNotes(e.target.value)}
                placeholder="Describe what changes you're making in this version..."
                rows={4}
              />
              <p className="text-sm text-muted-foreground">
                Explain what's new or different in this version
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setVersionDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={createVersion} 
              disabled={creatingVersion || !versionNotes.trim()}
              className="flex items-center gap-2"
            >
              {creatingVersion ? (
                <>
                  <Clock className="h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Create Version
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Version History Dialog */}
      <Dialog open={historyDialogOpen} onOpenChange={setHistoryDialogOpen}>
        <DialogContent className="sm:max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Version History
            </DialogTitle>
            <p className="text-sm text-muted-foreground">
              Track all versions of your demo and rollback to previous versions if needed
            </p>
          </DialogHeader>
          
          <div className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Clock className="h-6 w-6 animate-spin" />
                <span className="ml-2">Loading version history...</span>
              </div>
            ) : versions.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <History className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No versions yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Create your first version to start tracking changes
                  </p>
                  <Button onClick={() => setHistoryDialogOpen(false)}>
                    Create First Version
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {versions.map((version) => (
                  <Card key={version.version_number} className="relative">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant={getVersionBadgeVariant(version)}>
                              v{version.version_number}
                            </Badge>
                            {version.is_current && (
                              <Badge variant="default" className="flex items-center gap-1">
                                <CheckCircle className="h-3 w-3" />
                                Current
                              </Badge>
                            )}
                          </div>
                          
                          <h4 className="font-semibold mb-1">{version.assistant_name}</h4>
                          <p className="text-sm text-muted-foreground capitalize mb-2">
                            {version.assistant_type.replace(/_/g, ' ')}
                          </p>
                          
                          {version.description && (
                            <p className="text-sm mb-2">{version.description}</p>
                          )}
                          
                          {version.version_notes && (
                            <div className="bg-muted p-3 rounded-lg mb-3">
                              <div className="flex items-center gap-2 mb-1">
                                <FileText className="h-3 w-3" />
                                <span className="text-xs font-medium">Version Notes</span>
                              </div>
                              <p className="text-sm">{version.version_notes}</p>
                            </div>
                          )}
                          
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(version.created_at)}
                            </div>
                          </div>
                        </div>
                        
                        {!version.is_current && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setSelectedVersion(version);
                              setRollbackDialogOpen(true);
                            }}
                            className="flex items-center gap-2"
                          >
                            <RotateCcw className="h-3 w-3" />
                            Rollback
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setHistoryDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rollback Confirmation Dialog */}
      <Dialog open={rollbackDialogOpen} onOpenChange={setRollbackDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              Confirm Rollback
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                <div>
                  <h4 className="font-semibold text-destructive mb-1">Warning</h4>
                  <p className="text-sm text-muted-foreground">
                    Rolling back to version {selectedVersion?.version_number} will replace your current demo configuration. 
                    This action cannot be undone.
                  </p>
                </div>
              </div>
            </div>

            {selectedVersion && (
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="secondary">v{selectedVersion.version_number}</Badge>
                    <span className="text-sm font-medium">{selectedVersion.assistant_name}</span>
                  </div>
                  <p className="text-sm text-muted-foreground capitalize mb-2">
                    {selectedVersion.assistant_type.replace(/_/g, ' ')}
                  </p>
                  {selectedVersion.version_notes && (
                    <p className="text-sm bg-muted p-2 rounded">
                      {selectedVersion.version_notes}
                    </p>
                  )}
                </CardContent>
              </Card>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setRollbackDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={rollbackToVersion}
              disabled={rollingBack}
              className="flex items-center gap-2"
            >
              {rollingBack ? (
                <>
                  <Clock className="h-4 w-4 animate-spin" />
                  Rolling back...
                </>
              ) : (
                <>
                  <RotateCcw className="h-4 w-4" />
                  Rollback to v{selectedVersion?.version_number}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default DemoVersioning;
