"""
DEPRECATED: Site extraction service for automated company information extraction.

⚠️  WARNING: This service is deprecated as of 2025-09-16
⚠️  Use the AI-powered extraction in routes/ai_prompt_generator.py instead
⚠️  This file is kept for reference and potential rollback only

New extraction endpoints:
- /ai/extract-content (multi-source AI extraction)
- /enhanced-helpdesk/extract-site-info (single URL with AI)
- /enhanced-helpdesk/extract-multi-site-info (multi-URL with AI)

The new AI-powered system provides:
✅ Business type detection
✅ Tone & audience analysis
✅ Multi-source content combination
✅ Document processing (PDF, Word, TXT)
✅ AI-generated insights
✅ Enhanced accuracy and depth
"""

import re
import json
import aiohttp
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import asyncio
from pydantic import BaseModel, HttpUrl

class ExtractedContactInfo(BaseModel):
    """Extracted contact information."""
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class ExtractedCompanyInfo(BaseModel):
    """Extracted company information."""
    company_name: Optional[str] = None
    services: List[str] = []
    business_hours: Optional[str] = None
    contact_info: ExtractedContactInfo = ExtractedContactInfo()
    about_text: Optional[str] = None
    meta_description: Optional[str] = None

class SiteExtractionService:
    """Service for extracting company information from websites."""

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def extract_company_info(self, url: str) -> ExtractedCompanyInfo:
        """
        Extract company information from a website URL.

        Args:
            url: The website URL to extract information from

        Returns:
            ExtractedCompanyInfo: Extracted company information
        """
        try:
            # Ensure URL has proper scheme
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'

            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=self._get_headers()) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: Failed to fetch URL")

                    html_content = await response.text()

            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract information
            extracted_info = ExtractedCompanyInfo()

            # Extract company name
            extracted_info.company_name = self._extract_company_name(soup, url)

            # Extract services
            extracted_info.services = self._extract_services(soup)

            # Extract business hours
            extracted_info.business_hours = self._extract_business_hours(soup)

            # Extract contact information
            extracted_info.contact_info = self._extract_contact_info(soup)

            # Extract about text
            extracted_info.about_text = self._extract_about_text(soup)

            # Extract meta description
            extracted_info.meta_description = self._extract_meta_description(soup)

            return extracted_info

        except Exception as e:
            # Return basic info with error handling
            return ExtractedCompanyInfo(
                company_name=self._extract_domain_name(url),
                about_text=f"Unable to extract detailed information: {str(e)}"
            )

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _extract_company_name(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract company name from HTML."""
        # Try title tag first
        title = soup.find('title')
        if title and title.text:
            title_text = title.text.strip()
            # Remove common suffixes
            for suffix in [' - Home', ' | Home', ' - Official Website', ' | Official Site']:
                if title_text.endswith(suffix):
                    title_text = title_text[:-len(suffix)]
            if title_text:
                return title_text

        # Try h1 tags
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            if h1.text.strip():
                return h1.text.strip()

        # Try meta property og:site_name
        og_site_name = soup.find('meta', property='og:site_name')
        if og_site_name and og_site_name.get('content'):
            return og_site_name['content']

        # Fallback to domain name
        return self._extract_domain_name(url)

    def _extract_domain_name(self, url: str) -> str:
        """Extract domain name from URL."""
        try:
            domain = urlparse(url).netloc
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            # Remove .com, .org, etc. for company name
            parts = domain.split('.')
            if len(parts) > 1:
                return parts[0].capitalize()
            return domain.capitalize()
        except:
            return "Company"

    def _extract_services(self, soup: BeautifulSoup) -> List[str]:
        """Extract services/products from HTML."""
        services = []

        # Look for common service/product keywords
        service_keywords = [
            'services', 'products', 'solutions', 'offerings', 'what we do',
            'insurance', 'policy', 'coverage', 'claim', 'benefit',
            'consultation', 'support', 'assistance', 'help'
        ]

        # Search in headings and nav items
        for element in soup.find_all(['h2', 'h3', 'h4', 'nav', 'li', 'a']):
            text = element.get_text().strip().lower()
            for keyword in service_keywords:
                if keyword in text and len(text) < 100:  # Reasonable length
                    clean_text = element.get_text().strip()
                    if clean_text and clean_text not in services and len(clean_text) > 3:
                        services.append(clean_text)

        # Limit to most relevant services
        return services[:8]

    def _extract_business_hours(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract business hours from HTML."""
        hours_patterns = [
            r'(\d{1,2}:?\d{0,2}\s*(?:am|pm|AM|PM)?\s*[-–]\s*\d{1,2}:?\d{0,2}\s*(?:am|pm|AM|PM)?)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday).*?(\d{1,2}:?\d{0,2})',
            r'(mon|tue|wed|thu|fri|sat|sun).*?(\d{1,2}:?\d{0,2})',
            r'(24/7|24 hours|round the clock)',
            r'(business hours|office hours|hours of operation)'
        ]

        text_content = soup.get_text()
        for pattern in hours_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                # Return first reasonable match
                for match in matches[:3]:
                    if isinstance(match, tuple):
                        match_text = ' '.join(match)
                    else:
                        match_text = match
                    if len(match_text) > 5 and len(match_text) < 100:
                        return match_text

        return "Please contact us for business hours"

    def _extract_contact_info(self, soup: BeautifulSoup) -> ExtractedContactInfo:
        """Extract contact information from HTML."""
        contact_info = ExtractedContactInfo()
        text_content = soup.get_text()

        # Extract phone numbers
        phone_pattern = r'(\+?[\d\s\-\(\)]{10,})'
        phone_matches = re.findall(phone_pattern, text_content)
        for match in phone_matches:
            # Clean and validate phone number
            cleaned = re.sub(r'[^\d+]', '', match)
            if len(cleaned) >= 10:
                contact_info.phone = match.strip()
                break

        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text_content)
        for email in email_matches:
            if not email.startswith(('no-reply', 'noreply')):
                contact_info.email = email
                break

        # Extract address (basic implementation)
        address_keywords = ['address', 'location', 'office', 'headquarters']
        for element in soup.find_all(['p', 'div', 'span']):
            text = element.get_text().strip()
            if any(keyword in text.lower() for keyword in address_keywords):
                # Look for text that might be an address
                if len(text) > 20 and len(text) < 200 and ',' in text:
                    contact_info.address = text
                    break

        return contact_info

    def _extract_about_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract about/description text from HTML."""
        # Try to find about section
        about_keywords = ['about', 'who we are', 'our story', 'company', 'overview']

        for keyword in about_keywords:
            # Look for headings with about keywords
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                if keyword in heading.get_text().lower():
                    # Find the next paragraph or div
                    next_element = heading.find_next(['p', 'div'])
                    if next_element:
                        text = next_element.get_text().strip()
                        if len(text) > 50 and len(text) < 1000:
                            return text

        # Fallback to first substantial paragraph
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if len(text) > 100 and len(text) < 800:
                return text

        return None

    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description from HTML."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content']

        # Try og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content']

        return None

# Service instance
site_extraction_service = SiteExtractionService()