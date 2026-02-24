import { useState, useMemo } from "react";
import {
  Plus,
  Search,
  Download,
  Send,
  MoreHorizontal,
  CheckCircle,
  Clock,
  AlertCircle,
  DollarSign,
  Loader2,
  RefreshCw,
  Trash2,
  CreditCard,
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  useInvoices,
  useInvoiceStats,
  useDownloadInvoicePDF,
  useSendInvoice,
  useDeleteInvoice,
  InvoiceStatus,
  type Invoice,
  type InvoiceFilters,
} from "@/lib/api/invoice-api";
import { toast } from "sonner";
import { CreateInvoiceDialog } from "@/components/admin/CreateInvoiceDialog";
import { MarkInvoicePaidDialog } from "@/components/admin/MarkInvoicePaidDialog";
import {
  useQBOStatus,
  useQBOSync,
  useQBOSyncInvoice,
  getQBOAuthUrl,
} from "@/lib/api/quickbooks-api";

const PAGE_SIZE = 20;

const getStatusInfo = (status: string) => {
  switch (status) {
    case "paid":
      return { color: "success", icon: CheckCircle };
    case "sent":
      return { color: "warning", icon: Clock };
    case "overdue":
      return { color: "destructive", icon: AlertCircle };
    case "draft":
      return { color: "muted", icon: Clock };
    case "cancelled":
      return { color: "outline", icon: AlertCircle };
    default:
      return { color: "muted", icon: Clock };
  }
};

export default function Invoices() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [page, setPage] = useState(1);

  // Dialog state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [markPaidDialogOpen, setMarkPaidDialogOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  // Build filters
  const filters = useMemo<InvoiceFilters>(() => {
    const f: InvoiceFilters = {
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
      sort_by: "created_at",
      sort_order: "desc",
    };
    if (searchQuery) f.search = searchQuery;
    if (statusFilter !== "all") f.status = [statusFilter as InvoiceStatus];
    return f;
  }, [searchQuery, statusFilter, page]);

  // Data hooks
  const { data: invoicesData, isLoading: loadingInvoices } = useInvoices(filters);
  const { data: stats, isLoading: loadingStats } = useInvoiceStats("GHS");

  // Mutation hooks
  const downloadPDF = useDownloadInvoicePDF();
  const sendInvoice = useSendInvoice();
  const deleteInvoice = useDeleteInvoice();

  // QuickBooks hooks
  const { data: qboStatus } = useQBOStatus();
  const qboSync = useQBOSync();
  const qboSyncInvoice = useQBOSyncInvoice();

  const invoices = invoicesData?.invoices ?? [];
  const totalPages = invoicesData ? Math.ceil(invoicesData.total / PAGE_SIZE) : 1;

  // Reset page on filter changes
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    setPage(1);
  };

  const handleStatusChange = (value: string) => {
    setStatusFilter(value);
    setPage(1);
  };

  const handleSendInvoice = (invoice: Invoice) => {
    sendInvoice.mutate(invoice.id, {
      onSuccess: () => {
        toast.success(`Invoice ${invoice.invoice_number} sent successfully`);
      },
      onError: (error) => {
        toast.error(`Failed to send invoice: ${error.message}`);
      },
    });
  };

  const handleDeleteInvoice = (invoice: Invoice) => {
    if (!window.confirm(`Delete invoice ${invoice.invoice_number}? This cannot be undone.`)) {
      return;
    }
    deleteInvoice.mutate(invoice.id, {
      onSuccess: () => {
        toast.success(`Invoice ${invoice.invoice_number} deleted`);
      },
      onError: (error) => {
        toast.error(`Failed to delete invoice: ${error.message}`);
      },
    });
  };

  const handleMarkPaid = (invoice: Invoice) => {
    setSelectedInvoice(invoice);
    setMarkPaidDialogOpen(true);
  };

  return (
    <div className="min-h-screen">
      <Header
        title="Invoices"
        subtitle="Track payments and billing"
        actions={
          <div className="flex gap-2">
            {qboStatus?.is_connected ? (
              <Button
                variant="outline"
                className="gap-2 border-emerald-600 text-emerald-600 hover:bg-emerald-50"
                disabled={qboSync.isPending}
                onClick={() => {
                  qboSync.mutate(undefined, {
                    onSuccess: (result) => {
                      if (result.failed > 0) {
                        toast.warning(
                          `Synced ${result.synced} invoice(s), ${result.failed} failed`
                        );
                      } else if (result.synced > 0) {
                        toast.success(
                          `${result.synced} invoice(s) synced to QuickBooks`
                        );
                      } else {
                        toast.info("All invoices are already synced");
                      }
                    },
                    onError: (error) => {
                      toast.error(`Sync failed: ${error.message}`);
                    },
                  });
                }}
              >
                {qboSync.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Sync QuickBooks
              </Button>
            ) : (
              <Button
                variant="outline"
                className="gap-2 border-emerald-600 text-emerald-600 hover:bg-emerald-50"
                onClick={async () => {
                  try {
                    const { auth_url } = await getQBOAuthUrl();
                    window.location.href = auth_url;
                  } catch (error: any) {
                    toast.error(error.message || "Failed to connect QuickBooks");
                  }
                }}
              >
                <RefreshCw className="h-4 w-4" />
                Connect QuickBooks
              </Button>
            )}
            <Button
              variant="accent"
              className="gap-2"
              onClick={() => setCreateDialogOpen(true)}
            >
              <Plus className="h-4 w-4" />
              Create Invoice
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Stats */}
        {loadingStats ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : stats ? (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <DollarSign className="h-8 w-8 text-success" />
                </div>
                <p className="text-2xl font-bold text-foreground mt-4">
                  {stats.currency} {stats.total_revenue.toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">Total Revenue</p>
                <p className="text-xs text-muted-foreground mt-1">{stats.paid_count} paid</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <DollarSign className="h-8 w-8 text-accent" />
                </div>
                <p className="text-2xl font-bold text-foreground mt-4">
                  {stats.currency} {stats.pending_amount.toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">Pending</p>
                <p className="text-xs text-muted-foreground mt-1">{stats.sent_count} invoices</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <DollarSign className="h-8 w-8 text-destructive" />
                </div>
                <p className="text-2xl font-bold text-foreground mt-4">
                  {stats.currency} {stats.overdue_amount.toLocaleString()}
                </p>
                <p className="text-sm text-muted-foreground">Overdue</p>
                <p className="text-xs text-muted-foreground mt-1">{stats.overdue_count} invoices</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <DollarSign className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-2xl font-bold text-foreground mt-4">{stats.total_invoices}</p>
                <p className="text-sm text-muted-foreground">Total Invoices</p>
                <p className="text-xs text-muted-foreground mt-1">{stats.draft_count} drafts</p>
              </CardContent>
            </Card>
          </div>
        ) : null}

        {/* Search & Filters */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search invoices..."
              className="pl-9"
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
            />
          </div>
          <Select value={statusFilter} onValueChange={handleStatusChange}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value={InvoiceStatus.DRAFT}>Draft</SelectItem>
              <SelectItem value={InvoiceStatus.SENT}>Sent</SelectItem>
              <SelectItem value={InvoiceStatus.PAID}>Paid</SelectItem>
              <SelectItem value={InvoiceStatus.OVERDUE}>Overdue</SelectItem>
              <SelectItem value={InvoiceStatus.CANCELLED}>Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Invoices Table */}
        <Card>
          <CardHeader>
            <CardTitle>All Invoices</CardTitle>
            <CardDescription>
              {invoicesData
                ? `${invoicesData.total} invoice${invoicesData.total !== 1 ? "s" : ""} found`
                : "Payment tracking and history"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingInvoices ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : invoices.length === 0 ? (
              <div className="text-center py-12">
                <CreditCard className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No Invoices Found</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {searchQuery || statusFilter !== "all"
                    ? "Try adjusting your filters"
                    : "Create your first invoice to get started"}
                </p>
                <Button onClick={() => setCreateDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Invoice
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invoice</TableHead>
                      <TableHead>Client</TableHead>
                      <TableHead>Property</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Due Date</TableHead>
                      <TableHead>Status</TableHead>
                      {qboStatus?.is_connected && (
                        <TableHead>QBO Sync</TableHead>
                      )}
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices.map((invoice) => {
                      const statusInfo = getStatusInfo(invoice.status);
                      const dueDate = new Date(invoice.due_date).toLocaleDateString();
                      const canSend =
                        invoice.status === InvoiceStatus.DRAFT ||
                        invoice.status === InvoiceStatus.SENT ||
                        invoice.status === InvoiceStatus.OVERDUE;
                      const canMarkPaid =
                        invoice.status === InvoiceStatus.SENT ||
                        invoice.status === InvoiceStatus.OVERDUE;
                      const canDelete = invoice.status === InvoiceStatus.DRAFT;

                      return (
                        <TableRow key={invoice.id}>
                          <TableCell>
                            <span className="font-mono font-medium text-foreground">
                              {invoice.invoice_number}
                            </span>
                          </TableCell>
                          <TableCell>{invoice.contact_name}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {invoice.property_name || "N/A"}
                          </TableCell>
                          <TableCell className="font-semibold">
                            {invoice.currency} {invoice.total_amount.toLocaleString()}
                          </TableCell>
                          <TableCell className="text-muted-foreground">{dueDate}</TableCell>
                          <TableCell>
                            <Badge variant={statusInfo.color as any} className="gap-1">
                              <statusInfo.icon className="h-3 w-3" />
                              {invoice.status}
                            </Badge>
                          </TableCell>
                          {qboStatus?.is_connected && (
                            <TableCell>
                              {invoice.qbo_sync_status === "synced" ? (
                                <Badge variant="success" className="gap-1">
                                  <CheckCircle className="h-3 w-3" />
                                  Synced
                                </Badge>
                              ) : invoice.qbo_sync_status === "error" ? (
                                <Badge variant="destructive" className="gap-1" title={invoice.qbo_sync_error || "Sync error"}>
                                  <AlertCircle className="h-3 w-3" />
                                  Error
                                </Badge>
                              ) : (
                                <Badge variant="outline" className="gap-1 text-muted-foreground">
                                  <Clock className="h-3 w-3" />
                                  Not synced
                                </Badge>
                              )}
                            </TableCell>
                          )}
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => {
                                  downloadPDF.mutate(invoice.id, {
                                    onSuccess: () => {
                                      toast.success(
                                        `Invoice ${invoice.invoice_number} downloaded`
                                      );
                                    },
                                    onError: (error) => {
                                      toast.error(
                                        `Failed to download PDF: ${error.message}`
                                      );
                                    },
                                  });
                                }}
                                disabled={downloadPDF.isPending}
                                title="Download PDF"
                              >
                                {downloadPDF.isPending ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Download className="h-4 w-4" />
                                )}
                              </Button>

                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon-sm">
                                    <MoreHorizontal className="h-4 w-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  {canSend && (
                                    <DropdownMenuItem
                                      onClick={() => handleSendInvoice(invoice)}
                                      disabled={sendInvoice.isPending}
                                    >
                                      <Send className="h-4 w-4 mr-2" />
                                      Send Invoice
                                    </DropdownMenuItem>
                                  )}
                                  {canMarkPaid && (
                                    <DropdownMenuItem
                                      onClick={() => handleMarkPaid(invoice)}
                                    >
                                      <CheckCircle className="h-4 w-4 mr-2" />
                                      Mark as Paid
                                    </DropdownMenuItem>
                                  )}
                                  {qboStatus?.is_connected &&
                                    invoice.qbo_sync_status !== "synced" &&
                                    invoice.status !== InvoiceStatus.DRAFT && (
                                    <DropdownMenuItem
                                      onClick={() => {
                                        qboSyncInvoice.mutate(invoice.id, {
                                          onSuccess: () => {
                                            toast.success(
                                              `Invoice ${invoice.invoice_number} synced to QuickBooks`
                                            );
                                          },
                                          onError: (error) => {
                                            toast.error(
                                              `Sync failed: ${error.message}`
                                            );
                                          },
                                        });
                                      }}
                                      disabled={qboSyncInvoice.isPending}
                                    >
                                      <RefreshCw className="h-4 w-4 mr-2" />
                                      Sync to QuickBooks
                                    </DropdownMenuItem>
                                  )}
                                  {canDelete && (
                                    <DropdownMenuItem
                                      onClick={() => handleDeleteInvoice(invoice)}
                                      className="text-destructive focus:text-destructive"
                                    >
                                      <Trash2 className="h-4 w-4 mr-2" />
                                      Delete
                                    </DropdownMenuItem>
                                  )}
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        )}
      </div>

      {/* Dialogs */}
      <CreateInvoiceDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
      <MarkInvoicePaidDialog
        open={markPaidDialogOpen}
        onOpenChange={setMarkPaidDialogOpen}
        invoice={selectedInvoice}
      />
    </div>
  );
}
