# Replace Mode Implementation Guide

**A complete technical reference for how StarSound's "Replace Mode" music patching works.**

⚠️ **Note:** For most users, **Remove Mode** is simpler and safer (see [Remove Mode Guide](REMOVE_MODE_IMPLEMENTATION.md)). Replace Mode is for advanced scenarios requiring precise track-by-track swapping. If you just want custom music in a biome, use Add or Remove Mode!

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Core Concept](#core-concept)
3. [Technical Architecture](#technical-architecture)
4. [The Process](#the-process)
5. [Real-World Example](#real-world-example)
6. [JSON Patch Operations](#json-patch-operations)
7. [Track Selection UI](#track-selection-ui)
8. [Multi-Biome Handling](#multi-biome-handling)
9. [Edge Cases & Fallback Behavior](#edge-cases--fallback-behavior)
10. [Troubleshooting](#troubleshooting)

---

## Overview

**Replace Mode** allows you to:
1. **Target specific** vanilla tracks (by index)
2. **Swap out** individual tracks one by one
3. **Keep** unreplaced vanilla tracks intact
4. **Control** exactly which songs play where

This is the most powerful mode for players with selective, precise preferences about their music.

---

## Core Concept

### The Problem Replace Mode Solves

Say you love the Starbound forest theme, BUT you hate track 2. Replace Mode lets you:

```
Starbound Forest (Day) - Before
├─ track_001.ogg ← Love this
├─ track_002.ogg ← HATE this
└─ track_003.ogg ← Love this

Replace Mode: Swap track 2 ONLY
↓↓↓

Starbound Forest (Day) - After
├─ track_001.ogg ← Kept (vanilla)
├─ mymusic.ogg   ← Replaced track 2
└─ track_003.ogg ← Kept (vanilla)
```

Player never hears track 2 again—only your custom song in that slot.

### Why Replace Mode?

- **Surgical precision:** Replace only the tracks you dislike
- **Partial preservation:** Keep the vanilla tracks you love
- **No vanilla loss:** Replaced tracks aren't deleted, just swapped in config
- **Player experience:** Feels like polished Starbound (not a complete takeover)
- **Compatibility:** Works with other mods (if they don't also replace the same tracks)

### Replace Mode vs. Other Modes

| Feature | Add Mode | Replace Mode | Both Mode |
|---------|----------|--------------|-----------|
| **Vanilla tracks present?** | ✅ Yes | ❌ Removed | ❌ Removed |
| **Can target specific tracks?** | ❌ No | ✅ Yes | ✅ Yes |
| **Multiple mods compatible?** | ✅ Yes | ⚠️ Conflicts possible | ⚠️ Conflicts possible |
| **Per-track control?** | ❌ No | ✅ Yes | ✅ Yes |
| **Simplest workflow?** | ✅ Yes | ❌ No | ❌ No |
| **Can add new tracks?** | ✅ Yes | ❌ No | ✅ Yes |

### ⚠️ CRITICAL WARNING: Silent Biome Risk

**Replace Mode uses REPLACE operations**, which means replaced track indices become empty if the mod is removed.

**If you later disable/remove the StarSound mod:**
- ❌ Affected biomes will have **NO MUSIC** (silent biomes!)
- 🔴 **Permanent data loss** — world data is baked, patches can't retroactively fix it
- ✅ **Solution:** Keep the mod installed indefinitely, OR
- ✅ **Better Solution:** Use **Add Mode instead** (vanilla fallback always available)

**Example of the problem:**
```
Replace Mode: Swap positions 0, 1, 2 in forest/day
├─ Position 0: mymusic1.ogg (was vanilla track 1)
├─ Position 1: mymusic2.ogg (was vanilla track 2)
├─ Position 2: mymusic3.ogg (was vanilla track 3)

If mod is removed/disabled:
├─ Position 0: [EMPTY - ERROR]
├─ Position 1: [EMPTY - ERROR]
├─ Position 2: [EMPTY - ERROR]
Result: SILENT (no music plays)
```

**This applies to BOTH Replace Mode AND Both Mode** (both use REPLACE operations). Use Add Mode to avoid this risk entirely.

---

## Technical Architecture

### Data Flow Diagram

```
User Audio Files (OGG/MP3/WAV)
        ↓
[User selects biome + specific track indices to replace]
        ↓
Stored in replace_selections:
  {
    (category, biome): {
      'day': {0: '/path/to/mysong.ogg', 2: '/path/to/other.ogg'},
      'night': {1: '/path/to/night_song.ogg'}
    }
  }
        ↓
[Audio Processing + File Organization]
        ↓
/music_replacers/{filename}.ogg (in mod folder)
        ↓
[Patch Generator - Replace Operations]
        ↓
JSON Patch: { "op": "replace", "path": "/musicTrack/day/tracks/0", "value": "/music_replacers/mysong.ogg" }
        ↓
client.config.patch (in mod)
        ↓
[Starbound Mod Loader]
        ↓
Starbound's JSON Config Updated
        ↓
Game plays replaced tracks only (no vanilla for replaced slots)
```

### File Structure

```
StarSound Mod Folder/
├── info.json
│   └─ Mod metadata
├── music_replacers/                    [← UNIQUE to Replace mode]
│   ├─ gentle_forest_day_2.ogg         [← Rename to match vanilla filename]
│   └─ gentle_forest_day_4.ogg
└── client.config.patch
    └─ [replace operations targeting indices 2 and 4]
```

**Note:** Replace mode uses `music_replacers/` folder (not `music/`), and filenames are renamed to match vanilla originals for clarity.

### Configuration Stored in StarSound

```
mod_saves/{mod_name}.json:
{
  "mod_name": "My Replace Mod",
  "patch_mode": "replace",
  "selected_biomes": [["forest", "gentle_forest"], ["desert", "scorched_sand"]],
  "replace_selections": {
    "(\"forest\", \"gentle_forest\")": {
      "day": {
        "0": "/Users/Music/forest_day_1.ogg",
        "2": "/Users/Music/forest_day_3.ogg"
      },
      "night": {}
    },
    "(\"desert\", \"scorched_sand\")": {
      "day": {
        "1": "/Users/Music/desert_day_2.ogg"
      },
      "night": {
        "0": "/Users/Music/desert_night_1.ogg"
      }
    }
  }
}
```

---

## The Process

### Step-by-Step Workflow

1. **User launches StarSound** → Opens `starsound_gui.py`

2. **User selects "Replace Base Game Music"** → Sets `patch_mode = 'replace'`

3. **Replace Mode Confirmation Dialog** → User confirms they understand mode limitations
   - "You will be replacing specific tracks"
   - "Unreplaced tracks stay vanilla"
   - "You can't use Add mode for this mod"

4. **ReplaceTracksDialog Opens** (custom dialog)
   - **Step A (Biome Selection):** User checks boxes for biomes to edit
   - **Step B (Track Selection):** For each selected biome:
     - Shows vanilla track names (e.g., "Track 1: gentle_forest_day_1.ogg")
     - User clicks checkboxes for which tracks to replace
     - File picker for choosing replacement audio files

5. **Selections Stored** → Builds `replace_selections` structure:
   ```python
   replace_selections = {
     ('forest', 'gentle_forest'): {
       'day': {0: '/Users/Music/mysong.ogg', 2: '/Users/Music/other.ogg'},
       'night': {}
     }
   }
   ```

6. **User generates mod** → Calls `generate_patch_file()`
   - Copies audio files to `staging/{mod_name}/music_replacers/`
   - Converts to OGG if needed
   - Creates backup in `backups/{mod_name}/originals/` + `converted/`
   - **Key step:** Renames files to vanilla names for clarity (e.g., `mysong.ogg` → `gentle_forest_day_2.ogg`)
   - Generates JSON Patch with `replace` operations (not `add`)

7. **StarSound creates mod** → Exports to `mod_path` (Starbound/mods/StarSound/)

### Code Entry Points

**Main GUI Handler:**
```python
# starsound_gui.py
def on_replace(self):
    # Confirm mode change
    reply = QMessageBox.question(self, 'Confirm Replace Mode', '...')
    
    if reply == QMessageBox.Yes:
        self.patch_mode = 'replace'
        self._show_replace_dialog_directly()  # Opens ReplaceTracksDialog
```

**Replace Dialog:**
```python
# dialogs/replace_tracks_dialog.py
class ReplaceTracksDialog(QDialog):
    def __init__(self, parent=None, logger=None, patch_mode='replace', ...):
        # Biome selection panel first
        # Then track selection per biome
        # Stores selections in self.replace_selections
        
    def on_next_to_track_selection(self):
        # Shows vanilla tracks for selected biome
        # User picks which indices to replace
```

**Patch Generator:**
```python
# utils/patch_generator.py
def generate_patch(mod_path, config, replace_selections=None, logger=None):
    patch_mode = config.get('patch_mode', 'replace')
    
    if replace_selections and patch_mode == 'replace':
        # Generate individual replace operations
        for index, user_ogg_path in replace_selections['day'].items():
            patch_ops.append({
                'op': 'replace',
                'path': f'/musicTrack/day/tracks/{index}',
                'value': f'/music_replacers/{filename}'
            })
```

---

## Real-World Example

### Scenario: User replaces specific desert tracks

**Input:**
- Biome: `("desert", "scorched_sand")`
- Day replacements:
  - Index 1 → `C:/Music/desert_intense.ogg`
  - Index 3 → `C:/Music/desert_ambient.ogg`
- Night replacements: (none)

**Vanilla Desert Day Tracks:**
```
Index 0: scorched_sand_day_1.ogg
Index 1: scorched_sand_day_2.ogg  ← Will replace with desert_intense.ogg
Index 2: scorched_sand_day_3.ogg
Index 3: scorched_sand_day_4.ogg  ← Will replace with desert_ambient.ogg
Index 4: scorched_sand_day_5.ogg
```

**Generated Patch Operations:**

```json
[
  {
    "op": "replace",
    "path": "/musicTrack/day/tracks/1",
    "value": "/music_replacers/scorched_sand_day_2.ogg"
  },
  {
    "op": "replace",
    "path": "/musicTrack/day/tracks/3",
    "value": "/music_replacers/scorched_sand_day_4.ogg"
  }
]
```

**Starbound's client.config After (patches applied):**

```json
{
  "musicTrack": {
    "day": {
      "tracks": [
        "/music_replacers/scorched_sand_day_1.ogg",  // Index 0 - kept vanilla
        "/music_replacers/scorched_sand_day_2.ogg",  // Index 1 - REPLACED
        "/music_replacers/scorched_sand_day_3.ogg",  // Index 2 - kept vanilla
        "/music_replacers/scorched_sand_day_4.ogg",  // Index 3 - REPLACED
        "/music_replacers/scorched_sand_day_5.ogg"   // Index 4 - kept vanilla
      ]
    }
  }
}
```

**Result:** Desert day plays a mix:
- Indices 0, 2, 4 = vanilla tracks (kept)
- Indices 1, 3 = user's custom tracks (replaced)

---

## JSON Patch Operations

### The `replace` Operation (Index Targeting)

**Syntax: Using index to target specific track**

```json
{
  "op": "replace",
  "path": "/musicTrack/day/tracks/1",
  "value": "/music_replacers/my_replacement.ogg"
}
```

- `op`: `"replace"` ← Not `"add"`, but `"replace"`
- `path`: `/musicTrack/day/tracks/1` ← Index `1` = 2nd track (0-indexed)
- `value`: `/music_replacers/my_replacement.ogg` ← Replacement file path

### Index Numbering

**0-indexed = confusing for users, so UI clarifies:**

```
UI shows: "Track 1: gentle_forest_day_1.ogg"  ← User-friendly (1-indexed)
Code uses: index = 0                            ← JSON Patch (0-indexed)

UI shows: "Track 2: gentle_forest_day_2.ogg"
Code uses: index = 1

UI shows: "Track 3: gentle_forest_day_3.ogg"
Code uses: index = 2
```

### Multi-Biome Replace Operations

If user replaces tracks across multiple biomes:

```json
[
  // Forest day - replace index 0
  { "op": "replace", "path": "/musicTrack/day/tracks/0", "value": "/music_replacers/forest_day_1.ogg" },
  
  // Forest night - replace index 2
  { "op": "replace", "path": "/musicTrack/night/tracks/2", "value": "/music_replacers/forest_night_3.ogg" },
  
  // Desert day - replace index 1
  { "op": "replace", "path": "/musicTrack/day/tracks/1", "value": "/music_replacers/desert_day_2.ogg" }
]
```

All three operations apply to **single biome context** in Starbound's config (patches apply to global `/musicTrack/`).

---

## Track Selection UI

### ReplaceTracksDialog - Two-Step UI

#### Step 1: Biome Selection Panel

```
┌─ Replace Tracks - Select Which Tracks to Replace ─┐
│                                                     │
│ Select one or more biomes:                          │
│                                                     │
│ ☐ Forest (3 biomes)                                 │
│   ☐ Gentle Forest (5 day + 4 night tracks)          │
│   ☐ Bamboo Forest (4 day + 3 night tracks)          │
│   ☐ Volcanic Forest (6 day + 5 night tracks)        │
│                                                     │
│ ☐ Desert (2 biomes)                                 │
│   ☐ Scorched Sand (5 day + 4 night tracks)          │
│   ☐ Stony Peak (6 day + 3 night tracks)             │
│                                                     │
│ Selected: Gentle Forest, Scorched Sand             │
│                                                     │
│                              [Next: Select Tracks] │
└─────────────────────────────────────────────────────┘
```

User checks biomes they want to customize.

#### Step 2: Track Selection Panel (Per-Biome)

For each selected biome, show all vanilla tracks:

```
┌─ Replace Tracks - Select Specific Tracks ─────────┐
│                                                     │
│ Gentle Forest - Day Tracks:                         │
│                                                     │
│ ☐ Track 1: gentle_forest_day_1.ogg [Preview]       │
│ ☑ Track 2: gentle_forest_day_2.ogg [Preview]       │
│            ↳ /Users/Music/mysong.ogg [Replace]    │
│ ☐ Track 3: gentle_forest_day_3.ogg [Preview]       │
│ ☑ Track 4: gentle_forest_day_4.ogg [Preview]       │
│            ↳ /Users/Music/other.ogg [Replace]     │
│ ☐ Track 5: gentle_forest_day_5.ogg [Preview]       │
│                                                     │
│───────────────────────────────────────────────────│
│ Gentle Forest - Night Tracks:                       │
│                                                     │
│ ☐ Track 1: gentle_forest_night_1.ogg [Preview]     │
│ ☐ Track 2: gentle_forest_night_2.ogg [Preview]     │
│ ☐ Track 3: gentle_forest_night_3.ogg [Preview]     │
│ ☐ Track 4: gentle_forest_night_4.ogg [Preview]     │
│                                                     │
│                       [Back]  [Next: Scorched Sand] │
└─────────────────────────────────────────────────────┘
```

User can:
- Check boxes to mark which tracks to replace
- Click "Replace" button to pick audio file
- Click "Preview" to hear vanilla track before replacing

---

## Multi-Biome Handling

### Single Mod, Multiple Biomes

User can create ONE mod that replaces tracks across many biomes:

```
My Fantasy Music Mod:
├─ Forest - Gentle Forest
│  └─ Replace day track 1 + night track 3
├─ Desert - Scorched Sand
│  └─ Replace day tracks 0 and 2
└─ Mountain - Snow Peaks
   └─ Replace night track 1
```

**Single `client.config.patch` with 5 replace operations:**

```json
[
  { "op": "replace", "path": "/musicTrack/day/tracks/1", "value": "/music_replacers/gentle_forest_day_2.ogg" },
  { "op": "replace", "path": "/musicTrack/night/tracks/3", "value": "/music_replacers/gentle_forest_night_4.ogg" },
  { "op": "replace", "path": "/musicTrack/day/tracks/0", "value": "/music_replacers/scorched_sand_day_1.ogg" },
  { "op": "replace", "path": "/musicTrack/day/tracks/2", "value": "/music_replacers/scorched_sand_day_3.ogg" },
  { "op": "replace", "path": "/musicTrack/night/tracks/1", "value": "/music_replacers/snow_peaks_night_2.ogg" }
]
```

### Behind the Scenes: Same Biome, Index Conflict

⚠️ **Important:** If two Replace mods try to replace the same track index:

```
Mod A: Replace forest day track 1
Mod B: Replace forest day track 1

Result: Mod B wins (last patch applied)
Consequence: Mod A's replacement is ignored
```

This is why Replace mode is less mod-compatible than Add mode.

---

## Edge Cases & Fallback Behavior

### Edge Case 1: Biome Has No Night Tracks

**Problem:** Some biomes don't have night music.

**Behavior:**
- UI shows night section as "⚠️ No night tracks in vanilla"
- ReplaceTracksDialog hides night checkboxes
- No night `replace` operations generated

```python
if not night_tracks:
    # Empty section - UI skips or shows placeholder
    empty_msg = QLabel('⚠️ No night tracks to replace in this biome')
    layout.addWidget(empty_msg)
```

### Edge Case 2: User Cancels Replace Dialog Mid-Selection

**Problem:** User selects biomes, then cancels before finishing track selection.

**Behavior:**
- `replace_selections` is NOT saved to `mod_saves/`
- Changes are discarded
- User can re-enter Replace mode and try again
- Previous selections are NOT remembered

### Edge Case 3: User Replaces Track That Doesn't Exist

**Problem:** UI shows 5 tracks, user's config tries to replace index 7 (doesn't exist).

**Behavior:**
- JSON Patch fails silently (Starbound mod loader skips invalid operations)
- Mod loads, but that replacement doesn't apply
- No error message (Starbound's behavior)

**Prevention in StarSound:**
- Generate range checks before creating patch operations
- Validate index < length(vanilla_tracks) for that biome

### Edge Case 4: Audio File Removed Between Sessions

**Problem:** User saves mod with `forest_intense.ogg` replacement, then deletes the file.

**Behavior:**
- File path is stored in `backups/{mod_name}/originals/`
- When user loads mod in StarSound, attempts to re-generate
- File not found → Error dialog → User can re-upload

### Edge Case 5: Two Mods Both Replace Audio in Same Biome

**Problem:** Replace Mod A + Replace Mod B, both targeting forest.

**Scenario:**
```
Vanilla forest day tracks: [vanilla1, vanilla2, vanilla3]
Mod A: Replace index 0 with "modA_track.ogg"
Mod B: Replace index 1 with "modB_track.ogg"

Result:
[modA_track.ogg, modB_track.ogg, vanilla3]  ← Both mods applied!
```

**Why it works:** Each mod targets different indices, so no conflict.

**When it fails:**
```
Vanilla forest day tracks: [vanilla1, vanilla2, vanilla3]
Mod A: Replace index 0 with "modA_track.ogg"
Mod B: Replace index 0 with "modB_track.ogg"  ← Same index!

Result:
[modB_track.ogg, vanilla2, vanilla3]  ← Mod B overwrites Mod A!
```

---

## Troubleshooting

### Issue: "Replace dialog shows no vanilla tracks"

**Possible causes:**
1. Vanilla tracks not installed
2. `vanilla_tracks/` folder not found in StarSound
3. Biome configuration file missing

**Fix:**
```bash
# Check vanilla tracks folder exists
ls -la StarSound/vanilla_tracks/

# Ensure biome data files present
ls StarSound/vanilla_tracks/*.json
```

### Issue: "Replaced track doesn't play in-game"

**Checklist:**
1. ✅ File exists: `Starbound/mods/StarSound/music_replacers/mysong.ogg`
2. ✅ Patch is valid: `client.config.patch` is valid JSON
3. ✅ Index matches: Patch targets `/tracks/1` but vanilla has only 2 tracks (0-1, so valid)
4. ✅ Biome matches: You're in the right biome (forest day = forest day patch, not night)
5. ✅ Random chance: Track plays randomly, you might not hear it first 10 plays

**Debug:**
```bash
# Validate patch JSON
python -c "import json; json.load(open('Starbound/mods/StarSound/client.config.patch'))" && echo "JSON OK"

# Check file exists
file Starbound/mods/StarSound/music_replacers/*.ogg
```

### Issue: "Starbound mod won't load at all"

**Causes:**
1. **Invalid JSON patch** → Syntax error in patch file
2. **Missing `info.json`** → Mod metadata file required
3. **Path typo** → Patch references `/music_replaces/` instead of `/music_replacers/`

**Fix steps:**
1. Download mod from Starbound/mods folder
2. Check `client.config.patch` JSON syntax
3. Look for typos in replacement paths
4. Regenerate mod from StarSound if all else fails

### Issue: "Same index replaced by two of my mods"

**Behavior:** Mod B wins (loads second), overwrites Mod A.

**Solution:**
- Use different biomes for each mod, OR
- Use Add Mode instead (conflicts less), OR
- Manually edit one mod's patch to target different indices

---

## Summary

| Aspect | Details |
|--------|---------|
| **Mode Name** | Replace Base Game Music |
| **What it does** | Swaps specific vanilla tracks (by index) |
| **JSON Operation** | `replace` with index targeting |
| **File Structure** | `music_replacers/` folder |
| **Track naming** | Renamed to vanilla names for clarity |
| **Mod compatibility** | ⚠️ Conflicts if replacing same indices |
| **Vanilla preservation** | ✅ Unreplaced tracks kept |
| **Per-track control** | ✅ Full control over each index |
| **User experience** | Selective soundtrack customization |
| **Use case** | Power users with specific preferences |
