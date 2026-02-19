/**
 * Payments Page
 *
 * Displays payment history with filtering, search, and stats.
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Search,
  Filter,
  Download,
  Eye,
  RefreshCw,
  Loader2,
  TrendingUp,
  DollarSign,
  CreditCard,
  CheckCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  listPayments,
  getPaymentStats,
  Payment,
  PaymentStats,
  PaymentStatus,
  PaymentMethod,
  PaymentGateway,
  formatPaymentAmount,
  getPaymentStatusLabel,
  getPaymentMethodLabel,
  getPaymentGatewayLabel,
} from "@/lib/api/payment-api";

export default function Payments() {
  const navigate = useNavigate();
  const { toast } = useToast();

  // Data state
  const [payments, setPayments] = useState<Payment[]>([]);
  const [stats, setStats] = useState<PaymentStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [methodFilter, setMethodFilter] = useState<string>("all");
  const [gatewayFilter, setGatewayFilter] = useState<string>("all");

  // Pagination state
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 20;

  // Load payments and stats
  const loadData = async (showRefreshing = false) => {
    if (showRefreshing) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    try {
      // Build filters
      const filters: Record<string, any> = {};
      if (statusFilter !== "all") filters.status = statusFilter;
      if (methodFilter !== "all") filters.payment_method = methodFilter;
      if (gatewayFilter !== "all") filters.gateway = gatewayFilter;
      if (searchQuery) filters.search = searchQuery;

      // Load payments
      const paymentsData = await listPayments(page, pageSize, filters);
      setPayments(paymentsData);

      // Calculate total pages (mock for now - API should return total count)
      setTotalPages(Math.ceil(paymentsData.length / pageSize));

      // Load stats
      const statsData = await getPaymentStats();
      setStats(statsData);
    } catch (error: any) {
      console.error("Failed to load payments:", error);
      toast({
        title: "Error",
        description: error.message || "Failed to load payments",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  // Load data on mount and when filters change
  useEffect(() => {
    loadData();
  }, [page, statusFilter, methodFilter, gatewayFilter]);

  // Search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery) {
        setPage(1);
        loadData();
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleRefresh = () => {
    loadData(true);
  };

  const handleViewPayment = (paymentId: string) => {
    navigate(`/payments/${paymentId}`);
  };

  const handleNewPayment = () => {
    navigate("/payments/new");
  };

  const getStatusBadgeVariant = (status: PaymentStatus): "default" | "success" | "destructive" | "outline" => {
    switch (status) {
      case PaymentStatus.COMPLETED:
        return "success";
      case PaymentStatus.FAILED:
      case PaymentStatus.CANCELLED:
        return "destructive";
      case PaymentStatus.PENDING:
      case PaymentStatus.PROCESSING:
        return "default";
      case PaymentStatus.REFUNDED:
      case PaymentStatus.PARTIALLY_REFUNDED:
        return "outline";
      default:
        return "default";
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20 md:pb-0">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Payments</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Manage and track all your payment transactions
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button onClick={handleNewPayment}>
              <Plus className="h-4 w-4 mr-2" />
              New Payment
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Revenue
                </CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatPaymentAmount(stats.total_amount, stats.currency || "GHS")}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.total_count} transactions
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Completed
                </CardTitle>
                <CheckCircle className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatPaymentAmount(stats.completed_amount, stats.currency || "GHS")}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.completed_count} payments
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Pending
                </CardTitle>
                <CreditCard className="h-4 w-4 text-yellow-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {formatPaymentAmount(stats.pending_amount, stats.currency || "GHS")}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.pending_count} payments
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Success Rate
                </CardTitle>
                <TrendingUp className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats.total_count > 0
                    ? Math.round((stats.completed_count / stats.total_count) * 100)
                    : 0}%
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.completed_count} of {stats.total_count}
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Filter Payments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by description, ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value={PaymentStatus.COMPLETED}>Completed</SelectItem>
                  <SelectItem value={PaymentStatus.PENDING}>Pending</SelectItem>
                  <SelectItem value={PaymentStatus.PROCESSING}>Processing</SelectItem>
                  <SelectItem value={PaymentStatus.FAILED}>Failed</SelectItem>
                  <SelectItem value={PaymentStatus.CANCELLED}>Cancelled</SelectItem>
                  <SelectItem value={PaymentStatus.REFUNDED}>Refunded</SelectItem>
                </SelectContent>
              </Select>

              <Select value={methodFilter} onValueChange={setMethodFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Payment Method" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Methods</SelectItem>
                  <SelectItem value={PaymentMethod.CARD}>Card</SelectItem>
                  <SelectItem value={PaymentMethod.MOBILE_MONEY}>Mobile Money</SelectItem>
                  <SelectItem value={PaymentMethod.BANK_TRANSFER}>Bank Transfer</SelectItem>
                  <SelectItem value={PaymentMethod.CASH}>Cash</SelectItem>
                  <SelectItem value={PaymentMethod.CHECK}>Check</SelectItem>
                </SelectContent>
              </Select>

              <Select value={gatewayFilter} onValueChange={setGatewayFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Gateway" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Gateways</SelectItem>
                  <SelectItem value={PaymentGateway.STRIPE}>Stripe</SelectItem>
                  <SelectItem value={PaymentGateway.FLUTTERWAVE}>Flutterwave</SelectItem>
                  <SelectItem value={PaymentGateway.PAYSTACK}>Paystack</SelectItem>
                  <SelectItem value={PaymentGateway.MANUAL}>Manual</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Payments Table */}
        <Card>
          <CardHeader>
            <CardTitle>Payment History</CardTitle>
            <CardDescription>
              {payments.length} payment{payments.length !== 1 ? "s" : ""} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            {payments.length === 0 ? (
              <div className="text-center py-12">
                <CreditCard className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No Payments Found</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {searchQuery || statusFilter !== "all" || methodFilter !== "all"
                    ? "Try adjusting your filters"
                    : "Create your first payment to get started"}
                </p>
                <Button onClick={handleNewPayment}>
                  <Plus className="h-4 w-4 mr-2" />
                  New Payment
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Method</TableHead>
                      <TableHead>Gateway</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payments.map((payment) => (
                      <TableRow key={payment.id}>
                        <TableCell className="text-sm">
                          {new Date(payment.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <div className="max-w-[200px]">
                            <p className="font-medium truncate">{payment.description}</p>
                            <p className="text-xs text-muted-foreground">
                              ID: {payment.id.slice(0, 8)}...
                            </p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <p className="text-sm">{payment.customer_name}</p>
                        </TableCell>
                        <TableCell className="font-semibold">
                          {formatPaymentAmount(payment.amount, payment.currency)}
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {getPaymentMethodLabel(payment.payment_method)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm">
                            {getPaymentGatewayLabel(payment.gateway)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge variant={getStatusBadgeVariant(payment.status)}>
                            {getPaymentStatusLabel(payment.status)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewPayment(payment.id)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
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
    </div>
  );
}
