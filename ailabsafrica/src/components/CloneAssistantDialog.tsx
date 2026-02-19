import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { useToast } from "@/components/ui/use-toast";
import { Copy, Loader2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";

interface CloneAssistantDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  assistant: {
    id: string;
    assistant_name: string;
    assistant_type: string;
    assistant_id: string;
  } | null;
  onSuccess: () => void;
}

const CloneAssistantDialog = ({ open, onOpenChange, assistant, onSuccess }: CloneAssistantDialogProps) => {
  const { toast } = useToast();
  const [newName, setNewName] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleClone = async () => {
    if (!assistant || !newName.trim()) {
      toast({ title: "Error", description: "Please enter a name for the cloned assistant", variant: "destructive" });
      return;
    }

    setIsLoading(true);
    try {
      const { error } = await supabase.functions.invoke("clone-assistant", {
        body: {
          source_assistant_id: assistant.assistant_id,
          new_name: newName.trim(),
          user_id: (await supabase.auth.getUser()).data.user?.id
        }
      });

      if (error) {
        if (error.message?.includes("already exists")) {
          toast({ title: "Name already exists", description: "Please choose a different name for the cloned assistant", variant: "destructive" });
        } else {
          throw error;
        }
        return;
      }

      toast({ title: "Success", description: "Assistant cloned successfully" });
      setNewName("");
      onOpenChange(false);
      onSuccess();
    } catch (error: any) {
      console.error("Clone error:", error);
      toast({ 
        title: "Clone failed", 
        description: error.message || "Failed to clone assistant", 
        variant: "destructive" 
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setNewName("");
    }
    onOpenChange(newOpen);
  };

  const generateCloneName = () => {
    if (!assistant) return "";
    const baseName = assistant.assistant_name;
    const timestamp = new Date().toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
    return `${baseName} (Copy - ${timestamp})`;
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Copy className="h-5 w-5" />
            Clone Assistant
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {assistant && (
            <div className="p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium">Cloning: {assistant.assistant_name}</p>
              <p className="text-xs text-muted-foreground capitalize">
                {assistant.assistant_type.replace(/_/g, ' ')}
              </p>
            </div>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="new-name">New Assistant Name</Label>
            <Input
              id="new-name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder={generateCloneName()}
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              This will create a copy of the assistant with all the same settings and configuration.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleClone}
            disabled={!newName.trim() || isLoading}
            className="flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Cloning...
              </>
            ) : (
              <>
                <Copy className="h-4 w-4" />
                Clone Assistant
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CloneAssistantDialog;
