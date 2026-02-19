#!/usr/bin/env python3
"""
Import Premier Health Insurance provider data to PostgreSQL
Optimized for AI voice agent queries with semantic search
"""

import re
import psycopg2
from psycopg2.extras import RealDictCursor
from openpyxl import load_workbook
import openai
from typing import List, Dict, Optional, Tuple
import json

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'kasaai_core',
    'options': '-c search_path=premier_health,public',  # or 'supabase_dev'
    'user': 'postgres',
    'password': 'aawwER44444'
}

class HealthcareDataImporter:
    def __init__(self, db_config: dict, openai_api_key: str = None):
        self.db_config = db_config
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key

    def connect_db(self):
        """Connect to PostgreSQL database"""
        return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)

    def normalize_phone(self, phone: str) -> str:
        """Standardize phone number format"""
        if not phone:
            return None

        # Remove common separators and spaces
        phone = re.sub(r'[^\d+]', '', str(phone))

        # Handle Ghana numbers (add country code if missing)
        if phone.startswith('0'):
            phone = '+233' + phone[1:]
        elif not phone.startswith('+'):
            phone = '+233' + phone

        return phone

    def extract_specialties(self, specialty_text: str) -> List[str]:
        """Extract and standardize specialties from text"""
        if not specialty_text:
            return []

        # Common specialty mappings
        specialty_mapping = {
            'GP': 'General Practice',
            'PED': 'Pediatrics',
            'PAED': 'Pediatrics',
            'GYN': 'Gynecology',
            'GYNAE': 'Gynecology',
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

        # Split by common delimiters
        parts = re.split(r'[/,;]', text)

        for part in parts:
            part = part.strip()
            if part in specialty_mapping:
                specialties.append(specialty_mapping[part])
            elif part:
                # Keep original if not in mapping
                specialties.append(part.title())

        return list(set(specialties))  # Remove duplicates

    def determine_provider_type(self, name: str, specialties: List[str]) -> str:
        """Determine provider type from name and specialties"""
        name_lower = name.lower()

        if 'hospital' in name_lower:
            return 'hospital'
        elif 'clinic' in name_lower:
            return 'clinic'
        elif any(word in name_lower for word in ['pharmacy', 'chemist']):
            return 'pharmacy'
        elif any(word in name_lower for word in ['eye', 'optical', 'vision']):
            return 'optical'
        elif 'centre' in name_lower or 'center' in name_lower:
            return 'clinic'
        else:
            return 'clinic'  # Default

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate OpenAI embedding for semantic search"""
        if not self.openai_api_key:
            return None

        try:
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def create_search_text(self, provider: dict) -> str:
        """Create comprehensive text for embedding generation"""
        parts = [
            provider['name'],
            provider.get('area', ''),
            ' '.join(provider.get('specialties', [])),
            provider.get('services_description', ''),
            provider.get('provider_type', '')
        ]
        return ' '.join(filter(None, parts))

    def parse_excel_data(self, file_path: str) -> List[Dict]:
        """Parse Excel file and extract provider data"""
        providers = []
        wb = load_workbook(file_path, read_only=True)

        for sheet_name in wb.sheetnames:
            print(f"Processing sheet: {sheet_name}")
            ws = wb[sheet_name]

            # Find header row (contains 'NAME', 'CONTACT', etc.)
            header_row = None
            for row_num in range(1, min(10, ws.max_row + 1)):
                row_values = [str(ws.cell(row=row_num, column=col).value or '') for col in range(1, 6)]
                if any('NAME' in val.upper() for val in row_values):
                    header_row = row_num
                    break

            if not header_row:
                print(f"Could not find header in {sheet_name}")
                continue

            current_area = None
            provider_index = 0

            for row_num in range(header_row + 1, ws.max_row + 1):
                row_data = [ws.cell(row=row_num, column=col).value for col in range(1, 6)]

                # Skip completely empty rows
                if not any(row_data):
                    continue

                # Check if this is an area header (no index number, just location)
                if (not row_data[0] or not str(row_data[0]).strip().isdigit()) and row_data[1]:
                    area_text = str(row_data[1]).strip()
                    if area_text and not any(word in area_text.lower() for word in ['clinic', 'hospital', 'pharmacy']):
                        current_area = area_text
                        continue

                # Parse provider data
                if row_data[1]:  # Has provider name
                    name = str(row_data[1]).strip()
                    if not name or len(name) < 3:
                        continue

                    specialties_text = str(row_data[2] or '').strip()
                    contact = str(row_data[3] or '').strip()
                    location = str(row_data[4] or '').strip() or current_area

                    specialties = self.extract_specialties(specialties_text)
                    provider_type = self.determine_provider_type(name, specialties)

                    # Split multiple phone numbers
                    phones = [self.normalize_phone(p.strip()) for p in re.split(r'[/,;]', contact) if p.strip()]

                    provider = {
                        'name': name,
                        'normalized_name': re.sub(r'[^\w\s]', '', name).lower(),
                        'provider_type': provider_type,
                        'phone_primary': phones[0] if phones else None,
                        'phone_secondary': phones[1] if len(phones) > 1 else None,
                        'address': location,
                        'area': current_area,
                        'region': 'Greater Accra',  # From the data
                        'specialties': specialties,
                        'services_description': specialties_text,
                        'search_keywords': specialties + [provider_type, name.lower()],
                        'source_sheet': sheet_name,
                        'source_row_number': row_num,
                        'is_active': True
                    }

                    providers.append(provider)
                    provider_index += 1

        return providers

    def setup_database(self):
        """Create database schema"""
        with open('/opt/kasaai/apps/automations/premier-health/schema.sql', 'r') as f:
            schema_sql = f.read()

        conn = self.connect_db()
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

    def import_providers(self, providers: List[Dict]):
        """Import providers into database"""
        conn = self.connect_db()

        try:
            with conn.cursor() as cur:
                # Clear existing data
                cur.execute("DELETE FROM provider_specialties")
                cur.execute("DELETE FROM healthcare_providers")

                insert_sql = """
                INSERT INTO healthcare_providers (
                    name, normalized_name, provider_type, phone_primary, phone_secondary,
                    address, area, region, specialties, services_description,
                    search_keywords, source_sheet, source_row_number, is_active, embedding
                ) VALUES (
                    %(name)s, %(normalized_name)s, %(provider_type)s, %(phone_primary)s, %(phone_secondary)s,
                    %(address)s, %(area)s, %(region)s, %(specialties)s, %(services_description)s,
                    %(search_keywords)s, %(source_sheet)s, %(source_row_number)s, %(is_active)s, %(embedding)s
                )
                """

                imported_count = 0
                for provider in providers:
                    try:
                        # Generate embedding if OpenAI key available
                        search_text = self.create_search_text(provider)
                        embedding = self.generate_embedding(search_text)
                        provider['embedding'] = embedding

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

    # Initialize importer (add OpenAI API key if available)
    importer = HealthcareDataImporter(DB_CONFIG)  # Add openai_api_key="your-key" for embeddings

    print("🏥 Premier Health Insurance Data Import")
    print("=" * 50)

    # Setup database
    print("1. Setting up database schema...")
    importer.setup_database()

    # Parse Excel data
    print("2. Parsing Excel file...")
    providers = importer.parse_excel_data(file_path)
    print(f"Found {len(providers)} providers")

    # Import to database
    print("3. Importing to database...")
    importer.import_providers(providers)

    print("✅ Import completed!")

if __name__ == "__main__":
    main()