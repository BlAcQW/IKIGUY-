import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import { getEnvironmentConfig } from './lib/env'

// Validate environment variables on app startup
try {
  getEnvironmentConfig();
  console.log('✅ Environment validation passed');
} catch (error) {
  console.error('❌ Environment validation failed:', error);
  // In development, show error in UI
  if (import.meta.env.DEV) {
    const root = document.getElementById("root");
    if (root) {
      root.innerHTML = `
        <div style="padding: 20px; font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto;">
          <h1 style="color: #dc2626;">🚨 Environment Configuration Error</h1>
          <p>Please check your .env file and ensure all required environment variables are set.</p>
          <pre style="background: #f3f4f6; padding: 15px; border-radius: 5px; overflow-x: auto;">
${error instanceof Error ? error.message : 'Unknown error'}
          </pre>
          <p><strong>Required variables:</strong></p>
          <ul>
            <li>VITE_SUPABASE_URL</li>
            <li>VITE_SUPABASE_ANON_KEY</li>
            <li>VITE_VAPI_PUBLIC_KEY</li>
          </ul>
          <p>Copy .env.example to .env and fill in your actual values.</p>
        </div>
      `;
    }
    throw error;
  }
}

createRoot(document.getElementById("root")!).render(<App />);
