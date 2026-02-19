"""
CRM Bulk Import Helper Functions.

Handles parsing Excel/CSV files and bulk importing contacts.
"""

import logging
from typing import List, Dict, Any, Tuple
import pandas as pd
import io
from datetime import datetime

from app.core.database import MongoDB
from app.models.crm import Customer, Contact, CustomerType
from app.schemas.crm import ContactImportRow, ContactBulkImportResult

logger = logging.getLogger(__name__)


async def parse_excel_file(file_content: bytes, filename: str) -> List[ContactImportRow]:
    """
    Parse Excel or CSV file into list of ContactImportRow objects.

    Supports flexible column naming:
    - phone, Phone, phone_number, Phone Number, mobile, Mobile, cell
    - email, Email, e-mail, E-mail
    - first_name, First Name, firstname, FirstName, given_name
    - last_name, Last Name, lastname, LastName, surname, family_name
    - company, Company, organization, Organization
    - job_title, Job Title, title, Title, position
    - notes, Notes, comments, Comments

    Args:
        file_content: File bytes
        filename: Original filename (to detect file type)

    Returns:
        List of ContactImportRow objects

    Raises:
        ValueError: If file cannot be parsed
    """
    try:
        # Determine file type and read
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError(f"Unsupported file type: {filename}. Use .csv, .xlsx, or .xls")

        # Normalize column names (lowercase, replace spaces with underscores)
        df.columns = df.columns.str.lower().str.replace(' ', '_')

        # Map flexible column names to standard fields
        column_mapping = {
            # Phone variations
            'phone': 'phone',
            'phone_number': 'phone',
            'mobile': 'mobile',
            'mobile_number': 'mobile',
            'cell': 'mobile',
            'cell_phone': 'mobile',
            # Email variations
            'email': 'email',
            'e-mail': 'email',
            'email_address': 'email',
            # Name variations
            'first_name': 'first_name',
            'firstname': 'first_name',
            'given_name': 'first_name',
            'last_name': 'last_name',
            'lastname': 'last_name',
            'surname': 'last_name',
            'family_name': 'last_name',
            # Company variations
            'company': 'company',
            'company_name': 'company',
            'organization': 'company',
            # Job title variations
            'job_title': 'job_title',
            'title': 'job_title',
            'position': 'job_title',
            'role': 'job_title',
            # Notes variations
            'notes': 'notes',
            'comments': 'notes',
            'description': 'notes',
        }

        # Rename columns based on mapping
        rename_dict = {}
        for col in df.columns:
            if col in column_mapping:
                rename_dict[col] = column_mapping[col]

        df = df.rename(columns=rename_dict)

        # Replace NaN with None
        df = df.where(pd.notna(df), None)

        # Convert to list of ContactImportRow objects
        contacts = []
        for _, row in df.iterrows():
            contact_data = {
                'phone': row.get('phone'),
                'mobile': row.get('mobile'),
                'email': row.get('email'),
                'first_name': row.get('first_name'),
                'last_name': row.get('last_name'),
                'company': row.get('company'),
                'job_title': row.get('job_title'),
                'notes': row.get('notes'),
            }

            # Skip completely empty rows
            if all(v is None for v in contact_data.values()):
                continue

            # At least one field must be present (phone, mobile, or email)
            if not any([contact_data['phone'], contact_data['mobile'], contact_data['email']]):
                continue

            contacts.append(ContactImportRow(**contact_data))

        logger.info(f"Parsed {len(contacts)} valid contacts from {filename}")
        return contacts

    except Exception as e:
        logger.error(f"Failed to parse file {filename}: {str(e)}")
        raise ValueError(f"Failed to parse file: {str(e)}")


async def bulk_import_contacts(
    contacts: List[ContactImportRow],
    organization_id: str,
    user_id: str,
    customer_name: str = "Imported Contacts",
    skip_duplicates: bool = True
) -> ContactBulkImportResult:
    """
    Bulk import contacts into the CRM.

    Creates or finds a customer to associate contacts with.
    Can handle minimal data (just phone numbers).

    Args:
        contacts: List of contact data to import
        organization_id: Organization ID
        user_id: User ID performing the import
        customer_name: Name for the customer to create/find
        skip_duplicates: Skip contacts with duplicate phone numbers

    Returns:
        ContactBulkImportResult with import statistics
    """
    db = MongoDB.get_database()

    # Find or create customer
    customer = await db.customers.find_one({
        "organization_id": organization_id,
        "company_name": customer_name,
        "is_active": True
    })

    if not customer:
        # Create new customer
        customer_obj = Customer(
            organization_id=organization_id,
            created_by=user_id,
            customer_type=CustomerType.BUSINESS,
            company_name=customer_name,
            email=f"imported@{customer_name.lower().replace(' ', '')}.placeholder",  # Placeholder email
        )
        await db.customers.insert_one(customer_obj.model_dump())
        customer_id = customer_obj.id
        logger.info(f"Created new customer {customer_id} for imports: {customer_name}")
    else:
        customer_id = customer["id"]
        logger.info(f"Using existing customer {customer_id}: {customer_name}")

    # Track results
    successful = 0
    failed = 0
    skipped = 0
    errors = []
    created_contact_ids = []

    # Process each contact
    for idx, contact_data in enumerate(contacts):
        try:
            # Extract phone (use mobile if phone not provided)
            phone = contact_data.phone or contact_data.mobile

            # Check for duplicates if requested
            if skip_duplicates and phone:
                existing = await db.contacts.find_one({
                    "organization_id": organization_id,
                    "$or": [
                        {"phone": phone},
                        {"mobile": phone},
                    ],
                    "is_active": True
                })
                if existing:
                    skipped += 1
                    logger.debug(f"Skipped duplicate contact with phone {phone}")
                    continue

            # Create contact with minimal required data
            # Use placeholders for required fields if not provided
            first_name = contact_data.first_name or "Contact"
            last_name = contact_data.last_name or f"#{idx + 1}"
            email = contact_data.email or f"contact{idx + 1}@placeholder.local"

            contact_obj = Contact(
                organization_id=organization_id,
                created_by=user_id,
                customer_id=customer_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=contact_data.phone,
                mobile=contact_data.mobile,
                job_title=contact_data.job_title,
                notes=contact_data.notes or f"Imported from bulk upload. Company: {contact_data.company or 'N/A'}",
                is_primary=False,
            )

            await db.contacts.insert_one(contact_obj.model_dump())
            created_contact_ids.append(contact_obj.id)
            successful += 1
            logger.debug(f"Imported contact: {first_name} {last_name}")

        except Exception as e:
            failed += 1
            error_msg = f"Row {idx + 1}: {str(e)}"
            errors.append({"row": idx + 1, "error": error_msg})
            logger.error(f"Failed to import contact row {idx + 1}: {str(e)}")

    result = ContactBulkImportResult(
        total_rows=len(contacts),
        successful=successful,
        failed=failed,
        skipped=skipped,
        customer_id=customer_id,
        errors=errors,
        created_contact_ids=created_contact_ids,
    )

    logger.info(
        f"Bulk import completed: {successful} successful, {failed} failed, {skipped} skipped"
    )

    return result
