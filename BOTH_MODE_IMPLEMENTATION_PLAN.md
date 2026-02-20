# "Both" Mode Implementation Plan

**Status:** Planning Phase (Blocked - See Issues Section)
**Created:** February 17, 2026
**Last Updated:** February 17, 2026

---

## 🎯 Feature Overview

"Both" mode allows users to:
1. Replace specific vanilla tracks with their music
2. Keep unreplaced vanilla tracks
3. Add new tracks to the music pool
4. All in one mod

---

## 📋 Button Details

- **Label:** "Both: Replace and Add Music"
- **Tooltip:** "Replace specific tracks AND add new tracks to the music pool."
- **Location:** Step 5 (Patching Method selection)
- **Status:** Button exists and renamed ✅

---

## 🔄 Workflow (BOTH Steps Required)

### User Flow:
```
Both button clicked
  ↓
Confirmation Dialog
  ↓
REQUIRED: Replace Dialog (select biome(s) + assign replacement tracks)
  ↓
REQUIRED: Biome Dialog (select biome(s) for new tracks)
  ↓
REQUIRED: Step 6 (select day/night tracks to add)
  ↓
Generate Mod (combined patches)
```

### Key Rule:
Both the Replace and Add portions are **MANDATORY**. If user cancels/closes at any step, entire flow cancels.

---

## 📁 Final Patch Format (Per Biome)

**File:** `biomes/{category}/{biome}.biome.patch`

```json
[
    // REPLACE operations (specific indices)
    {"op": "replace", "path": "/musicTrack/day/tracks/0", "value": "/music_replacers/forest/day/track1.ogg"},
    {"op": "replace", "path": "/musicTrack/day/tracks/1", "value": "/music_replacers/forest/day/track2.ogg"},
    ...
    
    // ADD operations (append to end)
    {"op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/new_track1.ogg"},
    {"op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/new_track2.ogg"},
    ...
]
```

### Path Conventions:
- **Replaced tracks:** `/music_replacers/{biome}/{day|night}/filename.ogg`
- **Added tracks:** `/music/filename.ogg`

### File Structure in Mod:
```
staging/{mod_name}/
├── biomes/
│   ├── surface/
│   │   ├── forest.biome.patch (combined replace + add)
│   │   └── ...
│   └── ...
├── music_replacers/
│   ├── forest/
│   │   ├── day/
│   │   │   ├── track1.ogg
│   │   │   └── ...
│   │   └── night/
│   │       └── ...
│   └── ...
└── music/
    ├── added_track1.ogg
    ├── added_track2.ogg
    └── ...
```

---

## 🔧 Implementation Tasks (In Order)

### Phase 1: Handler Setup
- [ ] Update `on_replace_and_add()` to chain dialogs sequentially
  - Show Replace dialog first
  - On success, show biome dialog
  - On success, show Step 6 tracks
  - On success, enable Generate button
- [ ] Ensure both flows store their data properly:
  - `replace_selections` for Replace portion
  - `day_tracks` / `night_tracks` for Add portion

### Phase 2: Patch Generation
- [ ] Create `generate_mod_both_mode()` function that:
  - Generates replace patches from `replace_selections`
  - Generates add patches from `day_tracks` / `night_tracks`
  - Groups by biome affected
  - Combines into single `.biome.patch` per affected biome
  - Returns combined patch array

### Phase 3: File Operations
- [ ] Copy replaced music to `staging/{mod_name}/music_replacers/{biome}/{day|night}/`
- [ ] Copy added music to `staging/{mod_name}/music/`
- [ ] Write combined `.biome.patch` files for each affected biome

### Phase 4: Persistence
- [ ] Ensure `_gather_current_mod_state()` includes both Replace and Add data
- [ ] Verify `ModSaveManager` correctly serializes/deserializes both
- [ ] Test restore on app restart with Both mode mod

### Phase 5: Integration
- [ ] Update `generate_patch_file()` to route to `generate_mod_both_mode()` when `patch_mode == 'both'`
- [ ] Add UI status updates during Both mode flow
- [ ] Test end-to-end Both mode generation

---

## 🐛 Known Issues to Fix FIRST

### Issue 1: Patch Generation Problems
- **Location:** patch_generator.py
- **Problem:** [TBD - Under investigation]
- **Blocks:** Both mode implementation
- **Fix:** TBD

### Issue 2: Persistence Problems
- **Location:** mod_save_manager.py or starsound_gui.py
- **Problem:** [TBD - Under investigation]
- **Blocks:** Both mode testing/restoration
- **Fix:** TBD

---

## 📊 Data Flow

```
starsound_gui.py
├── on_replace_and_add()
│   ├── Show confirm dialog
│   ├── Set patch_mode = 'both'
│   ├── Chain Replace dialog
│   │   └── Store replace_selections
│   ├── Chain Biome dialog
│   │   └── Store selected_biomes
│   ├── Chain Step 6 (day/night)
│   │   └── Store day_tracks, night_tracks
│   └── Call generate_patch_file()
│
└── generate_patch_file()
    └── Call generate_mod_both_mode()
        ├── Generate replace patches
        ├── Generate add patches
        ├── Combine by biome
        ├── Copy music files
        └── Write .biome.patch files

starsound_gui.py (Data Persistence)
├── _gather_current_mod_state()
│   └── Returns: {patch_mode: 'both', replace_selections, day_tracks, night_tracks, selected_biomes}
│
└── ModSaveManager
    ├── save_mod() → mod_saves/{mod_name}.json
    └── load_mod() → restore on app restart
```

---

## ✅ Success Criteria

- [ ] User can click "Both" button
- [ ] Replace dialog appears (required)
- [ ] Biome dialog appears (required)
- [ ] Step 6 appears (required)
- [ ] Generate creates valid combined patches
- [ ] Music files copied to correct folders
- [ ] Generated mod works in Starbound
- [ ] Both mode persists across app restart
- [ ] Can restore and modify Both mode mod

---

## 📝 Notes

- Replace portion handles specific track indices
- Add portion appends to end of music pools
- Both portions write to same `.biome.patch` file per biome
- This is the most complex feature combining Add + Replace + Persistence
- Fix identified issues first before implementing

---

## 🔗 Related Files

- `starsound_gui.py` - Main handler and UI flow
- `utils/patch_generator.py` - Patch generation logic
- `utils/mod_save_manager.py` - Persistence layer
- `atomicwriter.py` - File writing to staging
- `replace_tracks_dialog.py` - Replace UI interface

