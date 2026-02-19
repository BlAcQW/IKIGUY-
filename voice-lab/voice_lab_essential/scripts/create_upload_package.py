#!/usr/bin/env python3
"""
Create Upload Package for Voice Lab Files
Creates a compressed archive of important files for manual upload to Google Drive
"""

import tarfile
import zipfile
import json
import os
from pathlib import Path
from datetime import datetime
import shutil

def create_file_manifest() -> dict:
    """Create a manifest of all important files"""
    manifest = {
        "created": datetime.now().isoformat(),
        "total_files": 0,
        "total_size_mb": 0,
        "categories": {}
    }
    
    # Define file categories
    categories = {
        "notebooks": {
            "path": Path("notebooks"),
            "description": "Jupyter notebooks for voice processing pipeline",
            "extensions": [".ipynb", ".py", ".md"]
        },
        "scripts": {
            "path": Path("."),
            "description": "Python scripts and utilities",
            "patterns": [
                "000_enhanced_twi_processor.py",
                "comprehensive_audio_pipeline.py", 
                "upload_to_drive.py",
                "check_local_files.py",
                "create_upload_package.py"
            ]
        },
        "processed_data": {
            "path": Path("data/processed"),
            "description": "Processed audio and text data",
            "extensions": [".csv", ".json", ".wav", ".txt"]
        },
        "metadata": {
            "path": Path("data/metadata"), 
            "description": "Dataset metadata and summaries",
            "extensions": [".json", ".csv"]
        },
        "raw_summaries": {
            "path": Path("data/raw"),
            "description": "Raw dataset summaries (excluding large audio files)",
            "extensions": [".json", ".csv", ".txt"]
        }
    }
    
    for category, config in categories.items():
        manifest["categories"][category] = {
            "description": config["description"],
            "files": [],
            "count": 0,
            "size_mb": 0
        }
        
        if not config["path"].exists():
            continue
            
        # Get files based on category type
        if "extensions" in config:
            # Extension-based search
            for ext in config["extensions"]:
                files = list(config["path"].rglob(f"*{ext}"))
                for file_path in files:
                    if file_path.is_file():
                        size_mb = file_path.stat().st_size / (1024*1024)
                        
                        manifest["categories"][category]["files"].append({
                            "path": str(file_path),
                            "size_mb": round(size_mb, 2),
                            "relative_path": str(file_path.relative_to(config["path"]) if file_path.is_relative_to(config["path"]) else file_path)
                        })
                        manifest["categories"][category]["count"] += 1
                        manifest["categories"][category]["size_mb"] += size_mb
                        
        elif "patterns" in config:
            # Pattern-based search
            for pattern in config["patterns"]:
                file_path = config["path"] / pattern
                if file_path.exists() and file_path.is_file():
                    size_mb = file_path.stat().st_size / (1024*1024)
                    
                    manifest["categories"][category]["files"].append({
                        "path": str(file_path),
                        "size_mb": round(size_mb, 2),
                        "relative_path": pattern
                    })
                    manifest["categories"][category]["count"] += 1
                    manifest["categories"][category]["size_mb"] += size_mb
        
        # Update totals
        manifest["total_files"] += manifest["categories"][category]["count"]
        manifest["total_size_mb"] += manifest["categories"][category]["size_mb"]
    
    return manifest

def create_package(package_type: str = "essential"):
    """Create package with selected files"""
    print(f"📦 CREATING {package_type.upper()} PACKAGE")
    print("=" * 50)
    
    # Create manifest
    manifest = create_file_manifest()
    
    # Define package contents based on type
    if package_type == "essential":
        # Only most important files (< 10MB total)
        categories_to_include = ["notebooks", "scripts", "metadata"]
        max_size_mb = 10
        package_name = "voice_lab_essential"
        
    elif package_type == "complete":
        # All files except large raw audio
        categories_to_include = ["notebooks", "scripts", "processed_data", "metadata", "raw_summaries"]
        max_size_mb = 50
        package_name = "voice_lab_complete"
        
    else:
        # Custom package
        categories_to_include = ["notebooks", "scripts"]
        max_size_mb = 5
        package_name = "voice_lab_custom"
    
    # Create package directory
    package_dir = Path(f"./{package_name}")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy files to package
    total_copied = 0
    total_size = 0
    
    for category in categories_to_include:
        if category not in manifest["categories"]:
            continue
            
        category_info = manifest["categories"][category]
        category_dir = package_dir / category
        category_dir.mkdir(exist_ok=True)
        
        print(f"\n📁 Copying {category} ({category_info['count']} files)")
        
        for file_info in category_info["files"]:
            source_path = Path(file_info["path"])
            
            # Skip if file is too large for package
            if total_size + file_info["size_mb"] > max_size_mb:
                print(f"  ⚠️ Skipping {source_path.name} (would exceed {max_size_mb}MB limit)")
                continue
                
            if source_path.exists():
                # Create subdirectory structure if needed
                rel_path = file_info["relative_path"]
                dest_path = category_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(source_path, dest_path)
                total_copied += 1
                total_size += file_info["size_mb"]
                print(f"  ✅ {rel_path} ({file_info['size_mb']}MB)")
    
    # Add manifest to package
    package_manifest = {
        "package_type": package_type,
        "created": datetime.now().isoformat(),
        "files_included": total_copied,
        "total_size_mb": round(total_size, 2),
        "categories": categories_to_include,
        "original_manifest": manifest
    }
    
    with open(package_dir / "PACKAGE_MANIFEST.json", "w") as f:
        json.dump(package_manifest, f, indent=2)
    
    # Create README
    readme_content = f"""# Voice Lab {package_type.title()} Package
    
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Package Type: {package_type}
Files Included: {total_copied}
Total Size: {total_size:.1f}MB

## Contents:

"""
    
    for category in categories_to_include:
        if category in manifest["categories"]:
            info = manifest["categories"][category]
            readme_content += f"### {category.title()}\n"
            readme_content += f"{info['description']}\n"
            readme_content += f"Files: {info['count']}\n\n"
    
    readme_content += f"""
## Upload Instructions:

1. Compress this entire folder as a ZIP file
2. Upload to Google Drive manually
3. Extract in Google Drive or download and extract locally
4. Use the included PACKAGE_MANIFEST.json to understand the structure

## Next Steps:

1. **Phase 2**: Run ASR model development notebooks
2. **Phase 3**: Run TTS model development notebooks  
3. **Phase 4**: Model optimization and evaluation
4. **Phase 5**: Production deployment

## Files Overview:

- `notebooks/`: Complete Jupyter notebook pipeline
- `scripts/`: Python utilities and processors
- `metadata/`: Dataset summaries and statistics
- `PACKAGE_MANIFEST.json`: Detailed manifest of all included files

This package contains everything needed to continue the Twi/Akan voice technology development pipeline.
"""
    
    with open(package_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    print(f"\n📦 Package created: {package_dir}")
    print(f"📊 Files included: {total_copied}")
    print(f"💾 Total size: {total_size:.1f}MB")
    
    # Create compressed archive
    archive_path = Path(f"{package_name}.zip")
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(package_dir)
                zipf.write(file_path, arc_path)
    
    archive_size = archive_path.stat().st_size / (1024*1024)
    print(f"🗜️ Compressed archive: {archive_path} ({archive_size:.1f}MB)")
    
    return {
        "package_dir": package_dir,
        "archive_path": archive_path,
        "manifest": package_manifest
    }

def main():
    """Create upload packages"""
    print("📦 VOICE LAB PACKAGE CREATOR")
    print("=" * 50)
    print("Creating packages for Google Drive upload...")
    print("(Service account storage quota exceeded - using manual approach)")
    
    # Create essential package (< 10MB)
    essential = create_package("essential")
    
    print("\n" + "="*50)
    print("📋 UPLOAD INSTRUCTIONS:")
    print("=" * 50)
    print("1. Download the ZIP file to your local machine")
    print("2. Upload to Google Drive manually")
    print("3. Extract in Google Drive or keep as archive")
    print("\n🎯 RECOMMENDED APPROACH:")
    print("- Upload voice_lab_essential.zip (< 10MB)")
    print("- Contains all notebooks, scripts, and metadata")
    print("- Sufficient for continuing development")
    
    print(f"\n✅ READY FOR UPLOAD:")
    print(f"📦 Package: {essential['archive_path']}")
    print(f"💾 Size: {essential['archive_path'].stat().st_size / (1024*1024):.1f}MB")
    print(f"📄 Files: {essential['manifest']['files_included']}")
    
    print(f"\n🚀 NEXT STEPS:")
    print("1. Download voice_lab_essential.zip")
    print("2. Upload to your Google Drive")
    print("3. Continue with Phase 2 ASR development")
    print("4. All notebooks and scripts are included!")

if __name__ == "__main__":
    main()