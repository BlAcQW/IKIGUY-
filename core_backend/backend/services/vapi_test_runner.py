"""
Test Runner Service

Runs all standard unit and integration tests automatically on app startup.
Provides health checks for the entire system including VAPI tools.
"""

import os
import asyncio
import logging
import subprocess
import time
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class TestRunner:
    """Service to run all standard unit and integration tests and track results."""

    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.last_run: datetime = None
        self.enabled = os.getenv("STARTUP_TESTS_ENABLED", "true").lower() == "true"

    async def run_startup_tests(self) -> Dict[str, Any]:
        """
        Run all standard unit and integration tests on startup.

        Returns:
            Dict containing test results and summary
        """
        if not self.enabled:
            logger.info("Startup tests disabled")
            return {"enabled": False, "message": "Tests disabled"}

        logger.info("Starting comprehensive system tests...")
        start_time = time.time()

        results = {
            "enabled": True,
            "start_time": datetime.now().isoformat(),
            "test_categories": {},
            "summary": {},
            "duration_seconds": 0
        }

        try:
            # Run unit tests
            unit_result = await self._run_unit_tests()
            results["test_categories"]["unit_tests"] = unit_result

            # Run integration tests
            integration_result = await self._run_integration_tests()
            results["test_categories"]["integration_tests"] = integration_result

            # Run VAPI tools tests (quick subset)
            vapi_result = await self._run_vapi_tests()
            results["test_categories"]["vapi_tools"] = vapi_result

            # Generate summary
            total_tests = 0
            passed_tests = 0
            for category, test_result in results["test_categories"].items():
                if "test_count" in test_result:
                    total_tests += test_result["test_count"]
                if "passed_count" in test_result:
                    passed_tests += test_result["passed_count"]

            results["summary"] = {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "status": "PASS" if passed_tests == total_tests else "PARTIAL" if passed_tests > 0 else "FAIL"
            }

            results["duration_seconds"] = time.time() - start_time
            self.test_results = results
            self.last_run = datetime.now()

            logger.info(f"Startup tests completed: {results['summary']['status']} "
                       f"({passed_tests}/{total_tests} passed) in {results['duration_seconds']:.2f}s")

        except Exception as e:
            logger.error(f"Error running startup tests: {e}")
            results["error"] = str(e)
            results["summary"] = {"status": "ERROR"}

        return results

    async def _run_unit_tests(self) -> Dict[str, Any]:
        """Run standard unit tests."""
        try:
            # Run unit tests (fast, non-external dependencies)
            cmd = [
                "python", "-m", "pytest",
                "tests/",
                "-k", "not integration and not vapi and not slow",
                "-v", "--tb=short", "--maxfail=5"
            ]

            result = await self._run_pytest_command(cmd)
            return {
                "category": "unit_tests",
                "test_count": result.get("passed", 0) + result.get("failed", 0),
                "passed_count": result.get("passed", 0),
                "failed_count": result.get("failed", 0),
                "duration": result.get("duration", 0),
                "status": "PASS" if result.get("failed", 0) == 0 else "FAIL",
                "details": result.get("output", "")[:500]
            }

        except Exception as e:
            logger.error(f"Unit tests error: {e}")
            return {
                "category": "unit_tests",
                "test_count": 0,
                "passed_count": 0,
                "failed_count": 1,
                "status": "ERROR",
                "error": str(e)
            }

    async def _run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        try:
            # Run integration tests (may have external dependencies)
            cmd = [
                "python", "-m", "pytest",
                "tests/",
                "-m", "integration",
                "-v", "--tb=short", "--maxfail=3"
            ]

            result = await self._run_pytest_command(cmd)
            return {
                "category": "integration_tests",
                "test_count": result.get("passed", 0) + result.get("failed", 0),
                "passed_count": result.get("passed", 0),
                "failed_count": result.get("failed", 0),
                "duration": result.get("duration", 0),
                "status": "PASS" if result.get("failed", 0) == 0 else "FAIL",
                "details": result.get("output", "")[:500]
            }

        except Exception as e:
            logger.error(f"Integration tests error: {e}")
            return {
                "category": "integration_tests",
                "test_count": 0,
                "passed_count": 0,
                "failed_count": 1,
                "status": "ERROR",
                "error": str(e)
            }

    async def _run_vapi_tests(self) -> Dict[str, Any]:
        """Run VAPI tools tests (quick subset)."""
        try:
            # Run a subset of VAPI tests for quick validation
            cmd = [
                "python", "-m", "pytest",
                "tests/test_real_vapi_chat_healthcare_tools.py::TestRealVAPIChatHealthcareTools::test_emergency_healthcare_providers",
                "tests/test_real_vapi_chat_general_tools.py::TestRealVAPIChatGeneralTools::test_send_notification_email",
                "-v", "--tb=short", "--maxfail=2"
            ]

            result = await self._run_pytest_command(cmd)
            return {
                "category": "vapi_tools",
                "test_count": 2,
                "passed_count": result.get("passed", 0),
                "failed_count": result.get("failed", 0),
                "duration": result.get("duration", 0),
                "status": "PASS" if result.get("passed", 0) == 2 else "FAIL",
                "details": result.get("output", "")[:500]
            }

        except Exception as e:
            logger.error(f"VAPI tests error: {e}")
            return {
                "category": "vapi_tools",
                "test_count": 2,
                "passed_count": 0,
                "failed_count": 2,
                "status": "ERROR",
                "error": str(e)
            }


    async def _run_pytest_command(self, cmd: List[str]) -> Dict[str, Any]:
        """
        Run a pytest command and parse results.

        Args:
            cmd: Command list to execute

        Returns:
            Dict with test results
        """
        try:
            # Change to backend directory for proper test execution
            cwd = "/opt/kasaai/apps/core_backend"

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)

            output = stdout.decode() + stderr.decode()

            # Parse pytest output for results
            passed = output.count(" PASSED")
            failed = output.count(" FAILED")
            errors = output.count(" ERROR")

            return {
                "passed": passed,
                "failed": failed + errors,
                "duration": self._extract_duration(output),
                "output": output,
                "return_code": process.returncode
            }

        except asyncio.TimeoutError:
            logger.error("Pytest command timed out")
            return {"passed": 0, "failed": 1, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Error running pytest: {e}")
            return {"passed": 0, "failed": 1, "error": str(e)}

    def _extract_duration(self, output: str) -> float:
        """Extract test duration from pytest output."""
        try:
            import re
            match = re.search(r"in (\d+\.\d+)s", output)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0.0

    def get_test_status(self) -> Dict[str, Any]:
        """Get current test status and results."""
        return {
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "enabled": self.enabled,
            "results": self.test_results
        }

    async def run_full_tests(self) -> Dict[str, Any]:
        """Run full comprehensive VAPI tests (for manual triggering)."""
        logger.info("Starting comprehensive VAPI tests...")
        start_time = time.time()

        try:
            # Run all healthcare tests
            healthcare_cmd = [
                "python", "-m", "pytest",
                "tests/test_real_vapi_chat_healthcare_tools.py",
                "-v", "--tb=short"
            ]
            healthcare_result = await self._run_pytest_command(healthcare_cmd)

            # Run all general tests
            general_cmd = [
                "python", "-m", "pytest",
                "tests/test_real_vapi_chat_general_tools.py",
                "-v", "--tb=short"
            ]
            general_result = await self._run_pytest_command(general_cmd)

            total_passed = healthcare_result.get("passed", 0) + general_result.get("passed", 0)
            total_failed = healthcare_result.get("failed", 0) + general_result.get("failed", 0)
            total_tests = total_passed + total_failed

            return {
                "type": "comprehensive",
                "start_time": datetime.now().isoformat(),
                "duration_seconds": time.time() - start_time,
                "healthcare": healthcare_result,
                "general": general_result,
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": total_passed,
                    "failed_tests": total_failed,
                    "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
                    "status": "PASS" if total_failed == 0 else "FAIL"
                }
            }

        except Exception as e:
            logger.error(f"Error running comprehensive tests: {e}")
            return {
                "type": "comprehensive",
                "error": str(e),
                "status": "ERROR"
            }

# Global instance
test_runner = TestRunner()