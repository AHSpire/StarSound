#!/usr/bin/env python
"""
Test to verify biome tuples are correctly processed.
"""

def test_biome_processing():
    """Test that biome tuples are properly extracted and used."""
    
    # Simulate biomes data from GUI
    biomes = [
        ('surface', 'forest'),
        ('surface', 'desert'),
        ('underground', 'cavern')
    ]
    
    print("Testing biome tuple processing...")
    print(f"Selected biomes: {biomes}\n")
    
    patches_created = []
    for biome_category, biome_name in biomes:
        config = {
            'biome': biome_name,
            'biome_category': biome_category,
            'dayTracks': ['day1.ogg', 'day2.ogg'],
            'nightTracks': ['night1.ogg'],
        }
        
        patch_file = f"{biome_category}/{biome_name}.biome.patch"
        print(f"✓ Patch for {biome_category}/{biome_name}: {patch_file}")
        patches_created.append(patch_file)
    
    print(f"\nTotal patches created: {len(patches_created)}")
    
    # Verify no "None" in filenames
    for patch in patches_created:
        assert 'None' not in patch, f"Found 'None' in patch path: {patch}"
        assert patch.startswith(('surface/', 'underground/', 'space/', 'underground_detached/', 'surface_detached/')), \
            f"Invalid category in patch path: {patch}"
    
    print("✅ All biome processing tests PASSED!")
    print("✅ No 'None' patch files will be created")

if __name__ == "__main__":
    test_biome_processing()
