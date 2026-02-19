#!/usr/bin/env python3
"""
Check Local Files Available for Google Drive Upload
Scans the voice-lab directory and reports what's available for upload
"""

from pathlib import Path
import json

def scan_directory(directory: Path, max_depth: int = 3) -> dict:
    """Scan directory and return structure with file counts and sizes"""
    if not directory.exists():
        return {"status": "not_found"}
    
    result = {
        "status": "found",
        "total_files": 0,
        "total_size_mb": 0,
        "file_types": {},
        "subdirectories": {}
    }
    
    try:
        # Count files in current directory
        for item in directory.iterdir():
            if item.is_file():
                result["total_files"] += 1
                size_mb = item.stat().st_size / (1024 * 1024)
                result["total_size_mb"] += size_mb
                
                # Track file types
                ext = item.suffix.lower()
                if ext not in result["file_types"]:
                    result["file_types"][ext] = {"count": 0, "size_mb": 0}
                result["file_types"][ext]["count"] += 1
                result["file_types"][ext]["size_mb"] += size_mb
        
        # Recursively scan subdirectories (limited depth)
        if max_depth > 0:
            for subdir in directory.iterdir():
                if subdir.is_dir() and not subdir.name.startswith('.'):
                    subresult = scan_directory(subdir, max_depth - 1)
                    result["subdirectories"][subdir.name] = subresult
                    
                    if subresult["status"] == "found":
                        result["total_files"] += subresult["total_files"]
                        result["total_size_mb"] += subresult["total_size_mb"]
                        
    except Exception as e:
        result["error"] = str(e)
    
    return result

def main():
    """Check what local files are available for upload"""
    print("🔍 SCANNING LOCAL VOICE LAB FILES")
    print("=" * 50)
    
    base_dir = Path(".")
    
    # Define key directories to check
    directories_to_check = {
        "notebooks": "Jupyter notebooks",
        "data/processed": "Processed audio/text data", 
        "data/raw": "Raw datasets",
        "data/metadata": "Dataset metadata",
        "data/splits": "Train/val/test splits",
        ".": "Root directory files"
    }
    
    # Key files to check
    key_files = [
        "000_enhanced_twi_processor.py",
        "comprehensive_audio_pipeline.py", 
        "upload_to_drive.py",
        "check_local_files.py"
    ]
    
    scan_results = {}
    total_files = 0
    total_size_mb = 0
    
    print("\n📂 DIRECTORY SCAN:")
    for dir_path, description in directories_to_check.items():
        full_path = base_dir / dir_path
        result = scan_directory(full_path)
        scan_results[dir_path] = result
        
        if result["status"] == "found":
            print(f"✅ {description}: {full_path}")
            print(f"   📄 {result['total_files']} files ({result['total_size_mb']:.1f} MB)")
            
            # Show file types if any
            if result["file_types"]:
                print("   📊 File types:")
                for ext, info in sorted(result["file_types"].items()):
                    print(f"      {ext or 'no-extension'}: {info['count']} files ({info['size_mb']:.1f} MB)")
            
            total_files += result["total_files"]
            total_size_mb += result["total_size_mb"]
        else:
            print(f"❌ {description}: {full_path} (not found)")
        print()
    
    print("📄 KEY FILES:")
    for filename in key_files:
        file_path = base_dir / filename
        if file_path.exists():
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"✅ {filename} ({size_mb:.2f} MB)")
        else:
            print(f"❌ {filename} (not found)")
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"📁 Total files found: {total_files}")
    print(f"💾 Total size: {total_size_mb:.1f} MB")
    
    # Save detailed scan results
    scan_results["summary"] = {
        "total_files": total_files,
        "total_size_mb": total_size_mb,
        "scan_date": str(Path().resolve()),
        "base_directory": str(base_dir.resolve())
    }
    
    with open("local_files_scan.json", "w") as f:
        json.dump(scan_results, f, indent=2, default=str)
    
    print(f"📋 Detailed scan saved to: local_files_scan.json")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if total_files > 0:
        print(f"✅ You have {total_files} files ready for upload ({total_size_mb:.1f} MB)")
        print(f"🚀 Run: python upload_to_drive.py")
        
        if total_size_mb > 100:
            print(f"⚠️  Large upload size. Consider uploading in batches or excluding large files.")
    else:
        print(f"⚠️  No files found. Make sure you're running this from the voice-lab directory")
        print(f"🔄 Run the data acquisition and processing notebooks first")
    
    print(f"\n📋 Upload will organize files into Google Drive structure:")
    print(f"   📂 voice-lab-data/")
    print(f"      📁 notebooks/ (Jupyter notebooks)")
    print(f"      📁 processed/ (Processed datasets)")  
    print(f"      📁 raw/ (Raw datasets)")
    print(f"      📁 metadata/ (Dataset metadata)")
    print(f"      📁 splits/ (Train/val/test splits)")
    print(f"      📁 scripts/ (Python scripts)")

if __name__ == "__main__":
    main()