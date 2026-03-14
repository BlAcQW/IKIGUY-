import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { PageHeader } from '@/components/PageHeader';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Key, ExternalLink, Save, Loader2 } from 'lucide-react';
import { getOrgSettings, updateOrgSettings } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import type { OrgSettings, ProviderCredentials, PipelineDefaults, CallBehavior } from '@/types';
import { ProviderCredentialsCard } from './ProviderCredentialsCard';
import { PipelineDefaultsCard } from './PipelineDefaultsCard';
import { CallBehaviorCard } from './CallBehaviorCard';
import { AccountCard } from './AccountCard';
import { OrganizationCard } from './OrganizationCard';
import { TeamCard } from './TeamCard';

// ---------------------------------------------------------------------------
// Default settings — used while the API response is loading
// ---------------------------------------------------------------------------

const DEFAULT_SETTINGS: OrgSettings = {
  providerCredentials: {},
  pipelineDefaults: {
    silenceTimeout: 30,
    responseDelay: 0.5,
    interruptionThreshold: 0.5,
    transcriber: { provider: 'openai', model: 'whisper-1', language: 'en' },
    voice: { provider: 'openai', voiceId: 'alloy', speed: 1.0 },
    llm: { provider: 'openai', model: 'gpt-4', temperature: 0.7, maxTokens: 1000 },
  },
  callBehavior: {
    maxCallDuration: 3600,
    sessionIdleTimeout: 120,
    recordingEnabled: false,
    hipaaCompliant: false,
    retrySettings: { maxRetries: 0, retryDelay: 30 },
  },
};

export function SettingsPage() {
  const { user, refresh: refreshAuth } = useAuth();

  // Current form state
  const [settings, setSettings] = useState<OrgSettings>(DEFAULT_SETTINGS);
  // Snapshot captured after load / save — used for dirty detection
  const [baseline, setBaseline] = useState<string>('');
  // Which credential fields the user has actually typed in
  const [editedCredFields, setEditedCredFields] = useState<Set<keyof ProviderCredentials>>(new Set());

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Dirty = current form differs from last-saved baseline
  const isDirty = JSON.stringify(settings) !== baseline;

  // --- Load settings on mount ---
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await getOrgSettings();
        if (cancelled) return;
        setSettings(res.data);
        setBaseline(JSON.stringify(res.data));
      } catch (err) {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : 'Failed to load settings';
          toast.error('Error loading settings', { description: msg });
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // --- Save handler ---
  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      // Build the payload — only include credential fields the user actually edited
      // to avoid writing back masked placeholder values.
      const payload: Partial<OrgSettings> = {
        pipelineDefaults: settings.pipelineDefaults,
        callBehavior: settings.callBehavior,
      };

      if (editedCredFields.size > 0) {
        const creds: Partial<ProviderCredentials> = {};
        for (const key of editedCredFields) {
          creds[key] = settings.providerCredentials[key];
        }
        payload.providerCredentials = creds;
      }

      const res = await updateOrgSettings(payload);
      setSettings(res.data);
      setBaseline(JSON.stringify(res.data));
      setEditedCredFields(new Set());
      toast.success('Settings saved');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save settings';
      toast.error('Error saving settings', { description: msg });
    } finally {
      setSaving(false);
    }
  }, [settings, editedCredFields]);

  // --- Keyboard shortcut: Ctrl/Cmd+S ---
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        if (isDirty && !saving) handleSave();
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isDirty, saving, handleSave]);

  // --- Section update helpers ---

  function handleCredentialChange(key: keyof ProviderCredentials, value: string) {
    setSettings((prev) => ({
      ...prev,
      providerCredentials: { ...prev.providerCredentials, [key]: value },
    }));
    setEditedCredFields((prev) => new Set(prev).add(key));
  }

  function handlePipelineChange(patch: Partial<PipelineDefaults>) {
    setSettings((prev) => ({
      ...prev,
      pipelineDefaults: { ...prev.pipelineDefaults, ...patch },
    }));
  }

  function handleCallBehaviorChange(patch: Partial<CallBehavior>) {
    setSettings((prev) => ({
      ...prev,
      callBehavior: { ...prev.callBehavior, ...patch },
    }));
  }

  // --- Render ---

  if (loading) {
    return (
      <div className="animate-slide-up max-w-3xl">
        <PageHeader title="Settings" subtitle="Account settings and configuration" />
        <div className="flex items-center justify-center py-20 text-muted-foreground text-sm">
          <Loader2 size={16} className="animate-spin mr-2" />
          Loading settings...
        </div>
      </div>
    );
  }

  return (
    <div className="animate-slide-up max-w-3xl">
      {/* Header with Save button */}
      <div className="flex items-start justify-between mb-6">
        <PageHeader title="Settings" subtitle="Account settings and configuration" />
        <div className="flex items-center gap-2 pt-1">
          {isDirty && (
            <span className="text-xs text-amber-500 font-medium">Unsaved changes</span>
          )}
          <Button
            size="sm"
            disabled={!isDirty || saving}
            onClick={handleSave}
            className="gap-1.5 text-xs"
          >
            {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </div>
      </div>

      {/* 1. Account */}
      {user && (
        <AccountCard
          userName={user.name ?? ''}
          userEmail={user.email ?? ''}
          onProfileUpdated={refreshAuth}
        />
      )}

      {/* 2. Organization */}
      {user && <OrganizationCard userRole={user.role} />}

      {/* 3. Team */}
      {user && <TeamCard userRole={user.role} currentUserId={user.userId} />}

      {/* 4. API Keys — existing card, links to /api-keys */}
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

      {/* 5. Provider Credentials */}
      <ProviderCredentialsCard
        credentials={settings.providerCredentials}
        editedFields={editedCredFields}
        onChange={handleCredentialChange}
      />

      {/* 6. Pipeline Defaults */}
      <PipelineDefaultsCard
        defaults={settings.pipelineDefaults}
        onChange={handlePipelineChange}
      />

      {/* 7. Call Behavior */}
      <CallBehaviorCard
        behavior={settings.callBehavior}
        onChange={handleCallBehaviorChange}
      />
    </div>
  );
}
