"""
CRM Conversion Service.

Handles conversion workflows between CRM entities:
- Lead → Opportunity
- Lead → Customer
- Opportunity → Customer (with invoice creation)
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from bson import ObjectId

from app.core.database import MongoDB
from app.models.crm import (
    Lead,
    Opportunity,
    Customer,
    Contact,
    LeadStatus,
    OpportunityStage,
    CustomerType
)
from app.models.finance import Invoice, InvoiceStatus
from app.schemas.crm import (
    LeadToOpportunityConversion,
    LeadToCustomerConversion,
    OpportunityToCustomerConversion,
    ConversionResponse,
    MarkWonRequest
)

logger = logging.getLogger(__name__)


class CRMConversionService:
    """
    CRM entity conversion service.

    Handles all conversion workflows with proper data transfer,
    status updates, and system activity logging.
    """

    def __init__(self):
        self.db = MongoDB.get_database()

    async def convert_lead_to_opportunity(
        self,
        lead_id: str,
        conversion_data: LeadToOpportunityConversion,
        organization_id: str,
        user_id: str
    ) -> ConversionResponse:
        """
        Convert a lead to an opportunity.

        Workflow:
        1. Validate lead exists and can be converted
        2. Create opportunity with lead data
        3. Link opportunity to lead
        4. Update lead status to CONVERTED (unless keep_lead_active)
        5. Log system activity

        Args:
            lead_id: Lead ID to convert
            conversion_data: Conversion request data
            organization_id: Organization ID
            user_id: User performing conversion

        Returns:
            ConversionResponse with created opportunity details
        """
        # Get lead
        lead = await self.db.leads.find_one({
            "id": lead_id,
            "organization_id": organization_id,
            "is_active": True
        })

        if not lead:
            return ConversionResponse(
                success=False,
                message=f"Lead {lead_id} not found",
                lead_id=lead_id
            )

        # Check if already converted
        if lead.get("status") == LeadStatus.CONVERTED.value and not conversion_data.keep_lead_active:
            return ConversionResponse(
                success=False,
                message=f"Lead {lead_id} is already converted",
                lead_id=lead_id
            )

        # Create opportunity
        opportunity = Opportunity(
            organization_id=organization_id,
            name=conversion_data.opportunity_name,
            lead_id=lead_id,
            customer_id=None,  # No customer yet
            amount=conversion_data.amount,
            stage=conversion_data.stage,
            probability=conversion_data.probability,
            expected_close_date=conversion_data.expected_close_date,
            description=conversion_data.description or f"Converted from lead: {lead.get('first_name')} {lead.get('last_name')}",
            competitors=conversion_data.competitors,
            next_step=conversion_data.next_step,
            assigned_to=lead.get("assigned_to") or user_id,
            created_by=user_id
        )

        # Convert to dict for MongoDB
        opp_dict = opportunity.model_dump()

        # Convert date fields to datetime for MongoDB
        for key, value in opp_dict.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                opp_dict[key] = datetime.combine(value, datetime.min.time())

        await self.db.opportunities.insert_one(opp_dict)

        # Update lead
        update_data = {
            "updated_at": datetime.utcnow(),
            "updated_by": user_id
        }

        if not conversion_data.keep_lead_active:
            update_data["status"] = LeadStatus.CONVERTED.value
            update_data["converted_at"] = datetime.utcnow()

        await self.db.leads.update_one(
            {"id": lead_id, "organization_id": organization_id},
            {"$set": update_data}
        )

        logger.info(
            f"Converted lead {lead_id} to opportunity {opportunity.id} in org {organization_id}"
        )

        return ConversionResponse(
            success=True,
            message=f"Lead converted to opportunity: {conversion_data.opportunity_name}",
            lead_id=lead_id,
            opportunity_id=opportunity.id
        )

    async def convert_lead_to_customer(
        self,
        lead_id: str,
        conversion_data: LeadToCustomerConversion,
        organization_id: str,
        user_id: str
    ) -> ConversionResponse:
        """
        Convert a lead directly to a customer.

        Workflow:
        1. Validate lead exists
        2. Create customer from lead data
        3. Optionally create contact record
        4. Update lead status to CONVERTED
        5. Link lead to customer

        Args:
            lead_id: Lead ID to convert
            conversion_data: Conversion request data
            organization_id: Organization ID
            user_id: User performing conversion

        Returns:
            ConversionResponse with created customer details
        """
        # Get lead
        lead = await self.db.leads.find_one({
            "id": lead_id,
            "organization_id": organization_id,
            "is_active": True
        })

        if not lead:
            return ConversionResponse(
                success=False,
                message=f"Lead {lead_id} not found",
                lead_id=lead_id
            )

        # Create customer from lead data
        customer = Customer(
            organization_id=organization_id,
            customer_type=conversion_data.customer_type,
            first_name=lead.get("first_name") if conversion_data.customer_type == CustomerType.INDIVIDUAL else None,
            last_name=lead.get("last_name") if conversion_data.customer_type == CustomerType.INDIVIDUAL else None,
            company_name=conversion_data.company_name or lead.get("company"),
            email=lead.get("email"),
            phone=lead.get("phone"),
            account_manager=conversion_data.account_manager or lead.get("assigned_to"),
            tags=conversion_data.tags,
            customer_since=datetime.utcnow(),
            lifetime_value=0.0,
            created_by=user_id
        )

        customer_dict = customer.model_dump()
        await self.db.customers.insert_one(customer_dict)

        # Create contact if requested
        contact_id = None
        if conversion_data.create_contact:
            contact = Contact(
                organization_id=organization_id,
                customer_id=customer.id,
                first_name=lead.get("first_name"),
                last_name=lead.get("last_name"),
                email=lead.get("email"),
                phone=lead.get("phone"),
                job_title=lead.get("job_title"),
                is_primary=True,
                notes=f"Converted from lead on {datetime.utcnow().date()}",
                created_by=user_id
            )

            contact_dict = contact.model_dump()
            await self.db.contacts.insert_one(contact_dict)
            contact_id = contact.id

        # Update lead
        await self.db.leads.update_one(
            {"id": lead_id, "organization_id": organization_id},
            {
                "$set": {
                    "status": LeadStatus.CONVERTED.value,
                    "converted_at": datetime.utcnow(),
                    "converted_to_customer_id": customer.id,
                    "updated_at": datetime.utcnow(),
                    "updated_by": user_id
                }
            }
        )

        logger.info(
            f"Converted lead {lead_id} to customer {customer.id} in org {organization_id}"
        )

        return ConversionResponse(
            success=True,
            message=f"Lead converted to customer: {customer.company_name or f'{customer.first_name} {customer.last_name}'}",
            lead_id=lead_id,
            customer_id=customer.id,
            contact_id=contact_id
        )

    async def convert_opportunity_to_customer(
        self,
        opportunity_id: str,
        conversion_data: OpportunityToCustomerConversion,
        organization_id: str,
        user_id: str
    ) -> ConversionResponse:
        """
        Convert a won opportunity to a customer with optional invoice creation.

        Workflow:
        1. Validate opportunity (should be CLOSED_WON)
        2. Create or link customer
        3. Create invoice if requested (uses journal entry service)
        4. Create project if requested
        5. Update opportunity.customer_id
        6. Update customer.lifetime_value

        Args:
            opportunity_id: Opportunity ID to convert
            conversion_data: Conversion request data
            organization_id: Organization ID
            user_id: User performing conversion

        Returns:
            ConversionResponse with created entities
        """
        # Get opportunity
        opportunity = await self.db.opportunities.find_one({
            "id": opportunity_id,
            "organization_id": organization_id,
            "is_active": True
        })

        if not opportunity:
            return ConversionResponse(
                success=False,
                message=f"Opportunity {opportunity_id} not found",
                opportunity_id=opportunity_id
            )

        # Validate opportunity stage
        if opportunity.get("stage") != OpportunityStage.CLOSED_WON.value:
            return ConversionResponse(
                success=False,
                message=f"Opportunity must be marked as CLOSED_WON before conversion. Current stage: {opportunity.get('stage')}",
                opportunity_id=opportunity_id
            )

        customer_id = None
        contact_id = None

        # Create new customer or use existing
        if conversion_data.create_new_customer:
            # Get linked lead if exists
            lead = None
            if opportunity.get("lead_id"):
                lead = await self.db.leads.find_one({"id": opportunity["lead_id"]})

            # Create customer
            # Reason: Generate placeholder email if no lead exists to satisfy Customer model validation
            placeholder_email = f"customer-{opportunity.get('id')}@example.com"
            customer = Customer(
                organization_id=organization_id,
                customer_type=conversion_data.customer_type,
                first_name=lead.get("first_name") if lead and conversion_data.customer_type == CustomerType.INDIVIDUAL else None,
                last_name=lead.get("last_name") if lead and conversion_data.customer_type == CustomerType.INDIVIDUAL else None,
                company_name=lead.get("company") if lead else opportunity.get("name"),
                email=lead.get("email") if lead else placeholder_email,
                phone=lead.get("phone") if lead else None,
                account_manager=conversion_data.account_manager or opportunity.get("assigned_to"),
                customer_since=datetime.utcnow(),
                lifetime_value=opportunity.get("amount", 0.0),
                created_by=user_id
            )

            customer_dict = customer.model_dump()
            await self.db.customers.insert_one(customer_dict)
            customer_id = customer.id

            # Create contact if we have lead data
            if lead:
                contact = Contact(
                    organization_id=organization_id,
                    customer_id=customer.id,
                    first_name=lead.get("first_name"),
                    last_name=lead.get("last_name"),
                    email=lead.get("email"),
                    phone=lead.get("phone"),
                    job_title=lead.get("job_title"),
                    is_primary=True,
                    notes=f"Converted from opportunity {opportunity.get('name')}",
                    created_by=user_id
                )

                contact_dict = contact.model_dump()
                await self.db.contacts.insert_one(contact_dict)
                contact_id = contact.id

        else:
            # Use existing customer
            customer_id = conversion_data.existing_customer_id

            # Update customer lifetime value
            customer = await self.db.customers.find_one({"id": customer_id})
            if customer:
                new_ltv = customer.get("lifetime_value", 0.0) + opportunity.get("amount", 0.0)
                await self.db.customers.update_one(
                    {"id": customer_id},
                    {"$set": {"lifetime_value": new_ltv, "updated_at": datetime.utcnow()}}
                )

        # Create invoice if requested
        invoice_id = None
        if conversion_data.create_invoice and customer_id:
            # Generate invoice number
            invoice_count = await self.db.invoices.count_documents({"organization_id": organization_id})
            invoice_number = f"INV-{invoice_count + 1:05d}"

            invoice = Invoice(
                organization_id=organization_id,
                invoice_number=invoice_number,
                customer_id=customer_id,
                invoice_date=date.today(),
                due_date=date.today() + timedelta(days=conversion_data.invoice_due_days),
                status=InvoiceStatus.DRAFT,
                subtotal=opportunity.get("amount", 0.0),
                tax_amount=0.0,  # Can be enhanced to calculate tax
                total_amount=opportunity.get("amount", 0.0),
                amount_paid=0.0,
                balance_due=opportunity.get("amount", 0.0),
                currency="USD",
                customer_notes=conversion_data.invoice_notes or f"Invoice for: {opportunity.get('name')}",
                line_items=[],
                created_by=user_id
            )

            invoice_dict = invoice.model_dump()

            # Convert date fields
            for key, value in invoice_dict.items():
                if isinstance(value, date) and not isinstance(value, datetime):
                    invoice_dict[key] = datetime.combine(value, datetime.min.time())

            await self.db.invoices.insert_one(invoice_dict)
            invoice_id = invoice.id

            # Create journal entries for invoice
            try:
                from app.services.journal_entry_service import get_journal_entry_service
                journal_service = get_journal_entry_service()
                await journal_service.create_invoice_entries(invoice_id, organization_id)
                logger.info(f"Created journal entries for invoice {invoice_id}")
            except Exception as e:
                logger.error(f"Failed to create journal entries for invoice {invoice_id}: {e}")

        # Update opportunity
        await self.db.opportunities.update_one(
            {"id": opportunity_id, "organization_id": organization_id},
            {
                "$set": {
                    "customer_id": customer_id,
                    "updated_at": datetime.utcnow(),
                    "updated_by": user_id
                }
            }
        )

        logger.info(
            f"Converted opportunity {opportunity_id} to customer {customer_id} "
            f"with invoice {invoice_id} in org {organization_id}"
        )

        return ConversionResponse(
            success=True,
            message=f"Opportunity converted successfully. Customer created" + (f", invoice {invoice_number} created" if invoice_id else ""),
            opportunity_id=opportunity_id,
            customer_id=customer_id,
            contact_id=contact_id,
            invoice_id=invoice_id
        )

    async def mark_opportunity_won(
        self,
        opportunity_id: str,
        mark_won_data: MarkWonRequest,
        organization_id: str,
        user_id: str
    ) -> ConversionResponse:
        """
        Mark opportunity as won and automatically trigger conversion workflow.

        This is a streamlined endpoint that combines:
        1. Updating opportunity stage to CLOSED_WON
        2. Setting closed_date
        3. Automatically triggering customer conversion (if requested)
        4. Creating invoice (if requested)
        5. Creating journal entries
        6. Updating customer lifetime value
        7. Logging system activity

        Workflow:
        1. Validate opportunity exists
        2. Update opportunity to CLOSED_WON status
        3. Set closed_date and stage_entered_date
        4. Trigger conversion to customer (if create_customer=True)
        5. Create invoice with journal entries (if create_invoice=True)
        6. Log activity

        Args:
            opportunity_id: Opportunity ID to mark as won
            mark_won_data: Mark won request data
            organization_id: Organization ID
            user_id: User performing the action

        Returns:
            ConversionResponse with created entities
        """
        # Get opportunity
        opportunity = await self.db.opportunities.find_one({
            "id": opportunity_id,
            "organization_id": organization_id,
            "is_active": True
        })

        if not opportunity:
            return ConversionResponse(
                success=False,
                message=f"Opportunity {opportunity_id} not found",
                opportunity_id=opportunity_id
            )

        # Check if already won
        if opportunity.get("stage") == OpportunityStage.CLOSED_WON.value:
            return ConversionResponse(
                success=False,
                message=f"Opportunity {opportunity_id} is already marked as CLOSED_WON",
                opportunity_id=opportunity_id
            )

        # Update opportunity to CLOSED_WON
        closed_date = mark_won_data.closed_date or datetime.utcnow()
        update_data = {
            "stage": OpportunityStage.CLOSED_WON.value,
            "closed_date": closed_date,
            "stage_entered_date": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "updated_by": user_id
        }

        await self.db.opportunities.update_one(
            {"id": opportunity_id, "organization_id": organization_id},
            {"$set": update_data}
        )

        logger.info(f"Marked opportunity {opportunity_id} as CLOSED_WON in org {organization_id}")

        # If customer creation/linking is requested, trigger conversion workflow
        customer_id = None
        contact_id = None
        invoice_id = None

        if mark_won_data.create_customer or mark_won_data.existing_customer_id:
            from app.schemas.crm import OpportunityToCustomerConversion

            # Build conversion data
            conversion_data = OpportunityToCustomerConversion(
                create_new_customer=mark_won_data.create_customer,
                existing_customer_id=mark_won_data.existing_customer_id,
                customer_type=mark_won_data.customer_type,
                account_manager=mark_won_data.account_manager,
                create_invoice=mark_won_data.create_invoice,
                invoice_due_days=mark_won_data.invoice_due_days,
                invoice_notes=mark_won_data.invoice_notes,
                create_project=mark_won_data.create_project,
                project_name=mark_won_data.project_name
            )

            # Convert to customer
            result = await self.convert_opportunity_to_customer(
                opportunity_id=opportunity_id,
                conversion_data=conversion_data,
                organization_id=organization_id,
                user_id=user_id
            )

            if result.success:
                customer_id = result.customer_id
                contact_id = result.contact_id
                invoice_id = result.invoice_id
                logger.info(f"Auto-converted opportunity {opportunity_id} to customer {customer_id}")

        # Log system activity
        # Reason: Track the mark-won action for audit trail
        from app.models.crm import Activity, ActivityType, ActivityEntityType

        activity = Activity(
            organization_id=organization_id,
            entity_type=ActivityEntityType.OPPORTUNITY,
            entity_id=opportunity_id,
            activity_type=ActivityType.NOTE,
            subject="Opportunity Marked as Won",
            description=f"Opportunity marked as CLOSED_WON on {closed_date.strftime('%Y-%m-%d')}" +
                       (f". Customer {customer_id} created." if customer_id else "") +
                       (f" Invoice created." if invoice_id else ""),
            performed_by=user_id,
            activity_date=datetime.utcnow(),
            created_by=user_id
        )

        await self.db.activities.insert_one(activity.model_dump())

        # Update opportunity activity tracking
        await self.db.opportunities.update_one(
            {"id": opportunity_id, "organization_id": organization_id},
            {
                "$set": {
                    "last_activity_id": activity.id,
                    "last_activity_date": datetime.utcnow(),
                },
                "$inc": {"activity_count": 1}
            }
        )

        return ConversionResponse(
            success=True,
            message=f"Opportunity marked as won successfully" +
                   (f". Customer created" if customer_id else "") +
                   (f", invoice created" if invoice_id else ""),
            opportunity_id=opportunity_id,
            customer_id=customer_id,
            contact_id=contact_id,
            invoice_id=invoice_id
        )


# Singleton instance
_crm_conversion_service = None


def get_crm_conversion_service() -> CRMConversionService:
    """Get CRM conversion service singleton."""
    global _crm_conversion_service
    if _crm_conversion_service is None:
        _crm_conversion_service = CRMConversionService()
    return _crm_conversion_service
