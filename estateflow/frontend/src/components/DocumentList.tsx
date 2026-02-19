/**
 * DocumentList Component
 *
 * Displays list of documents with status indicators and actions.
 */

import { useState } from "react";
import {
  FileText,
  MoreVertical,
  Download,
  Send,
  Edit,
  Trash2,
  Calendar,
  User,
  CheckCircle2,
  Clock,
  XCircle,
} from "lucide-react";
import { useDocuments, useDeleteDocument, useDownloadPdf } from "../hooks/use-documents";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Skeleton } from "./ui/skeleton";
import { useToast } from "./ui/use-toast";
import type { DocumentStatus, DocumentFilters } from "../lib/api/document-api";

interface DocumentListProps {
  filters?: DocumentFilters;
  onEditDocument?: (documentId: string) => void;
  onViewDocument?: (documentId: string) => void;
}

export function DocumentList({
  filters,
  onEditDocument,
  onViewDocument,
}: DocumentListProps) {
  const { toast } = useToast();
  const { data, isLoading, error } = useDocuments(filters);
  const deleteMutation = useDeleteDocument();
  const downloadPdfMutation = useDownloadPdf();

  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleDelete = async (documentId: string, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"?`)) return;

    setActionLoading(documentId);
    try {
      await deleteMutation.mutateAsync(documentId);
      toast({
        title: "Success",
        description: "Document deleted successfully",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to delete document",
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleDownloadPdf = async (documentId: string) => {
    setActionLoading(documentId);
    try {
      await downloadPdfMutation.mutateAsync(documentId);
      toast({
        title: "Success",
        description: "PDF download started",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to download PDF",
        variant: "destructive",
      });
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: DocumentStatus) => {
    const config: Record<
      DocumentStatus,
      { variant: any; icon: any; label: string }
    > = {
      draft: {
        variant: "secondary",
        icon: Edit,
        label: "Draft",
      },
      pending_review: {
        variant: "outline",
        icon: Clock,
        label: "Pending Review",
      },
      ready: {
        variant: "default",
        icon: CheckCircle2,
        label: "Ready",
      },
      sent: {
        variant: "default",
        icon: Send,
        label: "Sent",
      },
      signed: {
        variant: "success",
        icon: CheckCircle2,
        label: "Signed",
      },
      expired: {
        variant: "warning",
        icon: Clock,
        label: "Expired",
      },
      cancelled: {
        variant: "destructive",
        icon: XCircle,
        label: "Cancelled",
      },
    };

    const { variant, icon: Icon, label } = config[status] || config.draft;

    return (
      <Badge variant={variant} className="flex items-center gap-1 w-fit">
        <Icon className="h-3 w-3" />
        {label}
      </Badge>
    );
  };

  const getDocumentTypeLabel = (type: string) => {
    return type
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (error) {
    return (
      <div className="text-center py-12 text-red-600">
        <p>Failed to load documents</p>
        <p className="text-sm text-gray-500">{error.message}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (!data || data.documents.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <FileText className="h-12 w-12 mx-auto mb-4 opacity-20" />
        <p className="text-lg font-medium">No documents found</p>
        <p className="text-sm">
          {filters
            ? "Try adjusting your filters"
            : "Create your first document to get started"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Document</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Parties</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Version</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.documents.map((document) => (
              <TableRow key={document.id}>
                <TableCell>
                  <div
                    className="flex items-center gap-2 cursor-pointer hover:text-blue-600"
                    onClick={() => onViewDocument?.(document.id)}
                  >
                    <FileText className="h-4 w-4 text-gray-400" />
                    <div>
                      <div className="font-medium">{document.title}</div>
                      {document.description && (
                        <div className="text-sm text-gray-500 line-clamp-1">
                          {document.description}
                        </div>
                      )}
                    </div>
                  </div>
                </TableCell>

                <TableCell>
                  <Badge variant="outline">
                    {getDocumentTypeLabel(document.document_type)}
                  </Badge>
                </TableCell>

                <TableCell>{getStatusBadge(document.status)}</TableCell>

                <TableCell>
                  <div className="flex flex-col gap-1">
                    {document.parties.slice(0, 2).map((party, index) => (
                      <div key={index} className="flex items-center gap-1 text-sm">
                        <User className="h-3 w-3 text-gray-400" />
                        <span className="text-gray-600">
                          {party.name}
                          {party.signature_status === "signed" && (
                            <CheckCircle2 className="h-3 w-3 inline ml-1 text-green-600" />
                          )}
                        </span>
                      </div>
                    ))}
                    {document.parties.length > 2 && (
                      <span className="text-xs text-gray-500">
                        +{document.parties.length - 2} more
                      </span>
                    )}
                  </div>
                </TableCell>

                <TableCell>
                  <div className="flex items-center gap-1 text-sm text-gray-600">
                    <Calendar className="h-3 w-3 text-gray-400" />
                    {formatDate(document.created_at)}
                  </div>
                </TableCell>

                <TableCell>
                  <Badge variant="secondary" className="text-xs">
                    v{document.version}
                  </Badge>
                </TableCell>

                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={actionLoading === document.id}
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onViewDocument?.(document.id)}>
                        <FileText className="h-4 w-4 mr-2" />
                        View Details
                      </DropdownMenuItem>

                      {document.status === "draft" && (
                        <DropdownMenuItem onClick={() => onEditDocument?.(document.id)}>
                          <Edit className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                      )}

                      <DropdownMenuSeparator />

                      <DropdownMenuItem
                        onClick={() => handleDownloadPdf(document.id)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download PDF
                      </DropdownMenuItem>

                      {["ready", "sent"].includes(document.status) && (
                        <DropdownMenuItem>
                          <Send className="h-4 w-4 mr-2" />
                          Send for Signature
                        </DropdownMenuItem>
                      )}

                      <DropdownMenuSeparator />

                      {document.status === "draft" && (
                        <DropdownMenuItem
                          onClick={() => handleDelete(document.id, document.title)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Info */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div>
          Showing <span className="font-medium">{data.documents.length}</span> of{" "}
          <span className="font-medium">{data.total}</span> documents
        </div>
        {data.total > data.limit && (
          <div>
            Page {Math.floor(data.offset / data.limit) + 1} of{" "}
            {Math.ceil(data.total / data.limit)}
          </div>
        )}
      </div>
    </div>
  );
}
