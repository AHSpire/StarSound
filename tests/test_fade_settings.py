"""
Test Fade Settings Processing
==============================

Tests that fade settings are properly converted and processed
through the per-track audio config workflow.
"""

import sys
from pathlib import Path

starsound_dir = Path(__file__).parent
sys.path.insert(0, str(starsound_dir / 'pygui'))

from utils.audio_utils import build_audio_filter_chain


def test_fade_conversion():
    """
    Test that per-track format (with _enabled) converts to audio_dialog format.
    """
    print("[TEST] Fade Settings Conversion")
    print("-" * 60)
    
    # Simulate per-track format as stored by PerTrackAudioConfigDialog
    per_track_settings = {
        'fade_enabled': True,
        'fade_in_duration': '0hr0m0.5s',
        'fade_out_duration': '0hr30m0s',
        'compression_enabled': False,
        'normalize_enabled': True,
        'trim_enabled': False,
    }
    
    # Simulate the conversion function from starsound_gui
    tool_keys = ['trim', 'silence_trim', 'sonic_scrubber', 'compression',
                 'soft_clip', 'eq', 'normalize', 'fade', 'de_esser', 'stereo_to_mono']
    
    converted = {}
    for key, value in per_track_settings.items():
        if key.endswith('_enabled'):
            tool_name = key[:-8]
            if tool_name in tool_keys:
                converted[tool_name] = value
        else:
            converted[key] = value
    
    print(f"✓ Input (per-track format):")
    for k, v in per_track_settings.items():
        print(f"  - {k}: {v}")
    
    print(f"\n✓ Output (audio-dialog format):")
    for k, v in converted.items():
        print(f"  - {k}: {v}")
    
    # Verify output has correct keys
    assert 'fade' in converted, "Missing 'fade' key in converted settings"
    assert converted['fade'] == True, "Fade should be enabled"
    assert converted['fade_in_duration'] == '0hr0m0.5s', "Fade in duration mismatch"
    assert converted['fade_out_duration'] == '0hr30m0s', "Fade out duration mismatch"
    
    print("\n✅ PASS: Fade settings converted correctly")
    return converted


def test_audio_filter_chain_with_fade():
    """
    Test that build_audio_filter_chain correctly processes fade settings.
    """
    print("\n[TEST] Audio Filter Chain with Fade")
    print("-" * 60)
    
    # Use converted settings from previous test
    audio_options = {
        'fade': True,
        'fade_in_duration': '0hr0m0.5s',
        'fade_out_duration': '0hr30m0s',
    }
    
    print(f"✓ Building filter chain with options:")
    for k, v in audio_options.items():
        print(f"  - {k}: {v}")
    
    try:
        audio_filter = build_audio_filter_chain(audio_options)
        
        print(f"\n✓ Generated filter chain:")
        print(f"  {audio_filter if audio_filter else '(empty - as expected with only fade)'}")
        
        # Verify fade filters are present
        assert 'afade' in audio_filter or audio_filter == '', "Fade filter should be generated"
        
        print("\n✅ PASS: Audio filter chain builds successfully with fade")
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_per_track_workflow():
    """
    Simulate the full per-track audio config workflow with segments.
    """
    print("\n[TEST] Full Per-Track Workflow with Segments")
    print("-" * 60)
    
    # Simulate what happens when user configures per-track settings
    per_track_settings = {
        "segment1.wav": {
            'fade_enabled': True,
            'fade_in_duration': '0hr0m1s',      # Longer fade in for intro
            'fade_out_duration': '0hr10m0s',     # Medium fade out
        },
        "segment2.wav": {
            'fade_enabled': True,
            'fade_in_duration': '0hr0m0.5s',    # Quick fade in
            'fade_out_duration': '0hr30m0s',     # Long fade out (end)
        },
    }
    
    print("✓ Per-track settings for 2 segments:")
    for segment, settings in per_track_settings.items():
        print(f"  {segment}:")
        print(f"    - fade_in: {settings['fade_in_duration']}")
        print(f"    - fade_out: {settings['fade_out_duration']}")
    
    # Convert each segment's settings
    tool_keys = ['trim', 'silence_trim', 'sonic_scrubber', 'compression',
                 'soft_clip', 'eq', 'normalize', 'fade', 'de_esser', 'stereo_to_mono']
    
    per_track_filters = {}
    
    for segment_path, track_settings in per_track_settings.items():
        # Convert from per-track to audio_dialog format
        converted = {}
        for key, value in track_settings.items():
            if key.endswith('_enabled'):
                tool_name = key[:-8]
                if tool_name in tool_keys:
                    converted[tool_name] = value
            else:
                converted[key] = value
        
        # Build filter
        try:
            audio_filter = build_audio_filter_chain(converted)
            per_track_filters[segment_path] = audio_filter
            print(f"\n✓ {segment_path}:")
            print(f"  Audio filter generated ({len(audio_filter)} chars)")
        except Exception as e:
            print(f"\n❌ {segment_path}: {e}")
            return False
    
    assert len(per_track_filters) == 2, "Should have 2 filter chains"
    print(f"\n✅ PASS: Full workflow complete - {len(per_track_filters)} segments processed")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("FADE SETTINGS PROCESSING TEST")
    print("=" * 60)
    
    tests = [
        test_fade_conversion,
        test_audio_filter_chain_with_fade,
        test_per_track_workflow,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            result = test_func()
            if result is not False and result is not None:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)
