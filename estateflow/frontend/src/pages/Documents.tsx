import { 
  FileText, 
  Plus, 
  Search, 
  Filter,
  Download,
  Share2,
  MoreHorizontal,
  FileCheck,
  FilePen,
  FileX,
  Sparkles
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

const documents = [
  {
    id: 1,
    name: "Lease Agreement - Downtown Loft",
    type: "lease",
    status: "signed",
    date: "Jan 15, 2024",
    client: "Mike Johnson",
    size: "2.4 MB",
  },
  {
    id: 2,
    name: "Property Inspection Report",
    type: "inspection",
    status: "pending",
    date: "Jan 18, 2024",
    client: "Sarah Mitchell",
    size: "1.8 MB",
  },
  {
    id: 3,
    name: "Offer Letter - Luxury Penthouse",
    type: "offer",
    status: "draft",
    date: "Jan 20, 2024",
    client: "Emily Chen",
    size: "0.9 MB",
  },
  {
    id: 4,
    name: "Rental Application",
    type: "application",
    status: "review",
    date: "Jan 22, 2024",
    client: "David Brown",
    size: "3.2 MB",
  },
];

const documentTypes = [
  { name: "Lease Agreements", icon: FileCheck, count: 45 },
  { name: "Offer Letters", icon: FilePen, count: 23 },
  { name: "Applications", icon: FileText, count: 67 },
  { name: "Inspections", icon: FileX, count: 34 },
];

export default function Documents() {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "signed": return "success";
      case "pending": return "warning";
      case "draft": return "muted";
      case "review": return "info";
      default: return "muted";
    }
  };

  return (
    <div className="min-h-screen">
      <Header 
        title="Documents" 
        subtitle="Manage contracts, agreements, and files"
        actions={
          <div className="flex items-center gap-3">
            <Button variant="outline" className="gap-2">
              <Sparkles className="h-4 w-4" />
              AI Generate
            </Button>
            <Button variant="accent" className="gap-2">
              <Plus className="h-4 w-4" />
              Upload
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Document Types */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {documentTypes.map((type) => (
            <Card key={type.name} variant="interactive">
              <CardContent className="p-6 flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                  <type.icon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-foreground">{type.count}</p>
                  <p className="text-sm text-muted-foreground">{type.name}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Search */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Search documents..." className="pl-9" />
          </div>
          <Button variant="outline" className="gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </Button>
        </div>

        {/* Documents List */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Documents</CardTitle>
            <CardDescription>Your files and contracts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center gap-4 p-4 rounded-xl bg-secondary/50 hover:bg-secondary transition-colors"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10">
                    <FileText className="h-6 w-6 text-accent" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="font-medium text-foreground truncate">{doc.name}</h4>
                      <Badge variant={getStatusColor(doc.status) as any}>{doc.status}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {doc.client} • {doc.date} • {doc.size}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="icon-sm">
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon-sm">
                      <Share2 className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon-sm">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
