import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Key, ExternalLink, Settings2, Shield } from 'lucide-react';

export function SettingsPage() {
  return (
    <div className="animate-slide-up max-w-3xl">
      <PageHeader title="Settings" subtitle="Account settings and configuration" />

      {/* API Keys Card */}
      <Card className="mb-4">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Key size={16} className="text-primary" />
            </div>
            <div className="flex-1">
              <CardTitle className="text-base font-display">API Keys</CardTitle>
              <CardDescription className="text-xs">
                Manage API keys for programmatic access to the LOAD API.
              </CardDescription>
            </div>
            <Link to="/api-keys">
              <Button variant="outline" size="sm" className="text-xs gap-1.5">
                Manage
                <ExternalLink size={12} />
              </Button>
            </Link>
          </div>
        </CardHeader>
      </Card>

      {/* General Settings Card (placeholder) */}
      <Card className="mb-4">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-muted">
              <Settings2 size={16} className="text-muted-foreground" />
            </div>
            <div>
              <CardTitle className="text-base font-display">General</CardTitle>
              <CardDescription className="text-xs">
                Organization name, timezone, and preferences.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">General settings coming soon.</p>
        </CardContent>
      </Card>

      {/* Security Card (placeholder) */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-muted">
              <Shield size={16} className="text-muted-foreground" />
            </div>
            <div>
              <CardTitle className="text-base font-display">Security</CardTitle>
              <CardDescription className="text-xs">
                Password, two-factor authentication, and sessions.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Security settings coming soon.</p>
        </CardContent>
      </Card>
    </div>
  );
}
