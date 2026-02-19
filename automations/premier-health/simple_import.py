#!/usr/bin/env python3
"""
Simple import script for Premier Health Insurance provider data
No external dependencies except system psycopg2
"""

import sys
import re
sys.path.append('/usr/lib/python3/dist-packages')

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("psycopg2 not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary', '--break-system-packages'])
    import psycopg2
    from psycopg2.extras import RealDictCursor

from openpyxl import load_workbook
from typing import List, Dict

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'kasaai_core',
    'options': '-c search_path=premier_health,public',
    'user': 'postgres',
    'password': 'aawwER44444'
}

def setup_database():
    """Create database schema"""
    schema_sql = '''
    -- Healthcare Provider Database Schema
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    CREATE EXTENSION IF NOT EXISTS unaccent;

    -- Drop existing tables
    DROP TABLE IF EXISTS provider_specialties CASCADE;
    DROP TABLE IF EXISTS healthcare_providers CASCADE;
    DROP TABLE IF EXISTS specialties CASCADE;
    DROP TABLE IF EXISTS locations CASCADE;

    -- Main providers table
    CREATE TABLE healthcare_providers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        normalized_name VARCHAR(255),
        provider_type VARCHAR(50),
        phone_primary VARCHAR(50),
        phone_secondary VARCHAR(50),
        email VARCHAR(255),
        website VARCHAR(255),
        address TEXT,
        area VARCHAR(100),
        region VARCHAR(100),
        specialties TEXT[],
        services_description TEXT,
        search_vector tsvector,
        search_keywords TEXT[],
        insurance_plans TEXT[],
        operating_hours JSONB,
        is_active BOOLEAN DEFAULT true,
        is_emergency BOOLEAN DEFAULT false,
        source_sheet VARCHAR(50),
        source_row_number INTEGER,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    -- Indexes for search optimization
    CREATE INDEX idx_providers_name_trgm ON healthcare_providers USING gin (name gin_trgm_ops);
    CREATE INDEX idx_providers_area_trgm ON healthcare_providers USING gin (area gin_trgm_ops);
    CREATE INDEX idx_providers_specialties ON healthcare_providers USING gin (specialties);
    CREATE INDEX idx_providers_search_vector ON healthcare_providers USING gin (search_vector);
    CREATE INDEX idx_providers_active ON healthcare_providers (is_active) WHERE is_active = true;

    -- Function to update search vector
    CREATE OR REPLACE FUNCTION update_search_vector() RETURNS trigger AS $$
    BEGIN
        NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.area, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(array_to_string(NEW.specialties, ' '), '')), 'C') ||
            setweight(to_tsvector('english', COALESCE(NEW.services_description, '')), 'D');
        NEW.updated_at := NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- Trigger for search vector
    CREATE TRIGGER trigger_update_search_vector
        BEFORE INSERT OR UPDATE ON healthcare_providers
        FOR EACH ROW EXECUTE FUNCTION update_search_vector();

    -- Simple search function
    CREATE OR REPLACE FUNCTION search_providers(
        query_text TEXT DEFAULT '',
        area_filter TEXT DEFAULT NULL,
        specialty_filter TEXT DEFAULT NULL,
        max_results INTEGER DEFAULT 10
    )
    RETURNS TABLE(
        id INTEGER,
        name VARCHAR(255),
        area VARCHAR(100),
        specialties TEXT[],
        phone_primary VARCHAR(50),
        address TEXT,
        text_rank DOUBLE PRECISION
    ) AS $$
    BEGIN
        RETURN QUERY
        SELECT
            p.id,
            p.name,
            p.area,
            p.specialties,
            p.phone_primary,
            p.address,
            CASE
                WHEN query_text != ''
                THEN ts_rank_cd(p.search_vector, plainto_tsquery('english', query_text))::DOUBLE PRECISION
                ELSE 0.0::DOUBLE PRECISION
            END as text_rank
        FROM healthcare_providers p
        WHERE p.is_active = true
            AND (area_filter IS NULL OR p.area ILIKE '%' || area_filter || '%')
            AND (specialty_filter IS NULL OR specialty_filter = ANY(p.specialties))
            AND (
                query_text = '' OR
                p.search_vector @@ plainto_tsquery('english', query_text) OR
                p.name ILIKE '%' || query_text || '%'
            )
        ORDER BY text_rank DESC, p.name
        LIMIT max_results;
    END;
    $$ LANGUAGE plpgsql;
    '''

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
        conn.commit()
        print("✅ Database schema created successfully")
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        conn.rollback()
    finally:
        conn.close()

def normalize_phone(phone: str) -> str:
    """Standardize phone number format"""
    if not phone:
        return None

    phone = re.sub(r'[^\d+]', '', str(phone))
    if phone.startswith('0'):
        phone = '+233' + phone[1:]
    elif not phone.startswith('+'):
        phone = '+233' + phone
    return phone

def extract_specialties(specialty_text: str) -> List[str]:
    """Extract specialties from text"""
    if not specialty_text:
        return []

    specialty_mapping = {
        'GP': 'General Practice',
        'PED': 'Pediatrics', 'PAED': 'Pediatrics',
        'GYN': 'Gynecology', 'GYNAE': 'Gynecology',
        'OBS/GYN': 'Obstetrics/Gynecology',
        'ENT': 'Ear Nose Throat',
        'PHY': 'Physiotherapy',
        'OPTHALMOLOGY': 'Ophthalmology',
        'OPTICAL SERVICES': 'Ophthalmology',
        'PHARMACY': 'Pharmacy',
        'ALL SPECIALIST': 'Multi-Specialty',
        'ALL SPECIALITY': 'Multi-Specialty'
    }

    specialties = []
    text = specialty_text.upper().strip()
    parts = re.split(r'[/,;]', text)

    for part in parts:
        part = part.strip()
        if part in specialty_mapping:
            specialties.append(specialty_mapping[part])
        elif part:
            specialties.append(part.title())

    return list(set(specialties))

def determine_provider_type(name: str) -> str:
    """Determine provider type from name"""
    name_lower = name.lower()
    if 'hospital' in name_lower:
        return 'hospital'
    elif 'clinic' in name_lower:
        return 'clinic'
    elif any(word in name_lower for word in ['pharmacy', 'chemist']):
        return 'pharmacy'
    elif any(word in name_lower for word in ['eye', 'optical', 'vision']):
        return 'optical'
    else:
        return 'clinic'

def parse_excel_data(file_path: str) -> List[Dict]:
    """Parse Excel file and extract provider data"""
    providers = []
    wb = load_workbook(file_path, read_only=True)

    for sheet_name in wb.sheetnames:
        print(f"Processing sheet: {sheet_name}")
        ws = wb[sheet_name]

        # Find header row
        header_row = None
        for row_num in range(1, min(10, ws.max_row + 1)):
            row_values = [str(ws.cell(row=row_num, column=col).value or '') for col in range(1, 6)]
            if any('NAME' in val.upper() for val in row_values):
                header_row = row_num
                break

        if not header_row:
            continue

        current_area = None

        for row_num in range(header_row + 1, ws.max_row + 1):
            row_data = [ws.cell(row=row_num, column=col).value for col in range(1, 6)]

            if not any(row_data):
                continue

            # Check for area header
            if (not row_data[0] or not str(row_data[0]).strip().isdigit()) and row_data[1]:
                area_text = str(row_data[1]).strip()
                if area_text and not any(word in area_text.lower() for word in ['clinic', 'hospital', 'pharmacy']):
                    current_area = area_text
                    continue

            # Parse provider data
            if row_data[1]:
                name = str(row_data[1]).strip()
                if not name or len(name) < 3:
                    continue

                specialties_text = str(row_data[2] or '').strip()
                contact = str(row_data[3] or '').strip()
                location = str(row_data[4] or '').strip() or current_area

                specialties = extract_specialties(specialties_text)
                provider_type = determine_provider_type(name)

                phones = [normalize_phone(p.strip()) for p in re.split(r'[/,;]', contact) if p.strip()]

                provider = {
                    'name': name,
                    'normalized_name': re.sub(r'[^\w\s]', '', name).lower(),
                    'provider_type': provider_type,
                    'phone_primary': phones[0] if phones else None,
                    'phone_secondary': phones[1] if len(phones) > 1 else None,
                    'address': location,
                    'area': current_area,
                    'region': 'Greater Accra',
                    'specialties': specialties,
                    'services_description': specialties_text,
                    'search_keywords': specialties + [provider_type, name.lower()],
                    'insurance_plans': ['Premier Health Insurance'],
                    'source_sheet': sheet_name,
                    'source_row_number': row_num,
                    'is_active': True
                }

                providers.append(provider)

    return providers

def import_providers(providers: List[Dict]):
    """Import providers into database"""
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn.cursor() as cur:
            insert_sql = '''
            INSERT INTO healthcare_providers (
                name, normalized_name, provider_type, phone_primary, phone_secondary,
                address, area, region, specialties, services_description,
                search_keywords, insurance_plans, source_sheet, source_row_number, is_active
            ) VALUES (
                %(name)s, %(normalized_name)s, %(provider_type)s, %(phone_primary)s, %(phone_secondary)s,
                %(address)s, %(area)s, %(region)s, %(specialties)s, %(services_description)s,
                %(search_keywords)s, %(insurance_plans)s, %(source_sheet)s, %(source_row_number)s, %(is_active)s
            )
            '''

            imported_count = 0
            for provider in providers:
                try:
                    cur.execute(insert_sql, provider)
                    imported_count += 1
                    if imported_count % 50 == 0:
                        print(f"Imported {imported_count} providers...")
                except Exception as e:
                    print(f"Error importing provider {provider['name']}: {e}")
                    continue

            conn.commit()
            print(f"✅ Successfully imported {imported_count} providers")

    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    """Main import function"""
    file_path = '/opt/kasaai/apps/automations/premier-health/PHI SERVICE PROVIDER LIST - UPDATED_4.xlsx'

    print("🏥 Premier Health Insurance Data Import")
    print("=" * 50)

    print("1. Setting up database schema...")
    setup_database()

    print("2. Parsing Excel file...")
    providers = parse_excel_data(file_path)
    print(f"Found {len(providers)} providers")

    print("3. Importing to database...")
    import_providers(providers)

    print("✅ Import completed!")

    # Test the search function
    print("\\n🔍 Testing search function...")
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT search_providers('eye doctor', 'Accra', NULL, 3)")
            results = cur.fetchall()
            print(f"Sample search results: {len(results)} found")
            for result in results:
                print(f"  - {result[0]}")
    except Exception as e:
        print(f"Search test error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()