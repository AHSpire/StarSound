# Per-Track Audio Processing Configuration ✨

## What's New?

Previously, when you selected **multiple audio tracks** at once in **Step 3**, all tracks would receive the **same audio processing settings**. Now you can customize audio processing **for each individual track**!

---

## The New Workflow

### Before (Single Settings for All)
```
Step 3: Select Tracks → Step 4: Convert
├─ Select: "track1.mp3", "track2.mp3", "track3.wav"
├─ Main Audio Processing Dialog (1 config for all 3 files)
└─ ALL 3 tracks get processed identically ❌
```

### After (Per-Track Customization)
```
Step 3: Select Tracks → Step 4: Convert
├─ Select: "track1.mp3", "track2.mp3", "track3.wav"
├─ Main Audio Processing Dialog (default settings)
├─ NEW! Per-Track Audio Config Dialog
│   ├─ 📋 Left panel: List of selected tracks
│   ├─ 🎛️ Right panel: Audio processing controls
│   ├─ Switch between tracks to customize each one
│   └─ Apply one track's settings to all others (bulk option)
└─ EACH track processed with its own settings ✅
```

---

## How to Use Per-Track Configuration

### Step-by-Step

1. **Select multiple audio files** in Step 3 (e.g., 5 tracks)

2. **Click "Step 4: Convert to OGG"**

3. **Main Audio Processing Dialog appears** (set defaults here)

4. **Per-Track Audio Config Dialog appears** with:
   - 📋 **Left Panel:** List of all your selected tracks
   - 🎛️ **Right Panel:** All audio processing controls
   - **Bottom Buttons:** "Apply This To All" & "Reset To Default"

5. **For each track you want to customize:**
   - Click on a track name in the left panel
   - Adjust audio settings on the right (compression, EQ, etc.)
   - Settings are saved when you switch to another track

6. **To apply settings to multiple tracks:**
   - Configure Track 1 the way you want
   - Click "📋 Apply This To All"
   - All 5 tracks now have Track 1's settings

7. **Click "✓ Apply & Continue"** to proceed with conversion

---

## Example Use Cases

### Use Case 1: Mix of Different Audio Formats
```
Selected Tracks:
├─ vocal_modern.mp3 → Heavy compression, bright EQ
├─ ambient_synth.wav → Gentle compression, warm EQ (bass-heavy)
└─ orchestral.flac → No compression, dark EQ (smooth)
```
**Action:** Customize each track individually in the per-track dialog

### Use Case 2: Similar Tracks with One Exception
```
Selected Tracks:
├─ boss_battle_1.wav ← Want same settings as others
├─ boss_battle_2.wav ← Want same settings as others
├─ boss_battle_3.wav ← Want different (less compression)
└─ menu_music.ogg ← Already different
```
**Action:**
1. Configure boss_battle_1 settings
2. Click "📋 Apply This To All"
3. Now customize boss_battle_3 separately
4. menu_music.ogg keeps whatever you set earlier

### Use Case 3: One-Size-Fits-All
```
Selected Tracks: 10 music files
```
**Action:**
1. Configure main audio processing dialog
2. Per-track dialog appears
3. Everything already has default settings
4. Click "✓ Apply & Continue" without changes
5. All 10 get the same processing (same as before)

---

## Features Explained

### 📋 Track List (Left Panel)
- Shows all selected tracks by filename
- Click a track to view/edit its settings
- Tracks stay selected as you scroll through
- Current track is highlighted in blue

### 🎛️ Audio Processing Controls (Right Panel)
- 10 professional audio tools:
  1. Audio Trimmer
  2. Silence Trimming
  3. Sonic Scrubber
  4. Compression
  5. Soft Clipping
  6. 3-Band EQ
  7. Normalization
  8. Fade In/Out
  9. De-Esser
  10. Stereo to Mono

- Enable/disable each tool with checkboxes ☑️
- Configure parameters for each enabled tool

### 📋 "Apply This To All" Button
- **What it does:** Takes current track's settings, copies them to all other selected tracks
- **When to use:** You want most tracks to have identical processing
- **Confirmation:** Pop-up message shows success

### 🔄 "Reset To Default" Button
- **What it does:** Restores current track to the default settings from the main audio processing dialog
- **When to use:** You made changes but want to undo them
- **Note:** Only affects the current track, not others

---

## Important Notes

⚠️ **Single Track Selection**
- If you only select 1 audio file
- Per-track dialog is **skipped** (only 1 track = same as before)
- Faster workflow for single-file conversions

✅ **Default Settings**
- Main Audio Processing Dialog sets the **default** for all tracks
- Per-track dialog lets you **override** per track
- You can use "Apply This To All" to sync to any track's custom settings

📝 **Settings Are Per-File Path**
- If you select the same file twice, each instance gets its own settings
- Settings don't persist between runs (reset when you start a new conversion)

🔗 **Settings & Conversion**
- Each track's settings are built into its own **audio filter chain**
- During conversion, each file uses its corresponding filter
- Ensures consistency and flexibility

---

## Troubleshooting

### Q: My track selection disappears when I switch tracks
**A:** The selection highlights show which track you're currently editing. It's working as intended.

### Q: Can I edit multiple tracks at once?
**A:** No, you configure one track at a time. But use "Apply This To All" to copy settings across tracks quickly.

### Q: What if I cancel the per-track dialog?
**A:** Conversion is cancelled. You can try again and select tracks.

### Q: Do per-track settings save between sessions?
**A:** No. Settings are created fresh each time you convert. This prevents confusion from old settings.

### Q: Can I see what settings each track will get?
**A:** Yes! Click on each track in the left panel to see its settings on the right.

---

## Feature Architecture

### How It Works Behind the Scenes

1. **User selects files in Step 3** → Files list: `[file1, file2, file3]`

2. **Click Convert → Main Audio Dialog** → User sets defaults

3. **Check if multiple files:**
   - ✅ Multiple → Show per-track dialog
   - ❌ Single → Skip directly to conversion

4. **Per-track dialog initializes:**
   - Load default settings for each file
   - Build UI with track list + controls
   - Wait for user input (modal dialog)

5. **User edits per-track settings:**
   - Click track → Load its settings into controls
   - Adjust controls → Settings update for that track
   - Switch track → Current track's settings saved, new track loaded

6. **User clicks "Apply & Continue":**
   - Save current track's settings
   - Return per-track settings dict to main window

7. **Conversion process:**
   - For each file:
     - Get its per-track settings
     - Build its unique audio filter chain
     - Convert with that filter

---

## Configuration Files & Data

### Where Settings Are Stored (During Conversion)
```
Main Window
├─ self.per_track_filters = {
│   "C:/path/track1.mp3": "...ffmpeg filter chain 1...",
│   "C:/path/track2.wav": "...ffmpeg filter chain 2...",
│   "C:/path/track3.ogg": "...ffmpeg filter chain 3...",
│  }
```

### Settings Dictionary Structure
```python
per_track_settings = {
    "track1.mp3": {
        "trim_enabled": True,
        "trim_start_time": "0hr0m0s",
        "trim_end_time": "0hr30m0s",
        "compression_enabled": True,
        "compression_preset": "Moderate (balanced)",
        "eq_enabled": False,
        # ... more settings
    },
    "track2.wav": {
        # Different settings for track 2
    }
}
```

---

## What's NOT Changed

✅ **These still work the same way:**
- Step 1: Enter mod name
- Step 2: Select patch mode (add/replace/both)
- Step 3: Select audio files
- Step 4: Audio file validation
- Step 5: Split long files (>30 min)
- Step 6: Select biomes/replacement tracks
- Step 7: Generate mod

❌ **Only ONE thing changed:**
- Between Step 1 (Main Audio Dialog) and Step 2 (Splitting/Conversion)
- Added: Optional Per-Track customization dialog

---

## Summary

This feature gives you **maximum flexibility** for multi-track projects:

| Scenario | Workflow | Time |
|----------|----------|------|
| 1 track | Main dialog → Convert | ⚡ Fast |
| 5 identical tracks | Main dialog → Skip per-track → Convert | ⚡ Fast |
| 5 similar tracks, 1 different | Main dialog → Per-track (bulk + override 1) → Convert | 🎯 Balanced |
| 5 completely different tracks | Main dialog → Per-track (customize each) → Convert | 🎨 Flexible |

All workflows are supported! 🎵✨

