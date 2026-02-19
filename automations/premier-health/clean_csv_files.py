#!/usr/bin/env python3
"""
Clean CSV files by removing header-only rows.
"""

import pandas as pd
from pathlib import Path

CSV_DIR = Path("/opt/kasaai/apps/automations/premier-health/regional_cities/enriched/")

def clean_csv_file(csv_path):
    """Remove header-only rows from CSV file."""
    print(f"\n📄 Processing {csv_path.name}...")
    
    df = pd.read_csv(csv_path)
    original_count = len(df)
    
    # Check which columns exist
    has_provider_num = 'provider number' in df.columns
    has_name = 'NAME OF HOSPITAL / CLINIC' in df.columns
    has_specialty = 'SPECIALITY' in df.columns
    
    if not (has_name and has_specialty):
        print(f"   ⚠️  Skipping - missing required columns")
        return 0
    
    # Build filter conditions
    conditions = [
        df['NAME OF HOSPITAL / CLINIC'].notna(),  # Has provider name
        df['SPECIALITY'].notna()  # Has specialty
    ]
    
    if has_provider_num:
        conditions.append(df['provider number'].notna())  # Has provider number
    
    # Apply all conditions
    cleaned_df = df.copy()
    for condition in conditions:
        cleaned_df = cleaned_df[condition]
    
    removed_count = original_count - len(cleaned_df)
    
    if removed_count > 0:
        # Save cleaned version
        cleaned_df.to_csv(csv_path, index=False)
        print(f"   ✅ Removed {removed_count} header rows ({original_count} → {len(cleaned_df)} rows)")
    else:
        print(f"   ℹ️  No header rows to remove")
    
    return removed_count


def main():
    """Clean all CSV files."""
    print("🧹 CLEANING CSV FILES")
    print("=" * 80)
    
    csv_files = list(CSV_DIR.glob("*_enriched.csv"))
    total_removed = 0
    
    for csv_path in sorted(csv_files):
        try:
            removed = clean_csv_file(csv_path)
            total_removed += removed
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY: Removed {total_removed} header rows across {len(csv_files)} files")
    print("=" * 80)


if __name__ == "__main__":
    main()
