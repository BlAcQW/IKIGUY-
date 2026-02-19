/**
 * Diaserve Properties Help & Documentation Page
 *
 * User guides, FAQs, and support resources.
 */

import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import {
  Building,
  Phone,
  MessageSquare,
  Mail,
  Users,
  FileText,
  CreditCard,
  BookOpen,
  ExternalLink,
  MessageCircle,
} from "lucide-react";

export default function Help() {
  return (
    <div className="min-h-screen">
      <Header
        title="Help & Support"
        subtitle="Get help with Diaserve Properties features and troubleshooting"
      />

      <div className="p-6 space-y-6">
        {/* Quick Help Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <BookOpen className="h-5 w-5 text-blue-600" />
                </div>
                <CardTitle className="text-base">Getting Started</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Learn the basics of managing properties, contacts, and campaigns
              </p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <MessageCircle className="h-5 w-5 text-green-600" />
                </div>
                <CardTitle className="text-base">Contact Support</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Get in touch with our support team for assistance
              </p>
            </CardContent>
          </Card>

          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <FileText className="h-5 w-5 text-purple-600" />
                </div>
                <CardTitle className="text-base">Documentation</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Browse comprehensive guides and API documentation
              </p>
            </CardContent>
          </Card>
        </div>

        {/* FAQs */}
        <Card>
          <CardHeader>
            <CardTitle>Frequently Asked Questions</CardTitle>
            <CardDescription>
              Common questions about Diaserve Properties features
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible className="w-full">
              {/* Property Management */}
              <AccordionItem value="properties">
                <AccordionTrigger className="text-left">
                  <div className="flex items-center gap-2">
                    <Building className="h-4 w-4" />
                    How do I add a new property?
                  </div>
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  Navigate to the Properties page and click "Add Property". Fill in the property
                  details including title, description, location, price, and amenities. You can
                  also upload photos and documents for each property.
                </AccordionContent>
              </AccordionItem>

              {/* Campaigns */}
              <AccordionItem value="campaigns">
                <AccordionTrigger className="text-left">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    What types of campaigns can I create?
                  </div>
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  Diaserve Properties supports multi-channel campaigns:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li><strong>Voice Calls</strong> - AI-powered voice campaigns using Vapi</li>
                    <li><strong>SMS</strong> - Text message campaigns via Arkesel</li>
                    <li><strong>WhatsApp</strong> - WhatsApp Business messages</li>
                    <li><strong>Email</strong> - Email campaigns via iRedMail</li>
                  </ul>
                  <p className="mt-2">
                    Create campaigns from the Campaigns page and target specific contact segments
                    based on tags, interest level, and property preferences.
                  </p>
                </AccordionContent>
              </AccordionItem>

              {/* Contacts */}
              <AccordionItem value="contacts">
                <AccordionTrigger className="text-left">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    How do I import contacts?
                  </div>
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  On the Campaigns page, switch to the Contacts tab and click "Import CSV".
                  Your CSV file should include columns for:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>first_name, last_name</li>
                    <li>email, phone</li>
                    <li>contact_type (lead, customer, prospect)</li>
                    <li>tags (comma-separated)</li>
                    <li>property_type_preferences, location_preferences</li>
                    <li>budget_min, budget_max</li>
                  </ul>
                </AccordionContent>
              </AccordionItem>

              {/* AI Features */}
              <AccordionItem value="ai">
                <AccordionTrigger className="text-left">
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    How does the AI voice agent work?
                  </div>
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  The AI voice agent uses Vapi to conduct natural conversations with leads.
                  It can answer questions about properties, collect contact information, and
                  schedule viewings. Configure your voice agent in Settings under API Keys
                  by adding your Vapi API key and Assistant ID.
                </AccordionContent>
              </AccordionItem>

              {/* Bookings */}
              <AccordionItem value="bookings">
                <AccordionTrigger className="text-left">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    How do I manage property viewings?
                  </div>
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  Navigate to the Bookings page to see all scheduled viewings. You can:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Create new booking slots for properties</li>
                    <li>Approve or reject booking requests</li>
                    <li>Send confirmation emails to clients</li>
                    <li>View booking history and statistics</li>
                  </ul>
                </AccordionContent>
              </AccordionItem>

              {/* Invoices */}
              <AccordionItem value="invoices">
                <AccordionTrigger className="text-left">
                  <div className="flex items-center gap-2">
                    <CreditCard className="h-4 w-4" />
                    How do I create invoices?
                  </div>
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  Go to the Invoices page and click "Create Invoice". Select the property,
                  client, and add line items for services or fees. You can generate PDF
                  invoices and send them directly to clients. Track payment status and
                  send reminders for overdue invoices.
                </AccordionContent>
              </AccordionItem>

              {/* API Configuration */}
              <AccordionItem value="api-keys">
                <AccordionTrigger className="text-left">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4" />
                    Where do I configure API keys?
                  </div>
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  Navigate to Settings → API Keys to configure:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li><strong>Arkesel</strong> - For SMS campaigns (API key and Sender ID)</li>
                    <li><strong>Vapi</strong> - For voice campaigns (API key and Assistant ID)</li>
                    <li><strong>iRedMail</strong> - For email campaigns (SMTP credentials)</li>
                    <li><strong>WhatsApp Business</strong> - For WhatsApp campaigns (Access token)</li>
                  </ul>
                  <p className="mt-2">
                    All API keys are stored securely and encrypted.
                  </p>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </CardContent>
        </Card>

        {/* Support Contact */}
        <Card>
          <CardHeader>
            <CardTitle>Need More Help?</CardTitle>
            <CardDescription>
              Our support team is here to assist you
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-100 rounded-lg mt-1">
                <Mail className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <p className="font-medium">Email Support</p>
                <p className="text-sm text-muted-foreground">
                  support@ailabsafrica.com
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 bg-green-100 rounded-lg mt-1">
                <Phone className="h-4 w-4 text-green-600" />
              </div>
              <div>
                <p className="font-medium">Phone Support</p>
                <p className="text-sm text-muted-foreground">
                  +233 24 123 4567 (Mon-Fri, 9am-5pm GMT)
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 bg-purple-100 rounded-lg mt-1">
                <ExternalLink className="h-4 w-4 text-purple-600" />
              </div>
              <div>
                <p className="font-medium">Documentation</p>
                <p className="text-sm text-muted-foreground">
                  Visit our comprehensive documentation portal
                </p>
                <Button variant="link" className="h-auto p-0 mt-1">
                  docs.ailabsafrica.com →
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
