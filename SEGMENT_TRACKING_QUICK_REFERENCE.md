# Segment Tracking Quick Reference
## For StarSound Developers

---

## What is it?

**Segment Tracking** enables per-segment audio processing for multi-hour files that are automatically split into smaller WAV chunks.

---

## The Core Idea

```
Long File (e.g., 3-hour podcast)
    ↓
Auto-Split into 8 segments (25 min each)
    ↓
Each segment tracked via self.segment_origins dict
    ↓
Per-track dialog groups segments by parent file
    ↓
User customizes audio for EACH segment individually
```

---

## Key Components

### 1. `self.segment_origins` Dictionary
**What:** Maps segments back to their original files  
**Type:** `Dict[segment_path: str, original_file_path: str]`  
**Created:** In `perform_file_splitting()` method  
**Passed to:** `PerTrackAudioConfigDialog` constructor

```python
# Example:
segment_origins = {
    "/path/podcast_part1.wav": "/path/podcast.mp3",
    "/path/podcast_part2.wav": "/path/podcast.mp3",
}
```

### 2. `parent_to_segments` Mapping
**What:** Inverse of segment_origins - groups segments by parent  
**Created:** In `PerTrackAudioConfigDialog.__init__()`  
**Used for:** Display grouping in track list

```python
# Example:
parent_to_segments = {
    "/path/podcast.mp3": ["/path/podcast_part1.wav", "/path/podcast_part2.wav"]
}
```

### 3. Per-Track Dialog Display
**Grouped View (when segments detected):**
```
📁 podcast.mp3 (original)
  ├─ podcast_part1.wav (part 1)
  ├─ podcast_part2.wav (part 2)
```

**Flat View (no segments):**
```
file1.mp3
file2.mp3
```

---

## Code Flow

### Step 1: File Splitting
```python
# In perform_file_splitting()
self.segment_origins = {}  # Initialize

for file_path, segments in split_results.items():
    for segment_path in segments:
        self.segment_origins[segment_path] = file_path  # Track origin
```

### Step 2: Pass to Dialog
```python
# In convert_audio() - STEP 2.5
segment_origins = getattr(self, 'segment_origins', {})

per_track_dialog = PerTrackAudioConfigDialog(
    files,
    audio_processing_options,
    self,
    segment_origins=segment_origins  # ← PASS HERE
)
```

### Step 3: Dialog Grouping
```python
# In PerTrackAudioConfigDialog.__init__()
if self.segment_origins:
    # Build parent_to_segments
    for segment_path, original_path in segment_origins.items():
        parent_to_segments[original_path].append(segment_path)
    
    # Display grouped view
```

### Step 4: Per-Segment Audio Processing
```python
# In convert_audio() - STEP 2.5
for file_path, track_settings in per_track_settings.items():
    audio_filter = build_audio_filter_chain(track_settings)
    per_track_filters[file_path] = audio_filter  # ← Each segment gets its own filter
```

---

## Common Tasks

### Accessing Segment Origins
```python
# From starsound_gui.py
if hasattr(self, 'segment_origins'):
    print(f"Total segments tracked: {len(self.segment_origins)}")
    for segment, original in self.segment_origins.items():
        print(f"{segment} came from {original}")
```

### Checking if Dialog Should Show Grouped View
```python
# In per_track_audio_config_dialog.py
if self.segment_origins:
    # Show grouped view with parent files and segment numbers
else:
    # Show flat view (original behavior)
```

### Building Custom Filter Per Segment
```python
# Each segment in per_track_settings is processed individually
for segment_file_path, settings_dict in per_track_settings.items():
    # settings_dict contains audio config for THIS segment
    audio_filter = build_audio_filter_chain(settings_dict)
    per_track_filters[segment_file_path] = audio_filter
    # ↑ This creates unique FFmpeg filter for each segment
```

---

## Default Behavior

### When segment_origins is Empty:
- Dialog shows flat file list (no grouping)
- No colored parent file headers
- Behaves exactly like original per-track dialog

### When segment_origins Has Entries:
- Dialog detects grouped audio
- Builds parent_to_segments mapping
- Shows grouped display with indented segment list
- Shows orange subtitle with segment count info

---

## Troubleshooting

### Problem: Dialog not showing grouped view
**Check:** Is `segment_origins` being passed to constructor?
```python
# Should have segment_origins parameter:
per_track_dialog = PerTrackAudioConfigDialog(
    files, default_options, self,
    segment_origins=segment_origins  # ← Required for grouping
)
```

### Problem: Segments not appearing in dialog
**Check:**
1. Did splitting complete successfully?
2. Is `perform_file_splitting()` populating `self.segment_origins`?
3. Are segments in the `files` list passed to dialog?

### Problem: Segment audio processing not applied
**Check:** Is each segment getting a unique filter in `per_track_filters`?
```python
# Each file_path should map to unique filter:
per_track_filters = {
    "segment1.wav": "filter_string_1",
    "segment2.wav": "filter_string_2",  # Different from segment1
}
```

---

## Logging Debug Info

### Check Segment Tracking Logs
```
grep "SEGMENT_TRACK" astarsoundlog_current.txt
```

Expected output:
```
[SEGMENT_TRACK] podcast_part1.wav origin: podcast.mp3
[SEGMENT_TRACK] podcast_part2.wav origin: podcast.mp3
[SEGMENT_TRACK] Segment origin map initialized with 2 segment(s)
```

### Check Per-Track Dialog Logs
```
grep "CONVERT_FLOW.*STEP 2.5" astarsoundlog_current.txt
```

Expected output:
```
[CONVERT_FLOW] STEP 2.5: Checking if per-track config needed
[CONVERT_FLOW] Multiple files (2) detected - showing per-track config
[CONVERT_FLOW] Segment grouping enabled: 2 segment(s)
[CONVERT_FLOW] Per-track settings received for 2 files
```

---

## Data Structures (Quick Ref)

### segment_origins
```python
{
    str(segment_path_1): str(original_file_path),
    str(segment_path_2): str(original_file_path),
    ...
}
```

### parent_to_segments
```python
{
    str(original_file_path_1): [
        str(segment_path_1),
        str(segment_path_2),
    ],
    ...
}
```

### per_track_settings (from dialog)
```python
{
    str(file_path): {
        'trim_enabled': bool,
        'trim_start_time': str,
        'trim_end_time': str,
        # ... other audio settings ...
    },
    ...
}
```

### per_track_filters (for conversion)
```python
{
    str(file_path_1): str(ffmpeg_filter_string_1),
    str(file_path_2): str(ffmpeg_filter_string_2),
    ...
}
```

---

## Integration Checklist

When modifying segment tracking, verify:

- [ ] `segment_origins` initialized in `perform_file_splitting()`
- [ ] Segments added to `segment_origins` during split loop
- [ ] `segment_origins` passed to `PerTrackAudioConfigDialog` constructor
- [ ] Dialog accepts `segment_origins` parameter
- [ ] `parent_to_segments` mapping built in dialog
- [ ] Grouped/flat view displays correctly based on `parent_to_segments`
- [ ] Per-track settings include all segments
- [ ] Per-segment filters generated individually
- [ ] Logging includes `[SEGMENT_TRACK]` and `[CONVERT_FLOW]` tags
- [ ] Tests pass: `python test_segment_tracking.py`

---

## Related Documentation

- **Full Architecture:** `SEGMENT_TRACKING_ARCHITECTURE.md`
- **Per-Track Dialog:** See `per_track_audio_config_dialog.py` docstring
- **Main Workflow:** See `convert_audio()` method in `starsound_gui.py`
- **Splitting Logic:** See `perform_file_splitting()` method in `starsound_gui.py`
- **Audio Utils:** See `split_audio_file()` in `utils/audio_utils.py`

---

**Last Updated:** Today  
**Status:** ✅ Complete
