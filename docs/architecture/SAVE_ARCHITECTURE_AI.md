# StarSound Save Architecture - AI-Optimized Reference

## [SYSTEM] Core Specification

```
[SYSTEM]                StarSound 3-Tier Save Architecture
[VERSION]               1.0
[SCOPE]                 Complete data persistence workflow
[TARGET_AUDIENCE]       AI agents + Human developers
[STABILITY]             Production-grade (no breaking changes)
[LAST_VALIDATED]        Phase 12 - AI Documentation Optimization
```

---

## [TIER_HIERARCHY] Visual Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│ STARBOUND APPLICATION FLOW                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  START: User opens StarSound app                                   │
│    │                                                                │
│    ├─→ SettingsManager._load_settings()                           │
│    │     └─ Reads: ~/mod_saves/settings.json                      │
│    │     └─ Returns: {last_mod_name, last_patch_mode, ...}        │
│    │                                                                │
│    ├─→ Restore last_mod_name from settings                        │
│    │     └─ If exists: ModSaveManager.load_mod(last_mod_name)     │
│    │     └─ Populates: ALL UI fields from saved config            │
│    │                                                                │
│    ├─ INTERACTIVE PHASE: User edits configuration                 │
│    │  ├─→ [AUTO-SAVE-TRIGGER]: Any field changed                 │
│    │  │     └─ Calls: _auto_save_mod_state(action_name)          │
│    │  │     └─ Writes: mod_saves/{mod_name}.json                 │
│    │  │     └─ Writes: settings.json (last selections)            │
│    │  │                                                             │
│    │  └─→ [AUTO-SAVE-TRIGGER]: Audio file selected               │
│    │        └─ Copies: Source to staging/music/                   │
│    │        └─ Saves: mod_saves/{mod_name}.json                  │
│    │                                                                │
│    └─ GENERATION PHASE: User clicks "Generate Mod"               │
│        ├─→ patch_generator.py reads: replace_selections            │
│        ├─→ atomicwriter.py compiles: staging/ → .pak file         │
│        └─→ _auto_save_mod_state('Generate Mod')                   │
│           └─ Final snapshot saved                                 │
│                                                                     │
│  END: User closes app or closes starsound                         │
│    └─→ closeEvent() → _auto_save_mod_state('window close')       │
│    │    └─ Writes: mod_saves/{mod_name}.json (final state)       │
│    │    └─ Writes: settings.json (last session)                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## [STORAGE_TIERS] Detailed Specification

### [TIER_1_STAGING]

```
Location:     StarSound/staging/
Manager:      atomicwriter.py + patch_generator.py::GenerateMod
Purpose:      Temporary working directory for mod compilation
Scope:        Per-mod (organized by mod_name)
Persistence:  Session-based (retained between app restarts)
User Access:  Internal (not visible in standard UI)

Structure:
  staging/
  ├── {mod_name}/                          (e.g., "My Awesome Mod/")
  │   ├── music/
  │   │   ├── track1.ogg                   [Final OGG files for Starbound patching]
  │   │   ├── track2.ogg                   [Includes: converted non-OGG + backed-up OGGs]
  │   │   └── ...
  │   ├── backups/
  │   │   ├── originals/
  │   │   │   ├── oggs/                    [OGG files user selected (Step 3) - backed up]
  │   │   │   │   ├── track1.ogg
  │   │   │   │   └── ...
  │   │   │   └── [non-OGG files]         [MP3, WAV, FLAC - to be converted]
  │   │   │       ├── track1.mp3
  │   │   │       └── ...
  │   │   └── converted/                   [Post-conversion OGGs after audio processing]
  │   │       └── ...
  │   ├── client.config.patch              [JSON patch file]
  │   ├── _metadata                        [Mod metadata]
  │   └── ...
  └── {another_mod}/
      └── ...

Data Format:  Binary files (.ogg, .pak) + JSON patch

Triggers for Write:
  ✓ User selects audio file → If OGG: copied to backups/originals/oggs/ AND music/
                                If non-OGG: copied to backups/originals/ (kept for conversion)
  ✓ User converts audio → .ogg written to music/
  ✓ User clicks Generate Mod → Full structure compiled
  ✓ User changes mod name → Folder reorganized
  ✓ User adds/removes audio → Structure updated

Cleanup:
  ✗ NOT automatically deleted (persist between sessions)
  ✓ Manual deletion via UI: "Clear Staging" button (future)
  ✓ User can delete staging/{mod_name}/ manually
```

### [TIER_2_MOD_SAVES]

```
Location:     StarSound/mod_saves/
Manager:      ModSaveManager (mod_save_manager.py)
Purpose:      Persistent configuration snapshots for quick reloading
Scope:        Per-mod (one JSON file per mod)
Persistence:  Infinite (user-controlled deletion)
User Access:  High (visible in dropdown, can be shared)

Structure:
  mod_saves/
  ├── settings.json ←────────────────────┐ (SEE [TIER_3])
  ├── My Awesome Mod.json               │
  ├── Another Mod.json                  │
  ├── Legacy Mod.json                   │
  └── ...

JSON Schema per {mod_name}.json:
  {
    "mod_name": "My Awesome Mod",
    "saved_at": "2026-02-17T14:23:45.123456",
    "config": {
      "mod_name": "My Awesome Mod",
      "patch_mode": "add",
      "day_tracks": ["(forest, night)", "(ocean, surface)", ...],
      "night_tracks": [...],
      "selected_biomes": [["forest", "surface_forest"], ...],
      "folder_path": "C:\\Generated Mods\\My Awesome Mod\\",
      "replaced_tracks": {
        "('forest', 'surface_forest')": {
          "day": {0: "C:\\music\\track1.ogg", 2: "C:\\music\\track2.ogg"},
          "night": {1: "C:\\music\\night.ogg"}
        }
      },
      "audio_files": {
        "day": ["C:\\music\\track1.ogg", "C:\\music\\track2.ogg"],
        "night": ["C:\\music\\night.ogg"]
      }
    }
  }

Data Format:  JSON (human-readable)

Triggers for Write (ASE_001 to ASE_011):
  ✓ ASE_001: Mod name confirmed (focus out) → save_mod()
  ✓ ASE_002: Dice checkbox toggled → save_mod()
  ✓ ASE_003: Audio file selected → OGG files: backup + copy; Non-OGG: queue for conversion
             → save_mod()
  ✓ ASE_004: Audio file cleared → save_mod()
  ✓ ASE_005: Audio converted to OGG → save_mod()
  ✓ ASE_006: Add mode selected → save_mod()
  ✓ ASE_007: Replace mode selected → save_mod()
  ✓ ASE_008: Replace+Add mode selected → save_mod()
  ✓ ASE_009: Biome selected → save_mod()
  ✓ ASE_010: Replace track selections finalized → save_mod()
  ✓ ASE_011: Generate Mod button clicked → save_mod()

Associated Methods:
  FN_M001: save_mod(mod_name: str, mod_config: dict) → bool
  FN_M002: load_mod(filename: str) → dict | None
  FN_M003: list_saved_mods() → List[Tuple[str, str]]
  FN_M004: delete_mod_save(filename: str) → bool
  FN_M005: get_save_path() → Path
```

### [TIER_3_SETTINGS]

```
Location:     StarSound/mod_saves/settings.json
Manager:      SettingsManager (settings_manager.py)
Purpose:      Application-level preferences and session restoration
Scope:        Global (single file for all app sessions)
Persistence:  Infinite (overwrites on each session end)
User Access:  Hidden (behind-the-scenes)

JSON Schema:
  {
    "last_mod_name": "My Awesome Mod",
    "last_patch_mode": "add",
    "crt_effects_enabled": true,
    "last_audio_dir": "C:\\Users\\User\\Music",
    "last_mod_folder": "C:\\Generated Mods"
  }

Data Format:  JSON (human-readable)

Triggers for Set (ASE_013 to ASE_016):
  ✓ ASE_013: Mod name confirmed → set('last_mod_name', value)
  ✓ ASE_014: Patch mode selected → set('last_patch_mode', value)
  ✓ ASE_015: CRT effects toggled → set('crt_effects_enabled', value)
  ✓ ASE_016: Audio dialog opened → set('last_audio_dir', value)

Associated Methods:
  FN_S001: set(key: str, value: any) → None
  FN_S002: get(key: str, default: any) → any
  FN_S003: _load_settings() → dict
  FN_S004: _save_settings() → None

Lifecycle:
  App Startup:
    ├─ SettingsManager.__init__()
    ├─ Reads: settings.json
    ├─ Populates: self.settings dict
    └─ [READY]

  During Session:
    ├─ set(key, value) called
    ├─ Updates: self.settings[key] = value
    ├─ Calls: _save_settings()
    └─ Writes: settings.json immediately

  App Cleanup:
    ├─ Last state already saved (via auto-sets)
    └─ No additional cleanup needed
```

---

## [AUTO_SAVE_EVENTS] Complete Registry

### Summary Table

| Event_ID | Event_Name | Trigger_Location | Saves_To | Condition |
|----------|-----------|------------------|----------|-----------|
| ASE_001 | mod_name_confirm | modname_input.focusOutEvent | MOD_SAVES + settings | name != '' |
| ASE_002 | dice_name_confirm | autofill_checkbox.stateChanged | MOD_SAVES + settings | checked==True |
| ASE_003 | audio_select_day | browse_audio_day() completes | MOD_SAVES + staging | file selected |
| ASE_004 | audio_clear_day | clear_audio() called (day) | MOD_SAVES | (cleared) |
| ASE_005 | audio_convert | convert_audio() completes | MOD_SAVES + staging | converted_count > 0 |
| ASE_006 | patch_mode_add | on_add_mode_selected() | MOD_SAVES + settings | mode=='add' |
| ASE_007 | patch_mode_replace | on_replace_mode_selected() | MOD_SAVES + settings | mode=='replace' |
| ASE_008 | patch_mode_replace_add | on_replace_and_add_mode_selected() | MOD_SAVES + settings | mode=='replace_and_add' |
| ASE_009 | biome_selected | biome_checkboxes.stateChanged | MOD_SAVES | biome_list != [] |
| ASE_010 | replace_track_confirm | replace_dialog.accept() | MOD_SAVES | replace_selections != {} |
| ASE_011 | generate_mod | on_generate_mod_clicked() | MOD_SAVES + staging + output | generation completes |
| ASE_012 | window_close | MainWindow.closeEvent() | MOD_SAVES | mod_name != '' |

### Detailed Event Specifications

#### ASE_001: mod_name_confirm

```
Trigger:      User finishes editing mod name field (focus out)
Function:     starsound_gui.py :: on_modname_focus_out()
Handler:      modname_input.focusOutEvent() signal
Action:       _auto_save_mod_state('mod name confirmed')
Saves To:     modname_input.text() → MOD_SAVES/{text}.json
Updates:      settings.json['last_mod_name'] = text
Condition:    mod_name != '' (non-empty, non-blank)
Idempotent:   ✓ Yes (same name → same save)
Rollback:     Load previous version from mod_saves/
```

#### ASE_002: dice_name_confirm

```
Trigger:      User checks "Auto-fill from music" checkbox
Function:     starsound_gui.py :: on_autofill_checkbox_toggled()
Handler:      autofill_checkbox.stateChanged(state) signal
Action:       If checked: set_autofill_name()
              _auto_save_mod_state('dice name confirmed')
Saves To:     Generated name → MOD_SAVES
Updates:      settings.json['last_mod_name'] = generated_name
Condition:    checkbox.isChecked() == True
Idempotent:   ✓ Yes (same checkbox state → same name)
Rollback:     Manual edit mod_name field to undo
```

#### ASE_003: audio_select_day

```
Trigger:      User clicks "Browse" button (Step 3a Day)
Function:     starsound_gui.py :: browse_audio_day() / browse_audio()
Handler:      audio_browse_day_btn.clicked()
Action:       QFileDialog.getOpenFileName() → Select .ogg/.mp3/.wav/etc
              If OGG file:
                ├─ Copy to staging/{mod}/backups/originals/oggs/ (backup)
                ├─ Copy to staging/{mod}/music/ (ready for patching)
                ├─ Remove from selection (no conversion needed)
              If non-OGG file:
                ├─ Copy to staging/{mod}/backups/originals/ (cache)
                ├─ Keep in selection (will be converted)
              _auto_save_mod_state('user selected audio file')
Saves To:     OGG → MOD_SAVES config['audio_files']['day'] + backups + music
              Non-OGG → MOD_SAVES config['audio_files']['day'] (for conversion)
Condition:    File dialog returns non-None path
Idempotent:   ✗ No (each selection replaces previous)
UI Display:   OGGs show as "✅ OGG (ready)" in green (no conversion needed)
              Non-OGGs show with format indicator (will convert)
Threading:    Non-OGG conversion happens in background thread
```

#### ASE_004: audio_clear_day

```
Trigger:      User clicks "Clear" button (Step 3a Day)
Function:     starsound_gui.py :: clear_audio()
Handler:      audio_clear_day_btn.clicked()
Action:       audio_file_day_label.setText('')
              audio_file_day = None
              _auto_save_mod_state('user cleared audio file')
Saves To:     config['audio_files']['day'] = None → MOD_SAVES
Condition:    Always triggered by button click
Idempotent:   ✓ Yes (clearing empty state → same result)
Cleanup:      Staging music files NOT deleted
```

#### ASE_005: audio_convert

```
Trigger:      Audio conversion thread completes successfully
Function:     starsound_gui.py :: convert_audio()
Handler:      Threading callback (on_audio_conversion_complete)
Action:       converted_ogg_path = result['converted_path']
              _auto_save_mod_state('audio conversion complete')
Saves To:     config['audio_files']['converted'] → MOD_SAVES
              .ogg file → staging/music/
Condition:    converted_count > 0 (at least one file converted)
Idempotent:   ✗ No (conversion outputs change filename)
Threading:    ✓ Async (spawned in background, saved on completion)
Error:        If conversion fails, no auto-save triggered
```

#### ASE_006: patch_mode_add

```
Trigger:      User clicks "Add to Music" radio button
Function:     starsound_gui.py :: on_add_mode_selected()
Handler:      add_radio_btn.clicked()
Action:       self.patch_mode = 'add'
              _auto_save_mod_state('patch mode selected: add')
Saves To:     config['patch_mode'] = 'add' → MOD_SAVES
Updates:      settings.json['last_patch_mode'] = 'add'
Condition:    add_radio_btn.isChecked() == True
Idempotent:   ✓ Yes (same mode → same save)
UI Update:    Replace/Replace+Add UI sections hidden
```

#### ASE_007: patch_mode_replace

```
Trigger:      User clicks "Replace Specific Tracks" radio button
Function:     starsound_gui.py :: on_replace_mode_selected()
Handler:      replace_radio_btn.clicked()
Action:       self.patch_mode = 'replace'
              _auto_save_mod_state('patch mode selected: replace')
Saves To:     config['patch_mode'] = 'replace' → MOD_SAVES
Updates:      settings.json['last_patch_mode'] = 'replace'
Condition:    replace_radio_btn.isChecked() == True
Idempotent:   ✓ Yes (same mode → same save)
UI Update:    Replace UI sections shown, Replace+Add hidden
```

#### ASE_008: patch_mode_replace_add

```
Trigger:      User clicks "Replace + Add New Tracks" radio button
Function:     starsound_gui.py :: on_replace_and_add_mode_selected()
Handler:      replace_and_add_radio_btn.clicked()
Action:       self.patch_mode = 'replace_and_add'
              _auto_save_mod_state('patch mode selected: replace_and_add')
Saves To:     config['patch_mode'] = 'replace_and_add' → MOD_SAVES
Updates:      settings.json['last_patch_mode'] = 'replace_and_add'
Condition:    replace_and_add_radio_btn.isChecked() == True
Idempotent:   ✓ Yes (same mode → same save)
UI Update:    Replace + Replace+Add UI sections shown
```

#### ASE_009: biome_selected

```
Trigger:      User checks/unchecks biome checkbox
Function:     starsound_gui.py :: on_biome_checkbox_toggled()
Handler:      biome_checkboxes.stateChanged() signal
Action:       selected_biomes = [checked items]
              _auto_save_mod_state('biome selection changed')
Saves To:     config['selected_biomes'] = list → MOD_SAVES
Condition:    Always triggered by checkbox state change
Idempotent:   ✗ No (each toggle changes state)
Frequency:    High (multiple requests per modifier session)
Debounce:     ✗ None (saves immediately)
```

#### ASE_010: replace_track_confirm

```
Trigger:      User clicks "Confirm & Close" in Replace Tracks dialog
Function:     replace_tracks_dialog.py :: accept()
Handler:      dialog.accepted signal
Action:       MainWindow receives dialog.replace_selections
              _auto_save_mod_state('replace track selections')
Saves To:     config['replaced_tracks'] → MOD_SAVES
Condition:    Dialog closes with accept() (not reject/cancel)
Idempotent:   ✗ No (selections usually different)
Data Structure: {(category, biome): {day: {idx: path}, night: {...}}}
Frequency:    Low (once per Replace mode session)
```

#### ASE_011: generate_mod

```
Trigger:      User clicks "Generate Mod" button
Function:     starsound_gui.py :: on_generate_mod_clicked()
Handler:      generate_btn.clicked()
Action:       patch_generator.py::GenerateMod runs
              _auto_save_mod_state('Generate Mod complete')
Saves To:     Final config snapshot → MOD_SAVES
              Compiled mod files → staging/output/ + user location
Condition:    Generation completes successfully
Idempotent:   ✗ No (generates new mod file)
Error:        If generation fails, no auto-save triggered
Threading:    ✓ Async (progress bar while running)
```

#### ASE_012: window_close

```
Trigger:      User closes MainWindow (X button)
Function:     starsound_gui.py :: closeEvent(event)
Handler:      QMainWindow.closeEvent(event) signal
Action:       _auto_save_mod_state('window close')
Saves To:     Final session state → MOD_SAVES
Condition:    mod_name != '' (no saving for blank mods)
Idempotent:   ✓ Yes (final state snapshot)
Timing:       Before window actually closes
Blocking:     ✗ No (doesn't wait, just queues)
```

---

## [CODE_REFERENCES] Line Numbers

### starsound_gui.py

### starsound_gui.py

| Feature | Function | Line | Purpose |
|---------|----------|------|---------|
| Initialize | `__init__` | 130-170 | Create ModSaveManager, SettingsManager |
| Auto-save hub | `_auto_save_mod_state(action)` | ~2330 | Route all saves through here |
| Clear audio | `clear_audio()` | ~2340 | Clear audio + auto-save |
| Audio selection | `browse_audio()` | ~3035 | Audio selection with OGG/non-OGG separation |
| | | | OGG files: backup to backups/originals/oggs/ + music/ |
| | | | Non-OGG files: copy to backups/originals/ for conversion |
| Audio convert | `convert_audio()` | ~2107 | Handle ASE_005, convert to OGG |
| Patch mode: add | `on_add_mode_selected()` | ~1603 | Handle ASE_006 |
| Patch mode: replace | `on_replace_mode_selected()` | ~1650 | Handle ASE_007 |
| Patch mode: replace+add | `on_replace_and_add_mode_selected()` | ~1680 | Handle ASE_008 |
| Biome select | `on_biome_checkbox_toggled()` | ~1915 | Handle ASE_009 |
| Dialog accept | Signal handler for replace_dialog | ~1667 | Handle ASE_010 |
| Generate mod | `on_generate_mod_clicked()` | ~2200 | Handle ASE_011 |
| Window close | `closeEvent(event)` | ~2555 | Handle ASE_012 |

### mod_save_manager.py

| Feature | Function | Purpose |
|---------|----------|---------|
| Save config | `save_mod(mod_name, mod_config)` | Persist to mod_saves/{name}.json |
| Load config | `load_mod(filename)` | Read from mod_saves/{name}.json |
| List mods | `list_saved_mods()` | Populate dropdown menu |
| Delete mod | `delete_mod_save(filename)` | Remove saved config |
| Get path | `get_save_path()` | Return mod_saves directory path |

### settings_manager.py

| Feature | Function | Purpose |
|---------|----------|---------|
| Get setting | `get(key, default)` | Retrieve app preference |
| Set setting | `set(key, value)` | Update app preference (auto-saves) |

### replace_tracks_dialog.py

| Feature | Function | Purpose |
|---------|----------|---------|
| Dialog init | `__init__(parent, logger, ...)` | Initialize dialog state |
| Accept | `accept()` | Emit signal when user confirms |

---

## [DATA_DEPENDENCY_GRAPH] Critical Flow Paths

```
┌─────────────────────────────────────────────────────────────────┐
│ USER INPUT → AUTO-SAVE CHAIN                                    │
└─────────────────────────────────────────────────────────────────┘

Path 1: Mod Name Change
  modname_input.setText(value)
    ├─→ on_modname_focus_out() triggered
    ├─→ _auto_save_mod_state('mod name confirmed')
    ├─→ mod_save_manager.save_mod(mod_name, state)
    │   └─→ Writes: mod_saves/{mod_name}.json
    ├─→ settings.set('last_mod_name', mod_name)
    │   └─→ Writes: mod_saves/settings.json
    └─→ logger.update_metadata(mod_name=mod_name)

Path 2: Audio File Selection
  audio_browse_day_btn.clicked()
    ├─→ browse_audio_day()
    ├─→ QFileDialog → User selects file
    ├─→ _auto_save_mod_state('user selected audio file')
    ├─→ mod_save_manager.save_mod(mod_name, {audio_files: [...], ...})
    │   └─→ Writes: mod_saves/{mod_name}.json
    ├─→ Copy file to staging/music/{filename}
    │   └─→ Create: staging/{mod_name}/music/{ogg_name}
    └─→ settings.set('last_audio_dir', file_path.parent)
        └─→ Writes: mod_saves/settings.json

Path 3: Audio Conversion (Async)
  convert_audio() (MainThread)
    ├─→ Spawn: AudioConversionThread in background
    │   └─→ ffmpeg.exe processes WAV/MP3 → OGG
    ├─→ on_audio_conversion_complete() (MainThread callback)
    │   ├─→ if converted_count > 0:
    │   ├─→   _auto_save_mod_state('audio conversion complete')
    │   ├─→   mod_save_manager.save_mod(mod_name, {audio_files: [...], ...})
    │   │      └─→ Writes: mod_saves/{mod_name}.json
    │   ├─→   .ogg file exists in staging/music/
    │   └─→   settings.set('last_audio_dir', ...) (already set above)
    └─→ Update UI: Show "Conversion Complete" message

Path 4: Patch Mode Selection
  replace_radio_btn.clicked()
    ├─→ on_replace_mode_selected()
    ├─→ self.patch_mode = 'replace'
    ├─→ _auto_save_mod_state('patch mode selected: replace')
    ├─→ mod_save_manager.save_mod(mod_name, {patch_mode: 'replace', ...})
    │   └─→ Writes: mod_saves/{mod_name}.json
    ├─→ settings.set('last_patch_mode', 'replace')
    │   └─→ Writes: mod_saves/settings.json
    └─→ Update UI: Show Replace-specific sections

Path 5: Replace Tracks Dialog
  replace_radio_btn.clicked()
    ├─→ on_replace_mode_selected() [+ shows UI]
    ├─→ User clicks "Select Tracks" button
    ├─→ ReplaceTracksDialog opens
    │   ├─→ User selects biomes (checkboxes)
    │   ├─→ User assigns tracks to .ogg files
    │   └─→ User clicks "Confirm & Close"
    ├─→ Dialog.accept() emitted
    ├─→ on_replace_dialog_accepted() handler
    │   ├─→ self.replace_selections = dialog.replace_selections
    │   ├─→ _auto_save_mod_state('replace track selections')
    │   ├─→ mod_save_manager.save_mod(mod_name, {replaced_tracks: {...}, ...})
    │   │   └─→ Writes: mod_saves/{mod_name}.json
    │   └─→ Dialog closes
    └─→ Continue to Generate Mod

Path 6: Generate Mod (async)
  generate_btn.clicked()
    ├─→ on_generate_mod_clicked()
    ├─→ Spawn: GenerateMod thread in background
    │   └─→ patch_generator.py processes all config
    ├─→ on_generation_complete() callback
    │   ├─→ if success:
    │   ├─→   _auto_save_mod_state('Generate Mod complete')
    │   ├─→   mod_save_manager.save_mod(mod_name, final_config)
    │   │       └─→ Writes: mod_saves/{mod_name}.json
    │   ├─→   Mod .pak file created in user-chosen location
    │   ├─→   Progress bar updated to 100%
    │   └─→ Show success message
    └─→ Continue to window or new mod

Path 7: Window Close
  MainWindow.closeEvent(event)
    ├─→ if mod_name != '':
    │   ├─→ _auto_save_mod_state('window close')
    │   ├─→ mod_save_manager.save_mod(mod_name, current_state)
    │   └─→ Writes: mod_saves/{mod_name}.json
    └─→ window.close()
```

---

## [INITIALIZATION_ORDER] Startup Sequence

```
1. MainWindow.__init__() starts
   │
   ├─ Create ModSaveManager
   │   └─ ModSaveManager.__init__(starsound_dir)
   │       └─ self.mod_saves_path = starsound_dir / 'mod_saves'
   │
   ├─ Create SettingsManager
   │   └─ SettingsManager.__init__(starsound_dir)
   │       └─ _load_settings()
   │           ├─ Read: mod_saves/settings.json
   │           └─ self.settings = {last_mod_name, ...}
   │
   ├─ Load last mod name from settings
   │   └─ last_name = self.settings.get('last_mod_name', '')
   │
   ├─ If last_name exists:
   │   └─ mod_config = mod_save_manager.load_mod(last_name)
   │       └─ Read: mod_saves/{last_name}.json
   │
   ├─ Restore UI from mod_config
   │   ├─ modname_input.setText(mod_config['mod_name'])
   │   ├─ patch_mode = mod_config.get('patch_mode', 'add')
   │   ├─ selected_biomes = mod_config.get('selected_biomes', [])
   │   ├─ audio_files = mod_config.get('audio_files', {})
   │   └─ Replace track selections, etc.
   │
   └─ [READY_FOR_USER_INTERACTION]
```

---

## [ERROR_HANDLING] Failure Modes

### Mechanism 1: STAGING Failures

```
Scenario: Disk full when writing .ogg to staging/music/
  ├─ atomicwriter.copy_file() raises OSError
  ├─ Caught by: try/except in browse_audio_day()
  ├─ Action: Show user dialog("Disk full - cannot save audio file")
  ├─ MOD_SAVES: NOT updated (partial operation)
  └─ Recovery: User frees space and retries

Scenario: Audio conversion fails
  ├─ ffmpeg.exe process returns non-zero exit code
  ├─ Caught by: AudioConversionThread.run() exception handler
  ├─ Action: Callback on_audio_conversion_error(exception)
  ├─ MOD_SAVES: NOT updated (conversion incomplete)
  ├─ UI: Show error message + error details
  └─ Recovery: User retries conversion or selects different file

Scenario: Corrupt staging folder
  ├─ Directory not found, permission denied, etc.
  ├─ Caught by: try/except in atomicwriter functions
  ├─ Action: Log exception + show user message
  ├─ MOD_SAVES: Still available (independent tier)
  └─ Recovery: User can delete staging/{mod_name}/ and retry
```

### Mechanism 2: MOD_SAVES Failures

```
Scenario: Invalid JSON in mod_saves/{name}.json
  ├─ json.load() raises JSONDecodeError
  ├─ Caught by: ModSaveManager.load_mod()
  ├─ Action: Return None + log error
  ├─ UI: Show "Couldn't load saved mod" message
  └─ Recovery: User can start fresh or restore from backup

Scenario: Permission denied writing to mod_saves/
  ├─ write_text() raises PermissionError
  ├─ Caught by: ModSaveManager.save_mod() exception handler
  ├─ Action: Log error + show user message
  ├─ MOD_SAVES: File unchanged (safe)
  ├─ UI: Continue but warn user
  └─ Recovery: Check file permissions, retry on next operation

Scenario: Disk full when writing mod_saves/{name}.json
  ├─ write_text() raises OSError
  ├─ Caught by: ModSaveManager.save_mod()
  ├─ Action: Log error + show user message
  ├─ MOD_SAVES: File unchanged (safe)
  └─ Recovery: Free disk space and retry
```

### Mechanism 3: SETTINGS Failures

```
Scenario: Invalid JSON in settings.json
  ├─ json.load() raises JSONDecodeError
  ├─ Caught by: SettingsManager._load_settings()
  ├─ Action: Return {} + log warning
  ├─ Result: App starts with no previous session state
  └─ Recovery: Auto-creates new settings.json on first save

Scenario: settings.json missing on startup
  ├─ open() raises FileNotFoundError
  ├─ Caught by: SettingsManager._load_settings()
  ├─ Action: Return {} (init with defaults)
  ├─ Result: App starts with no previous session
  └─ Recovery: Created automatically on first user action
```

---

## [INVARIANTS] Critical Guarantees

```
INV_001: Every auto-save event has a unique Event_ID (ASE_001-012)
         └─ Enforced by: Event registry table

INV_002: STAGING files are never accessed except by atomicwriter.py
         └─ Enforced by: No direct file ops in starsound_gui.py

INV_003: MOD_SAVES always contains valid JSON
         └─ Enforced by: ModSaveManager pre-serialization check

INV_004: SETTINGS always only has one instance (Singleton pattern)
         └─ Enforced by: Single SettingsManager created in __init__

INV_005: Mod name is never empty in saved states
         └─ Enforced by: if mod_name != '' check before save

INV_006: No circular dependencies between save mechanisms
         └─ TIER_1 → TIER_2 only (staging doesn't read mod_saves)
         └─ TIER_2 → TIER_3 only (settings is independent)

INV_007: All .ogg files in staging/music/ match audio_files config
         └─ Enforced by: atomicwriter maintains consistency

INV_008: replace_selections data structure is immutable after save
         └─ Enforced by: Deep copy before passing to patch_generator

INV_009: Auto-save operations are idempotent where noted
         └─ Enforced by: Event specification table

INV_010: No auto-save happens during window initialization
         └─ Enforced by: self.is_initializing flag check
```

---

## [DISTINCT_FROM] Non-Overlap Boundaries

### STAGING ≠ MOD_SAVES

```
STAGING:                          MOD_SAVES:
├─ Purpose: Technical build       ├─ Purpose: User-facing config
├─ Scope: Per-mod folder          ├─ Scope: JSON snapshots
├─ Accessed by: atomicwriter      ├─ Accessed by: ModSaveManager
├─ Deleted: Manual or rarely      ├─ Deleted: By user selection
├─ Format: .ogg + folders         ├─ Format: JSON files
├─ Speed: Local disk I/O          ├─ Speed: JSON parsing
└─ Backup value: Low              └─ Backup value: High
```

### MOD_SAVES ≠ SETTINGS

```
MOD_SAVES:                        SETTINGS:
├─ Scope: Per-mod config          ├─ Scope: Global app state
├─ Multiple files: Yes            ├─ Single file: settings.json
├─ User-selectable: Yes           ├─ User-selectable: No
├─ Shared: Can email to others    ├─ Shared: Not applicable
├─ Updates: Per action (ASE_N)    ├─ Updates: Selective (ASE_13+)
└─ Dropdown: List mods here       └─ Hidden: Background use
```

### STAGING ≠ SETTINGS

```
STAGING:                          SETTINGS:
├─ Scope: Per-mod technical       ├─ Scope: Global preferences
├─ Temporary: Ish                 ├─ Permanent: Until deleted
├─ Contains: Binaries + JSON      ├─ Contains: Only JSON
└─ Accessed by: Internal only     └─ Accessed by: Main window
```

---

## [REGRESSION_TESTS] Test Vectors for Each Event

### Test Vector: ASE_001 (Mod Name Confirm)

```
Setup: Launch app with blank mod name
Test:  
  1. Click modname_input field
  2. Type "Test Mod"
  3. Click elsewhere (focus out)
  4. Verify: mod_saves/Test Mod.json created
  5. Verify: settings.json['last_mod_name'] == 'Test Mod'
  6. Close app
  7. Relaunch app
  8. Verify: modname_input field still shows "Test Mod"
Result: ✓ PASS if all verify steps succeed
```

### Test Vector: ASE_002 (Dice Name Confirm)

```
Setup: Clear mod_name field (or launch fresh)
Test:
  1. Click "Auto-fill from Music" checkbox
  2. Verify: mod_name auto-generated (contains "AStarSound")
  3. Verify: mod_saves/{generated_name}.json created
  4. Uncheck checkbox
  5. Verify: mod_name clears (if expected behavior)
Result: ✓ PASS if name generates + saves
```

### Test Vector: ASE_003 (Audio Select)

```
Setup: Have test.ogg file ready
Test:
  1. Enter mod name "Audio Test"
  2. Click browse button (Step 3a day)
  3. Select test.ogg
  4. Verify: audio_file_day_label shows filename
  5. Verify: test.ogg copied to staging/Audio Test/music/test.ogg
  6. Verify: mod_saves/Audio Test.json updated with audio_files
  7. Close app
  8. Relaunch app
  9. Verify: Mod loaded, audio still present
Result: ✓ PASS if file copied + saved + restored
```

### Test Vector: ASE_005 (Audio Convert)

```
Setup: Have test.mp3 file ready
Test:
  1. Enter mod name "Convert Test"
  2. Click browse button, select test.mp3
  3. Click "Convert to OGG"
  4. Wait for conversion complete
  5. Verify: test.ogg appears in staging/Convert Test/music/
  6. Verify: mod_saves/Convert Test.json updated with .ogg path
  7. Close app, relaunch
  8. Verify: Mod loads with converted audio
Result: ✓ PASS if conversion + save + restore all work
```

### Test Vector: ASE_006/007/008 (Patch Modes)

```
Setup: Create mod with test audio
Test:
  1. Select Add mode
  2. Verify: mod_saves shows patch_mode='add'
  3. Verify: settings.json['last_patch_mode']='add'
  4. Select Replace mode
  5. Verify: mod_saves updated to patch_mode='replace'
  6. Select Replace+Add mode
  7. Verify: mod_saves updated to patch_mode='replace_and_add'
  8. Close app, relaunch
  9. Verify: Last selected mode is current
Result: ✓ PASS if all modes save + restore correctly
```

### Test Vector: ASE_011 (Generate Mod)

```
Setup: Configure complete mod (name, audio, patch mode)
Test:
  1. Click Generate Mod
  2. Wait for generation (progress bar)
  3. Verify: Output .pak file created
  4. Verify: mod_saves with final config snapshot
  5. Close app, relaunch
  6. Verify: Mod name still loaded + all settings restored
Result: ✓ PASS if generation + save + restore all work
```

### Test Vector: ASE_012 (Window Close)

```
Setup: Create mod with some configuration
Test:
  1. Close app window (X button)
  2. Verify: Auto-save triggered (check logs)
  3. Verify: mod_saves/{mod_name}.json has current state
  4. Relaunch app
  5. Verify: Last mod loaded with all previous settings
  6. Verify: Can immediately click Generate (mod ready)
Result: ✓ PASS if close + save + restore all work
```

---

## [DEVELOPER_NOTES] Important Reference

### Thread Safety

```
✓ SAFE: All auto-save operations run on MainThread
✗ UNSAFE: Audio conversion happens in background thread

Consequence:
  - Audio conversion completes in AudioConversionThread
  - Callback on_audio_conversion_complete() queued to MainThread
  - _auto_save_mod_state() called from MainThread
  - No race condition (save ops are serialized)

Pattern:
  def convert_audio():  # Main thread
      thread = AudioConversionThread()
      thread.finished.connect(on_audio_conversion_complete)  # Slot queued
      thread.start()  # Async
  
  def on_audio_conversion_complete(result):  # MainThread (queued)
      _auto_save_mod_state(...)  # Safe
```

### Performance Implications

```
Staging Operations (Disk I/O):
  ├─ Copy .ogg to music/ ≈ 1-5ms per file (SSD)
  ├─ Read .ogg from disk ≈ 5-20ms per file
  ├─ Generate patch JSON ≈ 1-2ms
  └─ Total for 10 tracks ≈ 50-200ms (acceptable)

Mod_Saves Operations (JSON I/O):
  ├─ Serialize config to JSON ≈ 0.5-1ms
  ├─ Write to disk ≈ 1-5ms (SSD)
  └─ Total save ≈ 1-6ms per operation

Settings Operations (JSON I/O):
  ├─ Update single key ≈ 0.1ms
  ├─ Write to disk ≈ 0.5-2ms
  └─ Total set() ≈ 1-2ms per operation

Bottleneck: Disk I/O (especially for large audio files)
Solution: Use SSD + staging folder persistence
```

### Debugging Helpers

```
Enable Verbose Logging:
  ├─ grep_search for "_auto_save_mod_state" to trace all saves
  ├─ Check AStarSoundlog_current.txt for save timestamps
  ├─ Check debug_output.txt for JSON content

Common Issues:
  ├─ Mod not saving?
  │   └─ Verify: ModSaveManager.get_save_path() exists
  │   └─ Verify: mod_name != ''
  │   └─ Verify: Disk has free space
  │
  ├─ Settings not persisting?
  │   └─ Verify: settings.json exists in mod_saves/
  │   └─ Verify: Valid JSON syntax
  │   └─ Verify: File permissions allow write
  │
  ├─ Audio files disappearing?
  │   └─ Verify: staging folder not deleted
  │   └─ Verify: audio_files config matches staging/music/
  │   └─ Verify: File permissions on .ogg files
  │
  └─ Stale config loading?
      └─ Delete: mod_saves/{mod_name}.json
      └─ Restart: App will generate fresh copy
```

---

## [CONCLUSION] Architecture Summary

StarSound's three-tier save architecture provides:

| Tier | Role | Benefit |
|------|------|---------|
| STAGING | Technical compilation | Performance + staging flexibility |
| MOD_SAVES | User-facing configs | Persistence + shareability |
| SETTINGS | App preferences | Session restoration + UX |

Together, they enable:
- ✅ Resume sessions exactly where left off
- ✅ Share mod configs with other users
- ✅ Persist audio conversions across restarts
- ✅ Fast incremental builds
- ✅ Robust error recovery
