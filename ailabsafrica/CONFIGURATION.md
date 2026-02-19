# Configuration Guide

This guide will help you set up all the necessary environment variables and API keys for the AI Labs Africa platform.

## 🔧 Environment Variables

Create a `.env` file in the root directory with the following variables:

### Required Variables

```bash
# Supabase Configuration
VITE_SUPABASE_URL=your_supabase_url_here
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Google Gemini AI (for conversation summaries)
VITE_GEMINI_API_KEY=your_gemini_api_key_here

# Vapi Configuration (for voice AI)
VITE_VAPI_API_KEY=your_vapi_api_key_here
VITE_VAPI_WEBHOOK_SECRET=your_vapi_webhook_secret_here
```

### Optional Variables

```bash
# Analytics and Monitoring
VITE_GOOGLE_ANALYTICS_ID=your_ga4_id_here
VITE_SENTRY_DSN=your_sentry_dsn_here

# Payment Processing
VITE_STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key_here
VITE_STRIPE_SECRET_KEY=your_stripe_secret_key_here

# Email Service
VITE_SENDGRID_API_KEY=your_sendgrid_api_key_here
VITE_FROM_EMAIL=noreply@yourdomain.com

# SMS Service
VITE_TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
VITE_TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
VITE_TWILIO_PHONE_NUMBER=your_twilio_phone_number_here
```

## 🔑 API Key Setup

### 1. Google Gemini AI

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key and add it to your `.env` file as `VITE_GEMINI_API_KEY`

### 2. Vapi

1. Go to [Vapi Dashboard](https://dashboard.vapi.ai/)
2. Navigate to API Keys section
3. Create a new API key
4. Copy the key and add it to your `.env` file as `VITE_VAPI_API_KEY`

### 3. Supabase

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to Settings > API
4. Copy the URL and anon key
5. Add them to your `.env` file

## 🌐 Webhook Configuration

### Vapi Webhook Setup

1. Deploy the webhook function to Supabase:
   ```bash
   supabase functions deploy vapi-webhook
   ```

2. Get your webhook URL:
   ```
   https://your-project.supabase.co/functions/v1/vapi-webhook
   ```

3. Configure the webhook in Vapi Dashboard:
   - Go to Settings > Webhooks
   - Add your webhook URL
   - Select the events you want to receive:
     - `call-start`
     - `call-end`
     - `end-of-call-report`
     - `transcript`

4. Set the webhook secret in your `.env` file as `VITE_VAPI_WEBHOOK_SECRET`

## 🚀 Deployment Configuration

### Supabase Edge Functions

Make sure to set the following environment variables in your Supabase dashboard:

1. Go to Settings > Edge Functions
2. Add the following variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `VAPI_WEBHOOK_SECRET`

### Production Environment

For production deployment, ensure all environment variables are properly set in your hosting platform (Vercel, Netlify, etc.).

## 🔒 Security Notes

- Never commit your `.env` file to version control
- Use different API keys for development and production
- Regularly rotate your API keys
- Monitor API usage to avoid unexpected costs

## 🧪 Testing Configuration

To test your configuration:

1. Start the development server:
   ```bash
   npm run dev
   ```

2. Check the browser console for any configuration errors

3. Test the Gemini integration by generating a summary in the Voice Agent Details page

4. Test the Vapi webhook by making a test call

## 📞 Support

If you encounter any issues with configuration:

1. Check the browser console for error messages
2. Verify all API keys are correct and have proper permissions
3. Ensure your Supabase project is properly set up
4. Check the Vapi dashboard for webhook delivery status

For additional help, refer to the documentation or contact support.
