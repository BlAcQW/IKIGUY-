import { useState } from 'react';
import {
  Plus,
  Search,
  Filter,
  Download,
  Send,
  MoreHorizontal,
  CheckCircle,
  Clock,
  AlertCircle,
  DollarSign,
  Loader2
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useInvoices, useInvoiceStats, InvoiceStatus, useDownloadInvoicePDF } from "@/lib/api/invoice-api";
import { toast } from "sonner";

export default function Invoices() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<InvoiceStatus[]>([]);

  // Fetch invoices and stats from backend
  const { data: invoicesData, isLoading: loadingInvoices } = useInvoices({
    search: searchQuery || undefined,
    status: statusFilter.length > 0 ? statusFilter : undefined,
    limit: 20,
    sort_by: 'created_at',
    sort_order: 'desc',
  });

  const { data: stats, isLoading: loadingStats } = useInvoiceStats('GHS');

  // PDF download mutation
  const downloadPDF = useDownloadInvoicePDF();
  const getStatusInfo = (status: string) => {
    switch (status) {
      case "paid":
        return { color: "success", icon: CheckCircle };
      case "pending":
        return { color: "warning", icon: Clock };
      case "overdue":
        return { color: "destructive", icon: AlertCircle };
      default:
        return { color: "muted", icon: Clock };
    }
  };

  return (
    <div className="min-h-screen">
      <Header 
        title="Invoices" 
        subtitle="Track payments and billing"
        actions={
          <Button variant="accent" className="gap-2">
            <Plus className="h-4 w-4" />
            Create Invoice
          </Button>
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

        {/* Search */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search invoices..."
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

        {/* Invoices List */}
        <Card>
          <CardHeader>
            <CardTitle>All Invoices</CardTitle>
            <CardDescription>Payment tracking and history</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Invoice</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Client</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Property</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Amount</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Due Date</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingInvoices ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center">
                        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mx-auto" />
                      </td>
                    </tr>
                  ) : invoicesData && invoicesData.invoices.length > 0 ? (
                    invoicesData.invoices.map((invoice) => {
                      const statusInfo = getStatusInfo(invoice.status);
                      const dueDate = new Date(invoice.due_date).toLocaleDateString();

                      return (
                        <tr key={invoice.id} className="border-b border-border hover:bg-secondary/50 transition-colors">
                          <td className="py-4 px-4">
                            <span className="font-mono font-medium text-foreground">{invoice.invoice_number}</span>
                          </td>
                          <td className="py-4 px-4 text-foreground">{invoice.contact_name}</td>
                          <td className="py-4 px-4 text-muted-foreground">{invoice.property_name || 'N/A'}</td>
                          <td className="py-4 px-4 font-semibold text-foreground">
                            {invoice.currency} {invoice.total_amount.toLocaleString()}
                          </td>
                          <td className="py-4 px-4 text-muted-foreground">{dueDate}</td>
                          <td className="py-4 px-4">
                            <Badge variant={statusInfo.color as any} className="gap-1">
                              <statusInfo.icon className="h-3 w-3" />
                              {invoice.status}
                            </Badge>
                          </td>
                          <td className="py-4 px-4">
                            <div className="flex items-center gap-2">
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => {
                                  downloadPDF.mutate(invoice.id, {
                                    onSuccess: () => {
                                      toast.success(`Invoice ${invoice.invoice_number} downloaded`);
                                    },
                                    onError: (error) => {
                                      toast.error(`Failed to download PDF: ${error.message}`);
                                    }
                                  });
                                }}
                                disabled={downloadPDF.isPending}
                              >
                                {downloadPDF.isPending ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Download className="h-4 w-4" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => toast.info("Email sending coming soon!")}
                              >
                                <Send className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="icon-sm">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-muted-foreground">
                        No invoices found. Create your first invoice to get started.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
