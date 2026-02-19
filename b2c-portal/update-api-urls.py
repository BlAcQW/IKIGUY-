#!/usr/bin/env python3
import os
import re
from pathlib import Path
import shutil
from datetime import datetime

# Create backup directory
backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copytree('src', backup_dir)
print(f"✅ Backup created at: {backup_dir}")

# Paths to process
src_dir = Path('src')
files_to_process = list(src_dir.glob('**/*.ts')) + list(src_dir.glob('**/*.tsx'))

# Skip the api-config file itself
files_to_process = [f for f in files_to_process if 'api-config' not in str(f)]

replacements_made = 0
files_updated = []

for file_path in files_to_process:
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Check if file contains hardcoded URLs
    if any(url in content for url in [
        'https://api.ailabsafrica.com',
        'https://flow-api.ailabsafrica.com',
        'http://localhost:8000',
        'http://localhost:30027'
    ]):
        # Check if already imports from api-config
        has_api_import = 'from @/config/api-config' in content or "from '@/config/api-config'" in content or 'from "@/config/api-config"' in content

        if not has_api_import:
            # Add import statement
            import_statement = "import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';\n"

            # Find where to insert import
            import_match = re.search(r'^import .* from .*$', content, re.MULTILINE)
            if import_match:
                # Find last import
                import_lines = re.findall(r'^import .* from .*$', content, re.MULTILINE)
                if import_lines:
                    last_import = import_lines[-1]
                    content = content.replace(last_import, last_import + '\n' + import_statement)
            else:
                # No imports, add at beginning
                content = import_statement + '\n' + content

        # Replace URL variable declarations
        content = re.sub(
            r"const API_BASE_URL\s*=\s*import\.meta\.env\.VITE_[A-Z_]+\s*\|\|\s*'https://api\.ailabsafrica\.com'",
            "// Using API_BASE_URL from api-config",
            content
        )
        content = re.sub(
            r"const API_BASE_URL\s*=\s*'https://api\.ailabsafrica\.com'",
            "// Using API_BASE_URL from api-config",
            content
        )
        content = re.sub(
            r"const API_URL\s*=\s*import\.meta\.env\.[A-Z_]+\s*\|\|\s*'https://api\.ailabsafrica\.com'",
            "const API_URL = API_BASE_URL",
            content
        )
        content = re.sub(
            r"const CORE_API_URL\s*=\s*import\.meta\.env\.[A-Z_]+\s*\|\|\s*'https://api\.ailabsafrica\.com'",
            "// Using CORE_API_URL from api-config",
            content
        )
        content = re.sub(
            r"const CORE_API_BASE_URL\s*=\s*import\.meta\.env\.[A-Z_]+\s*\|\|\s*'http://localhost:8000'",
            "const CORE_API_BASE_URL = CORE_API_URL",
            content
        )

        # Replace hardcoded URLs in strings (but not in comments or template literals)
        # This is tricky - we need to be careful not to break template literals

        # Replace in regular strings
        content = re.sub(r"'https://api\.ailabsafrica\.com'", "API_BASE_URL", content)
        content = re.sub(r'"https://api\.ailabsafrica\.com"', "API_BASE_URL", content)
        content = re.sub(r"'http://localhost:8000'", "CORE_API_URL", content)
        content = re.sub(r'"http://localhost:8000"', "CORE_API_URL", content)

        # Replace in template literals - need to use ${} syntax
        content = re.sub(r"`https://api\.ailabsafrica\.com", "`${API_BASE_URL}", content)
        content = re.sub(r"`http://localhost:8000", "`${CORE_API_URL}", content)

        # Fix any double slashes that might have been created
        content = re.sub(r"\$\{API_BASE_URL\}/", "${API_BASE_URL}/", content)
        content = re.sub(r"\$\{CORE_API_URL\}/", "${CORE_API_URL}/", content)

        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            files_updated.append(str(file_path))
            replacements_made += 1
            print(f"📝 Updated: {file_path}")

print(f"\n✅ Updated {replacements_made} files")
print(f"📁 Files updated: {len(files_updated)}")

if files_updated:
    print("\n📋 Updated files:")
    for f in files_updated[:10]:  # Show first 10
        print(f"   - {f}")
    if len(files_updated) > 10:
        print(f"   ... and {len(files_updated) - 10} more")