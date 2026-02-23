"""
Per-Track Audio Processing Configuration Dialog
==============================================

Allows users to configure different audio processing settings for each
individual track when multiple tracks are selected at once in Step 3.

Features:
- Display list of all selected audio tracks
- Configure audio processing for each track individually
- Apply presets to single track or all tracks
- Override default settings per track
"""

# For UI styling standards, see ../UI_STYLE_GUIDE.md

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QLineEdit, QGridLayout, QMessageBox,
    QListWidget, QListWidgetItem, QSplitter, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from dialogs.help_window import HelpWindow
import os
import subprocess
import platform
import shutil
import json
from pathlib import Path
from utils.audio_utils import parse_time_string, ensure_ffmpeg_installed


class PerTrackAudioConfigDialog(QDialog):
    """
    Modal dialog for configuring per-track audio processing.
    
    Shows a list of selected tracks on the left and audio processing
    controls on the right. User can switch between tracks to customize
    settings individually.
    """
    
    def __init__(self, audio_files, default_options=None, parent=None, segment_origins=None):
        """
        Initialize the Per-Track Audio Config Dialog.
        
        Args:
            audio_files: List of file paths selected by user
            default_options: Default audio processing options dict from main dialog
            parent: Parent widget (main window)
            segment_origins: Dict mapping segment_path -> original_file_path (for split tracking)
                           If provided, groups segments by parent track in the list display
        
        Segment Grouping:
        - If segment_origins is provided, segments are visually grouped by parent file
        - User can configure each segment individually or apply to all segments of a parent
        """
        super().__init__(parent)
        self.setWindowTitle('🎵 Configure Audio Processing Per Track')
        self.setModal(True)
        # Explicitly disable Windows help button hint
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(1400)
        self.setMinimumHeight(850)
        
        # Store audio files and configurations
        self.audio_files = audio_files
        self.segment_origins = segment_origins or {}  # Maps segment_path -> original_file_path
        
        # Convert default options from audio_processing_dialog format to internal format
        self.default_options = self._convert_audio_options(default_options or {})
        
        # If this is split audio (segments detected), disable edge-sensitive audio processing filters by default
        # Trim and silence_trim can damage segment boundaries during split operations
        # However, fade should ALWAYS apply - each segment becomes its own track and needs proper fade in/out
        if self.segment_origins:
            debug_msg = f'[SPLIT_AUDIO_DETECTED] {len(self.segment_origins)} segment(s). Disabling trim/silence_trim by default (keeping fade enabled).'
            if hasattr(self.parent(), 'logger'):
                self.parent().logger.log(debug_msg)
            else:
                print(f'[PER_TRACK_CONFIG] {debug_msg}')
            
            self.default_options['trim_enabled'] = False  # Audio Trimming off for splits - would damage segment boundaries
            self.default_options['silence_trim_enabled'] = False  # Silence Trimming off - too aggressive on segment edges
            # NOTE: fade_enabled is NOT disabled - segments are individual tracks that need fade processing
        else:
            if hasattr(self.parent(), 'logger'):
                self.parent().logger.log('[PER_TRACK_CONFIG] No segments detected - using default audio settings')

        
        # Initialize per-track settings storage
        # Structure: {file_path: {audio_processing_options}}
        self.per_track_settings = {}
        for file_path in audio_files:
            self.per_track_settings[file_path] = self.default_options.copy() if self.default_options else {}
        
        self.current_track_index = 0
        
        # Build parent-to-segments mapping for display (if segments detected)
        self.parent_to_segments = {}  # Maps original file -> list of segments
        if self.segment_origins:
            for segment_path, original_path in self.segment_origins.items():
                # Only include segments/parents that are actually in the current audio_files list
                if segment_path in audio_files or original_path in audio_files:
                    if original_path not in self.parent_to_segments:
                        self.parent_to_segments[original_path] = []
                    self.parent_to_segments[original_path].append(segment_path)
        
        # Track WAV files and temp directories for cleanup on dialog close
        self.wav_files_to_clean = []  # Track .wav files that should be cleaned up
        self.temp_dirs_to_clean = []  # Track temp directories that should be cleaned up
        for audio_file in audio_files:
            if audio_file.endswith('.wav'):
                self.wav_files_to_clean.append(audio_file)
                # Also track parent temp directory
                parent_dir = os.path.dirname(audio_file)
                if '.starsound_splits_temp' in parent_dir:
                    if parent_dir not in self.temp_dirs_to_clean:
                        self.temp_dirs_to_clean.append(parent_dir)
        
        # See UI_STYLE_GUIDE.md for styling standards
        self.setStyleSheet('''
            QDialog {
                background-color: #1a1f2e;
            }
            QLabel {
                color: #e6ecff;
            }
            QListWidget {
                background-color: #283046;
                color: #e6ecff;
                border: 1px solid #3a4a6a;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px;
            }
            QListWidget::item:selected {
                background-color: #00d4ff;
                color: #1a1f2e;
                font-weight: bold;
            }
            QToolTip {
                background-color: #2a3f5f;
                color: #e6ecff;
                border: 2px solid #00d4ff;
                border-radius: 4px;
                padding: 4px;
                font-size: 11px;
            }
        ''')
        
        # Configure tooltip styling globally for this application
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            # Apply bright tooltip styling at app level (tooltips render outside dialog context)
            current_style = app.styleSheet()
            app.setStyleSheet(current_style + '''
                QToolTip {
                    background-color: #2a3f5f;
                    color: #e6ecff;
                    border: 2px solid #00d4ff;
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 11px;
                }
            ''')
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Title section
        title = QLabel('🎵 Configure Audio Processing Per Track')
        title.setStyleSheet('color: #00d4ff; font-size: 16px; font-weight: bold;')
        main_layout.addWidget(title)
        
        # Subtitle section: indicate if segments are grouped
        if self.parent_to_segments:
            subtitle = QLabel(f'Customize settings for {len(audio_files)} split segment(s) from {len(self.parent_to_segments)} original file(s)')
            subtitle.setStyleSheet('color: #ffa500; font-size: 12px; margin-bottom: 12px; font-weight: bold;')
            subtitle_note = QLabel('💡 Segments are grouped by parent file. Configure each segment individually or use "Apply To All".')
            subtitle_note.setStyleSheet('color: #888888; font-size: 11px; margin-bottom: 12px; font-style: italic;')
            main_layout.addWidget(subtitle)
            main_layout.addWidget(subtitle_note)
        else:
            subtitle = QLabel(f'Customize audio settings individually for {len(audio_files)} track(s)')
            subtitle.setStyleSheet('color: #888888; font-size: 12px; margin-bottom: 12px;')
            main_layout.addWidget(subtitle)
        
        # ===== PRESET SYSTEM =====
        presets_label = QLabel('🎵 Quick Presets:')
        presets_label.setStyleSheet('color: #ffcc00; font-size: 11px; margin-top: 8px;')
        main_layout.addWidget(presets_label)
        
        presets_row = QHBoxLayout()
        presets = [
            ('🎧 Lo-Fi', 'lofi'),
            ('🎼 Orchestral', 'orchestral'),
            ('🎹 Electronic', 'electronic'),
            ('☁️ Ambient', 'ambient'),
            ('🤘 Metal', 'metal'),
            ('🎸 Acoustic', 'acoustic'),
            ('🎵 Pop', 'pop'),
            ('✗ None', 'none'),
            ('✓ All', 'all'),
        ]
        
        for preset_label, preset_id in presets:
            btn = QPushButton(preset_label)
            btn.setMaximumWidth(110)
            btn.setStyleSheet('''
                QPushButton {
                    background-color: #2a3a4a;
                    color: #e6ecff;
                    border: 1px solid #3a4a6a;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #3a4a5a;
                    border: 1px solid #00d4ff;
                }
            ''')
            btn.clicked.connect(lambda checked, pid=preset_id: self.apply_preset_to_current(pid))
            presets_row.addWidget(btn)
        
        presets_row.addStretch()
        main_layout.addLayout(presets_row)
        
        # ===== OGG BITRATE SELECTION =====
        bitrate_row = QHBoxLayout()
        bitrate_label = QLabel('OGG Bitrate:')
        bitrate_label.setStyleSheet('color: #e6ecff;')
        bitrate_row.addWidget(bitrate_label)
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(['192 kbps (default)', '128 kbps', '256 kbps', '320 kbps'])
        self.bitrate_combo.setCurrentIndex(0)  # Default to 192 kbps
        self.bitrate_combo.setStyleSheet(
            'QComboBox { background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px; }'
            'QComboBox QAbstractItemView { background: #283046; color: #e6ecff; selection-background-color: #3a4a6a; }'
            'QComboBox::drop-down { border: none; }'
            'QComboBox:focus { border: 1px solid #5a8ed5; }'
        )
        bitrate_row.addWidget(self.bitrate_combo)
        bitrate_row.addStretch()
        main_layout.addLayout(bitrate_row)
        
        # Content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setSizes([300, 900])  # Set initial proportions
        
        # ===== LEFT PANEL: Track list =====
        left_panel_layout = QVBoxLayout()
        left_panel_layout.setSpacing(10)
        
        left_panel_label = QLabel('📋 Selected Tracks:')
        left_panel_label.setStyleSheet('color: #00d4ff; font-weight: bold; font-size: 12px;')
        left_panel_layout.addWidget(left_panel_label)
        
        self.track_list_widget = QListWidget()
        self.track_list_widget.setMinimumWidth(200)
        self.track_list_widget.clear()  # Ensure list is empty before populating
        self.track_list_widget.setFocusPolicy(Qt.StrongFocus)  # Enable keyboard focus
        # Note: Arrow key navigation is handled natively by QListWidget and automatically skips non-selectable items
        
        # If segments detected, show grouped view; otherwise show flat list
        if self.parent_to_segments:
            # GROUPED VIEW: Show segments grouped by parent, plus any standalone files
            from PyQt5.QtGui import QFont, QColor
            
            # Track which files have been displayed (as segments)
            displayed_files = set()
            
            # Display grouped segments first
            for parent_path, segments in self.parent_to_segments.items():
                parent_name = os.path.basename(parent_path)
                
                # Add parent file as header (disabled, not selectable)
                parent_item = QListWidgetItem(f'📁 {parent_name} (original)')
                parent_item.setFlags(parent_item.flags() & ~Qt.ItemIsSelectable)  # Disabled
                # Style parent item: blue color, bold font
                parent_item.setForeground(QColor('#4e8cff'))
                parent_font = QFont()
                parent_font.setBold(True)
                parent_item.setFont(parent_font)
                self.track_list_widget.addItem(parent_item)
                
                # Add each segment as a child
                for segment_index, segment_path in enumerate(segments):
                    segment_name = os.path.basename(segment_path)
                    segment_num = segment_index + 1
                    display_name = f'  ├─ {segment_name} (part {segment_num})'
                    
                    item = QListWidgetItem(display_name)
                    # Find the index of the original file this segment came from
                    original_file = self.segment_origins.get(segment_path, segment_path)
                    try:
                        file_index = audio_files.index(original_file)
                    except ValueError:
                        # If original file not in list either, use segment_path
                        try:
                            file_index = audio_files.index(segment_path)
                        except ValueError:
                            # Fallback: skip if neither found
                            continue
                    
                    item.setData(Qt.UserRole, file_index)
                    # Style segment item: normal color
                    item.setForeground(QColor('#e6ecff'))
                    self.track_list_widget.addItem(item)
                    
                    # Track this file as displayed
                    displayed_files.add(segment_path)
            
            # Display standalone files (not part of any segment group)
            self.track_list_widget.addItem(QListWidgetItem(''))  # Separator
            separator_item = self.track_list_widget.item(self.track_list_widget.count() - 1)
            separator_item.setFlags(separator_item.flags() & ~Qt.ItemIsSelectable)
            
            for i, file_path in enumerate(audio_files):
                if file_path not in displayed_files:
                    # This is a standalone file
                    filename = os.path.basename(file_path)
                    item = QListWidgetItem(filename)
                    item.setData(Qt.UserRole, i)
                    item.setForeground(QColor('#e6ecff'))
                    self.track_list_widget.addItem(item)
        else:
            # FLAT VIEW: No segments, show all files as-is
            for i, file_path in enumerate(audio_files):
                filename = os.path.basename(file_path)
                item = QListWidgetItem(filename)
                item.setData(Qt.UserRole, i)
                self.track_list_widget.addItem(item)
        
        # Select first selectable track by default
        if self.track_list_widget.count() > 0:
            for i in range(self.track_list_widget.count()):
                item = self.track_list_widget.item(i)
                if item.flags() & Qt.ItemIsSelectable:
                    self.track_list_widget.setCurrentRow(i)
                    break
        
        self.track_list_widget.itemSelectionChanged.connect(self.on_track_selected)
        left_panel_layout.addWidget(self.track_list_widget, 1)
        
        # Track buttons
        track_btn_layout = QHBoxLayout()
        track_btn_layout.setSpacing(6)
        
        apply_to_all_btn = QPushButton('📋 Apply To All')
        apply_to_all_btn.setStyleSheet('''
            QPushButton {
                background-color: #2d5a3d;
                color: #e6ecff;
                border-radius: 4px;
                padding: 6px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d7a4d;
            }
        ''')
        apply_to_all_btn.clicked.connect(self.apply_current_to_all)
        track_btn_layout.addWidget(apply_to_all_btn)
        
        # Preview and open buttons
        preview_btn = QPushButton('▶️ Preview')
        preview_btn.setStyleSheet('''
            QPushButton {
                background-color: #3a6ea5;
                color: #e6ecff;
                border: 1px solid #4e8cff;
                border-radius: 4px;
                padding: 6px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4e8cff;
                border: 1px solid #6bbcff;
            }
        ''')
        preview_btn.setToolTip('Play the selected track to preview it')
        preview_btn.clicked.connect(self.preview_current_track)
        track_btn_layout.addWidget(preview_btn)
        
        left_panel_layout.addLayout(track_btn_layout)
        
        # Create left panel container
        left_panel_container = QWidget()
        left_panel_container.setStyleSheet('background-color: #1a1f2e;')
        left_panel_container.setLayout(left_panel_layout)
        
        # ===== RIGHT PANEL: Audio processing controls =====
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setSpacing(10)
        
        # Header with current track name
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        right_panel_label = QLabel('🎛️ Audio Processing Settings:')
        right_panel_label.setStyleSheet('color: #00d4ff; font-weight: bold; font-size: 12px;')
        self.track_name_label = QLabel('')
        self.track_name_label.setStyleSheet('color: #00ff00; font-weight: bold; font-size: 11px; margin-left: 12px;')
        header_layout.addWidget(right_panel_label)
        header_layout.addWidget(self.track_name_label)
        header_layout.addStretch()
        right_panel_layout.addLayout(header_layout)
        
        # Create scrollable area for audio controls
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet('background-color: #1a1f2e; border: 1px solid #3a4a6a; border-radius: 4px;')
        scroll_area.setWidgetResizable(True)
        
        # Audio controls container
        self.audio_controls_widget = QVBoxLayout()
        self.create_audio_controls()
        controls_widget = QWidget()
        controls_widget.setStyleSheet('background-color: #1a1f2e;')
        controls_widget.setLayout(self.audio_controls_widget)
        
        scroll_area.setWidget(controls_widget)
        right_panel_layout.addWidget(scroll_area, 1)
        
        # Bottom buttons for controls
        control_btn_layout = QHBoxLayout()
        control_btn_layout.setSpacing(6)
        
        reset_btn = QPushButton('🔄 Reset To Default')
        reset_btn.setStyleSheet('''
            QPushButton {
                background-color: #c41e3a;
                color: #e6ecff;
                border-radius: 4px;
                padding: 6px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e63235;
            }
        ''')
        reset_btn.clicked.connect(self.reset_current_to_default)
        control_btn_layout.addWidget(reset_btn)
        control_btn_layout.addStretch()
        right_panel_layout.addLayout(control_btn_layout)
        
        # Create right panel container
        right_panel_container = QWidget()
        right_panel_container.setStyleSheet('background-color: #1a1f2e;')
        right_panel_container.setLayout(right_panel_layout)
        
        # Add panels to splitter
        splitter.addWidget(left_panel_container)
        splitter.addWidget(right_panel_container)
        splitter.setStretchFactor(0, 1)  # Left panel resizable
        splitter.setStretchFactor(1, 2)  # Right panel gets more space by default
        splitter.setCollapsible(0, False)  # Prevent collapsing left
        splitter.setCollapsible(1, False)  # Prevent collapsing right
        main_layout.addWidget(splitter, 1)
        
        # Dialog buttons
        dialog_btn_layout = QHBoxLayout()
        dialog_btn_layout.setSpacing(8)
        dialog_btn_layout.addStretch()
        
        confirm_btn = QPushButton('Continue')
        confirm_btn.setStyleSheet('''
            QPushButton {
                background-color: #2d5a3d;
                color: #e6ecff;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #3d7a4d;
            }
        ''')
        confirm_btn.clicked.connect(self.accept)
        dialog_btn_layout.addWidget(confirm_btn)
        
        cancel_btn = QPushButton('✗ Cancel')
        cancel_btn.setStyleSheet('''
            QPushButton {
                background-color: #c41e3a;
                color: #e6ecff;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #e63235;
            }
        ''')
        cancel_btn.clicked.connect(self.reject)
        dialog_btn_layout.addWidget(cancel_btn)
        
        help_btn = QPushButton('?')
        help_btn.setMaximumWidth(40)
        help_btn.setToolTip('Show help for per-track audio configuration')
        help_btn.setStyleSheet('background-color: #3a5a7a; color: #e6ecff; border-radius: 4px; padding: 6px; font-weight: bold; font-size: 14px;')
        help_btn.clicked.connect(self.show_help)
        dialog_btn_layout.addWidget(help_btn)
        
        main_layout.addLayout(dialog_btn_layout)
        
        # Load first track settings
        self.load_track_settings(self.audio_files[0] if self.audio_files else '')
        self._update_track_name_display()
    
    def _convert_audio_options(self, options: dict) -> dict:
        """
        Convert audio options from audio_processing_dialog format to internal format.
        
        The audio_processing_dialog returns a dict like:
            {'trim': True, 'trim_start_time': '0hr0m0s', 'compression': True, 'compression_preset': 'Moderate (balanced)', ...}
        
        We need to convert enabled flags to {tool}_enabled format for consistent internal storage.
        """
        converted = {}
        
        # Top-level tool enable flags that need _enabled suffix
        tool_keys = ['trim', 'silence_trim', 'sonic_scrubber', 'compression', 
                     'soft_clip', 'eq', 'normalize', 'fade', 'de_esser', 'stereo_to_mono']
        
        # Sub-flags that are checkboxes but not top-level enablers
        sub_flag_keys = ['silence_trim_start', 'silence_trim_end']
        
        for key, value in options.items():
            # Main tool enable flags get _enabled suffix
            if key in tool_keys and isinstance(value, bool):
                converted[f'{key}_enabled'] = value
            # Sub-flags stay as-is (they're parameters, not enable flags)
            else:
                converted[key] = value
        
        return converted
    
    def show_help(self):
        """Open the help dialog showing per-track audio configuration information."""
        try:
            help_dialog = HelpWindow(self, 'audio_processing')
            help_dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, 'Help Error', f'Could not open help:\n{str(e)}')
    
    def create_audio_controls(self):
        """
        Create the audio processing control widgets.
        These are reused for different tracks (contents updated on track change).
        """
        # Clear existing controls
        while self.audio_controls_widget.count() > 0:
            item = self.audio_controls_widget.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create all audio processing checkboxes and their settings
        # We'll store references to controls for later retrieval
        self.audio_controls = {}
        
        # Tool 1: Audio Trimmer
        trim_cb = QCheckBox('[1] Audio Trimmer - Precise start/end time control')
        trim_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        trim_cb.setToolTip('Remove unwanted sections from start/end of track. Example: Remove intro/outro. Only use for full files, not segment splits.')
        self.audio_controls['trim'] = {'checkbox': trim_cb}
        self.audio_controls_widget.addWidget(trim_cb)
        
        trim_row = QHBoxLayout()
        trim_row.addSpacing(20)
        
        trim_start_label = QLabel('Start:')
        trim_start_label.setStyleSheet('color: #e6ecff;')
        trim_row.addWidget(trim_start_label)
        
        trim_start_time = QLineEdit('0hr0m0s')
        trim_start_time.setMaximumWidth(120)
        trim_start_time.setPlaceholderText('0hr0m0s')
        trim_start_time.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        trim_row.addWidget(trim_start_time)
        self.audio_controls['trim']['start_time'] = trim_start_time
        
        trim_end_label = QLabel('End:')
        trim_end_label.setStyleSheet('color: #e6ecff;')
        trim_row.addWidget(trim_end_label)
        
        trim_end_time = QLineEdit('0hr30m0s')
        trim_end_time.setMaximumWidth(120)
        trim_end_time.setPlaceholderText('0hr30m0s')
        trim_end_time.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        trim_row.addWidget(trim_end_time)
        self.audio_controls['trim']['end_time'] = trim_end_time
        trim_row.addStretch()
        
        self.audio_controls_widget.addLayout(trim_row)
        
        # Tool 2: Silence Trimming
        silence_trim_cb = QCheckBox('[2] Silence Trimming - Remove quiet padding at start/end')
        silence_trim_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        silence_trim_cb.setToolTip('Automatically removes quiet/blank sections. Good for live recordings with gaps. Disabled for split segments.')
        self.audio_controls['silence_trim'] = {'checkbox': silence_trim_cb}
        self.audio_controls_widget.addWidget(silence_trim_cb)
        
        # Trim Start
        silence_start_layout = QHBoxLayout()
        silence_start_layout.addSpacing(20)
        
        silence_trim_start_cb = QCheckBox('Trim Start')
        silence_trim_start_cb.setChecked(True)
        silence_trim_start_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        silence_start_layout.addWidget(silence_trim_start_cb)
        self.audio_controls['silence_trim']['trim_start_cb'] = silence_trim_start_cb
        
        start_threshold_label = QLabel('Threshold:')
        start_threshold_label.setStyleSheet('color: #e6ecff; padding-left: 8px;')
        silence_start_layout.addWidget(start_threshold_label)
        
        silence_threshold_start = QComboBox()
        silence_threshold_start.addItems(['-80dB (silent)', '-70dB', '-60dB (default)', '-50dB', '-40dB (aggressive)'])
        silence_threshold_start.setCurrentIndex(2)
        silence_threshold_start.setMaximumWidth(180)
        silence_threshold_start.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 2px;')
        silence_start_layout.addWidget(silence_threshold_start)
        self.audio_controls['silence_trim']['threshold_start'] = silence_threshold_start
        
        start_duration_label = QLabel('Duration:')
        start_duration_label.setStyleSheet('color: #e6ecff; padding-left: 8px;')
        silence_start_layout.addWidget(start_duration_label)
        
        silence_duration_start = QLineEdit('0.1')
        silence_duration_start.setMaximumWidth(80)
        silence_duration_start.setPlaceholderText('0.1')
        silence_duration_start.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        silence_start_layout.addWidget(silence_duration_start)
        self.audio_controls['silence_trim']['duration_start'] = silence_duration_start
        
        start_duration_note = QLabel('sec')
        start_duration_note.setStyleSheet('color: #888888;')
        silence_start_layout.addWidget(start_duration_note)
        silence_start_layout.addStretch()
        
        self.audio_controls_widget.addLayout(silence_start_layout)
        
        # Trim End
        silence_end_layout = QHBoxLayout()
        silence_end_layout.addSpacing(20)
        
        silence_trim_end_cb = QCheckBox('Trim End')
        silence_trim_end_cb.setChecked(True)
        silence_trim_end_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        silence_end_layout.addWidget(silence_trim_end_cb)
        self.audio_controls['silence_trim']['trim_end_cb'] = silence_trim_end_cb
        
        end_threshold_label = QLabel('Threshold:')
        end_threshold_label.setStyleSheet('color: #e6ecff; padding-left: 8px;')
        silence_end_layout.addWidget(end_threshold_label)
        
        silence_threshold_end = QComboBox()
        silence_threshold_end.addItems(['-80dB (silent)', '-70dB', '-60dB (default)', '-50dB', '-40dB (aggressive)'])
        silence_threshold_end.setCurrentIndex(2)
        silence_threshold_end.setMaximumWidth(180)
        silence_threshold_end.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 2px;')
        silence_end_layout.addWidget(silence_threshold_end)
        self.audio_controls['silence_trim']['threshold_end'] = silence_threshold_end
        
        end_duration_label = QLabel('Duration:')
        end_duration_label.setStyleSheet('color: #e6ecff; padding-left: 8px;')
        silence_end_layout.addWidget(end_duration_label)
        
        silence_duration_end = QLineEdit('0.1')
        silence_duration_end.setMaximumWidth(80)
        silence_duration_end.setPlaceholderText('0.1')
        silence_duration_end.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        silence_end_layout.addWidget(silence_duration_end)
        self.audio_controls['silence_trim']['duration_end'] = silence_duration_end
        
        end_duration_note = QLabel('sec')
        end_duration_note.setStyleSheet('color: #888888;')
        silence_end_layout.addWidget(end_duration_note)
        silence_end_layout.addStretch()
        
        self.audio_controls_widget.addLayout(silence_end_layout)
        
        # Tool 3: Sonic Scrubber
        sonic_scrubber_cb = QCheckBox('[3] Sonic Scrubber - Audio cleaning (remove rumble & hiss)')
        sonic_scrubber_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        sonic_scrubber_cb.setToolTip('Removes low rumble (<20Hz) and high hiss (>15kHz). Makes audio cleaner. Safe to use always.')
        self.audio_controls['sonic_scrubber'] = {'checkbox': sonic_scrubber_cb}
        self.audio_controls_widget.addWidget(sonic_scrubber_cb)
        
        # Tool 4: Compression
        compression_row = QHBoxLayout()
        compression_cb = QCheckBox('[4] Compression - Balance loud/quiet volumes')
        compression_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        compression_cb.setToolTip('Works best for vocal/acoustic. Electronic, techno, metal may lose character.')
        self.audio_controls['compression'] = {'checkbox': compression_cb}
        
        compression_preset = QComboBox()
        compression_preset.addItems(['Gentle (subtle)', 'Moderate (balanced)', 'Aggressive (strong)'])
        compression_preset.setCurrentIndex(1)
        compression_preset.setMaximumWidth(200)
        compression_preset.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 2px;')
        self.audio_controls['compression']['preset'] = compression_preset
        
        compression_row.addWidget(compression_cb)
        compression_row.addWidget(compression_preset)
        compression_row.addStretch()
        self.audio_controls_widget.addLayout(compression_row)
        
        # Tool 5: Soft Clipping
        soft_clip_cb = QCheckBox('[5] Soft Clipping/Limiting - Prevent harsh peak clipping')
        soft_clip_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        soft_clip_cb.setToolTip('Protects against harsh digital clipping. Limits peaks to safe levels. Always recommended when using compression/EQ.')
        self.audio_controls['soft_clip'] = {'checkbox': soft_clip_cb}
        self.audio_controls_widget.addWidget(soft_clip_cb)
        
        # Tool 6: EQ
        eq_row = QHBoxLayout()
        eq_cb = QCheckBox('[6] 3-Band EQ - Tone shaping (bass/mid/treble)')
        eq_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        eq_cb.setToolTip('Adjusts frequency response. Warm=bass boost, Bright=treble boost, Dark=treble cut. Use to match game aesthetic.')
        self.audio_controls['eq'] = {'checkbox': eq_cb}
        
        eq_preset = QComboBox()
        eq_preset.addItems(['Warm (bass-heavy)', 'Bright (crisp)', 'Dark (smooth)'])
        eq_preset.setMaximumWidth(200)
        eq_preset.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 2px;')
        self.audio_controls['eq']['preset'] = eq_preset
        
        eq_row.addWidget(eq_cb)
        eq_row.addWidget(eq_preset)
        eq_row.addStretch()
        self.audio_controls_widget.addLayout(eq_row)
        
        # Tool 7: Normalization
        normalize_cb = QCheckBox('[7] Audio Normalization - Consistent loudness levels')
        normalize_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        normalize_cb.setToolTip('Makes all tracks the same perceived loudness. Prevents needing volume adjustment in-game. Highly recommended.')
        self.audio_controls['normalize'] = {'checkbox': normalize_cb}
        self.audio_controls_widget.addWidget(normalize_cb)
        
        # Tool 8: Fade In/Out
        # Add checkbox first (on its own line)
        fade_cb = QCheckBox('[8] Fade In/Out - Smooth entry/exit')
        fade_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        fade_cb.setToolTip('Gradual volume in at start and out at end. Prevents clicks/pops. Standard for music mod tracks. ALWAYS recommended.')
        self.audio_controls['fade'] = {'checkbox': fade_cb}
        self.audio_controls_widget.addWidget(fade_cb)
        
        # Fade In controls on a separate indented row
        fade_in_row = QHBoxLayout()
        fade_in_row.addSpacing(20)  # Indent to show it's a sub-control
        
        fade_in_label = QLabel('Fade In Duration:')
        fade_in_label.setStyleSheet('color: #e6ecff;')
        fade_in_row.addWidget(fade_in_label)
        
        fade_in_time = QLineEdit('0hr0m0.5s')
        fade_in_time.setMaximumWidth(120)
        fade_in_time.setPlaceholderText('0hr0m0.5s')
        fade_in_time.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        fade_in_row.addWidget(fade_in_time)
        self.audio_controls['fade']['fade_in_duration'] = fade_in_time
        
        fade_in_row.addStretch()
        self.audio_controls_widget.addLayout(fade_in_row)
        
        # Fade Out controls - Simple "seconds from end" approach
        fade_out_row = QHBoxLayout()
        fade_out_row.addSpacing(20)  # Indent to show it's a sub-control
        
        fade_out_from_end_label = QLabel('Fade out in last:')
        fade_out_from_end_label.setStyleSheet('color: #e6ecff;')
        fade_out_row.addWidget(fade_out_from_end_label)
        
        fade_out_from_end_time = QLineEdit('0hr0m5s')
        fade_out_from_end_time.setMaximumWidth(120)
        fade_out_from_end_time.setPlaceholderText('0hr0m5s')
        fade_out_from_end_time.setToolTip('How many seconds from end of track to start fading? Example: "5s" = fade last 5 seconds')
        fade_out_from_end_time.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        fade_out_row.addWidget(fade_out_from_end_time)
        self.audio_controls['fade']['fade_out_from_end'] = fade_out_from_end_time
        
        fade_out_row.addStretch()
        self.audio_controls_widget.addLayout(fade_out_row)
        
        # Tool 9: De-Esser
        deesser_cb = QCheckBox('[9] De-Esser - Tame harsh S/T sounds (sibilance)')
        deesser_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        deesser_cb.setToolTip('Reduces harsh sibilance (S/T sounds in vocals). Use only if vocals sound too sharp/piercing. Skip for instrumental.')
        self.audio_controls['de_esser'] = {'checkbox': deesser_cb}
        self.audio_controls_widget.addWidget(deesser_cb)
        
        # Tool 10: Stereo to Mono
        stereo_mono_cb = QCheckBox('[10] Stereo to Mono - Convert stereo to single channel')
        stereo_mono_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        stereo_mono_cb.setToolTip('Converts stereo (L/R channels) to mono (center). Use if file is mono or to simplify. Most music stays stereo.')
        self.audio_controls['stereo_mono'] = {'checkbox': stereo_mono_cb}
        self.audio_controls_widget.addWidget(stereo_mono_cb)
        
        # Add stretch to push controls to top
        self.audio_controls_widget.addStretch()
    
    def _update_track_name_display(self):
        """Update the label showing the current track being edited."""
        if self.current_track_index < len(self.audio_files):
            current_file = self.audio_files[self.current_track_index]
            filename = os.path.basename(current_file)
            self.track_name_label.setText(f'Now editing: {filename}')
    
    def on_track_selected(self):
        """
        Handle track selection change.
        Load and display settings for the selected track.
        """
        current_item = self.track_list_widget.currentItem()
        if current_item is None:
            return
        
        # Save current track settings before switching
        self.save_current_track_settings()
        
        # Get new track index from UserRole data (not from row number, which includes headers/separators)
        index_data = current_item.data(Qt.UserRole)
        if index_data is None:
            # Item doesn't have UserRole (e.g., it's a parent header or separator)
            # Don't change the current track
            return
        
        self.current_track_index = index_data
        current_file_path = self.audio_files[self.current_track_index]
        
        # Load settings for this track
        self.load_track_settings(current_file_path)
        
        # Update display to show current track name
        self._update_track_name_display()
    
    def save_current_track_settings(self):
        """
        Save the current audio control values to the per-track settings dict.
        Converts internal control keys back to audio_processing_dialog format.
        """
        if self.current_track_index >= len(self.audio_files):
            return
        
        current_file_path = self.audio_files[self.current_track_index]
        
        # Extract all control values
        settings = {}
        
        for tool_name, controls in self.audio_controls.items():
            if 'checkbox' in controls:
                settings[f'{tool_name}_enabled'] = controls['checkbox'].isChecked()
            
            # Save individual control values
            for control_key, control_widget in controls.items():
                if control_key == 'checkbox':
                    continue
                
                # Map internal control keys back to audio_processing_dialog format
                # silence_trim['trim_start_cb'] → 'silence_trim_start' in settings
                # silence_trim['threshold_start'] → 'silence_threshold_start' in settings
                # compression['preset'] → 'compression_preset' in settings
                
                if tool_name == 'silence_trim' and control_key == 'trim_start_cb':
                    setting_key = 'silence_trim_start'
                elif tool_name == 'silence_trim' and control_key == 'trim_end_cb':
                    setting_key = 'silence_trim_end'
                elif tool_name == 'silence_trim' and control_key == 'threshold_start':
                    setting_key = 'silence_threshold_start'
                elif tool_name == 'silence_trim' and control_key == 'threshold_end':
                    setting_key = 'silence_threshold_end'
                elif tool_name == 'silence_trim' and control_key == 'duration_start':
                    setting_key = 'silence_duration_start'
                elif tool_name == 'silence_trim' and control_key == 'duration_end':
                    setting_key = 'silence_duration_end'
                elif tool_name == 'trim' and control_key == 'start_time':
                    setting_key = 'trim_start_time'
                elif tool_name == 'trim' and control_key == 'end_time':
                    setting_key = 'trim_end_time'
                elif tool_name == 'fade' and control_key == 'fade_in_duration':
                    setting_key = 'fade_in_duration'
                elif tool_name == 'fade' and control_key == 'fade_out_from_end':
                    # Simple: Just store the fade_out_duration value directly
                    # No need for FFmpeg duration calculation on this config screen
                    setting_key = 'fade_out_duration'
                    if isinstance(control_widget, QLineEdit):
                        settings[setting_key] = control_widget.text()
                    continue  # Skip normal setting
                elif tool_name == 'fade' and control_key == 'fade_out_duration':
                    setting_key = 'fade_out_duration'
                elif control_key == 'preset':
                    setting_key = f'{tool_name}_preset'
                else:
                    # Default: tool_name + control_key
                    setting_key = f'{tool_name}_{control_key}'
                
                if isinstance(control_widget, QLineEdit):
                    settings[setting_key] = control_widget.text()
                elif isinstance(control_widget, QComboBox):
                    settings[setting_key] = control_widget.currentText()
                elif isinstance(control_widget, QCheckBox):
                    settings[setting_key] = control_widget.isChecked()
        
        self.per_track_settings[current_file_path] = settings
    
    def load_track_settings(self, file_path):
        """
        Load and display settings for a specific track.
        Converts from audio_processing_dialog format to internal control format.
        """
        settings = self.per_track_settings.get(file_path, {})
        
        # Load all control values from settings
        for tool_name, controls in self.audio_controls.items():
            if 'checkbox' in controls:
                enabled_key = f'{tool_name}_enabled'
                is_enabled = settings.get(enabled_key, False)
                controls['checkbox'].setChecked(is_enabled)
            
            # Load individual control values
            for control_key, control_widget in controls.items():
                if control_key == 'checkbox':
                    continue
                
                # Map from audio_processing_dialog keys to our control keys
                if tool_name == 'silence_trim' and control_key == 'trim_start_cb':
                    setting_key = 'silence_trim_start'
                elif tool_name == 'silence_trim' and control_key == 'trim_end_cb':
                    setting_key = 'silence_trim_end'
                elif tool_name == 'silence_trim' and control_key == 'threshold_start':
                    setting_key = 'silence_threshold_start'
                elif tool_name == 'silence_trim' and control_key == 'threshold_end':
                    setting_key = 'silence_threshold_end'
                elif tool_name == 'silence_trim' and control_key == 'duration_start':
                    setting_key = 'silence_duration_start'
                elif tool_name == 'silence_trim' and control_key == 'duration_end':
                    setting_key = 'silence_duration_end'
                elif tool_name == 'trim' and control_key == 'start_time':
                    setting_key = 'trim_start_time'
                elif tool_name == 'trim' and control_key == 'end_time':
                    setting_key = 'trim_end_time'
                elif tool_name == 'fade' and control_key == 'fade_in_duration':
                    setting_key = 'fade_in_duration'
                elif tool_name == 'fade' and control_key == 'fade_out_from_end':
                    # Simple: Just load and display the fade_out_duration value directly
                    # No need for FFmpeg duration calculation on this config screen
                    setting_key = 'fade_out_duration'
                    fade_out_duration_value = settings.get(setting_key)
                    if fade_out_duration_value is not None:
                        control_widget.setText(str(fade_out_duration_value))
                    else:
                        control_widget.setText(control_widget.placeholderText())
                    continue  # Skip normal loading
                elif tool_name == 'fade' and control_key == 'fade_out_duration':
                    setting_key = 'fade_out_duration'
                elif control_key == 'preset':
                    setting_key = f'{tool_name}_preset'
                else:
                    # Default: tool_name + control_key
                    setting_key = f'{tool_name}_{control_key}'
                
                if isinstance(control_widget, QLineEdit):
                    control_widget.setText(settings.get(setting_key, control_widget.placeholderText()))
                elif isinstance(control_widget, QComboBox):
                    saved_value = settings.get(setting_key, '')
                    if saved_value:
                        index = control_widget.findText(saved_value)
                        if index >= 0:
                            control_widget.setCurrentIndex(index)
                elif isinstance(control_widget, QCheckBox):
                    control_widget.setChecked(settings.get(setting_key, False))
    
    def apply_current_to_all(self):
        """
        Apply current track's settings to all other tracks.
        """
        # Save current settings first
        self.save_current_track_settings()
        
        current_file_path = self.audio_files[self.current_track_index]
        current_settings = self.per_track_settings[current_file_path].copy()
        
        # Apply to all tracks
        for file_path in self.audio_files:
            self.per_track_settings[file_path] = current_settings.copy()
        
        # Show confirmation
        QMessageBox.information(self, 'Applied', 
            f'✓ Applied current track settings to all {len(self.audio_files)} track(s)!')
    
    def apply_preset_to_current(self, preset_id):
        """
        Apply a genre preset to the currently selected track.
        
        Presets include:
        - lofi: Minimal processing (normalization + fade only)
        - orchestral: Full processing (all tools on, moderate compression)
        - electronic: EQ + soft clip only (NO compression to avoid blown-out sound)
        - ambient: Minimal processing (normalization + fade only)
        - metal: Aggressive (compression + EQ + de-esser)
        - acoustic: Warm EQ only (NO compression to preserve dynamics)
        - pop: Bright EQ only (NO compression for modern sound)
        - none: All tools OFF
        - all: Full processing (all tools on)
        """
        # Preset configurations (matching audio_processing_dialog.py)
        presets = {
            'lofi': {
                'trim_enabled': False,
                'silence_trim_enabled': False,
                'sonic_scrubber_enabled': False,
                'compression_enabled': False,
                'soft_clip_enabled': False,
                'eq_enabled': False,
                'de_esser_enabled': False,
                'normalize_enabled': True,
                'stereo_to_mono_enabled': False,
                'fade_enabled': True,
                'eq_preset': 'Warm (bass-heavy)',
                'compression_preset': 'Gentle (subtle)',
            },
            'orchestral': {
                'trim_enabled': False,
                'silence_trim_enabled': True,
                'sonic_scrubber_enabled': True,
                'compression_enabled': True,
                'soft_clip_enabled': True,
                'eq_enabled': True,
                'de_esser_enabled': True,
                'normalize_enabled': True,
                'stereo_to_mono_enabled': False,
                'fade_enabled': True,
                'eq_preset': 'Dark (treble-heavy warmth)',
                'compression_preset': 'Moderate (balanced)',
            },
            'electronic': {
                'trim_enabled': False,
                'silence_trim_enabled': False,
                'sonic_scrubber_enabled': False,
                'compression_enabled': False,
                'soft_clip_enabled': True,
                'eq_enabled': True,
                'de_esser_enabled': False,
                'normalize_enabled': True,
                'stereo_to_mono_enabled': False,
                'fade_enabled': True,
                'eq_preset': 'Bright (treble-boost)',
                'compression_preset': 'Gentle (subtle)',
            },
            'ambient': {
                'trim_enabled': False,
                'silence_trim_enabled': False,
                'sonic_scrubber_enabled': False,
                'compression_enabled': False,
                'soft_clip_enabled': False,
                'eq_enabled': False,
                'de_esser_enabled': False,
                'normalize_enabled': True,
                'stereo_to_mono_enabled': False,
                'fade_enabled': True,
                'eq_preset': 'Warm (bass-heavy)',
                'compression_preset': 'Gentle (subtle)',
            },
            'metal': {
                'trim_enabled': False,
                'silence_trim_enabled': False,
                'sonic_scrubber_enabled': True,
                'compression_enabled': True,
                'soft_clip_enabled': True,
                'eq_enabled': True,
                'de_esser_enabled': True,
                'normalize_enabled': True,
                'stereo_to_mono_enabled': False,
                'fade_enabled': True,
                'eq_preset': 'Bright (treble-boost)',
                'compression_preset': 'Aggressive (strong)',
            },
            'acoustic': {
                'trim_enabled': False,
                'silence_trim_enabled': False,
                'sonic_scrubber_enabled': False,
                'compression_enabled': False,
                'soft_clip_enabled': False,
                'eq_enabled': True,
                'de_esser_enabled': False,
                'normalize_enabled': True,
                'stereo_to_mono_enabled': False,
                'fade_enabled': True,
                'eq_preset': 'Warm (bass-heavy)',
                'compression_preset': 'Gentle (subtle)',
            },
            'pop': {
                'trim_enabled': False,
                'silence_trim_enabled': False,
                'sonic_scrubber_enabled': False,
                'compression_enabled': False,
                'soft_clip_enabled': False,
                'eq_enabled': True,
                'de_esser_enabled': False,
                'normalize_enabled': True,
                'stereo_to_mono_enabled': False,
                'fade_enabled': True,
                'eq_preset': 'Bright (treble-boost)',
                'compression_preset': 'Gentle (subtle)',
            },
            'none': {
                'trim_enabled': False,
                'silence_trim_enabled': False,
                'sonic_scrubber_enabled': False,
                'compression_enabled': False,
                'soft_clip_enabled': False,
                'eq_enabled': False,
                'de_esser_enabled': False,
                'normalize_enabled': False,
                'stereo_to_mono_enabled': False,
                'fade_enabled': False,
                'eq_preset': 'Warm (bass-heavy)',
                'compression_preset': 'Gentle (subtle)',
            },
            'all': {
                'trim_enabled': False,
                'silence_trim_enabled': True,
                'sonic_scrubber_enabled': True,
                'compression_enabled': True,
                'soft_clip_enabled': True,
                'eq_enabled': True,
                'de_esser_enabled': True,
                'normalize_enabled': True,
                'stereo_to_mono_enabled': False,
                'fade_enabled': True,
                'eq_preset': 'Bright (treble-boost)',
                'compression_preset': 'Moderate (balanced)',
            },
        }
        
        preset_config = presets.get(preset_id, {})
        current_file_path = self.audio_files[self.current_track_index]
        
        # Apply preset to current track settings
        self.per_track_settings[current_file_path].update(preset_config)
        
        # Reload UI with preset settings
        self.load_track_settings(current_file_path)
    
    def reset_current_to_default(self):
        """
        Reset current track's settings to default.
        """
        current_file_path = self.audio_files[self.current_track_index]
        self.per_track_settings[current_file_path] = self.default_options.copy() if self.default_options else {}
        
        # Reload UI with default settings
        self.load_track_settings(current_file_path)
    
    def preview_current_track(self):
        """
        Play the currently selected track using the system's default audio player.
        """
        if self.current_track_index >= len(self.audio_files):
            QMessageBox.warning(self, 'Preview Error', 'No track selected.')
            return
        
        current_file_path = self.audio_files[self.current_track_index]
        
        # Verify file exists
        if not os.path.exists(current_file_path):
            QMessageBox.warning(self, 'Preview Error', f'File not found: {current_file_path}')
            return
        
        try:
            # Use system default player to preview
            if platform.system() == 'Windows':
                os.startfile(current_file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', current_file_path])
            else:  # Linux and other Unix-like systems
                subprocess.Popen(['xdg-open', current_file_path])
        except Exception as e:
            QMessageBox.warning(self, 'Preview Error', f'Could not open file: {str(e)}')
    
    def closeEvent(self, event):
        """
        Handle dialog close event (X button or keyboard shortcut).
        Clean up orphaned WAV files and temp directories from split operations.
        """
        # Clean up .wav files
        for wav_file in self.wav_files_to_clean:
            if os.path.exists(wav_file):
                try:
                    os.remove(wav_file)
                except Exception as e:
                    print(f'[CLEANUP] Failed to remove WAV file {wav_file}: {e}')
        
        # Clean up temp directories
        for temp_dir in self.temp_dirs_to_clean:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f'[CLEANUP] Failed to remove temp directory {temp_dir}: {e}')
        
        # Accept the close event
        event.accept()
    
    def get_per_track_settings(self):
        """
        Get the per-track audio processing settings.
        
        Returns:
            dict: {file_path: {audio_processing_options}}
        """
        # Save current track before returning
        self.save_current_track_settings()
        return self.per_track_settings
    
    def get_bitrate(self):
        """
        Get the selected OGG bitrate from the dropdown.
        
        Returns:
            str: Bitrate text (e.g., "192 kbps (default)")
        """
        return self.bitrate_combo.currentText()
