#!/bin/bash

# Script to replace hardcoded API URLs with environment variable references
# This will update all TypeScript and TypeScript React files

echo "Replacing hardcoded API URLs with environment variables..."

# Backup directory
BACKUP_DIR="./backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Create a backup of src directory
cp -r src "$BACKUP_DIR/"

# List of files to update (excluding the api-config.ts file itself)
FILES=$(find src -type f \( -name "*.ts" -o -name "*.tsx" \) ! -path "*/api-config.ts" ! -path "*/node_modules/*")

# Counter for replacements
TOTAL_REPLACEMENTS=0

for file in $FILES; do
    # Check if file contains hardcoded URLs
    if grep -q "https://api.ailabsafrica.com\|https://flow-api.ailabsafrica.com\|http://localhost:8000\|http://localhost:30027" "$file"; then
        echo "Processing: $file"

        # Create a temporary file
        temp_file="${file}.tmp"

        # First, add import statement if the file uses API URLs and doesn't already import api-config
        if ! grep -q "from.*api-config" "$file"; then
            # Check if file has other imports to add after
            if grep -q "^import" "$file"; then
                # Find the last import line and add our import after it
                awk '/^import/ { last_import = NR }
                     { lines[NR] = $0 }
                     END {
                         for (i = 1; i <= NR; i++) {
                             print lines[i]
                             if (i == last_import) {
                                 print "import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '\''@/config/api-config'\'';"
                             }
                         }
                     }' "$file" > "$temp_file"
            else
                # No imports, add at the beginning
                echo "import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';" > "$temp_file"
                cat "$file" >> "$temp_file"
            fi
        else
            cp "$file" "$temp_file"
        fi

        # Replace hardcoded URLs
        # Replace standalone URL declarations
        sed -i "s|const API_BASE_URL = import\.meta\.env\.VITE_[A-Z_]* || 'https://api\.ailabsafrica\.com'|const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://flow-api.ailabsafrica.com'|g" "$temp_file"
        sed -i "s|const CORE_API_URL = import\.meta\.env\.VITE_[A-Z_]* || 'https://api\.ailabsafrica\.com'|const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || 'https://flow-api.ailabsafrica.com'|g" "$temp_file"
        sed -i "s|const API_URL = import\.meta\.env\.VITE_[A-Z_]* || 'https://api\.ailabsafrica\.com'|const API_URL = import.meta.env.VITE_API_URL || 'https://flow-api.ailabsafrica.com'|g" "$temp_file"

        # Replace direct string literals in fetch calls and other uses
        sed -i "s|'https://api\.ailabsafrica\.com'|API_BASE_URL|g" "$temp_file"
        sed -i "s|\"https://api\.ailabsafrica\.com\"|API_BASE_URL|g" "$temp_file"
        sed -i "s|'https://flow-api\.ailabsafrica\.com'|API_BASE_URL|g" "$temp_file"
        sed -i "s|\"https://flow-api\.ailabsafrica\.com\"|API_BASE_URL|g" "$temp_file"
        sed -i "s|'http://localhost:8000'|CORE_API_URL|g" "$temp_file"
        sed -i "s|\"http://localhost:8000\"|CORE_API_URL|g" "$temp_file"

        # Replace template literals
        sed -i "s|\`https://api\.ailabsafrica\.com|\`\${API_BASE_URL}|g" "$temp_file"
        sed -i "s|\`https://flow-api\.ailabsafrica\.com|\`\${API_BASE_URL}|g" "$temp_file"
        sed -i "s|\`http://localhost:8000|\`\${CORE_API_URL}|g" "$temp_file"

        # Move temp file back
        mv "$temp_file" "$file"

        TOTAL_REPLACEMENTS=$((TOTAL_REPLACEMENTS + 1))
    fi
done

echo "✅ Replaced hardcoded URLs in $TOTAL_REPLACEMENTS files"
echo "📁 Backup created at: $BACKUP_DIR"
echo ""
echo "⚠️  Please review the changes and ensure:"
echo "   1. All imports are correctly added"
echo "   2. No duplicate imports were created"
echo "   3. The application still builds correctly"