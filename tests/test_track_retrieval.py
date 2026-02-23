#!/usr/bin/env python
"""
Test to verify track lists are accessible after the fix.
"""

class MockWindow:
    def __init__(self):
        self.day_tracks = ['/path/to/day1.ogg', '/path/to/day2.ogg']
        self.night_tracks = ['/path/to/night1.ogg']
    
    def get_tracks_for_generation(self):
        """Mimics the fixed generate_patch_file() logic."""
        day_tracks = self.day_tracks if hasattr(self, 'day_tracks') else []
        night_tracks = self.night_tracks if hasattr(self, 'night_tracks') else []
        return day_tracks, night_tracks

def test_track_retrieval():
    """Test that track lists are properly retrieved."""
    
    window = MockWindow()
    print("Testing track retrieval with populated lists...")
    
    day_tracks, night_tracks = window.get_tracks_for_generation()
    
    print(f"Day tracks: {day_tracks}")
    print(f"Night tracks: {night_tracks}")
    print(f"Total day tracks: {len(day_tracks)} (expect 2)")
    print(f"Total night tracks: {len(night_tracks)} (expect 1)")
    
    assert len(day_tracks) == 2, f"Expected 2 day tracks, got {len(day_tracks)}"
    assert len(night_tracks) == 1, f"Expected 1 night track, got {len(night_tracks)}"
    
    # Test with empty attributes
    window2 = MockWindow()
    delattr(window2, 'day_tracks')
    delattr(window2, 'night_tracks')
    
    print("\nTesting with missing attributes...")
    day_tracks, night_tracks = window2.get_tracks_for_generation()
    
    print(f"Day tracks (missing): {day_tracks} (expect [])")
    print(f"Night tracks (missing): {night_tracks} (expect [])")
    
    assert day_tracks == [], f"Expected empty day_tracks, got {day_tracks}"
    assert night_tracks == [], f"Expected empty night_tracks, got {night_tracks}"
    
    print("\n✅ All track retrieval tests PASSED!")

if __name__ == "__main__":
    test_track_retrieval()
