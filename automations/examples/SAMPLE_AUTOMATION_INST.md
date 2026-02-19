 create a frontdesk assistant
  automation template with category/industry generic. use
  the n8n service in @apps/core_backend/backend/services/integration_service.py  to search and find an excellent n8n workflow for helpdesks. let it
  integrate with freshdesk, resend to send emails to ailabsafrica@gmail.com with a summary of every call (there should be an n8n node that uses a chat agent to summarize the call transcript from vapi), tavily to make internet searches, freshnet to create tickets, and calendly to
  check availability and create appointments and save all calls to supabase table 
  
  frontdesk-assistant. 
  
  use the supabase mcp in the integration_service.py to create this table in the demo database. all api keys and info for required tools are here:
  @apps/automations/examples/integration_api_keys.md   . all the tool services are @apps/core_backend/backend/services/integration_service.py  . set the default transfer number to default number be +12397783680. 
  
  use info as default info: http://ggbpartners.com/ - GG&B Ghana. check the website for info for the system prompt etc