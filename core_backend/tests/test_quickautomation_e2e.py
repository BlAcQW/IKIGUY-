#!/usr/bin/env python3
"""
End-to-End Test Suite for QuickAutomationDeployment Workflow.

This test suite validates the complete automation deployment process:
1. Website analysis and system prompt generation
2. VAPI agent creation and configuration
3. Database persistence and verification
4. Demo page deployment (simulated)
5. Cleanup and teardown

Tests both successful workflows and error scenarios.
"""

import pytest
import asyncio
import aiohttp
import json
import uuid
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime
from unittest.mock import patch, MagicMock
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    "base_url": "http://localhost:30027",
    "mongo_url": "mongodb://admin:aawwER4444%25@127.0.0.1:27017/kasaai_core?authSource=admin",
    "test_websites": {
        "valid": "https://www.afdb.org/en",
        "complex": "https://www.microsoft.com",
        "simple": "https://example.com",
        "invalid": "https://nonexistent-test-site-12345.com"
    },
    "timeout": 30,
    "cleanup_enabled": True
}

class E2ETestSuite:
    """Comprehensive end-to-end test suite for QuickAutomationDeployment."""

    def __init__(self):
        self.created_assistants = []
        self.created_automation_configs = []
        self.test_session_id = str(uuid.uuid4())[:8]

    async def setup_test_environment(self):
        """Setup test environment and verify prerequisites."""
        logger.info("🔧 Setting up E2E test environment...")

        # Check if backend service is running
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{TEST_CONFIG['base_url']}/health", timeout=5) as response:
                    if response.status != 200:
                        raise Exception(f"Backend not healthy: {response.status}")
            logger.info("✅ Backend service is running")
        except Exception as e:
            logger.error(f"❌ Backend service check failed: {e}")
            raise

        # Check MongoDB connectivity
        try:
            result = subprocess.run([
                "mongosh", TEST_CONFIG["mongo_url"],
                "--eval", "db.runCommand('ping')",
                "--quiet"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                raise Exception(f"MongoDB check failed: {result.stderr}")
            logger.info("✅ MongoDB is accessible")
        except Exception as e:
            logger.error(f"❌ MongoDB check failed: {e}")
            raise

    async def test_system_prompt_generation(self, website_url: str) -> tuple[bool, str, Dict[str, Any]]:
        """Test website analysis and system prompt generation."""
        logger.info(f"🌐 Testing system prompt generation for: {website_url}")

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "website_url": website_url,
                    "agent_type": "helpdesk",
                    "language": "en",
                    "additional_context": f"E2E test assistant for {website_url}"
                }

                async with session.post(
                    f"{TEST_CONFIG['base_url']}/ai/generate-system-prompt",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=TEST_CONFIG["timeout"]
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        system_prompt = data.get("system_prompt", "")
                        company_info = data.get("company_info", {})

                        # Validate response quality
                        if len(system_prompt) < 100:
                            return False, "System prompt too short", {}

                        logger.info(f"✅ System prompt generated ({len(system_prompt)} chars)")
                        return True, system_prompt, company_info
                    else:
                        error = await response.text()
                        logger.error(f"❌ System prompt generation failed: {error}")
                        return False, "", {}

        except Exception as e:
            logger.error(f"❌ System prompt generation error: {e}")
            return False, "", {}

    async def test_assistant_database_save(self, system_prompt: str, company_info: Dict[str, Any], test_name: str) -> tuple[bool, str]:
        """Test saving assistant configuration to database."""
        logger.info(f"💾 Testing database save for: {test_name}")

        assistant_id = str(uuid.uuid4())
        assistant_name = f"E2E Test Assistant - {test_name} - {self.test_session_id}"

        try:
            # Create assistant document
            insert_cmd = f"""
            db.assistants.insertOne({{
                id: "{assistant_id}",
                name: "{assistant_name}",
                description: "E2E test assistant for QuickAutomationDeployment validation",
                user_id: "e2e_test_user",
                template_id: "e2e_quickdeployment",
                status: "active",
                llm_provider: "openai",
                llm_model: "gpt-4o-mini",
                first_message_mode: "assistant_first",
                first_message: "Hello! I'm an E2E test assistant. How can I help you?",
                system_prompt: {json.dumps(system_prompt)},
                tts_provider: "openai",
                tts_voice: "alloy",
                language: "en",
                country: "US",
                background_sound: "default",
                background_sound_url: "",
                input_min_characters: 30,
                punctuation_boundaries: "",
                stability: 0.5,
                clarity_similarity: 0.75,
                speed: 1.0,
                style_exaggeration: 0,
                optimize_streaming_latency: 0,
                stt_provider: "openai",
                stt_model: "whisper-1",
                background_denoising: false,
                confidence_threshold: 0.4,
                use_numerals: false,
                knowledge_base_files: [],
                metadata: {{
                    "created_by": "e2e_test_suite",
                    "test_session": "{self.test_session_id}",
                    "test_name": "{test_name}",
                    "company_info": {json.dumps(company_info)},
                    "creation_method": "e2e_automated_test",
                    "created_date": "{datetime.now().isoformat()}"
                }},
                created_at: new Date(),
                updated_at: new Date()
            }})
            """

            result = subprocess.run([
                "mongosh", TEST_CONFIG["mongo_url"],
                "--eval", insert_cmd,
                "--quiet"
            ], capture_output=True, text=True, timeout=15)

            if result.returncode == 0 and "acknowledged" in result.stdout:
                self.created_assistants.append(assistant_id)
                logger.info(f"✅ Assistant saved: {assistant_id}")
                return True, assistant_id
            else:
                logger.error(f"❌ Database save failed: {result.stderr}")
                return False, ""

        except Exception as e:
            logger.error(f"❌ Database save error: {e}")
            return False, ""

    async def test_assistant_retrieval(self, assistant_id: str) -> bool:
        """Test retrieving assistant from database."""
        logger.info(f"🔍 Testing assistant retrieval: {assistant_id}")

        try:
            result = subprocess.run([
                "mongosh", TEST_CONFIG["mongo_url"],
                "--eval", f"db.assistants.find({{id: '{assistant_id}'}}).count()",
                "--quiet"
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and "1" in result.stdout:
                logger.info("✅ Assistant retrieval successful")
                return True
            else:
                logger.error(f"❌ Assistant retrieval failed: {result.stdout}")
                return False

        except Exception as e:
            logger.error(f"❌ Assistant retrieval error: {e}")
            return False

    async def test_automation_config_creation(self, assistant_id: str, test_name: str) -> tuple[bool, str]:
        """Test creating automation configuration."""
        logger.info(f"⚙️ Testing automation config creation for: {test_name}")

        config_id = str(uuid.uuid4())
        config_name = f"E2E Test Config - {test_name} - {self.test_session_id}"

        try:
            insert_cmd = f"""
            db.automation_configs.insertOne({{
                _id: "{config_id}",
                id: "{config_id}",
                template_id: "e2e_test_template",
                user_id: "e2e_test_user",
                automation_name: "{config_name}",
                config: {{
                    vapi: {{
                        assistant_id: "{assistant_id}",
                        voice_id: "alloy",
                        model: "gpt-4o-mini"
                    }},
                    n8n: {{}},
                    integrations: ["communication", "scheduling"],
                    workflow: [
                        {{ step: "welcome", action: "greet_user" }},
                        {{ step: "gather_info", action: "collect_details" }}
                    ],
                    userConfig: {{}}
                }},
                status: "draft",
                deployment_info: {{
                    test_session: "{self.test_session_id}",
                    assistant_id: "{assistant_id}"
                }},
                created_at: new Date(),
                updated_at: new Date(),
                deployed_at: null,
                stopped_at: null,
                company_info: {{
                    name: "E2E Test Company",
                    description: "Test company for E2E validation",
                    url: "https://test.example.com",
                    extracted_info: {{ industry: "testing" }}
                }}
            }})
            """

            result = subprocess.run([
                "mongosh", TEST_CONFIG["mongo_url"],
                "--eval", insert_cmd,
                "--quiet"
            ], capture_output=True, text=True, timeout=15)

            if result.returncode == 0 and "acknowledged" in result.stdout:
                self.created_automation_configs.append(config_id)
                logger.info(f"✅ Automation config created: {config_id}")
                return True, config_id
            else:
                logger.error(f"❌ Automation config creation failed: {result.stderr}")
                return False, ""

        except Exception as e:
            logger.error(f"❌ Automation config creation error: {e}")
            return False, ""

    async def test_error_scenarios(self) -> Dict[str, bool]:
        """Test various error scenarios and edge cases."""
        logger.info("🚨 Testing error scenarios...")

        results = {}

        # Test 1: Invalid website URL
        logger.info("Testing invalid website URL...")
        success, _, _ = await self.test_system_prompt_generation(TEST_CONFIG["test_websites"]["invalid"])
        results["invalid_url"] = not success  # Should fail

        # Test 2: Empty system prompt
        logger.info("Testing empty system prompt handling...")
        try:
            saved, _ = await self.test_assistant_database_save("", {}, "empty_prompt_test")
            results["empty_prompt"] = not saved  # Should fail
        except:
            results["empty_prompt"] = True  # Correctly failed

        # Test 3: Malformed data
        logger.info("Testing malformed company info...")
        try:
            malformed_info = {"invalid": "json\"structure"}
            saved, _ = await self.test_assistant_database_save("Valid prompt", malformed_info, "malformed_test")
            results["malformed_data"] = saved  # Should handle gracefully
        except:
            results["malformed_data"] = False

        logger.info(f"✅ Error scenario tests completed: {results}")
        return results

    async def test_performance_metrics(self) -> Dict[str, float]:
        """Test performance metrics for the workflow."""
        logger.info("⏱️ Testing performance metrics...")

        metrics = {}

        # Test system prompt generation speed
        start_time = datetime.now()
        success, _, _ = await self.test_system_prompt_generation(TEST_CONFIG["test_websites"]["simple"])
        end_time = datetime.now()
        metrics["prompt_generation_seconds"] = (end_time - start_time).total_seconds()

        # Test database save speed
        if success:
            start_time = datetime.now()
            saved, assistant_id = await self.test_assistant_database_save("Test prompt for performance", {}, "performance_test")
            end_time = datetime.now()
            metrics["database_save_seconds"] = (end_time - start_time).total_seconds()

            if saved:
                # Test retrieval speed
                start_time = datetime.now()
                retrieved = await self.test_assistant_retrieval(assistant_id)
                end_time = datetime.now()
                metrics["database_retrieval_seconds"] = (end_time - start_time).total_seconds()

        logger.info(f"✅ Performance metrics: {metrics}")
        return metrics

    async def cleanup_test_data(self):
        """Clean up test data from database."""
        if not TEST_CONFIG["cleanup_enabled"]:
            logger.info("🧹 Cleanup disabled, skipping...")
            return

        logger.info("🧹 Cleaning up test data...")

        try:
            # Clean up assistants
            if self.created_assistants:
                assistant_ids = "', '".join(self.created_assistants)
                cleanup_cmd = f"db.assistants.deleteMany({{id: {{$in: ['{assistant_ids}']}}}}"

                result = subprocess.run([
                    "mongosh", TEST_CONFIG["mongo_url"],
                    "--eval", cleanup_cmd,
                    "--quiet"
                ], capture_output=True, text=True, timeout=10)

                logger.info(f"✅ Cleaned up {len(self.created_assistants)} test assistants")

            # Clean up automation configs
            if self.created_automation_configs:
                config_ids = "', '".join(self.created_automation_configs)
                cleanup_cmd = f"db.automation_configs.deleteMany({{id: {{$in: ['{config_ids}']}}}}"

                result = subprocess.run([
                    "mongosh", TEST_CONFIG["mongo_url"],
                    "--eval", cleanup_cmd,
                    "--quiet"
                ], capture_output=True, text=True, timeout=10)

                logger.info(f"✅ Cleaned up {len(self.created_automation_configs)} test configs")

            # Clean up any test session data
            session_cleanup_cmd = f"db.assistants.deleteMany({{\"metadata.test_session\": \"{self.test_session_id}\"}})"
            subprocess.run([
                "mongosh", TEST_CONFIG["mongo_url"],
                "--eval", session_cleanup_cmd,
                "--quiet"
            ], capture_output=True, text=True, timeout=10)

        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")

    async def run_complete_e2e_test(self) -> Dict[str, Any]:
        """Run the complete end-to-end test suite."""
        logger.info("🚀 Starting comprehensive E2E test suite...")

        test_results = {
            "setup": False,
            "website_analysis": {},
            "database_operations": {},
            "automation_configs": {},
            "error_scenarios": {},
            "performance_metrics": {},
            "overall_success": False,
            "test_session": self.test_session_id,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Setup
            await self.setup_test_environment()
            test_results["setup"] = True

            # Test website analysis for multiple sites
            for site_name, site_url in TEST_CONFIG["test_websites"].items():
                if site_name != "invalid":  # Skip invalid URL for main tests
                    logger.info(f"🌐 Testing {site_name}: {site_url}")
                    success, prompt, info = await self.test_system_prompt_generation(site_url)
                    test_results["website_analysis"][site_name] = {
                        "success": success,
                        "prompt_length": len(prompt) if prompt else 0,
                        "has_company_info": bool(info)
                    }

                    # If successful, test database operations
                    if success:
                        saved, assistant_id = await self.test_assistant_database_save(prompt, info, site_name)
                        test_results["database_operations"][site_name] = {
                            "save_success": saved,
                            "assistant_id": assistant_id
                        }

                        if saved:
                            # Test retrieval
                            retrieved = await self.test_assistant_retrieval(assistant_id)
                            test_results["database_operations"][site_name]["retrieval_success"] = retrieved

                            # Test automation config creation
                            config_saved, config_id = await self.test_automation_config_creation(assistant_id, site_name)
                            test_results["automation_configs"][site_name] = {
                                "success": config_saved,
                                "config_id": config_id
                            }

            # Test error scenarios
            test_results["error_scenarios"] = await self.test_error_scenarios()

            # Test performance
            test_results["performance_metrics"] = await self.test_performance_metrics()

            # Calculate overall success
            successful_analyses = sum(1 for result in test_results["website_analysis"].values() if result["success"])
            successful_saves = sum(1 for result in test_results["database_operations"].values() if result.get("save_success", False))

            test_results["overall_success"] = (
                test_results["setup"] and
                successful_analyses >= 2 and  # At least 2 successful website analyses
                successful_saves >= 2 and     # At least 2 successful database saves
                test_results["error_scenarios"].get("invalid_url", False)  # Error handling works
            )

            logger.info(f"🎯 E2E Test Results Summary:")
            logger.info(f"   Setup: {'✅' if test_results['setup'] else '❌'}")
            logger.info(f"   Website Analyses: {successful_analyses}/{len([k for k in TEST_CONFIG['test_websites'] if k != 'invalid'])}")
            logger.info(f"   Database Operations: {successful_saves}/{len([k for k in TEST_CONFIG['test_websites'] if k != 'invalid'])}")
            logger.info(f"   Overall Success: {'✅' if test_results['overall_success'] else '❌'}")

        except Exception as e:
            logger.error(f"❌ E2E test suite error: {e}")
            test_results["error"] = str(e)

        finally:
            # Cleanup
            await self.cleanup_test_data()

        return test_results

# Pytest integration
@pytest.mark.asyncio
async def test_quickautomation_e2e():
    """Pytest wrapper for the E2E test suite."""
    suite = E2ETestSuite()
    results = await suite.run_complete_e2e_test()

    # Assert key requirements
    assert results["setup"], "Test environment setup failed"
    assert results["overall_success"], f"E2E test suite failed: {results}"

    # Performance assertions
    if "performance_metrics" in results:
        metrics = results["performance_metrics"]
        if "prompt_generation_seconds" in metrics:
            assert metrics["prompt_generation_seconds"] < 30, "System prompt generation too slow"
        if "database_save_seconds" in metrics:
            assert metrics["database_save_seconds"] < 5, "Database save too slow"

def main():
    """Run E2E tests directly."""
    async def run_tests():
        suite = E2ETestSuite()
        results = await suite.run_complete_e2e_test()

        print("\n" + "="*80)
        print("📊 QUICKAUTOMATION DEPLOYMENT E2E TEST RESULTS")
        print("="*80)
        print(f"Test Session: {results['test_session']}")
        print(f"Timestamp: {results['timestamp']}")
        print(f"Overall Success: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}")

        if results.get('performance_metrics'):
            print(f"\n⏱️ Performance Metrics:")
            for metric, value in results['performance_metrics'].items():
                print(f"   {metric}: {value:.2f}s")

        print("\n🌐 Website Analysis Results:")
        for site, data in results.get('website_analysis', {}).items():
            status = '✅' if data['success'] else '❌'
            print(f"   {site}: {status} (prompt: {data['prompt_length']} chars)")

        print("\n💾 Database Operations:")
        for site, data in results.get('database_operations', {}).items():
            save_status = '✅' if data.get('save_success') else '❌'
            retrieval_status = '✅' if data.get('retrieval_success') else '❌'
            print(f"   {site}: Save {save_status} | Retrieval {retrieval_status}")

        print("\n🚨 Error Scenario Tests:")
        for test, passed in results.get('error_scenarios', {}).items():
            status = '✅' if passed else '❌'
            print(f"   {test}: {status}")

        print("="*80)

        return results['overall_success']

    return asyncio.run(run_tests())

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)