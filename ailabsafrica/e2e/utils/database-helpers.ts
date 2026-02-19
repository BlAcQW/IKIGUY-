import { supabase } from '../../src/integrations/supabase/client';

export interface TestAssistant {
  id: string;
  assistant_name: string;
  description: string;
  assistant_type: string;
  voice_id: string;
  user_id: string;
  created_at: string;
}

export interface TestUser {
  id: string;
  email: string;
  created_at: string;
}

export class DatabaseTestHelpers {
  /**
   * Create a test user for E2E testing
   */
  static async createTestUser(email: string, password: string): Promise<TestUser> {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      throw new Error(`Failed to create test user: ${error.message}`);
    }

    return {
      id: data.user!.id,
      email: data.user!.email!,
      created_at: data.user!.created_at,
    };
  }

  /**
   * Delete a test user and all associated data
   */
  static async deleteTestUser(userId: string): Promise<void> {
    // Delete all assistants created by this user
    const { error: assistantsError } = await supabase
      .from('assistants')
      .delete()
      .eq('user_id', userId);

    if (assistantsError) {
      console.warn(`Failed to delete assistants for user ${userId}:`, assistantsError);
    }

    // Delete all demos created by this user
    const { error: demosError } = await supabase
      .from('demos')
      .delete()
      .eq('user_id', userId);

    if (demosError) {
      console.warn(`Failed to delete demos for user ${userId}:`, demosError);
    }

    // Note: We can't delete the user directly via Supabase client
    // This would need to be done via admin API or database trigger
    console.log(`Test user ${userId} data cleaned up. User account remains for security.`);
  }

  /**
   * Get all assistants for a user
   */
  static async getUserAssistants(userId: string): Promise<TestAssistant[]> {
    const { data, error } = await supabase
      .from('assistants')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (error) {
      throw new Error(`Failed to get user assistants: ${error.message}`);
    }

    return data || [];
  }

  /**
   * Verify that an assistant was created in the database
   */
  static async verifyAssistantCreated(
    userId: string,
    assistantName: string,
    description: string,
    assistantType: string,
    voiceId: string
  ): Promise<TestAssistant> {
    const assistants = await this.getUserAssistants(userId);
    
    const assistant = assistants.find(
      a => a.assistant_name === assistantName &&
           a.description === description &&
           a.assistant_type === assistantType &&
           a.voice_id === voiceId
    );

    if (!assistant) {
      throw new Error(`Assistant not found in database: ${assistantName}`);
    }

    return assistant;
  }

  /**
   * Clean up all test data created during E2E tests
   */
  static async cleanupTestData(): Promise<void> {
    const testEmailPattern = /test-e2e.*@example\.com/;
    
    // Get all test users
    const { data: users, error: usersError } = await supabase.auth.admin.listUsers();
    
    if (usersError) {
      console.warn('Failed to list users for cleanup:', usersError);
      return;
    }

    const testUsers = users.users.filter(user => 
      user.email && testEmailPattern.test(user.email)
    );

    // Clean up each test user
    for (const user of testUsers) {
      await this.deleteTestUser(user.id);
    }

    console.log(`Cleaned up ${testUsers.length} test users`);
  }

  /**
   * Wait for an assistant to be created in the database
   */
  static async waitForAssistantCreation(
    userId: string,
    assistantName: string,
    timeoutMs: number = 30000
  ): Promise<TestAssistant> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeoutMs) {
      try {
        const assistants = await this.getUserAssistants(userId);
        const assistant = assistants.find(a => a.assistant_name === assistantName);
        
        if (assistant) {
          return assistant;
        }
      } catch (error) {
        console.warn('Error checking for assistant:', error);
      }
      
      // Wait 1 second before checking again
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`Assistant ${assistantName} was not created within ${timeoutMs}ms`);
  }
}
