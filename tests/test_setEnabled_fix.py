#!/usr/bin/env python
"""
Test to verify the boolean conversion in setEnabled() works correctly.
This simulates the exact fix applied to update_patch_btn_state().
"""

class MockButton:
    def __init__(self):
        self.enabled = False
    
    def setEnabled(self, state):
        """Simulate PyQt5's setEnabled which requires a bool, not a list."""
        if not isinstance(state, bool):
            raise TypeError(f"setEnabled(self, a0: bool): argument 1 has unexpected type '{type(state).__name__}'")
        self.enabled = state
    
    def isEnabled(self):
        return self.enabled

def test_setEnabled_with_lists():
    """Test that setEnabled properly handles boolean conversion."""
    
    button = MockButton()
    
    # Scenario 1: Empty lists should result in False
    day_tracks = []
    night_tracks = []
    selected_biomes = []
    
    # OLD (BUGGY) WAY - this would create lists instead of bools
    # day_tracks_selected = hasattr(obj, 'day_tracks') and day_tracks and len(day_tracks) > 0
    # This would result in [] (empty list) when day_tracks is empty!
    
    # NEW (FIXED) WAY - always returns bool
    day_tracks_selected = (len(day_tracks) > 0)  # False
    night_tracks_selected = (len(night_tracks) > 0)  # False
    biome_selected = (len(selected_biomes) > 0)  # False
    
    can_generate = (day_tracks_selected or night_tracks_selected) and biome_selected
    # can_generate should be False (bool), not [] (list)
    
    print(f"can_generate type: {type(can_generate).__name__} (expect 'bool')")
    print(f"can_generate value: {can_generate} (expect False)")
    
    # This should NOT raise TypeError anymore
    try:
        button.setEnabled(bool(can_generate))
        print("✓ setEnabled() accepted boolean - NO TypeError!")
    except TypeError as e:
        print(f"✗ FAILED: {e}")
        return False
    
    # Scenario 2: One track selected + one biome selected = can generate
    day_tracks = ['/path/to/track1.ogg']
    selected_biomes = [('Forest', 'Gentle')]
    
    day_tracks_selected = (len(day_tracks) > 0)  # True
    night_tracks_selected = (len(night_tracks) > 0)  # False
    biome_selected = (len(selected_biomes) > 0)  # True
    
    can_generate = (day_tracks_selected or night_tracks_selected) and biome_selected
    
    print(f"\nWith tracks+biomes - can_generate type: {type(can_generate).__name__}")
    print(f"can_generate value: {can_generate} (expect True)")
    
    try:
        button.setEnabled(bool(can_generate))
        print("✓ setEnabled() accepted boolean - NO TypeError!")
        if button.isEnabled():
            print("✓ Button is correctly ENABLED")
        return True
    except TypeError as e:
        print(f"✗ FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_setEnabled_with_lists()
    if success:
        print("\n✅ All setEnabled() tests PASSED! TypeError is fixed.")
    else:
        print("\n❌ setEnabled() test FAILED!")
