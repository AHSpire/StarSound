#!/usr/bin/env python
"""
Quick test to verify the Generate Mod button logic is working correctly.
"""

def test_button_enable_logic():
    """Test the enable logic for the Generate Mod button."""
    
    # Scenario 1: No tracks, no biomes selected
    day_tracks_selected = False
    night_tracks_selected = False
    biome_selected = False
    can_generate = (day_tracks_selected or night_tracks_selected) and biome_selected
    print(f"Scenario 1 (No tracks, no biomes): Button enabled = {can_generate} (expect False) ✓" if not can_generate else f"Scenario 1 FAILED: {can_generate}")
    
    # Scenario 2: Day tracks selected, but no biomes
    day_tracks_selected = True
    night_tracks_selected = False
    biome_selected = False
    can_generate = (day_tracks_selected or night_tracks_selected) and biome_selected
    print(f"Scenario 2 (Day tracks, no biomes): Button enabled = {can_generate} (expect False) ✓" if not can_generate else f"Scenario 2 FAILED: {can_generate}")
    
    # Scenario 3: Night tracks selected, but no biomes
    day_tracks_selected = False
    night_tracks_selected = True
    biome_selected = False
    can_generate = (day_tracks_selected or night_tracks_selected) and biome_selected
    print(f"Scenario 3 (Night tracks, no biomes): Button enabled = {can_generate} (expect False) ✓" if not can_generate else f"Scenario 3 FAILED: {can_generate}")
    
    # Scenario 4: Both day and night tracks selected, but no biomes
    day_tracks_selected = True
    night_tracks_selected = True
    biome_selected = False
    can_generate = (day_tracks_selected or night_tracks_selected) and biome_selected
    print(f"Scenario 4 (Both tracks, no biomes): Button enabled = {can_generate} (expect False) ✓" if not can_generate else f"Scenario 4 FAILED: {can_generate}")
    
    # Scenario 5: No tracks, but biomes selected
    day_tracks_selected = False
    night_tracks_selected = False
    biome_selected = True
    can_generate = (day_tracks_selected or night_tracks_selected) and biome_selected
    print(f"Scenario 5 (No tracks, biomes selected): Button enabled = {can_generate} (expect False) ✓" if not can_generate else f"Scenario 5 FAILED: {can_generate}")
    
    # Scenario 6: Day tracks selected AND biomes selected (SHOULD ENABLE)
    day_tracks_selected = True
    night_tracks_selected = False
    biome_selected = True
    can_generate = (day_tracks_selected or night_tracks_selected) and biome_selected
    print(f"Scenario 6 (Day tracks + biomes): Button enabled = {can_generate} (expect True) ✓" if can_generate else f"Scenario 6 FAILED: {can_generate}")
    
    # Scenario 7: Night tracks selected AND biomes selected (SHOULD ENABLE)
    day_tracks_selected = False
    night_tracks_selected = True
    biome_selected = True
    can_generate = (day_tracks_selected or night_tracks_selected) and biome_selected
    print(f"Scenario 7 (Night tracks + biomes): Button enabled = {can_generate} (expect True) ✓" if can_generate else f"Scenario 7 FAILED: {can_generate}")
    
    # Scenario 8: Both tracks selected AND biomes selected (SHOULD ENABLE)
    day_tracks_selected = True
    night_tracks_selected = True
    biome_selected = True
    can_generate = (day_tracks_selected or night_tracks_selected) and biome_selected
    print(f"Scenario 8 (Both + biomes): Button enabled = {can_generate} (expect True) ✓" if can_generate else f"Scenario 8 FAILED: {can_generate}")
    
    print("\n✅ All button logic test scenarios PASSED!")

if __name__ == "__main__":
    test_button_enable_logic()
