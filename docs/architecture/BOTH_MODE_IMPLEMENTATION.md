# Both Mode Implementation Guide

**A complete technical reference for how StarSound's "Both Mode" music patching works.**

⚠️ **Note:** **Remove Mode is the simplified, recommended alternative** most users should use instead (see [Remove Mode Guide](REMOVE_MODE_IMPLEMENTATION.md)). Both Mode is for advanced scenarios requiring fine-grained control. For most users, Remove Mode = same result, simpler workflow!

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Core Concept](#core-concept)
3. [Technical Architecture](#technical-architecture)
4. [The Three-Step Process](#the-three-step-process)
5. [Real-World Example](#real-world-example)
6. [JSON Patch Operations](#json-patch-operations)
7. [Edge Cases & Fallback Behavior](#edge-cases--fallback-behavior)
8. [Troubleshooting](#troubleshooting)

---

## Overview

**Both Mode** allows you to:
1. **Remove** all vanilla Starbound music from a biome
2. **Add** your custom music collection
3. All in a single operation — for complete biome ownership

This gives you maximum control over the biome's audio experience while maintaining compatibility with Starbound's patching system.

---

## Core Concept

### The Problem Both Mode Solves

**Add Mode** (layer music on top):
- Result: Vanilla tracks + your tracks = 15 total tracks
- Problem: Players hear vanilla music randomly mixed with yours

**Replace Mode** (swap out vanilla):
- Result: All vanilla removed, replaced with yours
- Problem: If someone disables/removes the mod, the biome reverts to vanilla (but you lose that metadata)

**Both Mode** (remove vanilla, then add yours):
- Result: Biome has ONLY your tracks
- Benefit: Complete control + clean separation of concerns via JSON Patch

### ⚠️ CRITICAL WARNING: Silent Biome Risk (Like Remove & Replace Modes)

**Both Mode uses REPLACE operations**, which means replaced track indices become empty if the mod is removed.

**If you later disable/remove the StarSound mod:**
- ❌ Affected biomes will have **NO MUSIC** (silent biomes!)
- 🔴 **Permanent data loss** — world data is baked, patches can't retroactively fix it
- ✅ **Solution:** Keep the mod installed indefinitely, OR
- ✅ **Better Solution:** Use **Add Mode instead** (vanilla fallback always available)

**Why this happens:** Both Mode first REPLACES the track array (like Replace Mode), then ADDS new tracks. If the mod is removed, only the first REPLACE operation is reverted, leaving empty slots.

**This silent biome issue affects all REPLACE-based modes** (Remove, Replace, Both). Only Add Mode avoids this by never removing vanilla tracks.

---

## Technical Architecture

Both Mode uses **RFC 6902 JSON Patch** operations with a key twist:

```
STEP 1: REPLACE PHASE (works exactly like Replace Mode)
1. READ vanilla track names (e.g., "epsilon-indi.ogg", "jupiter.ogg")
2. COPY user's custom tracks and RENAME them to match vanilla names
3. STORE renamed tracks in /music_add_and_replace/ directory
4. REPLACE each index with the renamed custom track path

STEP 2: ADD PHASE (distinct from regular Add Mode)
5. APPEND new custom tracks to the track list
6. COPY those new tracks to /music/ directory
7. ADD each track to the end using "add" operations
```

**Why this two-phase approach?**
- **Replace Phase:** Ensures all vanilla tracks are replaced with custom versions (like Replace Mode)
- **Add Phase:** Allows appending additional custom tracks beyond vanilla counts (like Add Mode)
- **Key Difference:** Uses `/music_add_and_replace/` for replaced tracks (not `/music_replacers/`)
- **Organization:** Keeps replaced and added tracks in separate directories for clarity
- **Result:** Complete control—vanilla removed AND additional tracks added

---

## The Two-Phase Process

Both Mode executes in two distinct phases:

### Phase 1: Replace (Works Exactly Like Replace Mode)

#### Step 1: Read Vanilla Track Names

StarSound reads the **vanilla biome data** to extract track names:

Example from `biomes/surface/forest.biome`:
```json
"musicTrack": {
  "day": {
    "tracks": [
      "/music/epsilon-indi.ogg",      ← Index 0
      "/music/hymn-to-the-stars.ogg", ← Index 1
      "/music/procyon.ogg"             ← Index 2
    ]
  },
  "night": {
    "tracks": [
      "/music/jupiter.ogg",            ← Index 0
      "/music/arctic-constellation1.ogg" ← Index 1
    ]
  }
}
```

#### Step 2: Copy and Rename Custom Tracks for Replacement

StarSound takes the **user's replacement tracks** and **renames them to match vanilla track names**:

```
User selects (via Replace UI):
  - Index 0 (day):   my_epic_song.ogg      → becomes epsilon-indi.ogg
  - Index 1 (day):   my_calm_song.ogg      → becomes hymn-to-the-stars.ogg
  - Index 2 (day):   my_atmospheric_song.ogg → becomes procyon.ogg
  - Index 0 (night): my_night_song.ogg     → becomes jupiter.ogg
```

These renamed files are stored in **`/music_add_and_replace/`** directory (NOT `/music_replacers/`).

#### Step 3: Generate Replace Operations

Create patch operations that **replace vanilla track references at each index**:

```json
{
  "op": "replace",
  "path": "/musicTrack/day/tracks/0",
  "value": "/music_add_and_replace/epsilon-indi.ogg"
},
{
  "op": "replace",
  "path": "/musicTrack/day/tracks/1",
  "value": "/music_add_and_replace/hymn-to-the-stars.ogg"
}
```

### Phase 2: Add (Distinct from Regular Add Mode)

#### Step 4: Append Additional Custom Tracks

StarSound appends any **additional custom tracks** beyond the vanilla count:

```
User selected (via Add UI):
  - day_extra_1.ogg
  - day_extra_2.ogg
  - night_extra_1.ogg
```

#### Step 5: Copy Additional Tracks

These new tracks are copied to **`/music/`** directory (NOT `/music_add_and_replace/`):

```
/mod_name/
  ├── music/
  │   ├── day_extra_1.ogg
  │   ├── day_extra_2.ogg
  │   └── night_extra_1.ogg
  └── music_add_and_replace/
      ├── epsilon-indi.ogg
      ├── hymn-to-the-stars.ogg
      └── jupiter.ogg
```

#### Step 6: Generate Add Operations

Append these additional tracks to the track list:

```json
{
  "op": "add",
  "path": "/musicTrack/day/tracks/-",
  "value": "/music/day_extra_1.ogg"
},
{
  "op": "add",
  "path": "/musicTrack/day/tracks/-",
  "value": "/music/day_extra_2.ogg"
}
```

---

## Real-World Example

### Before (Vanilla Forest)
```json
"musicTrack": {
  "day": {
    "tracks": [
      "/music/epsilon-indi.ogg",
      "/music/hymn-to-the-stars.ogg",
      "/music/procyon.ogg"
    ]
  },
  "night": {
    "tracks": [
      "/music/jupiter.ogg"
    ]
  }
}
```

### User Selections (Both Mode)

**Replace Selections:**
- Day, Track 0: `my_epic.ogg` (replaces `epsilon-indi.ogg`)
- Day, Track 1: `my_calm.ogg` (replaces `hymn-to-the-stars.ogg`)
- Night, Track 0: `my_night.ogg` (replaces `jupiter.ogg`)

**Add Selections:**
- Day: `my_epic_bonus.ogg`, `my_calm_bonus.ogg`
- Night: `my_night_bonus.ogg`

### Generated Mod Folder Structure

```
mod_name/
├── _metadata
├── biomes/surface/forest.biome.patch
├── music/                          ← Added tracks folder
│   ├── my_epic_bonus.ogg
│   ├── my_calm_bonus.ogg
│   └── my_night_bonus.ogg
└── music_add_and_replace/          ← Replaced tracks folder (Both Mode specific)
    ├── epsilon-indi.ogg            (renamed from my_epic.ogg)
    ├── hymn-to-the-stars.ogg       (renamed from my_calm.ogg)
    └── jupiter.ogg                 (renamed from my_night.ogg)
```

### Generated Patch (Both Mode)

```json
[
  {"op": "replace", "path": "/musicTrack/day/tracks/0", "value": "/music_add_and_replace/epsilon-indi.ogg"},
  {"op": "replace", "path": "/musicTrack/day/tracks/1", "value": "/music_add_and_replace/hymn-to-the-stars.ogg"},
  {"op": "replace", "path": "/musicTrack/night/tracks/0", "value": "/music_add_and_replace/jupiter.ogg"},
  {"op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/my_epic_bonus.ogg"},
  {"op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/my_calm_bonus.ogg"},
  {"op": "add", "path": "/musicTrack/night/tracks/-", "value": "/music/my_night_bonus.ogg"}
]
```

### After (Your Custom Forest with Bonus Tracks)

```json
"musicTrack": {
  "day": {
    "tracks": [
      "/music_add_and_replace/epsilon-indi.ogg",     ← Replaced
      "/music_add_and_replace/hymn-to-the-stars.ogg", ← Replaced
      "/music/procyon.ogg",                          ← Vanilla (unchanged)
      "/music/my_epic_bonus.ogg",                    ← Added
      "/music/my_calm_bonus.ogg"                     ← Added
    ]
  },
  "night": {
    "tracks": [
      "/music_add_and_replace/jupiter.ogg",          ← Replaced
      "/music/my_night_bonus.ogg"                    ← Added
    ]
  }
}
```

✅ **Result:** Forest plays your custom replaced music + extra bonus tracks!

---

## JSON Patch Operations

### Phase 1: Replace Operations (Index-Based)
```json
{
  "op": "replace",
  "path": "/musicTrack/day/tracks/0",
  "value": "/music_add_and_replace/epsilon-indi.ogg"
}
```

**What it does:**
- Finds the array at `/musicTrack/day/tracks`
- Replaces the element at index `0` (vanilla `epsilon-indi.ogg`)
- Points to the renamed custom track in `/music_add_and_replace/`
- Preserves vanilla track positioning (indices stay the same)

### Phase 2: Add Operations (Append-Based)
```json
{
  "op": "add",
  "path": "/musicTrack/day/tracks/-",
  "value": "/music/my_custom_track.ogg"
}
```

**What it does:**
- Appends a new track to the end of `/musicTrack/day/tracks`
- Uses the `-` syntax (Starbound-specific JSON Patch syntax)
- Points to new additional tracks in `/music/`
- Allows adding more tracks than vanilla provides

### Directory Organization: The Key Difference

| Mode | Replaced Tracks Folder | Added Tracks Folder | Comparison |
|------|------------------------|-------------------|----------|
| **Replace** | `/music_replacers/` | N/A | Only replaces vanilla |
| **Add** | N/A | `/music/` | Only adds new tracks |
| **Both** | `/music_add_and_replace/` | `/music/` | Both phases, separate folders |

**Why separate folders?**
- **`/music_add_and_replace/`:** Contains renamed vanilla-named tracks for replacement
- **`/music/`:** Contains additional tracks to be appended
- **Clarity:** Immediately shows which tracks are replacements vs. additions
- **Organization:** Prevents naming collisions between phases

---

## Edge Cases & Fallback Behavior

### What If the Biome Has No Vanilla Tracks?

Some biomes (e.g., `core/mooncorelayer.biome`) have empty track arrays:

```json
"musicTrack": {
  "day": { "tracks": [] },
  "night": { "tracks": [] }
}
```

**Behavior:** Both Mode still works perfectly!
- The "replace" operation replaces `[]` with `[]` (no-op, harmless)
- The "add" operations populate your tracks normally

### What If Player Disables the Mod?

Depending on when the patch was applied:

| Scenario | Result |
|----------|--------|
| **Existing world (baked)** | Loses all music for affected biomes — world needs regeneration (Terraformer) |
| **New world (not baked yet)** | Reverts to vanilla for new areas explored |

⚠️ **This is why Both Mode includes the Remove caveat** — players should keep the mod installed indefinitely.

### What If Player Has Other Music Mods?

**Conflicts occur if:**
- Multiple mods try to patch the same biome
- Later patches override earlier ones

**StarSound doesn't handle this automatically** (it's outside scope), but:
- Patches are applied in load order
- Last patch wins
- Future version: Compatibility Checker (planned for v1.0)

---

## Troubleshooting

### Issue: "Both Mode generated, but I only hear vanilla music"

**Possible causes:**
1. **Existing world** — Music is baked at world generation
   - **Solution:** Use Terraformer or create a new world

2. **Mod not enabled** — StarSound mod not active in Starbound
   - **Solution:** Check mods folder, ensure mod is enabled in launcher

3. **Patch syntax error** — JSON malformed
   - **Solution:** Check `latest_patch.txt` in mod folder for exact patch generated

### Issue: "My custom music only plays sometimes"

**Possible cause:**
- Starbound's music system randomizes tracks
- With 1-2 custom tracks, vanilla tracks may still play if they exist

**Solution:**
- Make sure you're using Both Mode (not Add Mode)
- Verify the patch applied correctly

### Issue: "Biome now has NO music"

**Possible cause:**
- Remove Mode was used and mod was later uninstalled/disabled
- World is pre-existing (music baked at generation)

**Solution:**
- Reinstall the StarSound mod
- OR use Terraformer to regenerate the biome (gives vanilla back)

---

## Best Practices

### ✅ DO:
- Use **Both Mode** when you want to replace vanilla AND add bonus tracks
- Use **Replace Mode** when you ONLY want to replace vanilla (no additions)
- Keep at least 2-3 custom tracks per time period for variety
- Test with new world first before applying to existing saves
- Keep mod installed indefinitely (or have backup restore plan)
- Understand the folder difference: `/music_add_and_replace/` (replaced) vs `/music/` (added)

### ❌ DON'T:
- Confuse **Both Mode** with **Replace Mode**—they use different folder structures
  - Both Mode: `/music_add_and_replace/` + `/music/`
  - Replace Mode: `/music_replacers/` only
- Use Both Mode if you plan to disable the mod later
- Provide only 1 track (Starbound will play it repeatedly)
- Mix Both Mode with Replace Mode on the same biome with overlapping selections
- Forget that added tracks are APPENDED (they come after replaced tracks in rotation)

---

## Summary

Both Mode provides a **two-phase approach** to music patching:

### Phase 1: Replace (Exactly like Replace Mode)
- Works exactly like **Replace Mode** operationally
- Replaces vanilla tracks at specific indices with custom versions
- Renamed custom tracks stored in **`/music_add_and_replace/`** folder
- Generates **replace operations** with index-based paths

### Phase 2: Add (Distinct from regular Add Mode)
- Appends additional custom tracks beyond vanilla count
- Additional tracks stored in **`/music/`** folder
- Generates **add operations** to append new tracks
- Allows you to have MORE tracks than vanilla

### Key Architectural Differences

| Aspect | Replace Mode | Add Mode | Both Mode |
|--------|--------------|----------|-----------|
| Folder Structure | `/music_replacers/` | `/music/` | `/music_add_and_replace/` + `/music/` |
| Replace Tracks | ✅ Replaces indices | ❌ No | ✅ Replaces indices (Phase 1) |
| Add Tracks | ❌ No | ✅ Appends | ✅ Appends (Phase 2) |
| Operations | Replace only | Add only | Replace + Add |
| Track Result | Vanilla removed, custom only | Vanilla + custom mixed | Vanilla removed, custom + bonus |

### Benefits of Both Mode
- ✅ Complete control over biome music (like Replace Mode)
- ✅ Ability to add extra tracks beyond vanilla count (like Add Mode)
- ✅ Clean separation of replacement and addition phases
- ✅ Deterministic, reproducible results
- ✅ RFC 6902 compliant patch operations

**Trade-off:**
- ⚠️ Mod must stay installed (world data is baked)
- ⚠️ More complex than Replace or Add alone

If you want simplicity, choose **Replace Mode** (replace only) or **Add Mode** (add only).
If you want full control, choose **Both Mode** (replace + add).
If you want TOTAL control, choose **Add Mode** with **REMOVE** enabled. Read warnings before attempting!

