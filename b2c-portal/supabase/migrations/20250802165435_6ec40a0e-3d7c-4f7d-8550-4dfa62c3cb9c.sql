-- Enable Google OAuth provider settings (this will be configured in Supabase dashboard)
-- No SQL changes needed for OAuth providers as they're configured in dashboard

-- Create function to handle new user signup and create workspace
CREATE OR REPLACE FUNCTION public.handle_new_user_signup()
RETURNS TRIGGER AS $$
BEGIN
  -- Insert into profiles table with workspace
  INSERT INTO public.profiles (user_id, display_name, workspace_name)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
    COALESCE(NEW.raw_user_meta_data->>'workspace_name', 'My Workspace')
  );
  
  -- Create initial usage summary
  INSERT INTO public.usage_summary (user_id, minutes_included, current_balance)
  VALUES (NEW.id, 100, 100.00); -- Start with 100 free minutes and $100 balance
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user_signup();