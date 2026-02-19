-- Fix the search path issue for security
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
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';