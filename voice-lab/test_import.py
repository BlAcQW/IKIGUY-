#!/usr/bin/env python3
"""Test the enhanced import mechanism"""

import os
import sys
import importlib.util

# Copy the 000_enhanced_twi_processor.py to current directory for testing
import shutil
shutil.copy("/opt/kasaai/apps/voice-lab/000_enhanced_twi_processor.py", "./000_enhanced_twi_processor.py")

print("Testing import mechanism...")
print("=" * 60)

# Test the import code from the notebook
loaded = False

# List of possible file locations
possible_paths = [
    "000_enhanced_twi_processor.py",
    "./000_enhanced_twi_processor.py",
]

for path in possible_paths:
    if os.path.exists(path):
        print(f"✅ Found processor at: {path}")
        spec = importlib.util.spec_from_file_location("enhanced_twi_processor", path)
        if spec and spec.loader:
            enhanced_twi_processor = importlib.util.module_from_spec(spec)
            sys.modules['enhanced_twi_processor'] = enhanced_twi_processor
            spec.loader.exec_module(enhanced_twi_processor)
            
            # Now import the class
            from enhanced_twi_processor import EnhancedTwiTextProcessor
            print(f"✅ Successfully imported EnhancedTwiTextProcessor")
            loaded = True
            
            # Test the processor
            processor = EnhancedTwiTextProcessor()
            result = processor.process_text("Me pɛ GH₵100")
            print(f"✅ Test processing: '{result['processed']}'")
            break

if loaded:
    print("\n✅ Import mechanism works correctly!")
else:
    print("\n❌ Import failed")

# Clean up
if os.path.exists("./000_enhanced_twi_processor.py"):
    os.remove("./000_enhanced_twi_processor.py")