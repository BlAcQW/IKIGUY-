/**
 * Contact Form Dialog
 *
 * Dialog for creating and editing contacts/leads.
 * Supports all contact fields and custom property preferences.
 */

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Loader2, X, Plus } from "lucide-react";

interface ContactFormDialogProps {
  open: boolean;
  onClose: () => void;
  contact?: any; // Existing contact for editing (optional)
  onSubmit: (data: ContactFormData) => Promise<void>;
}

export interface ContactFormData {
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  contact_type: string;
  interest_level: string;
  tags: string[];
  source?: string;
  notes?: string;
  // EstateFlow-specific fields
  property_type_preferences?: string[];
  location_preferences?: string[];
  budget_min?: number;
  budget_max?: number;
}

const CONTACT_TYPES = [
  { value: "lead", label: "Lead" },
  { value: "customer", label: "Customer" },
  { value: "prospect", label: "Prospect" },
  { value: "member", label: "Member" },
];

const INTEREST_LEVELS = [
  { value: "hot", label: "Hot - Ready to act" },
  { value: "warm", label: "Warm - Interested" },
  { value: "cold", label: "Cold - Exploring" },
  { value: "unqualified", label: "Unqualified" },
];

const PROPERTY_TYPES = [
  "Apartment",
  "House",
  "Villa",
  "Penthouse",
  "Loft",
  "Townhouse",
  "Land",
  "Commercial",
];

export function ContactFormDialog({
  open,
  onClose,
  contact,
  onSubmit,
}: ContactFormDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [tagInput, setTagInput] = useState("");
  const [formData, setFormData] = useState<ContactFormData>({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    contact_type: "lead",
    interest_level: "warm",
    tags: [],
    source: "",
    notes: "",
    property_type_preferences: [],
    location_preferences: [],
    budget_min: undefined,
    budget_max: undefined,
  });

  // Load contact data when editing
  useEffect(() => {
    if (contact) {
      setFormData({
        first_name: contact.first_name || "",
        last_name: contact.last_name || "",
        email: contact.email || "",
        phone: contact.phone || "",
        contact_type: contact.contact_type || "lead",
        interest_level: contact.interest_level || "warm",
        tags: contact.tags || [],
        source: contact.source || "",
        notes: contact.notes || "",
        property_type_preferences: contact.custom_data?.property_type_preferences || [],
        location_preferences: contact.custom_data?.location_preferences || [],
        budget_min: contact.custom_data?.budget_min,
        budget_max: contact.custom_data?.budget_max,
      });
    } else {
      // Reset for new contact
      setFormData({
        first_name: "",
        last_name: "",
        email: "",
        phone: "",
        contact_type: "lead",
        interest_level: "warm",
        tags: [],
        source: "",
        notes: "",
        property_type_preferences: [],
        location_preferences: [],
        budget_min: undefined,
        budget_max: undefined,
      });
    }
  }, [contact, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await onSubmit(formData);
      onClose();
    } catch (error) {
      console.error("Failed to save contact:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, tagInput.trim()],
      });
      setTagInput("");
    }
  };

  const handleRemoveTag = (tag: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter((t) => t !== tag),
    });
  };

  const togglePropertyType = (type: string) => {
    const current = formData.property_type_preferences || [];
    if (current.includes(type)) {
      setFormData({
        ...formData,
        property_type_preferences: current.filter((t) => t !== type),
      });
    } else {
      setFormData({
        ...formData,
        property_type_preferences: [...current, type],
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent
        className="w-full max-w-full md:max-w-2xl max-h-[90vh] overflow-y-auto"
        aria-describedby="contact-form-description"
      >
        <DialogHeader>
          <DialogTitle>
            {contact ? "Edit Contact" : "Add New Contact"}
          </DialogTitle>
          <p id="contact-form-description" className="sr-only">
            Form to {contact ? "edit an existing" : "create a new"} contact or lead
          </p>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6 pt-4">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Basic Information</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="first_name">First Name *</Label>
                <Input
                  id="first_name"
                  required
                  value={formData.first_name}
                  onChange={(e) =>
                    setFormData({ ...formData, first_name: e.target.value })
                  }
                />
              </div>

              <div>
                <Label htmlFor="last_name">Last Name *</Label>
                <Input
                  id="last_name"
                  required
                  value={formData.last_name}
                  onChange={(e) =>
                    setFormData({ ...formData, last_name: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                />
              </div>

              <div>
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+233241234567"
                  value={formData.phone}
                  onChange={(e) =>
                    setFormData({ ...formData, phone: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="contact_type">Contact Type</Label>
                <Select
                  value={formData.contact_type}
                  onValueChange={(value) =>
                    setFormData({ ...formData, contact_type: value })
                  }
                >
                  <SelectTrigger id="contact_type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CONTACT_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="interest_level">Interest Level</Label>
                <Select
                  value={formData.interest_level}
                  onValueChange={(value) =>
                    setFormData({ ...formData, interest_level: value })
                  }
                >
                  <SelectTrigger id="interest_level">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {INTEREST_LEVELS.map((level) => (
                      <SelectItem key={level.value} value={level.value}>
                        {level.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="source">Source</Label>
              <Input
                id="source"
                placeholder="e.g., Website, Referral, Social Media"
                value={formData.source}
                onChange={(e) =>
                  setFormData({ ...formData, source: e.target.value })
                }
              />
            </div>
          </div>

          {/* Property Preferences */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Property Preferences</h3>

            <div>
              <Label>Property Types</Label>
              <div className="flex flex-wrap gap-2 mt-2">
                {PROPERTY_TYPES.map((type) => (
                  <Badge
                    key={type}
                    variant={
                      formData.property_type_preferences?.includes(type)
                        ? "default"
                        : "outline"
                    }
                    className="cursor-pointer"
                    onClick={() => togglePropertyType(type)}
                  >
                    {type}
                  </Badge>
                ))}
              </div>
            </div>

            <div>
              <Label htmlFor="location_preferences">Location Preferences</Label>
              <Input
                id="location_preferences"
                placeholder="Enter locations (comma-separated)"
                value={formData.location_preferences?.join(", ") || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    location_preferences: e.target.value
                      .split(",")
                      .map((l) => l.trim())
                      .filter(Boolean),
                  })
                }
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="budget_min">Budget Min (GHS)</Label>
                <Input
                  id="budget_min"
                  type="number"
                  placeholder="0"
                  value={formData.budget_min || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      budget_min: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
              </div>

              <div>
                <Label htmlFor="budget_max">Budget Max (GHS)</Label>
                <Input
                  id="budget_max"
                  type="number"
                  placeholder="0"
                  value={formData.budget_max || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      budget_max: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
              </div>
            </div>
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label htmlFor="tags">Tags</Label>
            <div className="flex gap-2">
              <Input
                id="tags"
                placeholder="Add a tag"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddTag();
                  }
                }}
              />
              <Button type="button" variant="secondary" onClick={handleAddTag}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {formData.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="gap-1">
                    {tag}
                    <X
                      className="h-3 w-3 cursor-pointer"
                      onClick={() => handleRemoveTag(tag)}
                    />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Notes */}
          <div>
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              placeholder="Add any additional notes about this contact..."
              rows={4}
              value={formData.notes}
              onChange={(e) =>
                setFormData({ ...formData, notes: e.target.value })
              }
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {contact ? "Update Contact" : "Create Contact"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
