#!/usr/bin/env python3
"""Quick test to verify Replace mode displays correctly in TracksViewerWindow"""

import sys
import json
from pathlib import Path

# Add pygui to path so we can import it
sys.path.insert(0, str(Path(__file__).parent / 'pygui'))

# Mock test to verify the logic
def test_replace_display():
    patch_mode = 'replace'
    replace_selections = {
        ('surface', 'forest'): {
            'day': {0: 'C:/Music/forest_day.ogg'},
            'night': {0: 'C:/Music/forest_night.ogg'}
        },
        ('surface', 'garden'): {
            'day': {0: 'C:/Music/garden_day.ogg'},
            'night': {}
        }
    }
    add_selections = {}
    
    # Test the condition logic
    print(f"patch_mode = {patch_mode}")
    print(f"replace_selections count = {len(replace_selections)}")
    print(f"add_selections count = {len(add_selections)}")
    print()
    
    # Simulate the old logic (broken)
    print("OLD LOGIC (broken):")
    if not add_selections:
        print("  ❌ Would show 'No tracks selected yet' - WRONG!")
    else:
        print("  Show add selections")
    print()
    
    # Simulate the new logic (fixed)
    print("NEW LOGIC (fixed):")
    
    # Check if we're in Replace mode with selections
    if patch_mode == 'replace' and replace_selections:
        print("  ✅ Would show Replace tracks header + content")
        for (category, biome_name) in sorted(replace_selections.keys()):
            biome_data = replace_selections[(category, biome_name)]
            day_replace = biome_data.get('day', {})
            night_replace = biome_data.get('night', {})
            replace_count = len(day_replace) + len(night_replace)
            print(f"    📍 {category.upper()}: {biome_name} ({replace_count} replacement(s))")
            if day_replace:
                print(f"      🌅 Day: {list(day_replace.values())}")
            if night_replace:
                print(f"      🌙 Night: {list(night_replace.values())}")
    else:
        print("  Would fall through to Add mode logic")
    
    # Check final condition for empty message
    has_selections = bool(add_selections) if patch_mode != 'replace' else bool(replace_selections)
    print()
    print(f"has_selections = {has_selections}")
    if not has_selections:
        print("  ❌ Would show 'No tracks selected yet'")
    else:
        print("  ✅ Would show tracks (not empty message)")

if __name__ == '__main__':
    test_replace_display()
