# Track Splitting - End-to-End Testing Checklist

## 📋 Pre-Test Setup

- [ ] Launch StarSound GUI
- [ ] Location: `c:\Projects\StarSound\pygui\starsound_gui.py`
- [ ] Open your 30+ minute test track(s) in file explorer for quick access
- [ ] Have the debug log ready: Watch `starsoundlogs/` directory for new logs
- [ ] Have Step 1 (Mod Name) filled out with a test mod name like "SplitTest"

---

## 🧪 Test Flow: Detection Phase

### Test 1.1: File Selection Detection
- [ ] Click "Select Audio File(s)"
- [ ] Choose your 30+ minute track
- [ ] **EXPECTED**: Yellow ⚠️ badge appears next to filename with duration (e.g., "⚠️ 45.3 min")
- [ ] **EXPECTED**: Status says "⚠️ X file(s) need splitting"
- [ ] **VERIFY**: Check log for: `"Enhance Audio Validator to detect >30min files"`

### Test 1.2: Multiple Files (if testing)
- [ ] Select 2+ files: mix of short (<30 min) and long (>30 min)
- [ ] **EXPECTED**: Only long files get yellow badges
- [ ] Short files show normally
- [ ] Status shows correct count: "⚠️ 2 file(s) need splitting"

---

## 🎛️ Test Flow: Audio Configuration Phase

### Test 2.1: Audio Dialog Opens First
- [ ] Click "Convert to OGG"
- [ ] **EXPECTED**: Audio Processing Configuration dialog appears (NOT split dialog)
- [ ] **EXPECTED**: Title shows "🎛️ Audio Processing Configuration"
- [ ] **VERIFY**: Log shows: `"Showing audio processing configuration dialog"`

### Test 2.2: Audio Settings Interaction
- [ ] Click "🎵 Match Vanilla Profile" button
- [ ] **EXPECTED**: Tools enable/disable automatically
- [ ] **EXPECTED**: Confirmation dialog shows settings
- [ ] Click "✓ Apply"
- [ ] Dialog should close and return to main window

### Test 2.3: Custom Settings (Optional)
- [ ] Click "Configure Audio Processing" again
- [ ] Toggle individual tools on/off
- [ ] Adjust some settings (compression preset, EQ, etc.)
- [ ] Click Apply with different settings
- [ ] **VERIFY**: Settings are retained

---

## ✂️ Test Flow: Split Confirmation Phase

### Test 3.1: Split Confirmation Dialog
- [ ] After audio config → **EXPECTED**: Split confirmation dialog appears
- [ ] Dialog shows:
  - [ ] Filename correct
  - [ ] Duration correct (e.g., "45.3 minutes")
  - [ ] Message explains why (Starbound 30-min limit)
  - [ ] Two buttons: "✓ Split It" and "✗ Skip Splitting"
- [ ] **VERIFY**: Log shows dialog creation

### Test 3.2: Accept Split Flow
- [ ] Click "✓ Split It"
- [ ] **EXPECTED**: Dialog closes, no more dialogs appear
- [ ] **EXPECTED**: Splitting begins (status updates: "Splitting: [filename]...")
- [ ] **VERIFY**: Log shows: `"User accepted splitting for: [filename]"`

### Test 3.3: Deny + Reconsider Flow
- [ ] (Restart and select file again if needed)
- [ ] Click "Convert to OGG" → Audio dialog → Apply
- [ ] At split confirmation: Click "✗ Skip Splitting"
- [ ] **EXPECTED**: Denial warning dialog appears with red header
- [ ] Dialog shows: "⚠️ ⚠️ Are you sure?"
- [ ] Dialog offers buttons: "← Split It (Better Idea)" and "Continue Anyway"
- [ ] Click "← Split It (Better Idea)"
- [ ] **EXPECTED**: Returns to split confirmation dialog
- [ ] **EXPECTED**: Log shows: `"User reconsidered, showing split dialog again"`

### Test 3.4: Denial Confirmed Flow
- [ ] At denial dialog: Click "Continue Anyway"
- [ ] **EXPECTED**: Denial dialog closes
- [ ] **VERIFY**: Log shows: `"User chose to proceed without splitting"`
- [ ] File will be processed as-is (likely won't work in Starbound)

---

## 🔪 Test Flow: FFmpeg Splitting Phase

### Test 4.1: Splitting Begins
- [ ] After accepting split: **EXPECTED**: Status says "Splitting: [filename]..."
- [ ] **EXPECTED**: May take 30-90 seconds depending on file size
- [ ] **VERIFY**: Watch system resources (FFmpeg using CPU)
- [ ] **VERIFY**: Log shows: `"Starting FFmpeg split operation for: [filename]"`

### Test 4.2: Splitting Completes
- [ ] Status updates to: "✓ [filename] split into X segments"
- [ ] **EXPECTED**: Files created in same directory as source
- [ ] **EXPECTED**: Files named: `original_part1.ogg`, `original_part2.ogg`, etc.
- [ ] **VERIFY**: File browser shows new segment files
- [ ] **VERIFY**: Each segment ~25 minutes (or less for final segment)

### Test 4.3: Split Preview Dialog
- [ ] After splitting: **EXPECTED**: Preview dialog appears
- [ ] Dialog shows:
  - [ ] Original filename
  - [ ] Original duration (total)
  - [ ] "Split into: X segments"
  - [ ] Scrollable list of all segments with individual durations
  - [ ] Button: "✓ Proceed with Conversion"
- [ ] **VERIFY**: Log shows: `"Showing split preview dialog"`

### Test 4.4: Preview Confirmed
- [ ] Click "✓ Proceed with Conversion"
- [ ] **EXPECTED**: Preview dialog closes
- [ ] **EXPECTED**: Conversion phase begins
- [ ] **VERIFY**: Status shows progress or conversion start

---

## 🎵 Test Flow: Audio Conversion Phase

### Test 5.1: All Segments Processed
- [ ] Conversion starts (may show FFmpeg output)
- [ ] **EXPECTED**: Each segment is processed with audio settings
- [ ] **EXPECTED**: Files output to mod folder in `/music/` directory
- [ ] **EXPECTED**: Output filenames same as input (e.g., `original_part1.ogg`, `part2.ogg`)
- [ ] **VERIFY**: Log shows conversion for each file

### Test 5.2: Conversion Complete
- [ ] Status shows: "All files converted successfully! (X)"
- [ ] **EXPECTED**: X = total number of segments (e.g., 5 files if split into 5 parts)
- [ ] **VERIFY**: Mod folder contains all split files:
  ```
  staging/SplitTest/music/
    ├── original_part1.ogg
    ├── original_part2.ogg
    ├── original_part3.ogg
    ├── original_part4.ogg
    └── original_part5.ogg
  ```

---

## 📄 Test Flow: Patch File Verification

### Test 6.1: Patch File Created
- [ ] Look for generated patch file: `staging/SplitTest/client.config.patch`
- [ ] **EXPECTED**: File exists and is valid JSON
- [ ] Open in text editor

### Test 6.2: Patch Entries
- [ ] **EXPECTED**: Array of patch objects
- [ ] **EXPECTED**: One entry per segment
- [ ] Each entry should look like:
  ```json
  {
    "op": "add",
    "path": "/musicTrack/day/tracks/-",
    "value": "/music/original_part1.ogg"
  }
  ```
- [ ] **VERIFY**: 5 entries total (one per segment)
- [ ] **VERIFY**: Each "value" path unique (`part1`, `part2`, etc.)

---

## 🐛 Debugging If Things Go Wrong

### If Detection Fails
- [ ] Check: Is file actually >30 minutes?
- [ ] Verify: `utils/audio_utils.py` has `get_audio_duration()` function
- [ ] Check log: `"User selected X audio files"`
- [ ] Try: Select a different long file

### If Audio Dialog Won't Open
- [ ] Check: `audio_processing_dialog.py` exists
- [ ] Check: `AudioProcessingDialog` class imported in `starsound_gui.py`
- [ ] Check log: `"Showing audio processing configuration dialog"`
- [ ] Try: Close and reopen app

### If Split Dialog Won't Appear
- [ ] Verify: Audio dialog was completed and Apply clicked
- [ ] Check log: `"Using audio processing options from dialog configuration"`
- [ ] Verify: File is in `self.files_needing_split` dict
- [ ] Try: Re-select file and start over

### If Splitting Fails
- [ ] Check: FFmpeg is available (should be in utils/ffmpeg-8.0.1-full_build/)
- [ ] Check log: `"FFmpeg error: [message]"`
- [ ] Verify: Source file is readable and valid OGG
- [ ] Try: Run FFmpeg manually on test file to confirm it works

### If Preview Won't Show
- [ ] Check: Splitting actually completed (check file system)
- [ ] Check log: `"Successfully split into X segments"`
- [ ] Verify: `split_preview_dialog.py` exists
- [ ] Check: No exceptions in stderr

### If Conversion Fails
- [ ] Check: Audio settings were applied correctly
- [ ] Verify: All segments exist in staging directory
- [ ] Check log: `"User started audio conversion for: [file]"`
- [ ] Look for: `"ffmpeg error:"` in log

---

## ✅ Success Criteria

**Test PASSES if:**
1. ✅ Files >30 min show yellow badge on selection
2. ✅ Audio dialog appears first when converting
3. ✅ Split confirmation dialog appears after audio config
4. ✅ FFmpeg creates segment files
5. ✅ Preview dialog shows all segments
6. ✅ All segments converted to final format
7. ✅ Patch file contains all segment entries
8. ✅ Mod folder has all output files
9. ✅ No crashes or critical errors
10. ✅ Logs are clear and helpful

---

## 📊 Test Results Template

```
Date: 2/18/2026
Tester: Stephanie
Test File: [filename.ogg]
Duration: [X minutes]
Original Size: [X MB]

Results:
- Detection: ✅ PASS / ❌ FAIL
- Audio Dialog: ✅ PASS / ❌ FAIL
- Split Confirmation: ✅ PASS / ❌ FAIL
- FFmpeg Splitting: ✅ PASS / ❌ FAIL
- Preview Dialog: ✅ PASS / ❌ FAIL
- Audio Conversion: ✅ PASS / ❌ FAIL
- Patch File: ✅ PASS / ❌ FAIL

Segments Created: X
Final Mod Size: [X MB]

Issues Found:
- [If any]

Notes:
- [Any observations]
```

---

## 🚀 Quick Start

1. **Select long file** (30+ min)
2. **Click "Convert to OGG"**
3. **Follow all dialogs** (Audio → Split → Preview)
4. **Watch status updates**
5. **Check log and mod folder**
6. **Report results!**

---

Good luck! 🎵
