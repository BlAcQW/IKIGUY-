#!/usr/bin/env python3
"""
Area mapping and location normalization for healthcare provider search
Handles common area name variations and aliases for better voice query matching
"""

import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

class AreaMapper:
    def __init__(self):
        # Known area aliases and common names
        self.area_aliases = {
            # Main areas with their common aliases
            'MADINA': ['MADINA / ADENTA / DODOWA', 'ADENTA', 'DODOWA'],
            'ADENTA': ['MADINA / ADENTA / DODOWA', 'MADINA', 'DODOWA'],
            'DODOWA': ['MADINA / ADENTA / DODOWA', 'MADINA', 'ADENTA'],

            'ACCRA CENTRAL': ['ACCRA CENTRAL / TUDU / MAKOLA', 'TUDU', 'MAKOLA', 'CENTRAL ACCRA', 'TOWN'],
            'TUDU': ['ACCRA CENTRAL / TUDU / MAKOLA', 'ACCRA CENTRAL', 'MAKOLA'],
            'MAKOLA': ['ACCRA CENTRAL / TUDU / MAKOLA', 'ACCRA CENTRAL', 'TUDU', 'MAKOLA MARKET'],

            'CIRCLE': ['CIRCLE / KANESHIE / NORTH KANESHIE / INDUSTRIAL AREA', 'KANESHIE', 'NORTH KANESHIE', 'INDUSTRIAL AREA'],
            'KANESHIE': ['CIRCLE / KANESHIE / NORTH KANESHIE / INDUSTRIAL AREA', 'CIRCLE', 'NORTH KANESHIE', 'INDUSTRIAL AREA'],
            'NORTH KANESHIE': ['CIRCLE / KANESHIE / NORTH KANESHIE / INDUSTRIAL AREA', 'CIRCLE', 'KANESHIE', 'INDUSTRIAL AREA'],
            'INDUSTRIAL AREA': ['CIRCLE / KANESHIE / NORTH KANESHIE / INDUSTRIAL AREA', 'CIRCLE', 'KANESHIE', 'NORTH KANESHIE'],

            'AIRPORT': ['AIRPORT RESIDENTIAL AREA / 37 AREA', '37 AREA', 'AIRPORT RESIDENTIAL', 'KOTOKA'],
            '37 AREA': ['AIRPORT RESIDENTIAL AREA / 37 AREA', 'AIRPORT', 'AIRPORT RESIDENTIAL AREA'],
            'AIRPORT RESIDENTIAL AREA': ['AIRPORT RESIDENTIAL AREA / 37 AREA', '37 AREA', 'AIRPORT'],

            'LAPAZ': ['LAPAZ / NYAMEKYE / DARKUMAN / ODORKOR', 'NYAMEKYE', 'DARKUMAN', 'ODORKOR'],
            'NYAMEKYE': ['LAPAZ / NYAMEKYE / DARKUMAN / ODORKOR', 'LAPAZ', 'DARKUMAN', 'ODORKOR'],
            'DARKUMAN': ['LAPAZ / NYAMEKYE / DARKUMAN / ODORKOR', 'LAPAZ', 'NYAMEKYE', 'ODORKOR'],
            'ODORKOR': ['LAPAZ / NYAMEKYE / DARKUMAN / ODORKOR', 'LAPAZ', 'NYAMEKYE', 'DARKUMAN'],

            'KOKOMLEMLE': ['KOKOMLEMLE / MAAMOBI / NIMA', 'MAAMOBI', 'NIMA'],
            'MAAMOBI': ['KOKOMLEMLE / MAAMOBI / NIMA', 'KOKOMLEMLE', 'NIMA'],
            'NIMA': ['KOKOMLEMLE / MAAMOBI / NIMA', 'KOKOMLEMLE', 'MAAMOBI'],

            'LEGON': ['LEGON & NORTH LEGON', 'NORTH LEGON', 'UG', 'UNIVERSITY OF GHANA'],
            'NORTH LEGON': ['LEGON & NORTH LEGON', 'LEGON'],

            'DZORWULU': ['DZORWULU & ABELENKPE', 'ABELENKPE'],
            'ABELENKPE': ['DZORWULU & ABELENKPE', 'DZORWULU'],

            # Standalone areas
            'ADABRAKA': ['ADABRAKA'],
            'ASYLUM DOWN': ['ASYLUM DOWN', 'ASYLUM'],
        }

        # Common area aliases that don't exist in our database but users might search for
        self.external_aliases = {
            'TESANO': ['KOKOMLEMLE / MAAMOBI / NIMA'],  # Tesano is near Kokomlemle
            'KORLE-BU': ['ADABRAKA'],  # Korle-Bu is near Adabraka
            'KORLEBU': ['ADABRAKA'],
            'DANSOMAN': ['LAPAZ / NYAMEKYE / DARKUMAN / ODORKOR'],  # Dansoman is in this general area
            'TEMA': ['MADINA / ADENTA / DODOWA'],  # Tema is east, similar to Adenta area
            'SPINTEX': ['MADINA / ADENTA / DODOWA'],  # Spintex road area
            'EAST LEGON': ['LEGON & NORTH LEGON'],
            'WEIJA': ['LAPAZ / NYAMEKYE / DARKUMAN / ODORKOR'],
            'MALLAM': ['LAPAZ / NYAMEKYE / DARKUMAN / ODORKOR'],
            'ACHIMOTA': ['KOKOMLEMLE / MAAMOBI / NIMA'],
            'DOME': ['KOKOMLEMLE / MAAMOBI / NIMA'],
            'HAATSO': ['MADINA / ADENTA / DODOWA'],
            'PANTANG': ['MADINA / ADENTA / DODOWA'],
            'KWABENYA': ['MADINA / ADENTA / DODOWA'],
            'ASHONGMAN': ['MADINA / ADENTA / DODOWA'],
            'ROMAN RIDGE': ['DZORWULU & ABELENKPE'],
            'LABONE': ['AIRPORT RESIDENTIAL AREA / 37 AREA'],
            'OSU': ['AIRPORT RESIDENTIAL AREA / 37 AREA'],
            'TESHIE': ['MADINA / ADENTA / DODOWA'],
            'NUNGUA': ['MADINA / ADENTA / DODOWA'],
            'KASOA': ['LAPAZ / NYAMEKYE / DARKUMAN / ODORKOR'],  # Western area
        }

        # STT (Speech-to-Text) misheard location aliases
        self.stt_aliases = {
            # === ASHANTI REGION (NOW COVERED) ===
            'KUMASI': ['KUMASI'],
            'COMASSIE': ['KUMASI'],  # STT mishearing of Kumasi
            'COMASIE': ['KUMASI'],  # STT variant
            'KUMASE': ['KUMASI'],  # STT variant
            'ASAFO': ['ASAFO'],
            'ASA': ['ASAFO'],  # Abbreviation for Asafo
            'OBUASI': ['OBUASI'],
            'MAMPONG': ['MAMPONTENG'],
            'BEKWAI': ['BEKWAI'],
            'ASHANTI': ['KUMASI'],  # Default to capital
            'BOMSO': ['BOMSO'],
            'KNUST': ['KNUST'],
            'EJISU': ['EJISU'],
            'ASOKWA': ['ASOKWA'],
            'BANTAMA': ['BANTAMA'],
            'ABREPO': ['ABREPO'],
            'TAFO': ['TAFO'],
            'BREMANG': ['BREMANG'],
            'MAMPONTENG': ['MAMPONTENG'],
            'ABUAKWA': ['ABUAKWA'],
            'SANTASI': ['SANTASI'],
            'SUNTRESO': ['SUNTRESO'],
            'AYEDUASE': ['AYEDUASE'],
            'OFORIKROM': ['OFORIKROM'],
            'MANHYIA': ['MANHYIA'],
            'KOTEI': ['KOTEI'],
            'ADUM': ['ADUM'],
            'FOMENA': ['FOMENA'],
            'JUABEN': ['JUABEN'],
            'KONONGO': ['KONONGO'],
            'KENYASI': ['KENYASI'],
            'MANSO NKWANTA': ['MANSO NKWANTA'],

            # === NORTHERN REGIONS (NOW COVERED) ===
            'TAMALE': ['TAMALE'],
            'BOLGATANGA': ['BOLGATANGA'],
            'WA': ['WA'],
            'BAWKU': ['BAWKU'],
            'NORTHERN': ['TAMALE'],  # Default to capital
            'NAVRONGO': ['NAVRONGO'],
            'LAWRA': ['LAWRA'],

            # === WESTERN REGION (NOW COVERED) ===
            'TAKORADI': ['TAKORADI'],
            'SEKONDI': ['SEKONDI'],
            'TARKWA': ['TARKWA'],
            'WESTERN': ['TAKORADI'],  # Default to capital
            'SAMREBOI': ['SAMREBOI'],
            'TAKORADI MARKET CIRCLE': ['TAKORADI MARKET CIRCLE'],
            'APOWA': ['APOWA'],
            'EFFIAKUMA': ['EFFIAKUMA'],

            # === EASTERN & VOLTA REGIONS (NOW COVERED) ===
            'KOFORIDUA': ['KOFORIDUA'],
            'HO': ['HO'],
            'HOHOE': ['HOHOE'],
            'EASTERN': ['KOFORIDUA'],  # Default to capital
            'VOLTA': ['HO'],  # Default to capital
            'NKAWKAW': ['NKAWKAW'],
            'BEPONG': ['BEPONG'],
            'NKWANTA': ['NKWANTA'],
            'SAKARIGA': ['SAKARIGA'],
            'AGOGO': ['AGOGO'],
            'KPASSA': ['KPASSA'],
            'SUHUM': ['SUHUM'],
            'DONKORKROM': ['DONKORKROM'],
            'KWABRE': ['KWABRE'],
            'TROM': ['TROM'],

            # === BONO REGIONS (NOW COVERED) ===
            'SUNYANI': ['SUNYANI'],
            'TECHIMAN': ['TECHIMAN'],
            'BEREKUM': ['BEREKUM'],
            'BONO': ['SUNYANI'],  # Default to capital
            'WENCHI': ['WENCHI'],
            'KINTAMPO': ['KINTAMPO'],
            'ATEBUBU': ['ATEBUBU'],
            'DROBO': ['DROBO'],
            'DUAYAW NKWANTA': ['DUAYAW NKWANTA'],

            # === CENTRAL REGION (NOW COVERED) ===
            'CAPE COAST': ['CAPE COAST'],
            'CENTRAL': ['CAPE COAST'],  # Default to capital

            # Potential mishearing of actual areas
            'MEDINA': ['MADINA / ADENTA / DODOWA'],  # Medina -> Madina
            'MADONNA': ['MADINA / ADENTA / DODOWA'],  # Madonna -> Madina
            'MODERNA': ['MADINA / ADENTA / DODOWA'],  # Moderna -> Madina
            'MARINA': ['MADINA / ADENTA / DODOWA'],  # Marina -> Madina

            'CIRCUS': ['CIRCLE / KANESHIE / NORTH KANESHIE / INDUSTRIAL AREA'],  # Circus -> Circle
            'CIRCLE-E': ['CIRCLE / KANESHIE / NORTH KANESHIE / INDUSTRIAL AREA'],  # Circle-E -> Circle

            'ASYLUM': ['ASYLUM DOWN'],  # Short form
            'ASYLUMDOWN': ['ASYLUM DOWN'],  # No space

            'AIRPORT': ['AIRPORT RESIDENTIAL AREA / 37 AREA'],  # Short form
            'KOTOKA': ['AIRPORT RESIDENTIAL AREA / 37 AREA'],  # Airport name

            # Known problem areas from user feedback
            'WHITESMITH': [],  # Not a real area - will suggest alternatives
            'WHITE SMITH': [],
            'BANKERS': [],  # Not a real area - will suggest alternatives
            'BANKER': [],
        }

        # Combine all mappings
        self.all_mappings = {**self.area_aliases, **self.external_aliases, **self.stt_aliases}

        # Create reverse mapping for faster lookup
        self.db_area_to_components = {}
        for db_area in set().union(*self.area_aliases.values()):
            if '/' in db_area or '&' in db_area:
                components = []
                for sep in ['/', '&']:
                    if sep in db_area:
                        components = [comp.strip() for comp in db_area.split(sep)]
                        break
                self.db_area_to_components[db_area] = components

    def normalize_location(self, location: str) -> Optional[str]:
        """
        Normalize a location string to match database area names

        Args:
            location (str): User input location

        Returns:
            Optional[str]: Matching database area name or None
        """
        if not location:
            return None

        location_upper = location.upper().strip()

        # Direct match in our mappings
        if location_upper in self.all_mappings:
            # Return the first (primary) database area
            return self.all_mappings[location_upper][0]

        # Partial match - check if location is contained in any area name
        for db_area in self.db_area_to_components:
            if location_upper in db_area.upper():
                return db_area

        # Fuzzy matching with similarity threshold
        best_match = None
        best_score = 0.0

        for alias, db_areas in self.all_mappings.items():
            similarity = SequenceMatcher(None, location_upper, alias).ratio()
            if similarity > best_score and similarity > 0.7:  # 70% similarity threshold
                best_match = db_areas[0]
                best_score = similarity

        return best_match

    def get_area_suggestions(self, location: str) -> List[str]:
        """
        Get multiple area suggestions for a location

        Args:
            location (str): User input location

        Returns:
            List[str]: List of possible database area matches
        """
        if not location:
            return []

        location_upper = location.upper().strip()
        suggestions = []

        # Direct matches
        if location_upper in self.all_mappings:
            suggestions.extend(self.all_mappings[location_upper])

        # Partial matches
        for db_area in self.db_area_to_components:
            if location_upper in db_area.upper() and db_area not in suggestions:
                suggestions.append(db_area)

        # Fuzzy matches
        for alias, db_areas in self.all_mappings.items():
            similarity = SequenceMatcher(None, location_upper, alias).ratio()
            if similarity > 0.6:  # Lower threshold for suggestions
                for area in db_areas:
                    if area not in suggestions:
                        suggestions.append(area)

        return suggestions[:5]  # Limit to top 5 suggestions

    def expand_location_search(self, location: str) -> List[str]:
        """
        Expand a location search to include related areas

        Args:
            location (str): User input location

        Returns:
            List[str]: List of areas to search (for OR conditions)
        """
        suggestions = self.get_area_suggestions(location)
        if not suggestions:
            # If no suggestions, try the original location
            return [location]
        return suggestions

# Example usage and testing
if __name__ == "__main__":
    mapper = AreaMapper()

    test_locations = [
        'Tesano', 'Korle-Bu', 'Dansoman', 'Madina', 'Circle',
        'East Legon', 'Achimota', 'Airport', 'Tema'
    ]

    print("=== AREA MAPPING TEST ===")
    for location in test_locations:
        normalized = mapper.normalize_location(location)
        suggestions = mapper.get_area_suggestions(location)
        expanded = mapper.expand_location_search(location)

        print(f"\nLocation: {location}")
        print(f"  Normalized: {normalized}")
        print(f"  Suggestions: {suggestions}")
        print(f"  Expanded: {expanded}")