# Remove Mode: The Safest & Most Expedient Option

**The easiest, most reliable way to add music to Starbound. Complete technical reference for StarSound's "Remove Mode" (Add mode + vanilla removal).**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Core Concept](#core-concept)
3. [Technical Architecture](#technical-architecture)
4. [The Process](#the-process)
5. [Real-World Example](#real-world-example)
6. [JSON Patch Operations](#json-patch-operations)
7. [Risk & Warning System](#risk--warning-system)
8. [Multi-Track Scenarios](#multi-track-scenarios)
9. [Edge Cases & Fallback Behavior](#edge-cases--fallback-behavior)
10. [Troubleshooting](#troubleshooting)

---

## Overview

**Remove Mode** (checkbox: "🗑️ Remove vanilla tracks first?") is the **safest, simplest, and most predictable** way to modify Starbound music. It allows you to:

1. **Automatically remove** ALL vanilla tracks from selected biomes (clean slate)
2. **Add your custom music** as the ONLY option (guaranteed playback)
3. **No conflicts** - zero risk of vanilla/custom mix-ups
4. **100% predictable** - only your music plays, always
5. **One-step solution** - select biome + select songs + done

### ⚠️ Important Limitation: Mod Conflicts

**Remove Mode uses REPLACE operations**, just like Replace Mode. This means it **can conflict with other music mods that also use REPLACE** (instead of ADD).

**What conflict means:** Mods using REPLACE operations can't stack together. Whichever mod loads last will overwrite the earlier mod's changes.

**Who conflicts with Remove Mode:**
- ✅ ADD-based mods (e.g., other music mods adding tracks) — **NO conflict**
- ⚠️ REPLACE-based mods (some workshop mods) — **WILL conflict**
- ✅ Starbound's vanilla track system — **NO conflict** (that's the point!)

**Example conflict:**
```
Mod A uses Remove Mode: Replaces /musicTrack/day/tracks = [A1.ogg, A2.ogg]
Mod B is a Replace-based mod: Replaces /musicTrack/day/tracks = [B1.ogg]
Result: Whichever loads last wins (usually Mod B overwrites Mod A)
```

**Solution:** If you have other Replace-based music mods enabled:
1. Decide which mod you want to use and choose only one.
2. Understand that once a world is generated, removing either mod will cause them to default back to vanilla soundtracks.

**For most players:** This is not an issue — most workshop mods use ADD mode. You'll know if there's a conflict because only one mod's music will play.

### Who Should Use Remove Mode?

✅ **Recommended for 99% of users** — It's the safest, fastest option
- **First-time users** ← Start here!
- **Players who want simplicity** — Just add your music, no complexity
- **Multi-part tracks** (e.g., part1, part2, part3)
- **Complete thematic overhauls** (completely replace forest, desert, etc.)
- **album soundtracks** (your songs, nothing else)
- **Biome exclusivity** (desert nights = ONLY your music)
- **Anyone avoiding vanilla/custom conflicts** ← This is you!
- **Players without other Replace-based music mods** ← Usually you!

---

## Core Concept

### The Problem Remove Mode Solves

Normally in Add Mode, your tracks mix with vanilla. With 3 vanilla tracks and 2 of yours, each track has equal probability (20% each), meaning ~60% vanilla and ~40% yours simply due to **quantity in the array**, not priority. But for some use cases, you want ONLY your music:

```
Standard Add Mode: Forest Day tracks
├─ vanilla_forest_day_1.ogg
├─ vanilla_forest_day_2.ogg
├─ vanilla_forest_day_3.ogg
├─ your_music_1.ogg
└─ your_music_2.ogg
Result: Each track has 20% play chance (3 vanilla = 60%, 2 yours = 40%)

Remove Mode: Forest Day tracks (with vanilla removal enabled)
├─ your_music_1.ogg
└─ your_music_2.ogg
Result: 100% your music (guaranteed)
```

### Why Is Remove Mode The Best Choice?

#### 🚀 **By the Numbers: Expedient & Safe**

| Metric | Remove Mode | Add Mode | Replace Mode | Both Mode |
|--------|-------------|----------|--------------|----------|
| **Setup steps** | 3 clicks | 3 clicks | 5 clicks | 7 clicks |
| **Risk of vanilla bleed** | ❌ ZERO | ⚠️ HIGH | ⚠️ MEDIUM | ⚠️ MEDIUM |
| **Predictable playback** | ✅ 100% | ❌ ~50-60% | ❌ ~0-100% variable | ❌ complex |
| **User support requests** | Minimal | Moderate | High | Very High |
| **Recommended for beginners** | ✅ YES | ❌ NO | ❌ NO | ❌ NO |

#### 💡 **Real-World Use Cases**

**Use Case 1: Multi-part Tracks (Ambient Suite)**
- **Your music:** "Journey_01.ogg", "Journey_02.ogg", "Journey_03.ogg"
- **Problem with Add Mode:** They shuffle with vanilla tracks, breaks the flow
- **Solution:** Remove Mode → ONLY your 3 parts play → immersion maintained ✅

**Use Case 2: Complete Theme Replacement (Forest Overhaul)**
- **Your goal:** Make forest sound like orchestral garden (no vanilla mixing in)
- **Problem with Add Mode:** 3 vanilla + 2 yours = vanilla plays ~60% of time (math!)
- **Solution:** Remove Mode → guaranteed 100% orchestral ✅

**Use Case 3: Biome-Specific Soundtracks (Desert Nights)**
- **Your goal:** Desert nights at midnight = ONLY your atmospheric track
- **Problem with Replace Mode:** Requires picking specific vanilla tracks to swap
- **Solution:** Remove Mode → one click, all vanilla gone, your track plays ✅

### Detailed Mode Comparison

| Feature | Add Mode | Replace Mode | Both Mode | **Remove Mode** |
|---------|----------|--------------|-----------|----------|
| **Vanilla tracks remain?** | ✅ Yes (mixed in) | ❌ No | ❌ No | ❌ No |
| **Can choose specific tracks to replace?** | ❌ No | ✅ Yes (complex) | ✅ Yes (very complex) | ❌ No (cleaner!) |
| **Add multiple custom tracks?** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Workflow complexity** | Simple | Complex | Very Complex | **Simplest** |
| **Setup time** | ~2 min | ~10 min | ~15 min | **~1 min** |
| **Guarantees ONLY your music plays?** | ❌ No (50-60% vanilla) | ⚠️ Variable | ⚠️ Complex | **✅ 100% YES** |
| **Vanilla/Custom conflict possible?** | ✅ Yes (high) | ⚠️ Maybe | ⚠️ Maybe | **❌ Never** |
| **Conflicts with other Replace-based mods?** | ❌ No | ⚠️ Yes | ⚠️ Yes | **⚠️ Yes (rare)** |
| **User support difficulty** | Moderate | High | Very High | **Low** |
| **Recommended for new users?** | ⚠️ Maybe | ❌ No | ❌ No | **✅ HIGHLY** |
| **Permanent vanilla loss?** | ❌ No | ❌ No | ❌ No | ✅ Yes (but expected) |

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
Selected Biomes + "Remove Vanilla" Checkbox = TRUE
        ↓
[Patch Generator - Remove Phase]
        ↓
Step 1: REPLACE entire day/night arrays with empty
        { "op": "replace", "path": "/musicTrack/day/tracks", "value": [] }
        ↓
Step 2: ADD your tracks with sequential indices (0, 1, 2...)
        { "op": "add", "path": "/musicTrack/day/tracks/0", "value": "/music/{track1}" }
        { "op": "add", "path": "/musicTrack/day/tracks/1", "value": "/music/{track2}" }
        ↓
client.config.patch (in mod/biomes/{category}/{biome}.biome.patch)
        ↓
[Starbound Mod Loader]
        ↓
Vanilla tracks removed, custom tracks become ONLY option
        ↓
Game plays 100% your music (random selection among your tracks)
```

### File Structure

```
StarSound Mod (Remove Mode)
├── info.json
│   └─ Mod metadata
├── music/
│   ├─ your_track_1.ogg
│   ├─ your_track_2.ogg
│   └─ your_track_3.ogg
└── biomes/
    └─ {category}/
        └─ {biome}.biome.patch
           ├─ REPLACE day/tracks with []
           ├─ REPLACE night/tracks with []
           ├─ ADD /music/your_track_1.ogg at index 0
           ├─ ADD /music/your_track_2.ogg at index 1
           └─ ADD /music/your_track_3.ogg at index 2
```

### Configuration Stored in StarSound

```json
{
  "mod_name": "My Forest Overhaul",
  "patch_mode": "add",
  "remove_vanilla_tracks": true,  // KEY: This flag enables Remove mode
  "selected_biomes": [["surface", "forest"]],
  "day_tracks": ["/Users/Music/Ambient_Forest_1.ogg", "/Users/Music/Ambient_Forest_2.ogg"],
  "night_tracks": ["/Users/Music/Forest_Night_Dream.ogg"],
  "audio_config": { ... }
}
```

---

## The Process

### Step-by-Step Workflow

1. **User launches StarSound** → Opens `starsound_gui.py`
2. **User selects "Add to Game"** → Sets `patch_mode = 'add'`
3. **⭐ USER ENABLES "Remove vanilla tracks"** → Checkbox checked → Sets `remove_vanilla_tracks = True`
   - Confirmation dialog warns about permanent consequences
   - User must explicitly click "Yes, I understand"
4. **User selects biome(s)** → Stores in `selected_biomes` (e.g., `[["surface", "forest"]]`)
5. **User selects audio files** → Stores in `day_tracks` and `night_tracks`
6. **User generates mod** → Calls `generate_patch_file()`
   - Copies audio files to `staging/{mod_name}/music/`
   - Detects `remove_vanilla_tracks = True` flag
   - In Add mode with flag: REPLACE vanilla arrays + ADD with direct indices
7. **StarSound creates mod** → Exports to `mod_path` (Starbound/mods/StarSound/)

### Code Entry Points

**Main GUI Handler:**
```python
# starsound_gui.py
def on_add_to_game(self):
    self.patch_mode = 'add'
    self.remove_vanilla_tracks = False  # Default: don't remove
    self._show_biome_dialog()  # Shows checkbox for removal option

def _on_remove_vanilla_toggled(self, checked):
    """Show confirmation dialog when user enables vanilla removal"""
    if checked:
        # WARNING DIALOG appears
        reply = QMessageBox.question(
            self,
            '⚠️ Remove All Vanilla Tracks?',
            'This will PERMANENTLY remove vanilla tracks...'
        )
        if reply != QMessageBox.Yes:
            self.remove_vanilla_checkbox.setChecked(False)
```

**Patch Generator:**
```python
# patch_generator.py
def generate_patch(mod_path, config, logger=None):
    patch_mode = config.get('patchMode', 'add')
    remove_vanilla_tracks = config.get('remove_vanilla_tracks', False)
    
    # CASE: Add mode + remove vanilla enabled
    if patch_mode == 'add' and remove_vanilla_tracks:
        # STEP 1: Clear vanilla arrays
        patch_ops.append({'op': 'replace', 'path': '/musicTrack/day/tracks', 'value': []})
        patch_ops.append({'op': 'replace', 'path': '/musicTrack/night/tracks', 'value': []})
        
        # STEP 2: Add your tracks with direct indices (after arrays are empty)
        for idx, track in enumerate(day_tracks):
            patch_ops.append({
                'op': 'add',
                'path': f'/musicTrack/day/tracks/{idx}',
                'value': f'/music/{track}'
            })
```

---

## Real-World Example

### Scenario: User replaces Forest with orchestral music

**Input:**
- Biome: `("surface", "forest")`
- Day tracks: `["Orchestral_Forest_1.ogg", "Orchestral_Forest_2.ogg"]`
- Night tracks: `["Orchestral_Moonlight.ogg"]`
- Remove vanilla: `TRUE`

**Original Starbound Forest:**
```json
{
  "musicTrack": {
    "day": {
      "tracks": [
        "/music/gentle_forest_day_1.ogg",
        "/music/gentle_forest_day_2.ogg",
        "/music/gentle_forest_day_3.ogg"
      ]
    },
    "night": {
      "tracks": [
        "/music/gentle_forest_night_1.ogg",
        "/music/gentle_forest_night_2.ogg"
      ]
    }
  }
}
```

**Generated Patch Operations:**
```json
[
  {"op": "replace", "path": "/musicTrack/day/tracks", "value": []},
  
  {"op": "replace", "path": "/musicTrack/night/tracks", "value": []},
  
  {"op": "add", "path": "/musicTrack/day/tracks/0", "value": "/music/Orchestral_Forest_1.ogg"},
  {"op": "add", "path": "/musicTrack/day/tracks/1", "value": "/music/Orchestral_Forest_2.ogg"},
  
  {"op": "add", "path": "/musicTrack/night/tracks/0", "value": "/music/Orchestral_Moonlight.ogg"}
]
```

**Starbound's Forest After Patches Applied:**
```json
{
  "musicTrack": {
    "day": {
      "tracks": [
        "/music/Orchestral_Forest_1.ogg",    // Your track (index 0)
        "/music/Orchestral_Forest_2.ogg"     // Your track (index 1)
      ]
    },
    "night": {
      "tracks": [
        "/music/Orchestral_Moonlight.ogg"    // Your track (index 0)
      ]
    }
  }
}
```

**Result:**
- Forest day: 100% your orchestral music (random between 2 tracks)
- Forest night: 100% your moonlight piece
- Original forest music: ❌ PERMANENTLY GONE (unless mod is removed)

---

## JSON Patch Operations

### How Remove Mode Works: REPLACE vs Individual REMOVE

**Why REPLACE instead of individual REMOVE operations?**

There are two ways to clear all vanilla tracks:

❌ **Individual REMOVE operations (old approach - not used):**
```json
{"op":"remove", "path": "/musicTrack/day/tracks/11"},
{"op":"remove", "path": "/musicTrack/day/tracks/10"},
{"op":"remove", "path": "/musicTrack/day/tracks/9"},
... 25+ more remove operations for all vanilla tracks
```
Problems:
- Generates 25+ operations instead of 1
- Complex index management (each remove shifts indices)
- Fragile - easily breaks if vanilla track count changes
- Hard to maintain and debug
- Permanent removal of vanilla tracks from save/biome

✅ **REPLACE operation (current approach - much better):**
```json
{"op":"replace", "path": "/musicTrack/day/tracks", "value": []}
```
Benefits:
- Single clean operation instead of 25+
- Instantly clears entire array in one step
- Robust - works regardless of vanilla track count
- Easy to understand and maintain
- Allows vanilla music to play as fallback if mod is removed

We use REPLACE because it's simpler, more reliable, and achieves the same result with far fewer operations.

### REPLACE Operation (Clear Vanilla)

**Syntax: Replace entire array with empty**

```json
{
  "op": "replace",
  "path": "/musicTrack/day/tracks",
  "value": []
}
```

- `op`: `"replace"` ← Replaces the entire array
- `path`: `/musicTrack/day/tracks` ← Full array path (not individual index)
- `value`: `[]` ← Empty array (removes all vanilla tracks)

### ADD Operation (Sequential Indices)

**Syntax: Add with direct index (not append)**

```json
{
  "op": "add",
  "path": "/musicTrack/day/tracks/0",
  "value": "/music/your_song.ogg"
}
```

- `op`: `"add"` ← Add operation
- `path`: `/musicTrack/day/tracks/0` ← Specific index (0, 1, 2...) [NOT `-`]
- `value`: `/music/your_song.ogg` ← Path relative to Starbound root

**Why Direct Indices?**

❌ **WRONG (append syntax):**
```json
{ "op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/song.ogg" }
```
This would FAIL if array is empty or if later tracks use different syntax.

✅ **RIGHT (direct index):**
```json
{ "op": "add", "path": "/musicTrack/day/tracks/0", "value": "/music/song1.ogg" }
{ "op": "add", "path": "/musicTrack/day/tracks/1", "value": "/music/song2.ogg" }
```
This works regardless of array state and guarantees order.

### Order Matters!

⚠️ **CRITICAL:** REPLACE operations MUST come BEFORE ADD operations

```json
[
  {"op": "replace", "path": "/musicTrack/day/tracks", "value": []},     // Step 1: Clear
  {"op": "add", "path": "/musicTrack/day/tracks/0", "value": "/music/new1.ogg"},  // Step 2: Add
  {"op": "add", "path": "/musicTrack/day/tracks/1", "value": "/music/new2.ogg"}   // Step 3: Add
]
```

If ADD came before REPLACE, the new tracks would be removed too!

---

## Risk & Warning System

### User Confirmation Workflow

When user checks "Remove vanilla tracks":

```
User checks ☑️ Remove vanilla tracks?
        ↓
[CONFIRMATION DIALOG APPEARS]
"⚠️ Are you SURE? This will:
 • PERMANENTLY REMOVE vanilla tracks from this biome
 • Your custom music becomes the ONLY music that plays
 • Original biome music will NEVER play again
 • This affects ONLY the selected biome(s)
 
 If you disable/remove this mod later:
 • Affected biomes will have NO MUSIC (fallback fails)
 • Vanilla recovery requires Terraformer or save regeneration
 
 Only use if you understand the risks!
 
 Proceed? [Yes] [No]"
        ↓
If Yes: remove_vanilla_tracks = True, proceed with mod generation
If No:  Checkbox unchecked, mode skipped
```

### Recorded Warnings

In `starsound_gui.py`:
- User must explicitly click "Yes, I understand"
- Checkbox reverts to unchecked if user declines
- Warning tooltip visible on checkbox (hover for details)
- Session flag tracks if user confirmed this session

In logs:
```
[INFO] Remove vanilla tracks ENABLED for surface/forest
[WARN] User confirmed understanding permanent consequences
[INFO] Generated patches with REPLACE + direct index ADD operations
```

### Recovery Options

If player later disables/removes the mod:

**Option 1: Restore from Backup (if mod still in mods folder)**
- Re-enable the mod
- Affected biomes play your music again

**Option 2: Terraformer Tool (in-game)**
- Starbound mod that can restore vanilla music to biomes
- Works on existing saves

**Option 3: Regenerate World**
- Create new world to get vanilla music back
- Old world stays modified (permanent)

---

## Multi-Track Scenarios

### Scenario 1: Split Album (3 parts)

User has album: `Album_Part1.ogg`, `Album_Part2.ogg`, `Album_Part3.ogg`

**Without Remove Mode (problematic):**
```
Forest day tracks (with Add mode - 3 vanilla + 3 album):
├─ vanilla_1.ogg (16.7% play chance each = 50% for vanilla)
├─ vanilla_2.ogg
├─ vanilla_3.ogg
├─ Album_Part1.ogg (16.7% play chance = 50% for album) ← Parts shuffle with vanilla!
├─ Album_Part2.ogg                                         Wrong order, breaks listening
└─ Album_Part3.ogg
```
Problem: Your album parts randomly intersperse with vanilla tracks instead of playing sequentially.

**With Remove Mode (ideal):**
```
Forest day tracks (Remove + Add - only your 3 parts):
├─ Album_Part1.ogg (33.3% play chance each)
├─ Album_Part2.ogg
└─ Album_Part3.ogg
```
Better! By chance you might still hear them out of order (random selection), but at least no vanilla breaks the immersion.

### Scenario 2: Multiple Biome Coverage

User replaces multiple biomes with thematic music:

```
Config:
  selected_biomes: [
    ["surface", "arctic"],
    ["surface", "desert"],
    ["underground", "underground0a"]
  ]
  remove_vanilla_tracks: TRUE

Result:
  ✅ arctic.biome.patch → Only mountain ambient plays
  ✅ desert.biome.patch → Only desert synth plays
  ✅ underground0a.biome.patch → Only cave ambient plays
  ❌ All vanilla tracks permanently removed from these 3 biomes
```

### Scenario 3: Day/Night Split

User wants different audio for day/night:

```
Forest Day: Add orchestral (remove vanilla)
  → /musicTrack/day/tracks replaced, add orchestral_1, orchestral_2

Forest Night: Keep vanilla OR Add different music
  → /musicTrack/night/tracks replaced, add nocturnal_1, nocturnal_2
```

---

## Edge Cases & Fallback Behavior

### Edge Case 1: User cancels after enabling Remove

**Problem:** User enables "Remove vanilla", then cancels the biome dialog.

**Behavior:**
- `remove_vanilla_tracks` flag NOT saved
- Checkbox reverts to unchecked via signal handler
- Mod is NOT generated
- Vanilla tracks stay intact (no change)

```python
def _on_cancel_remove_vanilla(self):
    """Cancel the 'Remove vanilla tracks' setting"""
    self.remove_vanilla_tracks = False
    self.remove_vanilla_checkbox.setChecked(False)
    self._auto_save_mod_state('Cancelled Remove Vanilla Tracks')
```

### Edge Case 2: Biome has no vanilla tracks

**Problem:** Some biomes might have empty music arrays.

**Behavior:**
- REPLACE still executes (replaces empty with empty, harmless)
- ADD operations proceed normally
- Result: Biome goes from silence to your music ✅

```python
if patch_mode == 'add' and remove_vanilla_tracks:
    # Always add REPLACE ops, even if no vanilla tracks exist
    patch_ops.append({'op': 'replace', 'path': '/musicTrack/day/tracks', 'value': []})
    # Then ADD your tracks
```

### Edge Case 3: Very large track list (10+ songs)

**Problem:** Add 10 songs to a biome with Remove enabled.

**Behavior:**
- REPLACE clears vanilla (1 operation)
- ADD generates 10 operations with indices 0-9
- Patch file is slightly larger but still valid
- All 10 tracks available for random selection

```json
{"op": "replace", "path": "/musicTrack/day/tracks", "value": []},
{"op": "add", "path": "/musicTrack/day/tracks/0", "value": "/music/track_01.ogg"},
{"op": "add", "path": "/musicTrack/day/tracks/1", "value": "/music/track_02.ogg"},
...
{"op": "add", "path": "/musicTrack/day/tracks/9", "value": "/music/track_10.ogg"}
```

### Edge Case 4: User removes mod after Remove Mode used

**Problem:** Player removes the StarSound mod from Starbound/mods/ folder.

**Behavior:**
- Vanilla fallback in Starbound tries to load removed tracks
- Starbound has no fallback tracks (they were REPLACED, not overwritten)
- Affected biomes become SILENT ⚠️

```
Before mod: /music/vanilla_forest_1.ogg ← exists in assets
After Remove mode applied: /music/vanilla_forest_1.ogg ← REPLACED away
Remove mod: /music/vanilla_forest_1.ogg ← NO LONGER EXISTS
Result: No tracks found, biome is silence
```

**Fix:** Restore mod OR use Terraformer tool

---

## Troubleshooting

### Issue: "Remove vanilla tracks checkbox is grayed out"

**Problem:** Checkbox exists but can't be clicked.

**Causes:**
1. Currently in Replace mode (not Add mode) - Remove only works in Add
2. No biomes selected yet
3. Starbound installation not detected (vanilla tracks not available)

**Fix:**
- Switch to "Add to Game" mode
- Select at least one biome
- Verify Starbound location in settings

---

### Issue: "I checked Remove, but vanilla tracks still play"

**Problem:** Mod was generated but vanilla music still appears in-game.

**Likely cause:** `remove_vanilla_tracks` flag wasn't saved to config before generation.

**Verify:**
1. Open `mod_saves/{mod_name}.json`
2. Check for: `"remove_vanilla_tracks": true` (must be true, not false)
3. If false: Regenerate mod and ensure checkbox is checked before generating

**In game:**
1. Verify mod is enabled in Starbound's mod list
2. IMPORTANT: Mod affects newly generated worlds only (existing worlds baked with vanilla)
3. Create new world to test
4. Teleport to affected biome

---

### Issue: "My tracks don't play in the right order"

**Problem:** You added 3 songs expecting them in order, but they play randomly.

**Expected behavior:**
- Starbound randomizes ALL tracks regardless of how they're added
- Remove Mode with 3 tracks: ~33% each, random order
- To guarantee order: Use different biomes for each track, or split into regions

**NOT a bug:** This is Starbound's design (intentional randomization).

---

### Issue: "Starbound mod won't load after Remove mode"

**Problem:** Mod folder created but Starbound says mod failed to load.

**Check:**
1. **Patch syntax:** Validate JSON with `python -m json.tool mod.patch`
2. **File permissions:** Ensure mod folder is readable
3. **Starbound language:** Mods must use Starbound's asset paths correctly `/musicTrack/day/tracks`

**Debug:**
```bash
# Verify patch file is valid JSON
python -c "import json; json.load(open('Starbound/mods/StarSound/biomes/surface/forest.biome.patch'))"
# Should print nothing if valid
```

---

### Issue: "Only one of my music mods plays, not both"

**Problem:** You have Remove Mode and another music mod enabled, but only one's music plays.

**Cause:** **Mod conflict!** Both mods use REPLACE operations on the track arrays. Whichever loads last overwrites the earlier one.

**Who conflicts:**
- ✅ ADD-based mods — compatible, no issue
- ⚠️ REPLACE-based mods (some workshop mods) — **conflicts with Remove Mode**

**Solutions:**

1. **Best solution: Check the other mod's type**
   - Look at the mod's config/patch file
   - If it uses ADD operations: Should work together (look for other issue)
   - If it uses REPLACE: There's a natural conflict

2. **Manage mod load order:**
   - Put Remove Mode mod first in Starbound's load order
   - Put REPLACE-based mods after
   - Mod with HIGHEST priority wins (loads last)
   - Adjust in Starbound's mod management

3. **Workaround: Use Add Mode instead**
   - Switch from Remove Mode to Add Mode
   - ADD operations stack with both REPLACE and ADD mods
   - Trade-off: Vanilla tracks will mix with custom (50-60% vanilla playback)

4. **Nuclear option: Disable one mod**
   - Disable the conflicting mod
   - Use Remove Mode alone
   - Re-enable it when not playing

**This is not a bug:** It's how JSON patch operations work. REPLACE operations can't coexist with each other by design.

---

**Problem:** Removed vanilla tracks from a biome, now want them back.

**Solutions:**

1. **Immediate (mod still in mods folder):**
   - Go back to StarSound
   - SELECT SAME BIOME
   - UNCHECK "Remove vanilla tracks"
   - Regenerate with Add mode (normal append)
   - Result: Your tracks + vanilla restored

2. **Later (mod disabled):**
   - Use in-game Terraformer mod
   - OR regenerate that world

3. **Permanent recovery:**
   - Create new world (fresh vanilla)
   - Old world stays modified

---

## Summary

| Aspect | Details |
|--------|---------|
| **Mode Name** | Add to Game (with Remove Vanilla Checkbox) |
| **What it does** | Removes all vanilla tracks, replaces with your music |
| **Activation** | Add Mode + Check "Remove vanilla tracks" checkbox |
| **JSON Operations** | REPLACE array empty + ADD with direct indices |
| **User Confirmation** | Required (warning dialog) |
| **File Structure** | /music/ folder + patch file with REPLACE/ADD |
| **Mod compatibility** | Limited (overwrites entire biome) |
| **Vanilla preservation** | ❌ NO (permanent removal) |
| **Player experience** | 100% your music (random among your tracks) |
| **Use case** | Complete thematic replacements, multi-part tracks, biome exclusivity |
| **Reversibility** | Partially (need mod or tool, or new world) |
| **Risk Level** | ⚠️ HIGH (data loss if mod removed) |
