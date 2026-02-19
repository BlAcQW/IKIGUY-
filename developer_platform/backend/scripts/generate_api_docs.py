#!/usr/bin/env python3
"""
Generate API reference documentation for KasaAI Developer Platform.

This script creates comprehensive markdown documentation for all API endpoints
based on the actual route definitions in the v1 API.

Usage:
    python scripts/generate_api_docs.py
"""

from pathlib import Path
from typing import Dict, List, Any


# API Endpoint definitions
API_ENDPOINTS = [
    # USAGE & ANALYTICS
    {
        "category": "usage",
        "file": "get-quota.md",
        "method": "GET",
        "path": "/api/v1/usage/quota",
        "title": "Get Quota Status",
        "description": "Retrieve current quota and usage limits for your API key",
        "auth_required": True,
        "parameters": [],
        "response_example": {
            "plan": "free",
            "daily": {
                "limit": 100,
                "used": 45,
                "remaining": 55,
                "reset_at": "2025-10-24T00:00:00Z"
            },
            "monthly": {
                "limit": 1000,
                "used": 456,
                "remaining": 544,
                "reset_at": "2025-11-01T00:00:00Z"
            }
        }
    },
    {
        "category": "usage",
        "file": "get-rate-limit.md",
        "method": "GET",
        "path": "/api/v1/usage/rate-limit",
        "title": "Get Rate Limit Status",
        "description": "Retrieve current rate limit information including remaining tokens",
        "auth_required": True,
        "parameters": [],
        "response_example": {
            "tokens_remaining": 8,
            "tokens_capacity": 20,
            "refill_rate": 10.0,
            "last_request": "2025-10-23T12:05:00Z"
        }
    },
    {
        "category": "usage",
        "file": "get-stats.md",
        "method": "GET",
        "path": "/api/v1/usage/stats",
        "title": "Get Usage Statistics",
        "description": "Retrieve detailed usage analytics for your API key",
        "auth_required": True,
        "parameters": [
            {
                "name": "days",
                "type": "integer",
                "in": "query",
                "required": False,
                "default": 30,
                "description": "Number of days to include (1-90)"
            }
        ],
        "response_example": {
            "total_requests": 150,
            "total_cost": 125.5,
            "avg_response_time_ms": 245.3,
            "requests_by_endpoint": {
                "/api/v1/assistants": 50,
                "/api/v1/calls": 100
            },
            "requests_by_status": {
                "200": 145,
                "201": 5
            },
            "daily_usage": [
                {"date": "2025-10-20", "requests": 30, "cost": 25.0},
                {"date": "2025-10-21", "requests": 45, "cost": 37.5}
            ]
        }
    },
    {
        "category": "usage",
        "file": "get-summary.md",
        "method": "GET",
        "path": "/api/v1/usage/summary",
        "title": "Get Usage Summary",
        "description": "Get comprehensive usage summary including quota, rate limits, and stats",
        "auth_required": True,
        "parameters": [],
        "response_example": {
            "quota": {"plan": "free", "daily": {}, "monthly": {}},
            "rate_limit": {"tokens_remaining": 8, "tokens_capacity": 20},
            "stats": {"total_requests": 150, "total_cost": 125.5}
        }
    },
]


def get_method_badge(method: str) -> str:
    """Get CSS class for HTTP method badge."""
    method_classes = {
        "GET": "method-get",
        "POST": "method-post",
        "PUT": "method-put",
        "PATCH": "method-patch",
        "DELETE": "method-delete",
    }
    return method_classes.get(method, "method-get")


def format_json_example(data: Any, indent: int = 0) -> str:
    """Format JSON data as a pretty-printed string."""
    import json
    return json.dumps(data, indent=2)


def generate_endpoint_doc(endpoint: Dict, output_dir: Path) -> None:
    """
    Generate markdown documentation for a single endpoint.

    Args:
        endpoint: Dictionary containing endpoint details
        output_dir: Directory to save the documentation file
    """
    lines = []

    # Front matter
    lines.extend([
        "---",
        f"title: {endpoint['title']}",
        f"description: {endpoint['description']}",
        "---",
        "",
        f"# {endpoint['title']}",
        "",
        endpoint['description'],
        "",
    ])

    # API endpoint box
    lines.extend([
        '<div class="api-endpoint">',
        '  <div class="api-endpoint__header">',
        f'    <span class="method-badge {get_method_badge(endpoint["method"])}">{endpoint["method"]}</span>',
        f'    <span class="api-endpoint__path">{endpoint["path"]}</span>',
        '  </div>',
        '</div>',
        "",
    ])

    # Authentication
    if endpoint.get('auth_required', True):
        lines.extend([
            "## Authentication",
            "",
            "This endpoint requires API key authentication via the `X-API-Key` header.",
            "",
        ])

    # Parameters
    parameters = endpoint.get('parameters', [])
    if parameters:
        lines.extend([
            "## Parameters",
            "",
            "| Parameter | Type | Location | Required | Description |",
            "|-----------|------|----------|----------|-------------|",
        ])

        for param in parameters:
            required = "✅ Yes" if param.get('required', False) else "No"
            default = param.get('default')
            desc = param['description']
            if default is not None:
                desc += f" (default: `{default}`)"

            lines.append(
                f"| `{param['name']}` | {param['type']} | {param.get('in', 'query')} | {required} | {desc} |"
            )

        lines.append("")

    # Request body
    request_body = endpoint.get('request_body')
    if request_body:
        lines.extend([
            "## Request Body",
            "",
            "```json",
            format_json_example(request_body),
            "```",
            "",
        ])

    # Response
    response_example = endpoint.get('response_example')
    if response_example:
        lines.extend([
            "## Response",
            "",
            "### Success Response (200 OK)",
            "",
            "```json",
            format_json_example(response_example),
            "```",
            "",
        ])

    # Example Request
    lines.extend([
        "## Example Request",
        "",
        "### cURL",
        "",
        "```bash",
        f'curl -X {endpoint["method"]} https://developer.ailabsafrica.com{endpoint["path"]} \\',
        '  -H "X-API-Key: your_api_key_here"',
    ])

    if parameters:
        query_params = [p for p in parameters if p.get('in') == 'query']
        if query_params:
            param_str = "&".join([f"{p['name']}={p.get('default', 'value')}" for p in query_params[:1]])
            lines[-1] += f' \\\n  "?{param_str}"'

    lines.extend([
        "```",
        "",
        "### Python",
        "",
        "```python",
        "import requests",
        "",
        f'url = "https://developer.ailabsafrica.com{endpoint["path"]}"',
        'headers = {"X-API-Key": "your_api_key_here"}',
        "",
        f'response = requests.{endpoint["method"].lower()}(url, headers=headers)',
        "data = response.json()",
        "print(data)",
        "```",
        "",
        "### JavaScript",
        "",
        "```javascript",
        f'const response = await fetch("https://developer.ailabsafrica.com{endpoint["path"]}", {{',
        f'  method: "{endpoint["method"]}",',
        '  headers: {',
        '    "X-API-Key": "your_api_key_here"',
        '  }',
        '});',
        "",
        "const data = await response.json();",
        "console.log(data);",
        "```",
        "",
    ])

    # Error Responses
    lines.extend([
        "## Error Responses",
        "",
        "### 401 Unauthorized",
        "",
        "Invalid or missing API key.",
        "",
        "```json",
        '{',
        '  "error": {',
        '    "code": "AUTHENTICATION_ERROR",',
        '    "message": "Invalid API key"',
        '  }',
        '}',
        "```",
        "",
        "### 429 Too Many Requests",
        "",
        "Rate limit exceeded.",
        "",
        "```json",
        '{',
        '  "error": {',
        '    "code": "RATE_LIMIT_EXCEEDED",',
        '    "message": "Rate limit exceeded. Please try again later.",',
        '    "retry_after": 30',
        '  }',
        '}',
        "```",
        "",
    ])

    # Related endpoints
    lines.extend([
        "## Related Endpoints",
        "",
    ])

    # Get related endpoints from same category
    related = [e for e in API_ENDPOINTS if e['category'] == endpoint['category'] and e['file'] != endpoint['file']]
    if related:
        for rel in related[:3]:
            lines.append(f"- [{rel['title']}](./{rel['file'].replace('.md', '')})")

    lines.append("")

    # Write file
    output_file = output_dir / endpoint['file']
    output_file.write_text("\n".join(lines))

    print(f"✅ Generated: {endpoint['file']}")


def main():
    """Main entry point."""
    print("🚀 KasaAI API Documentation Generator")
    print("=" * 50)

    try:
        # Determine output directory
        script_dir = Path(__file__).parent
        backend_dir = script_dir.parent
        apps_dir = backend_dir.parent.parent
        docs_dir = apps_dir / "docs" / "docs"

        if not docs_dir.exists():
            print(f"\n❌ Documentation directory not found: {docs_dir}")
            print("   Please ensure the docs site is set up first.")
            return 1

        # Group endpoints by category
        categories = {}
        for endpoint in API_ENDPOINTS:
            category = endpoint['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(endpoint)

        # Generate documentation
        print(f"\n📝 Generating API documentation...")
        print(f"   Output directory: {docs_dir / 'api-reference'}")
        print()

        total_endpoints = 0
        for category, endpoints in categories.items():
            category_dir = docs_dir / "api-reference" / category
            category_dir.mkdir(parents=True, exist_ok=True)

            print(f"📁 Category: {category} ({len(endpoints)} endpoints)")

            for endpoint in endpoints:
                generate_endpoint_doc(endpoint, category_dir)
                total_endpoints += 1

            print()

        print(f"✅ Generated {total_endpoints} endpoint documentation files!")
        print("\n💡 Next steps:")
        print("   1. Review generated files in apps/docs/docs/api-reference/")
        print("   2. Run 'npm run build' in apps/docs/ to rebuild the site")
        print("   3. Add more endpoints to this script as needed")
        print("   4. Commit changes to git")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
