import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/use-toast";
import { supabase } from "@/integrations/supabase/client";
import { Trash2, Loader2 } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface DemoRow {
  id: string;
  assistant_name: string;
  assistant_type: string;
  demo_url: string;
  created_at: string;
  status: string;
}

const CustomDemos = () => {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [demos, setDemos] = useState<DemoRow[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [deletingDemo, setDeletingDemo] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [demoToDelete, setDemoToDelete] = useState<DemoRow | null>(null);

  useEffect(() => {
    document.title = "My Custom Demos | AI Labs Africa";
  }, []);

  useEffect(() => {
    if (!loading && !user) {
      navigate("/auth");
    }
  }, [user, loading, navigate]);

  useEffect(() => {
    const load = async () => {
      if (!user) return;
      setIsLoading(true);
      try {
        const { data, error } = await supabase.functions.invoke("list-custom-demos");
        if (error) throw error;
        setDemos((data?.demos as DemoRow[]) || []);
      } catch (e: any) {
        console.error(e);
        toast({ title: "Failed to load demos", description: e.message, variant: "destructive" });
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [user]);

  const handleDeleteClick = (demo: DemoRow) => {
    setDemoToDelete(demo);
    setShowDeleteDialog(true);
  };

  const handleDeleteConfirm = async () => {
    if (!demoToDelete) return;
    
    setDeletingDemo(demoToDelete.id);
    try {
      const { data, error } = await supabase.functions.invoke("manage-custom-demos", {
        body: {
          action: "delete",
          demo_id: demoToDelete.id
        }
      });

      if (error) throw error;

      toast({
        title: "Success",
        description: "Demo deleted successfully"
      });

      // Remove the demo from the local state
      setDemos(prev => prev.filter(d => d.id !== demoToDelete.id));
    } catch (error: any) {
      console.error("Failed to delete demo:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to delete demo",
        variant: "destructive"
      });
    } finally {
      setDeletingDemo(null);
      setShowDeleteDialog(false);
      setDemoToDelete(null);
    }
  };

  return (
    <main className="container py-10">
      <section className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">My Custom Demos</h1>
          <Button onClick={() => navigate("/create-assistant")}>Create New</Button>
        </div>

        {isLoading ? (
          <p>Loading...</p>
        ) : demos.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>No demos yet</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">You haven't created any demos. Create your first assistant to get started.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {demos.map((d) => (
              <Card key={d.id}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{d.assistant_name}</span>
                    <span className="text-sm font-normal text-muted-foreground">{new Date(d.created_at).toLocaleString()}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <span className="text-sm uppercase tracking-wide text-muted-foreground">{d.assistant_type.replace(/_/g, ' ')}</span>
                    <div className="flex gap-2">
                      <Button variant="secondary" asChild>
                        <a href={d.demo_url} target="_blank" rel="noreferrer">Open</a>
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteClick(d)}
                        disabled={deletingDemo === d.id}
                      >
                        {deletingDemo === d.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Demo</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{demoToDelete?.assistant_name}"? This action cannot be undone and will also delete the assistant from VAPI.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteConfirm} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  );
};

export default CustomDemos;
