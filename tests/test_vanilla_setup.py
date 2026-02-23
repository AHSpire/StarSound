#!/usr/bin/env python3
"""Test vanilla_setup.py to verify it works with new paths"""

import sys
from pathlib import Path

# Add pygui to path
sys.path.insert(0, str(Path(__file__).parent / 'pygui'))

from utils.vanilla_setup import VanillaSetup
import json

def test_paths():
    """Test that vanilla_setup can initialize paths correctly"""
    setup = VanillaSetup()
    starsound_dir = Path(__file__).parent
    starbound_path = "c:\\Steam\\steamapps\\common\\Starbound"
    
    setup.initialize_paths(starbound_path, str(starsound_dir))
    
    print("✓ Paths initialized")
    print(f"  - biome_tracks_json: {setup.biome_tracks_json}")
    print(f"  - biome_tracks_json exists: {setup.biome_tracks_json.exists()}")
    print(f"  - vanilla_tracks_dir: {setup.vanilla_tracks_dir}")
    
    # Test that biome_tracks.json is accessible
    if setup.biome_tracks_json.exists():
        with open(setup.biome_tracks_json, 'r') as f:
            data = json.load(f)
            print(f"✓ biome_tracks.json loaded successfully")
            print(f"  - Number of biomes: {len(data)}")
            
            # Check structure
            first_biome = list(data.values())[0]
            if isinstance(first_biome, dict) and 'day' in first_biome and 'night' in first_biome:
                print(f"✓ biome_tracks.json has correct format (dict with day/night)")
                return True
            else:
                print(f"✗ biome_tracks.json format is wrong")
                print(f"  - First biome type: {type(first_biome)}")
                print(f"  - First biome keys: {list(first_biome.keys()) if isinstance(first_biome, dict) else 'N/A'}")
                return False
    else:
        print(f"✗ biome_tracks.json not found at {setup.biome_tracks_json}")
        return False

if __name__ == '__main__':
    print("Testing vanilla_setup.py...")
    if test_paths():
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Tests failed")
        sys.exit(1)
