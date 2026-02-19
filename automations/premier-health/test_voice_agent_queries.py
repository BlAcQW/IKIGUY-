#!/usr/bin/env python3
"""
Unit tests for voice agent query fixes
Tests the enhanced specialty pattern matching and location handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from voice_agent_queries import VoiceAgentQueries

class TestVoiceAgentQueryFixes(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'kasaai_core',
            'options': '-c search_path=premier_health,public',
            'user': 'postgres',
            'password': 'aawwER44444'
        }
        self.agent = VoiceAgentQueries(self.db_config)

    def test_specialty_pattern_matching(self):
        """Test that specialty patterns correctly map user queries to database specialties"""

        # Test gynecology variations
        test_cases = [
            ("Find me a gynecologist", "Gynecology"),
            ("Find me gynecologists", "Gynecology"),
            ("I need a women's health doctor", "Gynecology"),
            ("womens health specialist", "Gynecology"),
            ("gynae doctor", "Gynecology"),
        ]

        for query, expected_specialty in test_cases:
            with self.subTest(query=query):
                intent = self.agent.extract_intent(query)
                self.assertEqual(intent['specialty'], expected_specialty,
                               f"Query '{query}' should map to '{expected_specialty}'")

    def test_pharmacy_pattern_matching(self):
        """Test pharmacy pattern variations"""
        test_cases = [
            ("Find me pharmacies", "Pharmacy"),
            ("I need a pharmacy", "Pharmacy"),
            ("Find me chemists", "Pharmacy"),
            ("where can I get medication", "Pharmacy"),
            ("pharmaceutical store", "Pharmacy"),
        ]

        for query, expected_specialty in test_cases:
            with self.subTest(query=query):
                intent = self.agent.extract_intent(query)
                self.assertEqual(intent['specialty'], expected_specialty,
                               f"Query '{query}' should map to '{expected_specialty}'")

    def test_additional_specialty_patterns(self):
        """Test other enhanced specialty patterns"""
        test_cases = [
            ("eye doctor", "Ophthalmology"),
            ("ophthalmologist", "Ophthalmology"),
            ("pediatrician", "Pediatrics"),
            ("paediatric doctor", "Pediatrics"),
            ("obstetrician", "Obs"),
            ("maternity doctor", "Obs"),
            ("dermatologist", "Derm"),
            ("skin doctor", "Derm"),
            ("surgeon", "Surg"),
            ("urologist", "Urology"),
            ("neurologist", "Neu"),
            ("dietitian", "Diet"),
            ("laboratory", "Laboratory"),
            ("diagnostic center", "Laboratory"),
            ("ultrasound", "Scan"),
        ]

        for query, expected_specialty in test_cases:
            with self.subTest(query=query):
                intent = self.agent.extract_intent(query)
                self.assertEqual(intent['specialty'], expected_specialty,
                               f"Query '{query}' should map to '{expected_specialty}'")

    def test_location_extraction(self):
        """Test location extraction from queries"""
        test_cases = [
            ("Find me a doctor in Accra", "Accra"),
            ("pharmacy near Madina", "Madina"),
            ("gynecologist at East Legon", "East Legon"),
            ("hospital around Circle", "Circle"),
        ]

        for query, expected_location in test_cases:
            with self.subTest(query=query):
                intent = self.agent.extract_intent(query)
                self.assertEqual(intent['location'], expected_location,
                               f"Query '{query}' should extract location '{expected_location}'")

    def test_compound_queries(self):
        """Test queries with both specialty and location"""
        test_cases = [
            ("Find me a gynecologist in Madina", "Gynecology", "Madina"),
            ("pharmacy near East Legon", "Pharmacy", "East Legon"),
            ("eye doctor in Circle area", "Ophthalmology", "Circle"),
        ]

        for query, expected_specialty, expected_location in test_cases:
            with self.subTest(query=query):
                intent = self.agent.extract_intent(query)
                self.assertEqual(intent['specialty'], expected_specialty,
                               f"Query '{query}' should extract specialty '{expected_specialty}'")
                self.assertEqual(intent['location'], expected_location,
                               f"Query '{query}' should extract location '{expected_location}'")

    @patch('voice_agent_queries.psycopg2.connect')
    def test_suggestions_for_invalid_location(self, mock_connect):
        """Test that helpful suggestions are provided for invalid locations"""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Mock no similar areas found
        mock_cursor.fetchall.return_value = []

        # Test with invalid location
        intent = {'location': 'Nonexistent', 'specialty': 'Pharmacy', 'emergency': False}
        suggestions = self.agent._generate_suggestions([], intent, "pharmacy in Nonexistent")

        self.assertTrue(any("popular areas like Madina, East Legon, or Circle" in s for s in suggestions),
                       "Should suggest popular areas when location not found")

    @patch('voice_agent_queries.psycopg2.connect')
    def test_suggestions_with_similar_areas(self, mock_connect):
        """Test suggestions when similar areas are found"""
        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None

        # Mock similar areas found
        mock_cursor.fetchall.return_value = [
            {'area': 'East Legon', 'provider_count': 10},
            {'area': 'Legon', 'provider_count': 5}
        ]

        # Test with partial location match
        intent = {'location': 'Leg', 'specialty': 'Pharmacy', 'emergency': False}
        suggestions = self.agent._generate_suggestions([], intent, "pharmacy in Leg")

        self.assertTrue(any("East Legon, Legon" in s for s in suggestions),
                       "Should suggest similar areas when found")

    def test_intent_extraction_edge_cases(self):
        """Test edge cases in intent extraction"""
        # Test empty/minimal queries
        test_cases = [
            ("", None, None),
            ("doctor", None, None),
            ("help", None, None),
            ("find", None, None),
        ]

        for query, expected_specialty, expected_location in test_cases:
            with self.subTest(query=query):
                intent = self.agent.extract_intent(query)
                self.assertEqual(intent['specialty'], expected_specialty)
                self.assertEqual(intent['location'], expected_location)

    def test_emergency_detection(self):
        """Test emergency keyword detection"""
        emergency_queries = [
            "emergency hospital",
            "urgent care",
            "need help now",
            "accident hospital"
        ]

        for query in emergency_queries:
            with self.subTest(query=query):
                intent = self.agent.extract_intent(query)
                self.assertTrue(intent['emergency'], f"Query '{query}' should be detected as emergency")

    def test_provider_type_detection(self):
        """Test provider type detection"""
        test_cases = [
            ("find hospital", "hospital"),
            ("clinic near me", "clinic"),
            ("pharmacy location", "pharmacy"),
        ]

        for query, expected_type in test_cases:
            with self.subTest(query=query):
                intent = self.agent.extract_intent(query)
                self.assertEqual(intent['provider_type'], expected_type,
                               f"Query '{query}' should detect provider type '{expected_type}'")

class TestIntegrationFixes(unittest.TestCase):
    """Integration tests to verify the complete fix works with real database patterns"""

    def setUp(self):
        """Set up test fixtures"""
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'kasaai_core',
            'options': '-c search_path=premier_health,public',
            'user': 'postgres',
            'password': 'aawwER44444'
        }
        self.agent = VoiceAgentQueries(self.db_config)

    def test_previously_failing_queries(self):
        """Test queries that were failing before the fix"""
        # These are the actual queries from the failed transcript
        previously_failing = [
            "Find me gynecologists",
            "Find me pharmacies",
            "I need a gynecologist",
            "pharmacy near me"
        ]

        for query in previously_failing:
            with self.subTest(query=query):
                # These should now work and return results
                result = self.agent.search_providers(query, max_results=3)

                # Should extract specialty correctly
                intent = self.agent.extract_intent(query)
                expected_specialties = ['Gynecology', 'Pharmacy']

                if any(spec in query.lower() for spec in ['gynec', 'women']):
                    self.assertEqual(intent['specialty'], 'Gynecology')
                elif 'pharmac' in query.lower():
                    self.assertEqual(intent['specialty'], 'Pharmacy')

                # Should have confidence > 0 if results found
                if result.providers:
                    self.assertGreater(result.confidence, 0.0)
                    self.assertGreater(result.total_found, 0)

    def test_location_not_found_handling(self):
        """Test handling of non-existent locations"""
        queries_with_invalid_locations = [
            "Find me a gynecologist near Whitesmith",
            "Find me pharmacies near bankers"
        ]

        for query in queries_with_invalid_locations:
            with self.subTest(query=query):
                result = self.agent.search_providers(query, max_results=3)

                # Should extract intent correctly even if location doesn't exist
                intent = self.agent.extract_intent(query)
                self.assertIsNotNone(intent['specialty'])
                self.assertIsNotNone(intent['location'])

                # Should provide helpful suggestions
                self.assertTrue(len(result.suggested_refinements) > 0)
                suggestions_text = ' '.join(result.suggested_refinements)
                self.assertTrue('popular areas' in suggestions_text.lower() or
                              'try searching' in suggestions_text.lower())

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)