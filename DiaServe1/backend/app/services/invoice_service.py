"""
Invoice service for EstateFlow.

Handles invoice creation, numbering, calculations, and payment tracking.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.invoice import (
    Invoice,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceMarkPaid,
    InvoiceFilters,
    InvoiceListResponse,
    InvoiceStats,
    InvoiceStatus,
)

# Import local service stubs (replaces missing shared library)
from app.integration.document_generation_service import get_document_generation_service
from app.integration.email_service import get_email_service

logger = logging.getLogger(__name__)


class InvoiceService:
    """Service for managing invoices."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize invoice service.

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db.invoices

    async def _get_next_invoice_number(self, organization_id: str) -> str:
        """
        Generate next invoice number for organization.

        Args:
            organization_id: Organization ID

        Returns:
            Invoice number (e.g., DIA-1001)
        """
        # Get organization to fetch invoice settings
        org = await self.db.organizations.find_one({"id": organization_id})

        if not org:
            raise ValueError(f"Organization {organization_id} not found")

        # Get invoice settings
        invoice_settings = org.get("invoice_settings", {})
        prefix = invoice_settings.get("invoice_prefix", "INV")
        next_number = invoice_settings.get("next_invoice_number", 1000)

        # Generate invoice number
        invoice_number = f"{prefix}-{next_number}"

        # Increment next_invoice_number in organization
        await self.db.organizations.update_one(
            {"id": organization_id},
            {
                "$set": {
                    "invoice_settings.next_invoice_number": next_number + 1,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return invoice_number

    def _calculate_invoice_totals(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate invoice totals from line items.

        Args:
            invoice_data: Invoice data with line_items

        Returns:
            Updated invoice data with calculated totals
        """
        line_items = invoice_data.get("line_items", [])

        subtotal = 0.0
        tax_amount = 0.0

        # Calculate each line item
        for item in line_items:
            # Calculate line amount
            item["amount"] = item["quantity"] * item["unit_price"]

            # Calculate line tax
            tax_rate = item.get("tax_rate", 0.0)
            item["tax_amount"] = (item["amount"] * tax_rate) / 100

            # Add to totals
            subtotal += item["amount"]
            tax_amount += item["tax_amount"]

        # Update invoice totals
        invoice_data["subtotal"] = round(subtotal, 2)
        invoice_data["tax_amount"] = round(tax_amount, 2)
        invoice_data["total_amount"] = round(subtotal + tax_amount, 2)

        return invoice_data

    async def _get_contact_info(self, contact_id: str) -> Dict[str, str]:
        """
        Get contact information.

        Args:
            contact_id: Contact ID

        Returns:
            Contact information dict
        """
        contact = await self.db.contacts.find_one({"id": contact_id})

        if not contact:
            return {
                "contact_name": "Unknown Customer",
                "contact_email": "",
                "contact_phone": "",
                "contact_address": ""
            }

        return {
            "contact_name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
            "contact_email": contact.get("email", ""),
            "contact_phone": contact.get("phone", ""),
            "contact_address": contact.get("address", "")
        }

    async def _get_property_info(self, property_id: Optional[str]) -> Dict[str, str]:
        """
        Get property information.

        Args:
            property_id: Property ID (optional)

        Returns:
            Property information dict
        """
        if not property_id:
            return {"property_name": ""}

        property_doc = await self.db.properties.find_one({"id": property_id})

        if not property_doc:
            return {"property_name": ""}

        return {
            "property_name": property_doc.get("name", "")
        }

    async def create_invoice(
        self,
        organization_id: str,
        user_id: str,
        invoice_data: InvoiceCreate
    ) -> Invoice:
        """
        Create a new invoice.

        Args:
            organization_id: Organization ID
            user_id: User ID creating the invoice
            invoice_data: Invoice creation data

        Returns:
            Created invoice
        """
        # Generate invoice number
        invoice_number = await self._get_next_invoice_number(organization_id)

        # Get contact information
        contact_info = await self._get_contact_info(invoice_data.contact_id)

        # Get property information
        property_info = await self._get_property_info(invoice_data.property_id)

        # Build invoice document
        invoice_dict = {
            "id": str(uuid4()),
            "organization_id": organization_id,
            "invoice_number": invoice_number,
            "invoice_date": datetime.utcnow(),
            "due_date": invoice_data.due_date,
            "contact_id": invoice_data.contact_id,
            **contact_info,
            "property_id": invoice_data.property_id,
            **property_info,
            "line_items": [item.dict() for item in invoice_data.line_items],
            "currency": invoice_data.currency,
            "notes": invoice_data.notes or "",
            "terms": invoice_data.terms or "",
            "status": InvoiceStatus.DRAFT,
            "payment_method": None,
            "paid_date": None,
            "paid_amount": 0.0,
            "created_by": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "sent_at": None,
            "is_deleted": False,
            "deleted_at": None
        }

        # Calculate totals
        invoice_dict = self._calculate_invoice_totals(invoice_dict)

        # Insert into database
        await self.collection.insert_one(invoice_dict)

        logger.info(f"Created invoice {invoice_number} for organization {organization_id}")

        return Invoice(**invoice_dict)

    async def get_invoice(self, invoice_id: str, organization_id: str) -> Optional[Invoice]:
        """
        Get invoice by ID.

        Args:
            invoice_id: Invoice ID
            organization_id: Organization ID

        Returns:
            Invoice or None
        """
        invoice_dict = await self.collection.find_one({
            "id": invoice_id,
            "organization_id": organization_id,
            "is_deleted": False
        })

        if not invoice_dict:
            return None

        return Invoice(**invoice_dict)

    async def list_invoices(
        self,
        organization_id: str,
        filters: InvoiceFilters
    ) -> InvoiceListResponse:
        """
        List invoices with filters.

        Args:
            organization_id: Organization ID
            filters: Filter criteria

        Returns:
            Invoice list response
        """
        # Build query
        query: Dict[str, Any] = {
            "organization_id": organization_id,
            "is_deleted": False
        }

        # Status filter
        if filters.status:
            query["status"] = {"$in": [s.value for s in filters.status]}

        # Contact filter
        if filters.contact_id:
            query["contact_id"] = filters.contact_id

        # Property filter
        if filters.property_id:
            query["property_id"] = filters.property_id

        # Date range filter
        if filters.from_date or filters.to_date:
            date_query = {}
            if filters.from_date:
                date_query["$gte"] = filters.from_date
            if filters.to_date:
                date_query["$lte"] = filters.to_date
            query["invoice_date"] = date_query

        # Amount range filter
        if filters.min_amount is not None or filters.max_amount is not None:
            amount_query = {}
            if filters.min_amount is not None:
                amount_query["$gte"] = filters.min_amount
            if filters.max_amount is not None:
                amount_query["$lte"] = filters.max_amount
            query["total_amount"] = amount_query

        # Search filter
        if filters.search:
            query["$or"] = [
                {"invoice_number": {"$regex": filters.search, "$options": "i"}},
                {"contact_name": {"$regex": filters.search, "$options": "i"}}
            ]

        # Get total count
        total = await self.collection.count_documents(query)

        # Build sort
        sort_order = 1 if filters.sort_order == "asc" else -1
        sort = [(filters.sort_by, sort_order)]

        # Query with pagination
        cursor = self.collection.find(query).sort(sort).skip(filters.offset).limit(filters.limit)
        invoice_dicts = await cursor.to_list(length=filters.limit)

        invoices = [Invoice(**inv) for inv in invoice_dicts]

        return InvoiceListResponse(
            invoices=invoices,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
            has_more=(filters.offset + len(invoices)) < total
        )

    async def update_invoice(
        self,
        invoice_id: str,
        organization_id: str,
        updates: InvoiceUpdate
    ) -> Optional[Invoice]:
        """
        Update an invoice.

        Args:
            invoice_id: Invoice ID
            organization_id: Organization ID
            updates: Update data

        Returns:
            Updated invoice or None
        """
        # Get existing invoice
        invoice = await self.get_invoice(invoice_id, organization_id)
        if not invoice:
            return None

        # Only allow updates for draft or sent invoices
        if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.SENT]:
            raise ValueError("Cannot update paid or cancelled invoices")

        # Build update dict
        update_dict = {"updated_at": datetime.utcnow()}

        if updates.due_date is not None:
            update_dict["due_date"] = updates.due_date

        if updates.notes is not None:
            update_dict["notes"] = updates.notes

        if updates.terms is not None:
            update_dict["terms"] = updates.terms

        if updates.status is not None:
            update_dict["status"] = updates.status
            if updates.status == InvoiceStatus.SENT and not invoice.sent_at:
                update_dict["sent_at"] = datetime.utcnow()

        if updates.line_items is not None:
            # Recalculate totals
            temp_dict = {
                "line_items": [item.dict() for item in updates.line_items]
            }
            temp_dict = self._calculate_invoice_totals(temp_dict)

            update_dict["line_items"] = temp_dict["line_items"]
            update_dict["subtotal"] = temp_dict["subtotal"]
            update_dict["tax_amount"] = temp_dict["tax_amount"]
            update_dict["total_amount"] = temp_dict["total_amount"]

        # Update in database
        await self.collection.update_one(
            {"id": invoice_id, "organization_id": organization_id},
            {"$set": update_dict}
        )

        # Return updated invoice
        return await self.get_invoice(invoice_id, organization_id)

    async def delete_invoice(self, invoice_id: str, organization_id: str) -> bool:
        """
        Delete (soft delete) an invoice.

        Args:
            invoice_id: Invoice ID
            organization_id: Organization ID

        Returns:
            True if deleted
        """
        # Get existing invoice
        invoice = await self.get_invoice(invoice_id, organization_id)
        if not invoice:
            return False

        # Only allow deletion for draft invoices
        if invoice.status != InvoiceStatus.DRAFT:
            raise ValueError("Only draft invoices can be deleted")

        # Soft delete
        await self.collection.update_one(
            {"id": invoice_id, "organization_id": organization_id},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Deleted invoice {invoice_id} for organization {organization_id}")
        return True

    async def mark_paid(
        self,
        invoice_id: str,
        organization_id: str,
        payment_data: InvoiceMarkPaid
    ) -> Optional[Invoice]:
        """
        Mark invoice as paid.

        Args:
            invoice_id: Invoice ID
            organization_id: Organization ID
            payment_data: Payment information

        Returns:
            Updated invoice or None
        """
        # Get existing invoice
        invoice = await self.get_invoice(invoice_id, organization_id)
        if not invoice:
            return None

        # Update payment information
        await self.collection.update_one(
            {"id": invoice_id, "organization_id": organization_id},
            {
                "$set": {
                    "status": InvoiceStatus.PAID,
                    "payment_method": payment_data.payment_method,
                    "paid_amount": payment_data.paid_amount,
                    "paid_date": payment_data.paid_date,
                    "notes": payment_data.notes or invoice.notes,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Marked invoice {invoice_id} as paid")

        return await self.get_invoice(invoice_id, organization_id)

    async def get_stats(self, organization_id: str, currency: str = "GHS") -> InvoiceStats:
        """
        Get invoice statistics.

        Args:
            organization_id: Organization ID
            currency: Currency filter

        Returns:
            Invoice statistics
        """
        # Base query
        query = {
            "organization_id": organization_id,
            "is_deleted": False,
            "currency": currency
        }

        # Total invoices
        total_invoices = await self.collection.count_documents(query)

        # Status counts
        draft_count = await self.collection.count_documents({**query, "status": InvoiceStatus.DRAFT})
        sent_count = await self.collection.count_documents({**query, "status": InvoiceStatus.SENT})
        paid_count = await self.collection.count_documents({**query, "status": InvoiceStatus.PAID})
        overdue_count = await self.collection.count_documents({**query, "status": InvoiceStatus.OVERDUE})

        # Revenue (all paid invoices)
        paid_pipeline = [
            {"$match": {**query, "status": InvoiceStatus.PAID}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]
        paid_result = await self.collection.aggregate(paid_pipeline).to_list(length=1)
        total_revenue = paid_result[0]["total"] if paid_result else 0.0

        # Pending amount (sent invoices)
        pending_pipeline = [
            {"$match": {**query, "status": InvoiceStatus.SENT}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]
        pending_result = await self.collection.aggregate(pending_pipeline).to_list(length=1)
        pending_amount = pending_result[0]["total"] if pending_result else 0.0

        # Overdue amount
        overdue_pipeline = [
            {"$match": {**query, "status": InvoiceStatus.OVERDUE}},
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]
        overdue_result = await self.collection.aggregate(overdue_pipeline).to_list(length=1)
        overdue_amount = overdue_result[0]["total"] if overdue_result else 0.0

        return InvoiceStats(
            total_invoices=total_invoices,
            total_revenue=round(total_revenue, 2),
            pending_amount=round(pending_amount, 2),
            overdue_amount=round(overdue_amount, 2),
            draft_count=draft_count,
            sent_count=sent_count,
            paid_count=paid_count,
            overdue_count=overdue_count,
            currency=currency
        )

    async def generate_pdf(self, invoice_id: str, organization_id: str) -> bytes:
        """
        Generate PDF for an invoice using centralized document generation service.

        Args:
            invoice_id: Invoice ID
            organization_id: Organization ID

        Returns:
            PDF file as bytes

        Raises:
            ValueError: If invoice or organization not found
        """
        # Get invoice
        invoice = await self.get_invoice(invoice_id, organization_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        # Get organization
        org = await self.db.organizations.find_one({"id": organization_id})
        if not org:
            raise ValueError(f"Organization {organization_id} not found")

        # Prepare template data
        template_data = {
            "invoice": invoice.dict(),
            "organization": {
                "name": org.get("name", ""),
                "address": org.get("address", ""),
                "phone": org.get("phone", ""),
                "email": org.get("email", ""),
                "website": org.get("website", ""),
                "tax_id": org.get("tax_id", ""),
                "payment_info": org.get("payment_info", "")
            }
        }

        # Get document generation service
        doc_service = get_document_generation_service()

        # Get template directory
        template_dir = Path(__file__).parent.parent / "templates" / "invoices"

        # Generate PDF using centralized service
        pdf_bytes = await doc_service.generate_pdf(
            template_name="invoice.html",
            template_dir=template_dir,
            context=template_data
        )

        logger.info(f"Generated PDF for invoice {invoice_id} using centralized service")

        return pdf_bytes

    async def send_invoice(
        self,
        invoice_id: str,
        organization_id: str,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send invoice via email to customer with PDF attachment.

        Args:
            invoice_id: Invoice ID
            organization_id: Organization ID
            custom_message: Optional custom message to include in email

        Returns:
            Send result dictionary with success status

        Raises:
            ValueError: If invoice or organization not found, or if contact has no email
        """
        # Get invoice
        invoice = await self.get_invoice(invoice_id, organization_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")

        # Check if contact has email
        if not invoice.contact_email:
            raise ValueError(f"Contact {invoice.contact_name} has no email address")

        # Get organization
        org = await self.db.organizations.find_one({"id": organization_id})
        if not org:
            raise ValueError(f"Organization {organization_id} not found")

        # Generate PDF
        pdf_bytes = await self.generate_pdf(invoice_id, organization_id)

        # Get email service
        email_service = get_email_service()

        # Prepare email content
        org_name = org.get("name", "Estate Management")

        # Build email subject
        subject = f"Invoice {invoice.invoice_number} from {org_name}"

        # Build email body (plain text)
        body = f"""Dear {invoice.contact_name},

Please find attached invoice {invoice.invoice_number} for {invoice.currency} {invoice.total_amount:.2f}.

Invoice Details:
- Invoice Number: {invoice.invoice_number}
- Invoice Date: {invoice.invoice_date.strftime('%B %d, %Y')}
- Due Date: {invoice.due_date.strftime('%B %d, %Y')}
- Amount Due: {invoice.currency} {invoice.total_amount:.2f}

"""

        if invoice.property_name:
            body += f"- Property: {invoice.property_name}\n\n"

        if custom_message:
            body += f"{custom_message}\n\n"

        if invoice.notes:
            body += f"Notes: {invoice.notes}\n\n"

        # Add payment instructions
        if org.get("payment_info"):
            body += f"Payment Information:\n{org.get('payment_info')}\n\n"

        body += f"""Please make payment by {invoice.due_date.strftime('%B %d, %Y')}.

If you have any questions, please don't hesitate to contact us.

Best regards,
{org_name}
{org.get('email', '')}
{org.get('phone', '')}
"""

        # Build HTML body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #1e3a5f; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .invoice-details {{ background-color: white; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .detail-row {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .label {{ font-weight: bold; display: inline-block; width: 150px; }}
        .amount {{ font-size: 24px; font-weight: bold; color: #1e3a5f; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .payment-info {{ background-color: #e8f4fd; padding: 15px; border-left: 4px solid #3b82f6; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{org_name}</h1>
            <p>Invoice {invoice.invoice_number}</p>
        </div>

        <div class="content">
            <p>Dear {invoice.contact_name},</p>

            <p>Please find attached invoice {invoice.invoice_number}. A summary is provided below:</p>

            <div class="invoice-details">
                <div class="detail-row">
                    <span class="label">Invoice Number:</span>
                    <span>{invoice.invoice_number}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Invoice Date:</span>
                    <span>{invoice.invoice_date.strftime('%B %d, %Y')}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Due Date:</span>
                    <span>{invoice.due_date.strftime('%B %d, %Y')}</span>
                </div>
"""

        if invoice.property_name:
            html_body += f"""
                <div class="detail-row">
                    <span class="label">Property:</span>
                    <span>{invoice.property_name}</span>
                </div>
"""

        html_body += f"""
            </div>

            <div class="amount">
                Amount Due: {invoice.currency} {invoice.total_amount:.2f}
            </div>
"""

        if custom_message:
            html_body += f"<p>{custom_message}</p>"

        if invoice.notes:
            html_body += f"<p><strong>Notes:</strong> {invoice.notes}</p>"

        if org.get("payment_info"):
            html_body += f"""
            <div class="payment-info">
                <strong>Payment Information:</strong><br>
                {org.get('payment_info').replace(chr(10), '<br>')}
            </div>
"""

        html_body += f"""
            <p>Please make payment by <strong>{invoice.due_date.strftime('%B %d, %Y')}</strong>.</p>

            <p>If you have any questions, please don't hesitate to contact us.</p>

            <p>Best regards,<br>
            {org_name}</p>
        </div>

        <div class="footer">
            <p>{org.get('address', '')}</p>
            <p>{org.get('email', '')} | {org.get('phone', '')}</p>
            <p>{org.get('website', '')}</p>
        </div>
    </div>
</body>
</html>
"""

        # Prepare attachment
        attachment = {
            "filename": f"{invoice.invoice_number}.pdf",
            "content": pdf_bytes,
            "content_type": "application/pdf"
        }

        # Send email
        result = await email_service.send_email(
            to=invoice.contact_email,
            subject=subject,
            body=body,
            html_body=html_body,
            from_email=org.get("email"),
            from_name=org_name,
            attachments=[attachment]
        )

        # If successful, update invoice status to SENT
        if result.get("success"):
            await self.collection.update_one(
                {"id": invoice_id, "organization_id": organization_id},
                {
                    "$set": {
                        "status": InvoiceStatus.SENT,
                        "sent_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Invoice {invoice_id} sent successfully to {invoice.contact_email}")

        return result
