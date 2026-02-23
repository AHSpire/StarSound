#!/usr/bin/env python3
"""Test the vanilla setup flow to isolate any issues"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'pygui'))

from utils.vanilla_setup import VanillaSetup
from utils.starbound_locator import find_starbound_folder

def test_complete_flow():
    """Test the complete vanilla setup workflow"""
    
    print("=" * 60)
    print("VANILLA SETUP TEST - Simulating User Without Tracks")
    print("=" * 60)
    
    starsound_dir = Path(__file__).parent
    starbound_path = find_starbound_folder()
    
    print(f"\n1. Locating Starbound:")
    print(f"   - Found at: {starbound_path}")
    
    setup = VanillaSetup()
    setup.initialize_paths(str(starbound_path), str(starsound_dir))
    
    print(f"\n2. Checking requirements:")
    success, msg = setup.check_requirements()
    print(f"   - {msg}")
    if not success:
        print(f"   ERROR: {msg}")
        return False
    
    print(f"\n3. Creating backup of packed.pak...")
    success, msg = setup.backup_packed_pak()
    if success:
        print(f"   ✓ Backup created: {msg}")
    else:
        print(f"   ✗ Backup failed: {msg}")
        return False
    
    print(f"\n4. Running asset unpacker...")
    temp_dir = starsound_dir / 'pygui' / '_temp_unpack_test'
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    success, msg = setup.unpack_assets(str(temp_dir))
    if success:
        print(f"   ✓ Unpacking complete")
        # Check what's in temp_dir
        music_dir = temp_dir / 'music'
        if music_dir.exists():
            ogg_count = len(list(music_dir.glob('*.ogg')))
            print(f"   ✓ Found {ogg_count} music files in unpacked assets")
        else:
            print(f"   ✗ No music directory in unpacked assets!")
            return False
    else:
        print(f"   ✗ Unpacking failed: {msg}")
        return False
    
    print(f"\n5. Loading biome_tracks.json...")
    if setup.biome_tracks_json.exists():
        with open(setup.biome_tracks_json, 'r') as f:
            biome_data = json.load(f)
        print(f"   ✓ Loaded {len(biome_data)} biome entries")
        
        # Validate format
        sample = list(biome_data.values())[0]
        if isinstance(sample, dict) and 'day' in sample and 'night' in sample:
            print(f"   ✓ Format is correct (dict with day/night keys)")
        else:
            print(f"   ✗ Format is incorrect")
            return False
    else:
        print(f"   ✗ biome_tracks.json not found at {setup.biome_tracks_json}")
        return False
    
    print(f"\n6. Organizing music files...")
    # Create a test vanilla_tracks to avoid overwriting real one
    test_vanilla_dir = starsound_dir / 'pygui' / '_vanilla_tracks_test'
    if test_vanilla_dir.exists():
        import shutil
        shutil.rmtree(test_vanilla_dir)
    test_vanilla_dir.mkdir(parents=True, exist_ok=True)
    
    # Temporarily override vanilla_tracks_dir
    original_dir = setup.vanilla_tracks_dir
    setup.vanilla_tracks_dir = test_vanilla_dir
    
    success, msg = setup.organize_music_files(str(temp_dir), biome_data)
    if success:
        print(f"   ✓ {msg}")
        
        # Check what was created
        if test_vanilla_dir.exists():
            biome_count = len(list(test_vanilla_dir.glob('*/*')))
            print(f"   ✓ Created {biome_count} biome directories")
        else:
            print(f"   ✗ vanilla_tracks directory not created")
            return False
    else:
        print(f"   ✗ Organization failed: {msg}")
        return False
    
    print(f"\n7. Cleanup...")
    setup.cleanup_unpacked_files(str(temp_dir))
    print(f"   ✓ Temporary files cleaned")
    
    # Clean up test directories
    import shutil
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    if test_vanilla_dir.exists():
        shutil.rmtree(test_vanilla_dir)
    
    print("\n" + "=" * 60)
    print("✓ COMPLETE SETUP TEST PASSED!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    try:
        if test_complete_flow():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
