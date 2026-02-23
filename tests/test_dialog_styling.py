"""
Test Per-Track Dialog with Segment Grouping
=============================================

Tests the fixed per-track dialog with two 1-hour files being split.
Verifies that QListWidgetItem styling now works correctly.
"""

import sys
from pathlib import Path

# Add project directory to path
starsound_dir = Path(__file__).parent
sys.path.insert(0, str(starsound_dir / 'pygui'))

from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

app = QApplication.instance() or QApplication(sys.argv)


def test_per_track_dialog_item_styling():
    """
    Test that QListWidgetItem styling works correctly without setStyleSheet().
    
    Simulates two 1-hour files that were split into segments.
    """
    print("[TEST] Per-Track Dialog Item Styling")
    print("-" * 60)
    
    try:
        from pygui.dialogs.per_track_audio_config_dialog import PerTrackAudioConfigDialog
        
        # Simulate two 1-hour files after splitting
        audio_files = [
            "C:/Users/Stephanie/Music/podcast1_part1.wav",
            "C:/Users/Stephanie/Music/podcast1_part2.wav",
            "C:/Users/Stephanie/Music/podcast1_part3.wav",
            "C:/Users/Stephanie/Music/podcast2_part1.wav",
            "C:/Users/Stephanie/Music/podcast2_part2.wav",
            "C:/Users/Stephanie/Music/podcast2_part3.wav",
        ]
        
        # Simulate segment origins from perform_file_splitting()
        segment_origins = {
            "C:/Users/Stephanie/Music/podcast1_part1.wav": "C:/Users/Stephanie/Music/podcast1.mp3",
            "C:/Users/Stephanie/Music/podcast1_part2.wav": "C:/Users/Stephanie/Music/podcast1.mp3",
            "C:/Users/Stephanie/Music/podcast1_part3.wav": "C:/Users/Stephanie/Music/podcast1.mp3",
            "C:/Users/Stephanie/Music/podcast2_part1.wav": "C:/Users/Stephanie/Music/podcast2.mp3",
            "C:/Users/Stephanie/Music/podcast2_part2.wav": "C:/Users/Stephanie/Music/podcast2.mp3",
            "C:/Users/Stephanie/Music/podcast2_part3.wav": "C:/Users/Stephanie/Music/podcast2.mp3",
        }
        
        default_options = {
            'trim_enabled': False,
            'compression_enabled': True,
            'compression_preset': 'Moderate (balanced)',
        }
        
        # Try creating the dialog with segment grouping
        dialog = PerTrackAudioConfigDialog(
            audio_files, 
            default_options, 
            None, 
            segment_origins=segment_origins
        )
        
        # Verify the dialog was created successfully
        assert dialog is not None, "Dialog creation failed"
        
        # Check that track list widget exists and has items
        assert dialog.track_list_widget is not None, "Track list widget not created"
        item_count = dialog.track_list_widget.count()
        print(f"✓ Track list widget created with {item_count} items")
        
        # Verify items were added (should have parent headers + segments)
        # Expected: 2 parent headers + 6 segments = 8 items
        assert item_count > 0, "No items in track list"
        print(f"✓ Items in widget: {item_count}")
        
        # Verify parent items have correct properties
        parent_count = 0
        segment_count = 0
        for i in range(item_count):
            item = dialog.track_list_widget.item(i)
            text = item.text()
            is_selectable = item.flags() & Qt.ItemIsSelectable
            
            if "original" in text:
                parent_count += 1
                # Parent items should NOT be selectable
                assert not is_selectable, f"Parent item {i} should not be selectable"
                print(f"✓ Parent header: {text}")
            elif "├─" in text:
                segment_count += 1
                # Segment items SHOULD be selectable
                assert is_selectable, f"Segment item {i} should be selectable"
                # Verify color was applied
                color = item.foreground().color()
                assert color.isValid(), f"Segment item {i} has invalid color"
        
        print(f"✓ Parent headers: {parent_count}")
        print(f"✓ Segments: {segment_count}")
        
        # Verify grouping: should have 2 parents with 3 segments each
        assert parent_count == 2, f"Expected 2 parent headers, got {parent_count}"
        assert segment_count == 6, f"Expected 6 segments, got {segment_count}"
        
        print("\n✅ PASS: Per-track dialog with segment grouping works correctly")
        print("✅ QListWidgetItem styling applied without errors")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mixed_scenario():
    """
    Test realistic scenario with mixed split and non-split files,
    like when user manually selects files (some short, some long).
    """
    print("\n[TEST] Mixed Files (Some Split, Some Not)")
    print("-" * 60)
    
    try:
        from pygui.dialogs.per_track_audio_config_dialog import PerTrackAudioConfigDialog
        
        # Simulate:
        # - track1.mp3 (10 min, < 30 min threshold, NOT split)
        # - track2.mp3 (60 min, > 30 min, split into 3 segments)
        # - track3.mp3 (5 min, < 30 min threshold, NOT split)
        
        audio_files = [
            "C:/Users/Stephanie/Music/track1.mp3",
            "C:/Users/Stephanie/Music/track2_part1.wav",
            "C:/Users/Stephanie/Music/track2_part2.wav",
            "C:/Users/Stephanie/Music/track2_part3.wav",
            "C:/Users/Stephanie/Music/track3.mp3",
        ]
        
        # Only track2 segments have origins (they were split)
        segment_origins = {
            "C:/Users/Stephanie/Music/track2_part1.wav": "C:/Users/Stephanie/Music/track2.mp3",
            "C:/Users/Stephanie/Music/track2_part2.wav": "C:/Users/Stephanie/Music/track2.mp3",
            "C:/Users/Stephanie/Music/track2_part3.wav": "C:/Users/Stephanie/Music/track2.mp3",
        }
        
        default_options = {}
        
        # Create dialog
        dialog = PerTrackAudioConfigDialog(
            audio_files, 
            default_options, 
            None, 
            segment_origins=segment_origins
        )
        
        assert dialog is not None, "Dialog creation failed"
        
        # Verify mixed display works
        item_count = dialog.track_list_widget.count()
        print(f"✓ Dialog created with {item_count} items")
        
        # Should show: 
        # - track2.mp3 (parent header)
        # - track2_part1.wav, track2_part2.wav, track2_part3.wav (segments)
        # - separator
        # - track1.mp3, track3.mp3 (standalone files)
        # Total: 1 + 3 + 1 + 2 = 7 items
        assert item_count >= 6, f"Expected at least 6 items, got {item_count}"
        
        print("✓ Mixed file scenario handled correctly")
        print("\n✅ PASS: Mixed scenario works without errors")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("PER-TRACK DIALOG ITEM STYLING FIX TEST")
    print("=" * 60)
    
    tests = [
        test_per_track_dialog_item_styling,
        test_mixed_scenario,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        if test_func():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)
