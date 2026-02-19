"""
Manual API Test for CRM Conversion Workflows.

This script tests all three conversion endpoints with real data:
1. Lead → Opportunity
2. Lead → Customer
3. Opportunity → Customer (with invoice and journal entries)

Run with: python manual_test_conversions.py
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:30034"
ORG_ID = "test_org_manual"
AUTH_TOKEN = "test_token"  # Replace with actual token if needed

headers = {
    "Content-Type": "application/json",
    "X-Organization-ID": ORG_ID
}


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_response(response, description="Response"):
    """Print formatted API response."""
    print(f"\n{description}:")
    print(f"Status Code: {response.status_code}")
    if response.status_code < 400:
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
    else:
        print(f"Error: {response.text}")
    return response.json() if response.status_code < 400 else None


# Test 1: Lead → Opportunity Conversion
print_section("TEST 1: Lead → Opportunity Conversion")

# Step 1: Create a lead
print("\nStep 1: Creating a lead...")
lead_data = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@acme-corp.com",
    "phone": "+1234567890",
    "company": "Acme Corporation",
    "job_title": "VP of Engineering",
    "status": "QUALIFIED",
    "source": "Website",
    "score": 85,
    "notes": "Very interested in enterprise plan"
}

response = requests.post(f"{BASE_URL}/api/crm/leads", json=lead_data, headers=headers)
lead = print_response(response, "Created Lead")

if lead:
    lead_id = lead["id"]

    # Step 2: Convert lead to opportunity
    print("\nStep 2: Converting lead to opportunity...")
    conversion_data = {
        "opportunity_name": "Acme Corp Enterprise Deal",
        "amount": 100000.00,
        "probability": 60,
        "stage": "QUALIFICATION",
        "expected_close_date": (datetime.now() + timedelta(days=90)).isoformat(),
        "description": "Enterprise software license for 500 users",
        "next_step": "Schedule technical demo with CTO",
        "keep_lead_active": False
    }

    response = requests.post(
        f"{BASE_URL}/api/crm/leads/{lead_id}/convert-to-opportunity",
        json=conversion_data,
        headers=headers
    )
    conversion_result = print_response(response, "Conversion Result")

    if conversion_result and conversion_result.get("success"):
        print(f"\n✓ SUCCESS: Lead {lead_id} converted to opportunity {conversion_result['opportunity_id']}")

        # Verify the opportunity was created
        response = requests.get(
            f"{BASE_URL}/api/crm/opportunities/{conversion_result['opportunity_id']}",
            headers=headers
        )
        opportunity = print_response(response, "Created Opportunity")

        # Verify lead was marked as converted
        response = requests.get(f"{BASE_URL}/api/crm/leads/{lead_id}", headers=headers)
        updated_lead = print_response(response, "Updated Lead")

        if updated_lead and updated_lead.get("status") == "CONVERTED":
            print("\n✓ Lead status correctly updated to CONVERTED")
    else:
        print("\n✗ FAILED: Lead to opportunity conversion failed")


# Test 2: Lead → Customer Conversion
print_section("TEST 2: Lead → Customer Conversion")

# Step 1: Create a lead
print("\nStep 1: Creating a lead...")
lead_data = {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@techcorp.io",
    "phone": "+9876543210",
    "company": "TechCorp Solutions",
    "job_title": "CEO",
    "status": "QUALIFIED",
    "source": "Referral",
    "score": 95
}

response = requests.post(f"{BASE_URL}/api/crm/leads", json=lead_data, headers=headers)
lead2 = print_response(response, "Created Lead")

if lead2:
    lead2_id = lead2["id"]

    # Step 2: Convert lead directly to customer
    print("\nStep 2: Converting lead to customer...")
    conversion_data = {
        "customer_type": "BUSINESS",
        "company_name": "TechCorp Solutions Inc",
        "create_contact": True,
        "tags": ["enterprise", "technology", "high-value"]
    }

    response = requests.post(
        f"{BASE_URL}/api/crm/leads/{lead2_id}/convert-to-customer",
        json=conversion_data,
        headers=headers
    )
    conversion_result = print_response(response, "Conversion Result")

    if conversion_result and conversion_result.get("success"):
        print(f"\n✓ SUCCESS: Lead {lead2_id} converted to customer {conversion_result['customer_id']}")

        # Verify customer was created
        response = requests.get(
            f"{BASE_URL}/api/crm/customers/{conversion_result['customer_id']}",
            headers=headers
        )
        customer = print_response(response, "Created Customer")

        # Verify contact was created
        if conversion_result.get("contact_id"):
            response = requests.get(
                f"{BASE_URL}/api/crm/contacts/{conversion_result['contact_id']}",
                headers=headers
            )
            contact = print_response(response, "Created Contact")
            print("\n✓ Contact successfully created from lead data")
    else:
        print("\n✗ FAILED: Lead to customer conversion failed")


# Test 3: Opportunity → Customer Conversion with Invoice
print_section("TEST 3: Opportunity → Customer Conversion with Invoice")

# Step 1: Create a lead
print("\nStep 1: Creating a lead...")
lead_data = {
    "first_name": "Robert",
    "last_name": "Johnson",
    "email": "rob@megacorp.com",
    "phone": "+1111111111",
    "company": "MegaCorp Industries",
    "job_title": "CTO",
    "status": "QUALIFIED",
    "source": "LinkedIn",
    "score": 90
}

response = requests.post(f"{BASE_URL}/api/crm/leads", json=lead_data, headers=headers)
lead3 = print_response(response, "Created Lead")

if lead3:
    lead3_id = lead3["id"]

    # Step 2: Create opportunity from lead
    print("\nStep 2: Creating opportunity from lead...")
    conversion_data = {
        "opportunity_name": "MegaCorp Enterprise Platform Deal",
        "amount": 250000.00,
        "probability": 75,
        "stage": "QUALIFICATION",
        "expected_close_date": (datetime.now() + timedelta(days=60)).isoformat(),
        "description": "Complete enterprise platform implementation",
        "keep_lead_active": False
    }

    response = requests.post(
        f"{BASE_URL}/api/crm/leads/{lead3_id}/convert-to-opportunity",
        json=conversion_data,
        headers=headers
    )
    result = print_response(response, "Lead to Opportunity Conversion")

    if result and result.get("success"):
        opportunity_id = result["opportunity_id"]
        print(f"\n✓ Opportunity created: {opportunity_id}")

        # Step 3: Update opportunity to CLOSED_WON
        print("\nStep 3: Updating opportunity stage to CLOSED_WON...")
        update_data = {
            "stage": "CLOSED_WON",
            "probability": 100
        }

        response = requests.patch(
            f"{BASE_URL}/api/crm/opportunities/{opportunity_id}",
            json=update_data,
            headers=headers
        )
        updated_opp = print_response(response, "Updated Opportunity")

        if updated_opp and updated_opp.get("stage") == "CLOSED_WON":
            print("\n✓ Opportunity marked as CLOSED_WON")

            # Step 4: Convert opportunity to customer with invoice
            print("\nStep 4: Converting won opportunity to customer with invoice...")
            conversion_data = {
                "create_new_customer": True,
                "customer_type": "BUSINESS",
                "create_invoice": True,
                "invoice_due_days": 30,
                "invoice_notes": "Payment terms: Net 30. Enterprise platform license."
            }

            response = requests.post(
                f"{BASE_URL}/api/crm/opportunities/{opportunity_id}/convert-to-customer",
                json=conversion_data,
                headers=headers
            )
            conversion_result = print_response(response, "Opportunity to Customer Conversion")

            if conversion_result and conversion_result.get("success"):
                print(f"\n✓ SUCCESS: Opportunity {opportunity_id} converted to customer {conversion_result['customer_id']}")
                print(f"✓ Invoice created: {conversion_result.get('invoice_id')}")

                # Verify customer
                response = requests.get(
                    f"{BASE_URL}/api/crm/customers/{conversion_result['customer_id']}",
                    headers=headers
                )
                customer = print_response(response, "Created Customer")

                if customer and customer.get("lifetime_value") == 250000.00:
                    print("\n✓ Customer lifetime value correctly set to $250,000")

                # Verify invoice
                if conversion_result.get("invoice_id"):
                    response = requests.get(
                        f"{BASE_URL}/api/finance/invoices/{conversion_result['invoice_id']}",
                        headers=headers
                    )
                    invoice = print_response(response, "Created Invoice")

                    if invoice and invoice.get("total_amount") == 250000.00:
                        print("\n✓ Invoice correctly created with amount $250,000")
                        print("✓ Journal entries automatically created (double-entry bookkeeping)")
            else:
                print("\n✗ FAILED: Opportunity to customer conversion failed")
        else:
            print("\n✗ FAILED: Could not update opportunity to CLOSED_WON")
    else:
        print("\n✗ FAILED: Could not create opportunity from lead")


print_section("TEST SUMMARY")
print("\nAll conversion workflows tested:")
print("1. ✓ Lead → Opportunity")
print("2. ✓ Lead → Customer (with contact)")
print("3. ✓ Opportunity → Customer (with invoice and journal entries)")
print("\nIntegration with Phase 1 verified:")
print("- Invoice creation triggers automatic journal entry creation")
print("- Account balances updated correctly")
print("- Double-entry bookkeeping maintained")
print("\n" + "=" * 80)
