users shoud be able to use this template to create helpdesk demos for different clients.

when i select it, it should ask for the name of the company.
Default name should be Premier Health Insurance.

It should have a text field for description. Preconfigure to use default description: @apps/automations/premier-health/premeir_default_company_info.md

It should have a field for company url. Preconfigure with default url: https://premierhealthinsurance.org/

The next stage in the flow should allow users to extract information from the website and combine that with provided description to create a system prompt for the agent.
Preconfigure with default prompt: 
 able to use site extraction tool to ectract info from the url when needed as used in creating voice agents and combine that info with whatever is in the company info field and generate system prompt for vapi agent

preconfigure it to find a good helpdesk n8n automation template using :
    "n8n-workflows Docs": {
      "url": "https://gitmcp.io/Zie619/n8n-workflows/blob/main/README.md"
    }
and the n8n mcp

also preconfigure it to create a vapi assistant that integrates with the n8n workflow

use calendly to provide it tools for checking availability and booking appointments

use supabase for recording information from the call including summary

use tavily to give it web search capabilities

use resend to enable it send email to ailabsafrica@gmail.com 

enable it to send sms using vonage and resend for emails to users upon request

here is an example of an n8n, vapi integration with tools

provide a checkbox for provide demo. let it be checked by default. 

if demo is checked use our llm with fallback system to create an html similar to whats used in creating voice agents in /voice-agent ....
replace the assistant-id with the id from the vapi assistant created.
replace the content with the content from the company information provided
use the api call using /deploy-demo in ... to create a demo providing the html. see how /deploy-demo is used in ...
i should be able to see  a list of all helpdesks deployed
they should have a link to preview demo
they should have a link to view call analytics - this will be gathered using the vapi webhook and n8n mcp tools for monitoring the automation as well as database info
check example implementations
i should be able  



SUMMARY:
Voice AI (e.g., VAPI): Vonage for calls; webhook to n8n; store call summaries in Supabase; route to ticketing Freshdesk.

RAG helpdesk bot: LangChain + vector DB Pinecone over KB; escalate to human via ticket creation.

Automation: n8n glues everything—intake → classify → answer or escalate → notify on-call → log/analytics.

Analytics: pipe events to Supabase → Metabase dashboards for SLA, FRT, CSAT.