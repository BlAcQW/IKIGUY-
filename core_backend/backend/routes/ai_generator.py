"""
AI Generator Routes

This module provides AI-powered content generation services,
including system prompt generation from website analysis.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, Any, Optional, List
import httpx
import asyncio
import logging
from datetime import datetime
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Generator"])


class SystemPromptRequest(BaseModel):
    website_url: HttpUrl = Field(..., description="Website URL to analyze")
    agent_type: str = Field(..., description="Type of agent (helpdesk, sales, etc.)")
    language: str = Field("en", description="Language for the system prompt")
    company_name: Optional[str] = Field(None, description="Company name override")
    additional_context: Optional[str] = Field(None, description="Additional context to include")


class SystemPromptResponse(BaseModel):
    system_prompt: str = Field(..., description="Generated system prompt")
    suggested_description: Optional[str] = Field(None, description="Suggested agent description")
    company_info: Dict[str, Any] = Field({}, description="Extracted company information")
    confidence_score: float = Field(0.0, description="Confidence in extraction (0-1)")


# Agent type templates
AGENT_TEMPLATES = {
    "helpdesk": {
        "role": "customer support specialist",
        "traits": ["helpful", "patient", "solution-focused", "professional"],
        "goals": ["resolve customer issues", "provide accurate information", "ensure customer satisfaction"],
        "style": "friendly and professional"
    },
    "sales": {
        "role": "sales representative",
        "traits": ["persuasive", "knowledgeable", "consultative", "goal-oriented"],
        "goals": ["qualify leads", "understand customer needs", "present solutions", "close deals"],
        "style": "engaging and consultative"
    },
    "political": {
        "role": "campaign assistant",
        "traits": ["informative", "respectful", "non-partisan", "encouraging"],
        "goals": ["inform about candidates", "encourage voter participation", "answer policy questions"],
        "style": "respectful and informative"
    },
    "church": {
        "role": "church assistant",
        "traits": ["caring", "supportive", "spiritual", "welcoming"],
        "goals": ["provide spiritual support", "connect members", "share information about events"],
        "style": "warm and caring"
    },
    "survey": {
        "role": "research assistant",
        "traits": ["neutral", "thorough", "systematic", "professional"],
        "goals": ["collect accurate data", "ensure participation", "maintain objectivity"],
        "style": "neutral and systematic"
    },
    "appointment": {
        "role": "scheduling coordinator",
        "traits": ["organized", "efficient", "accommodating", "detail-oriented"],
        "goals": ["schedule appointments", "manage calendars", "confirm bookings", "handle changes"],
        "style": "efficient and accommodating"
    },
    "lead_gen": {
        "role": "lead generation specialist",
        "traits": ["curious", "persistent", "analytical", "strategic"],
        "goals": ["identify prospects", "qualify leads", "gather contact information", "schedule follow-ups"],
        "style": "professional and strategic"
    },
    "education": {
        "role": "educational assistant",
        "traits": ["knowledgeable", "patient", "encouraging", "adaptive"],
        "goals": ["support learning", "answer questions", "provide guidance", "track progress"],
        "style": "supportive and encouraging"
    },
    "healthcare": {
        "role": "healthcare assistant",
        "traits": ["empathetic", "professional", "accurate", "confidential"],
        "goals": ["provide health information", "schedule appointments", "answer questions", "maintain privacy"],
        "style": "professional and empathetic"
    },
    "custom": {
        "role": "AI assistant",
        "traits": ["helpful", "professional", "adaptive", "knowledgeable"],
        "goals": ["assist users", "provide information", "solve problems"],
        "style": "professional and helpful"
    }
}


@router.post("/generate-system-prompt", response_model=SystemPromptResponse)
async def generate_system_prompt(request: SystemPromptRequest, background_tasks: BackgroundTasks):
    """
    Generate a customized system prompt by analyzing a website and agent type.
    
    This endpoint:
    1. Scrapes and analyzes the provided website
    2. Extracts company information and services
    3. Generates a tailored system prompt based on agent type
    4. Returns the prompt with confidence metrics
    """
    try:
        # Extract company information from website
        company_info = await analyze_website(str(request.website_url))
        
        # Get agent template
        agent_template = AGENT_TEMPLATES.get(request.agent_type, AGENT_TEMPLATES["custom"])
        
        # Generate system prompt
        system_prompt = await create_system_prompt(
            company_info=company_info,
            agent_template=agent_template,
            agent_type=request.agent_type,
            language=request.language,
            company_name_override=request.company_name,
            additional_context=request.additional_context
        )
        
        # Generate suggested description
        suggested_description = await generate_agent_description(
            company_info=company_info,
            agent_type=request.agent_type,
            language=request.language
        )
        
        # Calculate confidence score
        confidence_score = calculate_confidence_score(company_info)
        
        return SystemPromptResponse(
            system_prompt=system_prompt,
            suggested_description=suggested_description,
            company_info=company_info,
            confidence_score=confidence_score
        )
        
    except Exception as e:
        logger.error(f"Error generating system prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate system prompt: {str(e)}")


async def analyze_website(url: str) -> Dict[str, Any]:
    """
    Analyze a website to extract company information, services, and context.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch website content
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract company information
            company_info = {
                "url": url,
                "title": extract_title(soup),
                "description": extract_description(soup),
                "company_name": extract_company_name(soup, url),
                "services": extract_services(soup),
                "contact_info": extract_contact_info(soup),
                "about_text": extract_about_text(soup),
                "industry": detect_industry(soup),
                "tone": detect_tone(soup),
                "key_features": extract_key_features(soup),
                "target_audience": detect_target_audience(soup),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            return company_info
            
    except httpx.TimeoutException:
        logger.warning(f"Timeout analyzing website: {url}")
        return {"url": url, "error": "timeout", "extracted_at": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Error analyzing website {url}: {str(e)}")
        return {"url": url, "error": str(e), "extracted_at": datetime.utcnow().isoformat()}


def extract_title(soup: BeautifulSoup) -> str:
    """Extract page title."""
    title_tag = soup.find('title')
    return title_tag.get_text().strip() if title_tag else ""


def extract_description(soup: BeautifulSoup) -> str:
    """Extract page description from meta tags."""
    description_tag = soup.find('meta', attrs={'name': 'description'})
    if description_tag and description_tag.get('content'):
        return description_tag.get('content').strip()
    return ""


def extract_company_name(soup: BeautifulSoup, url: str) -> str:
    """Extract company name from various sources."""
    # Try logo alt text
    logo = soup.find('img', attrs={'alt': re.compile(r'logo', re.I)})
    if logo and logo.get('alt'):
        return logo.get('alt').strip()
    
    # Try h1 tag
    h1 = soup.find('h1')
    if h1:
        text = h1.get_text().strip()
        if len(text) < 50:  # Reasonable company name length
            return text
    
    # Try title extraction
    title = extract_title(soup)
    if title:
        # Remove common suffixes
        for suffix in [' - Home', ' | Home', ' - Official Website', ' | Official Site']:
            if title.endswith(suffix):
                return title[:-len(suffix)].strip()
    
    # Fallback to domain name
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netlify
        return domain.replace('www.', '').replace('.com', '').replace('.org', '').title()
    except:
        return "Company"


def extract_services(soup: BeautifulSoup) -> List[str]:
    """Extract services or products offered."""
    services = []
    
    # Look for service sections
    service_sections = soup.find_all(['div', 'section'], class_=re.compile(r'service|product|offering', re.I))
    for section in service_sections:
        items = section.find_all(['h2', 'h3', 'h4', 'li'])
        for item in items:
            text = item.get_text().strip()
            if 10 <= len(text) <= 100:  # Reasonable service description length
                services.append(text)
    
    return services[:10]  # Limit to top 10


def extract_contact_info(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract contact information."""
    contact_info = {}
    
    # Find contact section
    contact_section = soup.find(['div', 'section'], class_=re.compile(r'contact', re.I))
    if contact_section:
        # Extract phone numbers
        phone_pattern = re.compile(r'[\+]?[1-9]?[0-9]{7,14}')
        phone_matches = phone_pattern.findall(contact_section.get_text())
        if phone_matches:
            contact_info['phone'] = phone_matches[0]
        
        # Extract email addresses
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        email_matches = email_pattern.findall(contact_section.get_text())
        if email_matches:
            contact_info['email'] = email_matches[0]
    
    return contact_info


def extract_about_text(soup: BeautifulSoup) -> str:
    """Extract about text or company description."""
    # Look for about sections
    about_section = soup.find(['div', 'section'], class_=re.compile(r'about|company|who-we-are', re.I))
    if about_section:
        paragraphs = about_section.find_all('p')
        if paragraphs:
            return ' '.join([p.get_text().strip() for p in paragraphs])
    
    return ""


def detect_industry(soup: BeautifulSoup) -> str:
    """Detect industry based on content analysis."""
    content = soup.get_text().lower()
    
    industry_keywords = {
        "healthcare": ["health", "medical", "doctor", "clinic", "hospital", "patient"],
        "financial": ["finance", "bank", "investment", "loan", "credit", "money"],
        "retail": ["shop", "store", "buy", "product", "sale", "retail"],
        "technology": ["software", "app", "tech", "digital", "platform", "solution"],
        "education": ["school", "education", "student", "learning", "course", "training"],
        "real_estate": ["property", "real estate", "home", "house", "rent", "buy"],
        "automotive": ["car", "auto", "vehicle", "repair", "service", "dealership"],
        "hospitality": ["hotel", "restaurant", "travel", "booking", "hospitality"],
        "legal": ["law", "legal", "attorney", "lawyer", "court", "case"],
        "consulting": ["consulting", "advisor", "strategy", "business", "professional"]
    }
    
    for industry, keywords in industry_keywords.items():
        if sum(content.count(keyword) for keyword in keywords) >= 3:
            return industry
    
    return "general"


def detect_tone(soup: BeautifulSoup) -> str:
    """Detect the tone/style of the website."""
    content = soup.get_text().lower()
    
    if any(word in content for word in ["luxury", "premium", "exclusive", "elite"]):
        return "luxury"
    elif any(word in content for word in ["friendly", "family", "community", "personal"]):
        return "friendly"
    elif any(word in content for word in ["professional", "expert", "corporate", "business"]):
        return "professional"
    elif any(word in content for word in ["innovative", "cutting-edge", "advanced", "modern"]):
        return "innovative"
    else:
        return "professional"


def extract_key_features(soup: BeautifulSoup) -> List[str]:
    """Extract key features or benefits."""
    features = []
    
    # Look for feature sections
    feature_sections = soup.find_all(['div', 'section'], class_=re.compile(r'feature|benefit|why', re.I))
    for section in feature_sections:
        items = section.find_all(['li', 'h3', 'h4'])
        for item in items:
            text = item.get_text().strip()
            if 5 <= len(text) <= 80:
                features.append(text)
    
    return features[:8]  # Limit to top 8


def detect_target_audience(soup: BeautifulSoup) -> str:
    """Detect target audience based on content."""
    content = soup.get_text().lower()
    
    if any(word in content for word in ["business", "enterprise", "company", "corporate"]):
        return "business"
    elif any(word in content for word in ["individual", "personal", "family", "home"]):
        return "personal"
    elif any(word in content for word in ["student", "education", "learning"]):
        return "students"
    else:
        return "general"


async def create_system_prompt(
    company_info: Dict[str, Any],
    agent_template: Dict[str, Any],
    agent_type: str,
    language: str = "en",
    company_name_override: Optional[str] = None,
    additional_context: Optional[str] = None
) -> str:
    """
    Create a customized system prompt based on company information and agent type.
    """
    company_name = company_name_override or company_info.get("company_name", "the company")
    services = company_info.get("services", [])
    about_text = company_info.get("about_text", "")
    industry = company_info.get("industry", "general")
    tone = company_info.get("tone", "professional")
    
    # Build the system prompt
    prompt_parts = [
        f"You are a {tone} {agent_template['role']} for {company_name}."
    ]
    
    # Add company context
    if about_text:
        prompt_parts.append(f"About {company_name}: {about_text[:300]}")
    
    # Add services context
    if services:
        services_text = ", ".join(services[:5])
        prompt_parts.append(f"The company offers: {services_text}.")
    
    # Add role-specific traits
    traits_text = ", ".join(agent_template["traits"])
    prompt_parts.append(f"Your personality traits are: {traits_text}.")
    
    # Add goals
    goals_text = ", ".join(agent_template["goals"])
    prompt_parts.append(f"Your primary goals are to: {goals_text}.")
    
    # Add communication style
    prompt_parts.append(f"Always communicate in a {agent_template['style']} manner.")
    
    # Add agent-specific instructions
    agent_instructions = {
        "helpdesk": "When customers have issues, listen carefully, ask clarifying questions, and provide step-by-step solutions. If you cannot resolve an issue, escalate to a human agent.",
        "sales": "Focus on understanding the customer's needs first, then present relevant solutions. Ask qualifying questions and guide them toward making a decision. Be consultative, not pushy.",
        "political": "Stay neutral and factual about political topics. Focus on providing information about voting, candidates, and policies without showing bias.",
        "church": "Be supportive and caring in all interactions. Respect diverse spiritual journeys and provide information about church events, services, and community programs.",
        "survey": "Ask questions in a clear, neutral way. Ensure you collect accurate responses and maintain the participant's privacy. Be systematic and thorough.",
        "appointment": "Be efficient in scheduling. Confirm all details including date, time, location, and any special requirements. Always double-check availability.",
        "lead_gen": "Focus on qualifying prospects by understanding their needs, budget, and timeline. Gather contact information and determine the best next steps.",
        "education": "Be patient and encouraging with learners. Break down complex topics into understandable parts and provide additional resources when needed.",
        "healthcare": "Always maintain professional boundaries and patient confidentiality. Provide general health information but never diagnose or give medical advice."
    }
    
    if agent_type in agent_instructions:
        prompt_parts.append(agent_instructions[agent_type])
    
    # Add additional context if provided
    if additional_context:
        prompt_parts.append(additional_context)
    
    # Add general guidelines
    prompt_parts.extend([
        "Always be helpful and professional.",
        "If you don't know something, say so honestly.",
        "Keep responses conversational and natural.",
        "Use the customer's name when provided.",
        f"Respond in {language} unless otherwise requested."
    ])
    
    return " ".join(prompt_parts)


async def generate_agent_description(
    company_info: Dict[str, Any],
    agent_type: str,
    language: str = "en"
) -> str:
    """
    Generate a suggested description for the agent.
    """
    company_name = company_info.get("company_name", "Company")
    agent_template = AGENT_TEMPLATES.get(agent_type, AGENT_TEMPLATES["custom"])
    
    descriptions = {
        "helpdesk": f"Customer support assistant for {company_name}, ready to help resolve issues and answer questions.",
        "sales": f"Sales representative for {company_name}, helping customers find the right solutions for their needs.",
        "political": f"Campaign assistant providing information about candidates, policies, and voting processes.",
        "church": f"Church assistant for {company_name}, connecting members and providing information about services and events.",
        "survey": f"Research assistant conducting surveys and collecting data for {company_name}.",
        "appointment": f"Scheduling coordinator for {company_name}, helping book and manage appointments.",
        "lead_gen": f"Lead generation specialist for {company_name}, identifying and qualifying potential customers.",
        "education": f"Educational assistant for {company_name}, supporting students and answering academic questions.",
        "healthcare": f"Healthcare assistant for {company_name}, helping with appointments and general health information."
    }
    
    return descriptions.get(agent_type, f"{agent_template['role'].title()} for {company_name}")


def calculate_confidence_score(company_info: Dict[str, Any]) -> float:
    """
    Calculate confidence score based on extracted information quality.
    """
    score = 0.0
    
    # Base score for successful extraction
    if not company_info.get("error"):
        score += 0.2
    
    # Company name found
    if company_info.get("company_name") and len(company_info["company_name"]) > 3:
        score += 0.2
    
    # Description found
    if company_info.get("description"):
        score += 0.15
    
    # Services found
    if company_info.get("services") and len(company_info["services"]) > 0:
        score += 0.15
    
    # About text found
    if company_info.get("about_text") and len(company_info["about_text"]) > 50:
        score += 0.15
    
    # Contact info found
    if company_info.get("contact_info") and len(company_info["contact_info"]) > 0:
        score += 0.1
    
    # Industry detected
    if company_info.get("industry") and company_info["industry"] != "general":
        score += 0.05
    
    return min(1.0, score)


# Include the router in the main app
def get_router():
    return router