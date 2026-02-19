"""
Migration script for Ghanaian Location Services

Extracts location data from CSV files and seeds the MongoDB database
with comprehensive phonetic matching and pronunciation data.
"""

import asyncio
import csv
import re
import logging
from typing import Set, List, Dict, Any
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import (
    GhanaianLocation, STTCorrection, PronunciationGuide, LocationRelationship,
    ToolContext, LanguageContext, RelationshipType
)
from database.repositories import LocationRepository
from phonetic_matcher import PhoneticMatcher

# Add core backend to path for database connection
sys.path.append('/opt/kasaai/apps/core_backend')
from backend.database import get_database

logger = logging.getLogger(__name__)


class LocationDataMigrator:
    """
    Migrates location data from CSV and creates comprehensive database
    """

    def __init__(self, db_connection):
        """
        Initialize migrator with database connection

        Args:
            db_connection: MongoDB database connection
        """
        self.db = db_connection
        self.repository = LocationRepository(db_connection)
        self.phonetic_matcher = PhoneticMatcher(self.repository)

        # Track locations found during migration
        self.unique_locations: Set[str] = set()
        self.location_aliases: Dict[str, Set[str]] = {}
        self.provider_counts: Dict[str, int] = {}

        # Common STT corrections from experience
        self.known_stt_corrections = [
            # Accra variations
            ("akra", "ACCRA"),
            ("accraw", "ACCRA"),
            ("acra", "ACCRA"),
            ("accra central", "ACCRA CENTRAL"),
            ("accra centrum", "ACCRA CENTRAL"),

            # Area variations
            ("madena", "MADINA"),
            ("madina town", "MADINA"),
            ("kanashi", "KANESHIE"),
            ("kaneshi", "KANESHIE"),
            ("adabaka", "ADABRAKA"),
            ("adbraka", "ADABRAKA"),

            # Difficult names
            ("zorwulu", "DZORWULU"),
            ("jorvulu", "DZORWULU"),
            ("dzolvulu", "DZORWULU"),
            ("kokomlemele", "KOKOMLEMLE"),
            ("kokolemle", "KOKOMLEMLE"),
            ("koko lemle", "KOKOMLEMLE"),

            # Transportation hubs
            ("tema station", "TEMA"),
            ("kaneshie market", "KANESHIE"),
            ("makola market", "MAKOLA"),
            ("tudu station", "TUDU"),

            # Hospital areas
            ("korle bu", "KORLE-BU"),
            ("korlebu", "KORLE-BU"),
            ("thirty seven", "37 MILITARY HOSPITAL"),
            ("ridge hospital", "RIDGE"),

            # Common mishearings
            ("labadi", "LA BAADI"),
            ("labone", "LABONE"),
            ("osu bojo", "OSU"),
            ("cantonment", "CANTONMENTS"),
            ("airport area", "AIRPORT RESIDENTIAL"),

            # Suburb variations
            ("east legion", "EAST LEGON"),
            ("west legion", "WEST LEGON"),
            ("adjiran ganor", "ADJRINGANOR"),
            ("tse ado", "TSE ADDO"),

            # Industrial areas
            ("spintech", "SPINTEX"),
            ("tema community", "TEMA"),
            ("ashaman", "ASHAIMAN"),
            ("sakumono", "SAKUMONO ESTATE"),

            # Northern areas
            ("haatso road", "HAATSO"),
            ("kwabenya", "KWABENYA"),
            ("ofankor", "OFANKOR"),
            ("tantra hills", "TANTRA HILL"),
        ]

    async def migrate_from_csv(self, csv_file_path: str):
        """
        Extract locations from Premier Health CSV and populate database

        Args:
            csv_file_path: Path to the CSV file
        """
        logger.info(f"🔄 Starting migration from CSV: {csv_file_path}")

        try:
            # Step 1: Extract locations from CSV
            await self._extract_locations_from_csv(csv_file_path)

            # Step 2: Create location records
            await self._create_location_records()

            # Step 3: Add STT corrections
            await self._add_stt_corrections()

            # Step 4: Create pronunciation guides
            await self._create_pronunciation_guides()

            # Step 5: Add location relationships
            await self._add_location_relationships()

            logger.info("✅ Migration completed successfully")

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise

    async def _extract_locations_from_csv(self, csv_file_path: str):
        """Extract unique locations from CSV file"""
        logger.info("📊 Extracting locations from CSV...")

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Skip BOM if present
                content = file.read()
                if content.startswith('\ufeff'):
                    content = content[1:]

                # Parse CSV
                reader = csv.reader(content.splitlines())
                current_area = None
                provider_count = 0

                for row in reader:
                    if not row or len(row) < 2:
                        continue

                    # Check if this is an area header (empty first column, area name in second)
                    if not row[0].strip() and len(row) > 1 and row[1].strip():
                        current_area = self._normalize_location_name(row[1])
                        if current_area:
                            self.unique_locations.add(current_area)
                            self.provider_counts[current_area] = 0
                            provider_count = 0
                        continue

                    # Check if this is a provider row (number in first column)
                    if row[0].strip() and current_area and len(row) >= 5:
                        try:
                            provider_num = int(row[0].strip())
                            provider_count += 1
                            self.provider_counts[current_area] = provider_count

                            # Extract location from provider address (last column)
                            if len(row) > 4 and row[4].strip():
                                provider_location = self._extract_location_from_address(row[4])
                                if provider_location:
                                    # Add as alias to current area
                                    if current_area not in self.location_aliases:
                                        self.location_aliases[current_area] = set()
                                    self.location_aliases[current_area].add(provider_location)

                        except ValueError:
                            # Not a provider number, skip
                            continue

                logger.info(f"📍 Extracted {len(self.unique_locations)} unique locations")
                for location, count in list(self.provider_counts.items())[:10]:
                    logger.info(f"   • {location}: {count} providers")

        except Exception as e:
            logger.error(f"Failed to extract locations from CSV: {e}")
            raise

    def _normalize_location_name(self, location: str) -> str:
        """Normalize location name for database storage"""
        if not location:
            return ""

        # Remove extra whitespace and convert to uppercase
        normalized = ' '.join(location.strip().upper().split())

        # Remove common suffixes that don't help with location identification
        suffixes_to_remove = [
            " / MATAHEKO", " / MAMPROBI / KORLE-BU", " & NEW ACHIMOTA",
            " / ADJRINGANOR", " / CANTONMENTS", " / COMMUNITY 26",
            " ESTATE / LASHIBI / COMM. 18,19,21"
        ]

        for suffix in suffixes_to_remove:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()

        # Clean up common formatting issues
        normalized = re.sub(r'\s+/\s+', ' / ', normalized)  # Standardize slashes
        normalized = re.sub(r'\s+&\s+', ' & ', normalized)  # Standardize ampersands
        normalized = re.sub(r'\s+', ' ', normalized)  # Remove extra spaces

        return normalized

    def _extract_location_from_address(self, address: str) -> str:
        """Extract location name from provider address"""
        if not address or address.upper() in ['', 'N/A']:
            return ""

        # Common location patterns in addresses
        location_patterns = [
            r'\b(ACCRA MALL)\b',
            r'\b(EAST LEGON)\b',
            r'\b(WEST LEGON)\b',
            r'\b(SPINTEX ROAD)\b',
            r'\b(OSU)\b',
            r'\b(LABONE)\b',
            r'\b(CANTONMENTS)\b',
            r'\b(RIDGE)\b',
            r'\b(TESANO)\b',
            r'\b(DZORWULU)\b',
            r'\b(KOKOMLEMLE)\b',
            r'\b(MADINA)\b',
            r'\b(KANESHIE)\b',
            r'\b(ADABRAKA)\b',
        ]

        address_upper = address.upper()
        for pattern in location_patterns:
            match = re.search(pattern, address_upper)
            if match:
                return match.group(1)

        return ""

    async def _create_location_records(self):
        """Create GhanaianLocation records in database"""
        logger.info("🏗️ Creating location records...")

        created_count = 0
        for location_name in self.unique_locations:
            try:
                # Check if location already exists
                existing = await self.repository.get_location_by_name(location_name)
                if existing:
                    logger.debug(f"Location already exists: {location_name}")
                    continue

                # Generate phonetic codes
                phonetic_codes = self._generate_phonetic_codes(location_name)

                # Get aliases for this location
                aliases = list(self.location_aliases.get(location_name, set()))

                # Get provider count
                provider_count = self.provider_counts.get(location_name, 0)

                # Create location record
                location = GhanaianLocation(
                    canonical_name=location_name,
                    display_name=self._create_display_name(location_name),
                    aliases=aliases,
                    phonetic_codes=phonetic_codes,
                    pronunciation={
                        "difficulty_score": self._calculate_difficulty_score(location_name),
                        "syllable_count": len(location_name.split()),
                        "has_difficult_sounds": self._has_difficult_sounds(location_name)
                    },
                    geographic=self._get_geographic_info(location_name),
                    context={
                        "healthcare": {
                            "provider_count": provider_count,
                            "has_hospitals": provider_count > 5,
                            "coverage_area": "urban" if provider_count > 3 else "suburban"
                        }
                    }
                )

                await self.repository.create_location(location)
                created_count += 1
                logger.debug(f"Created location: {location_name}")

            except Exception as e:
                logger.error(f"Failed to create location {location_name}: {e}")

        logger.info(f"✅ Created {created_count} location records")

    def _generate_phonetic_codes(self, location_name: str) -> Dict[str, str]:
        """Generate phonetic codes for a location name"""
        # Use the same logic as PhoneticMatcher
        import phonetics
        from unidecode import unidecode

        normalized = unidecode(location_name.upper().strip())

        codes = {
            'soundex': phonetics.soundex(normalized) or '',
            'nysiis': phonetics.nysiis(normalized) or '',
            'metaphone': phonetics.metaphone(normalized) or '',
            'dmetaphone_primary': phonetics.dmetaphone(normalized)[0] or '',
            'dmetaphone_secondary': phonetics.dmetaphone(normalized)[1] or ''
        }

        # Add custom Ghanaian pattern
        codes['ghana_pattern'] = self._compute_ghana_pattern(normalized)

        return codes

    def _compute_ghana_pattern(self, text: str) -> str:
        """Compute custom Ghanaian phonetic pattern"""
        if not text:
            return ""

        # Common Ghanaian phonetic substitutions
        substitutions = {
            'KW': 'QU',    # Kwabenya -> Quabenya
            'NY': 'NI',    # Nyamekye -> Niamekye
            'DZ': 'Z',     # Dzorwulu -> Zorwulu
            'TSH': 'CH',   # Common in some pronunciations
            'PH': 'F',     # Standard substitution
            'GH': 'G',     # Ghana -> Gana
            'WH': 'W',     # What -> Wat
        }

        pattern = text
        for old, new in substitutions.items():
            pattern = pattern.replace(old, new)

        # Remove vowels except the first one
        if len(pattern) > 1:
            first_char = pattern[0]
            rest = ''.join(c for c in pattern[1:] if c not in 'AEIOU')
            pattern = first_char + rest

        # Limit to 6 characters
        return pattern[:6].ljust(6, '0')

    def _calculate_difficulty_score(self, location_name: str) -> float:
        """Calculate pronunciation difficulty score"""
        difficulty = 0.0
        name_upper = location_name.upper()

        # Check for difficult sound patterns
        difficult_patterns = {
            r'DZ': 0.9,      # Dzorwulu
            r'NY': 0.8,      # Nyamekye
            r'KW': 0.7,      # Kwabenya
            r'GB': 0.9,      # Gbegbeyise
            r'TSH': 0.8,     # Some Ewe names
            r'NG': 0.6,      # Ngleshie
        }

        for pattern, score in difficult_patterns.items():
            if re.search(pattern, name_upper):
                difficulty = max(difficulty, score)

        # Length-based difficulty
        if len(location_name) > 12:
            difficulty = max(difficulty, 0.7)
        elif len(location_name) > 10:
            difficulty = max(difficulty, 0.6)

        return min(1.0, difficulty)

    def _has_difficult_sounds(self, location_name: str) -> bool:
        """Check if location has difficult sounds for TTS"""
        difficult_sounds = ['DZ', 'NY', 'KW', 'GB', 'TSH', 'NG']
        name_upper = location_name.upper()
        return any(sound in name_upper for sound in difficult_sounds)

    def _create_display_name(self, canonical_name: str) -> str:
        """Create user-friendly display name"""
        # Convert to title case for display
        return ' '.join(word.capitalize() for word in canonical_name.split())

    def _get_geographic_info(self, location_name: str) -> Dict[str, Any]:
        """Get geographic context for location"""
        # Basic geographic classification based on known areas
        urban_areas = ['ACCRA CENTRAL', 'OSU', 'ADABRAKA', 'KANESHIE', 'MAKOLA', 'TUDU']
        suburban_areas = ['EAST LEGON', 'WEST LEGON', 'ADJRINGANOR', 'SPINTEX', 'TEMA']
        peripheral_areas = ['KWABENYA', 'OFANKOR', 'TANTRA HILL', 'DOME', 'HAATSO']

        if location_name in urban_areas:
            area_type = "urban_core"
            region = "Central Accra"
        elif location_name in suburban_areas:
            area_type = "suburban"
            region = "Greater Accra"
        elif location_name in peripheral_areas:
            area_type = "peripheral"
            region = "Greater Accra Metropolitan"
        else:
            area_type = "mixed"
            region = "Greater Accra"

        return {
            "area_type": area_type,
            "region": region,
            "urban_classification": area_type
        }

    async def _add_stt_corrections(self):
        """Add STT correction records"""
        logger.info("🎤 Adding STT corrections...")

        created_count = 0
        for misheard, correct in self.known_stt_corrections:
            try:
                # Check if location exists
                location = await self.repository.get_location_by_name(correct)
                if not location:
                    logger.debug(f"Skipping STT correction for non-existent location: {correct}")
                    continue

                # Check if correction already exists
                existing = await self.repository.get_stt_correction(misheard)
                if existing:
                    continue

                # Calculate phonetic similarity
                similarity = self._calculate_phonetic_similarity(misheard, correct)

                # Create STT correction
                correction = STTCorrection(
                    misheard_input=misheard.lower(),
                    correct_location=correct.upper(),
                    confidence=0.8,
                    phonetic_similarity=similarity,
                    frequency=1,
                    verified=False,
                    source="migration_script"
                )

                await self.repository.create_stt_correction(correction)
                created_count += 1

            except Exception as e:
                logger.error(f"Failed to create STT correction {misheard}->{correct}: {e}")

        logger.info(f"✅ Created {created_count} STT corrections")

    def _calculate_phonetic_similarity(self, text1: str, text2: str) -> float:
        """Calculate phonetic similarity between two texts"""
        codes1 = self._generate_phonetic_codes(text1)
        codes2 = self._generate_phonetic_codes(text2)

        matches = 0
        total = 0

        for algorithm in codes1:
            if algorithm in codes2:
                total += 1
                if codes1[algorithm] == codes2[algorithm] and codes1[algorithm]:
                    matches += 1

        return matches / total if total > 0 else 0.0

    async def _create_pronunciation_guides(self):
        """Create pronunciation guides for difficult locations"""
        logger.info("🗣️ Creating pronunciation guides...")

        difficult_locations = [
            {
                "name": "DZORWULU",
                "phonetic": "ZOR-wu-lu",
                "ipa": "d͡zoɾwulu",
                "difficulty": 0.9,
                "alternatives": ["the Dzorwulu area", "near Roman Ridge", "Zor-wu-lu area"]
            },
            {
                "name": "KOKOMLEMLE",
                "phonetic": "KO-kom-lem-le",
                "ipa": "kokomlɛmle",
                "difficulty": 0.8,
                "alternatives": ["the Kokomlemle area", "Koko-lemle area", "near Achimota"]
            },
            {
                "name": "NYAMEKYE",
                "phonetic": "NYA-me-kye",
                "ipa": "njamɛkje",
                "difficulty": 0.8,
                "alternatives": ["the Nyamekye area", "Nia-mek-ye area", "near Lapaz"]
            },
            {
                "name": "KWABENYA",
                "phonetic": "KWA-ben-ya",
                "ipa": "kwabɛnja",
                "difficulty": 0.7,
                "alternatives": ["the Kwabenya area", "Kwa-ben-ya area", "near Dome"]
            },
            {
                "name": "ABELENKPE",
                "phonetic": "A-bel-en-kpe",
                "ipa": "abɛlɛnkpɛ",
                "difficulty": 0.7,
                "alternatives": ["the Abelenkpe area", "Abel-en-kpe area", "near Dzorwulu"]
            }
        ]

        created_count = 0
        for guide_data in difficult_locations:
            try:
                # Check if location exists
                location = await self.repository.get_location_by_name(guide_data["name"])
                if not location:
                    continue

                # Check if guide already exists
                existing = await self.repository.get_pronunciation_guide(guide_data["name"])
                if existing:
                    continue

                # Generate SSML
                ssml_markup = f'<speak><phoneme alphabet="ipa" ph="{guide_data["ipa"]}">{guide_data["name"]}</phoneme></speak>'

                # Calculate speech rate
                speech_rate = max(0.7, 1.0 - (guide_data["difficulty"] * 0.3))

                # Create pronunciation guide
                guide = PronunciationGuide(
                    location_name=guide_data["name"],
                    language=LanguageContext.ENGLISH,
                    phonetic_spelling=guide_data["phonetic"],
                    ipa_notation=guide_data["ipa"],
                    ssml_markup=ssml_markup,
                    alternative_descriptions=guide_data["alternatives"],
                    difficulty_score=guide_data["difficulty"],
                    recommended_speech_rate=speech_rate,
                    syllable_breaks=guide_data["phonetic"].split("-"),
                    usage_context=[ToolContext.PREMIER_HEALTH, ToolContext.VAPI]
                )

                await self.repository.create_pronunciation_guide(guide)
                created_count += 1

            except Exception as e:
                logger.error(f"Failed to create pronunciation guide for {guide_data['name']}: {e}")

        logger.info(f"✅ Created {created_count} pronunciation guides")

    async def _add_location_relationships(self):
        """Add location relationships"""
        logger.info("🔗 Adding location relationships...")

        # Common area relationships
        relationships = [
            ("ACCRA CENTRAL", "TUDU", RelationshipType.ADJACENT, 0.9),
            ("ACCRA CENTRAL", "MAKOLA", RelationshipType.CONTAINS, 0.8),
            ("OSU", "LABONE", RelationshipType.ADJACENT, 0.8),
            ("OSU", "CANTONMENTS", RelationshipType.NEARBY, 0.7),
            ("EAST LEGON", "ADJRINGANOR", RelationshipType.ADJACENT, 0.8),
            ("SPINTEX", "SAKUMONO ESTATE", RelationshipType.NEARBY, 0.7),
            ("TEMA", "ASHAIMAN", RelationshipType.NEARBY, 0.6),
            ("MADINA", "ADENTA", RelationshipType.ADJACENT, 0.7),
            ("KANESHIE", "KOKOMLEMLE", RelationshipType.ADJACENT, 0.6),
            ("DZORWULU", "ABELENKPE", RelationshipType.ADJACENT, 0.8),
        ]

        created_count = 0
        for primary, related, rel_type, strength in relationships:
            try:
                # Check if both locations exist
                primary_loc = await self.repository.get_location_by_name(primary)
                related_loc = await self.repository.get_location_by_name(related)

                if not (primary_loc and related_loc):
                    continue

                # Create relationship
                relationship = LocationRelationship(
                    primary_location=primary,
                    related_location=related,
                    relationship_type=rel_type,
                    relationship_strength=strength,
                    bidirectional=True,
                    context_notes=f"{primary} and {related} are {rel_type.value}"
                )

                await self.repository.create_location_relationship(relationship)
                created_count += 1

            except Exception as e:
                logger.error(f"Failed to create relationship {primary}-{related}: {e}")

        logger.info(f"✅ Created {created_count} location relationships")


async def main():
    """Main migration function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Get database connection
        db = await get_database()

        # Create migrator
        migrator = LocationDataMigrator(db)

        # Run migration
        csv_path = "/opt/kasaai/apps/automations/premier-health/phi_apomoden_data.csv"
        await migrator.migrate_from_csv(csv_path)

        logger.info("🎉 Migration completed successfully!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())