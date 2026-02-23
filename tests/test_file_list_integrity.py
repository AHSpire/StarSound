"""
Test: File List Integrity During Splitting and Conversion
Verifies that the selected_audio_files list doesn't get corrupted with duplicates.
"""

import sys
import os
from pathlib import Path

# Add test path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pygui'))

def test_file_list_after_split():
    """
    Simulate the splitting process to verify file list integrity.
    """
    print("\n" + "=" * 70)
    print("TEST: File List Integrity During Split + Conversion")
    print("=" * 70 + "\n")
    
    # Simulate initial state (4 files to split)
    selected_audio_files = [
        'C:\\test\\comfy_osrs.mp3',
        'C:\\test\\lofi_inn.mp3',
        'C:\\test\\oblivion.mp3',
        'C:\\test\\elden_ring.mp3'
    ]
    
    print("1️⃣ INITIAL STATE:")
    print(f"   Selected files: {len(selected_audio_files)}")
    for i, f in enumerate(selected_audio_files, 1):
        print(f"   [{i}] {os.path.basename(f)}")
    
    # Get reference to the list (like convert_audio does with getattr)
    files = selected_audio_files
    print(f"\n2️⃣ REFERENCE TEST:")
    print(f"   files is selected_audio_files: {files is selected_audio_files}")
    
    # Simulate perform_file_splitting() modifying the list
    files_to_remove = selected_audio_files.copy()  # All 4 original files
    files_to_add = []
    
    # Create split segments
    for orig_file in files_to_remove:
        base = os.path.splitext(os.path.basename(orig_file))[0]
        for part in range(1, 4):
            files_to_add.append(f"{os.path.dirname(orig_file)}\\{base}_part{part}.wav")
    
    print(f"\n3️⃣ SPLITTING SIMULATION:")
    print(f"   Files to remove: {len(files_to_remove)}")
    print(f"   Files to add: {len(files_to_add)}")
    
    # Apply the split logic (from perform_file_splitting)
    for original in files_to_remove:
        if original in selected_audio_files:
            selected_audio_files.remove(original)
    
    selected_audio_files.extend(files_to_add)
    
    print(f"\n4️⃣ AFTER SPLIT:")
    print(f"   selected_audio_files now has: {len(selected_audio_files)} files")
    print(f"   files also has: {len(files)} files (reference test)")
    print(f"   Match: {len(files) == len(selected_audio_files)}")
    
    # Show list
    print(f"\n   Files in list:")
    for i, f in enumerate(files, 1):
        print(f"   [{i}] {os.path.basename(f)}")
    
    # Check for duplicates
    file_names = [os.path.basename(f) for f in files]
    duplicates = [name for name in file_names if file_names.count(name) > 1]
    
    if duplicates:
        print(f"\n❌ DUPLICATES FOUND: {duplicates}")
        return False
    else:
        print(f"\n✅ NO DUPLICATES - List is clean")
    
    # Verify we have exactly 12 files (4 originals × 3 parts)
    expected_count = 12
    if len(files) == expected_count:
        print(f"✅ CORRECT COUNT: {len(files)} == {expected_count}")
        return True
    else:
        print(f"❌ WRONG COUNT: {len(files)} != {expected_count}")
        return False

if __name__ == '__main__':
    result = test_file_list_after_split()
    print("\n" + "=" * 70)
    if result:
        print("✅ File list integrity test PASSED")
    else:
        print("❌ File list integrity test FAILED")
    print("=" * 70 + "\n")
    
    sys.exit(0 if result else 1)
