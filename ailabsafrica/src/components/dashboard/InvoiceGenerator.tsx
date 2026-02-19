import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { FileText, Download, Mail, Printer } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';

interface InvoiceGeneratorProps {
  transaction: any;
  onClose?: () => void;
}

interface InvoiceData {
  invoiceNumber: string;
  date: string;
  dueDate: string;
  customer: {
    name: string;
    email: string;
    phone?: string;
    company?: string;
  };
  items: Array<{
    description: string;
    quantity: number;
    unitPrice: number;
    amount: number;
  }>;
  subtotal: number;
  tax: number;
  total: number;
  status: string;
}

const InvoiceGenerator: React.FC<InvoiceGeneratorProps> = ({ transaction, onClose }) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [isGenerating, setIsGenerating] = useState(false);

  const generateInvoiceNumber = (): string => {
    const date = new Date();
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `INV-${year}${month}${day}-${random}`;
  };

  const createInvoiceData = (): InvoiceData => {
    const invoiceNumber = generateInvoiceNumber();
    const date = new Date().toISOString().split('T')[0];
    const dueDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    return {
      invoiceNumber,
      date,
      dueDate,
      customer: {
        name: user?.user_metadata?.full_name || user?.email || 'Customer',
        email: user?.email || '',
        phone: user?.user_metadata?.phone || '',
        company: user?.user_metadata?.company_name || ''
      },
      items: [
        {
          description: `Wallet Top Up - ${transaction.payment_method.toUpperCase()}`,
          quantity: 1,
          unitPrice: transaction.amount,
          amount: transaction.amount
        }
      ],
      subtotal: transaction.amount,
      tax: 0, // No tax for wallet top-ups
      total: transaction.amount,
      status: transaction.status
    };
  };

  const generateInvoicePDF = async (invoiceData: InvoiceData) => {
    setIsGenerating(true);
    
    try {
      // Call edge function to generate PDF
      const { data, error } = await supabase.functions.invoke('generate-invoice', {
        body: {
          invoiceData,
          transactionId: transaction.transaction_id
        }
      });

      if (error) throw error;

      if (data.pdfUrl) {
        // Download the PDF
        const link = document.createElement('a');
        link.href = data.pdfUrl;
        link.download = `invoice-${invoiceData.invoiceNumber}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        toast({
          title: "Invoice Generated",
          description: "Your invoice has been generated and downloaded successfully.",
        });
      }
    } catch (error: any) {
      console.error('Error generating invoice:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to generate invoice.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const sendInvoiceEmail = async (invoiceData: InvoiceData) => {
    setIsGenerating(true);
    
    try {
      const { error } = await supabase.functions.invoke('send-invoice-email', {
        body: {
          invoiceData,
          transactionId: transaction.transaction_id,
          customerEmail: invoiceData.customer.email
        }
      });

      if (error) throw error;

      toast({
        title: "Invoice Sent",
        description: "Invoice has been sent to your email address.",
      });
    } catch (error: any) {
      console.error('Error sending invoice:', error);
      toast({
        title: "Error",
        description: error.message || "Failed to send invoice email.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const printInvoice = (invoiceData: InvoiceData) => {
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const invoiceHTML = `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Invoice ${invoiceData.invoiceNumber}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .invoice-details { margin-bottom: 20px; }
            .customer-details { margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .total { text-align: right; font-weight: bold; }
            @media print { body { margin: 0; } }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>AI Labs Africa</h1>
            <h2>INVOICE</h2>
          </div>
          
          <div class="invoice-details">
            <p><strong>Invoice Number:</strong> ${invoiceData.invoiceNumber}</p>
            <p><strong>Date:</strong> ${invoiceData.date}</p>
            <p><strong>Due Date:</strong> ${invoiceData.dueDate}</p>
            <p><strong>Status:</strong> ${invoiceData.status.toUpperCase()}</p>
          </div>
          
          <div class="customer-details">
            <h3>Bill To:</h3>
            <p>${invoiceData.customer.name}</p>
            ${invoiceData.customer.company ? `<p>${invoiceData.customer.company}</p>` : ''}
            <p>${invoiceData.customer.email}</p>
            ${invoiceData.customer.phone ? `<p>${invoiceData.customer.phone}</p>` : ''}
          </div>
          
          <table>
            <thead>
              <tr>
                <th>Description</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              ${invoiceData.items.map(item => `
                <tr>
                  <td>${item.description}</td>
                  <td>${item.quantity}</td>
                  <td>$${item.unitPrice.toFixed(2)}</td>
                  <td>$${item.amount.toFixed(2)}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
          
          <div class="total">
            <p>Subtotal: $${invoiceData.subtotal.toFixed(2)}</p>
            <p>Tax: $${invoiceData.tax.toFixed(2)}</p>
            <p>Total: $${invoiceData.total.toFixed(2)}</p>
          </div>
          
          <div style="margin-top: 40px; text-align: center;">
            <p>Thank you for your business!</p>
            <p>AI Labs Africa</p>
          </div>
        </body>
      </html>
    `;

    printWindow.document.write(invoiceHTML);
    printWindow.document.close();
    printWindow.print();
  };

  const invoiceData = createInvoiceData();

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Invoice Generator
        </CardTitle>
        <CardDescription>
          Generate and manage invoices for your transactions
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Invoice Preview */}
        <div className="border rounded-lg p-4 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-semibold">Invoice Preview</h3>
            <Badge variant={transaction.status === 'completed' ? 'default' : 'secondary'}>
              {transaction.status.toUpperCase()}
            </Badge>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Invoice Number</p>
              <p className="font-medium">{invoiceData.invoiceNumber}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Date</p>
              <p className="font-medium">{invoiceData.date}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Customer</p>
              <p className="font-medium">{invoiceData.customer.name}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Amount</p>
              <p className="font-medium">${transaction.amount.toFixed(2)}</p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3">
          <Button 
            onClick={() => generateInvoicePDF(invoiceData)}
            disabled={isGenerating}
            className="flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            Download PDF
          </Button>
          
          <Button 
            onClick={() => sendInvoiceEmail(invoiceData)}
            disabled={isGenerating}
            variant="outline"
            className="flex items-center gap-2"
          >
            <Mail className="h-4 w-4" />
            Send Email
          </Button>
          
          <Button 
            onClick={() => printInvoice(invoiceData)}
            disabled={isGenerating}
            variant="outline"
            className="flex items-center gap-2"
          >
            <Printer className="h-4 w-4" />
            Print
          </Button>
          
          {onClose && (
            <Button 
              onClick={onClose}
              variant="ghost"
            >
              Close
            </Button>
          )}
        </div>

        {isGenerating && (
          <div className="text-center text-sm text-muted-foreground">
            Generating invoice...
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default InvoiceGenerator;
