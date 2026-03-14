import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useMarkInvoicePaid,
  PaymentMethod,
  type Invoice,
} from "@/lib/api/invoice-api";

interface MarkInvoicePaidDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  invoice: Invoice | null;
  onSuccess?: () => void;
}

const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  [PaymentMethod.CASH]: "Cash",
  [PaymentMethod.BANK_TRANSFER]: "Bank Transfer",
  [PaymentMethod.CREDIT_CARD]: "Credit Card",
  [PaymentMethod.MOBILE_MONEY]: "Mobile Money",
  [PaymentMethod.CHECK]: "Check",
  [PaymentMethod.OTHER]: "Other",
};

export function MarkInvoicePaidDialog({
  open,
  onOpenChange,
  invoice,
  onSuccess,
}: MarkInvoicePaidDialogProps) {
  const markPaid = useMarkInvoicePaid();

  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | "">("");
  const [paidAmount, setPaidAmount] = useState<number>(0);
  const [paidDate, setPaidDate] = useState("");
  const [notes, setNotes] = useState("");

  // Pre-fill when invoice changes or dialog opens
  useEffect(() => {
    if (open && invoice) {
      setPaidAmount(invoice.total_amount);
      setPaidDate(new Date().toISOString().split("T")[0]);
      setPaymentMethod("");
      setNotes("");
    }
  }, [open, invoice]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!invoice) return;

    if (!paymentMethod) {
      toast.error("Please select a payment method");
      return;
    }
    if (paidAmount <= 0) {
      toast.error("Paid amount must be greater than 0");
      return;
    }

    try {
      await markPaid.mutateAsync({
        invoiceId: invoice.id,
        paymentData: {
          payment_method: paymentMethod,
          paid_amount: paidAmount,
          paid_date: paidDate || undefined,
          notes: notes || undefined,
        },
      });

      toast.success(`Invoice ${invoice.invoice_number} marked as paid`);
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to mark invoice as paid"
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Mark Invoice as Paid</DialogTitle>
          <DialogDescription>
            {invoice && (
              <>
                Invoice <span className="font-mono font-medium">{invoice.invoice_number}</span>
                {" "}&mdash;{" "}
                <span className="font-semibold">
                  {invoice.currency} {invoice.total_amount.toLocaleString()}
                </span>
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Payment Method *</Label>
            <Select
              value={paymentMethod}
              onValueChange={(v) => setPaymentMethod(v as PaymentMethod)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select payment method" />
              </SelectTrigger>
              <SelectContent>
                {Object.values(PaymentMethod).map((method) => (
                  <SelectItem key={method} value={method}>
                    {PAYMENT_METHOD_LABELS[method]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Paid Amount *</Label>
            <Input
              type="number"
              min={0}
              step="0.01"
              value={paidAmount || ""}
              onChange={(e) => setPaidAmount(Number(e.target.value) || 0)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label>Paid Date</Label>
            <Input
              type="date"
              value={paidDate}
              onChange={(e) => setPaidDate(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Notes (optional)</Label>
            <Textarea
              placeholder="Payment notes..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={markPaid.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={markPaid.isPending}>
              {markPaid.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Processing...
                </>
              ) : (
                "Mark as Paid"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
