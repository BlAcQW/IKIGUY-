import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/components/ui/use-toast";
import { Plus, Key, Webhook, Settings, Activity, Globe, Zap } from "lucide-react";
import { ApiKeysTab } from "@/components/developer/ApiKeysTab";
import { WebhooksTab } from "@/components/developer/WebhooksTab";
import { McpTab } from "@/components/developer/McpTab";
import { UsageTab } from "@/components/developer/UsageTab";
import { SettingsTab } from "@/components/developer/SettingsTab";
import { ApiExplorerTab } from "@/components/developer/ApiExplorerTab";
import { supabase } from "@/integrations/supabase/client";

const DeveloperConsole = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user ?? null);
      setLoading(false);
    };

    getSession();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setUser(session?.user ?? null);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-center">KasaAI Developer Console</CardTitle>
            <CardDescription className="text-center">
              Sign in to access your developer tools
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              onClick={() => supabase.auth.signInWithOAuth({ provider: 'google' })}
              className="w-full"
            >
              Sign in with Google
            </Button>
            <Button
              onClick={() => window.location.href = '/auth'}
              variant="outline"
              className="w-full"
            >
              Sign in with Email
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="flex h-16 items-center px-4 lg:px-8">
          <div className="flex items-center space-x-2">
            <Globe className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-semibold">KasaAI Developer Console</h1>
          </div>
          <div className="ml-auto flex items-center space-x-4">
            <Badge variant="secondary">
              {user.email}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => supabase.auth.signOut()}
            >
              Sign out
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto py-6 lg:py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight mb-2">Developer Dashboard</h2>
          <p className="text-muted-foreground">
            Manage your API keys, webhooks, integrations, and monitor usage
          </p>
        </div>

        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="explorer">
              <Zap className="h-4 w-4 mr-2" />
              API Explorer
            </TabsTrigger>
            <TabsTrigger value="keys">
              <Key className="h-4 w-4 mr-2" />
              API Keys
            </TabsTrigger>
            <TabsTrigger value="webhooks">
              <Webhook className="h-4 w-4 mr-2" />
              Webhooks
            </TabsTrigger>
            <TabsTrigger value="mcp">
              <Plus className="h-4 w-4 mr-2" />
              MCP Registry
            </TabsTrigger>
            <TabsTrigger value="usage">
              <Activity className="h-4 w-4 mr-2" />
              Usage
            </TabsTrigger>
            <TabsTrigger value="settings">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active API Keys</CardTitle>
                  <Key className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">0</div>
                  <p className="text-xs text-muted-foreground">
                    +0 from last month
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">API Requests</CardTitle>
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">0</div>
                  <p className="text-xs text-muted-foreground">
                    +0% from last month
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Webhooks</CardTitle>
                  <Webhook className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">0</div>
                  <p className="text-xs text-muted-foreground">
                    0 active endpoints
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">MCP Connectors</CardTitle>
                  <Plus className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">0</div>
                  <p className="text-xs text-muted-foreground">
                    0 configured
                  </p>
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Quick Start</CardTitle>
                  <CardDescription>
                    Get started with the KasaAI API in minutes
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">1. Create an API Key</h4>
                    <p className="text-sm text-muted-foreground">
                      Generate your first API key to authenticate requests
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">2. Test API endpoints</h4>
                    <p className="text-sm text-muted-foreground">
                      Use the interactive API Explorer to test endpoints
                    </p>
                  </div>
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">3. Set up webhooks</h4>
                    <p className="text-sm text-muted-foreground">
                      Receive real-time notifications about events
                    </p>
                  </div>
                  <Button className="w-full">
                    View Documentation
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                  <CardDescription>
                    Your latest API usage and events
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-center py-8">
                    <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-sm text-muted-foreground">
                      No recent activity. Create an API key to get started.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="explorer">
            <ApiExplorerTab />
          </TabsContent>

          <TabsContent value="keys">
            <ApiKeysTab />
          </TabsContent>

          <TabsContent value="webhooks">
            <WebhooksTab />
          </TabsContent>

          <TabsContent value="mcp">
            <McpTab />
          </TabsContent>

          <TabsContent value="usage">
            <UsageTab />
          </TabsContent>

          <TabsContent value="settings">
            <SettingsTab />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default DeveloperConsole;