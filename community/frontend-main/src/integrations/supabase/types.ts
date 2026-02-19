export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "13.0.4"
  }
  public: {
    Tables: {
      assistants: {
        Row: {
          channel: string
          created_at: string
          guardrails: Json | null
          id: string
          language: string | null
          name: string
          prompt: string | null
          status: string | null
          template: string
          tenant_id: string | null
          updated_at: string
          user_id: string
          voice: string | null
        }
        Insert: {
          channel: string
          created_at?: string
          guardrails?: Json | null
          id?: string
          language?: string | null
          name: string
          prompt?: string | null
          status?: string | null
          template: string
          tenant_id?: string | null
          updated_at?: string
          user_id: string
          voice?: string | null
        }
        Update: {
          channel?: string
          created_at?: string
          guardrails?: Json | null
          id?: string
          language?: string | null
          name?: string
          prompt?: string | null
          status?: string | null
          template?: string
          tenant_id?: string | null
          updated_at?: string
          user_id?: string
          voice?: string | null
        }
        Relationships: []
      }
      bundle_purchases: {
        Row: {
          created_at: string
          id: string
          minutes: number
          price_usd: number
          provider: string
          status: string | null
          stripe_session_id: string | null
          tenant_id: string | null
          tier: string
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          minutes: number
          price_usd: number
          provider: string
          status?: string | null
          stripe_session_id?: string | null
          tenant_id?: string | null
          tier: string
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          minutes?: number
          price_usd?: number
          provider?: string
          status?: string | null
          stripe_session_id?: string | null
          tenant_id?: string | null
          tier?: string
          user_id?: string
        }
        Relationships: []
      }
      call_logs: {
        Row: {
          assistant_id: string
          assistant_name: string | null
          call_id: string
          created_at: string
          duration: number | null
          end_time: string | null
          from_phone: string | null
          id: string
          metadata: Json | null
          start_time: string
          status: string
          summary: string | null
          to_phone: string | null
          transcript: string | null
          updated_at: string
        }
        Insert: {
          assistant_id: string
          assistant_name?: string | null
          call_id: string
          created_at?: string
          duration?: number | null
          end_time?: string | null
          from_phone?: string | null
          id?: string
          metadata?: Json | null
          start_time: string
          status: string
          summary?: string | null
          to_phone?: string | null
          transcript?: string | null
          updated_at?: string
        }
        Update: {
          assistant_id?: string
          assistant_name?: string | null
          call_id?: string
          created_at?: string
          duration?: number | null
          end_time?: string | null
          from_phone?: string | null
          id?: string
          metadata?: Json | null
          start_time?: string
          status?: string
          summary?: string | null
          to_phone?: string | null
          transcript?: string | null
          updated_at?: string
        }
        Relationships: []
      }
      campaigns: {
        Row: {
          assistant_id: string
          audience_size: number | null
          created_at: string
          id: string
          name: string
          pacing: Json | null
          schedule: Json | null
          stats: Json | null
          status: string | null
          tenant_id: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          assistant_id: string
          audience_size?: number | null
          created_at?: string
          id?: string
          name: string
          pacing?: Json | null
          schedule?: Json | null
          stats?: Json | null
          status?: string | null
          tenant_id?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          assistant_id?: string
          audience_size?: number | null
          created_at?: string
          id?: string
          name?: string
          pacing?: Json | null
          schedule?: Json | null
          stats?: Json | null
          status?: string | null
          tenant_id?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "campaigns_assistant_id_fkey"
            columns: ["assistant_id"]
            isOneToOne: false
            referencedRelation: "assistants"
            referencedColumns: ["id"]
          },
        ]
      }
      contact_submissions: {
        Row: {
          company: string | null
          created_at: string
          email: string
          id: string
          message: string
          name: string
          phone: string | null
          status: string | null
          subject: string
          updated_at: string
        }
        Insert: {
          company?: string | null
          created_at?: string
          email: string
          id?: string
          message: string
          name: string
          phone?: string | null
          status?: string | null
          subject: string
          updated_at?: string
        }
        Update: {
          company?: string | null
          created_at?: string
          email?: string
          id?: string
          message?: string
          name?: string
          phone?: string | null
          status?: string | null
          subject?: string
          updated_at?: string
        }
        Relationships: []
      }
      custom_demos: {
        Row: {
          assistant_id: string
          assistant_name: string
          assistant_type: string
          created_at: string
          current_version: number | null
          demo_url: string
          description: string | null
          first_message: string | null
          guest_email: string | null
          guest_password: string | null
          guest_password_hash: string | null
          id: string
          is_guest: boolean | null
          metadata: Json | null
          model: string | null
          status: string
          system_prompt: string | null
          tenant_id: string | null
          updated_at: string
          user_id: string | null
          version_notes: string | null
          voice_id: string | null
          voice_name: string | null
          website_url: string | null
        }
        Insert: {
          assistant_id: string
          assistant_name: string
          assistant_type: string
          created_at?: string
          current_version?: number | null
          demo_url: string
          description?: string | null
          first_message?: string | null
          guest_email?: string | null
          guest_password?: string | null
          guest_password_hash?: string | null
          id?: string
          is_guest?: boolean | null
          metadata?: Json | null
          model?: string | null
          status?: string
          system_prompt?: string | null
          tenant_id?: string | null
          updated_at?: string
          user_id?: string | null
          version_notes?: string | null
          voice_id?: string | null
          voice_name?: string | null
          website_url?: string | null
        }
        Update: {
          assistant_id?: string
          assistant_name?: string
          assistant_type?: string
          created_at?: string
          current_version?: number | null
          demo_url?: string
          description?: string | null
          first_message?: string | null
          guest_email?: string | null
          guest_password?: string | null
          guest_password_hash?: string | null
          id?: string
          is_guest?: boolean | null
          metadata?: Json | null
          model?: string | null
          status?: string
          system_prompt?: string | null
          tenant_id?: string | null
          updated_at?: string
          user_id?: string | null
          version_notes?: string | null
          voice_id?: string | null
          voice_name?: string | null
          website_url?: string | null
        }
        Relationships: []
      }
      custom_templates: {
        Row: {
          category: string
          created_at: string | null
          description: string | null
          difficulty: string
          features: Json | null
          id: string
          is_favorite: boolean | null
          is_public: boolean | null
          name: string
          parent_template_id: string | null
          sample_questions: Json | null
          success_rate: number | null
          system_prompt: string
          tags: Json | null
          updated_at: string | null
          usage_count: number | null
          use_cases: Json | null
          user_id: string | null
          version: number | null
        }
        Insert: {
          category: string
          created_at?: string | null
          description?: string | null
          difficulty: string
          features?: Json | null
          id?: string
          is_favorite?: boolean | null
          is_public?: boolean | null
          name: string
          parent_template_id?: string | null
          sample_questions?: Json | null
          success_rate?: number | null
          system_prompt: string
          tags?: Json | null
          updated_at?: string | null
          usage_count?: number | null
          use_cases?: Json | null
          user_id?: string | null
          version?: number | null
        }
        Update: {
          category?: string
          created_at?: string | null
          description?: string | null
          difficulty?: string
          features?: Json | null
          id?: string
          is_favorite?: boolean | null
          is_public?: boolean | null
          name?: string
          parent_template_id?: string | null
          sample_questions?: Json | null
          success_rate?: number | null
          system_prompt?: string
          tags?: Json | null
          updated_at?: string | null
          usage_count?: number | null
          use_cases?: Json | null
          user_id?: string | null
          version?: number | null
        }
        Relationships: []
      }
      demo_analytics: {
        Row: {
          created_at: string | null
          demo_id: string
          event_data: Json | null
          event_type: string
          id: string
          ip_address: unknown | null
          session_id: string | null
          user_agent: string | null
        }
        Insert: {
          created_at?: string | null
          demo_id: string
          event_data?: Json | null
          event_type: string
          id?: string
          ip_address?: unknown | null
          session_id?: string | null
          user_agent?: string | null
        }
        Update: {
          created_at?: string | null
          demo_id?: string
          event_data?: Json | null
          event_type?: string
          id?: string
          ip_address?: unknown | null
          session_id?: string | null
          user_agent?: string | null
        }
        Relationships: []
      }
      demo_bookings: {
        Row: {
          company_name: string | null
          created_at: string
          demo_type: string
          email: string
          full_name: string
          id: string
          notes: string | null
          phone: string | null
          preferred_date: string
          preferred_time: string
          status: string | null
          tenant_id: string | null
          timezone: string | null
          updated_at: string
          user_id: string | null
        }
        Insert: {
          company_name?: string | null
          created_at?: string
          demo_type?: string
          email: string
          full_name: string
          id?: string
          notes?: string | null
          phone?: string | null
          preferred_date: string
          preferred_time: string
          status?: string | null
          tenant_id?: string | null
          timezone?: string | null
          updated_at?: string
          user_id?: string | null
        }
        Update: {
          company_name?: string | null
          created_at?: string
          demo_type?: string
          email?: string
          full_name?: string
          id?: string
          notes?: string | null
          phone?: string | null
          preferred_date?: string
          preferred_time?: string
          status?: string | null
          tenant_id?: string | null
          timezone?: string | null
          updated_at?: string
          user_id?: string | null
        }
        Relationships: []
      }
      demo_comment_replies: {
        Row: {
          comment_id: string
          created_at: string | null
          id: string
          is_public: boolean | null
          reply_text: string
          updated_at: string | null
          user_id: string | null
        }
        Insert: {
          comment_id: string
          created_at?: string | null
          id?: string
          is_public?: boolean | null
          reply_text: string
          updated_at?: string | null
          user_id?: string | null
        }
        Update: {
          comment_id?: string
          created_at?: string | null
          id?: string
          is_public?: boolean | null
          reply_text?: string
          updated_at?: string | null
          user_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "demo_comment_replies_comment_id_fkey"
            columns: ["comment_id"]
            isOneToOne: false
            referencedRelation: "demo_comments"
            referencedColumns: ["id"]
          },
        ]
      }
      demo_comments: {
        Row: {
          comment_text: string
          created_at: string | null
          demo_id: string
          flagged_reason: string | null
          id: string
          ip_address: unknown | null
          is_approved: boolean | null
          is_flagged: boolean | null
          rating: number | null
          updated_at: string | null
          user_agent: string | null
          user_email: string | null
          user_name: string
        }
        Insert: {
          comment_text: string
          created_at?: string | null
          demo_id: string
          flagged_reason?: string | null
          id?: string
          ip_address?: unknown | null
          is_approved?: boolean | null
          is_flagged?: boolean | null
          rating?: number | null
          updated_at?: string | null
          user_agent?: string | null
          user_email?: string | null
          user_name: string
        }
        Update: {
          comment_text?: string
          created_at?: string | null
          demo_id?: string
          flagged_reason?: string | null
          id?: string
          ip_address?: unknown | null
          is_approved?: boolean | null
          is_flagged?: boolean | null
          rating?: number | null
          updated_at?: string | null
          user_agent?: string | null
          user_email?: string | null
          user_name?: string
        }
        Relationships: []
      }
      demo_html_storage: {
        Row: {
          assistant_id: string
          assistant_name: string
          assistant_type: string
          created_at: string | null
          demo_id: string
          html_content: string
          id: string
          updated_at: string | null
        }
        Insert: {
          assistant_id: string
          assistant_name: string
          assistant_type: string
          created_at?: string | null
          demo_id: string
          html_content: string
          id?: string
          updated_at?: string | null
        }
        Update: {
          assistant_id?: string
          assistant_name?: string
          assistant_type?: string
          created_at?: string | null
          demo_id?: string
          html_content?: string
          id?: string
          updated_at?: string | null
        }
        Relationships: []
      }
      demo_sessions: {
        Row: {
          demo_id: string
          duration_seconds: number | null
          ended_at: string | null
          id: string
          interactions: number | null
          metadata: Json | null
          page_views: number | null
          session_id: string
          started_at: string | null
        }
        Insert: {
          demo_id: string
          duration_seconds?: number | null
          ended_at?: string | null
          id?: string
          interactions?: number | null
          metadata?: Json | null
          page_views?: number | null
          session_id: string
          started_at?: string | null
        }
        Update: {
          demo_id?: string
          duration_seconds?: number | null
          ended_at?: string | null
          id?: string
          interactions?: number | null
          metadata?: Json | null
          page_views?: number | null
          session_id?: string
          started_at?: string | null
        }
        Relationships: []
      }
      demo_versions: {
        Row: {
          assistant_id: string
          assistant_name: string
          assistant_type: string
          created_at: string
          created_by: string
          demo_id: string
          demo_url: string
          description: string | null
          id: string
          version_notes: string | null
          version_number: number
          voice_id: string | null
          voice_name: string | null
          website_url: string | null
        }
        Insert: {
          assistant_id: string
          assistant_name: string
          assistant_type: string
          created_at?: string
          created_by: string
          demo_id: string
          demo_url: string
          description?: string | null
          id?: string
          version_notes?: string | null
          version_number: number
          voice_id?: string | null
          voice_name?: string | null
          website_url?: string | null
        }
        Update: {
          assistant_id?: string
          assistant_name?: string
          assistant_type?: string
          created_at?: string
          created_by?: string
          demo_id?: string
          demo_url?: string
          description?: string | null
          id?: string
          version_notes?: string | null
          version_number?: number
          voice_id?: string | null
          voice_name?: string | null
          website_url?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "demo_versions_demo_id_fkey"
            columns: ["demo_id"]
            isOneToOne: false
            referencedRelation: "custom_demos"
            referencedColumns: ["id"]
          },
        ]
      }
      emails: {
        Row: {
          content: string
          created_at: string
          from_email: string | null
          from_name: string | null
          id: string
          sent_at: string | null
          status: string | null
          subject: string
          to_email: string
        }
        Insert: {
          content: string
          created_at?: string
          from_email?: string | null
          from_name?: string | null
          id?: string
          sent_at?: string | null
          status?: string | null
          subject: string
          to_email: string
        }
        Update: {
          content?: string
          created_at?: string
          from_email?: string | null
          from_name?: string | null
          id?: string
          sent_at?: string | null
          status?: string | null
          subject?: string
          to_email?: string
        }
        Relationships: []
      }
      payment_transactions: {
        Row: {
          amount: number
          created_at: string
          currency: string
          id: string
          payment_method: string
          provider_reference: string | null
          provider_response: Json | null
          status: string
          tenant_id: string | null
          transaction_id: string
          updated_at: string
          user_id: string
          wallet_id: string
        }
        Insert: {
          amount: number
          created_at?: string
          currency?: string
          id?: string
          payment_method: string
          provider_reference?: string | null
          provider_response?: Json | null
          status?: string
          tenant_id?: string | null
          transaction_id: string
          updated_at?: string
          user_id: string
          wallet_id: string
        }
        Update: {
          amount?: number
          created_at?: string
          currency?: string
          id?: string
          payment_method?: string
          provider_reference?: string | null
          provider_response?: Json | null
          status?: string
          tenant_id?: string | null
          transaction_id?: string
          updated_at?: string
          user_id?: string
          wallet_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "payment_transactions_wallet_id_fkey"
            columns: ["wallet_id"]
            isOneToOne: false
            referencedRelation: "wallets"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          company_name: string | null
          created_at: string
          current_step: string | null
          display_name: string | null
          id: string
          industry: string | null
          phone: string | null
          tenant_id: string | null
          timezone: string | null
          updated_at: string
          user_id: string
          workspace_name: string | null
        }
        Insert: {
          company_name?: string | null
          created_at?: string
          current_step?: string | null
          display_name?: string | null
          id?: string
          industry?: string | null
          phone?: string | null
          tenant_id?: string | null
          timezone?: string | null
          updated_at?: string
          user_id: string
          workspace_name?: string | null
        }
        Update: {
          company_name?: string | null
          created_at?: string
          current_step?: string | null
          display_name?: string | null
          id?: string
          industry?: string | null
          phone?: string | null
          tenant_id?: string | null
          timezone?: string | null
          updated_at?: string
          user_id?: string
          workspace_name?: string | null
        }
        Relationships: []
      }
      refunds: {
        Row: {
          amount: number
          created_at: string | null
          id: string
          processed_at: string | null
          reason: string | null
          status: string | null
          transaction_id: string
          updated_at: string | null
          user_id: string
        }
        Insert: {
          amount: number
          created_at?: string | null
          id?: string
          processed_at?: string | null
          reason?: string | null
          status?: string | null
          transaction_id: string
          updated_at?: string | null
          user_id: string
        }
        Update: {
          amount?: number
          created_at?: string | null
          id?: string
          processed_at?: string | null
          reason?: string | null
          status?: string | null
          transaction_id?: string
          updated_at?: string | null
          user_id?: string
        }
        Relationships: []
      }
      usage_bundles: {
        Row: {
          created_at: string
          description: string | null
          id: string
          is_active: boolean | null
          minutes: number
          name: string
          price: number
          updated_at: string
        }
        Insert: {
          created_at?: string
          description?: string | null
          id?: string
          is_active?: boolean | null
          minutes: number
          name: string
          price: number
          updated_at?: string
        }
        Update: {
          created_at?: string
          description?: string | null
          id?: string
          is_active?: boolean | null
          minutes?: number
          name?: string
          price?: number
          updated_at?: string
        }
        Relationships: []
      }
      usage_summary: {
        Row: {
          current_balance: number | null
          id: string
          minutes_included: number | null
          minutes_used: number | null
          overage_rate: number | null
          tenant_id: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          current_balance?: number | null
          id?: string
          minutes_included?: number | null
          minutes_used?: number | null
          overage_rate?: number | null
          tenant_id?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          current_balance?: number | null
          id?: string
          minutes_included?: number | null
          minutes_used?: number | null
          overage_rate?: number | null
          tenant_id?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      usage_tracking: {
        Row: {
          assistant_id: string
          call_id: string | null
          created_at: string | null
          duration_minutes: number | null
          id: string
          metadata: Json | null
          status: string | null
          total_cost: number | null
          updated_at: string | null
          user_id: string
        }
        Insert: {
          assistant_id: string
          call_id?: string | null
          created_at?: string | null
          duration_minutes?: number | null
          id?: string
          metadata?: Json | null
          status?: string | null
          total_cost?: number | null
          updated_at?: string | null
          user_id: string
        }
        Update: {
          assistant_id?: string
          call_id?: string | null
          created_at?: string | null
          duration_minutes?: number | null
          id?: string
          metadata?: Json | null
          status?: string | null
          total_cost?: number | null
          updated_at?: string | null
          user_id?: string
        }
        Relationships: []
      }
      voice_agents: {
        Row: {
          assistant_id: string
          created_at: string | null
          description: string | null
          id: string
          name: string
          status: string | null
          updated_at: string | null
          user_id: string
          voice_id: string | null
          voice_name: string | null
        }
        Insert: {
          assistant_id: string
          created_at?: string | null
          description?: string | null
          id?: string
          name: string
          status?: string | null
          updated_at?: string | null
          user_id: string
          voice_id?: string | null
          voice_name?: string | null
        }
        Update: {
          assistant_id?: string
          created_at?: string | null
          description?: string | null
          id?: string
          name?: string
          status?: string | null
          updated_at?: string | null
          user_id?: string
          voice_id?: string | null
          voice_name?: string | null
        }
        Relationships: []
      }
      wallet_transactions: {
        Row: {
          amount: number
          balance_after: number
          balance_before: number
          created_at: string
          description: string
          id: string
          reference_id: string | null
          reference_type: string | null
          type: string
          user_id: string
          wallet_id: string
        }
        Insert: {
          amount: number
          balance_after: number
          balance_before: number
          created_at?: string
          description: string
          id?: string
          reference_id?: string | null
          reference_type?: string | null
          type: string
          user_id: string
          wallet_id: string
        }
        Update: {
          amount?: number
          balance_after?: number
          balance_before?: number
          created_at?: string
          description?: string
          id?: string
          reference_id?: string | null
          reference_type?: string | null
          type?: string
          user_id?: string
          wallet_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "wallet_transactions_wallet_id_fkey"
            columns: ["wallet_id"]
            isOneToOne: false
            referencedRelation: "wallets"
            referencedColumns: ["id"]
          },
        ]
      }
      wallets: {
        Row: {
          balance: number
          created_at: string
          currency: string
          id: string
          tenant_id: string | null
          updated_at: string
          user_id: string
        }
        Insert: {
          balance?: number
          created_at?: string
          currency?: string
          id?: string
          tenant_id?: string | null
          updated_at?: string
          user_id: string
        }
        Update: {
          balance?: number
          created_at?: string
          currency?: string
          id?: string
          tenant_id?: string | null
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      create_demo_version: {
        Args: { p_demo_id: string; p_version_notes?: string }
        Returns: number
      }
      create_stripe_checkout_session: {
        Args: {
          bundle_minutes: number
          bundle_price: number
          bundle_tier: string
        }
        Returns: string
      }
      get_current_tenant: {
        Args: Record<PropertyKey, never>
        Returns: string
      }
      get_demo_comment_stats: {
        Args: { p_demo_id: string }
        Returns: {
          approved_comments: number
          average_rating: number
          rating_distribution: Json
          total_comments: number
        }[]
      }
      get_demo_comments_with_replies: {
        Args: { p_demo_id: string; p_limit?: number; p_offset?: number }
        Returns: {
          comment_text: string
          created_at: string
          demo_id: string
          id: string
          is_approved: boolean
          is_flagged: boolean
          rating: number
          replies: Json
          user_email: string
          user_name: string
        }[]
      }
      get_demo_version_history: {
        Args: { p_demo_id: string }
        Returns: {
          assistant_name: string
          assistant_type: string
          created_at: string
          description: string
          is_current: boolean
          version_notes: string
          version_number: number
        }[]
      }
      hash_guest_password: {
        Args: { password: string }
        Returns: string
      }
      increment_template_usage: {
        Args: { template_id: string }
        Returns: undefined
      }
      rollback_demo_version: {
        Args: { p_demo_id: string; p_version_number: number }
        Returns: boolean
      }
      verify_guest_password: {
        Args: { demo_id: string; password: string }
        Returns: boolean
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
