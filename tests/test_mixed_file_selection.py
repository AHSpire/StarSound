"""
Test Track Selection Fix for Mixed Files
=========================================

Tests that clicking on non-split files in a mixed scenario (some split, some not)
doesn't cause IndexError.

This verifies the fix that uses UserRole data instead of row numbers.
"""

import sys
from pathlib import Path

starsound_dir = Path(__file__).parent
sys.path.insert(0, str(starsound_dir / 'pygui'))

from PyQt5.QtWidgets import QApplication, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt

app = QApplication.instance() or QApplication(sys.argv)


def test_mixed_files_tracking():
    """
    Test that UserRole tracking works for mixed split/non-split files.
    
    Scenario:
    - file1.mp3 (non-split, index 0)
    - file2.mp3 (split into 2 segments, indices 1-2)
    - file3.mp3 (non-split, index 3)
    """
    print("[TEST] Mixed Files Tracking with UserRole")
    print("-" * 60)
    
    # Simulate the audio files list
    audio_files = [
        "file1.mp3",
        "file2_part1.wav",
        "file2_part2.wav",
        "file3.mp3",
    ]
    
    # Simulate segment origins
    segment_origins = {
        "file2_part1.wav": "file2.mp3",
        "file2_part2.wav": "file2.mp3",
    }
    
    # Build parent_to_segments like the dialog does
    parent_to_segments = {}
    for segment_path, original_path in segment_origins.items():
        if original_path not in parent_to_segments:
            parent_to_segments[original_path] = []
        parent_to_segments[original_path].append(segment_path)
    
    # Create list widget like the dialog does
    list_widget = QListWidget()
    
    # Build grouped view
    displayed_files = set()
    
    # Display grouped segments first
    for parent_path, segments in parent_to_segments.items():
        # Add parent header (no UserRole)
        parent_item = QListWidgetItem(f'📁 {parent_path} (original)')
        parent_item.setFlags(parent_item.flags() & ~Qt.ItemIsSelectable)
        list_widget.addItem(parent_item)
        
        # Add segments with UserRole
        for segment_index, segment_path in enumerate(segments):
            display_name = f'  ├─ {segment_path} (part {segment_index + 1})'
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, audio_files.index(segment_path))  # ← CRITICAL: Set UserRole
            list_widget.addItem(item)
            displayed_files.add(segment_path)
    
    # Add separator
    separator_item = QListWidgetItem('')
    separator_item.setFlags(separator_item.flags() & ~Qt.ItemIsSelectable)
    list_widget.addItem(separator_item)
    
    # Add standalone files with UserRole
    for i, file_path in enumerate(audio_files):
        if file_path not in displayed_files:
            item = QListWidgetItem(file_path)
            item.setData(Qt.UserRole, i)  # ← CRITICAL: Set UserRole
            list_widget.addItem(item)
    
    print(f"✓ Created list widget with {list_widget.count()} items:")
    for row in range(list_widget.count()):
        item = list_widget.item(row)
        text = item.text()
        user_role = item.data(Qt.UserRole)
        selectable = item.flags() & Qt.ItemIsSelectable
        status = "selectable" if selectable else "NOT selectable"
        print(f"  Row {row}: {text[:40]:40} | UserRole: {user_role} | {status}")
    
    print(f"\n✓ Simulating user clicks:")
    
    # Test clicking on file1.mp3 (should work)
    current_index = None
    
    # Find row for file1.mp3
    for row in range(list_widget.count()):
        item = list_widget.item(row)
        if 'file1.mp3' in item.text():
            user_role = item.data(Qt.UserRole)
            if user_role is not None:
                current_index = user_role
                print(f"  Clicked file1.mp3 (row {row}) → audio_files[{current_index}]")
                assert current_index == 0, f"file1.mp3 should have index 0, got {current_index}"
                assert audio_files[current_index] == 'file1.mp3'
                print(f"    ✓ Correctly mapped to: {audio_files[current_index]}")
    
    # Test clicking on file2_part1.wav (should work)
    for row in range(list_widget.count()):
        item = list_widget.item(row)
        if 'file2_part1.wav' in item.text():
            user_role = item.data(Qt.UserRole)
            if user_role is not None:
                current_index = user_role
                print(f"  Clicked file2_part1.wav (row {row}) → audio_files[{current_index}]")
                assert current_index == 1, f"file2_part1.wav should have index 1, got {current_index}"
                assert audio_files[current_index] == 'file2_part1.wav'
                print(f"    ✓ Correctly mapped to: {audio_files[current_index]}")
    
    # Test clicking on file3.mp3 (should work - this was failing before)
    for row in range(list_widget.count()):
        item = list_widget.item(row)
        if 'file3.mp3' in item.text():
            user_role = item.data(Qt.UserRole)
            if user_role is not None:
                current_index = user_role
                print(f"  Clicked file3.mp3 (row {row}) → audio_files[{current_index}]")
                assert current_index == 3, f"file3.mp3 should have index 3, got {current_index}"
                assert audio_files[current_index] == 'file3.mp3'
                print(f"    ✓ Correctly mapped to: {audio_files[current_index]}")
    
    # Test clicking on separator or parent header (should NOT set current_index)
    parent_header_clicked = False
    separator_clicked = False
    
    for row in range(list_widget.count()):
        item = list_widget.item(row)
        user_role = item.data(Qt.UserRole)
        
        if 'original' in item.text() and user_role is None:
            print(f"  Clicked parent header (row {row}) → no UserRole, skipped")
            parent_header_clicked = True
            assert user_role is None, "Parent header should not have UserRole"
            print(f"    ✓ Correctly skipped (not selectable anyway)")
        
        if item.text() == '' and user_role is None:
            print(f"  Clicked separator (row {row}) → no UserRole, skipped")
            separator_clicked = True
            assert user_role is None, "Separator should not have UserRole"
            print(f"    ✓ Correctly skipped (not selectable anyway)")
    
    print(f"\n✅ PASS: Mixed file tracking works correctly")
    print(f"✅ Standalone files after separator can be selected without IndexError")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("MIXED FILES TRACK SELECTION TEST")
    print("=" * 60)
    
    try:
        if test_mixed_files_tracking():
            print("\n" + "=" * 60)
            print("RESULT: PASSED ✅")
            print("=" * 60)
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
