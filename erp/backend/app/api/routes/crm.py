"""
CRM (Customer Relationship Management) Routes.

Handles customers, leads, opportunities, and contacts.
All data is organization-scoped.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
import pandas as pd
import io

from app.core.database import MongoDB
from app.models.crm import Customer, Lead, Opportunity, Contact, CustomerType
from app.schemas.crm import (
    CustomerCreate,
    CustomerUpdate,
    LeadCreate,
    LeadUpdate,
    OpportunityCreate,
    OpportunityUpdate,
    ContactCreate,
    ContactUpdate,
    ContactBulkImportRequest,
    ContactBulkImportResult,
    ContactImportRow,
    LeadToOpportunityConversion,
    LeadToCustomerConversion,
    OpportunityToCustomerConversion,
    ConversionResponse,
    MarkWonRequest,
)
from app.services.crm_conversion_service import get_crm_conversion_service
from apps.shared.dependencies import require_organization_access, OrganizationScoped

logger = logging.getLogger(__name__)
router = APIRouter()


# Customer endpoints
@router.post("/customers", response_model=Customer, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    scope: OrganizationScoped = Depends(),
):
    """Create a new customer."""
    db = MongoDB.get_database()

    # Create full Customer model with organization data
    customer = Customer(
        **customer_data.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub"),
    )

    await db.customers.insert_one(customer.model_dump())
    logger.info(f"Customer {customer.id} created in org {scope.org_id}")
    return customer


@router.get("/customers", response_model=List[Customer])
async def list_customers(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
):
    """List all customers in the organization."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}
    if search:
        query["$or"] = [
            {"company_name": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    cursor = db.customers.find(query).skip(skip).limit(limit).sort("created_at", -1)
    customers = await cursor.to_list(length=limit)
    return [Customer(**c) for c in customers]


@router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get customer by ID."""
    db = MongoDB.get_database()
    customer = await db.customers.find_one({"id": customer_id, "organization_id": org_id})

    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    return Customer(**customer)


@router.patch("/customers/{customer_id}", response_model=Customer)
async def update_customer(
    customer_id: str,
    update_data: CustomerUpdate,
    scope: OrganizationScoped = Depends(),
):
    """Update customer."""
    db = MongoDB.get_database()

    # Only include fields that were actually set
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    result = await db.customers.update_one(
        {"id": customer_id, "organization_id": scope.org_id},
        {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    customer = await db.customers.find_one({"id": customer_id})
    return Customer(**customer)


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete customer."""
    db = MongoDB.get_database()

    result = await db.customers.update_one(
        {"id": customer_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    return None


# Lead endpoints
@router.post("/leads", response_model=Lead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    scope: OrganizationScoped = Depends(),
):
    """Create a new lead."""
    db = MongoDB.get_database()

    # Create full Lead model with organization data
    lead = Lead(
        **lead_data.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub"),
    )

    await db.leads.insert_one(lead.model_dump())
    logger.info(f"Lead {lead.id} created in org {scope.org_id}")
    return lead


@router.get("/leads", response_model=List[Lead])
async def list_leads(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    source: Optional[str] = None,
    score_min: Optional[int] = None,
    score_max: Optional[int] = None,
):
    """List all leads in the organization."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search across name and email
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if status_filter:
        query["status"] = status_filter
    if source:
        query["source"] = source
    if score_min is not None:
        query.setdefault("score", {})["$gte"] = score_min
    if score_max is not None:
        query.setdefault("score", {})["$lte"] = score_max

    cursor = db.leads.find(query).skip(skip).limit(limit).sort("created_at", -1)
    leads = await cursor.to_list(length=limit)
    return [Lead(**l) for l in leads]


@router.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(
    lead_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get lead by ID."""
    db = MongoDB.get_database()
    lead = await db.leads.find_one({"id": lead_id, "organization_id": org_id})

    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    return Lead(**lead)


@router.patch("/leads/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: str,
    update_data: LeadUpdate,
    scope: OrganizationScoped = Depends(),
):
    """Update lead."""
    db = MongoDB.get_database()

    # Only include fields that were actually set
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    result = await db.leads.update_one(
        {"id": lead_id, "organization_id": scope.org_id},
        {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    lead = await db.leads.find_one({"id": lead_id})
    return Lead(**lead)


@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lead(
    lead_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete lead."""
    db = MongoDB.get_database()

    result = await db.leads.update_one(
        {"id": lead_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    return None


# Opportunity endpoints
@router.post("/opportunities", response_model=Opportunity, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    opp_data: OpportunityCreate,
    scope: OrganizationScoped = Depends(),
):
    """Create a new opportunity."""
    db = MongoDB.get_database()

    # Create full Opportunity model with organization data
    opportunity = Opportunity(
        **opp_data.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub"),
    )

    await db.opportunities.insert_one(opportunity.model_dump())
    logger.info(f"Opportunity {opportunity.id} created in org {scope.org_id}")
    return opportunity


@router.get("/opportunities", response_model=List[Opportunity])
async def list_opportunities(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    customer_id: Optional[str] = None,
    stage: Optional[str] = None,
    probability_min: Optional[int] = None,
    amount_min: Optional[float] = None,
):
    """List all opportunities in the organization."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if customer_id:
        query["customer_id"] = customer_id
    if stage:
        query["stage"] = stage
    if probability_min is not None:
        query.setdefault("probability", {})["$gte"] = probability_min
    if amount_min is not None:
        query.setdefault("amount", {})["$gte"] = amount_min

    cursor = db.opportunities.find(query).skip(skip).limit(limit).sort("created_at", -1)
    opps = await cursor.to_list(length=limit)
    return [Opportunity(**o) for o in opps]


@router.get("/opportunities/{opportunity_id}", response_model=Opportunity)
async def get_opportunity(
    opportunity_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get opportunity by ID."""
    db = MongoDB.get_database()
    opp = await db.opportunities.find_one({"id": opportunity_id, "organization_id": org_id})

    if not opp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

    return Opportunity(**opp)


@router.patch("/opportunities/{opportunity_id}", response_model=Opportunity)
async def update_opportunity(
    opportunity_id: str,
    update_data: OpportunityUpdate,
    scope: OrganizationScoped = Depends(),
):
    """Update opportunity."""
    db = MongoDB.get_database()

    # Only include fields that were actually set
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    result = await db.opportunities.update_one(
        {"id": opportunity_id, "organization_id": scope.org_id},
        {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

    opp = await db.opportunities.find_one({"id": opportunity_id})
    return Opportunity(**opp)


@router.delete("/opportunities/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_opportunity(
    opportunity_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete opportunity."""
    db = MongoDB.get_database()

    result = await db.opportunities.update_one(
        {"id": opportunity_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

    return None


# Contact endpoints
@router.post("/contacts", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    scope: OrganizationScoped = Depends(),
):
    """Create a new contact."""
    db = MongoDB.get_database()

    # Create full Contact model with organization data
    contact = Contact(
        **contact_data.model_dump(),
        organization_id=scope.org_id,
        created_by=scope.user.get("id") or scope.user.get("sub"),
    )

    await db.contacts.insert_one(contact.model_dump())
    return contact


@router.get("/contacts", response_model=List[Contact])
async def list_contacts(
    org_id: str = Depends(require_organization_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    customer_id: Optional[str] = None,
    is_primary: Optional[bool] = None,
):
    """List all contacts in the organization."""
    db = MongoDB.get_database()

    query = {"organization_id": org_id, "is_active": True}

    # Search
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
        ]

    # Filters
    if customer_id:
        query["customer_id"] = customer_id
    if is_primary is not None:
        query["is_primary"] = is_primary

    cursor = db.contacts.find(query).skip(skip).limit(limit).sort("created_at", -1)
    contacts = await cursor.to_list(length=limit)
    return [Contact(**c) for c in contacts]


@router.get("/contacts/{contact_id}", response_model=Contact)
async def get_contact(
    contact_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Get contact by ID."""
    db = MongoDB.get_database()
    contact = await db.contacts.find_one({"id": contact_id, "organization_id": org_id})

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    return Contact(**contact)


@router.patch("/contacts/{contact_id}", response_model=Contact)
async def update_contact(
    contact_id: str,
    update_data: ContactUpdate,
    scope: OrganizationScoped = Depends(),
):
    """Update contact."""
    db = MongoDB.get_database()

    # Only include fields that were actually set
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_by"] = scope.user.get("id") or scope.user.get("sub")

    result = await db.contacts.update_one(
        {"id": contact_id, "organization_id": scope.org_id},
        {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    contact = await db.contacts.find_one({"id": contact_id})
    return Contact(**contact)


@router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    org_id: str = Depends(require_organization_access),
):
    """Soft delete contact."""
    db = MongoDB.get_database()

    result = await db.contacts.update_one(
        {"id": contact_id, "organization_id": org_id},
        {"$set": {"is_active": False}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    return None


# Bulk Import Endpoints
@router.post("/contacts/bulk-import/file", response_model=ContactBulkImportResult)
async def bulk_import_contacts_from_file(
    file: UploadFile = File(...),
    customer_name: str = "Imported Contacts",
    skip_duplicates: bool = True,
    scope: OrganizationScoped = Depends(),
):
    """
    Bulk import contacts from Excel or CSV file.

    Accepts files with minimal data (even just phone numbers).
    Automatically creates or finds a customer to associate contacts with.

    Supported column names (case-insensitive):
    - phone, Phone Number, mobile, Mobile, cell
    - email, Email, E-mail
    - first_name, First Name, FirstName, given_name
    - last_name, Last Name, LastName, surname
    - company, Company, organization
    - job_title, Job Title, title, position
    - notes, Notes, comments

    Example minimal CSV:
    ```
    phone
    +233501234567
    +233509876543
    ```

    Example with more data:
    ```
    phone,first_name,last_name,company
    +233501234567,John,Doe,Acme Inc
    +233509876543,Jane,Smith,Tech Corp
    ```

    Returns:
        ContactBulkImportResult with statistics and created contact IDs
    """
    from .crm_bulk_import import parse_excel_file, bulk_import_contacts

    try:
        # Read file content
        file_content = await file.read()

        # Parse file
        contacts = await parse_excel_file(file_content, file.filename)

        if not contacts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid contacts found in file. Ensure at least one phone, mobile, or email is provided per row."
            )

        # Import contacts
        result = await bulk_import_contacts(
            contacts=contacts,
            organization_id=scope.org_id,
            user_id=scope.user.get("id") or scope.user.get("sub"),
            customer_name=customer_name,
            skip_duplicates=skip_duplicates
        )

        logger.info(
            f"Bulk import from file '{file.filename}' completed: "
            f"{result.successful} successful, {result.failed} failed, {result.skipped} skipped"
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Bulk import failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk import failed: {str(e)}"
        )


@router.post("/contacts/bulk-import/json", response_model=ContactBulkImportResult)
async def bulk_import_contacts_from_json(
    import_request: ContactBulkImportRequest,
    scope: OrganizationScoped = Depends(),
):
    """
    Bulk import contacts from JSON data.

    Alternative to file upload - accepts JSON array of contacts.
    Useful for frontend-parsed data or API integrations.

    Example request:
    ```json
    {
      "contacts": [
        {"phone": "+233501234567"},
        {"phone": "+233509876543", "first_name": "John", "last_name": "Doe"}
      ],
      "customer_name": "Imported Contacts",
      "skip_duplicates": true
    }
    ```

    Returns:
        ContactBulkImportResult with statistics and created contact IDs
    """
    from .crm_bulk_import import bulk_import_contacts

    try:
        if not import_request.contacts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No contacts provided"
            )

        # Import contacts
        result = await bulk_import_contacts(
            contacts=import_request.contacts,
            organization_id=scope.org_id,
            user_id=scope.user.get("id") or scope.user.get("sub"),
            customer_name=import_request.customer_name,
            skip_duplicates=import_request.skip_duplicates
        )

        logger.info(
            f"Bulk import from JSON completed: "
            f"{result.successful} successful, {result.failed} failed, {result.skipped} skipped"
        )

        return result

    except Exception as e:
        logger.error(f"Bulk import failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk import failed: {str(e)}"
        )


@router.get("/contacts/bulk-import/template")
async def download_import_template():
    """
    Download a template Excel file for bulk contact import.

    Returns a simple Excel file with example data showing the supported columns.
    """
    # Create sample DataFrame
    template_data = {
        'phone': ['+233501234567', '+233509876543', '+1234567890'],
        'mobile': ['', '', ''],
        'email': ['john@example.com', '', ''],
        'first_name': ['John', 'Jane', ''],
        'last_name': ['Doe', 'Smith', ''],
        'company': ['Acme Inc', '', ''],
        'job_title': ['Manager', '', ''],
        'notes': ['VIP client', '', 'From networking event']
    }

    df = pd.DataFrame(template_data)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Contacts', index=False)

    output.seek(0)

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': 'attachment; filename=contact_import_template.xlsx'
        }
    )


# CRM Conversion Endpoints

@router.post("/leads/{lead_id}/convert-to-opportunity", response_model=ConversionResponse)
async def convert_lead_to_opportunity(
    lead_id: str,
    conversion_data: LeadToOpportunityConversion,
    scope: OrganizationScoped = Depends(),
):
    """
    Convert a lead to an opportunity.

    Workflow:
    1. Validate lead exists and can be converted
    2. Create opportunity with lead data
    3. Link opportunity to lead
    4. Update lead status to CONVERTED (unless keep_lead_active=true)
    5. Log system activity

    Args:
        lead_id: Lead ID to convert
        conversion_data: Conversion request data (opportunity details)
        scope: Organization and user context

    Returns:
        ConversionResponse with created opportunity details

    Example request:
    ```json
    {
      "opportunity_name": "Enterprise Software Deal",
      "amount": 50000.00,
      "probability": 40,
      "stage": "QUALIFICATION",
      "expected_close_date": "2025-12-31T00:00:00",
      "description": "High-value enterprise deal",
      "next_step": "Schedule demo with decision makers",
      "keep_lead_active": false
    }
    ```
    """
    service = get_crm_conversion_service()

    result = await service.convert_lead_to_opportunity(
        lead_id=lead_id,
        conversion_data=conversion_data,
        organization_id=scope.org_id,
        user_id=scope.user.get("id") or scope.user.get("sub")
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    return result


@router.post("/leads/{lead_id}/convert-to-customer", response_model=ConversionResponse)
async def convert_lead_to_customer(
    lead_id: str,
    conversion_data: LeadToCustomerConversion,
    scope: OrganizationScoped = Depends(),
):
    """
    Convert a lead directly to a customer.

    Use this when a lead becomes a customer without going through the opportunity stage.
    Automatically creates customer record and optionally creates a contact.

    Workflow:
    1. Validate lead exists
    2. Create customer from lead data
    3. Optionally create contact record
    4. Update lead status to CONVERTED
    5. Link lead to customer

    Args:
        lead_id: Lead ID to convert
        conversion_data: Conversion request data (customer details)
        scope: Organization and user context

    Returns:
        ConversionResponse with created customer and contact details

    Example request:
    ```json
    {
      "customer_type": "BUSINESS",
      "company_name": "Acme Corporation",
      "create_contact": true,
      "account_manager": "user_123",
      "tags": ["enterprise", "high-value"]
    }
    ```
    """
    service = get_crm_conversion_service()

    result = await service.convert_lead_to_customer(
        lead_id=lead_id,
        conversion_data=conversion_data,
        organization_id=scope.org_id,
        user_id=scope.user.get("id") or scope.user.get("sub")
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    return result


@router.post("/opportunities/{opportunity_id}/convert-to-customer", response_model=ConversionResponse)
async def convert_opportunity_to_customer(
    opportunity_id: str,
    conversion_data: OpportunityToCustomerConversion,
    scope: OrganizationScoped = Depends(),
):
    """
    Convert a won opportunity to a customer with optional invoice creation.

    **IMPORTANT**: Opportunity must be marked as CLOSED_WON before conversion.

    This endpoint integrates with the financial system:
    - Creates or links customer record
    - Optionally creates invoice from opportunity amount
    - Automatically creates journal entries for the invoice (double-entry bookkeeping)
    - Updates customer lifetime value
    - Links opportunity to customer

    Workflow:
    1. Validate opportunity (must be CLOSED_WON)
    2. Create new customer or link existing customer
    3. Create invoice if requested (default: true)
    4. Automatically create journal entries:
       - DR Accounts Receivable
       - CR Revenue
       - CR Sales Tax Payable (if applicable)
    5. Update opportunity.customer_id
    6. Update customer.lifetime_value

    Args:
        opportunity_id: Opportunity ID to convert
        conversion_data: Conversion request data (customer and invoice details)
        scope: Organization and user context

    Returns:
        ConversionResponse with created customer, contact, and invoice details

    Example request (create new customer with invoice):
    ```json
    {
      "create_new_customer": true,
      "customer_type": "BUSINESS",
      "account_manager": "user_123",
      "create_invoice": true,
      "invoice_due_days": 30,
      "invoice_notes": "Payment terms: Net 30"
    }
    ```

    Example request (link to existing customer):
    ```json
    {
      "create_new_customer": false,
      "existing_customer_id": "customer_456",
      "create_invoice": true,
      "invoice_due_days": 15,
      "invoice_notes": "Expedited payment requested"
    }
    ```
    """
    service = get_crm_conversion_service()

    result = await service.convert_opportunity_to_customer(
        opportunity_id=opportunity_id,
        conversion_data=conversion_data,
        organization_id=scope.org_id,
        user_id=scope.user.get("id") or scope.user.get("sub")
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    logger.info(
        f"Opportunity {opportunity_id} converted to customer {result.customer_id} "
        f"in org {scope.org_id} by user {scope.user.get('id')}"
    )

    return result


@router.post("/opportunities/{opportunity_id}/mark-won", response_model=ConversionResponse)
async def mark_opportunity_won(
    opportunity_id: str,
    mark_won_data: MarkWonRequest,
    scope: OrganizationScoped = Depends(),
):
    """
    Mark an opportunity as CLOSED_WON and automatically trigger conversion workflow.

    **Streamlined workflow that combines multiple actions:**
    1. Updates opportunity stage to CLOSED_WON
    2. Sets closed_date and stage_entered_date
    3. Optionally creates customer from opportunity
    4. Optionally creates invoice with automatic journal entries
    5. Updates customer lifetime value
    6. Logs system activity for audit trail

    **This endpoint integrates with:**
    - CRM (opportunity management)
    - Finance (invoice + journal entries)
    - Customer management (customer creation/linking)
    - Activity tracking (automatic activity logging)

    **Workflow:**
    1. Validate opportunity exists and is not already won
    2. Mark opportunity as CLOSED_WON
    3. If create_customer=True: Create new customer or link to existing
    4. If create_invoice=True: Create invoice with automatic journal entries
       - DR Accounts Receivable
       - CR Revenue
       - CR Sales Tax Payable (if applicable)
    5. Update customer lifetime value
    6. Log activity ("Opportunity Marked as Won")
    7. Update opportunity activity tracking fields

    Args:
        opportunity_id: Opportunity ID to mark as won
        mark_won_data: Mark won request data with customer and invoice options
        scope: Organization and user context

    Returns:
        ConversionResponse with created customer, contact, and invoice details

    Example request (full automation):
    ```json
    {
      "create_customer": true,
      "customer_type": "BUSINESS",
      "account_manager": "user_123",
      "create_invoice": true,
      "invoice_due_days": 30,
      "invoice_notes": "Payment terms: Net 30",
      "create_project": false
    }
    ```

    Example request (mark won only, no automation):
    ```json
    {
      "create_customer": false,
      "create_invoice": false
    }
    ```

    Example request (link to existing customer):
    ```json
    {
      "create_customer": false,
      "existing_customer_id": "customer_456",
      "create_invoice": true,
      "invoice_due_days": 15
    }
    ```
    """
    service = get_crm_conversion_service()

    result = await service.mark_opportunity_won(
        opportunity_id=opportunity_id,
        mark_won_data=mark_won_data,
        organization_id=scope.org_id,
        user_id=scope.user.get("id") or scope.user.get("sub")
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message
        )

    logger.info(
        f"Opportunity {opportunity_id} marked as won in org {scope.org_id} by user {scope.user.get('id')}"
    )

    return result
