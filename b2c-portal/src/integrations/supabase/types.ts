export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instanciate createClient with right options
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
          tier?: string
          user_id?: string
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
      profiles: {
        Row: {
          company_name: string | null
          created_at: string
          display_name: string | null
          id: string
          industry: string | null
          phone: string | null
          timezone: string | null
          updated_at: string
          user_id: string
          workspace_name: string | null
        }
        Insert: {
          company_name?: string | null
          created_at?: string
          display_name?: string | null
          id?: string
          industry?: string | null
          phone?: string | null
          timezone?: string | null
          updated_at?: string
          user_id: string
          workspace_name?: string | null
        }
        Update: {
          company_name?: string | null
          created_at?: string
          display_name?: string | null
          id?: string
          industry?: string | null
          phone?: string | null
          timezone?: string | null
          updated_at?: string
          user_id?: string
          workspace_name?: string | null
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
          updated_at: string
          user_id: string
        }
        Insert: {
          current_balance?: number | null
          id?: string
          minutes_included?: number | null
          minutes_used?: number | null
          overage_rate?: number | null
          updated_at?: string
          user_id: string
        }
        Update: {
          current_balance?: number | null
          id?: string
          minutes_included?: number | null
          minutes_used?: number | null
          overage_rate?: number | null
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
      create_stripe_checkout_session: {
        Args: {
          bundle_minutes: number
          bundle_price: number
          bundle_tier: string
        }
        Returns: string
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
