import { createClient } from '@supabase/supabase-js'

// These would normally come from environment variables
// For development, using placeholder values - replace with real values
const supabaseUrl = process.env.VITE_SUPABASE_URL || 'https://your-project.supabase.co'
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY || 'your-anon-key'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Database types for TypeScript
export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          username: string | null
          full_name: string | null
          avatar_url: string | null
          email: string
          level: string
          total_points: number
          verified_languages: string[]
          language_expertise: Array<{
            language_code: string
            language_name: string
            proficiency_level: string
          }>
          can_validate: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          username?: string | null
          full_name?: string | null
          avatar_url?: string | null
          email: string
          level?: string
          total_points?: number
          verified_languages?: string[]
          language_expertise?: Array<{
            language_code: string
            language_name: string
            proficiency_level: string
          }>
          can_validate?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          username?: string | null
          full_name?: string | null
          avatar_url?: string | null
          email?: string
          level?: string
          total_points?: number
          verified_languages?: string[]
          language_expertise?: Array<{
            language_code: string
            language_name: string
            proficiency_level: string
          }>
          can_validate?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      submissions: {
        Row: {
          id: string
          user_id: string
          language_code: string
          type: 'text' | 'audio' | 'link'
          title: string
          description: string
          text_content: string | null
          audio_url: string | null
          external_url: string | null
          file_url: string | null
          status: 'pending' | 'approved' | 'rejected' | 'draft'
          validation_status: 'pending' | 'validated' | 'disputed'
          quality_score: number | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          language_code: string
          type: 'text' | 'audio' | 'link'
          title: string
          description: string
          text_content?: string | null
          audio_url?: string | null
          external_url?: string | null
          file_url?: string | null
          status?: 'pending' | 'approved' | 'rejected' | 'draft'
          validation_status?: 'pending' | 'validated' | 'disputed'
          quality_score?: number | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          language_code?: string
          type?: 'text' | 'audio' | 'link'
          title?: string
          description?: string
          text_content?: string | null
          audio_url?: string | null
          external_url?: string | null
          file_url?: string | null
          status?: 'pending' | 'approved' | 'rejected' | 'draft'
          validation_status?: 'pending' | 'validated' | 'disputed'
          quality_score?: number | null
          created_at?: string
          updated_at?: string
        }
      }
      languages: {
        Row: {
          code: string
          name: string
          native_name: string
          family: string
          iso639_1: string | null
          iso639_2: string
          iso639_3: string
          speakers: number
          countries: string[]
          regions: string[]
          writing_systems: string[]
          status: string
          description: string
          created_at: string
          updated_at: string
        }
      }
      validations: {
        Row: {
          id: string
          submission_id: string
          validator_id: string
          action: 'approve' | 'reject' | 'request_changes'
          quality_rating: number
          confidence_level: number
          comments: string | null
          specific_issues: string[]
          suggested_corrections: string | null
          created_at: string
        }
        Insert: {
          id?: string
          submission_id: string
          validator_id: string
          action: 'approve' | 'reject' | 'request_changes'
          quality_rating: number
          confidence_level: number
          comments?: string | null
          specific_issues?: string[]
          suggested_corrections?: string | null
          created_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}