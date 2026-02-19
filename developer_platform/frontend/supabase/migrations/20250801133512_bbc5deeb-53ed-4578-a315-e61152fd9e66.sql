-- Create devplat schema for KasaAI Developer Platform
CREATE SCHEMA IF NOT EXISTS devplat;

-- API Keys table
CREATE TABLE devplat.api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  workspace_id UUID,
  key_hash TEXT NOT NULL UNIQUE,
  key_prefix TEXT NOT NULL,
  name TEXT NOT NULL,
  scopes TEXT[] NOT NULL DEFAULT '{}',
  rate_limit_rpm INTEGER DEFAULT 300,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'revoked')),
  last_used_at TIMESTAMP WITH TIME ZONE,
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES auth.users(id)
);

-- Webhooks table
CREATE TABLE devplat.webhooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  url TEXT NOT NULL,
  secret TEXT NOT NULL,
  events TEXT[] NOT NULL DEFAULT '{}',
  enabled BOOLEAN DEFAULT true,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES auth.users(id)
);

-- MCP Servers table
CREATE TABLE devplat.mcp_servers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  tool_names TEXT[] DEFAULT '{}',
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
  config JSONB DEFAULT '{}',
  last_health_check TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_by UUID REFERENCES auth.users(id)
);

-- Quotas table
CREATE TABLE devplat.quotas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  api_key_id UUID REFERENCES devplat.api_keys(id) ON DELETE CASCADE,
  period TEXT DEFAULT 'daily' CHECK (period IN ('hourly', 'daily', 'monthly')),
  limit_requests INTEGER NOT NULL,
  limit_minutes INTEGER,
  used_requests INTEGER DEFAULT 0,
  used_minutes INTEGER DEFAULT 0,
  reset_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '1 day',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API Request Logs table
CREATE TABLE devplat.api_request_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  api_key_id UUID REFERENCES devplat.api_keys(id),
  tenant_id UUID NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  status_code INTEGER NOT NULL,
  latency_ms INTEGER,
  request_size INTEGER,
  response_size INTEGER,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Webhook Deliveries table
CREATE TABLE devplat.webhook_deliveries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  webhook_id UUID REFERENCES devplat.webhooks(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'delivered', 'failed', 'retrying')),
  attempts INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 5,
  response_status INTEGER,
  response_body TEXT,
  next_retry_at TIMESTAMP WITH TIME ZONE,
  delivered_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit Logs table
CREATE TABLE devplat.audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  user_id UUID REFERENCES auth.users(id),
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id UUID,
  details JSONB DEFAULT '{}',
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on all tables
ALTER TABLE devplat.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE devplat.webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE devplat.mcp_servers ENABLE ROW LEVEL SECURITY;
ALTER TABLE devplat.quotas ENABLE ROW LEVEL SECURITY;
ALTER TABLE devplat.api_request_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE devplat.webhook_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE devplat.audit_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for tenant isolation
CREATE POLICY "Users can manage their tenant's API keys" ON devplat.api_keys
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM profiles 
      WHERE profiles.user_id = auth.uid() 
      AND profiles.user_id::text = tenant_id::text
    )
  );

CREATE POLICY "Users can manage their tenant's webhooks" ON devplat.webhooks
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM profiles 
      WHERE profiles.user_id = auth.uid() 
      AND profiles.user_id::text = tenant_id::text
    )
  );

CREATE POLICY "Users can manage their tenant's MCP servers" ON devplat.mcp_servers
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM profiles 
      WHERE profiles.user_id = auth.uid() 
      AND profiles.user_id::text = tenant_id::text
    )
  );

CREATE POLICY "Users can view their API key quotas" ON devplat.quotas
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM devplat.api_keys 
      WHERE api_keys.id = quotas.api_key_id 
      AND EXISTS (
        SELECT 1 FROM profiles 
        WHERE profiles.user_id = auth.uid() 
        AND profiles.user_id::text = api_keys.tenant_id::text
      )
    )
  );

CREATE POLICY "Users can view their tenant's request logs" ON devplat.api_request_logs
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM profiles 
      WHERE profiles.user_id = auth.uid() 
      AND profiles.user_id::text = tenant_id::text
    )
  );

CREATE POLICY "Users can view webhook deliveries for their webhooks" ON devplat.webhook_deliveries
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM devplat.webhooks 
      WHERE webhooks.id = webhook_deliveries.webhook_id 
      AND EXISTS (
        SELECT 1 FROM profiles 
        WHERE profiles.user_id = auth.uid() 
        AND profiles.user_id::text = webhooks.tenant_id::text
      )
    )
  );

CREATE POLICY "Users can view their tenant's audit logs" ON devplat.audit_logs
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM profiles 
      WHERE profiles.user_id = auth.uid() 
      AND profiles.user_id::text = tenant_id::text
    )
  );

-- Create indexes for performance
CREATE INDEX idx_api_keys_tenant_id ON devplat.api_keys(tenant_id);
CREATE INDEX idx_api_keys_key_hash ON devplat.api_keys(key_hash);
CREATE INDEX idx_api_keys_status ON devplat.api_keys(status);
CREATE INDEX idx_webhooks_tenant_id ON devplat.webhooks(tenant_id);
CREATE INDEX idx_mcp_servers_tenant_id ON devplat.mcp_servers(tenant_id);
CREATE INDEX idx_quotas_api_key_id ON devplat.quotas(api_key_id);
CREATE INDEX idx_request_logs_tenant_id ON devplat.api_request_logs(tenant_id);
CREATE INDEX idx_request_logs_created_at ON devplat.api_request_logs(created_at);
CREATE INDEX idx_webhook_deliveries_webhook_id ON devplat.webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_status ON devplat.webhook_deliveries(status);
CREATE INDEX idx_audit_logs_tenant_id ON devplat.audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_created_at ON devplat.audit_logs(created_at);

-- Create update timestamp triggers
CREATE TRIGGER update_api_keys_updated_at
  BEFORE UPDATE ON devplat.api_keys
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_webhooks_updated_at
  BEFORE UPDATE ON devplat.webhooks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mcp_servers_updated_at
  BEFORE UPDATE ON devplat.mcp_servers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quotas_updated_at
  BEFORE UPDATE ON devplat.quotas
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();