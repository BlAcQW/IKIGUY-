import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/use-toast";
import { Save, Download, AlertTriangle, Shield, Bell } from "lucide-react";

export const SettingsTab = () => {
  const [settings, setSettings] = useState({
    workspace_name: "My Workspace",
    contact_email: "developer@example.com",
    webhook_notifications: true,
    error_notifications: true,
    quota_alerts: true,
    allowed_ips: "",
    cors_origins: "https://my-app.com\nhttps://staging-app.com",
    rate_limit_burst: 300,
    rate_limit_sustained: 10000
  });

  const saveSettings = () => {
    // In real implementation, save to backend
    toast({
      title: "Settings Saved",
      description: "Your developer platform settings have been updated",
    });
  };

  const downloadAuditLog = () => {
    // In real implementation, trigger audit log download
    toast({
      title: "Download Started",
      description: "Your audit log will be downloaded shortly",
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Settings</h3>
        <p className="text-sm text-muted-foreground">
          Configure your developer platform preferences and security settings
        </p>
      </div>

      {/* Workspace Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Workspace Settings</CardTitle>
          <CardDescription>
            Basic information about your developer workspace
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="workspace_name">Workspace Name</Label>
            <Input
              id="workspace_name"
              value={settings.workspace_name}
              onChange={(e) => setSettings(prev => ({ ...prev, workspace_name: e.target.value }))}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="contact_email">Contact Email</Label>
            <Input
              id="contact_email"
              type="email"
              value={settings.contact_email}
              onChange={(e) => setSettings(prev => ({ ...prev, contact_email: e.target.value }))}
            />
            <p className="text-xs text-muted-foreground">
              Used for important notifications and security alerts
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bell className="h-5 w-5" />
            <span>Notification Preferences</span>
          </CardTitle>
          <CardDescription>
            Choose which notifications you want to receive
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Webhook Delivery Failures</Label>
              <p className="text-sm text-muted-foreground">
                Get notified when webhook deliveries fail
              </p>
            </div>
            <Switch
              checked={settings.webhook_notifications}
              onCheckedChange={(checked) => setSettings(prev => ({ ...prev, webhook_notifications: checked }))}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>API Error Alerts</Label>
              <p className="text-sm text-muted-foreground">
                Receive alerts for elevated error rates
              </p>
            </div>
            <Switch
              checked={settings.error_notifications}
              onCheckedChange={(checked) => setSettings(prev => ({ ...prev, error_notifications: checked }))}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Quota Warnings</Label>
              <p className="text-sm text-muted-foreground">
                Alert when approaching usage limits
              </p>
            </div>
            <Switch
              checked={settings.quota_alerts}
              onCheckedChange={(checked) => setSettings(prev => ({ ...prev, quota_alerts: checked }))}
            />
          </div>
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Security Settings</span>
          </CardTitle>
          <CardDescription>
            Configure security and access control settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="allowed_ips">Allowed IP Addresses</Label>
            <Textarea
              id="allowed_ips"
              placeholder="192.168.1.1&#10;10.0.0.0/8&#10;Leave empty to allow all IPs"
              value={settings.allowed_ips}
              onChange={(e) => setSettings(prev => ({ ...prev, allowed_ips: e.target.value }))}
              rows={3}
            />
            <p className="text-xs text-muted-foreground">
              One IP address or CIDR block per line. Leave empty to allow all IPs.
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="cors_origins">CORS Allowed Origins</Label>
            <Textarea
              id="cors_origins"
              placeholder="https://my-app.com&#10;https://staging-app.com"
              value={settings.cors_origins}
              onChange={(e) => setSettings(prev => ({ ...prev, cors_origins: e.target.value }))}
              rows={3}
            />
            <p className="text-xs text-muted-foreground">
              One origin per line. Required for browser-based API requests.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Rate Limiting */}
      <Card>
        <CardHeader>
          <CardTitle>Rate Limiting</CardTitle>
          <CardDescription>
            Configure API rate limits for your workspace
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="rate_limit_burst">Burst Limit (per minute)</Label>
              <Input
                id="rate_limit_burst"
                type="number"
                value={settings.rate_limit_burst}
                onChange={(e) => setSettings(prev => ({ ...prev, rate_limit_burst: parseInt(e.target.value) }))}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="rate_limit_sustained">Sustained Limit (per hour)</Label>
              <Input
                id="rate_limit_sustained"
                type="number"
                value={settings.rate_limit_sustained}
                onChange={(e) => setSettings(prev => ({ ...prev, rate_limit_sustained: parseInt(e.target.value) }))}
              />
            </div>
          </div>
          
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md flex items-start space-x-2">
            <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5" />
            <div className="text-sm text-yellow-800">
              <strong>Note:</strong> Rate limit changes may take up to 5 minutes to take effect. 
              Overly restrictive limits may impact your application's performance.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audit & Compliance */}
      <Card>
        <CardHeader>
          <CardTitle>Audit & Compliance</CardTitle>
          <CardDescription>
            Access audit logs and compliance information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div>
              <div className="font-medium">Download Audit Log</div>
              <div className="text-sm text-muted-foreground">
                Export complete audit trail of API key usage and actions
              </div>
            </div>
            <Button variant="outline" onClick={downloadAuditLog}>
              <Download className="h-4 w-4 mr-2" />
              Download
            </Button>
          </div>
          
          <div className="text-sm text-muted-foreground space-y-2">
            <p><strong>Data Retention:</strong> Audit logs are retained for 90 days</p>
            <p><strong>Compliance:</strong> SOC 2 Type II, GDPR compliant</p>
            <p><strong>Encryption:</strong> All data encrypted in transit and at rest</p>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={saveSettings}>
          <Save className="h-4 w-4 mr-2" />
          Save Settings
        </Button>
      </div>
    </div>
  );
};