"""Voice engine translation orchestrator."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Optional, Type

DEFAULT_LANGUAGE = "en"
BASE_DIR = Path(__file__).resolve().parent


def _load_translation_module(language: str) -> Optional[Type]:
    """Load a translation service implementation for ``language``.

    Args:
        language: Language code to look up.

    Returns:
        Optional[Type]: ``TranslationService`` class if available, otherwise ``None``.
    """
    filename = "translation_en.py" if language == DEFAULT_LANGUAGE else "translation.py"
    module_path = BASE_DIR / filename
    if not module_path.exists():
        return None
    spec = spec_from_file_location(module_path.stem, module_path)
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "TranslationService", None)


def handle(text: str, language: str) -> str:
    """Translate ``text`` using a language-specific service.

    Attempts to load the translation service for ``language``. If unavailable,
    the default language service is tried before raising an error.

    Args:
        text: Text to translate.
        language: Desired language code.

    Returns:
        str: Translated text.

    Raises:
        RuntimeError: If no translation service can be loaded.
    """
    service_cls = _load_translation_module(language)
    if service_cls is None and language != DEFAULT_LANGUAGE:
        service_cls = _load_translation_module(DEFAULT_LANGUAGE)
    if service_cls is None:
        raise RuntimeError("No translation service available")
    service = service_cls()
    return service.translate(text)

"""Dynamic module loaders for the voice engine orchestrator.

These helpers load translation and TTS modules from arbitrary file paths using
``importlib``. Loaded modules are inserted into :mod:`sys.modules` to leverage
Python's import cache and avoid repeated disk access.
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
from types import ModuleType


def _load_module(module_path: str, namespace: str) -> ModuleType:
    """Load a module from ``module_path`` under the provided ``namespace``.

    Args:
        module_path (str): Filesystem path to the target module.
        namespace (str): Dotted package prefix for the loaded module.

    Returns:
        ModuleType: The imported module instance.

    Raises:
        ImportError: If ``module_path`` cannot be loaded.
    """

    path = Path(module_path)
    module_name = f"{namespace}.{path.stem}"
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module at {module_path}")

    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_translation_module(module_path: str) -> ModuleType:
    """Load a translation module from ``module_path``.

    Args:
        module_path (str): Path to the translation module file.

    Returns:
        ModuleType: Imported translation module.
    """

    return _load_module(module_path, "voice_engine.translation")


def _load_tts_module(module_path: str) -> ModuleType:
    """Load a TTS module from ``module_path``.

    Args:
        module_path (str): Path to the TTS module file.

    Returns:
        ModuleType: Imported TTS module.
    """

    return _load_module(module_path, "voice_engine.tts")

