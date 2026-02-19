import { useState } from "react";
import {
  Users,
  Plus,
  Search,
  Filter,
  Mail,
  Phone,
  Building2,
  Calendar,
  MoreHorizontal,
  Star,
  MessageSquare,
  Upload,
  Loader2,
  Trash2,
  Edit
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ContactImportDialog } from "@/components/ContactImportDialog";
import { useContacts, useDeleteContact } from "@/hooks/use-campaigns";
import type { InterestStatus } from "@/lib/api/campaign-api";

export default function Contacts() {
  const [searchQuery, setSearchQuery] = useState("");
  const [importDialogOpen, setImportDialogOpen] = useState(false);

  // Fetch contacts with search
  const { data: contactsData, isLoading, error } = useContacts({
    search: searchQuery || undefined,
    limit: 100,
  });

  const contacts = contactsData?.contacts || [];
  const totalContacts = contactsData?.total || 0;

  // Calculate stats from real data
  const hotLeads = contacts.filter((c) => c.interest_status === "hot").length;
  const warmLeads = contacts.filter((c) => c.interest_status === "warm").length;
  const newLeads = contacts.filter((c) => c.lead_status === "new").length;

  const stats = [
    { name: "Total Contacts", value: totalContacts.toString() },
    { name: "Hot Leads", value: hotLeads.toString() },
    { name: "Warm Leads", value: warmLeads.toString() },
    { name: "New This Week", value: newLeads.toString() },
  ];

  const getStatusColor = (status: InterestStatus) => {
    switch (status) {
      case "hot": return "soft-destructive";
      case "warm": return "soft-warning";
      case "cold": return "soft";
      case "unqualified": return "soft";
      default: return "soft";
    }
  };

  const getLeadStatusColor = (status: string) => {
    switch (status) {
      case "new": return "soft";
      case "contacted": return "soft";
      case "qualified": return "soft-success";
      case "negotiating": return "soft-warning";
      case "converted": return "soft-success";
      case "lost": return "soft";
      default: return "soft";
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="min-h-screen">
      <Header
        title="Contacts"
        subtitle="Manage your clients and leads"
        actions={
          <div className="flex gap-2">
            <Button
              variant="soft"
              className="gap-2"
              onClick={() => setImportDialogOpen(true)}
            >
              <Upload className="h-4 w-4" />
              Import CSV
            </Button>
            <Button variant="gradient" className="gap-2">
              <Plus className="h-4 w-4" />
              Add Contact
            </Button>
          </div>
        }
      />

      <ContactImportDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
      />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {stats.map((stat, index) => (
            <Card
              key={stat.name}
              variant="elevated"
              className="group overflow-hidden animate-scale-in hover:border-primary/30"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 group-hover:from-primary/30 group-hover:to-secondary/30 transition-all duration-200 shadow-inner-soft">
                    <Users className="h-6 w-6 text-primary" />
                  </div>
                </div>
                <p className="text-3xl font-bold text-foreground mb-1">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.name}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search contacts..."
              className="pl-9"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Contacts List */}
        <Card variant="elevated" className="animate-slide-up-fade">
          <CardHeader>
            <CardTitle>All Contacts</CardTitle>
            <CardDescription>Your clients, leads, and tenants</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-red-500">Failed to load contacts</p>
                <p className="text-sm text-muted-foreground mt-1">{error.message}</p>
              </div>
            ) : contacts.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No contacts found</p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => setImportDialogOpen(true)}
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Import Contacts from CSV
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {contacts.map((contact) => (
                  <ContactRow
                    key={contact.id}
                    contact={contact}
                    getStatusColor={getStatusColor}
                    getLeadStatusColor={getLeadStatusColor}
                    getInitials={getInitials}
                    formatDate={formatDate}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ==================== Contact Row Component ====================

interface ContactRowProps {
  contact: any;
  getStatusColor: (status: InterestStatus) => string;
  getLeadStatusColor: (status: string) => string;
  getInitials: (name: string) => string;
  formatDate: (dateString: string) => string;
}

function ContactRow({
  contact,
  getStatusColor,
  getLeadStatusColor,
  getInitials,
  formatDate,
}: ContactRowProps) {
  const deleteMutation = useDeleteContact();

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete ${contact.name}?`)) {
      deleteMutation.mutate(contact.id);
    }
  };

  return (
    <div className="flex items-center gap-4 p-4 rounded-xl border border-border hover:bg-secondary/50 hover:border-primary/30 transition-all duration-200 group">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-primary to-secondary text-primary-foreground font-semibold shadow-inner-soft group-hover:shadow-premium transition-all">
        {getInitials(contact.name)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h4 className="font-medium text-foreground">{contact.name}</h4>
          <Badge variant={getStatusColor(contact.interest_status) as any}>
            {contact.interest_status}
          </Badge>
          <Badge variant={getLeadStatusColor(contact.lead_status) as any}>
            {contact.lead_status}
          </Badge>
          {contact.tags && contact.tags.length > 0 && (
            <Badge variant="outline">{contact.tags[0]}</Badge>
          )}
        </div>
        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground flex-wrap">
          {contact.email && (
            <span className="flex items-center gap-1">
              <Mail className="h-3.5 w-3.5" />
              {contact.email}
            </span>
          )}
          {contact.phone && (
            <span className="flex items-center gap-1">
              <Phone className="h-3.5 w-3.5" />
              {contact.phone}
            </span>
          )}
        </div>
      </div>
      <div className="text-right">
        {contact.budget_min && contact.budget_max && (
          <p className="text-sm text-foreground">
            GHS {contact.budget_min.toLocaleString()} - {contact.budget_max.toLocaleString()}
          </p>
        )}
        {contact.property_type_preferences && contact.property_type_preferences.length > 0 && (
          <p className="text-xs text-muted-foreground">
            {contact.property_type_preferences.join(", ")}
          </p>
        )}
        {contact.last_contacted ? (
          <p className="text-xs text-muted-foreground">
            Last contact: {formatDate(contact.last_contacted)}
          </p>
        ) : (
          <p className="text-xs text-muted-foreground">Never contacted</p>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon-sm">
          <MessageSquare className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon-sm">
          <Phone className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={handleDelete}
          disabled={deleteMutation.isPending}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
