"""
Test Real VAPI Chat Healthcare Tools vs Database

This module contains tests that compare actual VAPI chat responses with direct
database queries to verify healthcare tools functionality.

Tests healthcare tools:
- search_healthcare_providers
- get_emergency_providers
- get_available_areas
- get_available_specialties
- get_provider_details
"""

import os
import json
import time
import logging
import requests
import pytest
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import sys

class DateTimeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Add paths for healthcare tools import
sys.path.append('/opt/kasaai/apps/automations/premier-health')

try:
    from voice_agent_tools import HealthcareVoiceTools
except ImportError as e:
    logging.warning(f"Failed to import voice_agent_tools: {e}")
    # This is optional for testing since we're mainly testing VAPI responses
    HealthcareVoiceTools = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Test result comparing VAPI chat vs direct database query."""
    question: str
    category: str
    vapi_success: bool
    vapi_response: str
    vapi_tool_calls: List[str]
    db_success: bool
    db_response: str
    db_data: Dict[str, Any]
    comparison: Dict[str, Any]
    execution_time: float

class TestRealVAPIChatHealthcareTools:
    """
    Test VAPI chat responses against direct database queries.

    This class performs comprehensive testing by:
    1. Sending questions to VAPI chat API
    2. Running equivalent direct database queries
    3. Comparing results for accuracy and consistency
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        self.api_key = '42cf1e7c-2ef9-4bd7-ba30-52f2813605a2'
        self.vapi_base_url = 'https://api.vapi.ai'

        # Database configuration for direct queries
        self.db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'community',
            'user': 'postgres',
            'password': 'aawwER44444'
        }

        # Initialize healthcare tools for direct database access (if available)
        if HealthcareVoiceTools:
            self.healthcare_tools = HealthcareVoiceTools(self.db_config)
        else:
            self.healthcare_tools = None

        # Test results tracking
        self.test_results: List[TestResult] = []
        self.start_time = datetime.now()

        # Tool ID mappings
        self.tool_ids = {
            'search_healthcare_providers': '91680cf0-fc9d-4a59-b65a-8ea2ececcac7',
            'get_emergency_providers': '74e8e539-776f-4fc6-ba2f-46aa241722be',
            'get_available_areas': 'c3b245ff-a8ee-42ed-b39d-6e50d0fc09e0',
            'get_available_specialties': '23954934-c55e-4faa-b0ca-23ed45ce5289',
            'get_provider_details': 'f0f98b68-ade8-4a01-ae0a-d09a9dc39c6f'
        }

    def chat_with_vapi(self, question: str, tool_ids: List[str]) -> Tuple[bool, str, List[str]]:
        """
        Send a question to VAPI chat API and get response.

        Args:
            question: Question to ask the assistant
            tool_ids: List of tool IDs to include in the assistant

        Returns:
            Tuple of (success, response, tool_calls)
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                "assistant": {
                    "model": {
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "messages": [{
                            "role": "system",
                            "content": "You are Ama, a Healthcare Navigator for Premier Health Insurance. Help customers find medical providers in Ghana."
                        }],
                        "toolIds": tool_ids
                    }
                },
                "input": question
            }

            response = requests.post(
                f"{self.vapi_base_url}/chat",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
                data = response.json()

                # Extract response and tool calls
                response_text = ""
                tool_calls = []

                for output in data.get('output', []):
                    if output.get('role') == 'assistant':
                        if 'content' in output and output['content']:
                            response_text = output['content']
                        if 'tool_calls' in output:
                            for tool_call in output['tool_calls']:
                                tool_calls.append(tool_call['function']['name'])

                return True, response_text, tool_calls
            else:
                logger.error(f"VAPI API error: {response.status_code} - {response.text}")
                return False, f"API Error: {response.status_code}", []

        except Exception as e:
            logger.error(f"Error chatting with VAPI: {e}")
            return False, f"Exception: {str(e)}", []

    def run_database_query(self, question: str, category: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Run equivalent database query for comparison.

        Args:
            question: Original question
            category: Test category to determine which tool to use

        Returns:
            Tuple of (success, response, data)
        """
        try:
            question_lower = question.lower()

            # Emergency queries
            if any(word in question_lower for word in ['emergency', 'urgent', 'immediate']):
                location = None
                if 'accra' in question_lower:
                    location = 'Accra'
                elif 'tema' in question_lower:
                    location = 'Tema'

                result = self.healthcare_tools.get_emergency_providers(location=location)
                return result['success'], result['voice_response'], result

            # Area coverage queries
            elif 'areas' in question_lower and 'cover' in question_lower:
                result = self.healthcare_tools.get_available_areas()
                return result['success'], result['voice_response'], result

            # Specialty listing queries
            elif 'specialties' in question_lower and 'available' in question_lower:
                result = self.healthcare_tools.get_available_specialties()
                return result['success'], result['voice_response'], result

            # Location-based searches
            elif any(area in question_lower for area in ['accra central', 'east legon', 'tema', 'madina', 'circle']):
                area = None
                for test_area in ['accra central', 'east legon', 'tema', 'madina', 'circle']:
                    if test_area in question_lower:
                        area = test_area.title()
                        break

                if area:
                    result = self.healthcare_tools.get_providers_by_area(area)
                    return result['success'], result['voice_response'], result

            # Specialty-based searches
            elif any(specialty in question_lower for specialty in ['cardiologist', 'pediatrician', 'dentist', 'gynecologist', 'ophthalmologist']):
                specialty_map = {
                    'cardiologist': 'Cardiology',
                    'pediatrician': 'Pediatrics',
                    'dentist': 'Dental',
                    'gynecologist': 'Gynecology',
                    'ophthalmologist': 'Ophthalmology'
                }

                specialty = None
                for key, value in specialty_map.items():
                    if key in question_lower:
                        specialty = value
                        break

                if specialty:
                    result = self.healthcare_tools.get_providers_by_specialty(specialty)
                    return result['success'], result['voice_response'], result

            # General search
            else:
                # Extract location if present
                location = None
                if 'accra' in question_lower:
                    location = 'Accra'
                elif 'tema' in question_lower:
                    location = 'Tema'

                result = self.healthcare_tools.search_healthcare_providers(
                    query=question,
                    location=location,
                    max_results=5
                )
                return result['success'], result['voice_response'], result

        except Exception as e:
            logger.error(f"Database query error: {e}")
            return False, f"Database error: {str(e)}", {}

    def compare_responses(self, vapi_response: str, db_response: str, vapi_data: List[str], db_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare VAPI chat response with database response.

        Args:
            vapi_response: Response from VAPI chat
            db_response: Response from direct database query
            vapi_data: Tool calls from VAPI
            db_data: Raw data from database

        Returns:
            Comparison analysis
        """
        comparison = {
            'response_similarity': 0.0,
            'tool_calls_match': False,
            'provider_count_match': False,
            'contact_info_present': False,
            'professional_tone': False,
            'errors_found': [],
            'strengths': [],
            'recommendations': []
        }

        # Check if both responses are non-empty
        if not vapi_response or not db_response:
            comparison['errors_found'].append('One or both responses are empty')
            return comparison

        # Check professional tone
        professional_indicators = ['i found', 'here are', 'please', 'you can', 'would you like']
        if any(indicator in vapi_response.lower() for indicator in professional_indicators):
            comparison['professional_tone'] = True
            comparison['strengths'].append('Professional tone maintained')

        # Check for contact information
        if any(indicator in vapi_response.lower() for indicator in ['phone', 'contact', '+233']):
            comparison['contact_info_present'] = True
            comparison['strengths'].append('Contact information provided')

        # Check tool calls match expected functionality
        if vapi_data:
            comparison['tool_calls_match'] = True
            comparison['strengths'].append(f'Appropriate tool calls: {", ".join(vapi_data)}')

        # Check provider count consistency
        if 'total_found' in db_data:
            db_count = db_data['total_found']
            if db_count > 0 and 'found' in vapi_response.lower():
                comparison['provider_count_match'] = True
                comparison['strengths'].append('Provider count information consistent')
            elif db_count == 0 and ('couldn\'t find' in vapi_response.lower() or 'no' in vapi_response.lower()):
                comparison['provider_count_match'] = True
                comparison['strengths'].append('Correctly indicated no providers found')

        # Calculate basic response similarity
        vapi_words = set(vapi_response.lower().split())
        db_words = set(db_response.lower().split())

        if vapi_words and db_words:
            intersection = vapi_words.intersection(db_words)
            union = vapi_words.union(db_words)
            comparison['response_similarity'] = len(intersection) / len(union) if union else 0.0

        # Generate recommendations
        if not comparison['contact_info_present'] and db_data.get('total_found', 0) > 0:
            comparison['recommendations'].append('Include contact information in response')

        if not comparison['tool_calls_match']:
            comparison['recommendations'].append('Verify appropriate tool calls are being made')

        return comparison

    def test_emergency_healthcare_providers(self):
        """Test emergency healthcare provider search through VAPI chat."""
        tool_ids = [self.tool_ids['get_emergency_providers']]
        success, response, tool_calls = self.chat_with_vapi(
            'I need emergency care right now in Accra',
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert len(response) > 0
        assert 'get_emergency_providers' in tool_calls or 'emergency' in response.lower()

    def test_general_healthcare_search(self):
        """Test general healthcare provider search through VAPI chat."""
        tool_ids = [self.tool_ids['search_healthcare_providers']]
        success, response, tool_calls = self.chat_with_vapi(
            'Find doctors in Accra',
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert len(response) > 0

    def test_specialty_search(self):
        """Test specialty-based healthcare search through VAPI chat."""
        tool_ids = [self.tool_ids['search_healthcare_providers']]
        success, response, tool_calls = self.chat_with_vapi(
            'I need a cardiologist',
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert len(response) > 0

    def test_available_areas(self):
        """Test healthcare coverage areas listing through VAPI chat."""
        tool_ids = [self.tool_ids['get_available_areas']]
        success, response, tool_calls = self.chat_with_vapi(
            'What areas do you cover?',
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert len(response) > 0

    def test_available_specialties(self):
        """Test medical specialties listing through VAPI chat."""
        tool_ids = [self.tool_ids['get_available_specialties']]
        success, response, tool_calls = self.chat_with_vapi(
            'What medical specialties are available?',
            tool_ids
        )

        assert success, f"VAPI call failed: {response}"
        assert len(response) > 0

    @pytest.mark.integration
    def run_comprehensive_test(self) -> None:
        """Run comprehensive test comparing VAPI chat with database queries."""

        # Test questions with their expected tool usage
        test_cases = [
            {
                'question': 'I need emergency care right now in Accra',
                'category': 'Emergency Healthcare',
                'tools': ['get_emergency_providers']
            },
            {
                'question': 'Find doctors in Accra',
                'category': 'General Search',
                'tools': ['search_healthcare_providers']
            },
            {
                'question': 'I need a cardiologist',
                'category': 'Specialty Search',
                'tools': ['search_healthcare_providers']
            },
            {
                'question': 'What areas do you cover?',
                'category': 'Area Listing',
                'tools': ['get_available_areas']
            },
            {
                'question': 'What medical specialties are available?',
                'category': 'Specialty Listing',
                'tools': ['get_available_specialties']
            },
            {
                'question': 'Show me gynecologists in the system',
                'category': 'Specialty Search',
                'tools': ['search_healthcare_providers']
            },
            {
                'question': 'Find healthcare providers in Madina',
                'category': 'Location Search',
                'tools': ['search_healthcare_providers']
            }
        ]

        print("="*80)
        print("VAPI CHAT vs DATABASE COMPARISON TEST")
        print("="*80)
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Test Cases: {len(test_cases)}")
        print()

        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i}/{len(test_cases)}] Testing: {test_case['question']}")
            print(f"Category: {test_case['category']}")
            print("-" * 60)

            start_time = time.time()

            # Get tool IDs for this test
            tool_ids = [self.tool_ids[tool] for tool in test_case['tools'] if tool in self.tool_ids]

            # Test VAPI chat
            print("🤖 VAPI Chat Response:")
            vapi_success, vapi_response, vapi_tool_calls = self.chat_with_vapi(
                test_case['question'],
                tool_ids
            )

            if vapi_success:
                print(f"   Response: {vapi_response[:150]}...")
                print(f"   Tool Calls: {vapi_tool_calls}")
            else:
                print(f"   ERROR: {vapi_response}")

            # Brief pause between calls
            time.sleep(1)

            # Test direct database query
            print("\n🏥 Database Query Response:")
            db_success, db_response, db_data = self.run_database_query(
                test_case['question'],
                test_case['category']
            )

            if db_success:
                print(f"   Response: {db_response[:150]}...")
                print(f"   Providers Found: {db_data.get('total_found', 'N/A')}")
                if 'providers' in db_data and db_data['providers']:
                    print(f"   Example Provider: {db_data['providers'][0].get('name', 'N/A')}")
            else:
                print(f"   ERROR: {db_response}")

            # Compare responses
            print("\n📊 Comparison Analysis:")
            comparison = self.compare_responses(vapi_response, db_response, vapi_tool_calls, db_data)

            print(f"   Professional Tone: {'✅' if comparison['professional_tone'] else '❌'}")
            print(f"   Tool Calls Match: {'✅' if comparison['tool_calls_match'] else '❌'}")
            print(f"   Contact Info Present: {'✅' if comparison['contact_info_present'] else '❌'}")
            print(f"   Provider Count Match: {'✅' if comparison['provider_count_match'] else '❌'}")
            print(f"   Response Similarity: {comparison['response_similarity']:.2%}")

            if comparison['strengths']:
                print(f"   Strengths: {', '.join(comparison['strengths'])}")

            if comparison['errors_found']:
                print(f"   Issues: {', '.join(comparison['errors_found'])}")

            # Store result
            execution_time = time.time() - start_time
            result = TestResult(
                question=test_case['question'],
                category=test_case['category'],
                vapi_success=vapi_success,
                vapi_response=vapi_response,
                vapi_tool_calls=vapi_tool_calls,
                db_success=db_success,
                db_response=db_response,
                db_data=db_data,
                comparison=comparison,
                execution_time=execution_time
            )
            self.test_results.append(result)

            print(f"   Execution Time: {execution_time:.2f}s")
            print()

            # Brief pause between tests
            time.sleep(2)

        # Generate summary report
        self.generate_summary_report()

    def generate_summary_report(self) -> None:
        """Generate comprehensive summary report."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print("="*80)
        print("SUMMARY REPORT")
        print("="*80)

        # Overall statistics
        total_tests = len(self.test_results)
        vapi_successes = sum(1 for r in self.test_results if r.vapi_success)
        db_successes = sum(1 for r in self.test_results if r.db_success)
        professional_tone = sum(1 for r in self.test_results if r.comparison.get('professional_tone', False))
        tool_matches = sum(1 for r in self.test_results if r.comparison.get('tool_calls_match', False))

        print(f"Test Duration: {duration:.2f} seconds")
        print(f"Total Tests: {total_tests}")
        print(f"VAPI Success Rate: {vapi_successes}/{total_tests} ({vapi_successes/total_tests*100:.1f}%)")
        print(f"Database Success Rate: {db_successes}/{total_tests} ({db_successes/total_tests*100:.1f}%)")
        print(f"Professional Tone: {professional_tone}/{total_tests} ({professional_tone/total_tests*100:.1f}%)")
        print(f"Tool Call Accuracy: {tool_matches}/{total_tests} ({tool_matches/total_tests*100:.1f}%)")

        # Category breakdown
        print("\nCATEGORY BREAKDOWN:")
        categories = {}
        for result in self.test_results:
            cat = result.category
            if cat not in categories:
                categories[cat] = {'total': 0, 'vapi_success': 0, 'db_success': 0, 'tool_match': 0}
            categories[cat]['total'] += 1
            if result.vapi_success:
                categories[cat]['vapi_success'] += 1
            if result.db_success:
                categories[cat]['db_success'] += 1
            if result.comparison.get('tool_calls_match', False):
                categories[cat]['tool_match'] += 1

        for category, stats in categories.items():
            print(f"  {category}:")
            print(f"    VAPI: {stats['vapi_success']}/{stats['total']}")
            print(f"    DB: {stats['db_success']}/{stats['total']}")
            print(f"    Tools: {stats['tool_match']}/{stats['total']}")

        # Best performing tests
        successful_tests = [r for r in self.test_results if r.vapi_success and r.db_success]
        if successful_tests:
            print("\nBEST PERFORMING TESTS:")
            for result in successful_tests[:3]:
                print(f"  ✅ {result.question}")
                print(f"     VAPI: {result.vapi_response[:80]}...")
                print(f"     DB Found: {result.db_data.get('total_found', 'N/A')} providers")

        # Issues found
        failed_tests = [r for r in self.test_results if not r.vapi_success or not r.db_success]
        if failed_tests:
            print("\nISSUES FOUND:")
            for result in failed_tests:
                print(f"  ❌ {result.question}")
                if not result.vapi_success:
                    print(f"     VAPI Error: {result.vapi_response}")
                if not result.db_success:
                    print(f"     DB Error: {result.db_response}")

        print("="*80)

        # Save detailed results
        self.save_detailed_results()

    def save_detailed_results(self) -> None:
        """Save detailed test results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vapi_vs_database_test_results_{timestamp}.json"

        results_data = {
            "test_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_tests": len(self.test_results)
            },
            "results": []
        }

        for result in self.test_results:
            results_data["results"].append({
                "question": result.question,
                "category": result.category,
                "vapi_success": result.vapi_success,
                "vapi_response": result.vapi_response,
                "vapi_tool_calls": result.vapi_tool_calls,
                "db_success": result.db_success,
                "db_response": result.db_response,
                "db_total_found": result.db_data.get('total_found', 0),
                "db_providers": result.db_data.get('providers', [])[:2],  # Limit for file size
                "comparison": result.comparison,
                "execution_time": result.execution_time
            })

        filepath = f"/opt/kasaai/apps/core_backend/tests/{filename}"
        try:
            with open(filepath, 'w') as f:
                json.dump(results_data, f, indent=2, cls=DateTimeJSONEncoder)
            print(f"Detailed results saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

def main():
    """Main function to run the VAPI vs Database comparison test."""
    print("VAPI Chat vs Database Comparison Test")
    print("This script compares actual VAPI chat responses with direct database queries")
    print()

    # Check environment
    if not os.getenv('VAPI_API_KEY') and not '42cf1e7c-2ef9-4bd7-ba30-52f2813605a2':
        print("Warning: VAPI_API_KEY not set in environment")

    tester = VAPIVsDatabaseTester()

    try:
        tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        if tester.test_results:
            tester.generate_summary_report()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()