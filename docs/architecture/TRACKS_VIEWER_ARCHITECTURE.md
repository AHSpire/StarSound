# Tracks Viewer Architecture Guide

**A complete technical reference for StarSound's "Tracks Viewer" — the shared, modular component for displaying selected tracks across all modes.**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Philosophy: Modular Helpers](#philosophy-modular-helpers)
3. [Architecture Diagram](#architecture-diagram)
4. [Core Components](#core-components)
5. [The Shared Display Methods](#the-shared-display-methods)
6. [Data Collection System](#data-collection-system)
7. [Search & Filtering](#search--filtering)
8. [Integration with Add/Replace/Both Modes](#integration-with-addreplaceboth-modes)
9. [State Management](#state-management)
10. [Edge Cases & Performance](#edge-cases--performance)

---

## Overview

**Tracks Viewer** is a separate dialog window that displays all selected tracks across the entire project. It's invoked by:

- **Add Mode:** Show selected biomes + day/night tracks to add
- **Replace Mode:** Show selected replacements (vanilla → custom mapping)
- **Both Mode:** Show BOTH replacement tracks AND tracks to add (combined view)

### Key Design Principle: Modularity

Instead of duplicating code for each mode's track display, Tracks Viewer uses **shared helper methods**:

```python
def _display_add_tracks_section(self):
    """Shared: Draw ADD tracks (Add mode + Both mode)"""
    
def _display_replace_tracks_section(self):
    """Shared: Draw REPLACE tracks (Replace mode + Both mode)"""
    
def refresh_display(self):
    """Master: Decide which sections to show based on patch_mode"""
    if patch_mode == 'add':
        self._display_add_tracks_section()
    elif patch_mode == 'replace':
        self._display_replace_tracks_section()
    elif patch_mode == 'both':
        self._display_replace_tracks_section()      # ← Reuse!
        self._display_add_tracks_section()          # ← Reuse!
```

This eliminates code duplication and ensures consistent behavior across all modes.

### What Tracks Viewer Shows

```
┌─ Your Selected Tracks ────────────────────────┐
│                                                │
│ 🔍 Search:  [________]        (45 / 45)   [✕] │
│                                                │
│ ┌─ Section 1: TRACKS TO REPLACE ────┐        │
│ │ 🔄 TRACKS TO REPLACE              │        │
│ │   📍 FOREST: Gentle Forest (2)    │        │
│ │     ✕ Remove                      │        │
│ │     🌅 Day (1)                    │        │
│ │       vanilla_1 → mysong.ogg [✕] │        │
│ │     🌙 Night (1)                  │        │
│ │       vanilla_2 → other.ogg [✕]  │        │
│ │                                    │        │
│ ├─ Section 2: NEW TRACKS WILL BE ADDED ────┐ │
│ │ ✨ NEW TRACKS WILL BE ADDED       │        │
│ │   📍 FOREST: Gentle Forest (3)    │        │
│ │     ✕ Remove                      │        │
│ │     🌅 Day (2)                    │        │
│ │       • song1.ogg [✕]             │        │
│ │       • song2.ogg [✕]             │        │
│ │     🌙 Night (1)                  │        │
│ │       • night_song.ogg [✕]        │        │
│ │                                    │        │
│ └─────────────────────────────────────────┘  │
│                                                │
│              [🔄 Refresh]  [Close]            │
└────────────────────────────────────────────────┘
```

---

## Philosophy: Modular Helpers

### Problem It Solves

Without Tracks Viewer, here's what would happen:

❌ **Without Modularity:** Each mode builds its own display
```python
# Add mode - builds display
def show_add_display():
    for biome in add_selections:
        # ... 50 lines of UI code ...
        
# Replace mode - duplicates all that code!
def show_replace_display():
    for biome in replace_selections:
        # ... 50 lines of SAME UI code ...
        
# Both mode - duplicates BOTH displays!
def show_both_display():
    # ... 50 lines for replace ...
    # ... 50 lines for add ...
    # = 100 lines of duplicate code!
```

✅ **With Modularity:** Shared helpers eliminate duplication
```python
# Shared method for displaying Add section
def _display_add_tracks_section(self):
    # Single implementation, reused by Add + Both modes
    
# Shared method for displaying Replace section
def _display_replace_tracks_section(self):
    # Single implementation, reused by Replace + Both modes
    
# Master refresh method routes to appropriate helpers
def refresh_display(self):
    if mode == 'add':
        self._display_add_tracks_section()
    elif mode == 'replace':
        self._display_replace_tracks_section()
    elif mode == 'both':
        self._display_replace_tracks_section()       # ← Reuse!
        self._display_add_tracks_section()           # ← Reuse!
```

### Benefits

| Benefit | Impact |
|---------|--------|
| **Single source of truth** | Bug fix once = fixed in all modes |
| **Consistent UI** | All modes look the same, behave the same |
| **Maintainability** | Adding features (e.g., bulk remove) works for all modes |
| **Code size** | 50 lines shared vs 150 lines duplicated = 100 lines saved |
| **Testing** | Test shared method once, works in Add + Replace + Both |

---

## Architecture Diagram

```
MainWindow (starsound_gui.py)
    │
    ├─ self.add_selections = {biome: {day: [...], night: [...]}, ...}
    ├─ self.replace_selections = {biome: {day: {idx: path}, night: {idx: path}}, ...}
    ├─ self.patch_mode = 'add' | 'replace' | 'both'
    └─ self.selected_biomes = [(category, biome), ...]
         │
         │ User clicks "View Selected Tracks"
         │
         ↓
TracksViewerWindow (QDialog)
    │
    ├─ __init__() → Initialize UI with search bar + scroll area
    │   │
    │   ├─ _collect_track_data() → Gather all tracks from MainWindow
    │   │
    │   └─ refresh_display() → Decide which display sections to render
    │       │
    │       ├─ IF patch_mode == 'both':
    │       │   ├─ _display_replace_tracks_section()  [SHARED]
    │       │   └─ _display_add_tracks_section()      [SHARED]
    │       │
    │       ├─ ELIF patch_mode == 'add':
    │       │   └─ _display_add_tracks_section()      [SHARED]
    │       │       (with optional vanilla removal section)
    │       │
    │       └─ ELIF patch_mode == 'replace':
    │           └─ _display_replace_tracks_section()  [SHARED]
    │
    ├─ Search System (Background Worker):
    │   ├─ _on_search_changed() → User types
    │   ├─ _perform_search() → Background worker filters
    │   └─ _display_filtered_results() → Show only matching tracks
    │
    └─ Action Handlers:
        ├─ _remove_track_and_refresh() → Delete single track
        ├─ _clear_biome_and_refresh() → Delete all tracks from biome
        ├─ _remove_biome_and_refresh() → Remove entire biome
        └─ _on_cancel_remove_vanilla() → Cancel vanilla removal
```

---

## Core Components

### 1. TracksViewerWindow Class

```python
# starsound_gui.py
class TracksViewerWindow(QDialog):
    """
    Separate window for viewing and managing selected tracks.
    
    SHARED by all modes:
    - Add mode: Shows Add display only
    - Replace mode: Shows Replace display only
    - Both mode: Shows both displays together
    """
    
    def __init__(self, main_window):
        # Initialize UI elements
        # Create search bar + scroll area
        
    def refresh_display(self):
        """Master method: Routes to appropriate display helpers"""
        # Analyzes patch_mode
        # Calls shared helper methods
        # Updates search index
        
    def _display_add_tracks_section(self):
        """SHARED: Display Add section (Add mode + Both mode)"""
        
    def _display_replace_tracks_section(self):
        """SHARED: Display Replace section (Replace mode + Both mode)"""
        
    def _collect_track_data(self):
        """Gather all tracks for search indexing"""
```

### 2. Data Storage (In MainWindow)

```python
# MainWindow stores all track information
self.add_selections = {
    (category, biome): {
        'day': ['/path/to/song1.ogg', '/path/to/song2.ogg'],
        'night': ['/path/to/night_song.ogg']
    },
    ...
}

self.replace_selections = {
    (category, biome): {
        'day': {0: '/path/to/replacement1.ogg', 2: '/path/to/replacement3.ogg'},
        'night': {1: '/path/to/night_replacement.ogg'}
    },
    ...
}

self.patch_mode = 'add' | 'replace' | 'both'
self.selected_biomes = [(category, biome), ...]
```

### 3. Vanilla Tracks Helper

```python
# From utils/patch_generator.py
def get_vanilla_tracks_for_biome(biome_category: str, biome_name: str) -> dict:
    """
    Return vanilla track names for a biome.
    
    Returns:
    {
        'dayTracks': ['vanilla_day_1.ogg', 'vanilla_day_2.ogg', ...],
        'nightTracks': ['vanilla_night_1.ogg', ...]
    }
    """
```

Tracks Viewer uses this to display the "vanilla → custom" mapping in Replace mode.

---

## The Shared Display Methods

### Method 1: `_display_add_tracks_section()`

**Used by:** Add mode + Both mode

**Purpose:** Show tracks that will be ADDED to the game

**Code Flow:**

```python
def _display_add_tracks_section(self):
    """
    Display the 'NEW TRACKS WILL BE ADDED' section.
    Called by both Add and Both modes.
    """
    
    # Get add selections from MainWindow
    add_selections = getattr(self.main_window, 'add_selections', {})
    
    # Add header
    add_header = QLabel('✨ NEW TRACKS WILL BE ADDED')
    add_header.setStyleSheet('color: #00d4ff; font-weight: bold; font-size: 13px;')
    self.content_layout.addWidget(add_header)
    
    # For each biome with selections
    for (category, biome_name) in sorted(add_selections.keys()):
        biome_data = add_selections[(category, biome_name)]
        day_tracks = biome_data.get('day', [])
        night_tracks = biome_data.get('night', [])
        biome_count = len(day_tracks) + len(night_tracks)
        
        # Biome header with Remove button
        biome_header = QHBoxLayout()
        biome_label = QLabel(f'📍 {category.upper()}: {biome_name}')
        biome_header.addWidget(biome_label)
        biome_header.addStretch()
        
        remove_btn = QPushButton('✕ Remove')
        remove_btn.clicked.connect(
            lambda biome=(category, biome_name): 
                self._remove_biome_and_refresh(biome)
        )
        biome_header.addWidget(remove_btn)
        self.content_layout.addLayout(biome_header)
        
        # Display day tracks
        if day_tracks:
            for track_path in day_tracks:
                track_name = Path(track_path).name
                track_widget = QHBoxLayout()
                track_label = QLabel(f'  🌅 {track_name}')
                track_widget.addWidget(track_label)
                track_widget.addStretch()
                
                remove_track_btn = QPushButton('✕')
                remove_track_btn.clicked.connect(
                    lambda path=track_path, b=(category, biome_name):
                        self._remove_track_and_refresh(b, 'day', path)
                )
                track_widget.addWidget(remove_track_btn)
                self.content_layout.addLayout(track_widget)
        
        # Display night tracks (same pattern)
        # ...
```

**Output:** Structured display with removable tracks per biome

### Method 2: `_display_replace_tracks_section()`

**Used by:** Replace mode + Both mode

**Purpose:** Show "vanilla → custom" track replacements

**Code Flow:**

```python
def _display_replace_tracks_section(self):
    """
    Display the 'TRACKS TO REPLACE' section.
    Called by both Replace and Both modes.
    """
    
    # Get replace selections from MainWindow
    replace_selections = getattr(self.main_window, 'replace_selections', {})
    
    # Add header
    replace_header = QLabel('🔄 TRACKS TO REPLACE')
    replace_header.setStyleSheet('color: #ff9999; font-weight: bold; font-size: 13px;')
    self.content_layout.addWidget(replace_header)
    
    # For each biome with replacements
    for (category, biome_name) in sorted(replace_selections.keys()):
        biome_data = replace_selections[(category, biome_name)]
        day_replace = biome_data.get('day', {})  # {index: path, ...}
        night_replace = biome_data.get('night', {})
        
        replace_count = len(day_replace) + len(night_replace)
        
        # Get vanilla tracks for this biome (for display only)
        vanilla_data = get_vanilla_tracks_for_biome(category, biome_name)
        day_vanilla = vanilla_data.get('dayTracks', [])
        night_vanilla = vanilla_data.get('nightTracks', [])
        
        # Biome header
        biome_header = QHBoxLayout()
        biome_label = QLabel(f'📍 {category.upper()}: {biome_name}')
        biome_header.addWidget(biome_label)
        biome_header.addStretch()
        
        remove_btn = QPushButton('✕ Remove')
        remove_btn.clicked.connect(
            lambda biome=(category, biome_name):
                self._remove_replace_biome_and_refresh(biome)
        )
        biome_header.addWidget(remove_btn)
        self.content_layout.addLayout(biome_header)
        
        # Display day replacements
        if day_replace:
            day_title = QLabel('  🌅 Day')
            self.content_layout.addWidget(day_title)
            
            for idx, track_path in day_replace.items():
                vanilla_name = Path(day_vanilla[idx]).name if idx < len(day_vanilla) else '?'
                custom_name = Path(track_path).name
                
                mapping = QHBoxLayout()
                mapping_label = QLabel(f'    {vanilla_name} → {custom_name}')
                mapping.addWidget(mapping_label)
                mapping.addStretch()
                
                remove_track_btn = QPushButton('✕')
                remove_track_btn.clicked.connect(
                    lambda cat=category, b=biome_name, index=idx:
                        self._remove_replace_track_and_refresh((cat, b), 'day', index)
                )
                mapping.addWidget(remove_track_btn)
                self.content_layout.addLayout(mapping)
        
        # Display night replacements (same pattern)
        # ...
```

**Output:** Vanilla → Custom mappings with removal buttons

---

## Data Collection System

### `_collect_track_data()` Method

Prepares all track data for search filtering:

```python
def _collect_track_data(self):
    """Collect all track data for search filtering"""
    self.all_track_data = []
    self.search_index = []
    
    patch_mode = getattr(self.main_window, 'patch_mode', 'add')
    replace_selections = getattr(self.main_window, 'replace_selections', {})
    add_selections = getattr(self.main_window, 'add_selections', {})
    
    # Collect Replace tracks (if in Both mode)
    for biome in sorted(replace_selections.keys()):
        data = replace_selections[biome]
        biome_data = {
            'biome': biome,
            'day': data.get('day', {}),
            'night': data.get('night', {}),
            'is_replace': True
        }
        self.all_track_data.append(biome_data)
        
        # Add to search index (lightweight, just for searching)
        category, biome_name = biome
        self.search_index.append({
            'biome': biome,
            'biome_text': f'{category} {biome_name}',
            'tracks': [
                # List of all replacements for this biome
                (f'{biome_name} replace {Path(path).name}', path, 'day', True)
                for path in data.get('day', {}).values()
            ] + [
                (f'{biome_name} replace {Path(path).name}', path, 'night', True)
                for path in data.get('night', {}).values()
            ]
        })
    
    # Collect Add tracks (always)
    for biome in sorted(add_selections.keys()):
        data = add_selections[biome]
        biome_data = {
            'biome': biome,
            'day': data.get('day', []),
            'night': data.get('night', []),
            'is_replace': False
        }
        self.all_track_data.append(biome_data)
        
        # Add to search index
        category, biome_name = biome
        self.search_index.append({
            'biome': biome,
            'biome_text': f'{category} {biome_name}',
            'tracks': [
                (f'{biome_name} {Path(path).name}', path, 'day', False)
                for path in data.get('day', [])
            ] + [
                (f'{biome_name} {Path(path).name}', path, 'night', False)
                for path in data.get('night', [])
            ]
        })
```

### Search Index Structure

```python
# After _collect_track_data(), search_index looks like:
self.search_index = [
    {
        'biome': ('forest', 'gentle_forest'),
        'biome_text': 'forest gentle_forest',
        'tracks': [
            ('gentle_forest mysong.ogg', '/path/to/mysong.ogg', 'day', False),
            ('gentle_forest night_track.ogg', '/path/to/night_track.ogg', 'night', False),
        ]
    },
    # ... more biomes ...
]
```

This lightweight index makes searching very fast.

---

## Search & Filtering

### Search Architecture

Tracks Viewer uses a **background worker thread** to avoid freezing the UI while searching large track lists:

```
User Types        Debounce           Background          Display
                  Timer (800ms)       Worker Search       Results
                     │                   │                  │
   [ s  s o n  song ]─→─ (wait timeout) ─→─ [Filter]      │
                                           [Find matches]  │
                                                    └──────→ Show filtered
```

### Search Methods

```python
def _on_search_changed(self, search_text):
    """User types in search box (with debouncing)"""
    # Debounce timer kills old search, starts new one after 800ms
    
def _perform_search(self):
    """Actually perform the search (in background thread)"""
    # Filter search_index for matches
    # Return filtered results
    
def _display_filtered_results(self, filtered_data, total_count):
    """Display search results (called from worker thread)"""
    # Clear old widgets
    # Rebuild display with matching tracks only
    # Update count label
```

### Search Example

**User types:** "forest"

**Search matches:**
```
✓ (gentle_forest, daily_ambient.ogg)     - biome matches
✓ (gentle_forest, night_track.ogg)       - biome matches
✓ (bamboo_forest, remix.ogg)             - biome matches
✗ (desert, song.ogg)                     - no match
```

**Display shows:** Only forest-related tracks (3 results)

---

## Integration with Add/Replace/Both Modes

### Add Mode Flow

```
User selects "View Selected Tracks"
    ↓
TracksViewerWindow.__init__() called
    ↓
refresh_display() called
    ├─ Gets patch_mode = 'add' from MainWindow
    └─ _display_add_tracks_section()        [SHARED]
        ├─ Shows all biomes in add_selections
        ├─ Shows day/night tracks per biome
        └─ Allows per-track removal
```

### Replace Mode Flow

```
User selects "View Selected Tracks"
    ↓
TracksViewerWindow.__init__() called
    ↓
refresh_display() called
    ├─ Gets patch_mode = 'replace' from MainWindow
    └─ _display_replace_tracks_section()    [SHARED]
        ├─ Shows all biomes in replace_selections
        ├─ Shows "vanilla → custom" mappings
        └─ Allows per-replacement removal
```

### Both Mode Flow

```
User selects "View Selected Tracks"
    ↓
TracksViewerWindow.__init__() called
    ↓
refresh_display() called
    ├─ Gets patch_mode = 'both' from MainWindow
    ├─ _display_replace_tracks_section()    [SHARED]  ← Show replacements
    └─ _display_add_tracks_section()        [SHARED]  ← Then show adds
        └─ Both sections visible and independent
```

---

## State Management

### Removing Tracks (Action Cascade)

```
User clicks "Remove" button on a track
    ↓
_remove_track_and_refresh(biome, track_type, track_path)
    ├─ Delete from MainWindow.add_selections
    ├─ Call MainWindow._auto_save_mod_state()  (save to disk)
    ├─ Call MainWindow.update_patch_btn_state()
    └─ Call self.refresh_display()
        ├─ Re-collect track data
        ├─ Re-render display
        └─ Update search index
```

### Removing Biomes

```
User clicks "Remove" button on an entire biome
    ↓
_remove_biome_and_refresh(biome)
    ├─ Delete from MainWindow.add_selections
    ├─ Delete from MainWindow.selected_biomes (if in Add mode)
    ├─ Call MainWindow._auto_save_mod_state()
    ├─ Call MainWindow.update_patch_btn_state()
    └─ Call self.refresh_display()
        └─ Full re-render with updated state
```

### Consistency Guarantees

- **Always refresh after modification:** Every action calls `refresh_display()`
- **Always auto-save:** Every removal triggers `_auto_save_mod_state()`
- **Always update buttons:** ModPane buttons update availability after each action
- **Always sync MainWindow:** Changes immediately reflect in main window state

---

## Edge Cases & Performance

### Edge Case 1: Both Mode with Large Track Lists

**Problem:** Both sections visible simultaneously (many tracks)
- Replace section + Add section = lots of UI elements

**Solution:** Lazy rendering + search filtering
- Full list rendered once
- Search filters down to matching tracks only
- Background worker prevents UI freeze

### Edge Case 2: Clearing Search While Results Display

**Problem:** User types "forest", clears search, should show all again instantly

**Behavior:**
```python
if not self.current_search:  # User cleared search
    self.search_debounce_timer.stop()  # Cancel pending search
    self.current_search_id += 1  # Invalidate old results
    
    # Kill any running search worker to prevent stale results
    if self.search_worker and self.search_worker.isRunning():
        self.search_worker.requestInterruption()
    
    # Process events and refresh display (deferred to avoid flicker)
    QCoreApplication.processEvents()
    QTimer.singleShot(400, self.refresh_display)
```

### Edge Case 3: Removing Track During Search

**Problem:** User filters to "forest", removes a track—counter should update

**Behavior:**
```python
def _remove_track_and_refresh(self, biome, track_type, track_path):
    # Delete from MainWindow
    # ... (as above) ...
    
    # If search is active, refresh within search results
    if self.current_search:
        # Re-perform search to update filtered display
        self._perform_search()
    else:
        # Full refresh
        self.refresh_display()
```

### Performance Strategies

| Strategy | Benefit |
|----------|---------|
| **Background search worker** | 500+ tracks searchable without UI freeze |
| **Debounce timer (800ms)** | User stops typing → search runs, not per-keystroke |
| **Lightweight search index** | Fast pattern matching, minimal memory |
| **Deferred refresh** | UI processed before rebuilding, prevents visual glitches |
| **Search invalidation ID** | Prevents stale results from overwriting current state |

### Memory Efficiency

```python
# Lightweight search index (reused, not duplicated)
search_index = [
    {
        'biome_text': 'forest gentle_forest',
        'tracks': [('name1', 'name2', ...), ...]
    }
]

# NOT:
# full_ui_widgets = [QLabel(...), QPushButton(...), ...]  ← Heavy!
```

Only full UI widgets created when displaying (not in search index).

---

## Summary

| Aspect | Details |
|--------|---------|
| **Purpose** | Unified track display for Add/Replace/Both modes |
| **Architecture** | Modular shared display helpers |
| **Main method** | `refresh_display()` → routes to appropriate sections |
| **Shared helpers** | `_display_add_tracks_section()`, `_display_replace_tracks_section()` |
| **Data source** | MainWindow.add_selections + MainWindow.replace_selections |
| **Search** | Background worker + debounce + lightweight index |
| **Actions** | Remove track/biome with auto-save + state sync |
| **Performance** | Supports 500+ tracks, non-blocking search |
| **Code reuse** | Single implementation works for 3 modes = -100 lines duplicate code |

---

## Developer Notes for Future Enhancements

### Adding New Display Section

1. Create new shared method: `_display_xyz_tracks_section()`
2. Call it from `refresh_display()` based on condition
3. Make it reuse existing action handlers (`_remove_track_and_refresh`, etc.)
4. Add to search index in `_collect_track_data()`

Example:
```python
# New section for another feature
def _display_custom_tracks_section(self):
    """Display custom tracks"""
    # ... reuses same pattern as Add/Replace sections ...
    
def refresh_display(self):
    # ... existing code ...
    if has_new_feature:
        self._display_custom_tracks_section()
```

### Adding New Action

1. Create handler: `_my_action_and_refresh()`
2. Follow pattern: modify state → auto-save → update buttons → refresh
3. Connect to UI button

Example:
```python
def _duplicate_track_and_refresh(self, biome, track_type, track_path):
    """Duplicate a track"""
    # Make a copy in MainWindow
    # Call MainWindow._auto_save_mod_state()
    # Call MainWindow.update_patch_btn_state()
    # Call self.refresh_display()
```

---

## Testing Considerations

**Unit Test Tracks Viewer Methods:**
```python
def test_display_add_section_empty():
    """Test Add section with no tracks"""
    
def test_display_add_section_multiple_biomes():
    """Test Add section with 3+ biomes"""
    
def test_search_forest_returns_only_forest_tracks():
    """Test search functionality"""
    
def test_remove_track_updates_count():
    """Test removal and refresh"""
    
def test_both_mode_shows_both_sections():
    """Test Both mode displays both Replace + Add"""
```

**Integration Test with Modes:**
```python
def test_add_mode_opens_viewer():
    """Verify Add mode can open Tracks Viewer"""
    
def test_replace_mode_shows_mappings():
    """Verify Replace mode shows vanilla → custom"""
    
def test_both_mode_shows_both():
    """Verify Both mode shows both sections"""
```
