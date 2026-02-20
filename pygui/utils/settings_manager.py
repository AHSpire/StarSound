"""
[SYSTEM] SettingsManager - Application State Persistence
[VERSION] 1.0
[ROLE] SETTINGS_JSON Handler
[ARCHITECTURE_ID] SAVE_SYSTEM_v3::TIER_3

[TIER_HIERARCHY]
TIER_1: STAGING_FOLDER (atomicwriter) ──────────┐
TIER_2: MOD_SAVES_FOLDER (ModSaveManager) ──────┤
TIER_3: SETTINGS_JSON (THIS_CLASS) ← YOU_ARE_HERE
          └─ Path: StarSound/mod_saves/settings.json

[OPERATIONAL_SCOPE]
├─ Input: key (str) + value (any JSON-serializable)
├─ Output: settings.json key=value pair
├─ Storage: Persistent (app-level)
└─ Lifecycle: Loaded on startup, updated per operation

[INTERFACE_METHODS]
FN_001: set(key, value) → None
        ├─ Action: Updates in-memory dict
        ├─ Action: Immediately writes to settings.json
        ├─ Pattern: Blocking I/O (not async)
        └─ Idempotent: Safe to call repeatedly

FN_002: get(key, default=None) → any
        ├─ Returns: self.settings.get(key, default)
        ├─ Pattern: Memory-resident (no disk I/O)
        └─ Idempotent: Safe to call repeatedly

FN_003: _load_settings() → dict
        ├─ Reads: settings.json if exists
        ├─ Parses: JSON → dict
        ├─ Fallback: Empty dict {} if file missing
        └─ Called: Only during __init__

FN_004: _save_settings() → None
        ├─ Writes: self.settings dict to JSON
        ├─ Format: Pretty-printed (indent=2)
        └─ Called: By set() method

[DATA_SCHEMA] Key Registry
KEY            | TYPE   | DEFAULT | PURPOSE
───────────────┼────────┼─────────┼──────────────────────────────
last_mod_name  | str    | ""      | Restore active mod on startup
last_patch_mode| str    | "add"   | Restore patch mode preference
crt_effects...| bool   | False   | User CRT toggle preference
last_audio_dir | str    | ""      | Audio file dialog starting path
last_mod_folder| str    | ""      | Mod folder dialog starting path

[WRITE_FLOW]
set(key, value)
  ├─ self.settings[key] = value
  ├─ Calls: _save_settings()
  │           ↓
  │  file_path.write_text(json.dumps(self.settings, indent=2))
  │
  └─ Timing: Synchronous (blocking)

[READ_FLOW]
get(key, default)
  ├─ Pattern: No disk I/O (memory-only)
  ├─ Returns: self.settings.get(key, default)
  └─ Timing: Instant (μs, not blocking)

[INIT_SEQUENCE]
MainWindow.__init__()
  ├─ SettingsManager(starsound_dir)
  │   ├─ self.settings_file = {starsound_dir}/mod_saves/settings.json
  │   ├─ Calls: _load_settings()
  │   │   ├─ Reads: settings.json if exists
  │   │   ├─ Returns: dict (or {})
  │   │   └─ Stores: self.settings = result
  │   └─ [READY_FOR_OPERATIONS]
  │
  └─ Used in: __init__ initialization (load defaults)

[USAGE_PATTERN_IN_STARSOUND_GUI]
# Load on startup
last_patch_mode = self.settings.get('last_patch_mode', 'add')
self.patch_mode = last_patch_mode

# Save during operation
self.settings.set('last_patch_mode', 'replace')
self.settings.set('last_mod_name', 'My Mod')

# Usage: Restore session state
def load_last_mod():
    last_name = self.settings.get('last_mod_name', '')
    if last_name:
        config = self.mod_save_manager.load_mod(last_name)
        # Restore UI from config

[KEY_DISTINCTIONS]
This stores:                  NOT this:
─────────────────────────────────────────────────────────
App preferences              Per-mod configs (→ mod_saves/)
Last used state              Current session state
Global settings              UI component state
────────────────────────────────────────────────────────

[INVARIANTS]
INV_001: settings.json is always JSON-valid
INV_002: set() always immediate-writes (no async)
INV_003: get() never accesses disk (cache-only)
INV_004: Keys are lowercase snake_case strings
INV_005: Values must be JSON-serializable

[ERROR_HANDLING]
- _load_settings(): Returns {} if file not found or invalid JSON
- _save_settings(): Returns None on error (no exception raised)
- Pattern: Fail-soft (app continues even if settings unavailable)

[DISTINCT_FROM]
- MOD_SAVES: Per-mod configurations (persistent, user-visible)
- STAGING: Build artifacts (temporary, technical)
- Both coexist independently
"""

import json
from pathlib import Path


class SettingsManager:
    """Manage persistent application settings across sessions."""
    
    def __init__(self, starsound_dir: Path):
        """
        Initialize settings manager.
        
        Args:
            starsound_dir: Path to the StarSound root directory
        """
        self.settings_file = starsound_dir / 'settings.json'
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load settings from JSON file. Return empty dict if file doesn't exist."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f'Warning: Failed to load settings.json: {e}')
                return self._get_defaults()
        return self._get_defaults()
    
    def _get_defaults(self) -> dict:
        """Return default settings."""
        return {
            'last_game_path': '',
            'last_mod_folder': '',
            'last_mod_name': '',
            'last_patch_mode': 'add',
            'crt_effects_enabled': False,
            'current_font': 'Hobo',
        }
    
    def save(self) -> bool:
        """Save settings to JSON file. Return True if successful."""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f'Error: Failed to save settings.json: {e}')
            return False
    
    def get(self, key: str, default=None):
        """Get a setting value. Return default if key doesn't exist."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """Set a setting value and save to disk."""
        self.settings[key] = value
        self.save()
    
    def update(self, **kwargs):
        """Update multiple settings and save to disk."""
        self.settings.update(kwargs)
        self.save()
