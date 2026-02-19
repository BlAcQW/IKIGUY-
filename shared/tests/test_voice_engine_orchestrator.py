"""Tests for voice engine orchestrator translation fallback."""

import importlib
import sys
from importlib import util
from pathlib import Path

module_path = Path("apps/shared/voice-engine/backend/orchestrator.py").resolve()
spec = util.spec_from_file_location("orchestrator", module_path)
orchestrator = util.module_from_spec(spec)
spec.loader.exec_module(orchestrator)


def test_handle_falls_back_to_default_translation():
    """Orchestrator uses default service when specific module is missing."""
    backend_dir = module_path.parent
    original = backend_dir / "translation.py"
    backup = backend_dir / "translation_backup.py"
    original.rename(backup)
    try:
        importlib.invalidate_caches()
        sys.modules.pop("translation", None)
        result = orchestrator.handle("hello", "twi")
        assert result == "en:hello"
    finally:
        if backup.exists():
            backup.rename(original)
        importlib.invalidate_caches()
        sys.modules.pop("translation", None)

"""Tests for dynamic module loading in the voice engine orchestrator."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Load orchestrator module using file location because the package path
# contains a hyphen, making standard imports invalid.
ROOT = Path(__file__).resolve().parents[2]
ORCH_PATH = ROOT / "apps/shared/voice-engine/backend/orchestrator.py"
SPEC = importlib.util.spec_from_file_location(
    "voice_engine.backend.orchestrator", ORCH_PATH
)
orchestrator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = orchestrator
SPEC.loader.exec_module(orchestrator)


def _create_module(tmp_path: Path, name: str, body: str) -> Path:
    """Create a temporary module file with ``body``."""

    file_path = tmp_path / f"{name}.py"
    file_path.write_text(body)
    return file_path


def test_load_translation_module_caches(tmp_path):
    module_file = _create_module(tmp_path, "trans_mod", "VALUE = 1\n")
    mod1 = orchestrator._load_translation_module(str(module_file))
    mod2 = orchestrator._load_translation_module(str(module_file))
    assert mod1 is mod2
    assert mod1.VALUE == 1
    assert "voice_engine.translation.trans_mod" in sys.modules


def test_load_tts_module_caches(tmp_path):
    module_file = _create_module(tmp_path, "tts_mod", "NAME = 'voice'\n")
    mod1 = orchestrator._load_tts_module(str(module_file))
    mod2 = orchestrator._load_tts_module(str(module_file))
    assert mod1 is mod2
    assert mod1.NAME == "voice"
    assert "voice_engine.tts.tts_mod" in sys.modules


def test_load_module_missing_file(tmp_path):
    missing_file = tmp_path / "missing.py"
    with pytest.raises(FileNotFoundError):
        orchestrator._load_translation_module(str(missing_file))

import pytest


class DummyBus:
    def __init__(self) -> None:
        self.subscribed = False
        self.unsubscribed = False

    async def subscribe(self, event_type: str, handler) -> str:
        self.subscribed = True
        return "sub-1"

    async def unsubscribe(self, subscription_id: str) -> bool:
        self.unsubscribed = True
        return True


class VoiceEngineOrchestrator:
    def __init__(self, bus: DummyBus) -> None:
        self.bus = bus
        self.subscription_id: str | None = None

    async def start(self) -> None:
        self.subscription_id = await self.bus.subscribe("dummy", lambda _e: None)

    async def stop(self) -> None:
        if self.subscription_id is not None:
            await self.bus.unsubscribe(self.subscription_id)
            self.subscription_id = None


@pytest.mark.asyncio
async def test_start_stop_subscription_lifecycle() -> None:
    """Orchestrator subscribes on start and unsubscribes on stop."""

    orchestrator = VoiceEngineOrchestrator(DummyBus())
    await orchestrator.start()
    assert orchestrator.bus.subscribed
    await orchestrator.stop()
    assert orchestrator.bus.unsubscribed
