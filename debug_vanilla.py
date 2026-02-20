import sys
sys.path.insert(0, 'c:/Projects/StarSound/pygui')

from pathlib import Path
from utils.patch_generator import get_vanilla_tracks_for_biome

print("Debug: Checking vanilla track system")
print("=" * 60)

# Check 1: Does vanilla_tracks folder exist?
vanilla_dir = Path('c:/Projects/StarSound/pygui/vanilla_tracks')
print(f"1. vanilla_tracks folder exists: {vanilla_dir.exists()}")

# Check 2: Can we find day folders?
day_folders = list(vanilla_dir.rglob('day'))
print(f"2. Found {len(day_folders)} 'day' folders with rglob")

# Check 3: Do any day folders have files?
has_vanilla = False
if day_folders:
    for day_folder in day_folders[:1]:
        files = list(day_folder.glob('*.ogg'))
        print(f"3. First day folder: {day_folder.relative_to(vanilla_dir)}")
        print(f"   Contains {len(files)} .ogg files")
        if len(files) > 0:
            has_vanilla = True

print(f"4. has_vanilla result: {has_vanilla}")

# Check 4: Test get_vanilla_tracks_for_biome
print("\n5. Testing get_vanilla_tracks_for_biome('surface', 'forest'):")
result = get_vanilla_tracks_for_biome('surface', 'forest')
print(f"   Day tracks: {len(result['dayTracks'])}")
print(f"   Night tracks: {len(result['nightTracks'])}")

if result['dayTracks']:
    first_day = result['dayTracks'][0]
    print(f"\n6. First day track (raw): {repr(first_day)}")
    print(f"   Type: {type(first_day)}")
    
    # Test extraction
    track_name = first_day.split('\\')[-1] if '\\' in first_day else first_day.split('/')[-1]
    print(f"   Extracted name: {track_name}")

print("\n" + "=" * 60)
if has_vanilla and result['dayTracks']:
    print("✅ Everything should work!")
else:
    print("❌ Problem detected - vanilla tracks not being found or extracted")
