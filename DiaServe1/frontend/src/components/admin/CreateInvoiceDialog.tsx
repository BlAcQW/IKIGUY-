import { useState, useEffect, useMemo } from "react";
import { Plus, Trash2, Loader2 } from "lucide-react";
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
import { useCreateInvoice } from "@/lib/api/invoice-api";
import { useContacts } from "@/hooks/use-campaigns";
import { useProperties } from "@/hooks/use-properties";

interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
}

const EMPTY_LINE_ITEM: LineItem = {
  description: "",
  quantity: 1,
  unit_price: 0,
  tax_rate: 0,
};

interface CreateInvoiceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function CreateInvoiceDialog({
  open,
  onOpenChange,
  onSuccess,
}: CreateInvoiceDialogProps) {
  const createInvoice = useCreateInvoice();

  // Data hooks
  const { data: contactsData } = useContacts({ limit: 100 });
  const { data: propertiesData } = useProperties({ limit: 100 });

  // Form state
  const [contactId, setContactId] = useState("");
  const [propertyId, setPropertyId] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [currency, setCurrency] = useState("GHS");
  const [lineItems, setLineItems] = useState<LineItem[]>([{ ...EMPTY_LINE_ITEM }]);
  const [notes, setNotes] = useState("");
  const [terms, setTerms] = useState("");

  // Reset form when dialog closes
  useEffect(() => {
    if (!open) {
      setContactId("");
      setPropertyId("");
      setDueDate("");
      setCurrency("GHS");
      setLineItems([{ ...EMPTY_LINE_ITEM }]);
      setNotes("");
      setTerms("");
    }
  }, [open]);

  // Computed totals
  const totals = useMemo(() => {
    let subtotal = 0;
    let tax = 0;
    for (const item of lineItems) {
      const amount = item.quantity * item.unit_price;
      subtotal += amount;
      tax += amount * (item.tax_rate / 100);
    }
    return { subtotal, tax, total: subtotal + tax };
  }, [lineItems]);

  const contacts = contactsData?.contacts ?? [];
  const properties = propertiesData?.properties ?? [];

  const updateLineItem = (index: number, field: keyof LineItem, value: string | number) => {
    setLineItems((prev) =>
      prev.map((item, i) => (i === index ? { ...item, [field]: value } : item))
    );
  };

  const removeLineItem = (index: number) => {
    setLineItems((prev) => prev.filter((_, i) => i !== index));
  };

  const addLineItem = () => {
    setLineItems((prev) => [...prev, { ...EMPTY_LINE_ITEM }]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!contactId) {
      toast.error("Please select a contact");
      return;
    }
    if (!dueDate) {
      toast.error("Please set a due date");
      return;
    }
    if (lineItems.length === 0) {
      toast.error("At least one line item is required");
      return;
    }

    const hasInvalidItem = lineItems.some(
      (item) => !item.description.trim() || item.unit_price <= 0
    );
    if (hasInvalidItem) {
      toast.error("Each line item needs a description and a unit price greater than 0");
      return;
    }

    try {
      await createInvoice.mutateAsync({
        contact_id: contactId,
        property_id: propertyId || undefined,
        due_date: dueDate,
        currency,
        line_items: lineItems.map((item) => ({
          description: item.description,
          quantity: item.quantity,
          unit_price: item.unit_price,
          tax_rate: item.tax_rate || undefined,
        })),
        notes: notes || undefined,
        terms: terms || undefined,
      });

      toast.success("Invoice created successfully");
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to create invoice"
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Invoice</DialogTitle>
          <DialogDescription>
            Create a new invoice for a contact. Add line items and set payment terms.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Contact & Property */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Contact *</Label>
              <Select value={contactId} onValueChange={setContactId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a contact" />
                </SelectTrigger>
                <SelectContent>
                  {contacts.map((contact) => (
                    <SelectItem key={contact.id} value={contact.id}>
                      {contact.name}
                      {contact.email ? ` (${contact.email})` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Property (optional)</Label>
              <Select value={propertyId} onValueChange={setPropertyId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a property" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  {properties.map((property) => (
                    <SelectItem key={property.id} value={property.id}>
                      {property.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Due Date & Currency */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Due Date *</Label>
              <Input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label>Currency</Label>
              <Select value={currency} onValueChange={setCurrency}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GHS">GHS</SelectItem>
                  <SelectItem value="USD">USD</SelectItem>
                  <SelectItem value="EUR">EUR</SelectItem>
                  <SelectItem value="GBP">GBP</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Line Items */}
          <div className="space-y-3">
            <Label>Line Items *</Label>
            <div className="space-y-2">
              {/* Header row */}
              <div className="grid grid-cols-[1fr_80px_100px_80px_80px_40px] gap-2 text-xs font-medium text-muted-foreground px-1">
                <span>Description</span>
                <span>Qty</span>
                <span>Unit Price</span>
                <span>Tax %</span>
                <span>Amount</span>
                <span />
              </div>

              {lineItems.map((item, index) => {
                const amount = item.quantity * item.unit_price;
                return (
                  <div
                    key={index}
                    className="grid grid-cols-[1fr_80px_100px_80px_80px_40px] gap-2 items-center"
                  >
                    <Input
                      placeholder="Description"
                      value={item.description}
                      onChange={(e) => updateLineItem(index, "description", e.target.value)}
                    />
                    <Input
                      type="number"
                      min={1}
                      value={item.quantity}
                      onChange={(e) =>
                        updateLineItem(index, "quantity", Number(e.target.value) || 1)
                      }
                    />
                    <Input
                      type="number"
                      min={0}
                      step="0.01"
                      placeholder="0.00"
                      value={item.unit_price || ""}
                      onChange={(e) =>
                        updateLineItem(index, "unit_price", Number(e.target.value) || 0)
                      }
                    />
                    <Input
                      type="number"
                      min={0}
                      max={100}
                      step="0.1"
                      placeholder="0"
                      value={item.tax_rate || ""}
                      onChange={(e) =>
                        updateLineItem(index, "tax_rate", Number(e.target.value) || 0)
                      }
                    />
                    <span className="text-sm font-medium text-right tabular-nums">
                      {amount.toLocaleString(undefined, {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => removeLineItem(index)}
                      disabled={lineItems.length === 1}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                );
              })}
            </div>

            <Button
              type="button"
              variant="outline"
              size="sm"
              className="gap-1"
              onClick={addLineItem}
            >
              <Plus className="h-4 w-4" />
              Add Line Item
            </Button>
          </div>

          {/* Totals */}
          <div className="rounded-lg border p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Subtotal</span>
              <span className="font-medium tabular-nums">
                {currency}{" "}
                {totals.subtotal.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Tax</span>
              <span className="font-medium tabular-nums">
                {currency}{" "}
                {totals.tax.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
            <div className="flex justify-between text-base font-semibold border-t pt-2">
              <span>Total</span>
              <span className="tabular-nums">
                {currency}{" "}
                {totals.total.toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          </div>

          {/* Notes & Terms */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Notes (optional)</Label>
              <Textarea
                placeholder="Additional notes for the client..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label>Terms (optional)</Label>
              <Textarea
                placeholder="Payment terms and conditions..."
                value={terms}
                onChange={(e) => setTerms(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createInvoice.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createInvoice.isPending}>
              {createInvoice.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Creating...
                </>
              ) : (
                "Create Invoice"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
