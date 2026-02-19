#!/usr/bin/env python
"""
Monitor background processing jobs
Check progress of Bible TTS and MichSet extraction
"""

from pathlib import Path
import time
import os

# Paths
BASE_DIR = Path("G:/My Drive/voice-lab-data")
PROCESSED_DIR = BASE_DIR / "processed"
BIBLE_DIR = PROCESSED_DIR / "bible_tts_complete"
MICHSET_DIR = PROCESSED_DIR / "michset_extracted_audio"

print("MONITORING BACKGROUND PROCESSING")
print("=" * 60)

def check_directory_progress(dir_path, name):
    """Check progress by counting files in directory"""
    if not dir_path.exists():
        return f"{name}: Directory not created yet"
    
    # Count files
    csv_files = list(dir_path.glob("*.csv"))
    json_files = list(dir_path.glob("*.json"))
    total_files = len(list(dir_path.rglob("*")))
    
    return f"{name}: {len(csv_files)} CSV, {len(json_files)} JSON, {total_files} total files"

def check_log_file(log_path):
    """Check last lines of log file"""
    if not log_path.exists():
        return "Log file not found"
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            if lines:
                # Get last 5 lines
                last_lines = lines[-5:]
                return ''.join(last_lines)
            else:
                return "Log file empty"
    except Exception as e:
        return f"Error reading log: {str(e)[:50]}"

# Check Bible TTS progress
print("\n1. BIBLE TTS PROCESSING")
print("-" * 40)
print(check_directory_progress(BIBLE_DIR, "Bible TTS"))

bible_log = Path("bible_tts_processing.log")
if bible_log.exists():
    print("\nLatest log entries:")
    print(check_log_file(bible_log))

# Check MichSet extraction progress  
print("\n2. MICHSET ARROW EXTRACTION")
print("-" * 40)
print(check_directory_progress(MICHSET_DIR, "MichSet"))

michset_log = Path("michset_extraction.log")
if michset_log.exists():
    print("\nLatest log entries:")
    print(check_log_file(michset_log))

# Check if processes are still running
print("\n3. PROCESS STATUS")
print("-" * 40)

# Check for Python processes
import subprocess
try:
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                          capture_output=True, text=True, timeout=5)
    python_processes = result.stdout.count('python.exe')
    print(f"Python processes running: {python_processes}")
except:
    print("Could not check process status")

print("\n" + "=" * 60)
print("Monitor complete. Processes are running in background.")
print("Check log files for detailed progress:")
print("  - bible_tts_processing.log")
print("  - michset_extraction.log")