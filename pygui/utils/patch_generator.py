# Utility: Flat list of biomes by category
############################################################
# utils/patch_generator.py
# Starbound JSON Patch Generator
#
# --- Starbound Patch Rules (Quick Reference) ---
#
# 1. Use JSON Patch format: list of {op, path, value} objects.
# 2. Add tracks: {"op": "add", "path": "/musicTrack/day/tracks/-"} (or night) appends to the random pool. Do not specify an index to avoid overwriting vanilla tracks.
# 3. Duplicate entries = higher play chance (weighting). Don't do without prompting user.
# 4. Replace all: {"op": "replace", "path": "/musicTrack/day/tracks"} overwrites the whole array.
# 5. Remove vanilla: {"op": "remove", "path": "/musicTrack/day/tracks/<index>"} removes by index.
# 6. Both Replace and Add: Use "replace" to replace original tracks with an empty array, then "add" to add your own tracks. This ensures no vanilla tracks remain.
# 7. Never rely on order: Starbound randomizes track selection (index 0 is not special).
# 8. Use forward slashes in all internal paths (e.g., /music/track.ogg).
# 9. You can combine add/replace/remove in one patch file with correct logic, remove first, then replace vanilla tracks, then add your own tracks.
# 10. Track index logic for replace or remove:
#     - /0 = first track
#     - /1 = second track
#     - /2 = third track
#     - Using "replace" or "remove" with /2 overwrites the third vanilla track.
#
# Example (add to day tracks):
#   {"op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/my_song.ogg"}
############################################################
############# CORRECT EXAMPLE FOR STAR-SOUND PATCH GENERATOR ######################
def add_to_starsound_manifest(ogg_name):
    # Always use pathlib and snake_case
    # Example: Adds a track to the day tracks pool with proper JSON Patch format
    entry = {"op": "add", "path": "/musicTrack/day/tracks/-", "value": f"/music/{ogg_name}"}
    return entry
###################################################################################
import os
import json
from getpass import getuser

# Utility: Flat list of biomes by category
def get_all_biomes_by_category() -> list:
    """
    Returns a flat list of (category, biome) tuples for ALL biomes.
    Dynamically loads from biome_tracks.json to stay current.
    Example: [('surface', 'forest'), ('underground', 'underground0a'), ...]
    
    NOTE: biome_tracks.json is maintained via scripts/regenerate_biome_tracks.py
    To update with new Starbound biomes, run:
        python scripts/regenerate_biome_tracks.py <starbound_unpacked_path> pygui/vanilla_tracks/biome_tracks.json
    Or on Windows, double-click regenerate_biome_tracks.bat
    """
    try:
        from pathlib import Path
        
        # Read from biome_tracks.json
        module_dir = Path(__file__).parent.parent  # pygui/
        biome_tracks_file = module_dir / 'vanilla_tracks' / 'biome_tracks.json'
        
        if biome_tracks_file.exists():
            with open(biome_tracks_file, 'r', encoding='utf-8') as f:
                biome_data = json.load(f)
            
            # Extract (category, biome) tuples from keys like "surface/forest"
            flat_list = []
            for key in sorted(biome_data.keys()):
                parts = key.split('/')
                if len(parts) == 2:
                    category, biome = parts
                    flat_list.append((category, biome))
            
            return flat_list
        else:
            # Fallback: hardcoded list if JSON not available
            biome_categories = {
                'core': ['blaststonecorelayer', 'gardencorelayer', 'magmarockcorelayer', 'mooncorelayer', 'obisidiancorelayer'],
                'space': ['asteroids', 'barrenasteroids', 'space'],
                'surface': [
                    'alien', 'arctic', 'arcticoceanfloor', 'asteroidfield', 'barren', 'cyberspace', 'desert', 'earth', 'forest',
                    'garden', 'jungle', 'lunarbase', 'magma', 'magmaoceanfloor', 'midnight', 'moon', 'ocean',
                    'oceanfloor', 'oceanmission', 'outpost', 'savannah', 'scorched', 'scorchedcity', 'snow', 'tentacle', 'toxic',
                    'toxicoceanfloor', 'tundra', 'volcanic', 'volcanicterraform'
                ],
                'surface_detached': [
                    'alpine', 'bioluminescence', 'bones', 'colourful', 'eyepatch', 'flesh', 'geode', 'giantflowers', 'hive', 
                    'ice', 'mushroompatch', 'oasis', 'prism', 'rust', 'spring', 'steamspring', 'swamp', 'tar'
                ],
                'underground': [
                    'barrenunderground', 'moonunderground', 'underground0a', 'underground0b', 'underground0c', 'underground0d',
                    'underground1a', 'underground1b', 'underground1c', 'underground1d', 'underground3a', 'underground3b', 'underground3c',
                    'underground3d', 'underground5a', 'underground5b', 'underground5c', 'underground5d', 'undergroundbrains',
                    'undergroundbrainssolid', 'undergroundtentacles'
                ],
                'underground_detached': [
                    'bonecaves', 'cellcaves', 'fleshcave', 'icecaves', 'luminouscaves', 'minivillage', 'mushrooms', 
                    'slimecaves', 'stonecaves', 'tarpit', 'wilderness'
                ]
            }
            flat_list = []
            for category, biomes in biome_categories.items():
                for biome in biomes:
                    flat_list.append((category, biome))
            return flat_list
            
    except Exception as e:
        return []

def get_vanilla_tracks_for_biome(biome_category: str, biome_name: str) -> dict:
    """
    Loads vanilla tracks for a specific biome in the EXACT ORDER from the biome file.
    Returns {'dayTracks': [...], 'nightTracks': [...]}
    
    CRITICAL: Tracks MUST be in original biome file order, not sorted!
    Order = Array indices. Wrong order = wrong patches!
    
    Loads from actual .biome JSON file to ensure correct track ordering.
    Note: .biome files contain // comments which need to be stripped before JSON parsing.
    """
    from pathlib import Path
    import json
    import re
    
    def strip_json_comments(json_str: str) -> str:
        """Remove // comments from JSON string while preserving string content"""
        # Pattern: // followed by anything except newline
        # But we need to avoid removing // inside strings
        lines = json_str.split('\n')
        result = []
        for line in lines:
            # Simple approach: find // outside of strings
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
                    # Found // outside string, skip to end of line
                    break
                else:
                    escaped = False
                    result_line.append(char)
            result.append(''.join(result_line))
        return '\n'.join(result)
    
    try:
        # Try to find the unpacked biome file
        biome_file_path = None
        
        # Multiple possible locations for unpacked Starbound files
        search_paths = [
            Path(r'c:\Users\Stephanie\OneDrive\Documents\Original Unpacked Starbound\biomes'),
            Path(r'c:\Steam\steamapps\common\Starbound\assets\packed.unpacked\biomes'),
            Path(__file__).parent.parent / 'vanilla_tracks' / 'biome_files'
        ]
        
        for search_root in search_paths:
            if search_root.exists():
                candidate = search_root / biome_category / f'{biome_name}.biome'
                if candidate.exists():
                    biome_file_path = candidate
                    break
        
        # If found, load track order from the actual biome file
        if biome_file_path:
            with open(biome_file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # Strip comments before parsing JSON
            clean_json = strip_json_comments(raw_content)
            biome_json = json.loads(clean_json)
            
            day_tracks = []
            night_tracks = []
            
            if 'musicTrack' in biome_json:
                music_track = biome_json['musicTrack']
                
                # Extract in exact order from biome file
                if 'day' in music_track and 'tracks' in music_track['day']:
                    day_tracks = [track.split('/')[-1] for track in music_track['day']['tracks']]
                
                if 'night' in music_track and 'tracks' in music_track['night']:
                    night_tracks = [track.split('/')[-1] for track in music_track['night']['tracks']]
            
            return {
                'dayTracks': day_tracks,
                'nightTracks': night_tracks
            }
        
        # Fallback: Try to load from biome_tracks.json if biome file not found
        module_dir = Path(__file__).parent.parent
        biome_tracks_file = module_dir / 'vanilla_tracks' / 'biome_tracks.json'
        
        if biome_tracks_file.exists():
            with open(biome_tracks_file, 'r', encoding='utf-8') as f:
                biome_data = json.load(f)
            
            biome_key = f"{biome_category}/{biome_name}"
            if biome_key in biome_data:
                biome_info = biome_data[biome_key]
                
                # Return in original order (DO NOT SORT)
                day_names = [track.split('/')[-1] for track in biome_info.get('day', [])]
                night_names = [track.split('/')[-1] for track in biome_info.get('night', [])]
                
                return {
                    'dayTracks': day_names,
                    'nightTracks': night_names
                }
        
        return {'dayTracks': [], 'nightTracks': []}
            
    except Exception as e:
        return {'dayTracks': [], 'nightTracks': []}

def suggest_json_fix(error_message):
    suggestions = []
    if 'Expecting property name enclosed in double quotes' in error_message:
        suggestions.append('Check for missing double quotes around property names')
    if 'Extra data' in error_message:
        suggestions.append('Check for trailing commas or extra content after the JSON')
    if 'Unterminated string' in error_message:
        suggestions.append('Check for unclosed string quotes')
    if not suggestions:
        suggestions.append('Check for missing commas, brackets, or braces')
    return suggestions

def attempt_auto_fix(json_string):
    fixed = json_string
    changes_applied = []
    # Remove trailing commas before closing braces/brackets
    import re
    fixed, n = re.subn(r',([\s]*[}}\]])', r'\1', fixed)
    if n:
        changes_applied.append('Removed trailing commas before closing braces/brackets')
    # Add more fixes as needed
    try:
        json.loads(fixed)
        return {'success': True, 'fixed': fixed, 'changesApplied': changes_applied}
    except Exception:
        return {'success': False, 'changesApplied': changes_applied}

def generate_patch(mod_path, config, replace_selections=None, logger=None):
    """
    Generate a patch file for a biome.
    
    Args:
        mod_path: Path to mod directory
        config: Config dict with biome, dayTracks, nightTracks, patchMode, etc.
                Optional 'remove_vanilla_tracks': Boolean to remove all vanilla tracks first (Add mode only)
        replace_selections: Optional dict for Replace feature. Format:
                           {'day': {0: '/path/to/ogg1.ogg', 1: '/path/to/ogg2.ogg'}, 
                            'night': {0: '/path/to/night1.ogg'}}
                           When provided with patchMode='both', generates BOTH individual replace 
                           operations AND add operations in the same patch file.
    
    Returns:
        Dict with success/failure info and patch path
    """
    import shutil
    from pathlib import Path
    
    biome = config.get('biome')
    biome_category = config.get('biome_category', 'surface')
    day_tracks = config.get('dayTracks', [])
    night_tracks = config.get('nightTracks', [])
    patch_mode = config.get('patchMode', 'replace')
    mod_name = config.get('modName', 'StarSoundMod')
    remove_vanilla_tracks = config.get('remove_vanilla_tracks', False)  # 🆕 Check for remove flag

    
    # Validate biome exists
    if not biome:
        return {
            'success': False,
            'message': 'No biome specified'
        }
    
    def get_vanilla_track_id(biome_category, biome_name, day_or_night, track_index):
        """Get the vanilla track ID (full path like /music/filename.ogg) from biome_tracks.json"""
        try:
            from pathlib import Path
            json_file = Path(__file__).parent.parent / 'biome_tracks.json'
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    biome_data = json.load(f)
                
                biome_key = f'{biome_category}/{biome_name}'
                if biome_key in biome_data:
                    tracks = biome_data[biome_key].get(day_or_night, [])
                    if 0 <= track_index < len(tracks):
                        return tracks[track_index]  # Returns like "/music/filename.ogg"
        except Exception:
            pass
        return None
    
    def extract_filename(track_id):
        """Extract just the filename from a track ID like /music/filename.ogg"""
        if track_id and isinstance(track_id, str):
            return track_id.split('/')[-1]  # Gets "filename.ogg"
        return None
    
    def normalize_track_path(track_path):
        """Extract just the filename/relative path from a full file path."""
        import os
        if '\\' in track_path:
            filename = os.path.basename(track_path)
            return filename
        elif ':' in track_path:
            filename = track_path.split('/')[-1] or track_path.split('\\')[-1]
            return filename
        else:
            return track_path
    
    patch_ops = []
    files_copied = []
    copy_errors = []
    
    # CASE 1: Combined BOTH mode (replace_selections + day/night tracks to add)
    if replace_selections and patch_mode == 'both':
        """BOTH mode: Generate individual replace operations THEN add operations"""
        if logger:
            logger.log(f'Both mode: Combining Replace + Add operations for {biome_category}/{biome}', context='PatchGen')
        
        # Ensure music_add_and_replace folder exists for replaced tracks
        mod_music_add_and_replace_folder = Path(mod_path) / 'music_add_and_replace'
        mod_music_add_and_replace_folder.mkdir(parents=True, exist_ok=True)
        
        # Ensure music folder exists for added tracks
        mod_music_folder = Path(mod_path) / 'music'
        mod_music_folder.mkdir(parents=True, exist_ok=True)
        
        # STEP 1: Generate individual replace operations (same as Replace mode)
        day_selections = replace_selections.get('day', {})
        night_selections = replace_selections.get('night', {})
        
        # Sort by index for consistent ordering
        for index in sorted(day_selections.keys()):
            user_ogg_path = day_selections[index]
            
            # Get the vanilla track ID for this biome/day/index
            vanilla_track_id = get_vanilla_track_id(biome_category, biome, 'day', index)
            vanilla_filename = extract_filename(vanilla_track_id) if vanilla_track_id else None
            
            # If we have a vanilla filename, use it; otherwise use user's filename
            if vanilla_filename:
                dest_filename = vanilla_filename
                patch_value = f'/music_add_and_replace/{vanilla_filename}'
            else:
                dest_filename = normalize_track_path(user_ogg_path)
                patch_value = f'/music_add_and_replace/{dest_filename}'
            
            # Copy user's file to mod with vanilla filename
            try:
                src = Path(user_ogg_path)
                if not src.exists():
                    msg = f'Source file does not exist: {user_ogg_path}'
                    copy_errors.append(msg)
                    if logger:
                        logger.warn(msg)
                else:
                    dest = mod_music_add_and_replace_folder / dest_filename
                    shutil.copy2(src, dest)
                    files_copied.append(f'{dest_filename}')
                    if logger:
                        logger.log(f'Copied {src.name} → {dest_filename}')
            except Exception as e:
                msg = f'Failed to copy {user_ogg_path} to {dest_filename}: {e}'
                copy_errors.append(msg)
                if logger:
                    logger.error(msg)
            
            patch_ops.append({
                'op': 'replace',
                'path': f'/musicTrack/day/tracks/{index}',
                'value': patch_value
            })
        
        for index in sorted(night_selections.keys()):
            user_ogg_path = night_selections[index]
            
            # Get the vanilla track ID for this biome/night/index
            vanilla_track_id = get_vanilla_track_id(biome_category, biome, 'night', index)
            vanilla_filename = extract_filename(vanilla_track_id) if vanilla_track_id else None
            
            # If we have a vanilla filename, use it; otherwise use user's filename
            if vanilla_filename:
                dest_filename = vanilla_filename
                patch_value = f'/music_add_and_replace/{vanilla_filename}'
            else:
                dest_filename = normalize_track_path(user_ogg_path)
                patch_value = f'/music_add_and_replace/{dest_filename}'
            
            # Copy user's file to mod with vanilla filename
            try:
                src = Path(user_ogg_path)
                if not src.exists():
                    msg = f'Source file does not exist: {user_ogg_path}'
                    copy_errors.append(msg)
                    if logger:
                        logger.warn(msg)
                else:
                    dest = mod_music_add_and_replace_folder / dest_filename
                    shutil.copy2(src, dest)
                    files_copied.append(f'{dest_filename}')
                    if logger:
                        logger.log(f'Copied {src.name} → {dest_filename}')
            except Exception as e:
                msg = f'Failed to copy {user_ogg_path} to {dest_filename}: {e}'
                copy_errors.append(msg)
                if logger:
                    logger.error(msg)
            
            patch_ops.append({
                'op': 'replace',
                'path': f'/musicTrack/night/tracks/{index}',
                'value': patch_value
            })
        
        # STEP 2: Generate ADD operations (append new tracks after replacements)
        # Normalize all track paths
        day_tracks_norm = [normalize_track_path(t) for t in day_tracks]
        night_tracks_norm = [normalize_track_path(t) for t in night_tracks]
        
        if day_tracks_norm:
            for track in day_tracks_norm:
                # Copy track to mod/music/
                try:
                    src = Path(track)
                    if src.exists():
                        dest = mod_music_folder / src.name
                        shutil.copy2(src, dest)
                        files_copied.append(f'{src.name}')
                        if logger:
                            logger.log(f'Copied ADD track: {src.name}')
                except Exception as e:
                    msg = f'Failed to copy ADD track {track}: {e}'
                    copy_errors.append(msg)
                    if logger:
                        logger.error(msg)
                
                patch_ops.append({
                    'op': 'add',
                    'path': '/musicTrack/day/tracks/-',
                    'value': f'/music/{track}'
                })
        
        if night_tracks_norm:
            for track in night_tracks_norm:
                # Copy track to mod/music/
                try:
                    src = Path(track)
                    if src.exists():
                        dest = mod_music_folder / src.name
                        shutil.copy2(src, dest)
                        files_copied.append(f'{src.name}')
                        if logger:
                            logger.log(f'Copied ADD track: {src.name}')
                except Exception as e:
                    msg = f'Failed to copy ADD track {track}: {e}'
                    copy_errors.append(msg)
                    if logger:
                        logger.error(msg)
                
                patch_ops.append({
                    'op': 'add',
                    'path': '/musicTrack/night/tracks/-',
                    'value': f'/music/{track}'
                })
    
    # CASE 2: Replace feature with individual track selections (Replace mode only)
    elif replace_selections and patch_mode != 'both':
        # Ensure mod music_replacers folder exists
        mod_music_folder = Path(mod_path) / 'music_replacers'
        mod_music_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate individual replace operations for each selected track index
        day_selections = replace_selections.get('day', {})
        night_selections = replace_selections.get('night', {})
        
        # Sort by index for consistent ordering
        for index in sorted(day_selections.keys()):
            user_ogg_path = day_selections[index]
            
            # Get the vanilla track ID for this biome/day/index
            vanilla_track_id = get_vanilla_track_id(biome_category, biome, 'day', index)
            vanilla_filename = extract_filename(vanilla_track_id) if vanilla_track_id else None
            
            # If we have a vanilla filename, use it; otherwise use user's filename
            if vanilla_filename:
                dest_filename = vanilla_filename
                patch_value = f'/music_replacers/{vanilla_filename}'
            else:
                dest_filename = normalize_track_path(user_ogg_path)
                patch_value = f'/music_replacers/{dest_filename}'
            
            # Copy user's file to mod with vanilla filename
            try:
                src = Path(user_ogg_path)
                if not src.exists():
                    msg = f'Source file does not exist: {user_ogg_path}'
                    copy_errors.append(msg)
                    if logger:
                        logger.warn(msg)
                else:
                    dest = mod_music_folder / dest_filename
                    shutil.copy2(src, dest)
                    files_copied.append(f'{dest_filename}')
                    if logger:
                        logger.log(f'Copied {src.name} → {dest_filename}')
            except Exception as e:
                msg = f'Failed to copy {user_ogg_path} to {dest_filename}: {e}'
                copy_errors.append(msg)
                if logger:
                    logger.error(msg)
            
            patch_ops.append({
                'op': 'replace',
                'path': f'/musicTrack/day/tracks/{index}',
                'value': patch_value
            })
        
        for index in sorted(night_selections.keys()):
            user_ogg_path = night_selections[index]
            
            # Get the vanilla track ID for this biome/night/index
            vanilla_track_id = get_vanilla_track_id(biome_category, biome, 'night', index)
            vanilla_filename = extract_filename(vanilla_track_id) if vanilla_track_id else None
            
            # If we have a vanilla filename, use it; otherwise use user's filename
            if vanilla_filename:
                dest_filename = vanilla_filename
                patch_value = f'/music_replacers/{vanilla_filename}'
            else:
                dest_filename = normalize_track_path(user_ogg_path)
                patch_value = f'/music_replacers/{dest_filename}'
            
            # Copy user's file to mod with vanilla filename
            try:
                src = Path(user_ogg_path)
                if not src.exists():
                    msg = f'Source file does not exist: {user_ogg_path}'
                    copy_errors.append(msg)
                    if logger:
                        logger.warn(msg)
                else:
                    dest = mod_music_folder / dest_filename
                    shutil.copy2(src, dest)
                    files_copied.append(f'{dest_filename}')
                    if logger:
                        logger.log(f'Copied {src.name} → {dest_filename}')
            except Exception as e:
                msg = f'Failed to copy {user_ogg_path} to {dest_filename}: {e}'
                copy_errors.append(msg)
                if logger:
                    logger.error(msg)
            
            patch_ops.append({
                'op': 'replace',
                'path': f'/musicTrack/night/tracks/{index}',
                'value': patch_value
            })
    
    # CASE 3: Standard Add/Replace feature (old behavior)
    else:
        # Ensure music folder exists for Add mode
        mod_music_folder = Path(mod_path) / 'music'
        mod_music_folder.mkdir(parents=True, exist_ok=True)
        
        # Copy tracks to mod/music/ BEFORE normalizing paths
        day_tracks_to_add = []
        for track_path in day_tracks:
            try:
                src = Path(track_path)
                if src.exists():
                    dest = mod_music_folder / src.name
                    shutil.copy2(src, dest)
                    files_copied.append(src.name)
                    day_tracks_to_add.append(src.name)  # Use just the filename for patch operations
                    if logger:
                        logger.log(f'Copied day track: {src.name}')
                else:
                    if logger:
                        logger.warn(f'Track file not found or already normalized: {track_path}')
                    day_tracks_to_add.append(track_path)  # Use as-is if file not found
            except Exception as e:
                msg = f'Failed to copy day track {track_path}: {e}'
                copy_errors.append(msg)
                if logger:
                    logger.error(msg)
        
        night_tracks_to_add = []
        for track_path in night_tracks:
            try:
                src = Path(track_path)
                if src.exists():
                    dest = mod_music_folder / src.name
                    shutil.copy2(src, dest)
                    files_copied.append(src.name)
                    night_tracks_to_add.append(src.name)  # Use just the filename for patch operations
                    if logger:
                        logger.log(f'Copied night track: {src.name}')
                else:
                    if logger:
                        logger.warn(f'Track file not found or already normalized: {track_path}')
                    night_tracks_to_add.append(track_path)  # Use as-is if file not found
            except Exception as e:
                msg = f'Failed to copy night track {track_path}: {e}'
                copy_errors.append(msg)
                if logger:
                    logger.error(msg)
        
        # Normalize all track paths for patch generation
        day_tracks = [normalize_track_path(t) for t in day_tracks_to_add]
        night_tracks = [normalize_track_path(t) for t in night_tracks_to_add]
        
        # 🆕 NEW: If Add mode AND remove_vanilla_tracks is enabled, replace vanilla arrays with empty FIRST
        if patch_mode == 'add' and remove_vanilla_tracks:
            if logger:
                logger.log(f'Removing vanilla tracks from {biome_category}/{biome}: replacing arrays with empty', context='PatchGen')
            
            # REPLACE entire day/night track arrays with empty (removes ALL vanilla tracks)
            # This is the core mechanism: replace all → then add new sequentially
            patch_ops.append({'op': 'replace', 'path': '/musicTrack/day/tracks', 'value': []})
            patch_ops.append({'op': 'replace', 'path': '/musicTrack/night/tracks', 'value': []})
            
            if logger:
                logger.log(f'Replaced day/night track arrays with empty arrays', context='PatchGen')
        
        if day_tracks:
            if patch_mode == 'both':
                patch_ops.append({'op': 'replace', 'path': '/musicTrack/day/tracks', 'value': []})
                for track in day_tracks:
                    patch_ops.append({'op': 'add', 'path': '/musicTrack/day/tracks/-', 'value': f'/music/{track}'})
            elif patch_mode == 'add':
                # 🆕 If we removed vanilla tracks, array is now empty - use direct indices
                if remove_vanilla_tracks:
                    for idx, track in enumerate(day_tracks):
                        patch_ops.append({'op': 'add', 'path': f'/musicTrack/day/tracks/{idx}', 'value': f'/music/{track}'})
                    if logger:
                        logger.log(f'Added {len(day_tracks)} day tracks with direct indices (after remove)', context='PatchGen')
                else:
                    # Normal append to existing vanilla tracks
                    for track in day_tracks:
                        patch_ops.append({'op': 'add', 'path': '/musicTrack/day/tracks/-', 'value': f'/music/{track}'})
            elif patch_mode == 'replace':
                patch_ops.append({'op': 'replace', 'path': '/musicTrack/day/tracks', 'value': day_tracks})
        
        if night_tracks:
            if patch_mode == 'both':
                patch_ops.append({'op': 'replace', 'path': '/musicTrack/night/tracks', 'value': []})
                for track in night_tracks:
                    patch_ops.append({'op': 'add', 'path': '/musicTrack/night/tracks/-', 'value': f'/music/{track}'})
            elif patch_mode == 'add':
                # 🆕 If we removed vanilla tracks, array is now empty - use direct indices
                if remove_vanilla_tracks:
                    for idx, track in enumerate(night_tracks):
                        patch_ops.append({'op': 'add', 'path': f'/musicTrack/night/tracks/{idx}', 'value': f'/music/{track}'})
                    if logger:
                        logger.log(f'Added {len(night_tracks)} night tracks with direct indices (after remove)', context='PatchGen')
                else:
                    # Normal append to existing vanilla tracks
                    for track in night_tracks:
                        patch_ops.append({'op': 'add', 'path': '/musicTrack/night/tracks/-', 'value': f'/music/{track}'})
            elif patch_mode == 'replace':
                patch_ops.append({'op': 'replace', 'path': '/musicTrack/night/tracks', 'value': night_tracks})
    
    # Format patch ops as JSON
    json_lines = []
    day_track_count = sum(1 for op in patch_ops if '/day/tracks' in op.get('path', ''))
    night_track_count = sum(1 for op in patch_ops if '/night/tracks' in op.get('path', ''))
    
    night_started = False
    for i, op in enumerate(patch_ops):
        # Add blank line before FIRST night track
        if night_track_count > 0 and day_track_count > 0:
            if '/night/tracks' in op.get('path', '') and not night_started:
                json_lines.append('')
                night_started = True
        
        # Format operation
        # Check if operation has a "value" field (remove ops don't)
        has_value = 'value' in op
        
        if op['op'] == 'remove' and not has_value:
            # Remove operations don't need a value field (RFC 6902)
            line = f'{{"op":"{op["op"]}", "path": "{op["path"]}"'
        else:
            # Add/Replace operations need a value field
            value = op.get("value", None)
            line = f'{{"op":"{op["op"]}", "path": "{op["path"]}", "value":'
            
            if isinstance(value, list):
                formatted_tracks = []
                for track in value:
                    if isinstance(track, str) and not track.startswith('/music/'):
                        formatted_tracks.append(f'/music/{track}')
                    else:
                        formatted_tracks.append(track)
                line += json.dumps(formatted_tracks)
            else:
                line += json.dumps(value)
        
        line += '}'
        if i < len(patch_ops) - 1:
            line += ','
        json_lines.append(line)
    
    json_string = '[\n' + '\n'.join(json_lines) + '\n]'
    
    # Validate JSON
    json_for_validation = '\n'.join([line for line in json_lines if line.strip()])
    json_for_validation = '[\n' + json_for_validation + '\n]'
    
    try:
        json.loads(json_for_validation)
    except Exception as e:
        auto_fix = attempt_auto_fix(json_string)
        suggestions = suggest_json_fix(str(e))
        return {
            'success': False,
            'message': f'JSON Syntax Error: {e}',
            'error': str(e),
            'suggestions': suggestions,
            'autoFix': auto_fix['success'] and {
                'success': True,
                'fixedJson': auto_fix['fixed'],
                'changes': auto_fix['changesApplied']
            } or {
                'success': False,
                'attemptedChanges': auto_fix['changesApplied']
            }
        }
    
    # Write patch file
    patch_file_name = f'{biome}.biome.patch'
    patch_dir = os.path.join(mod_path, 'biomes', biome_category)
    patch_path = os.path.join(patch_dir, patch_file_name)
    os.makedirs(os.path.dirname(patch_path), exist_ok=True)
    
    with open(patch_path, 'w', encoding='utf-8') as f:
        f.write(json_string)
    
    return {
        'success': True,
        'message': f'Patch created at {patch_path}',
        'patchPath': patch_path,
        'filesCopied': files_copied,
        'copyErrors': copy_errors
    }
