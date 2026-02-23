#!/usr/bin/env python3
"""
Test script to verify the mod generation workflow creates proper folder structure
"""

import sys
import json
from pathlib import Path
import shutil

# Add pygui to path
starsound_root = Path(__file__).parent
sys.path.insert(0, str(starsound_root / 'pygui'))

from utils.atomicwriter import create_mod_folder_structure

def test_create_mod_folder_structure():
    """Test that create_mod_folder_structure creates all required folders and _metadata"""
    
    test_staging = starsound_root / '.test_staging'
    test_mod_name = 'TestMod'
    
    # Cleanup if it exists
    if test_staging.exists():
        shutil.rmtree(test_staging)
    
    test_staging.mkdir(parents=True, exist_ok=True)
    
    print("[TEST] Creating mod folder structure...")
    try:
        result_path = create_mod_folder_structure(test_staging, test_mod_name)
        print(f"✅ Create function returned: {result_path}")
    except Exception as e:
        print(f"❌ Function failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify folder structure
    mod_path = test_staging / test_mod_name
    required_dirs = [
        'biomes/surface',
        'biomes/underground',
        'biomes/space',
        'music',
        'music_replacers',
        'music_add_and_replace',
        'outputs'
    ]
    
    print(f"\n[TEST] Checking if mod folder exists: {mod_path}")
    if not mod_path.exists():
        print(f"❌ Mod folder not created: {mod_path}")
        return False
    print(f"✅ Mod folder exists")
    
    print(f"\n[TEST] Checking required directories:")
    for dir_name in required_dirs:
        dir_path = mod_path / dir_name
        status = "✅" if dir_path.exists() else "❌"
        print(f"  {status} {dir_name}: {dir_path.exists()}")
        if not dir_path.exists():
            return False
    
    # Verify _metadata file
    metadata_file = mod_path / '_metadata'
    print(f"\n[TEST] Checking _metadata file: {metadata_file}")
    if not metadata_file.exists():
        print(f"❌ _metadata file not created")
        return False
    print(f"✅ _metadata file exists")
    
    # Parse metadata JSON
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        print(f"\n[TEST] _metadata contents:")
        for key, value in metadata.items():
            print(f"  ✅ {key}: {value}")
    except Exception as e:
        print(f"❌ Failed to parse _metadata: {e}")
        return False
    
    # Cleanup
    shutil.rmtree(test_staging)
    print(f"\n[TEST] Cleanup complete")
    print(f"\n✅ ALL TESTS PASSED!")
    return True

if __name__ == '__main__':
    success = test_create_mod_folder_structure()
    sys.exit(0 if success else 1)
