#!/usr/bin/env python
"""
Test the patch JSON formatting with blank line separator.
"""

import json
import sys
sys.path.insert(0, r'c:\Projects\StarSound\pygui')

from utils.patch_generator import generate_patch

def test_add_mode_formatting():
    """Test that 'add' mode creates properly formatted JSON with day/night separation."""
    
    config = {
        'biome': 'forest',
        'biome_category': 'surface',
        'dayTracks': [
            'animal_crossing_wild_world_2_00_am_piano_cover.ogg',
            'corridors_of_time.ogg',
            'old_runescape_soundtrack_book_of_spells.ogg'
        ],
        'nightTracks': [
            'okami_soundtrack_dragonpalace.ogg',
            'tribe_of_heavenly_gods_okami_extended.ogg',
            'diablo_tristram_village_seventwelve_strings_guitar.ogg'
        ],
        'patchMode': 'add',
        'modName': 'Test Mod'
    }
    
    result = generate_patch(r'c:\Projects\StarSound\staging\Test Mod', config)
    
    if result.get('success'):
        patch_path = result['patchPath']
        print(f"✓ Patch created: {patch_path}\n")
        
        with open(patch_path, 'r') as f:
            content = f.read()
        
        print("Patch content:")
        print(content)
        
        # Check for blank line separator
        lines = content.split('\n')
        blank_line_found = False
        for i, line in enumerate(lines):
            if line.strip() == '' and i > 0 and i < len(lines) - 1:  # blank line in middle
                blank_line_found = True
                print(f"\n✓ Blank line separator found at line {i + 1}")
        
        # Validate JSON (by removing blank lines for validation)
        try:
            json_validate = '\n'.join([line for line in lines if line.strip()])
            patch_data = json.loads(json_validate)
            print(f"✓ Valid JSON with {len(patch_data)} operations")
            
            # Count day and night operations
            day_ops = [op for op in patch_data if '/day/tracks' in op.get('path', '')]
            night_ops = [op for op in patch_data if '/night/tracks' in op.get('path', '')]
            
            print(f"✓ Day operations: {len(day_ops)}")
            print(f"✓ Night operations: {len(night_ops)}")
            
            # Verify format
            for i, op in enumerate(patch_data):
                assert 'op' in op, f"Operation {i} missing 'op'"
                assert 'path' in op, f"Operation {i} missing 'path'"
                assert 'value' in op, f"Operation {i} missing 'value'"
                
                # For add operations, verify /music/ prefix
                if op['op'] == 'add':
                    assert op['value'].startswith('/music/'), \
                        f"Operation {i} value missing /music/ prefix: {op['value']}"
            
            print("✓ All operations have correct structure")
            print("✓ All 'add' operations have /music/ prefix")
            
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON: {e}")
            return False
    else:
        print(f"✗ Patch generation failed: {result.get('message')}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_add_mode_formatting()
    if success:
        print("\n✅ JSON formatting test PASSED!")
    else:
        print("\n❌ JSON formatting test FAILED!")
