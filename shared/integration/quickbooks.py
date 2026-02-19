"""
QuickBooks Integration Module

This module provides integration with QuickBooks Online for accounting automation,
financial data management, and business process integration.
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
    from intuitlib.client import AuthClient
    from intuitlib.enums import Scopes
    QUICKBOOKS_AVAILABLE = True
except ImportError:
    QUICKBOOKS_AVAILABLE = False
    logging.warning("QuickBooks APIs not available. Install requests and intuitlib")

logger = logging.getLogger(__name__)


class QuickBooksEntityType(Enum):
    """QuickBooks entity types."""
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    INVOICE = "Invoice"
    BILL = "Bill"
    PAYMENT = "Payment"
    EXPENSE = "Expense"
    ITEM = "Item"
    ACCOUNT = "Account"
    TAX_RATE = "TaxRate"
    COMPANY_INFO = "CompanyInfo"


class QuickBooksTransactionStatus(Enum):
    """QuickBooks transaction status."""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    VOIDED = "Voided"
    PAID = "Paid"
    OVERDUE = "Overdue"


@dataclass
class QuickBooksConfig:
    """Configuration for QuickBooks integration."""
    
    client_id: str
    """QuickBooks client ID."""
    
    client_secret: str
    """QuickBooks client secret."""
    
    environment: str = "sandbox"
    """Environment: sandbox or production."""
    
    redirect_uri: str = "http://localhost:8000/oauth/callback"
    """OAuth redirect URI."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""


@dataclass
class QuickBooksCustomer:
    """QuickBooks customer data structure."""
    
    id: str
    """Customer ID."""
    
    name: str
    """Customer name."""
    
    email: Optional[str] = None
    """Customer email."""
    
    phone: Optional[str] = None
    """Customer phone."""
    
    company_name: Optional[str] = None
    """Company name."""
    
    billing_address: Optional[Dict[str, Any]] = None
    """Billing address."""
    
    shipping_address: Optional[Dict[str, Any]] = None
    """Shipping address."""
    
    active: bool = True
    """Customer status."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class QuickBooksInvoice:
    """QuickBooks invoice data structure."""
    
    id: str
    """Invoice ID."""
    
    number: str
    """Invoice number."""
    
    customer_id: str
    """Customer ID."""
    
    amount: float
    """Invoice amount."""
    
    balance: float
    """Outstanding balance."""
    
    status: QuickBooksTransactionStatus
    """Invoice status."""
    
    due_date: Optional[datetime] = None
    """Due date."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""
    
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    """Invoice line items."""


@dataclass
class QuickBooksPayment:
    """QuickBooks payment data structure."""
    
    id: str
    """Payment ID."""
    
    amount: float
    """Payment amount."""
    
    payment_method: str
    """Payment method."""
    
    customer_id: str
    """Customer ID."""
    
    reference_number: Optional[str] = None
    """Reference number."""
    
    invoice_ids: List[str] = field(default_factory=list)
    """Applied invoice IDs."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""


@dataclass
class QuickBooksExpense:
    """QuickBooks expense data structure."""
    
    id: str
    """Expense ID."""
    
    amount: float
    """Expense amount."""
    
    account_id: str
    """Account ID."""
    
    vendor_id: Optional[str] = None
    """Vendor ID."""
    
    description: Optional[str] = None
    """Expense description."""
    
    date: Optional[datetime] = None
    """Expense date."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""


class QuickBooksIntegration:
    """QuickBooks integration for accounting automation."""
    
    def __init__(self, config: QuickBooksConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.auth_client = AuthClient(
            client_id=config.client_id,
            client_secret=config.client_secret,
            environment=config.environment,
            redirect_uri=config.redirect_uri
        )
        self.access_token = None
        self.realm_id = None
        self.base_url = f"https://{'sandbox-' if config.environment == 'sandbox' else ''}quickbooks.api.intuit.com"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def authenticate(self, auth_code: str, realm_id: str) -> bool:
        """
        Authenticate with QuickBooks.
        
        Args:
            auth_code: Authorization code from OAuth flow
            realm_id: QuickBooks realm ID
            
        Returns:
            True if successful
        """
        try:
            self.auth_client.get_bearer_token(auth_code, realm_id=realm_id)
            self.access_token = self.auth_client.access_token
            self.realm_id = realm_id
            
            self.logger.info("Successfully authenticated with QuickBooks")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to authenticate with QuickBooks: {e}")
            return False
    
    async def get_auth_url(self) -> str:
        """
        Get OAuth authorization URL.
        
        Returns:
            Authorization URL
        """
        scopes = [
            Scopes.ACCOUNTING,
            Scopes.OPENID,
            Scopes.EMAIL,
            Scopes.PROFILE
        ]
        
        auth_url = self.auth_client.get_authorization_url(scopes)
        return auth_url
    
    async def create_customer(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company_name: Optional[str] = None
    ) -> QuickBooksCustomer:
        """
        Create a customer.
        
        Args:
            name: Customer name
            email: Customer email
            phone: Customer phone
            company_name: Company name
            
        Returns:
            Customer data
        """
        try:
            url = f"{self.base_url}/v3/company/{self.realm_id}/customer"
            
            data = {
                "Name": name,
                "Active": True
            }
            
            if email:
                data["PrimaryEmailAddr"] = {"Address": email}
            if phone:
                data["PrimaryPhone"] = {"FreeFormNumber": phone}
            if company_name:
                data["CompanyName"] = company_name
            
            response = requests.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            customer_data = response.json()["Customer"]
            
            return QuickBooksCustomer(
                id=customer_data["Id"],
                name=customer_data["Name"],
                email=customer_data.get("PrimaryEmailAddr", {}).get("Address"),
                phone=customer_data.get("PrimaryPhone", {}).get("FreeFormNumber"),
                company_name=customer_data.get("CompanyName"),
                billing_address=customer_data.get("BillAddr"),
                shipping_address=customer_data.get("ShipAddr"),
                active=customer_data.get("Active", True),
                created_at=datetime.fromisoformat(customer_data["MetaData"]["CreateTime"].replace("Z", "+00:00")) if customer_data.get("MetaData", {}).get("CreateTime") else None,
                updated_at=datetime.fromisoformat(customer_data["MetaData"]["LastUpdatedTime"].replace("Z", "+00:00")) if customer_data.get("MetaData", {}).get("LastUpdatedTime") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create customer: {e}")
            raise
    
    async def get_customer(self, customer_id: str) -> QuickBooksCustomer:
        """
        Get customer details.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Customer data
        """
        try:
            url = f"{self.base_url}/v3/company/{self.realm_id}/customer/{customer_id}"
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            customer_data = response.json()["Customer"]
            
            return QuickBooksCustomer(
                id=customer_data["Id"],
                name=customer_data["Name"],
                email=customer_data.get("PrimaryEmailAddr", {}).get("Address"),
                phone=customer_data.get("PrimaryPhone", {}).get("FreeFormNumber"),
                company_name=customer_data.get("CompanyName"),
                billing_address=customer_data.get("BillAddr"),
                shipping_address=customer_data.get("ShipAddr"),
                active=customer_data.get("Active", True),
                created_at=datetime.fromisoformat(customer_data["MetaData"]["CreateTime"].replace("Z", "+00:00")) if customer_data.get("MetaData", {}).get("CreateTime") else None,
                updated_at=datetime.fromisoformat(customer_data["MetaData"]["LastUpdatedTime"].replace("Z", "+00:00")) if customer_data.get("MetaData", {}).get("LastUpdatedTime") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get customer: {e}")
            raise
    
    async def get_customers(self, limit: int = 100) -> List[QuickBooksCustomer]:
        """
        Get all customers.
        
        Args:
            limit: Number of customers to return
            
        Returns:
            List of customers
        """
        try:
            url = f"{self.base_url}/v3/company/{self.realm_id}/query"
            query = f"SELECT * FROM Customer MAXRESULTS {limit}"
            
            response = requests.get(url, params={"query": query}, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            customers = []
            
            for customer_data in result.get("QueryResponse", {}).get("Customer", []):
                customer = QuickBooksCustomer(
                    id=customer_data["Id"],
                    name=customer_data["Name"],
                    email=customer_data.get("PrimaryEmailAddr", {}).get("Address"),
                    phone=customer_data.get("PrimaryPhone", {}).get("FreeFormNumber"),
                    company_name=customer_data.get("CompanyName"),
                    billing_address=customer_data.get("BillAddr"),
                    shipping_address=customer_data.get("ShipAddr"),
                    active=customer_data.get("Active", True),
                    created_at=datetime.fromisoformat(customer_data["MetaData"]["CreateTime"].replace("Z", "+00:00")) if customer_data.get("MetaData", {}).get("CreateTime") else None,
                    updated_at=datetime.fromisoformat(customer_data["MetaData"]["LastUpdatedTime"].replace("Z", "+00:00")) if customer_data.get("MetaData", {}).get("LastUpdatedTime") else None
                )
                customers.append(customer)
            
            return customers
            
        except Exception as e:
            self.logger.error(f"Failed to get customers: {e}")
            raise
    
    async def create_invoice(
        self,
        customer_id: str,
        line_items: List[Dict[str, Any]],
        due_date: Optional[datetime] = None
    ) -> QuickBooksInvoice:
        """
        Create an invoice.
        
        Args:
            customer_id: Customer ID
            line_items: Invoice line items
            due_date: Due date
            
        Returns:
            Invoice data
        """
        try:
            url = f"{self.base_url}/v3/company/{self.realm_id}/invoice"
            
            data = {
                "CustomerRef": {"value": customer_id},
                "Line": line_items
            }
            
            if due_date:
                data["DueDate"] = due_date.strftime("%Y-%m-%d")
            
            response = requests.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            invoice_data = response.json()["Invoice"]
            
            return QuickBooksInvoice(
                id=invoice_data["Id"],
                number=invoice_data["DocNumber"],
                customer_id=invoice_data["CustomerRef"]["value"],
                amount=invoice_data["TotalAmt"],
                balance=invoice_data["Balance"],
                status=QuickBooksTransactionStatus(invoice_data["TxnStatus"]),
                due_date=datetime.strptime(invoice_data["DueDate"], "%Y-%m-%d") if invoice_data.get("DueDate") else None,
                created_at=datetime.fromisoformat(invoice_data["MetaData"]["CreateTime"].replace("Z", "+00:00")) if invoice_data.get("MetaData", {}).get("CreateTime") else None,
                updated_at=datetime.fromisoformat(invoice_data["MetaData"]["LastUpdatedTime"].replace("Z", "+00:00")) if invoice_data.get("MetaData", {}).get("LastUpdatedTime") else None,
                line_items=invoice_data.get("Line", [])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create invoice: {e}")
            raise
    
    async def get_invoice(self, invoice_id: str) -> QuickBooksInvoice:
        """
        Get invoice details.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice data
        """
        try:
            url = f"{self.base_url}/v3/company/{self.realm_id}/invoice/{invoice_id}"
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            invoice_data = response.json()["Invoice"]
            
            return QuickBooksInvoice(
                id=invoice_data["Id"],
                number=invoice_data["DocNumber"],
                customer_id=invoice_data["CustomerRef"]["value"],
                amount=invoice_data["TotalAmt"],
                balance=invoice_data["Balance"],
                status=QuickBooksTransactionStatus(invoice_data["TxnStatus"]),
                due_date=datetime.strptime(invoice_data["DueDate"], "%Y-%m-%d") if invoice_data.get("DueDate") else None,
                created_at=datetime.fromisoformat(invoice_data["MetaData"]["CreateTime"].replace("Z", "+00:00")) if invoice_data.get("MetaData", {}).get("CreateTime") else None,
                updated_at=datetime.fromisoformat(invoice_data["MetaData"]["LastUpdatedTime"].replace("Z", "+00:00")) if invoice_data.get("MetaData", {}).get("LastUpdatedTime") else None,
                line_items=invoice_data.get("Line", [])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get invoice: {e}")
            raise
    
    async def create_payment(
        self,
        customer_id: str,
        amount: float,
        payment_method: str,
        invoice_ids: Optional[List[str]] = None,
        reference_number: Optional[str] = None
    ) -> QuickBooksPayment:
        """
        Create a payment.
        
        Args:
            customer_id: Customer ID
            amount: Payment amount
            payment_method: Payment method
            invoice_ids: Invoice IDs to apply payment to
            reference_number: Reference number
            
        Returns:
            Payment data
        """
        try:
            url = f"{self.base_url}/v3/company/{self.realm_id}/payment"
            
            data = {
                "CustomerRef": {"value": customer_id},
                "TotalAmt": amount,
                "PaymentMethodRef": {"value": payment_method}
            }
            
            if reference_number:
                data["PaymentRefNum"] = reference_number
            
            if invoice_ids:
                data["Line"] = []
                for invoice_id in invoice_ids:
                    data["Line"].append({
                        "Amount": amount,
                        "LinkedTxn": [{"TxnId": invoice_id, "TxnType": "Invoice"}]
                    })
            
            response = requests.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            payment_data = response.json()["Payment"]
            
            return QuickBooksPayment(
                id=payment_data["Id"],
                amount=payment_data["TotalAmt"],
                payment_method=payment_data["PaymentMethodRef"]["value"],
                reference_number=payment_data.get("PaymentRefNum"),
                customer_id=payment_data["CustomerRef"]["value"],
                invoice_ids=[line["LinkedTxn"][0]["TxnId"] for line in payment_data.get("Line", []) if line.get("LinkedTxn")],
                created_at=datetime.fromisoformat(payment_data["MetaData"]["CreateTime"].replace("Z", "+00:00")) if payment_data.get("MetaData", {}).get("CreateTime") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create payment: {e}")
            raise
    
    async def create_expense(
        self,
        amount: float,
        account_id: str,
        description: Optional[str] = None,
        vendor_id: Optional[str] = None,
        date: Optional[datetime] = None
    ) -> QuickBooksExpense:
        """
        Create an expense.
        
        Args:
            amount: Expense amount
            account_id: Account ID
            description: Expense description
            vendor_id: Vendor ID
            date: Expense date
            
        Returns:
            Expense data
        """
        try:
            url = f"{self.base_url}/v3/company/{self.realm_id}/purchase"
            
            data = {
                "AccountRef": {"value": account_id},
                "TotalAmt": amount,
                "Line": [{
                    "Amount": amount,
                    "DetailType": "AccountBasedExpenseLineDetail",
                    "AccountBasedExpenseLineDetail": {
                        "AccountRef": {"value": account_id}
                    }
                }]
            }
            
            if description:
                data["Line"][0]["Description"] = description
            if vendor_id:
                data["VendorRef"] = {"value": vendor_id}
            if date:
                data["TxnDate"] = date.strftime("%Y-%m-%d")
            
            response = requests.post(url, json=data, headers=self._get_headers())
            response.raise_for_status()
            
            expense_data = response.json()["Purchase"]
            
            return QuickBooksExpense(
                id=expense_data["Id"],
                amount=expense_data["TotalAmt"],
                account_id=expense_data["AccountRef"]["value"],
                vendor_id=expense_data.get("VendorRef", {}).get("value"),
                description=expense_data.get("Line", [{}])[0].get("Description"),
                date=datetime.strptime(expense_data["TxnDate"], "%Y-%m-%d") if expense_data.get("TxnDate") else None,
                created_at=datetime.fromisoformat(expense_data["MetaData"]["CreateTime"].replace("Z", "+00:00")) if expense_data.get("MetaData", {}).get("CreateTime") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create expense: {e}")
            raise
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all accounts.
        
        Returns:
            List of accounts
        """
        try:
            url = f"{self.base_url}/v3/company/{self.realm_id}/query"
            query = "SELECT * FROM Account"
            
            response = requests.get(url, params={"query": query}, headers=self._get_headers())
            response.raise_for_status()
            
            result = response.json()
            return result.get("QueryResponse", {}).get("Account", [])
            
        except Exception as e:
            self.logger.error(f"Failed to get accounts: {e}")
            raise
    
    async def get_company_info(self) -> Dict[str, Any]:
        """
        Get company information.
        
        Returns:
            Company information
        """
        try:
            url = f"{self.base_url}/v3/company/{self.realm_id}/companyinfo/{self.realm_id}"
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            return response.json()["CompanyInfo"]
            
        except Exception as e:
            self.logger.error(f"Failed to get company info: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the QuickBooks integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting company info
            company_info = await self.get_company_info()
            
            # Test customer retrieval
            customers = await self.get_customers(limit=1)
            
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "company_name": company_info.get("CompanyName"),
                "customers_count": len(customers),
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

