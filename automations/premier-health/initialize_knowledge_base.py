#!/usr/bin/env python3
"""
Initialize Premier Health RAG knowledge base with comprehensive documentation.
This script creates and indexes knowledge documents for the RAG system.
"""

import sys
import os
import asyncio

# Add paths for imports
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.helpdesk_rag_service import helpdesk_rag_service, KnowledgeDocument

# Premier Health Knowledge Base Documents
PREMIER_HEALTH_KNOWLEDGE = [
    KnowledgeDocument(
        id="ph_policy_001",
        title="Premier Health Insurance Coverage Overview",
        content="""
Premier Health Insurance provides comprehensive healthcare coverage for individuals and families in Ghana.

Coverage Includes:
- Inpatient care at network hospitals
- Outpatient consultations at clinics and medical centers
- Emergency medical services (24/7 coverage)
- Specialist consultations (cardiology, gynecology, pediatrics, etc.)
- Diagnostic services (laboratory tests, imaging, scans)
- Pharmacy benefits for prescribed medications
- Preventive care and health screenings
- Maternity and newborn care
- Dental services (basic coverage)
- Eye care and optical services

Geographic Coverage:
- Primary coverage: Greater Accra Region
- Extended network: Major cities across Ghana
- Emergency services: Nationwide

Network Size:
- 103+ healthcare providers in Greater Accra
- Major hospitals, clinics, pharmacies, and specialist centers
- Continuously expanding provider network

Claim Process:
- Present your Premier Health ID card at any network provider
- No upfront payment required for covered services
- Providers bill Premier Health directly
- For non-network emergencies, submit receipts within 30 days
""",
        category="insurance_policy",
        source="premier_health_handbook",
        tags=["coverage", "policy", "benefits", "insurance"],
        metadata={"version": "2025", "effective_date": "2025-01-01"}
    ),

    KnowledgeDocument(
        id="ph_providers_001",
        title="Premier Health Provider Network - Greater Accra",
        content="""
Premier Health Insurance has an extensive network of healthcare providers across Greater Accra Region.

Major Areas Covered:
- Accra Central: Multiple hospitals, clinics, and pharmacies
- East Legon: Premium healthcare facilities and specialist centers
- Madina: Community clinics and pharmacies
- Circle: Medical centers and diagnostic facilities
- Tema: Industrial area healthcare services
- Osu: Private clinics and specialist services
- Labone: Medical centers and hospitals
- Dansoman: Community healthcare facilities
- Spintex: Growing healthcare corridor
- Achimota: Hospital and clinic network

Types of Providers:
1. Hospitals: Major tertiary care centers with emergency services
2. Clinics: Outpatient care and primary health services
3. Pharmacies: Prescription medications and health products
4. Specialist Centers: Cardiology, gynecology, pediatrics, ophthalmology, etc.
5. Diagnostic Centers: Laboratory tests, imaging, X-rays, ultrasounds
6. Dental Clinics: Oral health and dental care
7. Optical Centers: Eye care and prescription glasses

How to Find a Provider:
- Call our 24/7 helpline
- Visit our website provider directory
- Use our mobile app location finder
- Ask our AI voice assistant for recommendations

All network providers are verified and meet Premier Health quality standards.
""",
        category="provider_network",
        source="provider_directory",
        tags=["providers", "network", "locations", "hospitals", "clinics"],
        metadata={"last_updated": "2025-01-15", "total_providers": 103}
    ),

    KnowledgeDocument(
        id="ph_emergency_001",
        title="Emergency Healthcare Services and Protocols",
        content="""
Premier Health Insurance provides 24/7 emergency healthcare coverage.

Emergency Numbers:
- Ghana National Ambulance: 193
- Premier Health Emergency Hotline: [Contact customer service]
- Police Emergency: 191
- Fire Service: 192

Emergency Coverage:
- Immediate care for life-threatening conditions
- Ambulance services (where available)
- Emergency room visits
- Emergency surgery
- Trauma care
- Cardiac emergencies
- Accident and injury care
- Poisoning and overdose treatment
- Severe allergic reactions
- Obstetric emergencies

What Qualifies as Emergency:
- Severe chest pain or difficulty breathing
- Uncontrolled bleeding
- Loss of consciousness
- Severe burns
- Suspected heart attack or stroke
- Major injuries from accidents
- Severe allergic reactions (anaphylaxis)
- Active labor and childbirth complications
- Poisoning or drug overdose
- Severe abdominal pain

Emergency Procedure:
1. Call 193 for ambulance (if needed)
2. Go to nearest network emergency facility
3. Present your Premier Health ID card
4. Emergency care will be provided immediately
5. No pre-authorization required for true emergencies

Non-Network Emergency Care:
- Coverage applies for genuine emergencies
- Keep all receipts and medical reports
- Submit claim within 30 days
- Claims department will review and process

Important: Always call 193 for life-threatening emergencies first, then notify Premier Health.
""",
        category="emergency_services",
        source="emergency_protocols",
        tags=["emergency", "urgent_care", "ambulance", "accident", "trauma"],
        metadata={"priority": "critical", "availability": "24/7"}
    ),

    KnowledgeDocument(
        id="ph_specialties_001",
        title="Medical Specialties and Specialist Services",
        content="""
Premier Health Insurance covers a wide range of medical specialties.

Available Specialties:

1. General Practice (GP)
   - Primary care physicians
   - Routine checkups and consultations
   - Common illness and injury treatment

2. Pediatrics
   - Child healthcare (newborn to 18 years)
   - Vaccinations and immunizations
   - Growth and development monitoring

3. Gynecology & Obstetrics
   - Women's health services
   - Prenatal and maternity care
   - Family planning
   - Gynecological procedures

4. Cardiology
   - Heart and cardiovascular health
   - ECG and cardiac testing
   - Hypertension management

5. Ophthalmology (Eye Care)
   - Vision testing and eye exams
   - Eye disease treatment
   - Prescription glasses (partial coverage)
   - Cataract surgery

6. Dermatology
   - Skin conditions and diseases
   - Acne treatment
   - Skin cancer screening

7. Ear, Nose, and Throat (ENT)
   - Ear infections and hearing problems
   - Sinus and nasal conditions
   - Throat disorders

8. Physiotherapy
   - Physical rehabilitation
   - Sports injury recovery
   - Pain management
   - Mobility improvement

9. Dentistry
   - Basic dental care
   - Tooth extraction
   - Fillings (covered services only)

10. Laboratory Services
    - Blood tests and analysis
    - Diagnostic testing
    - Health screenings

11. Radiology/Imaging
    - X-rays
    - Ultrasound
    - CT scans (with pre-authorization)
    - MRI (with pre-authorization)

Referral Process:
- See your GP first for initial consultation
- GP will provide referral to specialist if needed
- Some specialists require pre-authorization
- Emergency cases bypass referral requirement
""",
        category="medical_specialties",
        source="specialty_guide",
        tags=["specialties", "specialists", "doctors", "medical_services"],
        metadata={"total_specialties": 11}
    ),

    KnowledgeDocument(
        id="ph_claims_001",
        title="Claims Process and Reimbursement",
        content="""
Premier Health Insurance claims process is designed for ease and convenience.

Direct Billing (Preferred Method):
- Visit any network provider
- Present your Premier Health ID card
- Provider verifies coverage
- Services rendered
- Provider bills Premier Health directly
- No upfront payment from you

Out-of-Network Emergency Claims:
1. Pay for emergency services upfront
2. Collect all receipts and medical reports
3. Complete claim form (available on website/mobile app)
4. Submit within 30 days of service
5. Include: receipts, medical reports, discharge summary, prescriptions
6. Claims processed within 14-21 business days
7. Reimbursement via bank transfer or check

Required Documents for Claims:
- Completed claim form with signature
- Original receipts (itemized)
- Medical reports and diagnosis
- Prescription slips (for medications)
- Referral letter (if applicable)
- Discharge summary (for hospital admissions)
- Copy of Premier Health ID card
- Bank account details for reimbursement

Claim Submission Methods:
- Online portal: www.premierhealth.com.gh/claims
- Email: claims@premierhealth.com.gh
- Mobile app: Upload documents directly
- Physical submission: Visit any Premier Health office
- Mail: [Premier Health Claims Department Address]

Claim Processing Time:
- Complete claims: 14-21 business days
- Incomplete claims: 30-45 days (pending documentation)
- Emergency claims: Expedited processing (7-10 days)

Claim Denial Reasons:
- Services not covered under policy
- Missing or incomplete documentation
- Non-network provider (non-emergency)
- Pre-authorization not obtained (when required)
- Claim submitted after 30-day deadline
- Policy lapsed or suspended

Appeal Process:
- Submit appeal within 60 days of denial
- Provide additional supporting documents
- Review by claims committee
- Decision communicated within 30 days

Claim Status Check:
- Online portal
- Mobile app
- Call customer service: [Helpline number]
- Email inquiry: claims@premierhealth.com.gh
""",
        category="claims_reimbursement",
        source="claims_handbook",
        tags=["claims", "reimbursement", "billing", "payment"],
        metadata={"processing_time_days": "14-21", "deadline_days": 30}
    ),

    KnowledgeDocument(
        id="ph_pharmacy_001",
        title="Pharmacy Benefits and Medication Coverage",
        content="""
Premier Health Insurance includes comprehensive pharmacy benefits.

Medication Coverage:
- Prescription medications from network pharmacies
- Generic and brand-name drugs (based on formulary)
- Chronic disease medications (diabetes, hypertension, etc.)
- Acute illness medications
- Antibiotics and anti-infectives
- Pain management medications
- Contraceptives (covered under family planning)

Network Pharmacies:
Available in all major areas of Greater Accra including:
- Accra Central
- East Legon
- Madina
- Circle
- Osu
- Labone
- Tema
- Dansoman
- Spintex
- Achimota

How to Use Pharmacy Benefits:
1. Get prescription from your doctor
2. Present prescription at network pharmacy
3. Show your Premier Health ID card
4. Pharmacy verifies coverage
5. Receive your medication
6. No upfront payment (for covered medications)

Medication Tiers:
- Tier 1: Generic medications (fully covered)
- Tier 2: Preferred brand-name drugs (partial coverage)
- Tier 3: Non-preferred brands (higher copay)
- Tier 4: Specialty medications (requires pre-authorization)

Non-Covered Medications:
- Over-the-counter drugs (unless prescribed)
- Cosmetic medications
- Experimental or investigational drugs
- Nutritional supplements and vitamins
- Weight loss medications (unless medically necessary)

Prescription Refills:
- Most medications: 30-day supply
- Chronic conditions: 90-day supply available
- Refills require new prescription every 6-12 months

Specialty Medications:
- Requires pre-authorization
- Used for complex chronic conditions
- May require specialty pharmacy
- Higher cost-sharing applies

Medication Not Available at Pharmacy:
- Pharmacy will order (1-3 days)
- Alternative medication may be suggested
- Contact Premier Health for urgent needs

Medication Coverage Verification:
- Check formulary list on website
- Call pharmacy before filling prescription
- Contact customer service for coverage questions
""",
        category="pharmacy_benefits",
        source="pharmacy_handbook",
        tags=["pharmacy", "medications", "prescriptions", "drugs"],
        metadata={"network_pharmacies": "50+"}
    ),

    KnowledgeDocument(
        id="ph_contact_001",
        title="Contact Information and Customer Service",
        content="""
Premier Health Insurance - Contact Information

Customer Service:
- Phone: [Main helpline number]
- WhatsApp: [WhatsApp business number]
- Email: info@premierhealth.com.gh
- Hours: Monday-Friday 8:00 AM - 6:00 PM, Saturday 9:00 AM - 2:00 PM

24/7 Emergency Hotline:
- Emergency claims assistance
- After-hours provider referrals
- Emergency pre-authorization

Claims Department:
- Email: claims@premierhealth.com.gh
- Phone: [Claims hotline]
- Fax: [Claims fax number]

Provider Relations:
- Email: providers@premierhealth.com.gh
- Phone: [Provider services number]

Corporate Sales:
- Email: corporate@premierhealth.com.gh
- Phone: [Corporate sales number]

Head Office:
[Physical address]
Accra, Ghana

Branch Offices:
- Tema Branch: [Address]
- East Legon Office: [Address]

Online Services:
- Website: www.premierhealth.com.gh
- Member Portal: portal.premierhealth.com.gh
- Mobile App: Download from Google Play or App Store

Social Media:
- Facebook: @PremierHealthGhana
- Twitter: @PremierHealthGH
- Instagram: @premierhealthgh
- LinkedIn: Premier Health Insurance Ghana

Common Inquiries:
- Provider search: Use voice assistant or website directory
- Claim status: Check online portal or call claims department
- Card replacement: Contact customer service
- Policy information: Member portal or customer service
- Add dependent: Email or visit office with documentation
- Payment arrangements: Speak with billing department

Customer Service Languages:
- English
- Twi
- Ga
- Ewe

Response Time:
- Phone: Immediate (during business hours)
- Email: Within 24 hours
- Social media: Within 4 hours
- Formal complaints: Within 7 business days
""",
        category="contact_support",
        source="contact_directory",
        tags=["contact", "support", "customer_service", "helpline"],
        metadata={"availability": "24/7_emergency", "business_hours": "Mon-Sat"}
    ),

    KnowledgeDocument(
        id="ph_locations_001",
        title="Healthcare Provider Locations - Detailed Area Guide",
        content="""
Premier Health provider network spans Greater Accra with coverage in key neighborhoods.

ACCRA CENTRAL:
- Multiple general hospitals
- Walk-in clinics
- 24/7 pharmacies
- Diagnostic centers
- Good public transport access

EAST LEGON:
- Premium private hospitals
- Specialist medical centers
- Cosmopolitan area with international standard facilities
- Gynecology and pediatric specialists
- High concentration of dental and optical services

MADINA:
- Community health centers
- Affordable clinic options
- Several pharmacies
- Family medicine practices
- Good access for eastern suburbs

CIRCLE (OBRA SPOT):
- Central medical district
- Multiple specialist centers
- Diagnostic laboratories
- Affordable healthcare options
- Well-connected by public transport

TEMA (COMMUNITY 1-25):
- Industrial area healthcare
- Port city medical facilities
- Emergency services available
- Occupational health centers
- Good coverage across communities

OSU:
- International clinics
- Expat-friendly services
- Specialist consultations
- Premium healthcare facilities
- English-speaking providers

LABONE:
- Residential area clinics
- Family practice centers
- Pediatric specialists
- Dental clinics
- Well-established medical community

DANSOMAN:
- Community health centers
- Affordable clinic network
- Pharmacy coverage
- Growing healthcare infrastructure
- Serves western Accra suburbs

SPINTEX ROAD:
- Modern medical centers
- New healthcare corridor
- Specialist services expanding
- Good road access
- Serves growing residential areas

ACHIMOTA:
- Hospital services
- Community clinics
- Pharmacy network
- Junction area accessibility
- Serves northern suburbs

KANESHIE:
- Market area medical services
- Walk-in clinics
- Affordable healthcare
- Traditional and modern medicine
- High patient volume facilities

AIRPORT AREA:
- International standard clinics
- Business traveler services
- Executive health screening
- Premium diagnostic centers

How to Choose the Right Location:
1. Consider proximity to your home or workplace
2. Check provider specialty availability
3. Verify operating hours match your schedule
4. Consider public transport or parking availability
5. Read reviews on Premier Health app
6. For specialists, ask your GP for recommendations

Travel Time Estimates (from Accra Central):
- East Legon: 20-30 minutes
- Madina: 30-40 minutes
- Circle: 10-15 minutes
- Tema: 45-60 minutes
- Osu: 15-20 minutes
- Spintex: 25-35 minutes
""",
        category="location_guide",
        source="provider_directory",
        tags=["locations", "areas", "neighborhoods", "geography", "access"],
        metadata={"areas_covered": 15, "region": "Greater_Accra"}
    ),
]

async def initialize_knowledge_base():
    """Initialize Premier Health knowledge base with comprehensive documents."""
    print("🏥 Initializing Premier Health RAG Knowledge Base")
    print("=" * 60)

    try:
        # Initialize knowledge base
        result = await helpdesk_rag_service.initialize_knowledge_base(
            company_name="premier_health_production",
            documents=PREMIER_HEALTH_KNOWLEDGE
        )

        print(f"\n✅ Knowledge Base Initialized Successfully!")
        print(f"   Collection: {result['collection_name']}")
        print(f"   Documents indexed: {result['documents_indexed']}")
        print(f"   Chunks created: {result['chunks_created']}")
        print(f"   Embedding dimension: {result['embedding_dimension']}")
        print(f"   Created at: {result['created_at']}")

        # Get stats
        print(f"\n📊 Knowledge Base Statistics:")
        stats = await helpdesk_rag_service.get_knowledge_base_stats("premier_health_production")
        for key, value in stats.items():
            print(f"   {key}: {value}")

        print(f"\n✅ Initialization Complete!")

    except Exception as e:
        print(f"\n❌ Error initializing knowledge base: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_knowledge_base())
