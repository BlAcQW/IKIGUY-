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
			custom_demos: {
				Row: {
					assistant_id: string
					assistant_name: string
					assistant_type: string
					created_at: string
					demo_url: string
					description: string | null
					id: string
					status: string
					tenant_id: string | null
					updated_at: string
					user_id: string
					voice_id: string | null
					voice_name: string | null
					website_url: string | null
				}
				Insert: {
					assistant_id: string
					assistant_name: string
					assistant_type: string
					created_at?: string
					demo_url: string
					description?: string | null
					id?: string
					status?: string
					tenant_id?: string | null
					updated_at?: string
					user_id: string
					voice_id?: string | null
					voice_name?: string | null
					website_url?: string | null
				}
				Update: {
					assistant_id?: string
					assistant_name?: string
					assistant_type?: string
					created_at?: string
					demo_url?: string
					description?: string | null
					id?: string
					status?: string
					tenant_id?: string | null
					updated_at?: string
					user_id?: string
					voice_id?: string | null
					voice_name?: string | null
					website_url?: string | null
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
					user_id: string
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
					user_id: string
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
					user_id?: string
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
			assistant_drafts: {
				Row: {
					id: string
					user_id: string
					step: number
					data: Json
					created_at: string
					updated_at: string
				}
				Insert: {
					id?: string
					user_id: string
					step?: number
					data?: Json
					created_at?: string
					updated_at?: string
				}
				Update: {
					id?: string
					user_id?: string
					step?: number
					data?: Json
					created_at?: string
					updated_at?: string
				}
				Relationships: [
					{
						foreignKeyName: "assistant_drafts_user_id_fkey"
						columns: ["user_id"]
						isOneToOne: false
						referencedRelation: "users"
						referencedColumns: ["id"]
					}
				]
			}
			referral_programs: {
				Row: {
					id: string
					name: string
					description: string | null
					reward_type: string
					reward_value: number
					reward_currency: string
					max_rewards_per_user: number | null
					is_active: boolean
					terms_conditions: string | null
					created_at: string
					updated_at: string
				}
				Insert: {
					id?: string
					name: string
					description?: string | null
					reward_type: string
					reward_value: number
					reward_currency?: string
					max_rewards_per_user?: number | null
					is_active?: boolean
					terms_conditions?: string | null
					created_at?: string
					updated_at?: string
				}
				Update: {
					id?: string
					name?: string
					description?: string | null
					reward_type?: string
					reward_value?: number
					reward_currency?: string
					max_rewards_per_user?: number | null
					is_active?: boolean
					terms_conditions?: string | null
					created_at?: string
					updated_at?: string
				}
				Relationships: []
			}
			user_referrals: {
				Row: {
					id: string
					referrer_id: string
					referred_id: string | null
					referral_code: string
					referral_link: string
					program_id: string
					status: string
					conversion_date: string | null
					utm_source: string | null
					utm_medium: string | null
					utm_campaign: string | null
					created_at: string
					updated_at: string
				}
				Insert: {
					id?: string
					referrer_id: string
					referred_id?: string | null
					referral_code: string
					referral_link: string
					program_id: string
					status?: string
					conversion_date?: string | null
					utm_source?: string | null
					utm_medium?: string | null
					utm_campaign?: string | null
					created_at?: string
					updated_at?: string
				}
				Update: {
					id?: string
					referrer_id?: string
					referred_id?: string | null
					referral_code?: string
					referral_link?: string
					program_id?: string
					status?: string
					conversion_date?: string | null
					utm_source?: string | null
					utm_medium?: string | null
					utm_campaign?: string | null
					created_at?: string
					updated_at?: string
				}
				Relationships: [
					{
						foreignKeyName: "user_referrals_program_id_fkey"
						columns: ["program_id"]
						isOneToOne: false
						referencedRelation: "referral_programs"
						referencedColumns: ["id"]
					},
					{
						foreignKeyName: "user_referrals_referrer_id_fkey"
						columns: ["referrer_id"]
						isOneToOne: false
						referencedRelation: "profiles"
						referencedColumns: ["user_id"]
					},
					{
						foreignKeyName: "user_referrals_referred_id_fkey"
						columns: ["referred_id"]
						isOneToOne: false
						referencedRelation: "profiles"
						referencedColumns: ["user_id"]
					}
				]
			}
			referral_rewards: {
				Row: {
					id: string
					user_id: string
					referral_id: string
					program_id: string
					reward_type: string
					reward_value: number
					reward_currency: string
					status: string
					processed_date: string | null
					created_at: string
					updated_at: string
				}
				Insert: {
					id?: string
					user_id: string
					referral_id: string
					program_id: string
					reward_type: string
					reward_value: number
					reward_currency?: string
					status?: string
					processed_date?: string | null
					created_at?: string
					updated_at?: string
				}
				Update: {
					id?: string
					user_id?: string
					referral_id?: string
					program_id?: string
					reward_type?: string
					reward_value?: number
					reward_currency?: string
					status?: string
					processed_date?: string | null
					created_at?: string
					updated_at?: string
				}
				Relationships: [
					{
						foreignKeyName: "referral_rewards_user_id_fkey"
						columns: ["user_id"]
						isOneToOne: false
						referencedRelation: "profiles"
						referencedColumns: ["user_id"]
					},
					{
						foreignKeyName: "referral_rewards_referral_id_fkey"
						columns: ["referral_id"]
						isOneToOne: false
						referencedRelation: "user_referrals"
						referencedColumns: ["id"]
					},
					{
						foreignKeyName: "referral_rewards_program_id_fkey"
						columns: ["program_id"]
						isOneToOne: false
						referencedRelation: "referral_programs"
						referencedColumns: ["id"]
					}
				]
			}
			lead_campaigns: {
				Row: {
					id: string
					name: string
					description: string | null
					campaign_type: string
					status: string
					budget: number | null
					start_date: string
					end_date: string | null
					target_audience: Json | null
					settings: Json | null
					created_by: string
					created_at: string
					updated_at: string
				}
				Insert: {
					id?: string
					name: string
					description?: string | null
					campaign_type: string
					status?: string
					budget?: number | null
					start_date?: string
					end_date?: string | null
					target_audience?: Json | null
					settings?: Json | null
					created_by: string
					created_at?: string
					updated_at?: string
				}
				Update: {
					id?: string
					name?: string
					description?: string | null
					campaign_type?: string
					status?: string
					budget?: number | null
					start_date?: string
					end_date?: string | null
					target_audience?: Json | null
					settings?: Json | null
					created_by?: string
					created_at?: string
					updated_at?: string
				}
				Relationships: [
					{
						foreignKeyName: "lead_campaigns_created_by_fkey"
						columns: ["created_by"]
						isOneToOne: false
						referencedRelation: "profiles"
						referencedColumns: ["user_id"]
					}
				]
			}
			lead_sources: {
				Row: {
					id: string
					name: string
					source_type: string
					campaign_id: string | null
					utm_source: string | null
					utm_medium: string | null
					utm_campaign: string | null
					utm_term: string | null
					utm_content: string | null
					conversion_rate: number
					cost_per_lead: number | null
					created_at: string
					updated_at: string
				}
				Insert: {
					id?: string
					name: string
					source_type: string
					campaign_id?: string | null
					utm_source?: string | null
					utm_medium?: string | null
					utm_campaign?: string | null
					utm_term?: string | null
					utm_content?: string | null
					conversion_rate?: number
					cost_per_lead?: number | null
					created_at?: string
					updated_at?: string
				}
				Update: {
					id?: string
					name?: string
					source_type?: string
					campaign_id?: string | null
					utm_source?: string | null
					utm_medium?: string | null
					utm_campaign?: string | null
					utm_term?: string | null
					utm_content?: string | null
					conversion_rate?: number
					cost_per_lead?: number | null
					created_at?: string
					updated_at?: string
				}
				Relationships: [
					{
						foreignKeyName: "lead_sources_campaign_id_fkey"
						columns: ["campaign_id"]
						isOneToOne: false
						referencedRelation: "lead_campaigns"
						referencedColumns: ["id"]
					}
				]
			}
			lead_contacts: {
				Row: {
					id: string
					email: string
					first_name: string | null
					last_name: string | null
					phone: string | null
					company: string | null
					job_title: string | null
					source_id: string
					campaign_id: string | null
					status: string
					lead_score: number
					tags: string[] | null
					notes: string | null
					assigned_to: string
					last_contact_date: string | null
					next_follow_up: string | null
					created_at: string
					updated_at: string
				}
				Insert: {
					id?: string
					email: string
					first_name?: string | null
					last_name?: string | null
					phone?: string | null
					company?: string | null
					job_title?: string | null
					source_id: string
					campaign_id?: string | null
					status?: string
					lead_score?: number
					tags?: string[] | null
					notes?: string | null
					assigned_to: string
					last_contact_date?: string | null
					next_follow_up?: string | null
					created_at?: string
					updated_at?: string
				}
				Update: {
					id?: string
					email?: string
					first_name?: string | null
					last_name?: string | null
					phone?: string | null
					company?: string | null
					job_title?: string | null
					source_id?: string
					campaign_id?: string | null
					status?: string
					lead_score?: number
					tags?: string[] | null
					notes?: string | null
					assigned_to?: string
					last_contact_date?: string | null
					next_follow_up?: string | null
					created_at?: string
					updated_at?: string
				}
				Relationships: [
					{
						foreignKeyName: "lead_contacts_source_id_fkey"
						columns: ["source_id"]
						isOneToOne: false
						referencedRelation: "lead_sources"
						referencedColumns: ["id"]
					},
					{
						foreignKeyName: "lead_contacts_campaign_id_fkey"
						columns: ["campaign_id"]
						isOneToOne: false
						referencedRelation: "lead_campaigns"
						referencedColumns: ["id"]
					},
					{
						foreignKeyName: "lead_contacts_assigned_to_fkey"
						columns: ["assigned_to"]
						isOneToOne: false
						referencedRelation: "profiles"
						referencedColumns: ["user_id"]
					}
				]
			}
			lead_activities: {
				Row: {
					id: string
					lead_id: string
					activity_type: string
					subject: string | null
					description: string | null
					performed_by: string
					activity_date: string
					duration_minutes: number | null
					outcome: string | null
					next_action: string | null
					created_at: string
					updated_at: string
				}
				Insert: {
					id?: string
					lead_id: string
					activity_type: string
					subject?: string | null
					description?: string | null
					performed_by: string
					activity_date?: string
					duration_minutes?: number | null
					outcome?: string | null
					next_action?: string | null
					created_at?: string
					updated_at?: string
				}
				Update: {
					id?: string
					lead_id?: string
					activity_type?: string
					subject?: string | null
					description?: string | null
					performed_by?: string
					activity_date?: string
					duration_minutes?: number | null
					outcome?: string | null
					next_action?: string | null
					created_at?: string
					updated_at?: string
				}
				Relationships: [
					{
						foreignKeyName: "lead_activities_lead_id_fkey"
						columns: ["lead_id"]
						isOneToOne: false
						referencedRelation: "lead_contacts"
						referencedColumns: ["id"]
					},
					{
						foreignKeyName: "lead_activities_performed_by_fkey"
						columns: ["performed_by"]
						isOneToOne: false
						referencedRelation: "profiles"
						referencedColumns: ["user_id"]
					}
				]
			}
			marketing_analytics: {
				Row: {
					id: string
					campaign_id: string | null
					date: string
					metric_type: string
					metric_name: string
					metric_value: number
					dimensions: Json | null
					created_at: string
					updated_at: string
				}
				Insert: {
					id?: string
					campaign_id?: string | null
					date: string
					metric_type: string
					metric_name: string
					metric_value: number
					dimensions?: Json | null
					created_at?: string
					updated_at?: string
				}
				Update: {
					id?: string
					campaign_id?: string | null
					date?: string
					metric_type?: string
					metric_name?: string
					metric_value?: number
					dimensions?: Json | null
					created_at?: string
					updated_at?: string
				}
				Relationships: [
					{
						foreignKeyName: "marketing_analytics_campaign_id_fkey"
						columns: ["campaign_id"]
						isOneToOne: false
						referencedRelation: "lead_campaigns"
						referencedColumns: ["id"]
					}
				]
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
			get_current_tenant: {
				Args: Record<PropertyKey, never>
				Returns: string
			}
			generate_referral_code: {
				Args: Record<PropertyKey, never>
				Returns: string
			}
			get_user_referral_stats: {
				Args: {
					user_uuid: string
				}
				Returns: {
					total_referrals: number
					converted_referrals: number
					total_rewards: number
					pending_rewards: number
				}
			}
			track_referral_conversion: {
				Args: {
					referral_code_param: string
					new_user_id: string
				}
				Returns: boolean
			}
			calculate_lead_score: {
				Args: {
					lead_uuid: string
				}
				Returns: number
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
