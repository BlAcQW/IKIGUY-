/**
 * AITemplateGenerator Component
 *
 * AI-powered template generation with customization options.
 */

import { useState } from "react";
import { Sparkles, Loader2, FileText, Globe, Scale, Plus, X } from "lucide-react";
import { useGenerateTemplate } from "../hooks/use-documents";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Badge } from "./ui/badge";
import { useToast } from "./ui/use-toast";
import type { DocumentType } from "../lib/api/document-api";

interface AITemplateGeneratorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: (templateId: string) => void;
}

export function AITemplateGenerator({
  open,
  onOpenChange,
  onSuccess,
}: AITemplateGeneratorProps) {
  const { toast } = useToast();
  const generateMutation = useGenerateTemplate();

  // Form state
  const [documentType, setDocumentType] = useState<DocumentType>("lease_agreement");
  const [jurisdiction, setJurisdiction] = useState("Ghana");
  const [language, setLanguage] = useState("en");
  const [customClauses, setCustomClauses] = useState<string[]>([]);
  const [excludeClauses, setExcludeClauses] = useState<string[]>([]);
  const [additionalInstructions, setAdditionalInstructions] = useState("");
  const [newClause, setNewClause] = useState("");
  const [newExcludeClause, setNewExcludeClause] = useState("");

  const documentTypes: { value: DocumentType; label: string }[] = [
    { value: "lease_agreement", label: "Lease Agreement" },
    { value: "purchase_agreement", label: "Purchase Agreement" },
    { value: "rental_application", label: "Rental Application" },
    { value: "property_disclosure", label: "Property Disclosure" },
    { value: "offer_letter", label: "Offer Letter" },
    { value: "counter_offer", label: "Counter Offer" },
    { value: "addendum", label: "Addendum" },
    { value: "tenant_screening", label: "Tenant Screening" },
    { value: "eviction_notice", label: "Eviction Notice" },
    { value: "lease_renewal", label: "Lease Renewal" },
    { value: "move_in_checklist", label: "Move-In Checklist" },
    { value: "move_out_checklist", label: "Move-Out Checklist" },
    { value: "maintenance_request", label: "Maintenance Request" },
    { value: "rent_receipt", label: "Rent Receipt" },
    { value: "security_deposit_return", label: "Security Deposit Return" },
  ];

  const jurisdictions = [
    "Ghana",
    "Nigeria",
    "South Africa",
    "Kenya",
    "United States",
    "United Kingdom",
    "Canada",
  ];

  const languages = [
    { value: "en", label: "English" },
    { value: "es", label: "Spanish" },
    { value: "fr", label: "French" },
  ];

  const addCustomClause = () => {
    if (newClause.trim()) {
      setCustomClauses([...customClauses, newClause.trim()]);
      setNewClause("");
    }
  };

  const removeCustomClause = (index: number) => {
    setCustomClauses(customClauses.filter((_, i) => i !== index));
  };

  const addExcludeClause = () => {
    if (newExcludeClause.trim()) {
      setExcludeClauses([...excludeClauses, newExcludeClause.trim()]);
      setNewExcludeClause("");
    }
  };

  const removeExcludeClause = (index: number) => {
    setExcludeClauses(excludeClauses.filter((_, i) => i !== index));
  };

  const handleGenerate = async () => {
    try {
      const template = await generateMutation.mutateAsync({
        document_type: documentType,
        jurisdiction,
        language,
        custom_clauses: customClauses.length > 0 ? customClauses : undefined,
        exclude_clauses: excludeClauses.length > 0 ? excludeClauses : undefined,
        additional_instructions: additionalInstructions || undefined,
      });

      toast({
        title: "Success",
        description: "Template generated successfully!",
      });

      onSuccess?.(template.id);
      onOpenChange(false);

      // Reset form
      setDocumentType("lease_agreement");
      setJurisdiction("Ghana");
      setLanguage("en");
      setCustomClauses([]);
      setExcludeClauses([]);
      setAdditionalInstructions("");
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to generate template",
        variant: "destructive",
      });
    }
  };

  const isLoading = generateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            AI Template Generator
          </DialogTitle>
          <DialogDescription>
            Generate professional, legally compliant document templates using AI
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Document Type */}
          <div>
            <Label htmlFor="document-type" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Document Type
            </Label>
            <Select value={documentType} onValueChange={(v) => setDocumentType(v as DocumentType)}>
              <SelectTrigger id="document-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {documentTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Jurisdiction */}
          <div>
            <Label htmlFor="jurisdiction" className="flex items-center gap-2">
              <Scale className="h-4 w-4" />
              Jurisdiction
            </Label>
            <Select value={jurisdiction} onValueChange={setJurisdiction}>
              <SelectTrigger id="jurisdiction">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {jurisdictions.map((j) => (
                  <SelectItem key={j} value={j}>
                    {j}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Language */}
          <div>
            <Label htmlFor="language" className="flex items-center gap-2">
              <Globe className="h-4 w-4" />
              Language
            </Label>
            <Select value={language} onValueChange={setLanguage}>
              <SelectTrigger id="language">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {languages.map((lang) => (
                  <SelectItem key={lang.value} value={lang.value}>
                    {lang.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Custom Clauses */}
          <div>
            <Label className="mb-2 block">Custom Clauses (Optional)</Label>
            <div className="space-y-2">
              {customClauses.map((clause, index) => (
                <div key={index} className="flex items-center gap-2">
                  <Badge variant="secondary" className="flex-1">
                    {clause}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeCustomClause(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <div className="flex gap-2">
                <Input
                  value={newClause}
                  onChange={(e) => setNewClause(e.target.value)}
                  placeholder="e.g., Pet policy with $500 deposit"
                  onKeyDown={(e) => e.key === "Enter" && addCustomClause()}
                />
                <Button variant="outline" onClick={addCustomClause} disabled={!newClause.trim()}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Exclude Clauses */}
          <div>
            <Label className="mb-2 block">Exclude Standard Clauses (Optional)</Label>
            <div className="space-y-2">
              {excludeClauses.map((clause, index) => (
                <div key={index} className="flex items-center gap-2">
                  <Badge variant="outline" className="flex-1">
                    {clause}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeExcludeClause(index)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <div className="flex gap-2">
                <Input
                  value={newExcludeClause}
                  onChange={(e) => setNewExcludeClause(e.target.value)}
                  placeholder="e.g., Late payment fees"
                  onKeyDown={(e) => e.key === "Enter" && addExcludeClause()}
                />
                <Button
                  variant="outline"
                  onClick={addExcludeClause}
                  disabled={!newExcludeClause.trim()}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          {/* Additional Instructions */}
          <div>
            <Label htmlFor="instructions">Additional Instructions (Optional)</Label>
            <Textarea
              id="instructions"
              value={additionalInstructions}
              onChange={(e) => setAdditionalInstructions(e.target.value)}
              placeholder="e.g., Make it tenant-friendly with flexible terms, include provisions for early termination..."
              rows={4}
            />
          </div>

          {/* AI Note */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-purple-600 mt-0.5" />
              <div className="flex-1 text-sm">
                <p className="font-medium text-purple-900 mb-1">
                  AI-Powered Generation
                </p>
                <p className="text-purple-700">
                  Our AI will analyze your requirements and generate a professional,
                  legally compliant template with all necessary variables and clauses.
                  The template will be customized for {jurisdiction} law.
                </p>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleGenerate} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Template
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
