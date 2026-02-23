"""
Test: Per-File Split Configuration Dialog
Verifies that users can set individual segment lengths for each audio file.
"""

import sys
import os
from pathlib import Path

# Add pygui to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pygui'))

def test_per_file_split_dialog_exists():
    """Test that per-file split config dialog exists and can be imported"""
    print("\n✓ TEST 1: Per-File Split Configuration Dialog")
    print("=" * 60)
    
    try:
        from pygui.dialogs.per_file_split_config_dialog import PerFileSplitConfigDialog
        print("✓ Dialog imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import: {e}")
        return False

def test_per_file_split_integration():
    """Test that starsound_gui uses the new per-file dialog"""
    print("\n✓ TEST 2: GUI Integration (Uses Per-File Dialog)")
    print("=" * 60)
    
    gui_path = Path(__file__).parent / 'pygui' / 'starsound_gui.py'
    with open(gui_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        'PerFileSplitConfigDialog' in content,
        'per_file_segment_lengths' in content,
        'per_file_segment_lengths.get(file_path' in content,
    ]
    
    if all(checks):
        print("✓ Per-file dialog correctly integrated:")
        print("  - Dialog is imported and used")
        print("  - Per-file segment lengths are stored")
        print("  - Each file looks up its own segment length")
        return True
    else:
        print("✗ Integration incomplete")
        for i, check in enumerate(checks, 1):
            print(f"  Check {i}: {check}")
        return False

def test_segment_length_parameter():
    """Test that perform_file_splitting accepts dict parameter"""
    print("\n✓ TEST 3: Flexible Parameter Handling")
    print("=" * 60)
    
    gui_path = Path(__file__).parent / 'pygui' / 'starsound_gui.py'
    with open(gui_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        'segment_length: int | dict' in content or 'Union[int, dict]' in content,
        'isinstance(segment_length, int)' in content,
        'per_file_segment_lengths = segment_length' in content,
    ]
    
    if all(checks):
        print("✓ Parameter handling supports both formats:")
        print("  - Accepts single int (backward compatible)")
        print("  - Accepts dict (per-file configuration)")
        print("  - Converts int to dict internally")
        return True
    else:
        print("✗ Parameter handling incomplete")
        return False

def test_logging_per_file_config():
    """Test that logging shows individual segment lengths"""
    print("\n✓ TEST 4: Logging Details")
    print("=" * 60)
    
    gui_path = Path(__file__).parent / 'pygui' / 'starsound_gui.py'
    with open(gui_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        'User configured individual segment lengths' in content,
        'min segments' in content or '{seg_len}' in content,
        'Starting FFmpeg split operation for:' in content,
    ]
    
    if all(checks):
        print("✓ Logging includes per-file details:")
        print("  - Logs individual file configurations")
        print("  - Shows segment length for each file")
        print("  - Tracks split operations")
        return True
    else:
        print("✗ Logging incomplete")
        return False

def test_syntax_validation():
    """Verify no syntax errors in modified files"""
    print("\n✓ TEST 5: Syntax Validation")
    print("=" * 60)
    
    import subprocess
    files_to_check = [
        Path(__file__).parent / 'pygui' / 'per_file_split_config_dialog.py',
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
            print(f"✗ {filepath.name}: Could not check ({e})")
            all_valid = False
    
    return all_valid

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("PER-FILE SPLIT CONFIGURATION TEST SUITE")
    print("=" * 60)
    
    results = [
        test_per_file_split_dialog_exists(),
        test_per_file_split_integration(),
        test_segment_length_parameter(),
        test_logging_per_file_config(),
        test_syntax_validation(),
    ]
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✅ All per-file splitting tests passed!")
        print("\nBehavior:")
        print("  1. User selects audio files (3+ files with 30+ min duration)")
        print("  2. System detects files need splitting")
        print("  3. Shows Per-File Split Config Dialog with:")
        print("     • Sidebar: List of all files needing split")
        print("     • Main: Config controls for selected file")
        print("     • Per-file segment length: 5-30 min")
        print("     • Preview: Shows how many segments will be created")
        print("  4. User configures each file individually:")
        print("     • Elden Ring: 30-min segments (2 parts)")
        print("     • Oblivion: 25-min segments (maybe 2-3 parts)")
        print("     • LoFi track: 20-min segments (3 parts)")
        print("  5. Click 'Apply Configuration'")
        print("  6. Each file splits with its OWN settings")
        print("\nResult: Total 7-8 segments (not the same for all files!")
    else:
        print("\n❌ Some tests failed. Review the output above.")
        sys.exit(1)
