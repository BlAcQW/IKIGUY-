/**
 * Save Property Button Component
 *
 * Toggle button for saving/unsaving properties to favorites.
 * Works with authenticated users, shows login prompt for guests.
 */

import { useState, useEffect } from "react";
import { Heart } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import {
  saveProperty,
  unsaveProperty,
  checkPropertySaved,
} from "@/lib/api/user-api";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { LeadForm } from "@/components/LeadForm";

interface SavePropertyButtonProps {
  propertyId: string;
  /**
   * Variant: 'default' for property cards, 'large' for detail pages.
   */
  variant?: "default" | "large";
  /**
   * Optional className for custom styling.
   */
  className?: string;
  /**
   * Show text label alongside icon.
   */
  showLabel?: boolean;
}

export function SavePropertyButton({
  propertyId,
  variant = "default",
  className,
  showLabel = false,
}: SavePropertyButtonProps) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isSaved, setIsSaved] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [showLeadDialog, setShowLeadDialog] = useState(false);

  // Check if property is saved on mount (only if authenticated)
  useEffect(() => {
    if (user) {
      checkSavedStatus();
    } else {
      setIsChecking(false);
      setIsSaved(false);
    }
  }, [propertyId, user]);

  const checkSavedStatus = async () => {
    try {
      setIsChecking(true);
      const response = await checkPropertySaved(propertyId);
      setIsSaved(response.is_saved);
    } catch (error) {
      console.error("Error checking saved status:", error);
      setIsSaved(false);
    } finally {
      setIsChecking(false);
    }
  };

  const handleClick = async (e: React.MouseEvent) => {
    // Prevent event propagation (in case button is inside a clickable card)
    e.stopPropagation();
    e.preventDefault();

    // If not authenticated, show lead form dialog
    if (!user) {
      setShowLeadDialog(true);
      return;
    }

    // Toggle saved state
    setIsLoading(true);
    try {
      if (isSaved) {
        // Unsave property
        await unsaveProperty(propertyId);
        setIsSaved(false);
        toast({
          title: "Removed from favorites",
          description: "Property removed from your saved list.",
        });
      } else {
        // Save property
        await saveProperty(propertyId);
        setIsSaved(true);
        toast({
          title: "Added to favorites",
          description: "Property saved to your favorites list.",
        });
      }
    } catch (error: any) {
      console.error("Error toggling saved property:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to update saved property",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const buttonSize = variant === "large" ? "lg" : "sm";
  const iconSize = variant === "large" ? "h-5 w-5" : "h-4 w-4";

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant={isSaved ? "default" : "outline"}
            size={buttonSize}
            onClick={handleClick}
            disabled={isLoading || isChecking}
            className={cn(
              "gap-2 transition-all",
              isSaved && "bg-red-500 hover:bg-red-600 text-white",
              className
            )}
          >
            <Heart
              className={cn(
                iconSize,
                "transition-all",
                isSaved && "fill-current",
                isLoading && "animate-pulse"
              )}
            />
            {showLabel && (
              <span className="hidden sm:inline">
                {isLoading
                  ? "..."
                  : isSaved
                    ? "Saved"
                    : "Save"}
              </span>
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>
            {isChecking
              ? "Checking..."
              : isLoading
                ? "Updating..."
                : isSaved
                  ? "Remove from favorites"
                  : "Save to favorites"}
          </p>
        </TooltipContent>
      </Tooltip>

      <Dialog open={showLeadDialog} onOpenChange={setShowLeadDialog}>
        <DialogContent className="sm:max-w-[450px] p-0 border-none bg-transparent">
          <DialogHeader className="sr-only">
            <DialogTitle>Register Interest</DialogTitle>
          </DialogHeader>
          <LeadForm propertyId={propertyId} />
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
}
