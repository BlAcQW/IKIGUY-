# KasaAI Documentation Generation Scripts

This directory contains scripts for auto-generating API documentation from the backend codebase.

## Scripts

### `generate_api_docs.py`

Generates markdown documentation for API endpoints based on route definitions.

**Usage:**
```bash
python3 scripts/generate_api_docs.py
```

**What it does:**
- Reads API endpoint definitions from the script
- Generates comprehensive markdown documentation for each endpoint
- Includes code examples in cURL, Python, and JavaScript
- Adds authentication requirements and error responses
- Organizes docs by category (assistants, calls, workflows, usage, etc.)
- Outputs files to `apps/docs/docs/api-reference/`

**Output Structure:**
```
apps/docs/docs/api-reference/
├── usage/
│   ├── get-quota.md
│   ├── get-rate-limit.md
│   ├── get-stats.md
│   └── get-summary.md
├── assistants/
│   └── ... (future)
└── calls/
    └── ... (future)
```

## Adding New Endpoints

To add documentation for new endpoints:

1. Open `generate_api_docs.py`
2. Add an entry to the `API_ENDPOINTS` list:

```python
{
    "category": "assistants",  # Category name (creates subdirectory)
    "file": "create-assistant.md",  # Output filename
    "method": "POST",  # HTTP method
    "path": "/api/v1/assistants",  # API path
    "title": "Create Assistant",  # Document title
    "description": "Create a new voice assistant",  # Short description
    "auth_required": True,  # Requires API key
    "parameters": [  # Query/path parameters
        {
            "name": "param_name",
            "type": "string",
            "in": "query",
            "required": False,
            "default": "default_value",
            "description": "Parameter description"
        }
    ],
    "request_body": {  # Request body example (optional)
        "name": "My Assistant",
        "voice": {"provider": "elevenlabs"}
    },
    "response_example": {  # Response example
        "id": "asst_123",
        "status": "active"
    }
}
```

3. Run the script to generate documentation:
```bash
python3 scripts/generate_api_docs.py
```

4. Rebuild the docs site:
```bash
cd ../../../docs
npm run build
```

## Workflow Integration

### Manual Updates

After making changes to the API:

1. Update endpoint definitions in `generate_api_docs.py`
2. Run the generation script
3. Review generated markdown files
4. Rebuild and deploy the docs site

### CI/CD Integration (Future)

```yaml
# Example GitHub Actions workflow
name: Update API Docs
on:
  push:
    paths:
      - 'apps/developer_platform/backend/api/**'

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Generate API docs
        run: |
          python3 apps/developer_platform/backend/scripts/generate_api_docs.py
      - name: Build docs
        run: |
          cd apps/docs
          npm ci
          npm run build
      - name: Commit changes
        run: |
          git config user.name "Documentation Bot"
          git config user.email "bot@ailabsafrica.com"
          git add apps/docs/docs/api-reference/
          git commit -m "docs: Auto-update API reference" || echo "No changes"
          git push
```

## Documentation Standards

All generated documentation includes:

- ✅ **Front matter** - Title and description for Docusaurus
- ✅ **HTTP method badge** - Color-coded (GET, POST, PUT, DELETE, PATCH)
- ✅ **API path** - Full endpoint URL
- ✅ **Authentication** - API key requirements
- ✅ **Parameters** - Query, path, and header parameters
- ✅ **Request body** - JSON schema with examples
- ✅ **Response examples** - Success response with full JSON
- ✅ **Error responses** - Common error codes (401, 429, etc.)
- ✅ **Code examples** - cURL, Python, and JavaScript
- ✅ **Related endpoints** - Links to similar endpoints

## Troubleshooting

### Script fails with import errors

The script is standalone and doesn't import from the main app to avoid dependency issues.
All endpoint definitions are in the script itself.

### Documentation not showing up in Docusaurus

1. Check that files were generated in the correct directory
2. Verify sidebar configuration in `apps/docs/sidebars.ts`
3. Rebuild the docs site: `npm run build`

### Need to add more languages

Edit the `generate_endpoint_doc()` function and add code generation for:
- PHP
- Go
- Ruby
- Java
- etc.

## Future Enhancements

- [ ] Auto-extract endpoint definitions from FastAPI OpenAPI spec
- [ ] Generate TypeScript SDK documentation
- [ ] Add request/response validation examples
- [ ] Include rate limit information per endpoint
- [ ] Add changelog tracking for API versions
- [ ] Generate Postman/Insomnia collections
- [ ] Add interactive playground embeds

## Related Files

- `apps/docs/` - Docusaurus documentation site
- `apps/docs/docs/api-reference/` - Generated API documentation
- `apps/docs/sidebars.ts` - Sidebar configuration
- `apps/developer_platform/backend/api/v1/` - API route definitions
