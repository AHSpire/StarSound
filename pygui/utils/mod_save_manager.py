"""
[SYSTEM] ModSaveManager - Configuration Persistence Layer
[VERSION] 1.0
[ROLE] MOD_SAVES Handler
[ARCHITECTURE_ID] SAVE_SYSTEM_v3::TIER_2

[TIER_HIERARCHY]
TIER_1: STAGING_FOLDER (atomicwriter) ────────────┐
TIER_2: MOD_SAVES_FOLDER (THIS_CLASS) ← YOU_ARE_HERE
TIER_3: SETTINGS_JSON (SettingsManager) ─────────┘

[OPERATIONAL_SCOPE]
├─ Input: mod_name (str) + mod_config (dict)
├─ Output: mod_saves/{mod_name}.json
├─ Storage: Persistent (user-controlled)
└─ Lifecycle: Survives app restarts, user-deletable

[INTERFACE_METHODS]
FN_001: save_mod(mod_name, mod_config) → bool
        ├─ Sanitizes mod_name for filesystem
        ├─ Wraps config with metadata {mod_name, saved_at, config}
        ├─ Writes to mod_saves/{safe_name}.json
        └─ Returns: True if successful, False if error

FN_002: load_mod(filename) → dict | None
        ├─ Accepts: filename with or without .json extension
        ├─ Reads: mod_saves/{filename}.json
        ├─ Parses: JSON → extracts 'config' field
        └─ Returns: config dict or None if not found

FN_003: list_saved_mods() → List[Tuple[str, str]]
        ├─ Scans: mod_saves/*.json
        ├─ Extracts: (filename, mod_name) from each
        ├─ Sorts: By mod_name alphabetically
        └─ Returns: [(filename, mod_name), ...]

FN_004: delete_mod_save(filename) → bool
        ├─ Accepts: filename with or without .json
        ├─ Checks: if path exists
        ├─ Action: Deletes file via unlink()
        └─ Returns: True/False

FN_005: get_save_path() → Path
        └─ Returns: self.mod_saves_dir for external browsing

[DATA_SCHEMA] Configuration Structure
{
  "mod_name": string,                          # User-provided name
  "saved_at": ISO_8601_timestamp,            # When saved
  "config": {
    "mod_name": string,
    "patch_mode": "add" | "replace" | "both",
    "day_tracks": List[str],                 # File paths
    "night_tracks": List[str],               # File paths
    "selected_biomes": List[Tuple[str, str]], # [(category, biome), ...]
    "folder_path": string                    # Mod destination path
  }
}

[WRITE_FLOW]
starsound_gui.py::_auto_save_mod_state(action)
  ├─ Calls: self._gather_current_mod_state() → dict
  ├─ Calls: self.mod_save_manager.save_mod(mod_name, state)
  │            ↓
  │  [THIS_CLASS]::save_mod()
  │  ├─ Sanitize: safe_name = alphanumeric(mod_name)
  │  ├─ Build: config_with_metadata = {mod_name, saved_at, config}
  │  ├─ Write: Path(mod_saves_dir / f"{safe_name}.json").write_text(json)
  │  └─ Return: True/False
  │
  └─ Logging: [PERSIST] Auto-saved mod on {action}: {mod_name}

[INIT_DEPENDENCIES]
├─ starsound_dir: Path (passed from starsound_gui.py)
├─ Creates: mod_saves_dir = starsound_dir / 'mod_saves'
└─ Ensures: Directory exists via mkdir(parents=True, exist_ok=True)

[ERROR_HANDLING]
- All file operations wrapped in try/except
- Returns False on any exception
- Logs errors to stdout via print()
- Does NOT raise exceptions (fail-safe design)

[INVARIANTS]
INV_001: mod_name sanitization happens before filesystem write
INV_002: JSON always includes both mod_name and config wrapper
INV_003: saved_at timestamp is ISO 8601 format
INV_004: No modifications to config dict (read-only)
INV_005: Extension .json is added/removed transparently

[DISTINCT_FROM]
- STAGING_FOLDER: Contains build artifacts, not user configs
- SETTINGS_JSON: App-level prefs, not per-mod configs
- Both coexist but serve different purposes
"""

import json
import os
from pathlib import Path
from datetime import datetime


class ModSaveManager:
    """Manage mod configuration saves and loads."""
    
    def __init__(self, starsound_dir: Path):
        """
        Initialize mod save manager.
        
        Args:
            starsound_dir: Path to StarSound root directory
        """
        self.starsound_dir = starsound_dir
        self.mod_saves_dir = starsound_dir / 'mod_saves'
        self.mod_saves_dir.mkdir(parents=True, exist_ok=True)
    
    def _serialize_config(self, config: dict) -> dict:
        """Convert tuple keys in replace_selections and add_selections to string keys for JSON serialization"""
        import copy
        config_copy = copy.deepcopy(config)  # Use deepcopy to avoid shared references
        
        # Handle replace_selections with tuple keys → string keys
        if 'replace_selections' in config_copy and isinstance(config_copy['replace_selections'], dict):
            replace_sel = config_copy['replace_selections']
            print(f'[SERIALIZE] Before conversion: {len(replace_sel)} items in replace_selections')
            # Convert tuple keys to string keys: (cat, biome) → "cat|biome"
            serialized_replace = {}
            for key, value in replace_sel.items():
                if isinstance(key, tuple) and len(key) == 2:
                    # Convert tuple (category, biome) to string "category|biome"
                    str_key = f"{key[0]}|{key[1]}"
                    print(f'[SERIALIZE] Converted tuple key {key} -> "{str_key}"')
                else:
                    str_key = str(key)
                    print(f'[SERIALIZE] Kept key: {key} (type: {type(key).__name__})')
                serialized_replace[str_key] = value
            config_copy['replace_selections'] = serialized_replace
            print(f'[SERIALIZE] After conversion: {len(serialized_replace)} items in replace_selections')
        
        # Handle add_selections with tuple keys → string keys (NEW)
        if 'add_selections' in config_copy and isinstance(config_copy['add_selections'], dict):
            add_sel = config_copy['add_selections']
            print(f'[SERIALIZE] Before conversion: {len(add_sel)} items in add_selections')
            # Convert tuple keys to string keys: (cat, biome) → "cat|biome"
            serialized_add = {}
            for key, value in add_sel.items():
                if isinstance(key, tuple) and len(key) == 2:
                    # Convert tuple (category, biome) to string "category|biome"
                    str_key = f"{key[0]}|{key[1]}"
                    print(f'[SERIALIZE] Converted tuple key {key} -> "{str_key}"')
                else:
                    str_key = str(key)
                    print(f'[SERIALIZE] Kept key: {key} (type: {type(key).__name__})')
                serialized_add[str_key] = value
            config_copy['add_selections'] = serialized_add
            print(f'[SERIALIZE] After conversion: {len(serialized_add)} items in add_selections')
        
        return config_copy
    
    def _deserialize_config(self, config: dict) -> dict:
        """Convert string keys in replace_selections back to tuple keys"""
        import copy
        config_copy = copy.deepcopy(config)  # Use deepcopy to avoid shared references
        
        # Handle replace_selections with string keys → tuple keys
        if 'replace_selections' in config_copy and isinstance(config_copy['replace_selections'], dict):
            replace_sel = config_copy['replace_selections']
            print(f'[DESERIALIZE] Before conversion: {len(replace_sel)} items, keys={list(replace_sel.keys())[:3]}...')
            # Convert string keys back to tuples: "cat|biome" → (cat, biome)
            deserialized_replace = {}
            for key, value in replace_sel.items():
                if isinstance(key, str) and '|' in key:
                    parts = key.split('|', 1)  # Split only on first | in case biome name has |
                    tuple_key = (parts[0], parts[1])
                    print(f'[DESERIALIZE] Converted string key "{key}" -> tuple {tuple_key}')
                else:
                    # Already a tuple or other key type, keep as is
                    tuple_key = key if isinstance(key, tuple) else (key, '')
                    print(f'[DESERIALIZE] Kept key: {type(key).__name__} = {tuple_key}')
                
                # CRITICAL FIX: Convert nested track index keys from strings to integers
                # JSON serializes integer keys as strings, so "0" becomes 0, "1" becomes 1, etc.
                converted_value = value
                if isinstance(value, dict):
                    converted_value = {}
                    for time_type in ['day', 'night']:  # day/night sub-dicts
                        if time_type in value and isinstance(value[time_type], dict):
                            converted_tracks = {}
                            for track_idx, ogg_path in value[time_type].items():
                                # Convert string index to integer: "0" → 0
                                try:
                                    int_idx = int(track_idx)
                                    converted_tracks[int_idx] = ogg_path
                                    print(f'[DESERIALIZE] Converted track index "{track_idx}" -> {int_idx}')
                                except ValueError:
                                    # If not a pure number string, keep as is
                                    converted_tracks[track_idx] = ogg_path
                                    print(f'[DESERIALIZE] Could not convert track index "{track_idx}", keeping as string')
                            converted_value[time_type] = converted_tracks
                        else:
                            converted_value[time_type] = value.get(time_type, {})
                
                deserialized_replace[tuple_key] = converted_value
            config_copy['replace_selections'] = deserialized_replace
            print(f'[DESERIALIZE] [OK] Deserialized replace_selections with {len(deserialized_replace)} entries')
        else:
            print(f'[DESERIALIZE] No replace_selections found or not a dict')
        
        # Handle add_selections: convert string keys back to tuples (NEW)
        if 'add_selections' in config_copy and isinstance(config_copy['add_selections'], dict):
            add_sel = config_copy['add_selections']
            print(f'[DESERIALIZE] Before conversion: {len(add_sel)} items, keys={list(add_sel.keys())[:3]}...')
            # Convert string keys back to tuples: "cat|biome" → (cat, biome)
            deserialized_add = {}
            for key, value in add_sel.items():
                if isinstance(key, str) and '|' in key:
                    parts = key.split('|', 1)  # Split only on first | in case biome name has |
                    tuple_key = (parts[0], parts[1])
                    print(f'[DESERIALIZE] Converted string key "{key}" -> tuple {tuple_key}')
                else:
                    # Already a tuple or other key type, keep as is
                    tuple_key = key if isinstance(key, tuple) else (key, '')
                    print(f'[DESERIALIZE] Kept key: {type(key).__name__} = {tuple_key}')
                
                deserialized_add[tuple_key] = value
            config_copy['add_selections'] = deserialized_add
            print(f'[DESERIALIZE] [OK] Deserialized add_selections with {len(deserialized_add)} entries')
        else:
            print(f'[DESERIALIZE] No add_selections found or not a dict')
        
        # Handle selected_biomes: convert list items back to tuples if needed
        if 'selected_biomes' in config_copy and isinstance(config_copy['selected_biomes'], list):
            biomes = config_copy['selected_biomes']
            if biomes and len(biomes) > 0:
                # Check if first item is a list (from JSON) or tuple
                if isinstance(biomes[0], list):
                    print(f'[DESERIALIZE] Converting selected_biomes from lists to tuples: {len(biomes)} items')
                    converted_biomes = []
                    for item in biomes:
                        if isinstance(item, list) and len(item) == 2:
                            tuple_item = (item[0], item[1])
                            converted_biomes.append(tuple_item)
                            print(f'[DESERIALIZE] Converted list {item} -> tuple {tuple_item}')
                        else:
                            converted_biomes.append(item)
                    config_copy['selected_biomes'] = converted_biomes
                    print(f'[DESERIALIZE] [OK] Converted selected_biomes to tuples')
        
        return config_copy
    
    def save_mod(self, mod_name: str, mod_config: dict) -> bool:
        """
        Save a mod configuration to disk.
        
        Args:
            mod_name: Name of the mod (used as filename)
            mod_config: Dictionary containing mod configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Sanitize filename to prevent path traversal
            safe_name = "".join(c for c in mod_name if c.isalnum() or c in ' -_').strip()
            if not safe_name:
                safe_name = "unnamed_mod"
            
            save_path = self.mod_saves_dir / f"{safe_name}.json"
            
            # Serialize config (convert tuple keys to strings)
            serialized_config = self._serialize_config(mod_config)
            replace_sel_count = sum(len(v.get('day', {})) + len(v.get('night', {})) for v in serialized_config.get('replace_selections', {}).values())
            print(f'[SAVE] Serialized config: replace_selections has {replace_sel_count} entries')
            
            # Add metadata
            config_with_metadata = {
                'mod_name': mod_name,
                'saved_at': datetime.now().isoformat(),
                'config': serialized_config
            }
            
            with open(save_path, 'w') as f:
                json.dump(config_with_metadata, f, indent=2)
            
            print(f'[SAVE] [OK] Successfully saved to {save_path}')
            return True
        except Exception as e:
            print(f'[SAVE] [FAIL] Error saving mod: {e}')
            # traceback.print_exc()  # Skip detailed traceback to avoid encoding issues
            return False
    
    def load_mod(self, filename: str) -> dict | None:
        """
        Load a mod configuration from disk.
        
        Args:
            filename: Name of the save file (with or without .json extension)
            
        Returns:
            Dictionary containing mod configuration, or None if load fails
        """
        try:
            if not filename.endswith('.json'):
                filename += '.json'
            
            load_path = self.mod_saves_dir / filename
            
            if not load_path.exists():
                print(f'[LOAD] Mod save file not found: {load_path}')
                return None
            
            with open(load_path, 'r') as f:
                data = json.load(f)
            
            config = data.get('config', data)
            
            # Deserialize config (convert string keys back to tuples)
            config = self._deserialize_config(config)
            replace_sel_count = sum(len(v.get('day', {})) + len(v.get('night', {})) for v in config.get('replace_selections', {}).values())
            print(f'[LOAD] [OK] Loaded mod, replace_selections has {replace_sel_count} entries')
            
            return config
        except Exception as e:
            print(f'[LOAD] [FAIL] Error loading mod: {e}')
            # traceback.print_exc()  # Skip detailed traceback to avoid encoding issues
            return None
    
    def list_saved_mods(self) -> list:
        """
        Get list of all saved mod configurations.
        
        Returns:
            List of (filename, mod_name) tuples
        """
        try:
            mods = []
            for save_file in self.mod_saves_dir.glob('*.json'):
                try:
                    with open(save_file, 'r') as f:
                        data = json.load(f)
                        mod_name = data.get('mod_name', save_file.stem)
                        mods.append((save_file.name, mod_name))
                except:
                    # If file is corrupted, still list it by filename
                    mods.append((save_file.name, save_file.stem))
            
            return sorted(mods, key=lambda x: x[1].lower())
        except Exception as e:
            print(f'Error listing saved mods: {e}')
            return []
    
    def delete_mod_save(self, filename: str) -> bool:
        """
        Delete a saved mod configuration.
        
        Args:
            filename: Name of the save file (with or without .json extension)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not filename.endswith('.json'):
                filename += '.json'
            
            delete_path = self.mod_saves_dir / filename
            
            if delete_path.exists():
                delete_path.unlink()
                return True
            
            return False
        except Exception as e:
            print(f'Error deleting mod save: {e}')
            return False
    
    def get_save_path(self) -> Path:
        """Get the path to the mod_saves directory."""
        return self.mod_saves_dir
