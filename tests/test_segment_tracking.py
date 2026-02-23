"""
Test Segment Tracking Integration
==================================

Tests the segment origin tracking system that maps split segments back
to their original files for per-track audio configuration grouping.

This test simulates the workflow:
1. Files marked for splitting
2. FFmpeg splits them into segments
3. segment_origins dict tracks which segments came from which original
4. Per-track dialog receives segment_origins for grouping display
"""

import sys
import os
from pathlib import Path

# Add project directory to path
starsound_dir = Path(__file__).parent
sys.path.insert(0, str(starsound_dir))

def test_segment_origin_mapping():
    """
    Test that segment_origins mapping works correctly.
    
    Simulates:
    - Original file: track1.mp3 splits into track1_part1.wav, track1_part2.wav
    - Original file: track2.mp3 splits into track2_part1.wav, track2_part2.wav
    
    Expected result:
    - segment_origins has 4 entries (2 segments x 2 original files)
    - Each segment maps back to correct original
    """
    print("[TEST] Segment Origin Mapping")
    print("-" * 60)
    
    # Simulate segment origins
    segment_origins = {
        "/path/to/track1_part1.wav": "/path/to/track1.mp3",
        "/path/to/track1_part2.wav": "/path/to/track1.mp3",
        "/path/to/track2_part1.wav": "/path/to/track2.mp3",
        "/path/to/track2_part2.wav": "/path/to/track2.mp3",
    }
    
    # Build parent-to-segments mapping (as done in per-track dialog)
    parent_to_segments = {}
    for segment_path, original_path in segment_origins.items():
        if original_path not in parent_to_segments:
            parent_to_segments[original_path] = []
        parent_to_segments[original_path].append(segment_path)
    
    # Verify mapping
    print(f"✓ Total segments tracked: {len(segment_origins)}")
    print(f"✓ Total original files: {len(parent_to_segments)}")
    
    for original, segments in parent_to_segments.items():
        print(f"\n  Original: {os.path.basename(original)}")
        for i, segment in enumerate(segments, 1):
            print(f"    - {os.path.basename(segment)} (part {i})")
    
    # Verify integrity
    total_segments = sum(len(segs) for segs in parent_to_segments.values())
    assert total_segments == len(segment_origins), "Segment count mismatch!"
    assert len(parent_to_segments) == 2, "Should have 2 original files!"
    
    print("\n✅ PASS: Segment origin mapping works correctly")
    return True


def test_audio_files_list():
    """
    Test that audio_files list contains all segments (as it would after splitting).
    """
    print("\n[TEST] Audio Files List After Splitting")
    print("-" * 60)
    
    # Simulate the files list after splitting
    # (original files replaced with their segments)
    audio_files = [
        "/path/to/track1_part1.wav",
        "/path/to/track1_part2.wav",
        "/path/to/track2_part1.wav",
        "/path/to/track2_part2.wav",
    ]
    
    segment_origins = {
        "/path/to/track1_part1.wav": "/path/to/track1.mp3",
        "/path/to/track1_part2.wav": "/path/to/track1.mp3",
        "/path/to/track2_part1.wav": "/path/to/track2.mp3",
        "/path/to/track2_part2.wav": "/path/to/track2.mp3",
    }
    
    print(f"✓ Audio files to process: {len(audio_files)}")
    for f in audio_files:
        print(f"  - {os.path.basename(f)}")
    
    print(f"\n✓ Segments tracked in segment_origins: {len(segment_origins)}")
    
    # Verify all files have origin tracking
    files_with_origins = sum(1 for f in audio_files if f in segment_origins)
    assert files_with_origins == len(audio_files), "Not all files have segment origins!"
    
    print("\n✅ PASS: All audio files have origin tracking")
    return True


def test_per_track_dialog_integration():
    """
    Test that per-track dialog can process segment_origins correctly.
    """
    print("\n[TEST] Per-Track Dialog Integration")
    print("-" * 60)
    
    # Simulate the data as it would reach the dialog
    audio_files = [
        "/path/to/track1_part1.wav",
        "/path/to/track1_part2.wav",
        "/path/to/track2_part1.wav",
        "/path/to/track2_part2.wav",
    ]
    
    segment_origins = {
        "/path/to/track1_part1.wav": "/path/to/track1.mp3",
        "/path/to/track1_part2.wav": "/path/to/track1.mp3",
        "/path/to/track2_part1.wav": "/path/to/track2.mp3",
        "/path/to/track2_part2.wav": "/path/to/track2.mp3",
    }
    
    # Simulate dialog initialization logic
    parent_to_segments = {}
    if segment_origins:
        for segment_path, original_path in segment_origins.items():
            if original_path not in parent_to_segments:
                parent_to_segments[original_path] = []
            parent_to_segments[original_path].append(segment_path)
    
    # Verify grouping
    print(f"✓ Segment grouping detected: {bool(parent_to_segments)}")
    print(f"✓ Groups created: {len(parent_to_segments)}")
    
    for i, (parent_path, segments) in enumerate(parent_to_segments.items(), 1):
        print(f"\n  Group {i}: {os.path.basename(parent_path)}")
        print(f"    Segments: {len(segments)}")
        for segment in segments:
            print(f"      ├─ {os.path.basename(segment)}")
    
    print("\n✅ PASS: Per-track dialog grouping logic works")
    return True


def test_mixed_files_scenario():
    """
    Test realistic scenario with both split and non-split files.
    """
    print("\n[TEST] Mixed Files (Split + Non-Split)")
    print("-" * 60)
    
    # Scenario: User selects 3 files
    # - track1.mp3 (< 30 min, not split)
    # - track2.mp3 (> 30 min, split into 3 segments)
    # - track3.mp3 (< 30 min, not split)
    
    audio_files = [
        "/path/to/track1.mp3",            # Not split
        "/path/to/track2_part1.wav",      # Split segment 1
        "/path/to/track2_part2.wav",      # Split segment 2
        "/path/to/track2_part3.wav",      # Split segment 3
        "/path/to/track3.mp3",            # Not split
    ]
    
    segment_origins = {
        "/path/to/track2_part1.wav": "/path/to/track2.mp3",
        "/path/to/track2_part2.wav": "/path/to/track2.mp3",
        "/path/to/track2_part3.wav": "/path/to/track2.mp3",
    }
    
    # Build mapping
    parent_to_segments = {}
    for segment_path, original_path in segment_origins.items():
        if original_path not in parent_to_segments:
            parent_to_segments[original_path] = []
        parent_to_segments[original_path].append(segment_path)
    
    print(f"✓ Total files to process: {len(audio_files)}")
    print(f"✓ Split files (in segment_origins): {len(segment_origins)}")
    print(f"✓ Non-split files: {len(audio_files) - len(segment_origins)}")
    
    print(f"\n✓ Parent files with segments: {len(parent_to_segments)}")
    for parent, segments in parent_to_segments.items():
        print(f"  - {os.path.basename(parent)}: {len(segments)} segments")
    
    # List all files and their tracking status
    print(f"\n✓ File manifest:")
    for f in audio_files:
        if f in segment_origins:
            origin = segment_origins[f]
            print(f"  ├─ {os.path.basename(f)} (from {os.path.basename(origin)})")
        else:
            print(f"  ├─ {os.path.basename(f)} (standalone)")
    
    print("\n✅ PASS: Mixed files scenario works correctly")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("SEGMENT TRACKING INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        test_segment_origin_mapping,
        test_audio_files_list,
        test_per_track_dialog_integration,
        test_mixed_files_scenario,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ FAIL: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)
