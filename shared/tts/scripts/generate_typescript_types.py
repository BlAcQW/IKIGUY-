#!/usr/bin/env python3
"""
TypeScript Type Generation Script

Automatically generates TypeScript types from Pydantic models in apps/shared/tts/models.py.
Output is written to apps/shared/frontend/types/tts.ts for frontend consumption.

Usage:
    python apps/shared/tts/scripts/generate_typescript_types.py

    # With custom output path
    python apps/shared/tts/scripts/generate_typescript_types.py --output /path/to/output.ts

Author: KasaAI Team
Date: 2025-11-23
"""

import sys
import os
import argparse
import inspect
from pathlib import Path
from typing import get_type_hints, get_origin, get_args, Union
from enum import Enum
from datetime import datetime

# Add apps to path
sys.path.insert(0, "/opt/kasaai/apps")

from shared.tts.models import (
    AudioFormat,
    TTSProvider,
    TTSCapabilities,
    TTSRequest,
    VoiceCloneRequest,
    ConversationRequest,
    TTSResponse,
    ProviderStatus,
    BatchTTSRequest,
    BatchTTSResponse,
)

# Type mapping from Python to TypeScript
PYTHON_TO_TS_TYPE_MAP = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "bytes": "Uint8Array",
    "datetime": "Date",
    "dict": "Record<string, any>",
    "list": "Array",
    "Any": "any",
}


def python_type_to_typescript(python_type: type) -> str:
    """
    Convert Python type to TypeScript type.

    Args:
        python_type: Python type annotation

    Returns:
        TypeScript type string
    """
    # Handle None/Optional
    if python_type is type(None):
        return "null"

    # Get type origin (for generics like List[str])
    origin = get_origin(python_type)
    args = get_args(python_type)

    # Handle Union types (including Optional)
    if origin is Union:
        # Filter out None for Optional types
        non_none_args = [arg for arg in args if arg is not type(None)]
        ts_types = [python_type_to_typescript(arg) for arg in non_none_args]

        # Check if it's Optional (Union with None)
        has_none = type(None) in args

        if len(ts_types) == 1:
            return f"{ts_types[0]} | null" if has_none else ts_types[0]
        else:
            union_type = " | ".join(ts_types)
            return f"({union_type}) | null" if has_none else f"({union_type})"

    # Handle List/Array
    if origin is list:
        if args:
            item_type = python_type_to_typescript(args[0])
            return f"Array<{item_type}>"
        return "Array<any>"

    # Handle Dict/Record
    if origin is dict:
        if len(args) == 2:
            key_type = python_type_to_typescript(args[0])
            value_type = python_type_to_typescript(args[1])
            return f"Record<{key_type}, {value_type}>"
        return "Record<string, any>"

    # Handle Enums
    if inspect.isclass(python_type) and issubclass(python_type, Enum):
        return python_type.__name__

    # Handle basic types
    type_name = getattr(python_type, "__name__", str(python_type))

    # Remove Optional wrapper if present
    type_name = type_name.replace("typing.", "").replace("Optional[", "").replace("]", "")

    return PYTHON_TO_TS_TYPE_MAP.get(type_name, type_name)


def generate_enum_ts(enum_class: type[Enum]) -> str:
    """
    Generate TypeScript enum from Python Enum.

    Args:
        enum_class: Python Enum class

    Returns:
        TypeScript enum declaration
    """
    ts_lines = [f"export enum {enum_class.__name__} {{"]

    for member in enum_class:
        # Convert snake_case to SCREAMING_SNAKE_CASE for TS enum keys
        ts_key = member.name
        ts_value = member.value

        ts_lines.append(f"  {ts_key} = \"{ts_value}\",")

    ts_lines.append("}")

    return "\n".join(ts_lines)


def generate_interface_ts(model_class) -> str:
    """
    Generate TypeScript interface from Pydantic model.

    Args:
        model_class: Pydantic model class

    Returns:
        TypeScript interface declaration
    """
    # Get model fields from Pydantic V2
    fields = model_class.model_fields

    ts_lines = [f"export interface {model_class.__name__} {{"]

    for field_name, field in fields.items():
        # Get field type (Pydantic V2 uses annotation)
        field_type = field.annotation

        # Convert to TypeScript type
        ts_type = python_type_to_typescript(field_type)

        # Check if field is optional (Pydantic V2 uses is_required())
        is_optional = not field.is_required()

        # Add field to interface
        optional_marker = "?" if is_optional else ""
        ts_lines.append(f"  {field_name}{optional_marker}: {ts_type};")

    ts_lines.append("}")

    return "\n".join(ts_lines)


def generate_typescript_types(output_path: str):
    """
    Generate all TypeScript types from Pydantic models.

    Args:
        output_path: Path to output TypeScript file
    """
    print(f"Generating TypeScript types from Pydantic models...")
    print(f"Output: {output_path}")

    ts_content = []

    # Header
    ts_content.append("/**")
    ts_content.append(" * TTS TypeScript Types")
    ts_content.append(" * ")
    ts_content.append(" * AUTO-GENERATED from apps/shared/tts/models.py")
    ts_content.append(f" * Generated: {datetime.now().isoformat()}Z")
    ts_content.append(" * ")
    ts_content.append(" * DO NOT EDIT THIS FILE MANUALLY")
    ts_content.append(" * Run: python apps/shared/tts/scripts/generate_typescript_types.py")
    ts_content.append(" */")
    ts_content.append("")

    # Generate enums
    print("\nGenerating enums...")
    enums = [AudioFormat, TTSProvider]

    for enum_class in enums:
        print(f"  - {enum_class.__name__}")
        ts_content.append(generate_enum_ts(enum_class))
        ts_content.append("")

    # Generate interfaces
    print("\nGenerating interfaces...")
    interfaces = [
        TTSCapabilities,
        TTSRequest,
        VoiceCloneRequest,
        ConversationRequest,
        TTSResponse,
        ProviderStatus,
        BatchTTSRequest,
        BatchTTSResponse,
    ]

    for model_class in interfaces:
        print(f"  - {model_class.__name__}")
        ts_content.append(generate_interface_ts(model_class))
        ts_content.append("")

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        f.write("\n".join(ts_content))

    print(f"\n✓ TypeScript types generated successfully!")
    print(f"  Output: {output_path}")
    print(f"  Total types: {len(enums)} enums + {len(interfaces)} interfaces")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate TypeScript types from Pydantic TTS models"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="/opt/kasaai/apps/shared/frontend/types/tts.ts",
        help="Output TypeScript file path"
    )

    args = parser.parse_args()

    try:
        generate_typescript_types(args.output)
        return 0

    except Exception as e:
        print(f"\n❌ Error generating TypeScript types: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
