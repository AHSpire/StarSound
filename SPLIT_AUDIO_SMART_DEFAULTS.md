# Split Audio Smart Defaults - Summary

## What Changed

When you're working with **split audio tracks**, three aggressive audio processing filters are now **OFF by default**:

| Tool | Default (Regular Audio) | Default (Split Audio) | Why Changed? |
|------|------------------------|----------------------|------------|
| **Audio Trimming** | Depends on user | ❌ **OFF** | Can damage segment boundaries |
| **Silence Trimming** | Depends on user | ❌ **OFF** | Too aggressive on split edges (root cause of 0-second files) |
| **Fade In/Out** | Depends on user | ❌ **OFF** | Segments already have clean boundaries from split |
| **Normalization** | Depends on user | ✓ ON | Safe, improves volume consistency |
| **Compression** | Depends on user | ✓ ON | Safe audio enhancement |
| **Other Tools** | Depends on user | ✓ ON | Safe, user-controlled |

---

## How It Works

### When You Split Audio (e.g., 60-min file → 2 × 30-min segments):

1. **Open Per-Track Audio Config Dialog**
   - You'll see 4 segments in the list (e.g., 2 files × 2 parts each)
   - System detects "this is split audio" (has segment origins)

2. **Check Default Settings**
   - ❌ Audio Trimmer OFF
   - ❌ Silence Trimming OFF
   - ❌ Fade In/Out OFF
   - ✓ Normalization ON (or whatever default was set)
   - ✓ All other tools enabled/configured normally

3. **Why These 3 Are Off**
   - **Audio Trimming:** If you trim each segment, you might cut important content at boundaries
   - **Silence Trimming:** This removes quiet audio from start/stop edges - segments have natural quiet boundaries from splitting
   - **Fade In/Out:** Split produces clean audio boundaries; fades are unnecessary and add processing

4. **Configure Per Segment (If Desired)**
   - If you WANT to enable Silence Trimming for just 1 segment → Click the checkbox
   - Individual segments can be customized
   - Your changes are saved per-track

### When You Use Regular Audio (no splitting):

- All tools use the settings you configured in the main **Audio Processing** dialog
- No automatic disabling happens
- You have full control

---

## Example Workflow

**Scenario: You're converting your Elden Ring (60 min) + Oblivion (60 min) files**

### Step 1: Select both files
```
Files selected:
  • Elden Ring but it's lofi beats.mp3 (60 min)
  • Oblivion Ambience.mp3 (60 min)
```

### Step 2: Configure splitting (30-min segments)
- Creates 4 WAV files: 2 parts from each track

### Step 3: Open Per-Track Audio Config
- **Dialog detects:** "This is split audio with 4 segments from 2 originals"
- **Smart defaults applied:**
  ```
  Elden Ring part 1: trim OFF, silence_trim OFF, fade OFF
  Elden Ring part 2: trim OFF, silence_trim OFF, fade OFF
  Oblivion part 1:   trim OFF, silence_trim OFF, fade OFF
  Oblivion part 2:   trim OFF, silence_trim OFF, fade OFF
  ```

### Step 4: You can customize if needed
- Click any checkbox to enable a disabled tool
- Example: Enable Normalization on "Elden Ring part 1" only
- Click "Apply To All" to bulk-update all segments

### Step 5: Convert
- All segments convert **without aggressive filtering**
- No 0-second audio files from Silence Trimming
- Clean, consistent results

---

## Benefits

✅ **Prevents 0-second File Issues**  
No more conversions producing empty audio files from Silence Trimming  

✅ **Protects Clean Boundaries**  
Split operations create clean segment boundaries; filtering is unnecessary  

✅ **User Still Has Control**  
You can explicitly enable any filter if you want (e.g., if you really need Silence Trimming)  

✅ **Smart Detection**  
Disabling ONLY happens when system detects split audio (via segment_origins)  
Regular audio workflows are completely unchanged  

✅ **Selective Customization**  
Each segment can be configured individually if one needs special treatment  

---

## Test Results

✅ All 4 validation tests pass:
- Split audio defaults correctly disabled
- Regular audio unaffected
- Only 3 tools disabled (not others)
- No syntax errors

---

## Code Changes

**File Modified:** [per_track_audio_config_dialog.py](pygui/per_track_audio_config_dialog.py)

**Logic Added (lines 60-67):**
```python
# If this is split audio (segments detected), disable aggressive audio processing filters by default
if self.segment_origins:
    self.default_options['trim_enabled'] = False
    self.default_options['silence_trim_enabled'] = False
    self.default_options['fade_enabled'] = False
```

---

## Next Steps to Test

1. **Split your test audio files** (e.g., 60-minute track into 30-min segments)
2. **Verify defaults are OFF** when you open Per-Track Audio Config
3. **Convert** and confirm no 0-second files are produced
4. **Done!** Results should now be consistent

---

**Status:** ✅ **Ready for Testing**

This change makes split audio workflows safer by preventing aggressive filters from damaging segment boundaries, while still allowing you to enable any filter if you specifically need it.
