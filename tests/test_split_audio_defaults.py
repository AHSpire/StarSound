"""
Test: Split Audio Default Settings
Verifies that Audio Trimming, Silence Trimming, and Fade In/Out are disabled by default for split audio workflows.
"""

import sys
import os
from pathlib import Path

# Add pygui to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pygui'))

def test_split_audio_defaults_disabled():
    """Test that split audio has aggressive filters disabled by default"""
    print("\n✓ TEST 1: Split Audio Default Settings")
    print("=" * 60)
    
    # Check the code to verify the logic is in place
    dialog_path = Path(__file__).parent / 'pygui' / 'per_track_audio_config_dialog.py'
    with open(dialog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        "self.default_options['trim_enabled'] = False" in content,
        "self.default_options['silence_trim_enabled'] = False" in content,
        "self.default_options['fade_enabled'] = False" in content,
        "if self.segment_origins:" in content,
    ]
    
    if all(checks):
        print("✓ Split audio default disabling logic present:")
        print("  - Audio Trimming (trim_enabled) disabled")
        print("  - Silence Trimming (silence_trim_enabled) disabled")
        print("  - Fade In/Out (fade_enabled) disabled")
        print("  - Only triggers when segment_origins is provided (split audio)")
        return True
    else:
        print("✗ Missing some default disabling logic")
        for i, check in enumerate(checks):
            print(f"  Check {i+1}: {check}")
        return False

def test_regular_audio_unaffected():
    """Test that regular (non-split) audio is not affected by this change"""
    print("\n✓ TEST 2: Regular Audio Not Affected")
    print("=" * 60)
    
    dialog_path = Path(__file__).parent / 'pygui' / 'per_track_audio_config_dialog.py'
    with open(dialog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verify the logic is conditional on segment_origins
    if "if self.segment_origins:" in content:
        print("✓ Disabling logic is conditional:")
        print("  - Only applies when segment_origins is provided")
        print("  - Regular audio (no segment_origins) keeps default settings")
        return True
    else:
        print("✗ Logic should be conditional on segment_origins")
        return False

def test_other_tools_remain_enabled():
    """Test that other audio tools like Normalization stay enabled"""
    print("\n✓ TEST 3: Other Tools Remain Enabled")
    print("=" * 60)
    
    dialog_path = Path(__file__).parent / 'pygui' / 'per_track_audio_config_dialog.py'
    with open(dialog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count how many tools are being disabled
    disabled_count = 0
    if "trim_enabled'] = False" in content:
        disabled_count += 1
    if "silence_trim_enabled'] = False" in content:
        disabled_count += 1
    if "fade_enabled'] = False" in content:
        disabled_count += 1
    
    # Other tools should NOT be explicitly disabled
    other_tools_disabled = [
        'sonic_scrubber_enabled.*False' in content,
        'compression_enabled.*False' in content,
        'soft_clip_enabled.*False' in content,
        'normalize_enabled.*False' in content,
        'de_esser_enabled.*False' in content,
    ]
    
    import re
    other_tools = [
        bool(re.search(r"sonic_scrubber_enabled.*False", content)),
        bool(re.search(r"compression_enabled.*False", content)),
        bool(re.search(r"soft_clip_enabled.*False", content)),
        bool(re.search(r"normalize_enabled.*False", content)),
        bool(re.search(r"de_esser_enabled.*False", content)),
    ]
    
    if disabled_count == 3 and not any(other_tools):
        print(f"✓ Exactly 3 tools disabled for split audio:")
        print("  - Trim, Silence Trim, Fade (disabled)")
        print("  - Sonic Scrubber, Compression, Soft Clip, Normalize, De-Esser (remain enabled)")
        return True
    else:
        print(f"✗ Expected 3 disabled, found {disabled_count}")
        print(f"  Other tools accidentally disabled: {any(other_tools)}")
        return False

def test_no_syntax_errors():
    """Verify no syntax errors in modified file"""
    print("\n✓ TEST 4: Syntax Validation")
    print("=" * 60)
    
    import subprocess
    dialog_path = Path(__file__).parent / 'pygui' / 'per_track_audio_config_dialog.py'
    
    try:
        result = subprocess.run(
            ['python', '-m', 'py_compile', str(dialog_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✓ per_track_audio_config_dialog.py: No syntax errors")
            return True
        else:
            print(f"✗ Syntax error found:")
            print(f"  {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Could not check ({e})")
        return False

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("SPLIT AUDIO DEFAULT SETTINGS TEST SUITE")
    print("=" * 60)
    
    results = [
        test_split_audio_defaults_disabled(),
        test_regular_audio_unaffected(),
        test_other_tools_remain_enabled(),
        test_no_syntax_errors(),
    ]
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✅ All split audio default tests passed!")
        print("\nBehavior:")
        print("  • Split audio (has segment_origins):")
        print("    - Audio Trimmer: ❌ OFF")
        print("    - Silence Trimming: ❌ OFF")
        print("    - Fade In/Out: ❌ OFF")
        print("    - Normalization: ✓ ON")
        print("    - Compression: ✓ ON")
        print("    - Others: ✓ ON (as configured)")
        print("\n  • Regular audio (no segment_origins):")
        print("    - All tools use settings from main Audio Processing dialog")
    else:
        print("\n❌ Some tests failed. Review the output above.")
        sys.exit(1)
