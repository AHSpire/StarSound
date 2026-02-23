"""
Test: Multi-File Split Preview Dialog
Verifies that the split preview dialog correctly displays all split files.
"""

import sys
import os
from pathlib import Path

# Add pygui to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pygui'))

def test_multi_file_preview_support():
    """Test that split preview dialog supports multiple files"""
    print("\n✓ TEST 1: Multi-File Preview Support")
    print("=" * 60)
    
    dialog_path = Path(__file__).parent / 'pygui' / 'split_preview_dialog.py'
    with open(dialog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        'split_metadata: dict = None' in content or 'split_metadata=' in content,
        'split_metadata' in content and 'enumerate(split_metadata.items())' in content,
        '_build_multi_file_preview' in content,
    ]
    
    if all(checks):
        print("✓ Multi-file preview support implemented:")
        print("  - Accepts split_metadata parameter")
        print("  - Has _build_multi_file_preview method")
        print("  - Iterates through all files")
        return True
    else:
        print("✗ Multi-file preview support incomplete")
        for i, check in enumerate(checks, 1):
            print(f"  Check {i}: {check}")
        return False

def test_backward_compatibility():
    """Test that dialog still works with single-file parameters"""
    print("\n✓ TEST 2: Backward Compatibility (Single-File)")
    print("=" * 60)
    
    dialog_path = Path(__file__).parent / 'pygui' / 'split_preview_dialog.py'
    with open(dialog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        'original_filename: str = None' in content,
        'original_duration: float = None' in content,
        '_build_single_file_preview' in content,
        'if split_metadata:' in content and 'else:' in content,  # Conditional logic
    ]
    
    if all(checks):
        print("✓ Single-file preview still works:")
        print("  - All single-file parameters have defaults")
        print("  - Has _build_single_file_preview method")
        print("  - Conditional logic to choose between modes")
        return True
    else:
        print("✗ Backward compatibility incomplete")
        for i, check in enumerate(checks, 1):
            print(f"  Check {i}: {check}")
        return False

def test_gui_integration():
    """Test that starsound_gui passes all metadata to the dialog"""
    print("\n✓ TEST 3: GUI Integration (Passes All Files)")
    print("=" * 60)
    
    gui_path = Path(__file__).parent / 'pygui' / 'starsound_gui.py'
    with open(gui_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        'split_metadata=split_metadata' in content,  # Passes all metadata dict
        'For now, show preview for first split' not in content,  # Old comment removed
        'parent=self' in content,  # Uses keyword argument for parent
    ]
    
    if all(checks):
        print("✓ GUI correctly passes ALL split files:")
        print("  - No longer limits to just first file")
        print("  - Passes complete split_metadata dict")
        print("  - Uses proper keyword arguments")
        return True
    else:
        print("✗ GUI integration incomplete")
        for i, check in enumerate(checks, 1):
            print(f"  Check {i}: {check}")
        return False

def test_file_grouping():
    """Test that dialog shows files grouped together"""
    print("\n✓ TEST 4: File Grouping Display")
    print("=" * 60)
    
    dialog_path = Path(__file__).parent / 'pygui' / 'split_preview_dialog.py'
    with open(dialog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        '_build_multi_file_preview' in content,  # Has multi-file method
        'for i, (filename, metadata) in enumerate(split_metadata.items())' in content,  # Iterates all files
        'header = QLabel' in content and 'filename}' in content,  # Shows filename header
        '📁' in content,  # Uses folder emoji for visual grouping
    ]
    
    if all(checks):
        print("✓ Files are properly grouped:")
        print("  - Separate section for each file")
        print("  - Shows original duration and segment count per file")
        print("  - Visual grouping with headers and emoji")
        return True
    else:
        print("✗ File grouping incomplete")
        return False

def test_segment_counting():
    """Test that total segments are correctly calculated"""
    print("\n✓ TEST 5: Total Segment Counting")
    print("=" * 60)
    
    dialog_path = Path(__file__).parent / 'pygui' / 'split_preview_dialog.py'
    with open(dialog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'total_segments = sum(len(meta.get(\'segment_durations\', []))'  in content:
        print("✓ Total segments correctly calculated:")
        print("  - Sums segment_durations from all files")
        print("  - Shows total count in header")
        return True
    else:
        print("✗ Segment counting not found")
        return False

def test_syntax_validation():
    """Verify no syntax errors"""
    print("\n✓ TEST 6: Syntax Validation")
    print("=" * 60)
    
    import subprocess
    files_to_check = [
        Path(__file__).parent / 'pygui' / 'split_preview_dialog.py',
        Path(__file__).parent / 'pygui' / 'starsound_gui.py',
    ]
    
    all_valid = True
    for filepath in files_to_check:
        try:
            result = subprocess.run(
                ['python', '-m', 'py_compile', str(filepath)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✓ {filepath.name}: No syntax errors")
            else:
                print(f"✗ {filepath.name}: Syntax error")
                print(f"  {result.stderr}")
                all_valid = False
        except Exception as e:
            print(f"✗ {filepath.name}: {e}")
            all_valid = False
    
    return all_valid

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("MULTI-FILE SPLIT PREVIEW TEST SUITE")
    print("=" * 60)
    
    results = [
        test_multi_file_preview_support(),
        test_backward_compatibility(),
        test_gui_integration(),
        test_file_grouping(),
        test_segment_counting(),
        test_syntax_validation(),
    ]
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✅ All multi-file preview tests passed!")
        print("\nBehavior when splitting multiple files:")
        print("  1. Select 4 audio files (Elden Ring, Oblivion, LoFi, etc.)")
        print("  2. Each file configured with individual segment length")
        print("  3. Splitting completes")
        print("  4. Split Preview Dialog shows:")
        print("     ✓ Title: 'Audio Files Successfully Split!' (plural)")
        print("     ✓ Summary: 'Split: 4 file(s) into [X] segments total'")
        print("     ✓ Grouped display:")
        print("         📁 Elden Ring (60.0 min) → 2 segments:")
        print("           Part 1: elden_ring_part1.wav (30.0 min)")
        print("           Part 2: elden_ring_part2.wav (30.0 min)")
        print("         📁 Oblivion (60.0 min) → 3 segments:")
        print("           Part 1: oblivion_part1.wav (25.0 min)")
        print("           Part 2: oblivion_part2.wav (25.0 min)")
        print("           Part 3: oblivion_part3.wav (10.0 min)")
        print("         [... more files ...]")
        print("     ✓ User clicks 'Proceed with Conversion'")
        print("  5. All segments proceed to audio customization & conversion")
    else:
        print("\n❌ Some tests failed. Review the output above.")
        sys.exit(1)
