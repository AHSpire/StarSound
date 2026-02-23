r"""
Regenerate biome_tracks.json from Starbound biome files.

This script reads all .biome files from the Starbound biomes directory
and extracts day/night music tracks to create a fresh biome_tracks.json.

Usage:
    python regenerate_biome_tracks.py <starbound_unpacked_path> <output_file>
    
Example:
    python regenerate_biome_tracks.py "c:\Users\Stephanie\OneDrive\Documents\Original Unpacked Starbound" "c:\Projects\StarSound\pygui\vanilla_tracks\biome_tracks.json"
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def collect_biomes_from_directory(biome_dir: Path, category: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Read all .biome files from a directory and extract music tracks.
    
    Args:
        biome_dir: Path to biome directory (e.g., biomes/surface/)
        category: Category name (e.g., "surface", "core", "underground")
    
    Returns:
        Dict with keys like "category/biome_name" mapping to day/night tracks
    """
    result = {}
    
    if not biome_dir.exists():
        print(f"⚠️  {category} directory not found: {biome_dir}")
        return result
    
    biome_files = sorted(biome_dir.glob("*.biome"))
    print(f"📁 Found {len(biome_files)} biomes in {category}/")
    
    def strip_json_comments(json_str: str) -> str:
        """Remove // comments from JSON while preserving string content"""
        lines = json_str.split('\n')
        result = []
        for line in lines:
            in_string = False
            escaped = False
            result_line = []
            for i, char in enumerate(line):
                if char == '\\' and in_string:
                    escaped = not escaped
                    result_line.append(char)
                elif char == '"' and not escaped:
                    in_string = not in_string
                    result_line.append(char)
                elif char == '/' and not in_string and i + 1 < len(line) and line[i + 1] == '/':
                    break
                else:
                    escaped = False
                    result_line.append(char)
            result.append(''.join(result_line))
        return '\n'.join(result)
    
    for biome_file in biome_files:
        try:
            with open(biome_file, "r", encoding="utf-8") as f:
                raw_content = f.read()
            
            # Strip comments before parsing
            clean_json = strip_json_comments(raw_content)
            biome_data = json.loads(clean_json)
            
            biome_name = biome_data.get("name")
            music_track = biome_data.get("musicTrack", {})
            
            if not biome_name:
                print(f"  ⚠️  No 'name' field in {biome_file.name}")
                continue
            
            day_tracks = music_track.get("day", {}).get("tracks", [])
            night_tracks = music_track.get("night", {}).get("tracks", [])
            
            key = f"{category}/{biome_name}"
            result[key] = {
                "day": day_tracks,
                "night": night_tracks
            }
            
            print(f"  ✓ {biome_name} ({len(day_tracks)} day, {len(night_tracks)} night)")
            
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON error in {biome_file.name}: {e}")
        except Exception as e:
            print(f"  ✗ Error reading {biome_file.name}: {e}")
    
    return result


def regenerate_biome_tracks(starbound_unpacked: Path, output_file: Path) -> None:
    """
    Regenerate biome_tracks.json from Starbound biome files.
    
    Args:
        starbound_unpacked: Path to unpacked Starbound assets directory
        output_file: Path where biome_tracks.json will be written
    """
    biomes_root = starbound_unpacked / "biomes"
    
    if not biomes_root.exists():
        print(f"❌ Biomes directory not found: {biomes_root}")
        return
    
    all_biomes = {}
    
    # Process each category directory
    # Keep surface and surface_detached as separate categories to maintain distinction
    categories = [
        ("core", "core"),
        ("space", "space"),
        ("surface", "surface"),
        ("surface_detached", "surface_detached"),
        ("underground", "underground"),
        ("underground_detached", "underground_detached"),
        ("atmosphere", "atmosphere"),
    ]
    
    print("\n🔍 Scanning Starbound biome directories...\n")
    
    for dir_name, category in categories:
        biome_dir = biomes_root / dir_name
        category_biomes = collect_biomes_from_directory(biome_dir, category)
        all_biomes.update(category_biomes)
    
    print(f"\n📊 Total biomes collected: {len(all_biomes)}")
    
    # Sort by key for consistent output
    sorted_biomes = dict(sorted(all_biomes.items()))
    
    # Write to output file
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sorted_biomes, f, indent=2)
        print(f"\n✅ Successfully wrote biome_tracks.json")
        print(f"   Location: {output_file}")
        print(f"   Size: {len(json.dumps(sorted_biomes))} bytes (~{len(json.dumps(sorted_biomes)) // 1024}KB)")
        
    except Exception as e:
        print(f"\n❌ Failed to write output file: {e}")


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    
    starbound_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    # Validate input
    if not starbound_path.exists():
        print(f"❌ Starbound path not found: {starbound_path}")
        sys.exit(1)
    
    regenerate_biome_tracks(starbound_path, output_path)
