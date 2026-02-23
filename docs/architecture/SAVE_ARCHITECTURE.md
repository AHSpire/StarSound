# StarSound Save Architecture

## Overview

StarSound uses **FOUR separate storage mechanisms** to manage different types of data:

```
StarSound/
├── backups/                           (1) MUSIC BACKUPS FOLDER
│   ├── My Awesome Mod/
│   │   ├── originals/                 [User's original files (OGG, MP3, WAV, etc.)]
│   │   └── converted/                 [Converted OGG files]
│   └── Another Mod/
│       ├── originals/
│       └── converted/
│
├── staging/                           (2) STAGING FOLDER
│   ├── My Awesome Mod/
│   │   ├── music/                     [Ready-to-patch OGG files]
│   │   ├── client.config.patch
│   │   └── ... (patch structure)
│   └── Another Mod/
│       └── ...
│
├── mod_saves/                         (3) MOD SAVES FOLDER
│   ├── settings.json                  (4) SETTINGS.JSON
│   ├── My Awesome Mod.json            [Configuration snapshots]
│   ├── Another Mod.json
│   └── ...
│
└── pygui/
    ├── starsound_gui.py               [Main UI - coordinates all saves]
    ├── utils/
    │   ├── mod_save_manager.py        [Manager for mod_saves/]
    │   ├── settings_manager.py        [Manager for settings.json]
    │   └── ...
    └── dialogs/
        └── ... (UI dialogs)
```

---

## Mechanism 1: MUSIC BACKUPS FOLDER

**Location:** `StarSound/backups/`

**Manager:** `atomicwriter.py`

**Purpose:** Persistent storage of user's original audio files and converted OGG versions

**Structure:**
```
backups/
└── {mod_name}/
    ├── originals/                [User's uploaded files - OGG, MP3, WAV, etc.]
    │   ├── track1.mp3
    │   ├── track2.wav
    │   └── ...
    └── converted/                [Same files converted to OGG format]
        ├── track1.ogg
        ├── track2.ogg
        └── ...
```

**Lifecycle:** Persists between sessions (permanent backup of user's audio)

**Triggers for write:**
- When user selects audio files (copies originals to `backups/{mod_name}/originals/`)
- When audio is converted to OGG (copies to `backups/{mod_name}/converted/`)
- Survives mod deletion (can be reused if mod is recreated)

---

## Mechanism 2: STAGING FOLDER

**Location:** `StarSound/staging/`

**Managers:** `atomicwriter.py`, `GenerateMod` (in patch_generator.py)

**Purpose:** Temporary working directory where mods are built and compiled

**Contains:**
- OGG files ready for patching → `music/` directory
- In-progress mod structures
- JSON patch files
- Generated mod files ready for export

**Lifecycle:** Temporary - should be cleaned periodically

**Triggers for write:**
- When user clicks "Generate Mod"
- When mod name changes (new staging folder created)
- After audio conversion completes (copies converted OGG to `staging/{mod_name}/music/`)

---

## Mechanism 3: MOD_SAVES FOLDER

**Location:** `StarSound/mod_saves/`

**Manager:** `ModSaveManager` class in `utils/mod_save_manager.py`

**Purpose:** Persistent storage of mod configurations for quick reloading

**Contains:** JSON files named `{mod_name}.json`

**Structure of each saved mod:**
```json
{
  "mod_name": "My Awesome Mod",
  "saved_at": "2026-02-17T12:34:56.789000",
  "config": {
    "mod_name": "My Awesome Mod",
    "patch_mode": "add",
    "day_tracks": [...],
    "night_tracks": [...],
    "selected_biomes": [["forest", "surface"]],
    "folder_path": "C:\\..."
  }
}
```

**Lifecycle:** User-controlled (can be deleted manually, survives app restarts)

**Auto-save triggers in starsound_gui.py:**
1. ✅ Mod name confirmed (focus out or dice checkbox)
2. ✅ Audio files selected
3. ✅ Audio files cleared
4. ✅ Audio converted to OGG
5. ✅ Patch mode selected (Add/Replace/Replace+Add)
6. ✅ Biomes selected
7. ✅ Replace track selections finalized
8. ✅ Generate Mod button clicked
9. ✅ Window close (if mod name is set)

---

## Mechanism 4: SETTINGS.JSON

**Location:** `StarSound/mod_saves/settings.json`

**Manager:** `SettingsManager` class in `utils/settings_manager.py`

**Purpose:** Application-level preferences and last-used state

**Contains:**
```json
{
  "last_mod_name": "My Awesome Mod",
  "last_patch_mode": "add",
  "crt_effects_enabled": true,
  "last_used_audio_dir": "C:\\Users\\...",
  "last_used_mod_folder": "C:\\..."
}
```

**Lifecycle:** App-level config, loaded on startup, auto-saved on changes

**Usage:**
- Restore user's session state between app restarts
- Remember last selections without re-asking
- Persist user preferences (CRT effects toggle, etc.)

---

## Key Differences

| Aspect | Music Backups | Staging | Mod Saves | Settings |
|--------|---------------|---------|-----------|----------|
| **Purpose** | Preserve user's audio | Build working directory | Configuration backup | App preferences |
| **Scope** | Per-mod | Per-mod | Per-mod | Global |
| **Format** | Audio files + folders | Audio + patch files | JSON | JSON |
| **Lifecycle** | Permanent | Temporary | Permanent (user-controlled) | Persistent (auto-updated) |
| **Manager** | atomicwriter | atomicwriter | ModSaveManager | SettingsManager |
| **User-visible** | No (technical) | No (technical) | Yes (in UI) | No (behind-the-scenes) |
| **Survives mod deletion** | ✅ Yes | ❌ No | ❌ No | N/A |

---

## Auto-Save Flow

```
User Action                    Saves To
──────────────────────────────────────────────────────────
Write mod name             → mod_saves + settings
                              (on focus out)

Confirm dice name          → mod_saves + settings
                              (on checkbox)

Select audio files         → backups/{mod_name}/originals/ + mod_saves
                              (file copied + config saved)

Clear audio files          → mod_saves
                              (config updated)

Convert audio to OGG       → backups/{mod_name}/converted/ + staging (music/) + mod_saves
                              (after success, non-OGG → OGG in both locations)

Select patch mode          → mod_saves
                              (Add/Replace/Replace+Add)

Select biomes              → mod_saves
                              (biome selection saved)

Replace track selections   → mod_saves
                              (individual track picks)

Generate Mod button        → staging + mod_saves + actual mod file
                              (full compile)

Window close               → mod_saves
                              (final snapshot)
```

---

## Code Cross-References

### starsound_gui.py
- **Line ~130:** Initialize ModSaveManager and SettingsManager
- **Line ~330:** `_auto_save_mod_state(action)` - Main auto-save helper
- **Line ~340:** `clear_audio()` - Clear audio and auto-save
- **Line ~3035:** `browse_audio()` - Audio selection with OGG/non-OGG separation
  - OGG files: backup to `backups/originals/oggs/` + copy to `music/`
  - Non-OGG files: copy to `backups/originals/` for conversion
- **Line ~2160:** Auto-save after audio conversion
- **Line ~1603:** Auto-save after patch mode selection
- **Line ~1667:** Auto-save after replace selections
- **Line ~1915:** Auto-save after biome selection
- **Line ~2555:** `closeEvent()` - Auto-save on window close

### mod_save_manager.py
- `save_mod()` - Saves config to `mod_saves/{mod_name}.json`
- `load_mod()` - Loads config from saved file
- `list_saved_mods()` - Lists all saved mod configs

### settings_manager.py
- `set(key, value)` - Immediately saves to `settings.json`
- `get(key, default)` - Retrieves from loaded settings

---

## Example: User Session

1. **App starts** → Loads `settings.json` → Restores `last_mod_name`
2. **User loads mod** → `ModSaveManager.load_mod()` → Restores full config
3. **User selects OGG file** → Copies to `backups/originals/oggs/` + `music/` + Auto-saves
4. **User selects MP3 file** → Copies to `backups/originals/` + Auto-saves (queued for conversion)
5. **User converts MP3 to OGG** → Auto-saves + copies to `staging/music/`
6. **User generates mod** → Compiles from `staging/` → Creates mod file
7. **User closes app** → Auto-saves final state to `mod_saves/`
8. **Next session** → Settings.json loads last mod automatically

---

## Notes for Developers

- **DO NOT confuse** the four mechanisms - they serve different purposes
- **Backups are permanent** - never delete without user consent
- **Staging is temporary** - can be cleaned periodically
- **Mod_saves is user-visible** - can be browsed and shared
- **Settings is hidden** - manages app-level state
- **OGG handling** - When user selects `.ogg` files:
  - Automatically copied to `backups/{mod_name}/originals/` (backup copy)
  - Automatically copied to `staging/{mod_name}/music/` (ready for Starbound patching)
  - Removed from conversion queue (already in OGG format)
- **Non-OGG handling** - When user selects `.mp3`, `.wav`, etc:
  - Copied to `backups/{mod_name}/originals/` for safe-keeping
  - Kept in selection for async conversion to OGG
  - Converted OGG written to `backups/{mod_name}/converted/`
  - Final `.ogg` also copied to `staging/{mod_name}/music/` after conversion
- **All auto-saves check** `if mod_name and mod_name != 'blank_mod'` - no saving without a real name
- **Thread-safe** - audio conversion happens in background thread but auto-save is main thread
