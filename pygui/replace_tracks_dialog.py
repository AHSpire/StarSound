"""
[SYSTEM] ReplaceTracksDialog - Track Selection Workflow
[VERSION] 1.0
[ROLE] PATCH_GENERATOR Input Collector
[ARCHITECTURE_ID] SAVE_SYSTEM_v3::PATCH_MODE_HANDLER

[TIER_HIERARCHY]
STAGING_FOLDER (atomicwriter) ──────────┐
MOD_SAVES_FOLDER (ModSaveManager) ──────┤ ← (This dialog stores selections here)
SETTINGS_JSON (SettingsManager) ────────────┴─ (Not used by this dialog)

[DIALOG_WORKFLOW]
Step_1: User selects biomes (checkboxes)
        └─ Populates: self.selected_biomes = [(category, name), ...]
Step_2: Dialog shows vanilla track indices for each biome
Step_3: User assigns .ogg files to specific tracks
        └─ Populates: self.replace_selections structure
Step_4: User confirms selections → MainWindow.replace_selections = data
        └─ MainWindow._auto_save_mod_state('replace track selections')
        └─ Writes to: mod_saves/{mod_name}.json → replace_selections key
Step_5: User clicks Generate Mod → patch_generator.py consumes structure

[KEY_PRINCIPLE]
THIS DIALOG ONLY COLLECTS DATA.
It does NOT generate patches, does NOT write to staging, does NOT manipulate files.
It only populates self.replace_selections and returns it to MainWindow.

MainWindow then:
1. Auto-saves to MOD_SAVES (via _auto_save_mod_state)
2. On Generate Mod: passes to patch_generator.py which uses it

[DATA_STRUCTURE] replace_selections Registry
{
  (category_str, biome_name_str): {
    'day': {
      track_index_int: '/path/to/track.ogg',
      ...
    },
    'night': {
      track_index_int: '/path/to/track.ogg',
      ...
    }
  },
  ...
}

Example:
{
  ('forest', 'surface_forest'): {
    'day': {0: '/Users/.../mytrack1.ogg', 2: '/Users/.../mytrack2.ogg'},
    'night': {1: '/Users/.../night_track.ogg'}
  },
  ('underground', 'surface_underground_0'): {
    'day': {0: '/Users/.../underground_track.ogg'},
    'night': {}
  }
}

[STATE_VARIABLES]
self.replace_selections  | dict | Data to return to MainWindow
self.selected_biomes     | list | [(category, name), ...]
self.current_biome       | tuple | (category, name) being edited
self.patch_mode          | str  | 'replace' or 'replace_and_add' (passed from MainWindow)
self.mod_name            | str  | Current mod name (for logging)

[INTERFACE_METHODS]
FN_001: __init__(parent, logger, patch_mode, mod_name)
        ├─ Initializes: self.replace_selections = {}
        ├─ Sets: self.patch_mode from MainWindow
        └─ Loads: self.mod_name for metadata

FN_002: _build_biome_selection_panel() → QWidget
        ├─ Creates: Checkboxes for all biomes
        ├─ Populates: self.selected_biomes = [...] on user select
        └─ Returns: QWidget (Step 1 UI)

FN_003: on_next_to_track_selection()
        ├─ Validates: len(self.selected_biomes) > 0
        ├─ Opens: Step 2 UI
        └─ Triggered: By "Next: Select Tracks" button

FN_004: accept() → None
        ├─ Called: When user clicks "Confirm & Close"
        ├─ Action: Dialog emits accepted() signal
        ├─ MainWindow.replace_selections = self.replace_selections
        └─ MainWindow calls: _auto_save_mod_state('replace track selections')

[SAVE_FLOW_INTEGRATION]
ReplaceTracksDialog.accept()
  └─ Emits: self.accepted()
     └─ MainWindow.on_replace_dialog_accepted()
        ├─ self.replace_selections = dialog.replace_selections
        ├─ Calls: _auto_save_mod_state('replace track selections')
        │   └─ mod_save_manager.save_mod(mod_name, full_state)
        │       └─ Writes: mod_saves/{mod_name}.json with replace_selections key
        └─ Dialog closes

[KEY_DISTINCTIONS]
✓ DIALOG SCOPE:        Collect user selections
✗ NOT Dialog scope:    File operations, patch generation, staging writes
✓ Saved by:            MainWindow after dialog returns
✗ NOT saved here:      This class never calls save functions
✓ Used by:             patch_generator.py reads self.replace_selections
✗ NOT used by:         Most of starsound_gui.py (only passed at end)

[INVARIANTS]
INV_001: replace_selections must be dict, never None
INV_002: selected_biomes populated only by checkbox logic
INV_003: Dialog never writes files or modifies staging
INV_004: Dialog never calls save functions directly
INV_005: Each (category, biome) tuple is unique in replace_selections
INV_006: All paths in replace_selections must be absolute Path objects or strings

[ERROR_HANDLING]
- Empty biome selection: "Next" button disabled until ≥1 selected
- Missing .ogg file: Show error in track selection UI
- Pattern: Block invalid states before allowing progress, not after

[DISTINCT_FROM]
- patch_generator.py: Consumes replace_selections, generates JSON patches
- atomicwriter.py: Writes patches to staging folder
- ModSaveManager: Persists replace_selections to disk
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox, QMenu, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette
from pathlib import Path
import subprocess
import os
import threading


class ReplaceTracksDialog(QDialog):
    """Main Replace workflow dialog"""
    
    def __init__(self, parent=None, logger=None, patch_mode='replace', mod_name='', existing_selections=None):
        super().__init__(parent)
        self.setWindowTitle('Replace Tracks - StarSound')
        self.setMinimumSize(1000, 700)
        self.logger = logger
        self.patch_mode = patch_mode
        self.mod_name = mod_name
        
        # Set dark palette without starfield
        self._set_dark_palette()
        
        # Will store selections: {(category, biome): {'day': {index: ogg_path, ...}, 'night': {...}}, ...}
        # If existing selections are provided (e.g., from a restored mod), use them
        import copy
        self.replace_selections = copy.deepcopy(existing_selections) if existing_selections else {}
        
        # Current state
        self.selected_biomes = []
        self.current_biome = None  # (category, name)
        self.main_layout = QVBoxLayout(self)  # Store reference for refresh
        
        layout = self.main_layout
        
        # Title
        title = QLabel('Replace Music Tracks - Select Which Tracks to Replace')
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Info label
        info = QLabel('Select one or more biomes. For each biome, you\'ll pick individual tracks to replace.')
        info.setStyleSheet('color: #b19cd9; font-size: 12px;')
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Create buttons FIRST so they exist when signals fire during initialization
        self.next_btn = QPushButton('Next: Select Tracks')
        self.next_btn.clicked.connect(self.on_next_to_track_selection)
        self.next_btn.setEnabled(False)
        
        # Step 1: Biome selection (signals will fire now, buttons exist, so handler works)
        self.biome_panel = self._build_biome_selection_panel()  # Store reference for refresh
        layout.addWidget(self.biome_panel)
        
        # Add buttons to layout
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self.next_btn)
        layout.addLayout(btn_row)
        
        self.setLayout(layout)
    
    def _set_dark_palette(self):
        """Apply a dark color palette without starfield inheritance"""
        # Clear any inherited stylesheets first - this is crucial!
        self.setStyleSheet("")
        
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor('#23283b'))
        palette.setColor(QPalette.WindowText, QColor('#e6ecff'))
        palette.setColor(QPalette.Base, QColor('#22223a'))
        palette.setColor(QPalette.AlternateBase, QColor('#2a2a3a'))
        palette.setColor(QPalette.ToolTipBase, QColor('#23283b'))
        palette.setColor(QPalette.ToolTipText, QColor('#e6ecff'))
        palette.setColor(QPalette.Text, QColor('#e6ecff'))
        palette.setColor(QPalette.Button, QColor('#3a6ea5'))
        palette.setColor(QPalette.ButtonText, QColor('#e6ecff'))
        palette.setColor(QPalette.BrightText, QColor('#e6ecff'))
        palette.setColor(QPalette.Link, QColor('#4e8cff'))
        palette.setColor(QPalette.Highlight, QColor('#4e8cff'))
        palette.setColor(QPalette.HighlightedText, QColor('#e6ecff'))
        self.setPalette(palette)
    
    def _build_biome_selection_panel(self) -> QWidget:
        """Build the biome selection panel (Step 1)"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        label = QLabel('Step 1: Select a Biome')
        label_font = QFont()
        label_font.setBold(True)
        label.setFont(label_font)
        layout.addWidget(label)
        
        info = QLabel('You can select one biome at a time. After assigning tracks, you can go back and add more to other biomes.')
        info.setStyleSheet('color: #b19cd9; font-size: 11px;')
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Show currently selected biomes with delete buttons
        if self.replace_selections:
            selected_label = QLabel('Selected Biomes:')
            selected_label_font = QFont()
            selected_label_font.setPointSize(11)
            selected_label_font.setBold(True)
            selected_label.setFont(selected_label_font)
            selected_label.setStyleSheet('color: #00d4ff; margin-top: 8px;')
            layout.addWidget(selected_label)
            
            selected_biomes_layout = QHBoxLayout()
            for (category, biome_name) in sorted(self.replace_selections.keys()):
                biome_display = QLabel(f'  ✓ {category}: {biome_name}')
                biome_display.setStyleSheet('color: #90EE90; font-size: 11px;')
                selected_biomes_layout.addWidget(biome_display)
                
                # Add delete button
                delete_btn = QPushButton('✕')
                delete_btn.setFixedSize(24, 24)
                delete_btn.setStyleSheet(
                    'background-color: #c41e3a; color: white; font-weight: bold; '
                    'border-radius: 4px; padding: 0px;'
                )
                delete_btn.setToolTip(f'Remove {biome_name} and all its track selections')
                delete_btn.clicked.connect(lambda checked, biome=(category, biome_name): 
                    self._remove_biome_selection(biome))
                selected_biomes_layout.addWidget(delete_btn)
            
            selected_biomes_layout.addStretch()
            layout.addLayout(selected_biomes_layout)
        
        from utils.patch_generator import get_all_biomes_by_category, get_vanilla_tracks_for_biome
        
        # Tree widget for biome selection
        self.biome_tree = QTreeWidget()
        self.biome_tree.setColumnCount(1)
        self.biome_tree.setHeaderHidden(True)
        self.biome_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.biome_tree.setStyleSheet('color: white; background-color: #22223a; font-size: 12px;')
        
        biomes = get_all_biomes_by_category()
        first_selected_item = None  # Track first biome with existing selections
        
        for category, biome_name in biomes:
            # Get vanilla track counts
            vanilla_data = get_vanilla_tracks_for_biome(category, biome_name)
            day_count = len(vanilla_data.get('dayTracks', []))
            night_count = len(vanilla_data.get('nightTracks', []))
            
            display = f'{category}: {biome_name}'
            if day_count > 0 or night_count > 0:
                display += f' ✓ [Day: {day_count}, Night: {night_count}]'
            
            item = QTreeWidgetItem([display])
            item.setData(0, Qt.UserRole, (category, biome_name))
            self.biome_tree.addTopLevelItem(item)
            
            # Pre-select FIRST biome that has existing selections (single selection mode)
            if (self.replace_selections and 
                (category, biome_name) in self.replace_selections and 
                first_selected_item is None):
                first_selected_item = item
        
        layout.addWidget(self.biome_tree)
        
        # Selection summary
        self.biome_summary = QLabel('No biome selected.')
        self.biome_summary.setStyleSheet('color: #e6ecff; font-size: 11px; margin-top: 8px;')
        layout.addWidget(self.biome_summary)
        
        # Connect signal AFTER biome_summary is created so handler can update it
        self.biome_tree.itemSelectionChanged.connect(self._on_biome_selection_changed)
        
        # Now pre-select and trigger handler
        if first_selected_item:
            first_selected_item.setSelected(True)
        
        return panel
    
    def _on_biome_selection_changed(self):
        """Update biome selection summary and enable/disable Next button"""
        selected = []
        for i in range(self.biome_tree.topLevelItemCount()):
            item = self.biome_tree.topLevelItem(i)
            if item.isSelected():
                biome_data = item.data(0, Qt.UserRole)
                if biome_data:
                    selected.append(biome_data)
        
        self.selected_biomes = selected
        
        if selected:
            category, biome_name = selected[0]  # Single selection
            summary = f'Selected: {category}: {biome_name}'
            self.biome_summary.setText(summary)
            self.next_btn.setEnabled(True)
        else:
            self.biome_summary.setText('No biome selected.')
            self.next_btn.setEnabled(False)
    
    def on_next_to_track_selection(self):
        """Show track selection panel for selected biome"""
        if not self.selected_biomes:
            QMessageBox.warning(self, 'No Selection', 'Please select a biome.')
            return
        
        # Work with the single selected biome
        self.current_biome = self.selected_biomes[0]
        self._show_track_selection_panel()
    
    def _remove_biome_selection(self, biome):
        """Remove a biome and all its track selections from replace_selections"""
        category, biome_name = biome
        if biome in self.replace_selections:
            del self.replace_selections[biome]
            print(f'[REPLACE] Removed biome selection: {category}: {biome_name}')
            # Refresh the dialog to show updated selected biomes list
            self._refresh_biome_panel()
    
    def _refresh_biome_panel(self):
        """Refresh the biome selection panel to show updated selections"""
        # Remove old panel
        if hasattr(self, 'biome_panel') and self.biome_panel:
            index = self.main_layout.indexOf(self.biome_panel)
            if index >= 0:
                self.main_layout.removeWidget(self.biome_panel)
                self.biome_panel.deleteLater()
        
        # Create new panel with updated selections
        self.biome_panel = self._build_biome_selection_panel()
        self.main_layout.insertWidget(2, self.biome_panel)  # Insert at position 2 (after title and info)
    
    def _reset_to_biome_selection(self):
        """Reset UI to biome selection panel, keeping existing selections in replace_selections"""
        # Unselect all items in tree
        self.biome_tree.clearSelection()
        self.selected_biomes = []
        self.biome_summary.setText('No biome selected.')
        self.next_btn.setEnabled(False)
        self.current_biome = None
    
    def _show_track_selection_panel(self):
        """Show track selection UI for current biome"""
        if not self.current_biome:
            return
        
        category, biome_name = self.current_biome
        
        # Create a new dialog for track selection
        dlg = QDialog(self)
        dlg.setWindowTitle(f'Select Tracks to Replace - {category}: {biome_name}')
        dlg.setMinimumSize(900, 600)
        
        # Clear inherited stylesheets first - crucial to prevent starfield tiling!
        dlg.setStyleSheet("")
        
        # Apply dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor('#23283b'))
        palette.setColor(QPalette.WindowText, QColor('#e6ecff'))
        palette.setColor(QPalette.Base, QColor('#22223a'))
        palette.setColor(QPalette.AlternateBase, QColor('#2a2a3a'))
        palette.setColor(QPalette.Text, QColor('#e6ecff'))
        palette.setColor(QPalette.Button, QColor('#3a6ea5'))
        palette.setColor(QPalette.ButtonText, QColor('#e6ecff'))
        dlg.setPalette(palette)
        
        layout = QVBoxLayout(dlg)
        
        # Title
        title = QLabel(f'Select Tracks to Replace in {category}: {biome_name}')
        title_font = QFont()
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        info = QLabel(
            'Each track shows its index (position) and vanilla name.\n'
            'Click any track to choose which .ogg file should replace it.\n'
            'You can change your mind before saving.'
        )
        info.setStyleSheet('color: #b19cd9; font-size: 11px;')
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Track list with indices
        from utils.patch_generator import get_vanilla_tracks_for_biome
        vanilla_data = get_vanilla_tracks_for_biome(category, biome_name)
        day_tracks = vanilla_data.get('dayTracks', [])
        night_tracks = vanilla_data.get('nightTracks', [])
        
        # Check if biome has any tracks
        if not day_tracks and not night_tracks:
            # Empty biome message
            empty_msg = QLabel(
                '⚠ Nothing to Replace!\n\n'
                'This biome has no music normally, so there\'s nothing to replace.\n\n'
                'To add music to this biome, choose one of these options:\n'
                '  • Go back and select "Add to Game" instead\n'
                '  • Or select "Replace Base Game Music and Add To Game"\n\n'
                'This will add your music to this biome without trying to replace anything.'
            )
            empty_msg.setStyleSheet('color: #ffcc99; background-color: #3a2a1a; padding: 12px; border-radius: 4px; font-size: 11px;')
            empty_msg.setWordWrap(True)
            empty_msg.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty_msg, 1)
        else:
            # Info banner showing vanilla tracks are available and preview-able
            preview_info = QLabel('✓ Vanilla tracks available - 🔊 right-click any track name to preview')
            preview_info.setStyleSheet('color: #6fff99; background-color: #1a3a1a; padding: 8px; border-radius: 4px; font-size: 11px; font-weight: bold;')
            preview_info.setWordWrap(True)
            layout.addWidget(preview_info)
            
            # Scrollable track list
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            
            # Day tracks
            if day_tracks:
                # Day label with Clear All button
                day_header = QHBoxLayout()
                day_label = QLabel('Day Tracks')
                day_label_font = QFont()
                day_label_font.setBold(True)
                day_label.setFont(day_label_font)
                day_label.setStyleSheet('color: #b19cd9; margin-top: 8px;')
                day_header.addWidget(day_label)
                day_header.addStretch()
                
                clear_all_day_btn = QPushButton('Clear All Day Tracks')
                clear_all_day_btn.setMaximumWidth(150)
                clear_all_day_btn.setStyleSheet('background-color: #8a3a3a; color: #ffffff; font-size: 10px;')
                def on_clear_all_day():
                    if (category, biome_name) in self.replace_selections and 'day' in self.replace_selections[(category, biome_name)]:
                        self.replace_selections[(category, biome_name)]['day'] = {}
                        if self.logger:
                            self.logger.log(f'Cleared all day tracks for {biome_name}', context='ReplaceDialog')
                        # Refresh the dialog by re-showing the track selection panel
                        self._show_track_selection_panel()
                clear_all_day_btn.clicked.connect(on_clear_all_day)
                day_header.addWidget(clear_all_day_btn)
                
                day_header_widget = QWidget()
                day_header_widget.setLayout(day_header)
                scroll_layout.addWidget(day_header_widget)
                
                # Initialize selections for this biome if not already done
                if self.current_biome not in self.replace_selections:
                    self.replace_selections[self.current_biome] = {'day': {}, 'night': {}}
                
                for index, track_path in enumerate(day_tracks):
                    track_name = Path(track_path).name if track_path else f'Track {index}'
                    track_widget = self._build_track_selection_row(
                        index, track_name, 'day', category, biome_name
                    )
                    scroll_layout.addWidget(track_widget)
            
            # Night tracks
            if night_tracks:
                # Night label with Clear All button
                night_header = QHBoxLayout()
                night_label = QLabel('Night Tracks')
                night_label_font = QFont()
                night_label_font.setBold(True)
                night_label.setFont(night_label_font)
                night_label.setStyleSheet('color: #b19cd9; margin-top: 12px;')
                night_header.addWidget(night_label)
                night_header.addStretch()
                
                clear_all_night_btn = QPushButton('Clear All Night Tracks')
                clear_all_night_btn.setMaximumWidth(150)
                clear_all_night_btn.setStyleSheet('background-color: #8a3a3a; color: #ffffff; font-size: 10px;')
                def on_clear_all_night():
                    if (category, biome_name) in self.replace_selections and 'night' in self.replace_selections[(category, biome_name)]:
                        self.replace_selections[(category, biome_name)]['night'] = {}
                        if self.logger:
                            self.logger.log(f'Cleared all night tracks for {biome_name}', context='ReplaceDialog')
                        # Refresh the dialog by re-showing the track selection panel
                        self._show_track_selection_panel()
                clear_all_night_btn.clicked.connect(on_clear_all_night)
                night_header.addWidget(clear_all_night_btn)
                
                night_header_widget = QWidget()
                night_header_widget.setLayout(night_header)
                scroll_layout.addWidget(night_header_widget)
                
                for index, track_path in enumerate(night_tracks):
                    track_name = Path(track_path).name if track_path else f'Track {index}'
                    track_widget = self._build_track_selection_row(
                        index, track_name, 'night', category, biome_name
                    )
                    scroll_layout.addWidget(track_widget)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_widget)
            layout.addWidget(scroll)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)
        
        done_btn = QPushButton('Done - Show Summary')
        done_btn.clicked.connect(lambda: self._on_track_selection_done(dlg))
        
        # Disable Done button if no tracks to replace
        if not day_tracks and not night_tracks:
            done_btn.setEnabled(False)
            done_btn.setToolTip('This biome has no tracks to replace. Please select a different biome or use Add mode instead.')
        
        btn_row.addWidget(done_btn)
        
        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        dlg.exec_()
    
    def _build_track_selection_row(self, index: int, vanilla_name: str, day_or_night: str, category: str, biome: str) -> QWidget:
        """Build a single track selection row"""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 4, 0, 4)
        
        # Track label with index - make it right-clickable for preview
        label_text = f'{day_or_night.capitalize()} {index}: {vanilla_name}'
        label = QLabel(label_text)
        # Make track labels GREEN to indicate they're preview-able
        label.setStyleSheet('color: #6fff99; font-size: 11px; font-weight: bold;')
        label.setToolTip('🔊 Right-click to preview this vanilla track')
        label.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # Store vanilla track path for preview
        vanilla_track_path = self._get_vanilla_track_path(category, biome, day_or_night, index)
        
        def show_context_menu(position):
            if vanilla_track_path and vanilla_track_path.exists():
                menu = QMenu()
                preview_action = menu.addAction('🔊 Preview Original Track')
                action = menu.exec_(label.mapToGlobal(position))
                if action == preview_action:
                    self._play_vanilla_track(vanilla_track_path)
        
        label.customContextMenuRequested.connect(show_context_menu)
        layout.addWidget(label)
        
        # File assignment button
        btn = QPushButton('► Assign .ogg File')
        btn.setMaximumWidth(150)
        btn.setStyleSheet('background-color: #3a5a8a; font-size: 10px;')
        
        # Assignment status
        self.track_file_labels = getattr(self, 'track_file_labels', {})
        status_key = (category, biome, day_or_night, index)
        status = QLabel('(none selected)')
        status.setStyleSheet('color: #888888; font-size: 10px;')
        self.track_file_labels[status_key] = status
        
        # DEBUG: Log replace_selections state
        if self.logger:
            self.logger.log(f'[DEBUG] Checking {day_or_night} track {index}: replace_selections keys = {list(self.replace_selections.keys())}', context='ReplaceDialog')
        
        # Check if this track already has a file assigned from previous selections
        if (category, biome) in self.replace_selections:
            if self.logger:
                self.logger.log(f'[DEBUG] Found biome {(category, biome)} in replace_selections', context='ReplaceDialog')
            
            biome_selections = self.replace_selections[(category, biome)]
            if day_or_night in biome_selections and index in biome_selections[day_or_night]:
                assigned_file = biome_selections[day_or_night][index]
                filename = Path(assigned_file).name
                
                if self.logger:
                    self.logger.log(f'[DEBUG] Found existing assignment: {day_or_night} {index} = {filename}', context='ReplaceDialog')
                
                # Show existing assignment
                status.setText(f'✓ {filename}')
                status.setStyleSheet('color: #6fff99; font-size: 10px;')
                
                # Update button to indicate it can be changed
                btn.setText(f'✓ {filename[:20]}...' if len(filename) > 20 else f'✓ {filename}')
                btn.setStyleSheet('background-color: #3a8a5a; font-size: 10px; color: #6fff99;')
        else:
            if self.logger:
                self.logger.log(f'[DEBUG] Biome {(category, biome)} NOT in replace_selections', context='ReplaceDialog')
        
        # Store reference to selections for this track - pass status label to callback
        def on_assign_file():
            self._on_assign_track_file(index, day_or_night, category, biome, btn, label, status)
        
        btn.clicked.connect(on_assign_file)
        layout.addWidget(btn)
        layout.addWidget(status)
        
        # Add Clear button for this individual track
        clear_btn = QPushButton('✕')
        clear_btn.setMaximumWidth(30)
        clear_btn.setToolTip('Clear this track selection')
        clear_btn.setStyleSheet('background-color: #8a3a3a; color: #ffffff; font-size: 12px; font-weight: bold;')
        
        def on_clear_track():
            # Remove from replace_selections
            if (category, biome) in self.replace_selections:
                if day_or_night in self.replace_selections[(category, biome)]:
                    if index in self.replace_selections[(category, biome)][day_or_night]:
                        del self.replace_selections[(category, biome)][day_or_night][index]
                        if self.logger:
                            self.logger.log(f'Cleared {day_or_night} track {index} for {biome}', context='ReplaceDialog')
            
            # Reset UI
            status.setText('(none selected)')
            status.setStyleSheet('color: #888888; font-size: 10px;')
            btn.setText('► Assign .ogg File')
            btn.setStyleSheet('background-color: #3a5a8a; font-size: 10px;')
        
        clear_btn.clicked.connect(on_clear_track)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        row.setLayout(layout)
        return row
    
    def _get_vanilla_track_path(self, category: str, biome: str, day_or_night: str, index: int) -> Path:
        """Get the path to a vanilla track file"""
        from utils.patch_generator import get_vanilla_tracks_for_biome
        
        try:
            vanilla_data = get_vanilla_tracks_for_biome(category, biome)
            tracks = vanilla_data.get(f'{day_or_night}Tracks', [])
            
            if 0 <= index < len(tracks):
                return Path(tracks[index])
        except Exception as e:
            if self.logger:
                self.logger.warn(f'Failed to get vanilla track path: {e}', context='ReplaceDialog')
        
        return None
    
    def _play_vanilla_track(self, track_path: Path):
        """Play a vanilla track in a background thread"""
        if not track_path.exists():
            QMessageBox.warning(self, 'File Not Found', f'Track not found: {track_path.name}')
            return
        
        def play_audio():
            try:
                # Use OS-native default player by opening the file
                if os.name == 'nt':  # Windows - use default associated player
                    os.startfile(str(track_path))
                    if self.logger:
                        self.logger.log(f'Playing vanilla track with default player: {track_path.name}', context='ReplaceDialog')
                else:  # Linux/Mac - try common players
                    import subprocess
                    for player in ['paplay', 'play', 'ffplay']:
                        try:
                            subprocess.Popen([player, str(track_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            if self.logger:
                                self.logger.log(f'Playing vanilla track with {player}: {track_path.name}', context='ReplaceDialog')
                            break
                        except (FileNotFoundError, subprocess.CalledProcessError):
                            continue
            except Exception as e:
                if self.logger:
                    self.logger.warn(f'Failed to play track: {e}', context='ReplaceDialog')
        
        # Play in background thread so UI doesn't freeze
        thread = threading.Thread(target=play_audio, daemon=True)
        thread.start()
    
    def _on_assign_track_file(self, index: int, day_or_night: str, category: str, biome: str, btn: QPushButton, label: QLabel, status_label: QLabel = None):
        """Show file picker for assigning .ogg to a track"""
        # Determine initial directory (mod's music folder if available)
        initial_dir = ''
        if self.mod_name:
            try:
                from pathlib import Path
                mod_music_folder = Path(__file__).parent.parent / 'staging' / self.mod_name / 'music'
                if mod_music_folder.exists():
                    initial_dir = str(mod_music_folder)
            except Exception:
                initial_dir = ''
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f'Select .ogg file for {day_or_night.capitalize()} Track {index}',
            initial_dir,
            'OGG Files (*.ogg);;Audio Files (*.ogg *.mp3 *.wav);;All Files (*)'
        )
        
        if file_path:
            # Store selection
            if self.current_biome not in self.replace_selections:
                self.replace_selections[self.current_biome] = {'day': {}, 'night': {}}
            
            self.replace_selections[self.current_biome][day_or_night][index] = file_path
            
            # Update button label
            filename = Path(file_path).name
            btn.setText(f'✓ {filename[:20]}...' if len(filename) > 20 else f'✓ {filename}')
            btn.setStyleSheet('background-color: #3a8a5a; font-size: 10px; color: #6fff99;')
            
            # Update status label if provided
            if status_label:
                status_label.setText(f'✓ {filename}')
                status_label.setStyleSheet('color: #6fff99; font-size: 10px;')
            
            if self.logger:
                self.logger.log(f'Assigned {day_or_night} track {index} to {filename}', context='ReplaceDialog')
    
    def _on_track_selection_done(self, dlg: QDialog):
        """After user finishes selecting tracks for current biome, show summary"""
        if self.logger:
            self.logger.log(f'[DEBUG] Done button clicked. replace_selections = {self.replace_selections}', context='ReplaceDialog')
        
        # Check if ANY tracks actually have files assigned (not just biomes selected)
        has_actual_selections = False
        for biome_data in self.replace_selections.values():
            if biome_data.get('day') or biome_data.get('night'):
                has_actual_selections = True
                break
        
        if not has_actual_selections:
            if self.logger:
                self.logger.log('[DEBUG] No files assigned to any tracks yet', context='ReplaceDialog')
            QMessageBox.information(
                self, 
                'No Tracks Selected', 
                'You haven\'t assigned any .ogg files to tracks yet.\n\n'
                'Please click "► Assign .ogg File" on at least one track and select a file.'
            )
            return
        
        # Close track selection dialog
        dlg.accept()
        
        # Build and show summary
        self._show_summary_dialog()
    
    def _show_summary_dialog(self):
        """Show summary of all replace selections before finalizing"""
        dlg = QDialog(self)
        dlg.setWindowTitle('Replacement Summary - Confirm Before Finalizing')
        dlg.setMinimumSize(800, 500)
        
        # Clear inherited stylesheets first - crucial to prevent starfield tiling!
        dlg.setStyleSheet("")
        
        # Apply dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor('#23283b'))
        palette.setColor(QPalette.WindowText, QColor('#e6ecff'))
        palette.setColor(QPalette.Base, QColor('#22223a'))
        palette.setColor(QPalette.AlternateBase, QColor('#2a2a3a'))
        palette.setColor(QPalette.Text, QColor('#e6ecff'))
        palette.setColor(QPalette.Button, QColor('#3a6ea5'))
        palette.setColor(QPalette.ButtonText, QColor('#e6ecff'))
        dlg.setPalette(palette)
        
        layout = QVBoxLayout(dlg)
        
        title = QLabel('📋 Here\'s What Will Be Replaced')
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        layout.addWidget(title)
        
        info = QLabel(
            'Review the replacements below. Each shows:\n'
            '• Biome and track index\n'
            '• Which .ogg file will replace the vanilla track'
        )
        info.setStyleSheet('color: #b19cd9; font-size: 11px; margin-bottom: 8px;')
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Summary content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        for (category, biome), tracks_dict in self.replace_selections.items():
            # Biome header
            biome_header = QLabel(f'{category}: {biome}')
            biome_header_font = QFont()
            biome_header_font.setBold(True)
            biome_header.setFont(biome_header_font)
            biome_header.setStyleSheet('color: #4e8cff; margin-top: 8px;')
            scroll_layout.addWidget(biome_header)
            
            # Day tracks
            if tracks_dict.get('day'):
                day_header = QLabel('  Day:')
                day_header.setStyleSheet('color: #b19cd9; margin-left: 12px; margin-top: 4px;')
                scroll_layout.addWidget(day_header)
                
                for index in sorted(tracks_dict['day'].keys()):
                    ogg_path = tracks_dict['day'][index]
                    filename = Path(ogg_path).name
                    item = QLabel(f'    Track {index}: → {filename}')
                    item.setStyleSheet('color: #a9a9a9; font-size: 10px; margin-left: 24px;')
                    scroll_layout.addWidget(item)
            
            # Night tracks
            if tracks_dict.get('night'):
                night_header = QLabel('  Night:')
                night_header.setStyleSheet('color: #b19cd9; margin-left: 12px; margin-top: 6px;')
                scroll_layout.addWidget(night_header)
                
                for index in sorted(tracks_dict['night'].keys()):
                    ogg_path = tracks_dict['night'][index]
                    filename = Path(ogg_path).name
                    item = QLabel(f'    Track {index}: → {filename}')
                    item.setStyleSheet('color: #a9a9a9; font-size: 10px; margin-left: 24px;')
                    scroll_layout.addWidget(item)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        back_btn = QPushButton('← Add More Biomes')
        back_btn.clicked.connect(lambda: [dlg.reject(), self._reset_to_biome_selection()])
        btn_row.addWidget(back_btn)
        
        confirm_btn = QPushButton('✓ Confirm and Use These Replacements')
        confirm_btn.setStyleSheet('background-color: #3a8a5a; color: #6fff99;')
        confirm_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(confirm_btn)
        
        layout.addLayout(btn_row)
        dlg.setLayout(layout)
        
        if dlg.exec_() == QDialog.Accepted:
            # User confirmed, close the main Replace dialog
            self.accept()
        # Otherwise loop back to track selection
