-- Fix function security: Set search_path for create_stripe_checkout_session function
CREATE OR REPLACE FUNCTION public.create_stripe_checkout_session(bundle_minutes integer, bundle_price numeric, bundle_tier text)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  session_id TEXT;
BEGIN
  -- This would normally create a Stripe session
  -- For now, return a mock session ID
  session_id := 'cs_test_' || gen_random_uuid();
  RETURN session_id;
END;
$$;