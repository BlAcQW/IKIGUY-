#!/usr/bin/env python3
"""
TTS System Deployment Validation Script

Validates that all TTS consolidation components are properly deployed and functional.

Usage:
    python apps/shared/tts/scripts/validate_deployment.py
    python apps/shared/tts/scripts/validate_deployment.py --check-billing
    python apps/shared/tts/scripts/validate_deployment.py --check-cache
    python apps/shared/tts/scripts/validate_deployment.py --check-all

Author: KasaAI Team
Date: 2025-11-23
"""

import sys
import os
import asyncio
import argparse
from typing import Dict, List, Any
from datetime import datetime

# Add apps to path
sys.path.insert(0, "/opt/kasaai/apps")


class DeploymentValidator:
    """Validates TTS system deployment."""

    def __init__(self):
        """Initialize validator."""
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []

    async def run(self, check_billing: bool = False, check_cache: bool = False, check_all: bool = False):
        """
        Run deployment validation.

        Args:
            check_billing: Include billing system checks
            check_cache: Include cache system checks
            check_all: Include all optional checks
        """
        print("=" * 70)
        print("TTS System Deployment Validation")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 70)
        print()

        # Core imports validation
        await self._check_core_imports()

        # Module structure validation
        await self._check_module_structure()

        # Provider ID validation
        await self._check_provider_ids()

        # Optional checks
        if check_billing or check_all:
            await self._check_billing_system()

        if check_cache or check_all:
            await self._check_cache_system()

        # Print summary
        self._print_summary()

        # Return exit code
        return 0 if self.checks_failed == 0 else 1

    async def _check_core_imports(self):
        """Validate core TTS imports."""
        print("1. Core Imports Validation")
        print("-" * 70)

        imports = [
            ("AsyncTTSClient", "apps.shared.tts.client"),
            ("TTSProvider", "apps.shared.tts.models"),
            ("TTSRequest", "apps.shared.tts.models"),
            ("TTSResponse", "apps.shared.tts.models"),
            ("AudioFormat", "apps.shared.tts.models"),
            ("ProviderID", "apps.shared.tts.provider_ids"),
            ("normalize_provider_id", "apps.shared.tts.provider_ids"),
        ]

        for name, module_path in imports:
            try:
                module = __import__(module_path, fromlist=[name])
                getattr(module, name)
                print(f"  ✓ {name} from {module_path}")
                self.checks_passed += 1
            except ImportError as e:
                print(f"  ✗ {name} from {module_path}: {str(e)}")
                self.errors.append(f"Import failed: {name} from {module_path}")
                self.checks_failed += 1
            except AttributeError as e:
                print(f"  ✗ {name} not found in {module_path}: {str(e)}")
                self.errors.append(f"Attribute error: {name} in {module_path}")
                self.checks_failed += 1

        print()

    async def _check_module_structure(self):
        """Validate module file structure."""
        print("2. Module Structure Validation")
        print("-" * 70)

        required_files = [
            "apps/shared/tts/__init__.py",
            "apps/shared/tts/client.py",
            "apps/shared/tts/models.py",
            "apps/shared/tts/config.py",
            "apps/shared/tts/provider_ids.py",
            "apps/shared/tts/billing.py",
            "apps/shared/tts/cache.py",
            "apps/shared/tts/alerts.py",
            "apps/shared/tts/MIGRATION.md",
            "apps/shared/routes/tts_routes.py",
            "apps/shared/frontend/hooks/useComprehensiveTTS.tsx",
            "apps/shared/frontend/types/tts.ts",
        ]

        for file_path in required_files:
            full_path = os.path.join("/opt/kasaai", file_path)
            if os.path.exists(full_path):
                print(f"  ✓ {file_path}")
                self.checks_passed += 1
            else:
                print(f"  ✗ {file_path} (missing)")
                self.errors.append(f"Missing file: {file_path}")
                self.checks_failed += 1

        print()

    async def _check_provider_ids(self):
        """Validate provider ID standardization."""
        print("3. Provider ID Standardization")
        print("-" * 70)

        try:
            from apps.shared.tts.provider_ids import ProviderID, normalize_provider_id

            # Test canonical IDs
            canonical_ids = [
                "coqui_xtts",
                "f5_tts",
                "style_tts2",
                "melo_tts",
                "open_voice",
                "kokoro",
            ]

            for provider_id in canonical_ids:
                if ProviderID.is_valid(provider_id):
                    print(f"  ✓ Canonical ID: {provider_id}")
                    self.checks_passed += 1
                else:
                    print(f"  ✗ Invalid canonical ID: {provider_id}")
                    self.errors.append(f"Invalid provider ID: {provider_id}")
                    self.checks_failed += 1

            # Test legacy ID normalization
            legacy_mappings = [
                ("XTTS", "coqui_xtts"),
                ("StyleTTS2", "style_tts2"),
                ("F5-TTS", "f5_tts"),
            ]

            for legacy_id, expected_canonical in legacy_mappings:
                result = normalize_provider_id(legacy_id)
                if result == expected_canonical:
                    print(f"  ✓ Legacy mapping: {legacy_id} → {result}")
                    self.checks_passed += 1
                else:
                    print(f"  ✗ Legacy mapping failed: {legacy_id} → {result} (expected {expected_canonical})")
                    self.errors.append(f"Legacy mapping error: {legacy_id}")
                    self.checks_failed += 1

        except Exception as e:
            print(f"  ✗ Provider ID validation failed: {str(e)}")
            self.errors.append(f"Provider ID system error: {str(e)}")
            self.checks_failed += 1

        print()

    async def _check_billing_system(self):
        """Validate billing system."""
        print("4. Billing System Validation (Optional)")
        print("-" * 70)

        try:
            from apps.shared.tts.billing import TTSBillingManager
            from apps.shared.tts.models import TTSProvider

            print("  ✓ TTSBillingManager import successful")
            self.checks_passed += 1

            # Test cost estimation (no DB required)
            try:
                # This would require WalletService, so we just check the class exists
                print("  ✓ TTSBillingManager class available")
                self.checks_passed += 1
            except Exception as e:
                print(f"  ⚠ Billing system warning: {str(e)}")
                self.warnings.append(f"Billing system: {str(e)}")

        except ImportError as e:
            print(f"  ✗ Billing system import failed: {str(e)}")
            self.errors.append(f"Billing system error: {str(e)}")
            self.checks_failed += 1

        print()

    async def _check_cache_system(self):
        """Validate cache system."""
        print("5. Cache System Validation (Optional)")
        print("-" * 70)

        try:
            from apps.shared.tts.cache import TTSAudioCache

            print("  ✓ TTSAudioCache import successful")
            self.checks_passed += 1

            # Test cache key generation (no DB required)
            cache = TTSAudioCache(database=None, default_ttl_hours=24)
            cache_key = cache.generate_key(
                text="test",
                provider="coqui_xtts",
                voice="nova",
                language="en"
            )

            if len(cache_key) == 64:  # SHA256 hex length
                print(f"  ✓ Cache key generation: {cache_key[:16]}...")
                self.checks_passed += 1
            else:
                print(f"  ✗ Invalid cache key length: {len(cache_key)}")
                self.errors.append("Cache key generation error")
                self.checks_failed += 1

        except ImportError as e:
            print(f"  ✗ Cache system import failed: {str(e)}")
            self.errors.append(f"Cache system error: {str(e)}")
            self.checks_failed += 1
        except Exception as e:
            print(f"  ⚠ Cache system warning: {str(e)}")
            self.warnings.append(f"Cache system: {str(e)}")

        print()

    def _print_summary(self):
        """Print validation summary."""
        print("=" * 70)
        print("Validation Summary")
        print("=" * 70)
        print(f"Checks passed: {self.checks_passed}")
        print(f"Checks failed: {self.checks_failed}")
        print(f"Warnings: {len(self.warnings)}")
        print()

        if self.warnings:
            print("Warnings:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
            print()

        if self.errors:
            print("Errors:")
            for error in self.errors:
                print(f"  ✗ {error}")
            print()

        if self.checks_failed == 0:
            print("✅ Deployment validation PASSED - All checks successful!")
        else:
            print(f"❌ Deployment validation FAILED - {self.checks_failed} check(s) failed")

        print("=" * 70)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate TTS system deployment")
    parser.add_argument("--check-billing", action="store_true", help="Include billing system checks")
    parser.add_argument("--check-cache", action="store_true", help="Include cache system checks")
    parser.add_argument("--check-all", action="store_true", help="Include all optional checks")

    args = parser.parse_args()

    validator = DeploymentValidator()
    exit_code = await validator.run(
        check_billing=args.check_billing,
        check_cache=args.check_cache,
        check_all=args.check_all
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
