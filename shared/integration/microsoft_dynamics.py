"""
Microsoft Dynamics ERP Integration Module

This module provides integration with Microsoft Dynamics 365 for enterprise
resource planning, customer relationship management, and business process automation.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

try:
    import requests
    from msal import ConfidentialClientApplication
    MICROSOFT_DYNAMICS_AVAILABLE = True
except ImportError:
    MICROSOFT_DYNAMICS_AVAILABLE = False
    logging.warning("Microsoft Dynamics APIs not available. Install requests and msal")

logger = logging.getLogger(__name__)


class DynamicsModuleType(Enum):
    """Microsoft Dynamics module types."""
    ACCOUNT = "accounts"
    CONTACT = "contacts"
    LEAD = "leads"
    OPPORTUNITY = "opportunities"
    INVOICE = "invoices"
    QUOTE = "quotes"
    ORDER = "salesorders"
    PRODUCT = "products"
    CASE = "incidents"


class DynamicsLeadStatus(Enum):
    """Microsoft Dynamics lead status."""
    NEW = "New"
    QUALIFIED = "Qualified"
    DISQUALIFIED = "Disqualified"
    OPEN = "Open"
    CLOSED = "Closed"


class DynamicsOpportunityStatus(Enum):
    """Microsoft Dynamics opportunity status."""
    OPEN = "Open"
    WON = "Won"
    LOST = "Lost"
    CLOSED = "Closed"


@dataclass
class DynamicsConfig:
    """Configuration for Microsoft Dynamics ERP integration."""
    
    tenant_id: str
    """Azure AD tenant ID."""
    
    client_id: str
    """Azure AD client ID."""
    
    client_secret: str
    """Azure AD client secret."""
    
    environment_url: str
    """Dynamics 365 environment URL."""
    
    api_version: str = "v9.2"
    """API version."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""


@dataclass
class DynamicsAccount:
    """Microsoft Dynamics account data structure."""
    
    id: str
    """Account ID."""
    
    name: str
    """Account name."""
    
    email: Optional[str] = None
    """Email address."""
    
    phone: Optional[str] = None
    """Phone number."""
    
    address1_line1: Optional[str] = None
    """Address line 1."""
    
    address1_city: Optional[str] = None
    """City."""
    
    address1_country: Optional[str] = None
    """Country."""
    
    industry: Optional[str] = None
    """Industry."""
    
    revenue: Optional[float] = None
    """Annual revenue."""
    
    number_of_employees: Optional[int] = None
    """Number of employees."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class DynamicsContact:
    """Microsoft Dynamics contact data structure."""
    
    id: str
    """Contact ID."""
    
    first_name: str
    """First name."""
    
    last_name: str
    """Last name."""
    
    email: Optional[str] = None
    """Email address."""
    
    phone: Optional[str] = None
    """Phone number."""
    
    job_title: Optional[str] = None
    """Job title."""
    
    account_id: Optional[str] = None
    """Account ID."""
    
    address1_line1: Optional[str] = None
    """Address line 1."""
    
    address1_city: Optional[str] = None
    """City."""
    
    address1_country: Optional[str] = None
    """Country."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class DynamicsLead:
    """Microsoft Dynamics lead data structure."""
    
    id: str
    """Lead ID."""
    
    first_name: str
    """First name."""
    
    last_name: str
    """Last name."""
    
    email: Optional[str] = None
    """Email address."""
    
    phone: Optional[str] = None
    """Phone number."""
    
    company_name: Optional[str] = None
    """Company name."""
    
    job_title: Optional[str] = None
    """Job title."""
    
    status: DynamicsLeadStatus
    """Lead status."""
    
    source: Optional[str] = None
    """Lead source."""
    
    subject: Optional[str] = None
    """Subject."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class DynamicsOpportunity:
    """Microsoft Dynamics opportunity data structure."""
    
    id: str
    """Opportunity ID."""
    
    name: str
    """Opportunity name."""
    
    account_id: Optional[str] = None
    """Account ID."""
    
    contact_id: Optional[str] = None
    """Contact ID."""
    
    estimated_value: float
    """Estimated value."""
    
    estimated_close_date: Optional[datetime] = None
    """Estimated close date."""
    
    status: DynamicsOpportunityStatus
    """Opportunity status."""
    
    probability: Optional[int] = None
    """Probability percentage."""
    
    description: Optional[str] = None
    """Description."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class DynamicsInvoice:
    """Microsoft Dynamics invoice data structure."""
    
    id: str
    """Invoice ID."""
    
    name: str
    """Invoice name."""
    
    account_id: Optional[str] = None
    """Account ID."""
    
    contact_id: Optional[str] = None
    """Contact ID."""
    
    total_amount: float
    """Total amount."""
    
    invoice_date: Optional[datetime] = None
    """Invoice date."""
    
    due_date: Optional[datetime] = None
    """Due date."""
    
    status: str
    """Invoice status."""
    
    description: Optional[str] = None
    """Description."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


class MicrosoftDynamicsIntegration:
    """Microsoft Dynamics ERP integration for enterprise resource planning."""
    
    def __init__(self, config: DynamicsConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = config.environment_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        self.access_token = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Microsoft Dynamics using Azure AD."""
        try:
            authority = f"https://login.microsoftonline.com/{self.config.tenant_id}"
            scopes = [f"{self.base_url}/.default"]
            
            app = ConfidentialClientApplication(
                client_id=self.config.client_id,
                client_credential=self.config.client_secret,
                authority=authority
            )
            
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                })
                self.logger.info("Successfully authenticated with Microsoft Dynamics")
            else:
                raise Exception(f"Authentication failed: {result.get('error_description', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Microsoft Dynamics: {e}")
            raise
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the Dynamics API."""
        try:
            url = f"{self.base_url}/api/data/{self.config.api_version}/{endpoint}"
            
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to make {method} request to {endpoint}: {e}")
            raise
    
    async def create_account(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address1_line1: Optional[str] = None,
        address1_city: Optional[str] = None,
        address1_country: Optional[str] = None,
        industry: Optional[str] = None,
        revenue: Optional[float] = None,
        number_of_employees: Optional[int] = None
    ) -> DynamicsAccount:
        """
        Create an account.
        
        Args:
            name: Account name
            email: Email address
            phone: Phone number
            address1_line1: Address line 1
            address1_city: City
            address1_country: Country
            industry: Industry
            revenue: Annual revenue
            number_of_employees: Number of employees
            
        Returns:
            Account data
        """
        try:
            data = {"name": name}
            
            if email:
                data["emailaddress1"] = email
            if phone:
                data["telephone1"] = phone
            if address1_line1:
                data["address1_line1"] = address1_line1
            if address1_city:
                data["address1_city"] = address1_city
            if address1_country:
                data["address1_country"] = address1_country
            if industry:
                data["industrycode"] = industry
            if revenue:
                data["revenue"] = revenue
            if number_of_employees:
                data["numberofemployees"] = number_of_employees
            
            result = self._make_request("POST", "accounts", data)
            account_id = result.get("accountid")
            
            if account_id:
                return await self.get_account(account_id)
            else:
                raise Exception("Failed to create account")
            
        except Exception as e:
            self.logger.error(f"Failed to create account: {e}")
            raise
    
    async def get_account(self, account_id: str) -> DynamicsAccount:
        """
        Get account details.
        
        Args:
            account_id: Account ID
            
        Returns:
            Account data
        """
        try:
            result = self._make_request("GET", f"accounts({account_id})")
            
            return DynamicsAccount(
                id=result["accountid"],
                name=result["name"],
                email=result.get("emailaddress1"),
                phone=result.get("telephone1"),
                address1_line1=result.get("address1_line1"),
                address1_city=result.get("address1_city"),
                address1_country=result.get("address1_country"),
                industry=result.get("industrycode"),
                revenue=result.get("revenue"),
                number_of_employees=result.get("numberofemployees"),
                created_at=datetime.fromisoformat(result["createdon"].replace("Z", "+00:00")) if result.get("createdon") else None,
                updated_at=datetime.fromisoformat(result["modifiedon"].replace("Z", "+00:00")) if result.get("modifiedon") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get account: {e}")
            raise
    
    async def get_accounts(self, limit: int = 100) -> List[DynamicsAccount]:
        """
        Get all accounts.
        
        Args:
            limit: Number of accounts to return
            
        Returns:
            List of accounts
        """
        try:
            result = self._make_request("GET", f"accounts?$top={limit}")
            accounts = []
            
            for account_data in result.get("value", []):
                account = DynamicsAccount(
                    id=account_data["accountid"],
                    name=account_data["name"],
                    email=account_data.get("emailaddress1"),
                    phone=account_data.get("telephone1"),
                    address1_line1=account_data.get("address1_line1"),
                    address1_city=account_data.get("address1_city"),
                    address1_country=account_data.get("address1_country"),
                    industry=account_data.get("industrycode"),
                    revenue=account_data.get("revenue"),
                    number_of_employees=account_data.get("numberofemployees"),
                    created_at=datetime.fromisoformat(account_data["createdon"].replace("Z", "+00:00")) if account_data.get("createdon") else None,
                    updated_at=datetime.fromisoformat(account_data["modifiedon"].replace("Z", "+00:00")) if account_data.get("modifiedon") else None
                )
                accounts.append(account)
            
            return accounts
            
        except Exception as e:
            self.logger.error(f"Failed to get accounts: {e}")
            raise
    
    async def create_contact(
        self,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        job_title: Optional[str] = None,
        account_id: Optional[str] = None,
        address1_line1: Optional[str] = None,
        address1_city: Optional[str] = None,
        address1_country: Optional[str] = None
    ) -> DynamicsContact:
        """
        Create a contact.
        
        Args:
            first_name: First name
            last_name: Last name
            email: Email address
            phone: Phone number
            job_title: Job title
            account_id: Account ID
            address1_line1: Address line 1
            address1_city: City
            address1_country: Country
            
        Returns:
            Contact data
        """
        try:
            data = {
                "firstname": first_name,
                "lastname": last_name
            }
            
            if email:
                data["emailaddress1"] = email
            if phone:
                data["telephone1"] = phone
            if job_title:
                data["jobtitle"] = job_title
            if account_id:
                data["_parentaccountid_value"] = account_id
            if address1_line1:
                data["address1_line1"] = address1_line1
            if address1_city:
                data["address1_city"] = address1_city
            if address1_country:
                data["address1_country"] = address1_country
            
            result = self._make_request("POST", "contacts", data)
            contact_id = result.get("contactid")
            
            if contact_id:
                return await self.get_contact(contact_id)
            else:
                raise Exception("Failed to create contact")
            
        except Exception as e:
            self.logger.error(f"Failed to create contact: {e}")
            raise
    
    async def get_contact(self, contact_id: str) -> DynamicsContact:
        """
        Get contact details.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            Contact data
        """
        try:
            result = self._make_request("GET", f"contacts({contact_id})")
            
            return DynamicsContact(
                id=result["contactid"],
                first_name=result["firstname"],
                last_name=result["lastname"],
                email=result.get("emailaddress1"),
                phone=result.get("telephone1"),
                job_title=result.get("jobtitle"),
                account_id=result.get("_parentaccountid_value"),
                address1_line1=result.get("address1_line1"),
                address1_city=result.get("address1_city"),
                address1_country=result.get("address1_country"),
                created_at=datetime.fromisoformat(result["createdon"].replace("Z", "+00:00")) if result.get("createdon") else None,
                updated_at=datetime.fromisoformat(result["modifiedon"].replace("Z", "+00:00")) if result.get("modifiedon") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get contact: {e}")
            raise
    
    async def create_lead(
        self,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company_name: Optional[str] = None,
        job_title: Optional[str] = None,
        status: DynamicsLeadStatus = DynamicsLeadStatus.NEW,
        source: Optional[str] = None,
        subject: Optional[str] = None
    ) -> DynamicsLead:
        """
        Create a lead.
        
        Args:
            first_name: First name
            last_name: Last name
            email: Email address
            phone: Phone number
            company_name: Company name
            job_title: Job title
            status: Lead status
            source: Lead source
            subject: Subject
            
        Returns:
            Lead data
        """
        try:
            data = {
                "firstname": first_name,
                "lastname": last_name,
                "statuscode": 1 if status == DynamicsLeadStatus.NEW else 2
            }
            
            if email:
                data["emailaddress1"] = email
            if phone:
                data["telephone1"] = phone
            if company_name:
                data["companyname"] = company_name
            if job_title:
                data["jobtitle"] = job_title
            if source:
                data["leadsourcecode"] = source
            if subject:
                data["subject"] = subject
            
            result = self._make_request("POST", "leads", data)
            lead_id = result.get("leadid")
            
            if lead_id:
                return await self.get_lead(lead_id)
            else:
                raise Exception("Failed to create lead")
            
        except Exception as e:
            self.logger.error(f"Failed to create lead: {e}")
            raise
    
    async def get_lead(self, lead_id: str) -> DynamicsLead:
        """
        Get lead details.
        
        Args:
            lead_id: Lead ID
            
        Returns:
            Lead data
        """
        try:
            result = self._make_request("GET", f"leads({lead_id})")
            
            return DynamicsLead(
                id=result["leadid"],
                first_name=result["firstname"],
                last_name=result["lastname"],
                email=result.get("emailaddress1"),
                phone=result.get("telephone1"),
                company_name=result.get("companyname"),
                job_title=result.get("jobtitle"),
                status=DynamicsLeadStatus.NEW if result.get("statuscode") == 1 else DynamicsLeadStatus.QUALIFIED,
                source=result.get("leadsourcecode"),
                subject=result.get("subject"),
                created_at=datetime.fromisoformat(result["createdon"].replace("Z", "+00:00")) if result.get("createdon") else None,
                updated_at=datetime.fromisoformat(result["modifiedon"].replace("Z", "+00:00")) if result.get("modifiedon") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get lead: {e}")
            raise
    
    async def create_opportunity(
        self,
        name: str,
        estimated_value: float,
        account_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        estimated_close_date: Optional[datetime] = None,
        status: DynamicsOpportunityStatus = DynamicsOpportunityStatus.OPEN,
        probability: Optional[int] = None,
        description: Optional[str] = None
    ) -> DynamicsOpportunity:
        """
        Create an opportunity.
        
        Args:
            name: Opportunity name
            estimated_value: Estimated value
            account_id: Account ID
            contact_id: Contact ID
            estimated_close_date: Estimated close date
            status: Opportunity status
            probability: Probability percentage
            description: Description
            
        Returns:
            Opportunity data
        """
        try:
            data = {
                "name": name,
                "estimatedvalue": estimated_value,
                "statuscode": 1 if status == DynamicsOpportunityStatus.OPEN else 2
            }
            
            if account_id:
                data["_parentaccountid_value"] = account_id
            if contact_id:
                data["_parentcontactid_value"] = contact_id
            if estimated_close_date:
                data["estimatedclosedate"] = estimated_close_date.strftime("%Y-%m-%d")
            if probability:
                data["closeprobability"] = probability
            if description:
                data["description"] = description
            
            result = self._make_request("POST", "opportunities", data)
            opportunity_id = result.get("opportunityid")
            
            if opportunity_id:
                return await self.get_opportunity(opportunity_id)
            else:
                raise Exception("Failed to create opportunity")
            
        except Exception as e:
            self.logger.error(f"Failed to create opportunity: {e}")
            raise
    
    async def get_opportunity(self, opportunity_id: str) -> DynamicsOpportunity:
        """
        Get opportunity details.
        
        Args:
            opportunity_id: Opportunity ID
            
        Returns:
            Opportunity data
        """
        try:
            result = self._make_request("GET", f"opportunities({opportunity_id})")
            
            return DynamicsOpportunity(
                id=result["opportunityid"],
                name=result["name"],
                account_id=result.get("_parentaccountid_value"),
                contact_id=result.get("_parentcontactid_value"),
                estimated_value=result["estimatedvalue"],
                estimated_close_date=datetime.strptime(result["estimatedclosedate"], "%Y-%m-%d") if result.get("estimatedclosedate") else None,
                status=DynamicsOpportunityStatus.OPEN if result.get("statuscode") == 1 else DynamicsOpportunityStatus.WON,
                probability=result.get("closeprobability"),
                description=result.get("description"),
                created_at=datetime.fromisoformat(result["createdon"].replace("Z", "+00:00")) if result.get("createdon") else None,
                updated_at=datetime.fromisoformat(result["modifiedon"].replace("Z", "+00:00")) if result.get("modifiedon") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get opportunity: {e}")
            raise
    
    async def create_invoice(
        self,
        name: str,
        total_amount: float,
        account_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        invoice_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        description: Optional[str] = None
    ) -> DynamicsInvoice:
        """
        Create an invoice.
        
        Args:
            name: Invoice name
            total_amount: Total amount
            account_id: Account ID
            contact_id: Contact ID
            invoice_date: Invoice date
            due_date: Due date
            description: Description
            
        Returns:
            Invoice data
        """
        try:
            data = {
                "name": name,
                "totalamount": total_amount
            }
            
            if account_id:
                data["_accountid_value"] = account_id
            if contact_id:
                data["_contactid_value"] = contact_id
            if invoice_date:
                data["invoicedate"] = invoice_date.strftime("%Y-%m-%d")
            if due_date:
                data["duedate"] = due_date.strftime("%Y-%m-%d")
            if description:
                data["description"] = description
            
            result = self._make_request("POST", "invoices", data)
            invoice_id = result.get("invoiceid")
            
            if invoice_id:
                return await self.get_invoice(invoice_id)
            else:
                raise Exception("Failed to create invoice")
            
        except Exception as e:
            self.logger.error(f"Failed to create invoice: {e}")
            raise
    
    async def get_invoice(self, invoice_id: str) -> DynamicsInvoice:
        """
        Get invoice details.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice data
        """
        try:
            result = self._make_request("GET", f"invoices({invoice_id})")
            
            return DynamicsInvoice(
                id=result["invoiceid"],
                name=result["name"],
                account_id=result.get("_accountid_value"),
                contact_id=result.get("_contactid_value"),
                total_amount=result["totalamount"],
                invoice_date=datetime.strptime(result["invoicedate"], "%Y-%m-%d") if result.get("invoicedate") else None,
                due_date=datetime.strptime(result["duedate"], "%Y-%m-%d") if result.get("duedate") else None,
                status=result.get("statecode", "Active"),
                description=result.get("description"),
                created_at=datetime.fromisoformat(result["createdon"].replace("Z", "+00:00")) if result.get("createdon") else None,
                updated_at=datetime.fromisoformat(result["modifiedon"].replace("Z", "+00:00")) if result.get("modifiedon") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get invoice: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Microsoft Dynamics ERP integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting accounts
            result = self._make_request("GET", "accounts?$top=1")
            
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "api_version": self.config.api_version,
                "accounts_count": len(result.get("value", [])),
                "api_connectivity": "successful",
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }

