"""
End-to-end testing system for Ghanaian language processing

This module provides comprehensive end-to-end testing capabilities for
Ghanaian language processing operations, simulating real user scenarios
and validating the complete processing pipeline.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from unittest.mock import AsyncMock, MagicMock

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TestScenario(Enum):
    """Types of test scenarios"""
    CUSTOMER_SERVICE = "customer_service"
    VOICE_COMMANDS = "voice_commands"
    LANGUAGE_LEARNING = "language_learning"
    BUSINESS_COMMUNICATION = "business_communication"
    SOCIAL_INTERACTION = "social_interaction"
    EMERGENCY_SITUATION = "emergency_situation"


class TestResult(Enum):
    """Test result status"""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class TestCase:
    """Individual test case"""
    id: str
    scenario: TestScenario
    language: str
    input_text: str
    expected_output: Dict[str, Any]
    timeout_seconds: float = 30.0
    retry_count: int = 3
    priority: int = 1  # 1=low, 2=medium, 3=high
    tags: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Test execution result"""
    test_case: TestCase
    status: TestResult
    actual_output: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class E2ETestReport(BaseModel):
    """End-to-end test report"""
    test_suite: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    partial_tests: int
    timeout_tests: int
    error_tests: int
    execution_time_seconds: float
    success_rate: float
    results: List[TestResult]
    summary: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class GhanaianE2ETester:
    """
    End-to-end testing system for Ghanaian language processing
    
    Provides comprehensive testing capabilities for simulating real user
    scenarios and validating the complete processing pipeline.
    """
    
    def __init__(self, output_dir: str = "./e2e_test_results"):
        """
        Initialize E2E tester
        
        Args:
            output_dir: Directory for test results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test cases and results
        self.test_cases: List[TestCase] = []
        self.test_results: List[TestResult] = []
        
        # Test scenarios
        self.scenarios = self._load_test_scenarios()
        
        # Processing functions
        self.processors = {}
    
    def _load_test_scenarios(self) -> Dict[TestScenario, List[Dict[str, Any]]]:
        """Load test scenarios for different use cases"""
        return {
            TestScenario.CUSTOMER_SERVICE: [
                {
                    "language": "tw",
                    "input": "ɛte sɛn? me pɛ wo help me with my account",
                    "expected": {
                        "intent": "request",
                        "sentiment": "neutral",
                        "entities": ["account"]
                    }
                },
                {
                    "language": "en-GH",
                    "input": "make you help me with my wahala",
                    "expected": {
                        "intent": "request",
                        "sentiment": "negative",
                        "entities": ["problem"]
                    }
                },
                {
                    "language": "ee",
                    "input": "me nyɛ wo help me",
                    "expected": {
                        "intent": "request",
                        "sentiment": "negative",
                        "entities": []
                    }
                }
            ],
            TestScenario.VOICE_COMMANDS: [
                {
                    "language": "tw",
                    "input": "kyerɛ me wo account balance",
                    "expected": {
                        "intent": "request",
                        "entities": ["account", "balance"]
                    }
                },
                {
                    "language": "en-GH",
                    "input": "make you show me my money",
                    "expected": {
                        "intent": "request",
                        "entities": ["money"]
                    }
                }
            ],
            TestScenario.LANGUAGE_LEARNING: [
                {
                    "language": "tw",
                    "input": "ɛyɛ adeɛ pa",
                    "expected": {
                        "sentiment": "positive",
                        "translation": "It is good"
                    }
                },
                {
                    "language": "en-GH",
                    "input": "I dey fine",
                    "expected": {
                        "sentiment": "positive",
                        "translation": "I am fine"
                    }
                }
            ],
            TestScenario.BUSINESS_COMMUNICATION: [
                {
                    "language": "tw",
                    "input": "me pɛ wo business proposal",
                    "expected": {
                        "intent": "request",
                        "entities": ["business", "proposal"]
                    }
                },
                {
                    "language": "en-GH",
                    "input": "make you send me the contract",
                    "expected": {
                        "intent": "request",
                        "entities": ["contract"]
                    }
                }
            ],
            TestScenario.SOCIAL_INTERACTION: [
                {
                    "language": "tw",
                    "input": "ɛte sɛn? wo ho te sɛn?",
                    "expected": {
                        "intent": "greeting",
                        "sentiment": "positive"
                    }
                },
                {
                    "language": "en-GH",
                    "input": "how you dey? you dey fine?",
                    "expected": {
                        "intent": "greeting",
                        "sentiment": "positive"
                    }
                }
            ],
            TestScenario.EMERGENCY_SITUATION: [
                {
                    "language": "tw",
                    "input": "boa me! me dey wahala!",
                    "expected": {
                        "intent": "request",
                        "sentiment": "negative",
                        "urgency": "high"
                    }
                },
                {
                    "language": "en-GH",
                    "input": "help me! I dey trouble!",
                    "expected": {
                        "intent": "request",
                        "sentiment": "negative",
                        "urgency": "high"
                    }
                }
            ]
        }
    
    def register_processor(self, name: str, processor: Callable):
        """
        Register a processing function
        
        Args:
            name: Processor name
            processor: Processing function
        """
        self.processors[name] = processor
        logger.info(f"Registered processor: {name}")
    
    def generate_test_cases(
        self,
        scenarios: List[TestScenario] = None,
        languages: List[str] = None,
        count_per_scenario: int = 5
    ) -> List[TestCase]:
        """
        Generate test cases for specified scenarios
        
        Args:
            scenarios: List of scenarios to test (all if None)
            languages: List of languages to test (all if None)
            count_per_scenario: Number of test cases per scenario
            
        Returns:
            List of generated test cases
        """
        if scenarios is None:
            scenarios = list(TestScenario)
        
        if languages is None:
            languages = ["tw", "en-GH", "ee", "ga", "dag"]
        
        test_cases = []
        test_id = 1
        
        for scenario in scenarios:
            if scenario not in self.scenarios:
                logger.warning(f"No test data for scenario: {scenario}")
                continue
            
            scenario_data = self.scenarios[scenario]
            
            for language in languages:
                # Find test data for this language
                language_data = [d for d in scenario_data if d["language"] == language]
                
                if not language_data:
                    logger.warning(f"No test data for scenario {scenario} and language {language}")
                    continue
                
                # Generate test cases
                for i in range(count_per_scenario):
                    # Randomly select or generate test data
                    if i < len(language_data):
                        data = language_data[i]
                    else:
                        # Generate synthetic test case
                        data = self._generate_synthetic_test_case(scenario, language)
                    
                    test_case = TestCase(
                        id=f"test_{test_id:04d}",
                        scenario=scenario,
                        language=language,
                        input_text=data["input"],
                        expected_output=data["expected"],
                        tags=[scenario.value, language, f"priority_{data.get('priority', 1)}"]
                    )
                    
                    test_cases.append(test_case)
                    test_id += 1
        
        self.test_cases.extend(test_cases)
        logger.info(f"Generated {len(test_cases)} test cases")
        return test_cases
    
    def _generate_synthetic_test_case(self, scenario: TestScenario, language: str) -> Dict[str, Any]:
        """Generate synthetic test case for scenario and language"""
        # Base templates for different scenarios
        templates = {
            TestScenario.CUSTOMER_SERVICE: {
                "tw": [
                    ("me pɛ wo help me with {service}", {"intent": "request", "entities": ["{service}"]}),
                    ("wo account dey {status}", {"intent": "inform", "entities": ["account", "{status}"]})
                ],
                "en-GH": [
                    ("make you help me with {service}", {"intent": "request", "entities": ["{service}"]}),
                    ("my account dey {status}", {"intent": "inform", "entities": ["account", "{status}"]})
                ]
            },
            TestScenario.VOICE_COMMANDS: {
                "tw": [
                    ("kyerɛ me {info}", {"intent": "request", "entities": ["{info}"]}),
                    ("kɔ {action}", {"intent": "command", "entities": ["{action}"]})
                ],
                "en-GH": [
                    ("show me {info}", {"intent": "request", "entities": ["{info}"]}),
                    ("go {action}", {"intent": "command", "entities": ["{action}"]})
                ]
            }
        }
        
        # Get templates for scenario and language
        scenario_templates = templates.get(scenario, {})
        language_templates = scenario_templates.get(language, [])
        
        if not language_templates:
            # Fallback template
            return {
                "input": f"test input in {language}",
                "expected": {"intent": "unknown", "sentiment": "neutral"}
            }
        
        # Select random template
        template, expected = random.choice(language_templates)
        
        # Fill template with random values
        placeholders = {
            "service": random.choice(["account", "payment", "support", "billing"]),
            "status": random.choice(["active", "inactive", "suspended", "pending"]),
            "info": random.choice(["balance", "history", "details", "status"]),
            "action": random.choice(["forward", "back", "home", "menu"])
        }
        
        input_text = template
        expected_output = expected.copy()
        
        # Replace placeholders
        for placeholder, value in placeholders.items():
            input_text = input_text.replace(f"{{{placeholder}}}", value)
            if isinstance(expected_output.get("entities"), list):
                expected_output["entities"] = [
                    value if entity == f"{{{placeholder}}}" else entity
                    for entity in expected_output["entities"]
                ]
        
        return {
            "input": input_text,
            "expected": expected_output,
            "priority": random.randint(1, 3)
        }
    
    async def run_test_case(self, test_case: TestCase) -> TestResult:
        """
        Run a single test case
        
        Args:
            test_case: Test case to run
            
        Returns:
            Test result
        """
        logger.info(f"Running test case: {test_case.id} ({test_case.scenario.value} - {test_case.language})")
        
        start_time = time.time()
        actual_output = None
        error_message = None
        retry_count = 0
        
        # Try to execute the test case
        for attempt in range(test_case.retry_count + 1):
            try:
                # Run all processors
                actual_output = await self._run_processors(test_case)
                
                # Validate output
                validation_result = self._validate_output(test_case, actual_output)
                
                if validation_result["status"] == TestResult.PASSED:
                    break
                elif validation_result["status"] == TestResult.PARTIAL:
                    # Partial success, but don't retry
                    break
                else:
                    error_message = validation_result["message"]
                    retry_count = attempt
                    
            except asyncio.TimeoutError:
                error_message = f"Test case timed out after {test_case.timeout_seconds} seconds"
                retry_count = attempt
            except Exception as e:
                error_message = f"Test case failed: {str(e)}"
                retry_count = attempt
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Determine final status
        if actual_output is None:
            status = TestResult.ERROR
        elif retry_count > 0:
            status = TestResult.PARTIAL
        else:
            validation_result = self._validate_output(test_case, actual_output)
            status = validation_result["status"]
        
        result = TestResult(
            test_case=test_case,
            status=status,
            actual_output=actual_output,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            retry_count=retry_count,
            metadata={
                "scenario": test_case.scenario.value,
                "language": test_case.language,
                "priority": test_case.priority
            }
        )
        
        self.test_results.append(result)
        return result
    
    async def _run_processors(self, test_case: TestCase) -> Dict[str, Any]:
        """Run all registered processors on test case input"""
        output = {
            "input": test_case.input_text,
            "language": test_case.language,
            "scenario": test_case.scenario.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Run each processor
        for name, processor in self.processors.items():
            try:
                result = await processor(
                    text=test_case.input_text,
                    language=test_case.language,
                    context={"scenario": test_case.scenario.value}
                )
                output[name] = result
            except Exception as e:
                logger.error(f"Processor {name} failed: {e}")
                output[name] = {"error": str(e)}
        
        return output
    
    def _validate_output(self, test_case: TestCase, actual_output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate actual output against expected output"""
        if actual_output is None:
            return {
                "status": TestResult.ERROR,
                "message": "No output received",
                "score": 0.0
            }
        
        expected = test_case.expected_output
        score = 0.0
        total_checks = 0
        failed_checks = []
        
        # Check each expected field
        for field, expected_value in expected.items():
            total_checks += 1
            
            if field not in actual_output:
                failed_checks.append(f"Missing field: {field}")
                continue
            
            actual_value = actual_output[field]
            
            # Simple validation - in a real implementation, you'd have more sophisticated validation
            if isinstance(expected_value, list):
                # For lists (like entities), check if any expected items are present
                if isinstance(actual_value, list):
                    matches = sum(1 for item in expected_value if item in actual_value)
                    if matches > 0:
                        score += matches / len(expected_value)
                    else:
                        failed_checks.append(f"Field {field}: expected {expected_value}, got {actual_value}")
                else:
                    failed_checks.append(f"Field {field}: expected list, got {type(actual_value)}")
            else:
                # For simple values, check exact match
                if actual_value == expected_value:
                    score += 1.0
                else:
                    failed_checks.append(f"Field {field}: expected {expected_value}, got {actual_value}")
        
        # Calculate final score
        final_score = score / total_checks if total_checks > 0 else 0.0
        
        # Determine status
        if final_score >= 0.9:
            status = TestResult.PASSED
        elif final_score >= 0.6:
            status = TestResult.PARTIAL
        else:
            status = TestResult.FAILED
        
        return {
            "status": status,
            "score": final_score,
            "message": "; ".join(failed_checks) if failed_checks else "All checks passed",
            "failed_checks": failed_checks
        }
    
    async def run_test_suite(
        self,
        test_cases: List[TestCase] = None,
        max_concurrent: int = 5,
        timeout_seconds: float = 300.0
    ) -> E2ETestReport:
        """
        Run a complete test suite
        
        Args:
            test_cases: List of test cases to run (uses self.test_cases if None)
            max_concurrent: Maximum concurrent test executions
            timeout_seconds: Overall timeout for test suite
            
        Returns:
            Test report
        """
        if test_cases is None:
            test_cases = self.test_cases
        
        if not test_cases:
            raise ValueError("No test cases to run")
        
        logger.info(f"Starting test suite with {len(test_cases)} test cases")
        
        start_time = time.time()
        results = []
        
        # Run test cases with concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_test_with_semaphore(test_case):
            async with semaphore:
                return await self.run_test_case(test_case)
        
        # Create tasks for all test cases
        tasks = [run_test_with_semaphore(test_case) for test_case in test_cases]
        
        try:
            # Run all tests with timeout
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error(f"Test suite timed out after {timeout_seconds} seconds")
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
        
        # Process results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Test case failed with exception: {result}")
                # Create error result
                error_result = TestResult(
                    test_case=TestCase(id="error", scenario=TestScenario.CUSTOMER_SERVICE, language="en", input_text="", expected_output={}),
                    status=TestResult.ERROR,
                    error_message=str(result)
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        execution_time = time.time() - start_time
        
        # Generate report
        report = self._generate_report(processed_results, execution_time)
        
        logger.info(f"Test suite completed in {execution_time:.2f} seconds")
        logger.info(f"Results: {report.passed_tests} passed, {report.failed_tests} failed, {report.partial_tests} partial")
        
        return report
    
    def _generate_report(self, results: List[TestResult], execution_time: float) -> E2ETestReport:
        """Generate test report from results"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.status == TestResult.PASSED)
        failed_tests = sum(1 for r in results if r.status == TestResult.FAILED)
        partial_tests = sum(1 for r in results if r.status == TestResult.PARTIAL)
        timeout_tests = sum(1 for r in results if r.status == TestResult.TIMEOUT)
        error_tests = sum(1 for r in results if r.status == TestResult.ERROR)
        
        success_rate = (passed_tests + partial_tests * 0.5) / total_tests if total_tests > 0 else 0.0
        
        # Generate summary statistics
        summary = {
            "scenario_stats": {},
            "language_stats": {},
            "performance_stats": {
                "avg_execution_time_ms": sum(r.execution_time_ms for r in results) / total_tests if total_tests > 0 else 0.0,
                "max_execution_time_ms": max(r.execution_time_ms for r in results) if results else 0.0,
                "min_execution_time_ms": min(r.execution_time_ms for r in results) if results else 0.0
            }
        }
        
        # Scenario statistics
        for scenario in TestScenario:
            scenario_results = [r for r in results if r.test_case.scenario == scenario]
            if scenario_results:
                scenario_passed = sum(1 for r in scenario_results if r.status == TestResult.PASSED)
                scenario_total = len(scenario_results)
                summary["scenario_stats"][scenario.value] = {
                    "total": scenario_total,
                    "passed": scenario_passed,
                    "success_rate": scenario_passed / scenario_total
                }
        
        # Language statistics
        languages = set(r.test_case.language for r in results)
        for language in languages:
            language_results = [r for r in results if r.test_case.language == language]
            if language_results:
                language_passed = sum(1 for r in language_results if r.status == TestResult.PASSED)
                language_total = len(language_results)
                summary["language_stats"][language] = {
                    "total": language_total,
                    "passed": language_passed,
                    "success_rate": language_passed / language_total
                }
        
        return E2ETestReport(
            test_suite="Ghanaian Language Processing E2E Tests",
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            partial_tests=partial_tests,
            timeout_tests=timeout_tests,
            error_tests=error_tests,
            execution_time_seconds=execution_time,
            success_rate=success_rate,
            results=results,
            summary=summary
        )
    
    def save_report(self, report: E2ETestReport, filename: str = None):
        """
        Save test report to file
        
        Args:
            report: Test report to save
            filename: Output filename (auto-generated if None)
        """
        if filename is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"e2e_test_report_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        # Convert report to JSON-serializable format
        serializable_report = {
            "test_suite": report.test_suite,
            "total_tests": report.total_tests,
            "passed_tests": report.passed_tests,
            "failed_tests": report.failed_tests,
            "partial_tests": report.partial_tests,
            "timeout_tests": report.timeout_tests,
            "error_tests": report.error_tests,
            "execution_time_seconds": report.execution_time_seconds,
            "success_rate": report.success_rate,
            "timestamp": report.timestamp.isoformat(),
            "summary": report.summary,
            "results": [
                {
                    "test_case": {
                        "id": result.test_case.id,
                        "scenario": result.test_case.scenario.value,
                        "language": result.test_case.language,
                        "input_text": result.test_case.input_text,
                        "expected_output": result.test_case.expected_output,
                        "priority": result.test_case.priority,
                        "tags": result.test_case.tags
                    },
                    "status": result.status.value,
                    "execution_time_ms": result.execution_time_ms,
                    "error_message": result.error_message,
                    "retry_count": result.retry_count,
                    "timestamp": result.timestamp.isoformat(),
                    "metadata": result.metadata
                }
                for result in report.results
            ]
        }
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(serializable_report, f, indent=2)
        
        logger.info(f"Test report saved to {output_path}")
        
        # Generate human-readable report
        self._generate_human_readable_report(report, filename)
    
    def _generate_human_readable_report(self, report: E2ETestReport, base_filename: str):
        """Generate human-readable test report"""
        report_filename = base_filename.replace('.json', '_readable.md')
        report_path = self.output_dir / report_filename
        
        lines = [
            "# Ghanaian Language Processing End-to-End Test Report",
            f"Generated: {report.timestamp.isoformat()}",
            f"Test Suite: {report.test_suite}",
            "",
            "## Executive Summary",
            "",
            f"- **Total Tests**: {report.total_tests}",
            f"- **Passed**: {report.passed_tests}",
            f"- **Failed**: {report.failed_tests}",
            f"- **Partial**: {report.partial_tests}",
            f"- **Timeouts**: {report.timeout_tests}",
            f"- **Errors**: {report.error_tests}",
            f"- **Success Rate**: {report.success_rate:.2%}",
            f"- **Execution Time**: {report.execution_time_seconds:.2f} seconds",
            "",
            "## Scenario Performance",
            ""
        ]
        
        # Add scenario statistics
        for scenario, stats in report.summary.get("scenario_stats", {}).items():
            lines.extend([
                f"### {scenario.title()}",
                f"- Total Tests: {stats['total']}",
                f"- Passed: {stats['passed']}",
                f"- Success Rate: {stats['success_rate']:.2%}",
                ""
            ])
        
        lines.extend([
            "## Language Performance",
            ""
        ])
        
        # Add language statistics
        for language, stats in report.summary.get("language_stats", {}).items():
            lines.extend([
                f"### {language.upper()}",
                f"- Total Tests: {stats['total']}",
                f"- Passed: {stats['passed']}",
                f"- Success Rate: {stats['success_rate']:.2%}",
                ""
            ])
        
        lines.extend([
            "## Performance Statistics",
            "",
            f"- **Average Execution Time**: {report.summary['performance_stats']['avg_execution_time_ms']:.2f}ms",
            f"- **Maximum Execution Time**: {report.summary['performance_stats']['max_execution_time_ms']:.2f}ms",
            f"- **Minimum Execution Time**: {report.summary['performance_stats']['min_execution_time_ms']:.2f}ms",
            "",
            "## Failed Tests",
            ""
        ])
        
        # Add failed test details
        failed_results = [r for r in report.results if r.status in [TestResult.FAILED, TestResult.ERROR, TestResult.TIMEOUT]]
        
        if failed_results:
            for result in failed_results[:10]:  # Show first 10 failures
                lines.extend([
                    f"### {result.test_case.id}",
                    f"- **Scenario**: {result.test_case.scenario.value}",
                    f"- **Language**: {result.test_case.language}",
                    f"- **Input**: `{result.test_case.input_text}`",
                    f"- **Expected**: {result.test_case.expected_output}",
                    f"- **Status**: {result.status.value}",
                    f"- **Error**: {result.error_message or 'N/A'}",
                    f"- **Execution Time**: {result.execution_time_ms:.2f}ms",
                    ""
                ])
        else:
            lines.append("No failed tests!")
        
        # Save human-readable report
        with open(report_path, 'w') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Human-readable report saved to {report_path}")
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get statistics about test cases and results"""
        if not self.test_results:
            return {"message": "No test results available"}
        
        stats = {
            "total_test_cases": len(self.test_cases),
            "total_results": len(self.test_results),
            "scenario_distribution": {},
            "language_distribution": {},
            "status_distribution": {},
            "performance_metrics": {
                "avg_execution_time_ms": 0.0,
                "max_execution_time_ms": 0.0,
                "min_execution_time_ms": 0.0
            }
        }
        
        # Calculate distributions
        for result in self.test_results:
            # Scenario distribution
            scenario = result.test_case.scenario.value
            stats["scenario_distribution"][scenario] = stats["scenario_distribution"].get(scenario, 0) + 1
            
            # Language distribution
            language = result.test_case.language
            stats["language_distribution"][language] = stats["language_distribution"].get(language, 0) + 1
            
            # Status distribution
            status = result.status.value
            stats["status_distribution"][status] = stats["status_distribution"].get(status, 0) + 1
        
        # Calculate performance metrics
        execution_times = [r.execution_time_ms for r in self.test_results]
        if execution_times:
            stats["performance_metrics"]["avg_execution_time_ms"] = sum(execution_times) / len(execution_times)
            stats["performance_metrics"]["max_execution_time_ms"] = max(execution_times)
            stats["performance_metrics"]["min_execution_time_ms"] = min(execution_times)
        
        return stats
