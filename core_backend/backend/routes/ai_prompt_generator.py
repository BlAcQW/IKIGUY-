"""
AI-powered System Prompt Generator

This module provides functionality to generate system prompts for VAPI agents
by analyzing website content and tailoring prompts based on agent types.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Any, Optional, List
import httpx
import logging
from datetime import datetime
import re
from bs4 import BeautifulSoup
import openai
import anthropic
import asyncio
import os
from ..services.gemini_service import get_gemini_service
from fastapi import UploadFile, File
import PyPDF2
import docx
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Prompt Generator"])

# Load MASTER_TEMPLATE.md content
def load_master_template():
    """Load the MASTER_TEMPLATE.md content for VAPI integration."""
    try:
        template_path = "/opt/kasaai/apps/automations/templates/MASTER_TEMPLATE.md"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.warning(f"Could not load MASTER_TEMPLATE.md: {e}")
        return ""

MASTER_TEMPLATE = load_master_template()

class ContentExtractionRequest(BaseModel):
    website_url: Optional[HttpUrl] = Field(None, description="Primary website URL to analyze (deprecated, use website_urls)")
    website_urls: Optional[List[HttpUrl]] = Field(None, description="List of website URLs to analyze")
    documents: Optional[List[Dict[str, str]]] = Field(None, description="List of documents with name and content")
    enable_crawling: Optional[bool] = Field(False, description="Enable website crawling for comprehensive analysis")
    max_crawl_pages: Optional[int] = Field(5, description="Maximum pages to crawl per website (1-10)")
    use_firecrawl: Optional[bool] = Field(True, description="Use Firecrawl for enhanced content extraction")
    use_ai_extraction: Optional[bool] = Field(True, description="Use AI models for intelligent content extraction")
    ai_extraction_provider: Optional[str] = Field("gemini", description="AI provider for extraction (gemini, anthropic, openai)")
    # Reason: Changed default from firecrawl_first to ai_first for better content extraction
    extraction_priority: Optional[str] = Field("ai_first", description="Extraction method priority (firecrawl_first, ai_first, ai_only, firecrawl_only)")

class SystemPromptGenerate(BaseModel):
    website_url: Optional[HttpUrl] = Field(None, description="Primary website URL to analyze (deprecated, use website_urls)")
    website_urls: Optional[List[HttpUrl]] = Field(None, description="List of website URLs to analyze")
    documents: Optional[List[Dict[str, str]]] = Field(None, description="List of documents with name and content")
    extracted_content: Optional[str] = Field(None, description="Pre-extracted content from websites and documents")
    agent_type: str = Field(..., description="Type of agent to create")
    language: str = Field("en", description="Primary language for the prompt")
    company_name: Optional[str] = Field(None, description="Company name override")
    additional_context: Optional[str] = Field(None, description="Additional context or requirements")
    enable_crawling: Optional[bool] = Field(False, description="Enable website crawling for comprehensive analysis")
    max_crawl_pages: Optional[int] = Field(5, description="Maximum pages to crawl per website (1-10)")
    use_firecrawl: Optional[bool] = Field(True, description="Use Firecrawl for enhanced content extraction")
    use_ai_extraction: Optional[bool] = Field(True, description="Use AI models for intelligent content extraction")
    ai_extraction_provider: Optional[str] = Field("gemini", description="AI provider for extraction (gemini, anthropic, openai)")
    # Reason: Changed default from firecrawl_first to ai_first for better content extraction
    extraction_priority: Optional[str] = Field("ai_first", description="Extraction method priority (firecrawl_first, ai_first, ai_only, firecrawl_only)")


class VAPISystemPromptGenerate(BaseModel):
    website_url: Optional[HttpUrl] = Field(None, description="Company website URL to analyze")
    website_urls: Optional[List[HttpUrl]] = Field(None, description="List of website URLs to analyze")
    documents: Optional[List[Dict[str, str]]] = Field(None, description="List of documents with name and content")
    extracted_content: Optional[str] = Field(None, description="Pre-extracted content from websites and documents")
    company_name: Optional[str] = Field(None, description="Company name override")
    business_type: Optional[str] = Field(None, description="Business type (e.g., healthcare, retail, finance)")
    primary_service: Optional[str] = Field(None, description="Primary service or focus area")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    additional_context: Optional[str] = Field(None, description="Additional context or requirements")
    language: str = Field("en", description="Primary language for the prompt")
    enable_crawling: Optional[bool] = Field(False, description="Enable website crawling for comprehensive analysis")
    max_crawl_pages: Optional[int] = Field(5, description="Maximum pages to crawl per website (1-10)")
    use_firecrawl: Optional[bool] = Field(True, description="Use Firecrawl for enhanced content extraction")

class SystemPromptResponse(BaseModel):
    success: bool
    system_prompt: str
    suggested_description: str
    analyzed_content: Dict[str, Any]
    agent_type: str
    language: str

class VAPISystemPromptResponse(BaseModel):
    success: bool
    system_prompt: str
    suggested_description: str
    analyzed_content: Dict[str, Any]
    master_template_integrated: bool
    language: str
    vapi_optimized: bool


# Agent type templates and configurations
AGENT_TEMPLATES = {
    "helpdesk": {
        "role": "customer support specialist",
        "primary_goal": "resolve customer issues efficiently and professionally",
        "key_behaviors": [
            "Listen actively to customer concerns",
            "Provide step-by-step troubleshooting guidance",
            "Escalate complex issues when necessary",
            "Follow up to ensure resolution",
            "Maintain a helpful and patient tone"
        ],
        "tools_focus": ["knowledge_base", "ticket_creation", "escalation"]
    },
    "sales": {
        "role": "sales representative",
        "primary_goal": "qualify leads and drive conversions through consultative selling",
        "key_behaviors": [
            "Ask qualifying questions to understand needs",
            "Present relevant solutions and benefits",
            "Handle objections professionally",
            "Create urgency when appropriate",
            "Schedule follow-up meetings"
        ],
        "tools_focus": ["calendar", "crm", "lead_scoring", "email"]
    },
    "political": {
        "role": "political campaign assistant",
        "primary_goal": "engage voters and build support for the candidate/cause",
        "key_behaviors": [
            "Share candidate's key positions and achievements",
            "Address voter concerns with factual information",
            "Encourage voter registration and turnout",
            "Collect voter sentiment data",
            "Maintain respectful political discourse"
        ],
        "tools_focus": ["voter_database", "survey", "event_scheduling"]
    },
    "church": {
        "role": "church ministry assistant",
        "primary_goal": "support congregation members and facilitate church connections",
        "key_behaviors": [
            "Provide spiritual encouragement and support",
            "Share information about church services and events",
            "Connect members with appropriate ministries",
            "Collect prayer requests and follow up",
            "Maintain confidentiality and compassion"
        ],
        "tools_focus": ["member_directory", "event_calendar", "prayer_requests"]
    },
    "survey": {
        "role": "research assistant",
        "primary_goal": "collect high-quality survey responses and data",
        "key_behaviors": [
            "Ask clear, unbiased questions",
            "Encourage honest and complete responses",
            "Maintain participant engagement throughout",
            "Ensure data privacy and confidentiality",
            "Provide appropriate incentives or appreciation"
        ],
        "tools_focus": ["survey_platform", "data_collection", "analytics"]
    },
    "appointment": {
        "role": "appointment scheduler",
        "primary_goal": "efficiently schedule and manage appointments",
        "key_behaviors": [
            "Check availability in real-time",
            "Confirm appointment details clearly",
            "Send confirmation and reminder messages",
            "Handle rescheduling requests professionally",
            "Collect necessary information before booking"
        ],
        "tools_focus": ["calendar", "scheduling", "notifications", "crm"]
    },
    "lead_gen": {
        "role": "lead generation specialist", 
        "primary_goal": "identify and qualify potential customers",
        "key_behaviors": [
            "Engage prospects with compelling value propositions",
            "Ask strategic qualifying questions",
            "Capture complete contact information",
            "Schedule demos or sales meetings",
            "Nurture leads through the funnel"
        ],
        "tools_focus": ["crm", "lead_scoring", "calendar", "email"]
    },
    "education": {
        "role": "educational assistant",
        "primary_goal": "support student learning and engagement",
        "key_behaviors": [
            "Provide clear explanations and examples",
            "Adapt communication style to student level",
            "Encourage questions and curiosity",
            "Track student progress and needs",
            "Connect students with appropriate resources"
        ],
        "tools_focus": ["learning_management", "progress_tracking", "resources"]
    },
    "healthcare": {
        "role": "healthcare support assistant",
        "primary_goal": "provide health information and appointment support",
        "key_behaviors": [
            "Provide accurate health information within scope",
            "Schedule medical appointments efficiently",
            "Handle sensitive information with HIPAA compliance",
            "Offer comfort and support to patients",
            "Direct urgent matters to appropriate medical staff"
        ],
        "tools_focus": ["appointment_scheduling", "patient_records", "medical_resources"]
    },
    "custom": {
        "role": "specialized assistant",
        "primary_goal": "fulfill custom business requirements effectively",
        "key_behaviors": [
            "Adapt to specific business processes",
            "Maintain professional communication standards",
            "Follow custom workflows and procedures",
            "Provide consistent service delivery",
            "Escalate when outside defined scope"
        ],
        "tools_focus": ["custom_integrations", "workflow_automation"]
    }
}


@router.post("/extract-content")
async def extract_content(request: ContentExtractionRequest):
    """
    Extract and combine content from websites and documents for user review.
    
    This is the first step of the two-step process where users can review
    the extracted content before generating the system prompt.
    """
    try:
        extracted_sections = []
        
        # Prepare all website URLs for analysis
        urls_to_analyze = []
        if request.website_url:
            urls_to_analyze.append(str(request.website_url))
        if request.website_urls:
            urls_to_analyze.extend([str(url) for url in request.website_urls])
        
        # Extract content from websites using priority-based extraction
        if urls_to_analyze:
            extracted_sections.append("=== WEBSITE CONTENT ===")

            try:
                # Determine extraction method based on priority
                analysis = await _extract_websites_with_priority(
                    urls=urls_to_analyze,
                    extraction_priority=request.extraction_priority,
                    use_firecrawl=request.use_firecrawl,
                    use_ai_extraction=request.use_ai_extraction,
                    ai_extraction_provider=request.ai_extraction_provider,
                    enable_crawling=request.enable_crawling,
                    max_crawl_pages=min(request.max_crawl_pages, 10)
                )

                # Format the extracted content
                if len(urls_to_analyze) == 1:
                    extracted_sections.append(f"\n--- {analysis['url']} ({analysis.get('extraction_method', 'unknown')}) ---")
                else:
                    extracted_sections.append(f"\n--- Multiple URLs ({analysis.get('extraction_method', 'unknown')}) ---")
                    extracted_sections.append(f"URLs Analyzed: {len(analysis.get('urls', []))}")

                extracted_sections.append(f"Title: {analysis['title']}")
                extracted_sections.append(f"Company: {analysis['company_info']['name']}")
                extracted_sections.append(f"Description: {analysis['company_info']['description']}")
                extracted_sections.append(f"Business Type: {analysis['business_type']}")
                extracted_sections.append(f"Extraction Method: {analysis.get('extraction_method', 'unknown')}")

                if analysis.get('ai_provider_used'):
                    extracted_sections.append(f"AI Provider: {analysis['ai_provider_used']}")

                if analysis.get('pages_crawled'):
                    extracted_sections.append(f"Pages Crawled: {analysis['pages_crawled']}")

                if analysis['services_products']:
                    extracted_sections.append(f"Services/Products: {', '.join(analysis['services_products'][:15])}")

                if analysis['contact_info']:
                    contact_parts = []
                    for key, value in analysis['contact_info'].items():
                        if value:
                            contact_parts.append(f"{key}: {value}")
                    if contact_parts:
                        extracted_sections.append(f"Contact: {', '.join(contact_parts)}")

                extracted_sections.append(f"\nContent:\n{analysis['company_info']['full_content']}")
                extracted_sections.append("")

            except Exception as extraction_error:
                logger.error(f"All extraction methods failed: {str(extraction_error)}")
                extracted_sections.append(f"\n--- EXTRACTION FAILED ---")
                extracted_sections.append(f"Error: {str(extraction_error)}")
                extracted_sections.append("")
        
        # Extract content from documents
        if request.documents:
            extracted_sections.append("\n=== DOCUMENT CONTENT ===")
            
            for doc in request.documents:
                doc_name = doc.get("name", "Unknown Document")
                doc_content = doc.get("content", "")
                
                extracted_sections.append(f"\n--- {doc_name} ---")
                if doc_content:
                    extracted_sections.append(doc_content)
                else:
                    extracted_sections.append("No content available")
                extracted_sections.append("")
        
        # Combine all extracted content
        combined_content = "\n".join(extracted_sections)
        
        if not combined_content.strip():
            return {
                "success": False,
                "error": "No content could be extracted from the provided sources"
            }
        
        return {
            "success": True,
            "extracted_content": combined_content,
            "sources_analyzed": {
                "websites": len(urls_to_analyze),
                "documents": len(request.documents) if request.documents else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/generate-system-prompt", response_model=SystemPromptResponse)
async def generate_system_prompt(
    request: SystemPromptGenerate,
    background_tasks: BackgroundTasks
):
    """
    Generate a customized system prompt for a VAPI agent based on website analysis.
    
    This endpoint:
    1. Scrapes and analyzes the provided website
    2. Extracts key business information and context
    3. Combines website content with agent type requirements
    4. Generates a tailored system prompt using AI
    """
    try:
        # Check if we have pre-extracted content
        if request.extracted_content:
            # Use pre-extracted content - skip website/document analysis
            combined_analysis = create_analysis_from_extracted_content(request.extracted_content)
            documents_content = ""  # Already included in extracted content
        else:
            # Enhanced flow - analyze websites and documents with Firecrawl
            urls_to_analyze = []
            if request.website_url:
                urls_to_analyze.append(str(request.website_url))
            if request.website_urls:
                urls_to_analyze.extend([str(url) for url in request.website_urls])

            # Use priority-based extraction for enhanced analysis
            combined_analysis = await _extract_websites_with_priority(
                urls=urls_to_analyze,
                extraction_priority=request.extraction_priority,
                use_firecrawl=request.use_firecrawl,
                use_ai_extraction=request.use_ai_extraction,
                ai_extraction_provider=request.ai_extraction_provider,
                enable_crawling=request.enable_crawling,
                max_crawl_pages=min(request.max_crawl_pages, 10)
            )

            # Process documents if provided
            documents_content = ""
            if request.documents:
                documents_content = process_documents(request.documents)
        
        # Get agent template
        agent_template = AGENT_TEMPLATES.get(request.agent_type, AGENT_TEMPLATES["custom"])
        
        # Generate system prompt using AI with enhanced content
        system_prompt = await generate_ai_system_prompt_enhanced(
            website_analysis=combined_analysis,
            documents_content=documents_content,
            agent_template=agent_template,
            agent_type=request.agent_type,
            language=request.language,
            company_name=request.company_name,
            additional_context=request.additional_context
        )
        
        # Generate suggested description
        suggested_description = generate_agent_description(
            combined_analysis["company_info"],
            agent_template,
            request.agent_type
        )
        
        # Log the generation for analytics
        primary_url = None
        if request.website_url:
            primary_url = str(request.website_url)
        elif request.website_urls:
            primary_url = str(request.website_urls[0])
        
        background_tasks.add_task(
            log_prompt_generation,
            website_url=primary_url or "multiple_sources",
            agent_type=request.agent_type,
            success=True
        )
        
        return SystemPromptResponse(
            success=True,
            system_prompt=system_prompt,
            suggested_description=suggested_description,
            analyzed_content=combined_analysis,
            agent_type=request.agent_type,
            language=request.language
        )
        
    except Exception as e:
        logger.error(f"Error generating system prompt: {str(e)}")
        
        # Log the failed generation
        primary_url = None
        if request.website_url:
            primary_url = str(request.website_url)
        elif request.website_urls:
            primary_url = str(request.website_urls[0])
            
        background_tasks.add_task(
            log_prompt_generation,
            website_url=primary_url or "multiple_sources",
            agent_type=request.agent_type,
            success=False,
            error=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate system prompt: {str(e)}"
        )


@router.post("/generate-vapi-system-prompt", response_model=VAPISystemPromptResponse)
async def generate_vapi_system_prompt(
    request: VAPISystemPromptGenerate,
    background_tasks: BackgroundTasks
):
    """
    Generate a VAPI-optimized system prompt that integrates MASTER_TEMPLATE.md
    with company-specific information extracted from websites.

    This endpoint:
    1. Extracts company information from provided website(s)
    2. Integrates MASTER_TEMPLATE.md content for VAPI optimization
    3. Generates a comprehensive system prompt with tools and policies
    4. Returns VAPI-ready prompt with webhook configuration
    """
    try:
        # Check if we have pre-extracted content
        if request.extracted_content:
            # Use pre-extracted content - skip website analysis
            combined_analysis = create_analysis_from_extracted_content(request.extracted_content)
        else:
            # Analyze websites with enhanced extraction
            urls_to_analyze = []
            if request.website_url:
                urls_to_analyze.append(str(request.website_url))
            if request.website_urls:
                urls_to_analyze.extend([str(url) for url in request.website_urls])

            if urls_to_analyze:
                # Use priority-based extraction for comprehensive analysis
                combined_analysis = await _extract_websites_with_priority(
                    urls=urls_to_analyze,
                    extraction_priority="firecrawl_first",
                    use_firecrawl=request.use_firecrawl,
                    use_ai_extraction=True,
                    ai_extraction_provider="gemini",
                    enable_crawling=request.enable_crawling,
                    max_crawl_pages=min(request.max_crawl_pages, 10)
                )
            else:
                # Create minimal analysis for template-only generation
                combined_analysis = {
                    "company_info": {
                        "name": request.company_name or "Your Company",
                        "description": request.business_type or "Professional services",
                        "full_content": request.additional_context or ""
                    },
                    "business_type": request.business_type or "professional services",
                    "services_products": [request.primary_service] if request.primary_service else [],
                    "target_audience": request.target_audience or "customers",
                    "contact_info": {},
                    "tone_style": "professional and helpful",
                    "key_content": []
                }

        # Process documents if provided
        documents_content = ""
        if request.documents:
            documents_content = process_documents(request.documents)
            if documents_content:
                combined_analysis["company_info"]["full_content"] += f"\n\nAdditional Documents:\n{documents_content}"

        # Override with provided values if available
        if request.company_name:
            combined_analysis["company_info"]["name"] = request.company_name
        if request.business_type:
            combined_analysis["business_type"] = request.business_type
        if request.target_audience:
            combined_analysis["target_audience"] = request.target_audience

        # Generate VAPI-optimized system prompt with MASTER_TEMPLATE integration
        system_prompt = await generate_vapi_optimized_prompt(
            website_analysis=combined_analysis,
            language=request.language,
            additional_context=request.additional_context
        )

        # Generate suggested description for VAPI agent
        suggested_description = generate_vapi_agent_description(
            combined_analysis["company_info"],
            combined_analysis["business_type"]
        )

        # Log the generation for analytics
        primary_url = None
        if request.website_url:
            primary_url = str(request.website_url)
        elif request.website_urls:
            primary_url = str(request.website_urls[0])

        background_tasks.add_task(
            log_prompt_generation,
            website_url=primary_url or "template_only",
            agent_type="vapi_optimized",
            success=True
        )

        return VAPISystemPromptResponse(
            success=True,
            system_prompt=system_prompt,
            suggested_description=suggested_description,
            analyzed_content=combined_analysis,
            master_template_integrated=bool(MASTER_TEMPLATE),
            language=request.language,
            vapi_optimized=True
        )

    except Exception as e:
        logger.error(f"Error generating VAPI system prompt: {str(e)}")

        # Log the failed generation
        primary_url = None
        if request.website_url:
            primary_url = str(request.website_url)
        elif request.website_urls:
            primary_url = str(request.website_urls[0])

        background_tasks.add_task(
            log_prompt_generation,
            website_url=primary_url or "template_only",
            agent_type="vapi_optimized",
            success=False,
            error=str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate VAPI system prompt: {str(e)}"
        )


@router.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document for system prompt generation.
    
    Supports PDF, Word, and text files. Extracts text content and returns it
    for integration into the system prompt generation process.
    """
    try:
        # Validate file type
        allowed_types = {
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'text/plain': 'txt'
        }
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}. Supported: PDF, Word, TXT"
            )
        
        # Check file size (5MB limit)
        file_content = await file.read()
        if len(file_content) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 5MB"
            )
        
        # Extract text content based on file type
        file_type = allowed_types[file.content_type]
        extracted_content = extract_document_content(file_content, file_type, file.filename)
        
        if not extracted_content.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text content from the document"
            )
        
        # Limit content length for prompt generation
        max_content_length = 3000  # Reasonable limit for prompt context
        if len(extracted_content) > max_content_length:
            extracted_content = extracted_content[:max_content_length] + "..."
        
        return {
            "success": True,
            "filename": file.filename,
            "content": extracted_content,
            "content_length": len(extracted_content),
            "file_type": file_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )


def extract_document_content(file_content: bytes, file_type: str, filename: str) -> str:
    """
    Extract text content from various document types.
    """
    try:
        if file_type == 'pdf':
            return extract_pdf_content(file_content)
        elif file_type == 'docx':
            return extract_docx_content(file_content)
        elif file_type == 'doc':
            # For .doc files, we'll try to read as text since python-docx doesn't support old format
            return file_content.decode('utf-8', errors='ignore')
        elif file_type == 'txt':
            return file_content.decode('utf-8', errors='ignore')
        else:
            return ""
    except Exception as e:
        logger.error(f"Error extracting content from {filename}: {str(e)}")
        return f"Error extracting content from {filename}. Please try a different file format."


def extract_pdf_content(file_content: bytes) -> str:
    """
    Extract text content from PDF files.
    """
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text_content = []
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text_content.append(page_text)
            except Exception as e:
                logger.warning(f"Error extracting text from PDF page {page_num}: {str(e)}")
                continue
        
        return "\n".join(text_content)
    except Exception as e:
        logger.error(f"Error extracting PDF content: {str(e)}")
        return ""


def extract_docx_content(file_content: bytes) -> str:
    """
    Extract text content from Word documents.
    """
    try:
        doc_file = io.BytesIO(file_content)
        doc = docx.Document(doc_file)
        
        text_content = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)
        
        return "\n".join(text_content)
    except Exception as e:
        logger.error(f"Error extracting DOCX content: {str(e)}")
        return ""


async def analyze_website_content(website_url: str) -> Dict[str, Any]:
    """
    Scrape and analyze website content to extract business context.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch website content
            response = await client.get(website_url, follow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract key information
            analysis = {
                "url": website_url,
                "title": extract_page_title(soup),
                "company_info": extract_company_info(soup),
                "business_type": analyze_business_type(soup),
                "services_products": extract_services_products(soup),
                "contact_info": extract_contact_info(soup),
                "key_content": extract_key_content(soup),
                "tone_style": analyze_tone_style(soup),
                "target_audience": analyze_target_audience(soup),
                "scraped_at": datetime.utcnow().isoformat()
            }
            
            return analysis
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching website {website_url}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Unable to fetch website: {str(e)}")
    except Exception as e:
        logger.error(f"Error analyzing website {website_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Website analysis failed: {str(e)}")


def extract_page_title(soup: BeautifulSoup) -> str:
    """Extract the page title."""
    title_tag = soup.find('title')
    return title_tag.text.strip() if title_tag else ""


def extract_company_info(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract company information from the website."""
    company_info = {
        "name": "",
        "description": "",
        "mission": "",
        "values": [],
        "full_content": ""
    }
    
    # Try to find company name from title first, then other sources
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text()
        # Remove common suffixes
        for suffix in [" | Home", " - Home", " | Official Site", " - Official Website", " | Homepage"]:
            title_text = title_text.replace(suffix, "")
        company_info["name"] = title_text.strip()
    
    # Try other selectors if title isn't good
    if not company_info["name"] or len(company_info["name"]) > 50:
        for selector in ['h1', '.company-name', '.brand', '.logo', '.site-title']:
            element = soup.select_one(selector)
            if element and element.text.strip():
                company_info["name"] = element.text.strip()
                break
    
    # Extract description from meta description or about sections
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        company_info["description"] = meta_desc.get('content', '')
    
    # Look for about/mission/hero sections with more comprehensive search
    about_text = ""
    for selector in ['.about', '.mission', '.company-description', '#about', '.hero', '.intro', '.overview', '.company-info', '.about-us']:
        element = soup.select_one(selector)
        if element:
            text = element.get_text().strip()
            if len(text) > len(about_text) and len(text) > 20:  # Must be substantial content
                about_text = text
    
    # If we found about text and it's better than meta description, use it
    if about_text and len(about_text) > len(company_info["description"]):
        company_info["description"] = about_text[:800] + "..." if len(about_text) > 800 else about_text
    
    # Get overall page content for context - clean it up first
    # Remove unwanted elements
    for unwanted in soup(['nav', 'footer', 'script', 'style', 'header', '.menu', '.navigation']):
        unwanted.decompose()
    
    # Extract main content
    main_content = soup.find('main') or soup.find('.main') or soup.find('#main') or soup
    full_text = main_content.get_text() if main_content else ""
    
    # Clean up whitespace and get first 1200 characters
    full_text = ' '.join(full_text.split())
    company_info["full_content"] = full_text[:1200] + "..." if len(full_text) > 1200 else full_text
    
    return company_info


def analyze_business_type(soup: BeautifulSoup) -> str:
    """Analyze the type of business based on website content."""
    text_content = soup.get_text().lower()
    
    # Business type keywords
    business_types = {
        "healthcare": ["hospital", "clinic", "medical", "doctor", "health", "patient"],
        "education": ["school", "university", "education", "learning", "student", "course"],
        "technology": ["software", "tech", "digital", "app", "platform", "saas"],
        "retail": ["shop", "store", "buy", "product", "shopping", "retail"],
        "finance": ["bank", "finance", "investment", "insurance", "loan", "financial"],
        "legal": ["law", "lawyer", "legal", "attorney", "court", "litigation"],
        "consulting": ["consulting", "consultant", "advisory", "professional services"],
        "nonprofit": ["nonprofit", "charity", "foundation", "donate", "volunteer"]
    }
    
    scores = {}
    for business_type, keywords in business_types.items():
        score = sum(text_content.count(keyword) for keyword in keywords)
        scores[business_type] = score
    
    return max(scores, key=scores.get) if scores else "general"


def extract_services_products(soup: BeautifulSoup) -> List[str]:
    """Extract services or products from the website."""
    services = []
    
    # Look for services/products sections
    for selector in ['.services', '.products', '.offerings', '.solutions']:
        section = soup.select_one(selector)
        if section:
            items = section.find_all(['li', 'h3', 'h4', '.service-item', '.product-item'])
            for item in items[:10]:  # Limit to first 10 items
                text = item.get_text().strip()
                if text and len(text) < 100:
                    services.append(text)
    
    return services


def extract_contact_info(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract contact information."""
    contact_info = {}
    
    text_content = soup.get_text()
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text_content)
    if emails:
        contact_info["email"] = emails[0]
    
    # Phone pattern (US format)
    phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, text_content)
    if phones:
        contact_info["phone"] = phones[0]
    
    return contact_info


def extract_key_content(soup: BeautifulSoup) -> List[str]:
    """Extract key content sections for context."""
    key_content = []
    
    # Extract headings and important text
    for tag in soup.find_all(['h1', 'h2', 'h3', '.hero-text', '.intro']):
        text = tag.get_text().strip()
        if text and len(text) > 10 and len(text) < 200:
            key_content.append(text)
    
    return key_content[:5]  # Limit to top 5 pieces of content


def analyze_tone_style(soup: BeautifulSoup) -> str:
    """Analyze the tone and style of the website."""
    text_content = soup.get_text().lower()
    
    # Tone indicators
    if any(word in text_content for word in ["professional", "corporate", "business", "enterprise"]):
        return "professional"
    elif any(word in text_content for word in ["friendly", "fun", "creative", "innovative"]):
        return "friendly"
    elif any(word in text_content for word in ["caring", "compassionate", "support", "help"]):
        return "supportive"
    else:
        return "balanced"


def analyze_target_audience(soup: BeautifulSoup) -> str:
    """Analyze the target audience based on content."""
    text_content = soup.get_text().lower()

    if any(word in text_content for word in ["business", "enterprise", "corporate", "b2b"]):
        return "business"
    elif any(word in text_content for word in ["customer", "client", "consumer", "individual"]):
        return "consumer"
    else:
        return "general"


async def analyze_website_content_firecrawl(
    website_url: str,
    enable_crawling: bool = False,
    max_crawl_pages: int = 5,
    tenant_id: str = "ai_prompt_generator"
) -> Dict[str, Any]:
    """
    Analyze website content using Firecrawl for enhanced extraction.

    Args:
        website_url (str): URL to analyze
        enable_crawling (bool): Whether to crawl multiple pages
        max_crawl_pages (int): Maximum pages to crawl (1-10)
        tenant_id (str): Tenant ID for analytics tracking

    Returns:
        Dict[str, Any]: Enhanced website analysis
    """
    try:
        from ..services.firecrawl_consolidated_service import get_firecrawl_service

        service = await get_firecrawl_service()

        if enable_crawling and max_crawl_pages > 1:
            # Use crawling for comprehensive analysis
            result = await service.monitor_crawl_for_tenant(
                tenant_id=tenant_id,
                url=website_url,
                max_pages=min(max_crawl_pages, 10),  # Cap at 10 pages
                include_subdomains=False,
                context={"purpose": "ai_prompt_generation"}
            )

            if result.success and result.data and isinstance(result.data, list):
                # Combine content from all crawled pages
                return _process_crawled_pages(result.data, website_url)
            else:
                logger.warning(f"Firecrawl crawling failed for {website_url}, falling back to single page")

        # Single page smart scraping
        result = await service.smart_scrape_for_tenant(
            tenant_id=tenant_id,
            url=website_url,
            extract_type="content",
            context={"purpose": "ai_prompt_generation"}
        )

        if result.success and result.data:
            return _process_single_page(result.data, website_url)
        else:
            raise Exception(f"Firecrawl extraction failed: {result.error}")

    except Exception as e:
        logger.error(f"Firecrawl analysis failed for {website_url}: {str(e)}")
        raise


def _process_single_page(page, website_url: str) -> Dict[str, Any]:
    """
    Process a single Firecrawl page result into the expected analysis format.

    Args:
        page: Firecrawl page object
        website_url (str): Original URL

    Returns:
        Dict[str, Any]: Processed analysis
    """
    # Extract metadata
    metadata = page.metadata or {}
    title = page.title or metadata.get("title", "")
    description = page.description or metadata.get("description", "")

    # Get clean content
    content = page.content or page.markdown or ""

    # Extract company name from title or metadata
    company_name = _extract_company_name_from_content(title, content)

    # Analyze business type from content
    business_type = _analyze_business_type_from_content(content)

    # Extract services/products
    services_products = _extract_services_from_content(content)

    # Extract contact info
    contact_info = _extract_contact_from_content(content)

    # Analyze tone and audience
    tone_style = _analyze_tone_from_content(content)
    target_audience = _analyze_audience_from_content(content)

    return {
        "url": website_url,
        "title": title,
        "company_info": {
            "name": company_name,
            "description": description[:1500] + "..." if len(description) > 1500 else description,
            # Reason: Increased from 2000 to 5000 to capture more comprehensive content
            "full_content": content[:5000] + "..." if len(content) > 5000 else content,
            "mission": "",
            "values": []
        },
        "business_type": business_type,
        "services_products": services_products,
        "contact_info": contact_info,
        "key_content": _extract_key_content_from_text(content),
        "tone_style": tone_style,
        "target_audience": target_audience,
        "scraped_at": datetime.utcnow().isoformat(),
        "extraction_method": "firecrawl_single",
        "metadata": metadata
    }


def _process_crawled_pages(pages: List, website_url: str) -> Dict[str, Any]:
    """
    Process multiple crawled pages into a comprehensive analysis.

    Args:
        pages: List of Firecrawl page objects
        website_url (str): Original starting URL

    Returns:
        Dict[str, Any]: Combined analysis from all pages
    """
    if not pages:
        raise Exception("No pages were crawled")

    # Use first page as primary source
    primary_page = pages[0]
    combined_content = []
    all_services = []
    all_key_content = []
    combined_contact = {}

    for i, page in enumerate(pages):
        content = page.content or page.markdown or ""
        if content:
            combined_content.append(f"=== Page {i+1}: {page.url} ===\n{content}")

            # Extract services from each page
            page_services = _extract_services_from_content(content)
            all_services.extend(page_services)

            # Extract key content
            page_key_content = _extract_key_content_from_text(content)
            all_key_content.extend(page_key_content)

            # Update contact info if we find better information
            page_contact = _extract_contact_from_content(content)
            if len(page_contact) > len(combined_contact):
                combined_contact = page_contact

    # Combine all content
    full_combined_content = "\n\n".join(combined_content)

    # Process primary page for main metadata
    primary_analysis = _process_single_page(primary_page, website_url)

    # Update with combined data
    primary_analysis.update({
        "company_info": {
            **primary_analysis["company_info"],
            # Reason: Increased from 4000 to 8000 for crawled content to capture more pages
            "full_content": full_combined_content[:8000] + "..." if len(full_combined_content) > 8000 else full_combined_content
        },
        "services_products": list(set(all_services))[:20],  # Deduplicate and limit
        "key_content": list(set(all_key_content))[:15],     # Deduplicate and limit
        "contact_info": combined_contact,
        "pages_crawled": len(pages),
        "crawled_urls": [page.url for page in pages],
        "extraction_method": "firecrawl_crawl"
    })

    return primary_analysis


def _extract_company_name_from_content(title: str, content: str) -> str:
    """Extract company name from title and content."""
    if title:
        # Clean up title
        for suffix in [" | Home", " - Home", " | Official Site", " - Official Website", " | Homepage", " – Your Bridge to Premier Healthcare"]:
            title = title.replace(suffix, "")
        # Reason: Increased from 50 to 100 to capture longer company names with taglines
        if title and len(title) < 100:
            return title.strip()

    # Try to find company name in content
    lines = content.split('\n')[:10]  # Check first 10 lines
    for line in lines:
        line = line.strip()
        if line and len(line) < 100 and not any(skip in line.lower() for skip in ["welcome", "home", "about", "contact", "have any questions"]):
            return line

    return "Unknown Company"


def _analyze_business_type_from_content(content: str) -> str:
    """Analyze business type from content."""
    content_lower = content.lower()

    business_types = {
        "healthcare": ["hospital", "clinic", "medical", "doctor", "health", "patient", "medicine"],
        "education": ["school", "university", "education", "learning", "student", "course", "academy"],
        "technology": ["software", "tech", "digital", "app", "platform", "saas", "api"],
        "retail": ["shop", "store", "buy", "product", "shopping", "retail", "marketplace"],
        "finance": ["bank", "finance", "investment", "insurance", "loan", "financial", "credit"],
        "legal": ["law", "lawyer", "legal", "attorney", "court", "litigation", "justice"],
        "consulting": ["consulting", "consultant", "advisory", "professional services", "strategy"],
        "nonprofit": ["nonprofit", "charity", "foundation", "donate", "volunteer", "community"]
    }

    scores = {}
    for business_type, keywords in business_types.items():
        score = sum(content_lower.count(keyword) for keyword in keywords)
        scores[business_type] = score

    return max(scores, key=scores.get) if scores else "general"


def _extract_services_from_content(content: str) -> List[str]:
    """Extract services and products from content."""
    services = []
    lines = content.split('\n')

    # Look for service-related sections
    for line in lines:
        line = line.strip()
        if line and 20 < len(line) < 100:
            # Check if line contains service indicators
            service_indicators = ["service", "product", "solution", "offering", "feature"]
            if any(indicator in line.lower() for indicator in service_indicators):
                services.append(line)

        if len(services) >= 10:  # Limit services
            break

    return services


def _extract_contact_from_content(content: str) -> Dict[str, str]:
    """Extract contact information from content."""
    import re
    contact_info = {}

    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, content)
    if emails:
        contact_info["email"] = emails[0]

    # Phone pattern (multiple formats)
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
        r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'  # International
    ]

    for pattern in phone_patterns:
        phones = re.findall(pattern, content)
        if phones:
            contact_info["phone"] = phones[0]
            break

    return contact_info


def _extract_key_content_from_text(content: str) -> List[str]:
    """Extract key content sections from text."""
    key_content = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        if line and 30 < len(line) < 200:
            # Look for headings or important statements
            if any(indicator in line.lower() for indicator in ["about", "mission", "vision", "what we do", "our"]):
                key_content.append(line)

        if len(key_content) >= 5:
            break

    return key_content


def _analyze_tone_from_content(content: str) -> str:
    """Analyze tone and style from content."""
    content_lower = content.lower()

    if any(word in content_lower for word in ["professional", "corporate", "business", "enterprise", "industry"]):
        return "professional"
    elif any(word in content_lower for word in ["friendly", "fun", "creative", "innovative", "exciting"]):
        return "friendly"
    elif any(word in content_lower for word in ["caring", "compassionate", "support", "help", "community"]):
        return "supportive"
    else:
        return "balanced"


def _analyze_audience_from_content(content: str) -> str:
    """Analyze target audience from content."""
    content_lower = content.lower()

    if any(word in content_lower for word in ["business", "enterprise", "corporate", "b2b", "company"]):
        return "business"
    elif any(word in content_lower for word in ["customer", "client", "consumer", "individual", "personal"]):
        return "consumer"
    else:
        return "general"


async def analyze_multiple_websites_firecrawl(
    urls: List[str],
    enable_crawling: bool = False,
    max_crawl_pages: int = 5,
    tenant_id: str = "ai_prompt_generator"
) -> Dict[str, Any]:
    """
    Analyze multiple websites using Firecrawl with batch processing.

    Args:
        urls (List[str]): List of URLs to analyze
        enable_crawling (bool): Whether to crawl multiple pages
        max_crawl_pages (int): Maximum pages to crawl per website
        tenant_id (str): Tenant ID for analytics tracking

    Returns:
        Dict[str, Any]: Combined analysis from all websites
    """
    if not urls:
        return {
            "urls": [],
            "title": "",
            "company_info": {"name": "", "description": "", "full_content": ""},
            "business_type": "general",
            "services_products": [],
            "contact_info": {},
            "key_content": [],
            "tone_style": "professional",
            "target_audience": "general",
            "scraped_at": datetime.utcnow().isoformat(),
            "extraction_method": "firecrawl_batch"
        }

    try:
        from ..services.firecrawl_consolidated_service import get_firecrawl_service

        service = await get_firecrawl_service()
        all_analyses = []
        successful_urls = []

        if not enable_crawling:
            # Use batch scraping for multiple single pages
            result = await service.batch_scrape_for_tenant(
                tenant_id=tenant_id,
                urls=urls,
                options=None,  # Use default options
                context={"purpose": "ai_prompt_generation"}
            )

            if result.success and result.data and isinstance(result.data, list):
                for i, page in enumerate(result.data):
                    if page.content:
                        analysis = _process_single_page(page, urls[i])
                        all_analyses.append(analysis)
                        successful_urls.append(urls[i])
            else:
                logger.warning(f"Firecrawl batch scraping failed, falling back to individual scraping")
                raise Exception("Batch scraping failed")
        else:
            # Analyze each website individually with crawling
            for url in urls:
                try:
                    analysis = await analyze_website_content_firecrawl(
                        website_url=url,
                        enable_crawling=enable_crawling,
                        max_crawl_pages=max_crawl_pages,
                        tenant_id=tenant_id
                    )
                    all_analyses.append(analysis)
                    successful_urls.append(url)
                    logger.info(f"Successfully analyzed website with Firecrawl: {url}")
                except Exception as e:
                    logger.warning(f"Failed to analyze website {url}: {str(e)}")
                    continue

        if not all_analyses:
            raise Exception("Failed to analyze any of the provided websites with Firecrawl")

        # Combine analysis results
        combined_analysis = combine_website_analyses(all_analyses, successful_urls)
        combined_analysis["extraction_method"] = "firecrawl_batch" if not enable_crawling else "firecrawl_crawl_batch"

        return combined_analysis

    except Exception as e:
        logger.error(f"Firecrawl batch analysis failed: {str(e)}")
        raise





async def analyze_website_content_ai(
    website_url: str,
    ai_provider: str = "gemini",
    enable_crawling: bool = False,
    max_crawl_pages: int = 5
) -> Dict[str, Any]:
    """
    Use AI models to extract and analyze website content intelligently.

    Args:
        website_url (str): URL to analyze
        ai_provider (str): AI provider to use (openai, gemini, anthropic)
        enable_crawling (bool): Whether to crawl multiple pages
        max_crawl_pages (int): Maximum pages to crawl

    Returns:
        Dict[str, Any]: AI-powered website analysis
    """
    try:
        # Step 1: Get raw content using best available method
        raw_content = ""
        extraction_method = "ai_extraction"

        try:
            # Try Firecrawl first for raw content (better quality)
            from ..services.firecrawl_consolidated_service import get_firecrawl_service

            service = await get_firecrawl_service()

            if enable_crawling and max_crawl_pages > 1:
                result = await service.monitor_crawl_for_tenant(
                    tenant_id="ai_extraction",
                    url=website_url,
                    max_pages=min(max_crawl_pages, 10),
                    include_subdomains=False,
                    context={"purpose": "ai_content_extraction"}
                )

                if result.success and result.data and isinstance(result.data, list):
                    combined_content = []
                    for i, page in enumerate(result.data):
                        content = page.content or page.markdown or ""
                        if content:
                            combined_content.append(f"=== Page {i+1}: {page.url} ===\n{content}")

                    raw_content = "\n\n".join(combined_content)
                    extraction_method = "ai_extraction_firecrawl_crawl"
                else:
                    raise Exception("Firecrawl crawling failed")
            else:
                result = await service.smart_scrape_for_tenant(
                    tenant_id="ai_extraction",
                    url=website_url,
                    extract_type="content",
                    context={"purpose": "ai_content_extraction"}
                )

                if result.success and result.data:
                    raw_content = result.data.content or result.data.markdown or ""
                    extraction_method = "ai_extraction_firecrawl"
                else:
                    raise Exception("Firecrawl scraping failed")

        except Exception as firecrawl_error:
            logger.warning(f"Firecrawl failed for AI extraction: {str(firecrawl_error)}, using basic scraping")

            # Fallback to basic scraping
            basic_analysis = await analyze_website_content(website_url)
            raw_content = basic_analysis["company_info"]["full_content"]
            extraction_method = "ai_extraction_basic"

        if not raw_content or len(raw_content.strip()) < 50:
            raise Exception("Insufficient content extracted for AI analysis")

        # Step 2: Use AI to intelligently extract structured information
        extracted_data = await _extract_content_with_ai(raw_content, website_url, ai_provider)

        # Step 3: Format the response in expected structure
        analysis = {
            "url": website_url,
            "title": extracted_data.get("title", ""),
            "company_info": {
                "name": extracted_data.get("company_name", "Unknown Company"),
                "description": extracted_data.get("description", ""),
                # Reason: Increased from 2000 to 10000 to preserve more context for AI prompt generation
                "full_content": raw_content[:10000] + "..." if len(raw_content) > 10000 else raw_content,
                "mission": extracted_data.get("mission", ""),
                "values": extracted_data.get("values", [])
            },
            "business_type": extracted_data.get("business_type", "general"),
            "services_products": extracted_data.get("services_products", []),
            "contact_info": extracted_data.get("contact_info", {}),
            "key_content": extracted_data.get("key_content", []),
            "tone_style": extracted_data.get("tone_style", "professional"),
            "target_audience": extracted_data.get("target_audience", "general"),
            "scraped_at": datetime.utcnow().isoformat(),
            "extraction_method": extraction_method,
            "ai_provider_used": ai_provider,
            "content_length": len(raw_content)
        }

        return analysis

    except Exception as e:
        logger.error(f"AI content extraction failed for {website_url}: {str(e)}")
        raise


async def _extract_content_with_ai(
    raw_content: str,
    website_url: str,
    ai_provider: str
) -> Dict[str, Any]:
    """
    Use AI models to extract structured information from raw website content.

    Args:
        raw_content (str): Raw website content
        website_url (str): Original URL for context
        ai_provider (str): AI provider to use

    Returns:
        Dict[str, Any]: Structured extracted data
    """
    # Create AI prompt for content extraction
    # Reason: Increased from 4000 to 15000 to analyze more comprehensive website content
    extraction_prompt = f"""
    You are an expert content analyst. Analyze the following website content and extract structured information.

    Website URL: {website_url}

    Content to analyze:
    {raw_content[:15000]}

    Extract and return the following information in JSON format:
    {{
        "company_name": "The main company/organization name",
        "title": "Page title or main heading",
        "description": "Company description or tagline (50-200 words)",
        "mission": "Company mission statement if available",
        "values": ["list", "of", "company", "values"],
        "business_type": "primary business category (healthcare, technology, education, finance, legal, consulting, retail, nonprofit, or general)",
        "services_products": ["list", "of", "main", "services", "or", "products"],
        "contact_info": {{
            "email": "contact email if found",
            "phone": "contact phone if found",
            "address": "physical address if found"
        }},
        "key_content": ["important", "headings", "or", "statements"],
        "tone_style": "communication tone (professional, friendly, supportive, or balanced)",
        "target_audience": "primary audience (business, consumer, or general)"
    }}

    Important:
    - Provide accurate, concise information
    - Use "general" for business_type if unclear
    - Extract actual content, don't make up information
    - Keep services_products list to max 10 items
    - Keep key_content to max 5 items
    - Ensure all fields have appropriate values (use empty string/array if not found)
    """

    # Try different AI providers with fallback: Gemini → Anthropic → OpenAI
    gemini_service = get_gemini_service()
    if ai_provider in ["gemini", "anthropic", "openai"] and gemini_service.is_available():
        try:
            # Reason: Increased from 1500 to 2500 to allow more detailed extraction results
            extracted_content = await gemini_service.extract_structured_data(
                prompt=extraction_prompt,
                max_output_tokens=2500,
                temperature=0.1
            )
            logger.info("AI content extraction completed using Gemini")
            return _parse_ai_extraction_response(extracted_content.strip())
        except Exception as e:
            logger.warning(f"Gemini extraction failed: {str(e)}, trying Anthropic")

    if ai_provider in ["anthropic", "openai", "gemini"] and os.getenv("ANTHROPIC_API_KEY"):
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.messages.create(
                    model="claude-sonnet-4",
                    max_tokens=1500,
                    messages=[
                        {"role": "user", "content": extraction_prompt}
                    ]
                )
            )
            logger.info("AI content extraction completed using Anthropic Claude")
            return _parse_ai_extraction_response(response.content[0].text.strip())
        except Exception as e:
            logger.warning(f"Anthropic extraction failed: {str(e)}, trying OpenAI")

    if ai_provider in ["openai", "gemini", "anthropic"] and os.getenv("OPENAI_API_KEY"):
        try:
            client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are an expert content analyst. Return only valid JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            logger.info("AI content extraction completed using OpenAI")
            return _parse_ai_extraction_response(response.choices[0].message.content.strip())
        except Exception as e:
            logger.warning(f"OpenAI extraction failed: {str(e)}, using rule-based fallback")

    # Final fallback to rule-based extraction
    logger.info("All AI providers failed, using rule-based extraction")
    return _fallback_rule_based_extraction(raw_content, website_url)


def _parse_ai_extraction_response(ai_response: str) -> Dict[str, Any]:
    """
    Parse AI response and ensure it has the expected structure.

    Args:
        ai_response (str): Raw AI response

    Returns:
        Dict[str, Any]: Parsed and validated data
    """
    try:
        # Try to extract JSON from the response
        import json
        import re

        # Look for JSON block in the response
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            parsed_data = json.loads(json_str)
        else:
            # Try parsing the whole response as JSON
            parsed_data = json.loads(ai_response)

        # Validate and fill missing fields
        default_structure = {
            "company_name": "",
            "title": "",
            "description": "",
            "mission": "",
            "values": [],
            "business_type": "general",
            "services_products": [],
            "contact_info": {},
            "key_content": [],
            "tone_style": "professional",
            "target_audience": "general"
        }

        # Merge with defaults
        for key, default_value in default_structure.items():
            if key not in parsed_data or parsed_data[key] is None:
                parsed_data[key] = default_value

        # Validate lists are actually lists
        for list_field in ["values", "services_products", "key_content"]:
            if not isinstance(parsed_data[list_field], list):
                parsed_data[list_field] = []

        # Validate contact_info is a dict
        if not isinstance(parsed_data["contact_info"], dict):
            parsed_data["contact_info"] = {}

        return parsed_data

    except Exception as e:
        logger.error(f"Failed to parse AI extraction response: {str(e)}")
        logger.debug(f"AI response was: {ai_response[:500]}")
        raise Exception(f"Failed to parse AI response: {str(e)}")


def _fallback_rule_based_extraction(raw_content: str, website_url: str) -> Dict[str, Any]:
    """
    Fallback rule-based extraction when AI fails.

    Args:
        raw_content (str): Raw website content
        website_url (str): Website URL

    Returns:
        Dict[str, Any]: Extracted data using rules
    """
    # Use existing rule-based functions
    lines = raw_content.split('\n')
    title = lines[0] if lines else ""

    return {
        "company_name": _extract_company_name_from_content(title, raw_content),
        "title": title[:100],
        "description": raw_content[:200] + "..." if len(raw_content) > 200 else raw_content,
        "mission": "",
        "values": [],
        "business_type": _analyze_business_type_from_content(raw_content),
        "services_products": _extract_services_from_content(raw_content),
        "contact_info": _extract_contact_from_content(raw_content),
        "key_content": _extract_key_content_from_text(raw_content),
        "tone_style": _analyze_tone_from_content(raw_content),
        "target_audience": _analyze_audience_from_content(raw_content)
    }


async def analyze_multiple_websites_ai(
    urls: List[str],
    ai_provider: str = "gemini",
    enable_crawling: bool = False,
    max_crawl_pages: int = 5
) -> Dict[str, Any]:
    """
    Analyze multiple websites using AI-powered extraction.

    Args:
        urls (List[str]): List of URLs to analyze
        ai_provider (str): AI provider to use
        enable_crawling (bool): Whether to crawl multiple pages
        max_crawl_pages (int): Maximum pages to crawl per website

    Returns:
        Dict[str, Any]: Combined AI analysis from all websites
    """
    if not urls:
        return {
            "urls": [],
            "title": "",
            "company_info": {"name": "", "description": "", "full_content": ""},
            "business_type": "general",
            "services_products": [],
            "contact_info": {},
            "key_content": [],
            "tone_style": "professional",
            "target_audience": "general",
            "scraped_at": datetime.utcnow().isoformat(),
            "extraction_method": "ai_batch"
        }

    try:
        all_analyses = []
        successful_urls = []

        # Analyze each website individually with AI
        for url in urls:
            try:
                analysis = await analyze_website_content_ai(
                    website_url=url,
                    ai_provider=ai_provider,
                    enable_crawling=enable_crawling,
                    max_crawl_pages=max_crawl_pages
                )
                all_analyses.append(analysis)
                successful_urls.append(url)
                logger.info(f"Successfully analyzed website with AI: {url}")
            except Exception as e:
                logger.warning(f"Failed to analyze website {url} with AI: {str(e)}")
                continue

        if not all_analyses:
            raise Exception("Failed to analyze any of the provided websites with AI")

        # Combine analysis results
        combined_analysis = combine_website_analyses(all_analyses, successful_urls)
        combined_analysis["extraction_method"] = "ai_batch" if not enable_crawling else "ai_crawl_batch"
        combined_analysis["ai_provider_used"] = ai_provider

        return combined_analysis

    except Exception as e:
        logger.error(f"AI batch analysis failed: {str(e)}")
        raise


async def _extract_websites_with_priority(
    urls: List[str],
    extraction_priority: str = "firecrawl_first",
    use_firecrawl: bool = True,
    use_ai_extraction: bool = False,
    ai_extraction_provider: str = "gemini",
    enable_crawling: bool = False,
    max_crawl_pages: int = 5
) -> Dict[str, Any]:
    """
    Extract website content using priority-based method selection.

    Args:
        urls (List[str]): URLs to analyze
        extraction_priority (str): Priority order for extraction methods
        use_firecrawl (bool): Whether to use Firecrawl
        use_ai_extraction (bool): Whether to use AI extraction
        ai_extraction_provider (str): AI provider to use
        enable_crawling (bool): Whether to enable crawling
        max_crawl_pages (int): Maximum pages to crawl

    Returns:
        Dict[str, Any]: Extracted website analysis
    """
    if not urls:
        raise Exception("No URLs provided for extraction")

    # Define extraction methods based on priority
    extraction_methods = []

    if extraction_priority == "ai_only":
        extraction_methods = ["ai"]
    elif extraction_priority == "firecrawl_only":
        extraction_methods = ["firecrawl"]
    elif extraction_priority == "ai_first":
        extraction_methods = ["ai", "firecrawl", "basic"]
    elif extraction_priority == "basic":
        extraction_methods = ["basic"]
    else:  # firecrawl_first - Priority order: Firecrawl → AI → Basic
        extraction_methods = ["firecrawl", "ai", "basic"]

    # Filter methods based on user settings
    if not use_ai_extraction and "ai" in extraction_methods:
        extraction_methods.remove("ai")
    if not use_firecrawl and "firecrawl" in extraction_methods:
        extraction_methods.remove("firecrawl")

    # Ensure we have at least basic extraction as fallback
    if "basic" not in extraction_methods:
        extraction_methods.append("basic")

    # Try each extraction method in order
    fallback_notifications = []

    for method in extraction_methods:
        try:
            logger.info(f"Trying extraction method: {method}")

            if method == "ai" and use_ai_extraction:
                if len(urls) == 1:
                    analysis = await analyze_website_content_ai(
                        website_url=urls[0],
                        ai_provider=ai_extraction_provider,
                        enable_crawling=enable_crawling,
                        max_crawl_pages=max_crawl_pages
                    )
                else:
                    analysis = await analyze_multiple_websites_ai(
                        urls=urls,
                        ai_provider=ai_extraction_provider,
                        enable_crawling=enable_crawling,
                        max_crawl_pages=max_crawl_pages
                    )

                logger.info(f"Successfully extracted content using AI ({ai_extraction_provider})")
                # Add fallback notifications if we had to switch methods
                if fallback_notifications:
                    analysis["fallback_notifications"] = fallback_notifications
                return analysis

            elif method == "firecrawl" and use_firecrawl:
                if len(urls) == 1:
                    analysis = await analyze_website_content_firecrawl(
                        website_url=urls[0],
                        enable_crawling=enable_crawling,
                        max_crawl_pages=max_crawl_pages
                    )
                else:
                    analysis = await analyze_multiple_websites_firecrawl(
                        urls=urls,
                        enable_crawling=enable_crawling,
                        max_crawl_pages=max_crawl_pages
                    )

                logger.info("Successfully extracted content using Firecrawl")
                # Add fallback notifications if we had to switch methods
                if fallback_notifications:
                    analysis["fallback_notifications"] = fallback_notifications
                return analysis

            elif method == "basic":
                # Use original basic extraction for single or multiple URLs
                if len(urls) == 1:
                    analysis = await analyze_website_content(urls[0])
                    analysis["urls"] = urls
                else:
                    analysis = await analyze_multiple_websites(urls)

                logger.info("Successfully extracted content using basic method")
                # Add fallback notifications if we had to switch methods
                if fallback_notifications:
                    analysis["fallback_notifications"] = fallback_notifications
                    # Add specific notification for basic method fallback
                    analysis["fallback_notifications"].append({
                        "type": "warning",
                        "message": "⚠️ Using basic HTML extraction as fallback - some content may be limited",
                        "details": "Advanced extraction methods failed, switched to basic HTTP scraping"
                    })
                return analysis

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Extraction method '{method}' failed: {error_msg}")

            # Add notification about failed method
            if method == "firecrawl":
                fallback_notifications.append({
                    "type": "error",
                    "message": "🚫 Firecrawl extraction failed - switching to fallback method",
                    "details": f"Firecrawl API error: {error_msg}",
                    "fallback_action": "Trying AI extraction or basic HTTP method"
                })
            elif method == "ai":
                fallback_notifications.append({
                    "type": "error",
                    "message": f"🚫 AI extraction ({ai_extraction_provider}) failed - switching to fallback method",
                    "details": f"AI extraction error: {error_msg}",
                    "fallback_action": "Trying Firecrawl or basic HTTP method"
                })

            continue

    # If all methods failed
    raise Exception(f"All extraction methods failed for URLs: {urls}")


def generate_agent_description(
    company_info: Dict[str, str],
    agent_template: Dict[str, Any],
    agent_type: str
) -> str:
    """
    Generate a suggested description for the agent.
    """
    company_name = company_info.get("name", "Company")
    role = agent_template["role"]
    
    descriptions = {
        "helpdesk": f"AI-powered customer support agent for {company_name}, providing 24/7 assistance and troubleshooting support.",
        "sales": f"Intelligent sales assistant for {company_name}, qualifying leads and scheduling appointments with potential customers.",
        "political": f"Campaign outreach assistant supporting voter engagement and information sharing for {company_name}.",
        "church": f"Ministry support agent for {company_name}, connecting members with services and providing spiritual guidance.",
        "survey": f"Research assistant conducting surveys and collecting valuable feedback data for {company_name}.",
        "appointment": f"Automated appointment scheduler for {company_name}, managing bookings and calendar coordination.",
        "lead_gen": f"Lead generation specialist for {company_name}, identifying and qualifying potential customers.",
        "education": f"Educational support assistant for {company_name}, helping students and managing educational services.",
        "healthcare": f"Healthcare support agent for {company_name}, managing appointments and providing patient assistance.",
        "custom": f"Specialized AI assistant for {company_name}, providing customized support based on specific business requirements."
    }
    
    return descriptions.get(agent_type, f"AI-powered {role} for {company_name}")


async def log_prompt_generation(
    website_url: str,
    agent_type: str,
    success: bool,
    error: Optional[str] = None
):
    """
    Log prompt generation attempts for analytics.
    """
    try:
        from backend.database.mongodb import get_collection
        
        logs_collection = get_collection("ai_prompt_logs")
        
        log_entry = {
            "website_url": website_url,
            "agent_type": agent_type,
            "success": success,
            "error": error,
            "timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        await logs_collection.insert_one(log_entry)
        
    except Exception as e:
        logger.error(f"Error logging prompt generation: {str(e)}")


async def analyze_multiple_websites(urls: List[str]) -> Dict[str, Any]:
    """
    Analyze multiple websites and combine their content for comprehensive analysis.
    """
    if not urls:
        # Return empty analysis if no URLs provided
        return {
            "urls": [],
            "title": "",
            "company_info": {"name": "", "description": "", "full_content": ""},
            "business_type": "general",
            "services_products": [],
            "contact_info": {},
            "key_content": [],
            "tone_style": "professional",
            "target_audience": "general",
            "scraped_at": datetime.utcnow().isoformat()
        }
    
    all_analyses = []
    successful_urls = []
    
    # Analyze each website
    for url in urls:
        try:
            analysis = await analyze_website_content(url)
            all_analyses.append(analysis)
            successful_urls.append(url)
            logger.info(f"Successfully analyzed website: {url}")
        except Exception as e:
            logger.warning(f"Failed to analyze website {url}: {str(e)}")
            continue
    
    if not all_analyses:
        raise HTTPException(
            status_code=400, 
            detail="Failed to analyze any of the provided websites"
        )
    
    # Combine analysis results
    combined_analysis = combine_website_analyses(all_analyses, successful_urls)
    return combined_analysis


def combine_website_analyses(analyses: List[Dict[str, Any]], urls: List[str]) -> Dict[str, Any]:
    """
    Combine multiple website analyses into a comprehensive analysis.
    """
    # Use the first analysis as the base
    combined = analyses[0].copy()
    combined["urls"] = urls
    
    # Combine company info
    combined_company_info = {
        "name": "",
        "description": "",
        "full_content": "",
        "mission": "",
        "values": []
    }
    
    # Find the best company name (prefer non-generic names)
    for analysis in analyses:
        company_name = analysis.get("company_info", {}).get("name", "")
        if company_name and not any(generic in company_name.lower() for generic in ["example", "test", "demo"]):
            if not combined_company_info["name"] or len(company_name) > len(combined_company_info["name"]):
                combined_company_info["name"] = company_name
    
    # Combine descriptions and content
    all_descriptions = []
    all_content = []
    
    for analysis in analyses:
        company_info = analysis.get("company_info", {})
        desc = company_info.get("description", "")
        content = company_info.get("full_content", "")
        
        if desc and desc not in all_descriptions:
            all_descriptions.append(desc)
        if content and content not in all_content:
            all_content.append(content)
    
    combined_company_info["description"] = " ".join(all_descriptions)
    combined_company_info["full_content"] = " ".join(all_content)
    
    # Combine services and products
    all_services = []
    for analysis in analyses:
        services = analysis.get("services_products", [])
        for service in services:
            if service not in all_services:
                all_services.append(service)
    
    # Combine key content
    all_key_content = []
    for analysis in analyses:
        key_content = analysis.get("key_content", [])
        for content in key_content:
            if content not in all_key_content:
                all_key_content.append(content)
    
    # Use the most comprehensive contact info
    best_contact_info = {}
    for analysis in analyses:
        contact_info = analysis.get("contact_info", {})
        if len(contact_info) > len(best_contact_info):
            best_contact_info = contact_info
    
    # Update combined analysis
    combined["company_info"] = combined_company_info
    combined["services_products"] = all_services[:15]  # Limit to top 15
    combined["key_content"] = all_key_content[:10]     # Limit to top 10
    combined["contact_info"] = best_contact_info
    
    return combined


def process_documents(documents: List[Dict[str, str]]) -> str:
    """
    Process uploaded documents and extract relevant content for prompt generation.
    """
    combined_content = []
    
    for doc in documents:
        doc_name = doc.get("name", "Unknown Document")
        doc_content = doc.get("content", "")
        
        if doc_content:
            # Add document header and content
            doc_section = f"\n=== {doc_name} ===\n{doc_content}\n"
            combined_content.append(doc_section)
    
    return "\n".join(combined_content)


async def generate_ai_system_prompt_enhanced(
    website_analysis: Dict[str, Any],
    documents_content: str,
    agent_template: Dict[str, Any],
    agent_type: str,
    language: str,
    company_name: Optional[str] = None,
    assistant_name: Optional[str] = None,
    additional_context: Optional[str] = None
) -> str:
    """
    Enhanced version of AI system prompt generation that handles multiple websites and documents.

    Args:
        assistant_name: Name of the assistant (e.g., "Sarah", "Premier Health Assistant")
    """
    # Prepare context for AI
    company_name = company_name or website_analysis["company_info"]["name"] or "the company"
    # Reason: Use provided assistant name or generate from company name
    assistant_name = assistant_name or f"{company_name} Assistant"
    business_type = website_analysis["business_type"]
    company_description = website_analysis["company_info"]["description"]
    services = ", ".join(website_analysis["services_products"][:8])  # More services from multiple sites
    tone_style = website_analysis["tone_style"]
    
    # Enhanced content from multiple sources
    enhanced_content = website_analysis["company_info"]["full_content"]
    if documents_content:
        enhanced_content += f"\n\nAdditional Company Documents:\n{documents_content}"
    
    # Create the enhanced AI prompt with comprehensive information
    ai_prompt = f"""
    You are an expert AI prompt engineer specializing in creating system prompts for voice AI agents.

    Create a comprehensive system prompt for a {agent_template['role']} working for {company_name}.

    IMPORTANT: The assistant should introduce itself as "{assistant_name}" in the system prompt.
    Start the prompt with: You are "{assistant_name}", a [description]...

    Company Context:
    - Company: {company_name}
    - Assistant Name: {assistant_name}
    - Business Type: {business_type}
    - Description: {company_description}
    - Services/Products: {services}
    - Communication Style: {tone_style}
    - Target Audience: {website_analysis["target_audience"]}

    Comprehensive Website Analysis:
    URLs Analyzed: {website_analysis.get("urls", [])}
    {enhanced_content[:2000]}

    Contact Information:
    {website_analysis["contact_info"]}

    Key Content Themes:
    {website_analysis["key_content"][:5] if website_analysis["key_content"] else "Not available"}

    Agent Requirements:
    - Role: {agent_template['role']}
    - Primary Goal: {agent_template['primary_goal']}
    - Key Behaviors: {', '.join(agent_template['key_behaviors'])}
    - Language: {language}

    Additional Context: {additional_context or 'None'}

    Create a detailed system prompt that:
    1. Starts with 'You are "{assistant_name}", a [description]...' using the exact assistant name provided
    2. Clearly defines the agent's role and identity
    3. Incorporates comprehensive company-specific information from multiple sources
    4. Sets appropriate behavioral guidelines based on company culture and tone
    5. Matches the company's communication style and brand voice
    6. Provides clear instructions for handling various scenarios
    7. Includes relevant company context, services, and unique value propositions
    8. Sets boundaries and escalation procedures
    9. Is optimized for voice conversations (not text chat)
    10. Reflects the depth of information gathered from multiple websites and documents

    The prompt should be professional, actionable, and between 400-800 words.
    Make it sound natural and conversational for voice interactions.
    """
    
    # Try OpenAI first, then fallbacks (same as original but with enhanced prompt)
    if os.getenv("OPENAI_API_KEY"):
        try:
            client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are an expert AI prompt engineer who creates exceptional voice AI system prompts."},
                    {"role": "user", "content": ai_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            logger.info("Generated enhanced system prompt using OpenAI")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI failed: {str(e)}, trying Gemini")
    
    # Try Gemini as fallback using service
    gemini_service = get_gemini_service()
    if gemini_service.is_available():
        try:
            # Reason: Increased from 1000 to 2500 to avoid truncation of system prompts
            generated_prompt = await gemini_service.generate_system_prompt(
                prompt=ai_prompt,
                max_output_tokens=2500,
                temperature=0.7
            )
            logger.info("Generated enhanced system prompt using Gemini")
            return generated_prompt
        except Exception as e:
            logger.warning(f"Gemini failed: {str(e)}, trying Anthropic")
    
    # Try Anthropic as final fallback
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.messages.create(
                    model="claude-sonnet-4",
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": ai_prompt}
                    ]
                )
            )
            logger.info("Generated enhanced system prompt using Anthropic Claude")
            return response.content[0].text.strip()
        except Exception as e:
            logger.warning(f"Anthropic failed: {str(e)}, using template fallback")
    
    # Final fallback to enhanced template-based generation
    logger.info("All AI providers failed, using enhanced template-based generation")
    return generate_enhanced_template_system_prompt(
        website_analysis, documents_content, agent_template, company_name, language
    )


def generate_enhanced_template_system_prompt(
    website_analysis: Dict[str, Any],
    documents_content: str,
    agent_template: Dict[str, Any],
    company_name: str,
    language: str
) -> str:
    """
    Generate an enhanced system prompt using templates with multiple sources.
    """
    company_name = company_name or website_analysis["company_info"]["name"] or "our company"
    description = website_analysis["company_info"]["description"]
    services = website_analysis["services_products"][:5]
    
    prompt = f"""You are a professional {agent_template['role']} representing {company_name}.

Company Information:
{company_name} is a {website_analysis['business_type']} company. {description[:300] + '...' if len(description) > 300 else description}

Services & Offerings:
{', '.join(services) if services else 'Various business services'}

Your Role:
As a {agent_template['role']}, your primary goal is to {agent_template['primary_goal']}.

Key Responsibilities:
{chr(10).join(f'- {behavior}' for behavior in agent_template['key_behaviors'])}

Communication Guidelines:
- Maintain a {website_analysis['tone_style']} and professional tone
- Speak clearly and at an appropriate pace for phone conversations
- Ask clarifying questions when needed
- Provide accurate information about {company_name}
- Be helpful, patient, and understanding

Company-Specific Knowledge:
{documents_content[:500] + '...' if len(documents_content) > 500 else documents_content if documents_content else 'Use general knowledge about the company based on website information.'}

Important Notes:
- You are speaking on the phone, not via text chat
- Keep responses concise but informative
- If you cannot help with something, politely explain and offer alternatives
- Always represent {company_name} professionally
- Draw from the comprehensive company information gathered from multiple sources

Remember: Your goal is to provide excellent service while representing {company_name} authentically based on all available company information."""

    return prompt


def create_analysis_from_extracted_content(extracted_content: str) -> Dict[str, Any]:
    """
    Create a basic analysis structure from pre-extracted content.
    This is used when users have reviewed and approved the extracted content.
    """
    # Extract basic information from the content
    company_name = "Unknown Company"
    description = ""
    business_type = "general"
    
    # Try to extract company name from content
    lines = extracted_content.split('\n')
    for line in lines:
        if line.startswith("Company:"):
            company_name = line.replace("Company:", "").strip()
            break
        elif line.startswith("Title:"):
            title = line.replace("Title:", "").strip()
            if title and not any(x in title.lower() for x in ["home", "welcome", "index"]):
                company_name = title
    
    # Try to extract description
    for line in lines:
        if line.startswith("Description:"):
            description = line.replace("Description:", "").strip()
            break
    
    # Try to extract business type
    for line in lines:
        if line.startswith("Business Type:"):
            business_type = line.replace("Business Type:", "").strip()
            break
    
    # Create a basic analysis structure
    return {
        "urls": ["extracted_content"],
        "title": company_name,
        "company_info": {
            "name": company_name,
            "description": description,
            "full_content": extracted_content[:2000] + "..." if len(extracted_content) > 2000 else extracted_content,
            "mission": "",
            "values": []
        },
        "business_type": business_type,
        "services_products": [],
        "contact_info": {},
        "key_content": [],
        "tone_style": "professional",
        "target_audience": "general",
        "scraped_at": datetime.utcnow().isoformat()
    }


class TranscriptSummarizeRequest(BaseModel):
    transcript: str = Field(..., description="Call transcript to summarize")
    call_id: Optional[str] = Field(None, description="Unique call identifier")
    summary_type: str = Field("detailed", description="Type of summary: brief, detailed, or action_items")

class TranscriptSummarizeResponse(BaseModel):
    success: bool
    summary: str
    call_id: Optional[str]
    summary_type: str
    ai_provider_used: str


async def generate_ai_transcript_summary(
    transcript: str,
    summary_type: str = "detailed",
    call_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate AI-powered transcript summary using OpenAI, Gemini, or Anthropic as fallbacks.
    """

    # Create summary prompt based on type
    if summary_type == "brief":
        ai_prompt = f"""
        Provide a brief 2-3 sentence summary of this call transcript:

        Transcript:
        {transcript}

        Focus on the main purpose of the call and key outcomes.
        """
    elif summary_type == "action_items":
        ai_prompt = f"""
        Extract action items and next steps from this call transcript:

        Transcript:
        {transcript}

        List specific tasks, deadlines, and who is responsible for each action.
        If no clear action items exist, state "No specific action items identified."
        """
    else:  # detailed
        ai_prompt = f"""
        Provide a comprehensive summary of this call transcript including:
        1. Purpose of the call
        2. Key topics discussed
        3. Important decisions made
        4. Next steps or action items
        5. Overall outcome

        Transcript:
        {transcript}

        Be thorough but concise, focusing on business-relevant information.
        """

    ai_provider_used = "template_fallback"

    # Try OpenAI first
    if os.getenv("OPENAI_API_KEY"):
        try:
            client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at summarizing business call transcripts."},
                    {"role": "user", "content": ai_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            ai_provider_used = "openai"
            logger.info("Generated transcript summary using OpenAI")
            return {
                "summary": response.choices[0].message.content.strip(),
                "ai_provider_used": ai_provider_used
            }
        except Exception as e:
            logger.warning(f"OpenAI failed: {str(e)}, trying Gemini")

    # Try Gemini as fallback using service
    gemini_service = get_gemini_service()
    if gemini_service.is_available():
        try:
            extracted_summary = await gemini_service.generate_summary(
                content=ai_prompt,
                max_output_tokens=500,
                temperature=0.3
            )
            ai_provider_used = "gemini"
            logger.info("Generated transcript summary using Gemini")
            return {
                "summary": extracted_summary.strip(),
                "ai_provider_used": ai_provider_used
            }
        except Exception as e:
            logger.warning(f"Gemini failed: {str(e)}, trying Anthropic")

    # Try Anthropic as final fallback
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.messages.create(
                    model="claude-sonnet-4",
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": ai_prompt}
                    ]
                )
            )
            ai_provider_used = "anthropic"
            logger.info("Generated transcript summary using Anthropic Claude")
            return {
                "summary": response.content[0].text.strip(),
                "ai_provider_used": ai_provider_used
            }
        except Exception as e:
            logger.warning(f"Anthropic failed: {str(e)}, using template fallback")

    # Final fallback to simple template-based summary
    logger.info("All AI providers failed, using template-based summary")
    if summary_type == "brief":
        summary = f"Call summary for {call_id or 'unknown call'}: {transcript[:100]}..."
    elif summary_type == "action_items":
        summary = "Unable to extract action items automatically. Please review transcript manually."
    else:
        summary = f"Call transcript summary:\n\nTranscript length: {len(transcript)} characters\nCall ID: {call_id or 'Not provided'}\n\nFirst 200 characters: {transcript[:200]}..."

    return {
        "summary": summary,
        "ai_provider_used": ai_provider_used
    }


@router.post("/summarize-transcript", response_model=TranscriptSummarizeResponse)
async def summarize_transcript(request: TranscriptSummarizeRequest):
    """
    Generate AI-powered summary of call transcript.

    This endpoint uses multiple AI providers (OpenAI, Gemini, Anthropic) as fallbacks
    to ensure reliable transcript summarization.
    """
    try:
        if not request.transcript or len(request.transcript.strip()) < 10:
            raise HTTPException(status_code=400, detail="Transcript is too short or empty")

        # Generate AI summary
        result = await generate_ai_transcript_summary(
            transcript=request.transcript,
            summary_type=request.summary_type,
            call_id=request.call_id
        )

        return TranscriptSummarizeResponse(
            success=True,
            summary=result["summary"],
            call_id=request.call_id,
            summary_type=request.summary_type,
            ai_provider_used=result["ai_provider_used"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to summarize transcript: {str(e)}")


async def generate_vapi_optimized_prompt(
    website_analysis: Dict[str, Any],
    language: str,
    additional_context: Optional[str] = None
) -> str:
    """
    Generate a VAPI-optimized system prompt that integrates MASTER_TEMPLATE.md
    with company-specific information using multi-LLM fallback.
    """
    company_name = website_analysis["company_info"]["name"] or "the company"
    business_type = website_analysis["business_type"]
    company_description = website_analysis["company_info"]["description"]
    services = ", ".join(website_analysis["services_products"][:8])
    tone_style = website_analysis["tone_style"]
    target_audience = website_analysis["target_audience"]

    # Enhanced content for context
    enhanced_content = website_analysis["company_info"]["full_content"]

    # Create the AI prompt that integrates MASTER_TEMPLATE.md
    ai_prompt = f"""
    You are an expert AI prompt engineer specializing in creating VAPI (Voice AI Platform) system prompts.

    Create a comprehensive VAPI voice agent system prompt for {company_name}.

    COMPANY CONTEXT:
    - Company: {company_name}
    - Business Type: {business_type}
    - Description: {company_description}
    - Services/Products: {services}
    - Communication Style: {tone_style}
    - Target Audience: {target_audience}

    DETAILED COMPANY INFORMATION:
    {enhanced_content[:2000]}

    ADDITIONAL REQUIREMENTS: {additional_context or 'None'}

    INTEGRATION REQUIREMENTS:
    You must integrate and customize the following MASTER VAPI TEMPLATE for this specific company:

    {MASTER_TEMPLATE[:3000]}

    CUSTOMIZATION INSTRUCTIONS:
    1. Replace [AGENT_NAME] with an appropriate name for {company_name}'s voice agent
    2. Replace [ORGANIZATION_NAME] with {company_name}
    3. Customize the agent's role based on {business_type}
    4. Adapt the communication style to match {tone_style}
    5. Include company-specific services and information
    6. Maintain all VAPI webhook configurations and tool access instructions
    7. Keep the no-hallucination policy and error handling procedures
    8. Ensure the prompt is optimized for voice interactions
    9. Include relevant company contact information and escalation procedures
    10. Adapt conversation examples to the company's context

    The final prompt should be:
    - Professional and company-specific
    - Voice conversation optimized
    - Include all VAPI tools and webhook configuration
    - Maintain security and data handling policies
    - Be between 800-1500 words for comprehensive coverage
    - Ready for immediate VAPI deployment

    Return only the complete, customized system prompt without any explanatory text.
    """

    # Enhanced API fallback system with better error handling
    api_errors = []

    # Try OpenAI first with updated model
    if os.getenv("OPENAI_API_KEY"):
        try:
            client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await client.chat.completions.create(
                model="gpt-5-mini",  # Updated to 2025 model
                messages=[
                    {"role": "system", "content": "You are an expert VAPI system prompt engineer who creates exceptional voice AI prompts that integrate comprehensive templates with company-specific information."},
                    {"role": "user", "content": ai_prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            logger.info("✅ Generated VAPI-optimized system prompt using OpenAI GPT-5-mini")
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = f"OpenAI API failed: {str(e)}"
            api_errors.append(error_msg)
            logger.warning(f"⚠️ {error_msg}, trying Gemini as fallback")

    # Try Gemini as fallback using service
    gemini_service = get_gemini_service()
    if gemini_service.is_available():
        try:
            logger.info("✅ Using Gemini to generate VAPI-optimized system prompt")
            extracted_prompt = await gemini_service.generate_system_prompt(
                prompt=ai_prompt,
                max_output_tokens=2000,
                temperature=0.7
            )
            logger.info(f"✅ Generated VAPI-optimized system prompt using Gemini, length: {len(extracted_prompt)}")
            return extracted_prompt.strip()
        except Exception as e:
            error_msg = f"Gemini API failed: {str(e)}"
            api_errors.append(error_msg)
            logger.warning(f"⚠️ {error_msg}, trying Anthropic as final fallback")

    # Try Anthropic as final AI fallback with better error handling
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.messages.create(
                    model="claude-sonnet-4",  # Updated to 2025 model
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": ai_prompt}
                    ]
                )
            )
            logger.info("✅ Generated VAPI-optimized system prompt using Anthropic Claude Sonnet 4")
            return response.content[0].text.strip()
        except Exception as e:
            error_msg = f"Anthropic API failed: {str(e)}"
            api_errors.append(error_msg)
            if "credit balance is too low" in str(e).lower():
                logger.error(f"💳 Anthropic API credit balance insufficient: {str(e)}")
                api_errors.append("Anthropic API credit balance too low - please add credits to continue using Claude models")
            else:
                logger.warning(f"⚠️ {error_msg}")

    # Log all API failures for debugging
    if api_errors:
        logger.error("🚨 All AI API providers failed:")
        for i, error in enumerate(api_errors, 1):
            logger.error(f"  {i}. {error}")
        logger.info("🛠️ Using template-based fallback for VAPI prompt generation")

    # Final fallback to template-based generation
    logger.info("📝 Generating VAPI system prompt using template-based approach")
    return generate_vapi_template_fallback(website_analysis, additional_context)


def generate_vapi_template_fallback(
    website_analysis: Dict[str, Any],
    additional_context: Optional[str] = None
) -> str:
    """
    Generate a VAPI system prompt using template-based approach when AI providers fail.
    This integrates MASTER_TEMPLATE.md with company information.
    """
    company_name = website_analysis["company_info"]["name"] or "Your Company"
    business_type = website_analysis["business_type"]
    company_description = website_analysis["company_info"]["description"]
    services = website_analysis["services_products"][:5]

    # Create agent name based on company
    agent_name = f"{company_name} Assistant"

    # Start with base template and customize
    if MASTER_TEMPLATE:
        # Replace placeholders in MASTER_TEMPLATE
        customized_prompt = MASTER_TEMPLATE.replace(
            "[AGENT_NAME]", agent_name
        ).replace(
            "[ORGANIZATION_NAME]", company_name
        )

        # Add company-specific information
        company_section = f"""

COMPANY-SPECIFIC INFORMATION:
- Company: {company_name}
- Business Type: {business_type}
- Description: {company_description}
- Key Services: {', '.join(services)}

CUSTOMIZATION FOR {company_name.upper()}:
- Focus conversations on {business_type} services
- Emphasize company strengths: {company_description}
- Promote key services: {', '.join(services)}
"""

        if additional_context:
            company_section += f"\nAdditional Context: {additional_context}"

        # Insert company information after the base system prompt
        sections = customized_prompt.split("---")
        if len(sections) > 2:
            sections.insert(2, company_section + "\n---")
            customized_prompt = "\n".join(sections)
        else:
            customized_prompt += company_section

        return customized_prompt
    else:
        # Fallback if MASTER_TEMPLATE is not available
        return f"""
You are {agent_name}, a professional AI voice assistant for {company_name}.

COMPANY INFORMATION:
- Company: {company_name}
- Business Type: {business_type}
- Description: {company_description}
- Services: {', '.join(services)}

CORE PRINCIPLES:
- Be helpful, accurate, and professional at all times
- Only collect first name + use caller phone number automatically
- Never ask for email addresses or last names
- Provide clear, concise responses
- Escalate complex issues to human support when appropriate
- Always prioritize customer safety and satisfaction

CONVERSATION STYLE:
- Warm, friendly, and professional tone
- Clear and easy to understand language
- Keep responses concise but informative
- Ask one question at a time
- Confirm understanding before proceeding

For technical configuration, please integrate with VAPI webhook endpoints and tool access as per standard VAPI guidelines.
"""


def generate_vapi_agent_description(
    company_info: Dict[str, Any],
    business_type: str
) -> str:
    """
    Generate a suggested description for the VAPI agent based on company information.
    """
    company_name = company_info.get("name", "the company")
    description = company_info.get("description", "")

    base_description = f"AI voice assistant for {company_name}"

    if business_type and business_type != "unknown":
        base_description += f" specializing in {business_type}"

    if description:
        base_description += f". {description[:100]}..."

    base_description += " Provides professional customer support with VAPI optimization."

    return base_description


# Include the router in the main app
def get_router():
    return router