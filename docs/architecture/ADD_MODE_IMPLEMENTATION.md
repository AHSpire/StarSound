# Add Mode Implementation Guide

**A complete technical reference for how StarSound's "Add Mode" music patching works.**

⚠️ **Note:** If you want the simplest, safest option, use **Remove Mode** instead (see [Remove Mode Guide](REMOVE_MODE_IMPLEMENTATION.md)). Add Mode is for users who specifically want vanilla music mixed with custom music.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Core Concept](#core-concept)
3. [Technical Architecture](#technical-architecture)
4. [The Process](#the-process)
5. [Real-World Example](#real-world-example)
6. [JSON Patch Operations](#json-patch-operations)
7. [Advanced: Vanilla Track Removal](#advanced-vanilla-track-removal)
8. [Edge Cases & Fallback Behavior](#edge-cases--fallback-behavior)
9. [Troubleshooting](#troubleshooting)

---

## Overview

**Add Mode** allows you to:
1. **Add** your custom music to existing vanilla Starbound tracks
2. **Expand** the music pool for more variety
3. **Preserve** all original vanilla tracks (optionally remove them separately)
4. **Stack** multiple mods without conflicts

This is the safest, most compatible mode for players who want more music variety without replacing the original soundtrack.

---

## Core Concept

### The Problem Add Mode Solves

When a player encounters a biome in Starbound, the game randomly selects from all available tracks. By default:

```
Starbound Valley (Day) has 3 vanilla tracks
├─ track_001.ogg
├─ track_002.ogg
└─ track_003.ogg
```

**Add Mode expands this pool:**

```
Starbound Valley (Day) now has 5 tracks (3 vanilla + 2 your custom)
├─ track_001.ogg (vanilla)
├─ track_002.ogg (vanilla)
├─ track_003.ogg (vanilla)
├─ mysong_001.ogg (your custom)
└─ mysong_002.ogg (your custom)
```

Result: Players hear vanilla music ~60% of the time, your music ~40% of the time (random selection).

### Why Add Mode?

- **Compatibility:** Multiple mods can coexist (60% original + 20% mod1 + 20% mod2)
- **Familiarity:** Players still hear the original soundtrack
- **Safety:** No permanent changes to vanilla tracks
- **Non-invasive:** Players can disable/remove the mod cleanly

### Add Mode vs. Other Modes

| Feature | Add Mode | Replace Mode | Both Mode |
|---------|----------|--------------|-----------|
| **Vanilla tracks present?** | ✅ Yes | ❌ No | ❌ No |
| **Can target specific tracks?** | ❌ No | ✅ Yes | ✅ Yes |
| **Multiple mods compatible?** | ✅ Yes | ❌ Limited | ❌ Limited |
| **User control per track?** | ❌ No | ✅ Yes | ✅ Yes |
| **Simplest workflow?** | ✅ Yes | ❌ No | ❌ No |

---

## Technical Architecture

### Data Flow Diagram

```
User Audio Files (OGG/MP3/WAV)
        ↓
[Audio Processing]
        ↓
/music/{filename}.ogg (in mod folder)
        ↓
[Patch Generator]
        ↓
JSON Patch: { "op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/{filename}.ogg" }
        ↓
client.config.patch (in mod)
        ↓
[Starbound Mod Loader]
        ↓
Starbound's JSON Config Updated
        ↓
Game plays mix of vanilla + your tracks
```

### File Structure

```
StarSound Mod Folder/
├── info.json
│   └─ Mod metadata (name, version, etc.)
├── music/
│   ├─ mysong_001.ogg
│   ├─ mysong_002.ogg
│   └─ mysong_003.ogg
└── client.config.patch
    └─ [add operations for all tracks above]
```

### Configuration Stored in StarSound

```
mod_saves/{mod_name}.json:
{
  "mod_name": "My Music Mod",
  "patch_mode": "add",
  "selected_biomes": [["forest", "gentle_forest"]],
  "day_tracks": ["/Users/Music/song1.ogg", "/Users/Music/song2.ogg"],
  "night_tracks": [],
  "audio_config": {
    "day_tracks": {"ffmpeg_output": [...], "duration": [...]}
  }
}
```

---

## The Process

### Step-by-Step Workflow

1. **User launches StarSound** → Opens `starsound_gui.py`
2. **User selects "Add to Game"** → Sets `patch_mode = 'add'`
3. **User selects biome(s)** → Stores in `selected_biomes` (e.g., `[["forest", "gentle_forest"]]`)
4. **User selects audio files** → Stores paths in `day_tracks` and `night_tracks`
5. **User generates mod** → Calls `generate_patch_file()`
   - Copies audio files to `staging/{mod_name}/music/`
   - Converts to OGG if needed (MP3 → OGG, WAV → OGG, etc.)
   - Creates backup in `backups/{mod_name}/originals/` + `converted/`
   - Generates JSON Patch with `add` operations
6. **StarSound creates mod** → Exports to `mod_path` (Starbound/mods/StarSound/)

### Code Entry Points

**Main GUI Handler:**
```python
# starsound_gui.py
def on_add_to_game(self):
    self.patch_mode = 'add'
    self.logger.log('Add mode selected', context='PatchGen')
    self._show_biome_dialog()  # User selects biomes
```

**Patch Generator:**
```python
# patch_generator.py
def generate_patch(mod_path, config, replace_selections=None, logger=None):
    patch_mode = config.get('patch_mode', 'add')
    
    if patch_mode == 'add':
        # Standard Add/Append feature (old behavior)
        # Append to existing vanilla tracks
        for track in day_tracks:
            patch_ops.append({
                'op': 'add',
                'path': '/musicTrack/day/tracks/-',
                'value': f'/music/{track}'
            })
```

---

## Real-World Example

### Scenario: User adds 3 songs to Forest biome

**Input:**
- Biome: `("forest", "gentle_forest")`
- Day tracks: `["C:/Music/ambient1.ogg", "C:/Music/ambient2.ogg", "C:/Music/ambient3.ogg"]`
- Night tracks: `[]` (empty)

**Generated Patch Operations:**

```json
[
  {
    "op": "add",
    "path": "/musicTrack/day/tracks/-",
    "value": "/music/ambient1.ogg"
  },
  {
    "op": "add",
    "path": "/musicTrack/day/tracks/-",
    "value": "/music/ambient2.ogg"
  },
  {
    "op": "add",
    "path": "/musicTrack/day/tracks/-",
    "value": "/music/ambient3.ogg"
  }
]
```

**Starbound's client.config Before:**

```json
{
  "musicTrack": {
    "day": {
      "tracks": [
        "/music/gentle_forest_day_1.ogg",
        "/music/gentle_forest_day_2.ogg"
      ]
    }
  }
}
```

**Starbound's client.config After (patches applied):**

```json
{
  "musicTrack": {
    "day": {
      "tracks": [
        "/music/gentle_forest_day_1.ogg",            // vanilla (kept)
        "/music/gentle_forest_day_2.ogg",            // vanilla (kept)
        "/music/ambient1.ogg",                       // added
        "/music/ambient2.ogg",                       // added
        "/music/ambient3.ogg"                        // added
      ]
    }
  }
}
```

**Result:** Forest day biome now has 5 total tracks. Random selection = ~40% vanilla, ~60% your music.

---

## JSON Patch Operations

### The `add` Operation (Append Syntax)

**Syntax: Using `-` to append to array**

```json
{
  "op": "add",
  "path": "/musicTrack/day/tracks/-",
  "value": "/music/mysong.ogg"
}
```

- `op`: `"add"` ← Always this verb
- `path`: `/musicTrack/day/tracks/-` ← The `-` means "append to end"
- `value`: `/music/mysong.ogg` ← Path relative to Starbound root

### Why `-` is Critical

❌ **WRONG** (without `-`):
```json
{ "op": "add", "path": "/musicTrack/day/tracks/4", "value": "/music/song.ogg" }
```
This would fail if only 2 tracks exist (index 4 doesn't exist).

✅ **RIGHT** (with `-`):
```json
{ "op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/song.ogg" }
```
This always appends, regardless of array length.

### Multi-Biome Add Operations

If user selects multiple biomes, patch generator creates separate operations for each:

```json
[
  // Forest - Day
  { "op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/song1.ogg" },
  
  // Forest - Night
  { "op": "add", "path": "/musicTrack/night/tracks/-", "value": "/music/song2.ogg" },
  
  // Desert - Day
  { "op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/song3.ogg" }
]
```

---

## Advanced: Vanilla Track Removal

### Optional Feature: "Remove Vanilla Tracks"

Checkbox in UI: `"Remove all vanilla tracks before adding mine"`

When enabled:

**Before removal:**
```json
{ "op": "replace", "path": "/musicTrack/day/tracks", "value": [] }
```

**Then add your tracks:**
```json
{ "op": "add", "path": "/musicTrack/day/tracks/0", "value": "/music/mysong.ogg" }
{ "op": "add", "path": "/musicTrack/day/tracks/1", "value": "/music/mysong2.ogg" }
```

Note: Uses direct indices (`/tracks/0`, `/tracks/1`) instead of `-` because the array was just cleared.

### Code Implementation

```python
# patch_generator.py
if remove_vanilla_tracks:
    # Replace entire array with empty
    patch_ops.append({'op': 'replace', 'path': '/musicTrack/day/tracks', 'value': []})
    
    # Add user tracks with direct indices
    for idx, track in enumerate(day_tracks):
        patch_ops.append({
            'op': 'add',
            'path': f'/musicTrack/day/tracks/{idx}',
            'value': f'/music/{track}'
        })
else:
    # Append to existing vanilla (normal Add mode)
    for track in day_tracks:
        patch_ops.append({
            'op': 'add',
            'path': '/musicTrack/day/tracks/-',
            'value': f'/music/{track}'
        })
```

---

## Edge Cases & Fallback Behavior

### Edge Case 1: Empty Night Array

**Problem:** Some biomes have no night music (night array is empty or missing).

**Behavior:**
- Patch generator checks if `night_tracks` is empty
- If empty, skips night operations entirely
- If not empty, generates night `add` operations normally

```python
if night_tracks:
    for track in night_tracks:
        patch_ops.append({
            'op': 'add',
            'path': '/musicTrack/night/tracks/-',
            'value': f'/music/{track}'
        })
```

### Edge Case 2: User Cancels During Audio Processing

**Problem:** User starts adding 5 tracks but cancels midway.

**Behavior:**
- Staging folder is cleaned up
- `backups/` folder still preserves originals (user can retry)
- `mod_saves/{mod_name}.json` is NOT updated (partial state discarded)

### Edge Case 3: Audio Conversion Fails

**Problem:** MP3 file is corrupted or ffmpeg crashes.

**Behavior:**
- Error caught in try/except block
- Operation logs detailed error
- User sees error dialog with file name
- Mod is NOT generated (no corrupted files in /music/)

### Edge Case 4: Multiple Mods + Add Mode

**Problem:** User has Mod A (adds 3 forest tracks) + Mod B (adds 2 forest tracks).

**Behavior:**
- Both mods' patch files are independent
- Starbound loads both patches sequentially
- Forest day tracks = vanilla + Mod A tracks + Mod B tracks = 5 total ✅
- No conflicts (patches are additive)

---

## Troubleshooting

### Issue: "I don't hear my custom music in-game"

**Checklist:**
1. ✅ Mod file exists: `Starbound/mods/StarSound/`
2. ✅ Music files exist: `Starbound/mods/StarSound/music/*.ogg`
3. ✅ Patch file exists: `Starbound/mods/StarSound/client.config.patch`
4. ✅ Patch file is valid JSON: Check with `python -m json.tool`
5. ✅ Biome selection matches where you're testing (forest != desert)
6. ✅ Random chance: Vanilla 40% + your music 60%, you might just not hear it yet

**Debug:**
```bash
# Check if patch file is valid
python -c "import json; json.load(open('Starbound/mods/StarSound/client.config.patch'))"

# Check music files are readable
ls -la Starbound/mods/StarSound/music/
```

### Issue: "Starbound won't load the mod"

**Causes:**
1. **Invalid JSON in patch file** → Check syntax with json formatter
2. **Mod folder permission issue** → Ensure StarSound folder is writable
3. **Corrupted OGG file** → Re-convert with ffmpeg

**Fix:**
```bash
# Validate JSON
python -m json.tool Starbound/mods/StarSound/client.config.patch

# Re-generate mod with fresh conversion
# In StarSound GUI: Select biome, re-upload audio files, generate
```

### Issue: "Add mode silently does nothing"

**Problem:** Patch operations don't error, but nothing happens on load.

**Likely cause:** JSON Patch path is incorrect.

**Check in patch file:**
```json
{
  "path": "/musicTrack/day/tracks/-"  // ✅ Correct
  // vs
  "path": "/musictrack/day/tracks/-"  // ❌ Wrong (lowercase)
  // vs
  "path": "/music/day/tracks/-"       // ❌ Wrong (missing musicTrack)
}
```

**Verify:** The path MUST be exactly `/musicTrack/day/tracks/-` (case-sensitive).

---

## Summary

| Aspect | Details |
|--------|---------|
| **Mode Name** | Add to Game |
| **What it does** | Appends your music to existing vanilla tracks |
| **JSON Operation** | `add` with `-` append syntax |
| **File Structure** | `music/` folder with tracks |
| **Mod compatibility** | ✅ Multiple mods stackable |
| **Vanilla preservation** | ✅ Original tracks intact (unless removed) |
| **Player experience** | Mix of vanilla + custom music (random selection) |
| **Use case** | Players who want more variety, less invasive |
