/**
 * Payment Status Dialog Component
 *
 * Displays payment success, failure, or processing states.
 */

import { CheckCircle2, XCircle, Loader2, Download, ArrowRight } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Payment,
  PaymentStatus,
  formatPaymentAmount,
  getPaymentStatusLabel,
  getPaymentMethodLabel,
} from "@/lib/api/payment-api";

interface PaymentStatusDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  payment: Payment | null;
  status: "processing" | "success" | "failed";
  onViewPayment?: () => void;
  onViewInvoice?: () => void;
  onRetry?: () => void;
  onClose?: () => void;
}

export function PaymentStatusDialog({
  open,
  onOpenChange,
  payment,
  status,
  onViewPayment,
  onViewInvoice,
  onRetry,
  onClose,
}: PaymentStatusDialogProps) {
  const getStatusIcon = () => {
    switch (status) {
      case "success":
        return <CheckCircle2 className="h-16 w-16 text-green-500" />;
      case "failed":
        return <XCircle className="h-16 w-16 text-red-500" />;
      case "processing":
        return <Loader2 className="h-16 w-16 text-primary animate-spin" />;
    }
  };

  const getStatusTitle = () => {
    switch (status) {
      case "success":
        return "Payment Successful!";
      case "failed":
        return "Payment Failed";
      case "processing":
        return "Processing Payment...";
    }
  };

  const getStatusDescription = () => {
    switch (status) {
      case "success":
        return "Your payment has been processed successfully.";
      case "failed":
        return payment?.error_message || "Your payment could not be processed. Please try again.";
      case "processing":
        return "Please wait while we process your payment...";
    }
  };

  const handleClose = () => {
    onClose?.();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center space-y-4">
          <div className="flex justify-center">
            {getStatusIcon()}
          </div>
          <div>
            <DialogTitle className="text-2xl">{getStatusTitle()}</DialogTitle>
            <DialogDescription className="mt-2">
              {getStatusDescription()}
            </DialogDescription>
          </div>
        </DialogHeader>

        {payment && status !== "processing" && (
          <div className="space-y-4">
            <Separator />

            {/* Payment Details */}
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Amount Paid</span>
                <span className="font-semibold text-lg">
                  {formatPaymentAmount(payment.amount, payment.currency)}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Payment Method</span>
                <span className="text-sm">{getPaymentMethodLabel(payment.payment_method)}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Status</span>
                <Badge
                  variant={
                    payment.status === PaymentStatus.COMPLETED
                      ? "success"
                      : payment.status === PaymentStatus.FAILED
                      ? "destructive"
                      : "default"
                  }
                >
                  {getPaymentStatusLabel(payment.status)}
                </Badge>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Transaction ID</span>
                <span className="text-xs font-mono">{payment.id.slice(0, 12)}...</span>
              </div>

              {payment.completed_at && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Completed At</span>
                  <span className="text-sm">
                    {new Date(payment.completed_at).toLocaleString()}
                  </span>
                </div>
              )}
            </div>

            <Separator />

            {/* Actions */}
            <div className="space-y-2">
              {status === "success" && (
                <>
                  {onViewInvoice && payment.metadata?.invoice_id && (
                    <Button
                      onClick={onViewInvoice}
                      variant="default"
                      className="w-full"
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Download Invoice
                    </Button>
                  )}

                  {onViewPayment && (
                    <Button
                      onClick={onViewPayment}
                      variant="outline"
                      className="w-full"
                    >
                      View Payment Details
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  )}

                  <Button
                    onClick={handleClose}
                    variant="ghost"
                    className="w-full"
                  >
                    Close
                  </Button>
                </>
              )}

              {status === "failed" && (
                <>
                  {onRetry && (
                    <Button
                      onClick={onRetry}
                      variant="default"
                      className="w-full"
                    >
                      Try Again
                    </Button>
                  )}

                  <Button
                    onClick={handleClose}
                    variant="outline"
                    className="w-full"
                  >
                    Close
                  </Button>
                </>
              )}
            </div>

            {/* Error Details */}
            {status === "failed" && payment.error_code && (
              <div className="rounded-lg bg-destructive/10 p-3 text-sm">
                <p className="font-medium text-destructive">Error Code: {payment.error_code}</p>
                {payment.error_message && (
                  <p className="text-xs text-muted-foreground mt-1">{payment.error_message}</p>
                )}
              </div>
            )}
          </div>
        )}

        {status === "processing" && (
          <div className="text-center text-sm text-muted-foreground">
            This may take a few moments...
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
