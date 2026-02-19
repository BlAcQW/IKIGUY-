#!/usr/bin/env python3
"""
Generate API documentation from OpenAPI spec.

This script extracts the OpenAPI specification from the FastAPI app
and generates markdown documentation for Docusaurus.

Usage:
    python scripts/generate_docs.py
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List


def get_openapi_spec() -> Dict[str, Any]:
    """
    Get OpenAPI spec from FastAPI app.

    Returns:
        Dict containing OpenAPI specification
    """
    # Add backend directory to path
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir))

    # Import main module - this will trigger all imports
    import main

    # Get OpenAPI schema from FastAPI
    openapi_spec = main.app.openapi()

    return openapi_spec


def format_parameter_type(param: Dict[str, Any]) -> str:
    """Format parameter type for documentation."""
    schema = param.get("schema", {})
    param_type = schema.get("type", "string")

    if "enum" in schema:
        return f"{param_type} (enum)"
    elif param_type == "array":
        items_type = schema.get("items", {}).get("type", "any")
        return f"array<{items_type}>"

    return param_type


def format_request_body(request_body: Dict[str, Any]) -> str:
    """Format request body schema for documentation."""
    if not request_body:
        return ""

    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})

    # Try to get the schema reference or properties
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return f"See `{ref_name}` schema"

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    if not properties:
        return "JSON object"

    lines = ["```json", "{"]
    for prop_name, prop_schema in properties.items():
        prop_type = prop_schema.get("type", "any")
        is_required = prop_name in required
        req_marker = " (required)" if is_required else " (optional)"

        # Get example or default
        example = prop_schema.get("example", prop_schema.get("default"))
        if example is not None:
            if isinstance(example, str):
                lines.append(f'  "{prop_name}": "{example}",{req_marker}')
            else:
                lines.append(f'  "{prop_name}": {json.dumps(example)},{req_marker}')
        else:
            if prop_type == "string":
                lines.append(f'  "{prop_name}": "...",{req_marker}')
            elif prop_type == "number" or prop_type == "integer":
                lines.append(f'  "{prop_name}": 0,{req_marker}')
            elif prop_type == "boolean":
                lines.append(f'  "{prop_name}": true,{req_marker}')
            elif prop_type == "object":
                lines.append(f'  "{prop_name}": {{}},{req_marker}')
            elif prop_type == "array":
                lines.append(f'  "{prop_name}": []{req_marker}')

    lines.append("}")
    lines.append("```")

    return "\n".join(lines)


def format_response(response: Dict[str, Any]) -> str:
    """Format response schema for documentation."""
    content = response.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})

    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return f"See `{ref_name}` schema"

    return "JSON object"


def get_http_method_badge(method: str) -> str:
    """Get method badge class for styling."""
    method_colors = {
        "get": "method-get",
        "post": "method-post",
        "put": "method-put",
        "patch": "method-patch",
        "delete": "method-delete",
    }
    return method_colors.get(method.lower(), "method-get")


def generate_endpoint_doc(
    path: str,
    method: str,
    operation: Dict[str, Any],
    output_dir: Path
) -> None:
    """
    Generate markdown documentation for a single endpoint.

    Args:
        path: API path (e.g., /api/v1/assistants)
        method: HTTP method (GET, POST, etc.)
        operation: OpenAPI operation object
        output_dir: Directory to save documentation
    """
    # Extract endpoint details
    summary = operation.get("summary", "")
    description = operation.get("description", "")
    operation_id = operation.get("operationId", "")
    parameters = operation.get("parameters", [])
    request_body = operation.get("requestBody")
    responses = operation.get("responses", {})

    # Determine file name from operation_id or path
    if operation_id:
        # Convert operation_id like "create_assistant_v1" to "create-assistant"
        file_name = operation_id.replace("_v1", "").replace("_", "-")
    else:
        # Fallback: use path segments
        file_name = path.split("/")[-1] or "root"
        file_name = f"{method.lower()}-{file_name}"

    file_name = f"{file_name}.md"

    # Build markdown content
    md_lines = [
        "---",
        f"title: {summary or 'API Endpoint'}",
        f"description: {description[:100] if description else summary}",
        "---",
        "",
        f"# {summary or method.upper() + ' ' + path}",
        "",
    ]

    if description:
        md_lines.extend([
            description,
            "",
        ])

    # HTTP method and path
    md_lines.extend([
        '<div class="api-endpoint">',
        '  <div class="api-endpoint__header">',
        f'    <span class="method-badge {get_http_method_badge(method)}">{method.upper()}</span>',
        f'    <span class="api-endpoint__path">{path}</span>',
        '  </div>',
        '</div>',
        "",
    ])

    # Authentication
    md_lines.extend([
        "## Authentication",
        "",
        "This endpoint requires API key authentication.",
        "",
        "```bash",
        f'curl -X {method.upper()} https://developer.ailabsafrica.com{path} \\',
        '  -H "X-API-Key: your_api_key_here"',
        "```",
        "",
    ])

    # Parameters
    if parameters:
        md_lines.extend([
            "## Parameters",
            "",
            "| Parameter | Type | Required | Description |",
            "|-----------|------|----------|-------------|",
        ])

        for param in parameters:
            param_name = param.get("name", "")
            param_in = param.get("in", "query")
            param_required = param.get("required", False)
            param_desc = param.get("description", "")
            param_type = format_parameter_type(param)

            required_badge = "✅ Yes" if param_required else "No"

            md_lines.append(
                f"| `{param_name}` ({param_in}) | {param_type} | {required_badge} | {param_desc} |"
            )

        md_lines.append("")

    # Request Body
    if request_body:
        md_lines.extend([
            "## Request Body",
            "",
            format_request_body(request_body),
            "",
        ])

    # Responses
    if responses:
        md_lines.extend([
            "## Responses",
            "",
        ])

        for status_code, response in responses.items():
            response_desc = response.get("description", "")
            md_lines.extend([
                f"### {status_code} - {response_desc}",
                "",
                format_response(response),
                "",
            ])

    # Example request
    md_lines.extend([
        "## Example Request",
        "",
        "```bash",
        f'curl -X {method.upper()} https://developer.ailabsafrica.com{path} \\',
        '  -H "X-API-Key: your_api_key_here" \\',
        '  -H "Content-Type: application/json"',
    ])

    if request_body and method.upper() != "GET":
        md_lines.append('  -d \'{"key": "value"}\'')

    md_lines.extend([
        "```",
        "",
    ])

    # Write to file
    output_file = output_dir / file_name
    output_file.write_text("\n".join(md_lines))

    print(f"✅ Generated: {output_file.relative_to(output_file.parent.parent.parent)}")


def generate_docs_from_openapi(spec: Dict[str, Any], docs_dir: Path) -> None:
    """
    Generate markdown documentation from OpenAPI spec.

    Args:
        spec: OpenAPI specification dictionary
        docs_dir: Root documentation directory
    """
    paths = spec.get("paths", {})

    # Create output directories
    api_ref_dir = docs_dir / "api-reference"
    api_ref_dir.mkdir(parents=True, exist_ok=True)

    # Group endpoints by category
    categories: Dict[str, List[tuple]] = {}

    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                continue

            # Determine category from tags or path
            tags = operation.get("tags", [])
            category = tags[0] if tags else "General"

            # Clean category name
            category = category.lower().replace(" ", "-").replace("(", "").replace(")", "")

            if category not in categories:
                categories[category] = []

            categories[category].append((path, method, operation))

    # Generate documentation for each category
    for category, endpoints in categories.items():
        category_dir = api_ref_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n📁 Category: {category}")

        for path, method, operation in endpoints:
            generate_endpoint_doc(path, method, operation, category_dir)

    print(f"\n✅ Documentation generated in {api_ref_dir.relative_to(docs_dir.parent)}")


def main():
    """Main entry point."""
    print("🚀 KasaAI API Documentation Generator")
    print("=" * 50)

    try:
        # Get OpenAPI spec
        print("\n📥 Fetching OpenAPI specification...")
        spec = get_openapi_spec()

        print(f"✅ Found API: {spec.get('info', {}).get('title')}")
        print(f"   Version: {spec.get('info', {}).get('version')}")
        print(f"   Endpoints: {len(spec.get('paths', {}))}")

        # Determine docs directory
        script_dir = Path(__file__).parent
        backend_dir = script_dir.parent
        apps_dir = backend_dir.parent.parent
        docs_dir = apps_dir / "docs" / "docs"

        if not docs_dir.exists():
            print(f"\n❌ Documentation directory not found: {docs_dir}")
            print("   Please ensure the docs site is set up first.")
            return 1

        # Generate documentation
        print(f"\n📝 Generating documentation to {docs_dir}...")
        generate_docs_from_openapi(spec, docs_dir)

        print("\n✅ Documentation generation complete!")
        print("\n💡 Next steps:")
        print("   1. Review generated files in apps/docs/docs/api-reference/")
        print("   2. Run 'npm run build' in apps/docs/ to rebuild the site")
        print("   3. Commit changes to git")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
