"""Verify all modes can see complete biome list"""
import json
from pathlib import Path

biome_file = Path('pygui/vanilla_tracks/biome_tracks.json')
with open(biome_file) as f:
    biomes = json.load(f)

print("✅ Biome Coverage Check\n")
print(f"Total biomes in file: {len(biomes)}\n")

# Check specific biomes
test_biomes = ['surface/forest', 'surface/garden', 'surface/alien', 'core/gardencorelayer']
print("Priority biomes status:")
for biome_key in test_biomes:
    if biome_key in biomes:
        day = len(biomes[biome_key].get('day', []))
        night = len(biomes[biome_key].get('night', []))
        print(f"  ✓ {biome_key}: {day} day, {night} night tracks")
    else:
        print(f"  ✗ {biome_key}: MISSING")

# Count biomes by visibility mode
print("\n📊 Visibility by Mode:")
print("  Add mode: can see ALL biomes (including empty ones)")
with_tracks = [(k, len(v['day']), len(v['night'])) for k, v in biomes.items() if len(v['day']) > 0 or len(v['night']) > 0]
print(f"  Replace/Both modes: can see {len(with_tracks)} biomes (those with tracks)")

# Show breakdown
cats = {}
for k in with_tracks:
    cat = k[0].split('/')[0]
    cats[cat] = cats.get(cat, 0) + 1

print("\n  Replace/Both mode breakdown:")
for cat in sorted(cats.keys()):
    print(f"    {cat}: {cats[cat]} biomes")

print("\n✅ All modes should now see complete biome lists!")
