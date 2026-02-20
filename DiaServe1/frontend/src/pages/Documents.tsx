import { useState } from "react";
import {
  FileText,
  Plus,
  Search,
  Filter,
  Download,
  Share2,
  Trash2,
  FileCheck,
  FilePen,
  FileX,
  Sparkles,
  Loader2,
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useDocuments, useTemplates, useDeleteDocument, useDownloadPdf, useDownloadDocx } from "@/hooks/use-documents";
import { useToast } from "@/hooks/use-toast";

export default function Documents() {
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch real documents and templates
  const { data: docsData, isLoading: docsLoading } = useDocuments(
    searchQuery ? { limit: 50 } : { limit: 50 }
  );
  const { data: templatesData } = useTemplates();
  const deleteDocument = useDeleteDocument();
  const downloadPdf = useDownloadPdf();
  const downloadDocx = useDownloadDocx();

  const documents = docsData?.documents || [];
  const templates = templatesData?.templates || [];

  // Filter documents by search query (client-side for search input)
  const filteredDocuments = searchQuery
    ? documents.filter(doc =>
        doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.document_type.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : documents;

  // Compute document type counts from templates
  const documentTypes = [
    {
      name: "Lease Agreements",
      icon: FileCheck,
      count: templates.filter(t => t.document_type.includes("lease")).length
        + documents.filter(d => d.document_type.includes("lease")).length,
    },
    {
      name: "Offer Letters",
      icon: FilePen,
      count: documents.filter(d => d.document_type === "offer_letter" || d.document_type === "counter_offer").length,
    },
    {
      name: "Applications",
      icon: FileText,
      count: documents.filter(d => d.document_type === "rental_application" || d.document_type === "tenant_screening").length,
    },
    {
      name: "Other Documents",
      icon: FileX,
      count: documents.filter(d =>
        !d.document_type.includes("lease") &&
        d.document_type !== "offer_letter" &&
        d.document_type !== "counter_offer" &&
        d.document_type !== "rental_application" &&
        d.document_type !== "tenant_screening"
      ).length,
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "signed": return "success";
      case "pending_review":
      case "sent": return "warning";
      case "draft": return "muted";
      case "ready": return "info";
      default: return "muted";
    }
  };

  const handleDownload = (docId: string, format: "pdf" | "docx") => {
    if (format === "pdf") {
      downloadPdf.mutate(docId, {
        onError: () => toast({ title: "Error", description: "Failed to download PDF", variant: "destructive" }),
      });
    } else {
      downloadDocx.mutate(docId, {
        onError: () => toast({ title: "Error", description: "Failed to download DOCX", variant: "destructive" }),
      });
    }
  };

  const handleDelete = (docId: string) => {
    deleteDocument.mutate(docId, {
      onSuccess: () => toast({ title: "Deleted", description: "Document deleted successfully" }),
      onError: () => toast({ title: "Error", description: "Failed to delete document", variant: "destructive" }),
    });
  };

  return (
    <div className="min-h-screen">
      <Header
        title="Documents"
        subtitle="Manage contracts, agreements, and files"
        actions={
          <div className="flex items-center gap-3">
            <Button variant="outline" className="gap-2">
              <Sparkles className="h-4 w-4" />
              AI Generate
            </Button>
            <Button variant="accent" className="gap-2">
              <Plus className="h-4 w-4" />
              Upload
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Document Types */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {documentTypes.map((type) => (
            <Card key={type.name} variant="interactive">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                  <type.icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-foreground">{type.count}</p>
                  <p className="text-sm text-muted-foreground">{type.name}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Search */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search documents..."
              className="pl-9"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <Button variant="outline" className="gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </Button>
        </div>

        {/* Documents List */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Documents</CardTitle>
            <CardDescription>Your files and contracts</CardDescription>
          </CardHeader>
          <CardContent>
            {docsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
                <p className="font-medium">No documents found</p>
                <p className="text-sm mt-1">
                  {searchQuery ? "Try adjusting your search" : "Create your first document to get started"}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredDocuments.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center gap-4 p-4 rounded-xl bg-secondary/50 hover:bg-secondary transition-colors"
                  >
                    <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10">
                      <FileText className="h-6 w-6 text-accent" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-foreground truncate">{doc.title}</h4>
                        <Badge variant={getStatusColor(doc.status) as any}>{doc.status}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {doc.document_type.replace(/_/g, " ")} — {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => handleDownload(doc.id, "pdf")}
                        disabled={downloadPdf.isPending}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon-sm">
                        <Share2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        onClick={() => handleDelete(doc.id)}
                        disabled={deleteDocument.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
