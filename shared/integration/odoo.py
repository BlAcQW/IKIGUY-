"""
Odoo ERP Integration Module

This module provides integration with Odoo ERP for business process automation,
inventory management, and enterprise resource planning.
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
    ODOO_AVAILABLE = True
except ImportError:
    ODOO_AVAILABLE = False
    logging.warning("Odoo APIs not available. Install requests")

logger = logging.getLogger(__name__)


class OdooModuleType(Enum):
    """Odoo module types."""
    SALE = "sale.order"
    PURCHASE = "purchase.order"
    INVENTORY = "stock.picking"
    ACCOUNT = "account.move"
    PARTNER = "res.partner"
    PRODUCT = "product.product"
    EMPLOYEE = "hr.employee"
    PROJECT = "project.project"


class OdooOrderStatus(Enum):
    """Odoo order status."""
    DRAFT = "draft"
    SENT = "sent"
    SALE = "sale"
    DONE = "done"
    CANCELLED = "cancelled"


class OdooInvoiceStatus(Enum):
    """Odoo invoice status."""
    DRAFT = "draft"
    POSTED = "posted"
    CANCELLED = "cancelled"


@dataclass
class OdooConfig:
    """Configuration for Odoo ERP integration."""
    
    url: str
    """Odoo instance URL."""
    
    database: str
    """Database name."""
    
    username: str
    """Username."""
    
    password: str
    """Password."""
    
    timeout: int = 30
    """Request timeout in seconds."""
    
    verify_ssl: bool = True
    """Verify SSL certificates."""


@dataclass
class OdooSaleOrder:
    """Odoo sale order data structure."""
    
    id: int
    """Order ID."""
    
    name: str
    """Order name."""
    
    partner_id: int
    """Partner ID."""
    
    partner_name: str
    """Partner name."""
    
    amount_total: float
    """Total amount."""
    
    currency_id: int
    """Currency ID."""
    
    state: OdooOrderStatus
    """Order status."""
    
    date_order: Optional[datetime] = None
    """Order date."""
    
    payment_term_id: Optional[int] = None
    """Payment term ID."""
    
    user_id: Optional[int] = None
    """Salesperson ID."""
    
    team_id: Optional[int] = None
    """Sales team ID."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class OdooPurchaseOrder:
    """Odoo purchase order data structure."""
    
    id: int
    """Order ID."""
    
    name: str
    """Order name."""
    
    partner_id: int
    """Partner ID."""
    
    partner_name: str
    """Partner name."""
    
    amount_total: float
    """Total amount."""
    
    currency_id: int
    """Currency ID."""
    
    state: OdooOrderStatus
    """Order status."""
    
    date_order: Optional[datetime] = None
    """Order date."""
    
    payment_term_id: Optional[int] = None
    """Payment term ID."""
    
    user_id: Optional[int] = None
    """Purchaser ID."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class OdooInvoice:
    """Odoo invoice data structure."""
    
    id: int
    """Invoice ID."""
    
    name: str
    """Invoice name."""
    
    partner_id: int
    """Partner ID."""
    
    partner_name: str
    """Partner name."""
    
    amount_total: float
    """Total amount."""
    
    currency_id: int
    """Currency ID."""
    
    state: OdooInvoiceStatus
    """Invoice status."""
    
    invoice_date: Optional[datetime] = None
    """Invoice date."""
    
    due_date: Optional[datetime] = None
    """Due date."""
    
    payment_term_id: Optional[int] = None
    """Payment term ID."""
    
    user_id: Optional[int] = None
    """User ID."""
    
    move_type: str
    """Move type (out_invoice, in_invoice, etc.)."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class OdooPartner:
    """Odoo partner data structure."""
    
    id: int
    """Partner ID."""
    
    name: str
    """Partner name."""
    
    email: Optional[str] = None
    """Email address."""
    
    phone: Optional[str] = None
    """Phone number."""
    
    street: Optional[str] = None
    """Street address."""
    
    city: Optional[str] = None
    """City."""
    
    country_id: Optional[int] = None
    """Country ID."""
    
    is_company: bool
    """Whether it's a company."""
    
    customer_rank: int
    """Customer rank."""
    
    supplier_rank: int
    """Supplier rank."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


@dataclass
class OdooProduct:
    """Odoo product data structure."""
    
    id: int
    """Product ID."""
    
    name: str
    """Product name."""
    
    default_code: Optional[str] = None
    """Default code."""
    
    list_price: float
    """List price."""
    
    standard_price: float
    """Standard price."""
    
    type: str
    """Product type."""
    
    categ_id: int
    """Category ID."""
    
    categ_name: str
    """Category name."""
    
    uom_id: int
    """Unit of measure ID."""
    
    uom_name: str
    """Unit of measure name."""
    
    active: bool
    """Whether product is active."""
    
    created_at: Optional[datetime] = None
    """Creation timestamp."""
    
    updated_at: Optional[datetime] = None
    """Last update timestamp."""


class OdooIntegration:
    """Odoo ERP integration for business process automation."""
    
    def __init__(self, config: OdooConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = config.url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = config.timeout
        self.session.verify = config.verify_ssl
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        self.uid = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Odoo."""
        try:
            auth_url = f"{self.base_url}/web/session/authenticate"
            auth_data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": self.config.database,
                    "login": self.config.username,
                    "password": self.config.password
                },
                "id": 1
            }
            
            response = self.session.post(auth_url, json=auth_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("result") and result["result"].get("uid"):
                self.uid = result["result"]["uid"]
                self.logger.info("Successfully authenticated with Odoo")
            else:
                raise Exception("Authentication failed")
                
        except Exception as e:
            self.logger.error(f"Failed to authenticate with Odoo: {e}")
            raise
    
    def _call_method(self, model: str, method: str, params: List[Any]) -> Any:
        """Call Odoo method."""
        try:
            url = f"{self.base_url}/web/dataset/call_kw"
            data = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": method,
                    "args": params,
                    "kwargs": {}
                },
                "id": 1
            }
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("error"):
                raise Exception(f"Odoo API error: {result['error']}")
            
            return result.get("result")
            
        except Exception as e:
            self.logger.error(f"Failed to call Odoo method {method}: {e}")
            raise
    
    async def create_sale_order(
        self,
        partner_id: int,
        order_lines: List[Dict[str, Any]],
        date_order: Optional[datetime] = None,
        payment_term_id: Optional[int] = None,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None
    ) -> OdooSaleOrder:
        """
        Create a sale order.
        
        Args:
            partner_id: Partner ID
            order_lines: List of order lines
            date_order: Order date
            payment_term_id: Payment term ID
            user_id: Salesperson ID
            team_id: Sales team ID
            
        Returns:
            Sale order data
        """
        try:
            order_data = {
                "partner_id": partner_id,
                "order_line": order_lines
            }
            
            if date_order:
                order_data["date_order"] = date_order.strftime("%Y-%m-%d %H:%M:%S")
            if payment_term_id:
                order_data["payment_term_id"] = payment_term_id
            if user_id:
                order_data["user_id"] = user_id
            if team_id:
                order_data["team_id"] = team_id
            
            order_id = self._call_method("sale.order", "create", [order_data])
            
            # Get the created order
            return await self.get_sale_order(order_id)
            
        except Exception as e:
            self.logger.error(f"Failed to create sale order: {e}")
            raise
    
    async def get_sale_order(self, order_id: int) -> OdooSaleOrder:
        """
        Get sale order details.
        
        Args:
            order_id: Order ID
            
        Returns:
            Sale order data
        """
        try:
            fields = [
                "name", "partner_id", "amount_total", "currency_id", "state",
                "date_order", "payment_term_id", "user_id", "team_id",
                "create_date", "write_date"
            ]
            
            order_data = self._call_method("sale.order", "read", [[order_id], fields])
            
            if not order_data:
                raise Exception(f"Sale order {order_id} not found")
            
            order = order_data[0]
            
            # Get partner name
            partner_data = self._call_method("res.partner", "read", [[order["partner_id"][0]], ["name"]])
            partner_name = partner_data[0]["name"] if partner_data else ""
            
            return OdooSaleOrder(
                id=order["id"],
                name=order["name"],
                partner_id=order["partner_id"][0],
                partner_name=partner_name,
                amount_total=order["amount_total"],
                currency_id=order["currency_id"][0],
                state=OdooOrderStatus(order["state"]),
                date_order=datetime.strptime(order["date_order"], "%Y-%m-%d %H:%M:%S") if order.get("date_order") else None,
                payment_term_id=order["payment_term_id"][0] if order.get("payment_term_id") else None,
                user_id=order["user_id"][0] if order.get("user_id") else None,
                team_id=order["team_id"][0] if order.get("team_id") else None,
                created_at=datetime.strptime(order["create_date"], "%Y-%m-%d %H:%M:%S") if order.get("create_date") else None,
                updated_at=datetime.strptime(order["write_date"], "%Y-%m-%d %H:%M:%S") if order.get("write_date") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get sale order: {e}")
            raise
    
    async def get_sale_orders(self, limit: int = 100) -> List[OdooSaleOrder]:
        """
        Get all sale orders.
        
        Args:
            limit: Number of orders to return
            
        Returns:
            List of sale orders
        """
        try:
            fields = [
                "name", "partner_id", "amount_total", "currency_id", "state",
                "date_order", "payment_term_id", "user_id", "team_id",
                "create_date", "write_date"
            ]
            
            order_ids = self._call_method("sale.order", "search", [[], 0, limit])
            orders_data = self._call_method("sale.order", "read", [order_ids, fields])
            
            orders = []
            for order in orders_data:
                # Get partner name
                partner_data = self._call_method("res.partner", "read", [[order["partner_id"][0]], ["name"]])
                partner_name = partner_data[0]["name"] if partner_data else ""
                
                sale_order = OdooSaleOrder(
                    id=order["id"],
                    name=order["name"],
                    partner_id=order["partner_id"][0],
                    partner_name=partner_name,
                    amount_total=order["amount_total"],
                    currency_id=order["currency_id"][0],
                    state=OdooOrderStatus(order["state"]),
                    date_order=datetime.strptime(order["date_order"], "%Y-%m-%d %H:%M:%S") if order.get("date_order") else None,
                    payment_term_id=order["payment_term_id"][0] if order.get("payment_term_id") else None,
                    user_id=order["user_id"][0] if order.get("user_id") else None,
                    team_id=order["team_id"][0] if order.get("team_id") else None,
                    created_at=datetime.strptime(order["create_date"], "%Y-%m-%d %H:%M:%S") if order.get("create_date") else None,
                    updated_at=datetime.strptime(order["write_date"], "%Y-%m-%d %H:%M:%S") if order.get("write_date") else None
                )
                orders.append(sale_order)
            
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get sale orders: {e}")
            raise
    
    async def create_purchase_order(
        self,
        partner_id: int,
        order_lines: List[Dict[str, Any]],
        date_order: Optional[datetime] = None,
        payment_term_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> OdooPurchaseOrder:
        """
        Create a purchase order.
        
        Args:
            partner_id: Partner ID
            order_lines: List of order lines
            date_order: Order date
            payment_term_id: Payment term ID
            user_id: Purchaser ID
            
        Returns:
            Purchase order data
        """
        try:
            order_data = {
                "partner_id": partner_id,
                "order_line": order_lines
            }
            
            if date_order:
                order_data["date_order"] = date_order.strftime("%Y-%m-%d %H:%M:%S")
            if payment_term_id:
                order_data["payment_term_id"] = payment_term_id
            if user_id:
                order_data["user_id"] = user_id
            
            order_id = self._call_method("purchase.order", "create", [order_data])
            
            # Get the created order
            return await self.get_purchase_order(order_id)
            
        except Exception as e:
            self.logger.error(f"Failed to create purchase order: {e}")
            raise
    
    async def get_purchase_order(self, order_id: int) -> OdooPurchaseOrder:
        """
        Get purchase order details.
        
        Args:
            order_id: Order ID
            
        Returns:
            Purchase order data
        """
        try:
            fields = [
                "name", "partner_id", "amount_total", "currency_id", "state",
                "date_order", "payment_term_id", "user_id", "create_date", "write_date"
            ]
            
            order_data = self._call_method("purchase.order", "read", [[order_id], fields])
            
            if not order_data:
                raise Exception(f"Purchase order {order_id} not found")
            
            order = order_data[0]
            
            # Get partner name
            partner_data = self._call_method("res.partner", "read", [[order["partner_id"][0]], ["name"]])
            partner_name = partner_data[0]["name"] if partner_data else ""
            
            return OdooPurchaseOrder(
                id=order["id"],
                name=order["name"],
                partner_id=order["partner_id"][0],
                partner_name=partner_name,
                amount_total=order["amount_total"],
                currency_id=order["currency_id"][0],
                state=OdooOrderStatus(order["state"]),
                date_order=datetime.strptime(order["date_order"], "%Y-%m-%d %H:%M:%S") if order.get("date_order") else None,
                payment_term_id=order["payment_term_id"][0] if order.get("payment_term_id") else None,
                user_id=order["user_id"][0] if order.get("user_id") else None,
                created_at=datetime.strptime(order["create_date"], "%Y-%m-%d %H:%M:%S") if order.get("create_date") else None,
                updated_at=datetime.strptime(order["write_date"], "%Y-%m-%d %H:%M:%S") if order.get("write_date") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get purchase order: {e}")
            raise
    
    async def create_invoice(
        self,
        partner_id: int,
        invoice_lines: List[Dict[str, Any]],
        invoice_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        payment_term_id: Optional[int] = None,
        user_id: Optional[int] = None,
        move_type: str = "out_invoice"
    ) -> OdooInvoice:
        """
        Create an invoice.
        
        Args:
            partner_id: Partner ID
            invoice_lines: List of invoice lines
            invoice_date: Invoice date
            due_date: Due date
            payment_term_id: Payment term ID
            user_id: User ID
            move_type: Move type
            
        Returns:
            Invoice data
        """
        try:
            invoice_data = {
                "partner_id": partner_id,
                "invoice_line_ids": invoice_lines,
                "move_type": move_type
            }
            
            if invoice_date:
                invoice_data["invoice_date"] = invoice_date.strftime("%Y-%m-%d")
            if due_date:
                invoice_data["invoice_date_due"] = due_date.strftime("%Y-%m-%d")
            if payment_term_id:
                invoice_data["payment_term_id"] = payment_term_id
            if user_id:
                invoice_data["user_id"] = user_id
            
            invoice_id = self._call_method("account.move", "create", [invoice_data])
            
            # Get the created invoice
            return await self.get_invoice(invoice_id)
            
        except Exception as e:
            self.logger.error(f"Failed to create invoice: {e}")
            raise
    
    async def get_invoice(self, invoice_id: int) -> OdooInvoice:
        """
        Get invoice details.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice data
        """
        try:
            fields = [
                "name", "partner_id", "amount_total", "currency_id", "state",
                "invoice_date", "invoice_date_due", "payment_term_id", "user_id",
                "move_type", "create_date", "write_date"
            ]
            
            invoice_data = self._call_method("account.move", "read", [[invoice_id], fields])
            
            if not invoice_data:
                raise Exception(f"Invoice {invoice_id} not found")
            
            invoice = invoice_data[0]
            
            # Get partner name
            partner_data = self._call_method("res.partner", "read", [[invoice["partner_id"][0]], ["name"]])
            partner_name = partner_data[0]["name"] if partner_data else ""
            
            return OdooInvoice(
                id=invoice["id"],
                name=invoice["name"],
                partner_id=invoice["partner_id"][0],
                partner_name=partner_name,
                amount_total=invoice["amount_total"],
                currency_id=invoice["currency_id"][0],
                state=OdooInvoiceStatus(invoice["state"]),
                invoice_date=datetime.strptime(invoice["invoice_date"], "%Y-%m-%d") if invoice.get("invoice_date") else None,
                due_date=datetime.strptime(invoice["invoice_date_due"], "%Y-%m-%d") if invoice.get("invoice_date_due") else None,
                payment_term_id=invoice["payment_term_id"][0] if invoice.get("payment_term_id") else None,
                user_id=invoice["user_id"][0] if invoice.get("user_id") else None,
                move_type=invoice["move_type"],
                created_at=datetime.strptime(invoice["create_date"], "%Y-%m-%d %H:%M:%S") if invoice.get("create_date") else None,
                updated_at=datetime.strptime(invoice["write_date"], "%Y-%m-%d %H:%M:%S") if invoice.get("write_date") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get invoice: {e}")
            raise
    
    async def create_partner(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        street: Optional[str] = None,
        city: Optional[str] = None,
        country_id: Optional[int] = None,
        is_company: bool = False
    ) -> OdooPartner:
        """
        Create a partner.
        
        Args:
            name: Partner name
            email: Email address
            phone: Phone number
            street: Street address
            city: City
            country_id: Country ID
            is_company: Whether it's a company
            
        Returns:
            Partner data
        """
        try:
            partner_data = {
                "name": name,
                "is_company": is_company
            }
            
            if email:
                partner_data["email"] = email
            if phone:
                partner_data["phone"] = phone
            if street:
                partner_data["street"] = street
            if city:
                partner_data["city"] = city
            if country_id:
                partner_data["country_id"] = country_id
            
            partner_id = self._call_method("res.partner", "create", [partner_data])
            
            # Get the created partner
            return await self.get_partner(partner_id)
            
        except Exception as e:
            self.logger.error(f"Failed to create partner: {e}")
            raise
    
    async def get_partner(self, partner_id: int) -> OdooPartner:
        """
        Get partner details.
        
        Args:
            partner_id: Partner ID
            
        Returns:
            Partner data
        """
        try:
            fields = [
                "name", "email", "phone", "street", "city", "country_id",
                "is_company", "customer_rank", "supplier_rank", "create_date", "write_date"
            ]
            
            partner_data = self._call_method("res.partner", "read", [[partner_id], fields])
            
            if not partner_data:
                raise Exception(f"Partner {partner_id} not found")
            
            partner = partner_data[0]
            
            return OdooPartner(
                id=partner["id"],
                name=partner["name"],
                email=partner.get("email"),
                phone=partner.get("phone"),
                street=partner.get("street"),
                city=partner.get("city"),
                country_id=partner["country_id"][0] if partner.get("country_id") else None,
                is_company=partner["is_company"],
                customer_rank=partner["customer_rank"],
                supplier_rank=partner["supplier_rank"],
                created_at=datetime.strptime(partner["create_date"], "%Y-%m-%d %H:%M:%S") if partner.get("create_date") else None,
                updated_at=datetime.strptime(partner["write_date"], "%Y-%m-%d %H:%M:%S") if partner.get("write_date") else None
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get partner: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the Odoo ERP integration.
        
        Returns:
            Health check results
        """
        try:
            # Test API connectivity by getting partners
            partner_ids = self._call_method("res.partner", "search", [[], 0, 1])
            
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "database": self.config.database,
                "uid": self.uid,
                "partners_count": len(partner_ids),
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

