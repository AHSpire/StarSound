# StarSound Track Splitting Workflow
## Python Implementation Architecture

---

## 🎯 Overview

**Goal**: Allow users to add multi-hour audio files to Starbound by automatically splitting them into chunks under Starbound's 30-minute engine limit.

**Key Principle**: Minimal UI complexity. Single flow triggered at conversion time. Smart defaults with user tweaks available.

---

## 📋 Phase 1: Detection (Audio Validator Enhancement)

### When: File Selection
### What: Identify files needing splitting

**Location**: `utils/audio_utils.py` - Enhanced `check_audio_quality()` function

**New Function**: `get_audio_duration(file_path: Path) -> float`
```python
def get_audio_duration(file_path: Path) -> float:
    """
    Extract duration in minutes from audio file using ffprobe.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Duration in minutes (float), or 0 if error
    """
    # FFmpeg command:
    # ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 file.ogg
    # Parse result → convert seconds to minutes
```

**State Variable**:
```python
self.files_needing_split = {}  # {file_path: duration_minutes}
```

**UI Feedback**:
- After user selects files, scan each one
- Silently track which ones are >30 minutes
- Show badge in file list: `track.ogg (⚠️ 45 min - will split)`

---

## 📋 Phase 2: Conversion Trigger

### When: User clicks "Convert to Ogg"
### What: Loop through flagged files, show split dialog for each

**Location**: `starsound_gui.py` - `convert_audio()` method

**Pseudocode**:
```python
def convert_audio(self):
    # Loop through selected files
    for file in self.selected_files:
        if file in self.files_needing_split:
            duration = self.files_needing_split[file]
            
            # Show split confirmation dialog
            result = self.show_split_confirmation_dialog(file, duration)
            
            if result == "ACCEPT":
                # Proceed to Phase 3: Auto-Split
                self.process_file_splitting(file, duration)
            elif result == "DENY":
                # Show "Are you sure?" confirmation
                sure = self.show_denial_confirmation_dialog(file)
                if sure:
                    # Skip splitting, convert as-is (will likely fail in Starbound)
                    pass
                else:
                    # Go back, cancel entire conversion? Or just this file?
                    continue
        else:
            # File is ≤30 min, process normally
            self.convert_single_file(file)
```

---

## 📋 Phase 3: Auto-Split Algorithm

### When: User accepts split dialog
### What: FFmpeg splits file into optimal segments

**Location**: `utils/audio_utils.py` - New `split_audio_file()` function

**Algorithm Logic**:

| Duration Range | Strategy | Segment Size |
|---|---|---|
| 30-90 min | FFmpeg auto-split | 25 minutes each |
| > 90 min | User-configurable | 2-20 segments |

**For 30-90 min files**:
- Calculate: `segment_length = 25 minutes`
- Use FFmpeg `segment` filter to auto-split
- No user dialog needed (automatic 25-min chunks)

**For >90 min files**:
- Show config dialog asking: "How many segments?"
- Slider: 2-20 segments (or default to 4)
- Display calculated segment duration: "4 segments = ~22.5 min each"

**FFmpeg Command**:
```bash
ffmpeg -i input.ogg \
  -f segment \
  -segment_time 1500 \
  -c copy \
  -reset_timestamps 1 \
  output_%03d.ogg
```

**Function Signature**:
```python
def split_audio_file(
    file_path: Path,
    segment_length_minutes: int = 25,
    logger: Logger = None
) -> dict:
    """
    Split audio file into manageable segments using FFmpeg.
    
    Args:
        file_path: Path to audio file to split
        segment_length_minutes: Target segment duration (default 25)
        logger: Optional logger for debugging
        
    Returns:
        {
            'success': bool,
            'split_files': [Path, Path, ...],  # List of output files
            'message': str,
            'segment_count': int,
            'segment_durations': [float, float, ...]  # In minutes
        }
    """
```

**Output Files**: Saved in same directory as input
- `original_track_part1.ogg`
- `original_track_part2.ogg`
- `original_track_part3.ogg`
- etc.

---

## 📋 Phase 4: Confirmation & Review

### When: FFmpeg splitting completes
### What: Show user what was created, allow tweaks

**Location**: `starsound_gui.py` - `show_split_preview_dialog()`

**Dialog Content**:
- Original file: `soundtrack.ogg` (120 minutes)
- Split into: 5 segments
  - Part 1: 0-25 min (24:32)
  - Part 2: 25-50 min (24:58)
  - Part 3: 50-75 min (24:45)
  - Part 4: 75-100 min (24:12)
  - Part 5: 100-120 min (21:33)
- **[Proceed with Conversion]** | **[Cancel Splitting]**

**Optional**: If user wants to adjust split points:
- Allow manual tweaks (advanced feature, Phase 2+ only)

---

## 📋 Phase 5: Integration into Conversion

### When: Split files confirmed
### What: Add all split files to conversion pipeline

**Location**: `starsound_gui.py` - `convert_audio()` continuation

**What Happens**:
- All split segments enter normal audio processing
- Each segment treated as separate track
- All processing (compression, EQ, fade) applies to each segment
- Each segment becomes: `original_track_part1.ogg`, etc. in mod folder

**Track Pool Addition**:
- Each segment gets its own patch entry
- `"value": "/music/original_track_part1.ogg"`
- `"value": "/music/original_track_part2.ogg"`
- etc.

---

## 📋 Phase 6: Biome Assignment (Future)

### When: Split files added to mod
### What: Assign segments to specific biome day/night slots

**Status**: DEFERRED (Phase 2+ feature)

**Concept**:
- Replace vanilla biome tracks with silence/removes
- Ensure splits always play by occupying biome slots
- Example:
  - Forest Day → Remove all vanilla
  - Forest Day → Add 5 split segments
  - Starbound randomly picks from 5 segments

---

## 🎯 Minimal UI Approach

### Dialog Count: 2-4 modals maximum

1. **Split Confirmation** (Per file)
   - *"[Filename] is 47 minutes. Split it into 25-min chunks?"*
   - ✓ Accept | ✗ Deny

2. **Denial Warning** (If user denies)
   - *"Starbound won't play files >30 min. Split anyway?"*
   - ✓ Yes, convert as-is | ✗ No, split it

3. **Long-Track Config** (If >90 min, only if user enables)
   - *"This file is 180 minutes. How many segments?"*
   - Slider: **[2] ←→ [20]** (default 4)
   - Calculated duration shown

4. **Split Preview** (After FFmpeg completes)
   - Show what was created
   - Proceed or cancel

---

## 🛡️ Error Handling

### FFmpeg Split Fails:
- Log error: `"Split failed for [filename]: [error message]"`
- Show user: `"Could not split [filename]. Try reducing segment count."`
- Skip file or retry with different settings

### Disk Space:
- Check available space before splitting
- Warn: *"Need 2 GB free. You have 1.5 GB available."*

### Invalid Segment Ranges:
- Validate segment_time > 0
- Validate segment count: 2 ≤ count ≤ 20
- Reject invalid user inputs

---

## 📊 State Variables

```python
# In AudioProcessingDialog or similar
self.files_needing_split = {}           # {Path: duration_minutes}
self.split_decisions = {}               # {Path: "ACCEPT" | "DENY"}
self.pending_split_files = []           # Queue for splitting
self.split_results = {}                 # {Path: [split_file_list]}
```

---

## 🔄 Integration Points

### `browse_audio()` (File Selection)
```python
# After user selects files:
for file_path in selected_files:
    duration = get_audio_duration(file_path)
    if duration > 30:
        self.files_needing_split[file_path] = duration
        # Update UI badge
```

### `convert_audio()` (Conversion Trigger)
```python
# At start of conversion:
for file_path in self.selected_files:
    if file_path in self.files_needing_split:
        result = self.show_split_confirmation_dialog(file_path)
        if result == "ACCEPT":
            split_files = self.split_audio_file(file_path)
            self.pending_split_files.extend(split_files)
    else:
        self.pending_split_files.append(file_path)

# Then process all files (original + split segments)
for file_path in self.pending_split_files:
    self.process_single_file(file_path)
```

---

## 📝 Testing Checklist

- [ ] Detect files >30 min correctly
- [ ] Show split dialog on conversion click
- [ ] Accept → split with FFmpeg
- [ ] Deny → show "are you sure?" dialog
- [ ] Denial confirmed → skip splitting
- [ ] FFmpeg splits into correct number of segments
- [ ] Split files named correctly (part1, part2, etc.)
- [ ] Split preview shows correct durations
- [ ] All splits enter conversion pipeline
- [ ] All splits appear in mod folder
- [ ] All splits added to patch file
- [ ] Error handling for disk space
- [ ] Error handling for invalid inputs

---

## 🎬 Example Workflow: User adds 2-hour soundtrack

1. **User selects file**
   - File: `epic_soundtrack.ogg` (120 minutes)
   - UI shows: `epic_soundtrack.ogg (⚠️ 120 min - will split)`

2. **User clicks "Convert to Ogg"**
   - Dialog: *"epic_soundtrack.ogg is 120 minutes. Split into 25-min chunks?"*
   - User clicks: ✓ Accept

3. **System shows config (because >90 min)**
   - Dialog: *"Default: 5 segments (24 min each). Adjust?"*
   - User accepts default or changes to 4 segments

4. **FFmpeg splits**
   - `epic_soundtrack_part1.ogg` (24:00)
   - `epic_soundtrack_part2.ogg` (24:00)
   - `epic_soundtrack_part3.ogg` (24:00)
   - `epic_soundtrack_part4.ogg` (24:00)
   - `epic_soundtrack_part5.ogg` (24:00)

5. **Preview shown**
   - All 5 segments listed with durations
   - User clicks: **[Proceed with Conversion]**

6. **Audio processing applies to each segment**
   - Compression, EQ, normalization, fades

7. **Patch file created with 5 entries**
   ```json
   [
     { "op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/epic_soundtrack_part1.ogg" },
     { "op": "add", "path": "/musicTrack/day/tracks/-", "value": "/music/epic_soundtrack_part2.ogg" },
     ...
   ]
   ```

8. **Result**: User loads Starbound, hears different segments randomly throughout gameplay ✅

---

## 🚀 Phase Progression

1. **Phase 1 (Now)**: Detection + Confirmation Dialog
2. **Phase 2**: FFmpeg Auto-Split (25-min segments for 30-90 min)
3. **Phase 3**: Long-Track Config Dialog (custom segments for >90 min)
4. **Phase 4**: Split Preview + Tweaks
5. **Phase 5+**: Biome Assignment Logic

---

## 📞 Notes for Developer

- Keep dialogs **minimal and modal** (block main window for critical decisions)
- Use **background threading** for FFmpeg splitting (prevent UI freeze)
- **Log everything** to debug log for troubleshooting
- **Test edge cases**: 31-minute files, 90-minute files, 300-minute files
- **Validate user inputs** before passing to FFmpeg
- **Show progress** while FFmpeg is splitting (can take time on large files)

