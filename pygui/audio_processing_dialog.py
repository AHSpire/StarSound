"""
Audio Processing Dialog Module
==============================

Provides a modal dialog window for configuring all audio processing tools.
Extracted from main GUI to reduce main window clutter and improve UX.

Tools Included:
1. Audio Trimmer - Precise start/end time control
2. Silence Trimming - Remove quiet padding at start/end
3. Sonic Scrubber - Audio cleaning (remove rumble & hiss)
4. Compression - Balance loud/quiet volumes
5. Soft Clipping/Limiting - Prevent harsh peak clipping
6. 3-Band EQ - Tone shaping (bass/mid/treble)
7. Audio Normalization - Consistent loudness levels
8. Fade In/Out - Smooth entry/exit
9. De-Esser - Tame harsh S/T sounds (sibilance)
10. Stereo to Mono - Convert stereo to single channel
"""

# For UI styling standards, see ../UI_STYLE_GUIDE.md

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QLineEdit, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt


class AudioProcessingDialog(QDialog):
    """
    Modal dialog for configuring audio processing options.
    
    This dialog provides access to all 10 audio processing tools with
    their respective controls and presets. It's designed to be modal
    (blocks main window until closed) and preserves all state until
    the user applies or cancels.
    """
    
    def __init__(self, parent=None):
        """
        Initialize the Audio Processing Dialog.
        
        Args:
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.setWindowTitle('🎛️ Audio Processing Configuration')
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        
        # See UI_STYLE_GUIDE.md for styling standards
        self.setStyleSheet('''
            QDialog {
                background-color: #1a1f2e;
            }
            QLabel {
                color: #e6ecff;
            }
        ''')
        
        # Store checkboxes for bulk operations
        self.audio_tools_checkboxes = {}
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Title
        title = QLabel('🎛️ Audio Processing Options')
        title.setStyleSheet('color: #00d4ff; font-size: 14px; font-weight: bold; margin-bottom: 8px;')
        main_layout.addWidget(title)
        
        # Subtitle: Explain this is a global preset
        subtitle = QLabel('💡 Global Preset: Configure default settings below. You can customize these per-track during conversion if needed.')
        subtitle.setStyleSheet('color: #888888; font-size: 11px; margin-bottom: 12px; font-style: italic;')
        main_layout.addWidget(subtitle)

        # Subtitle: 3rd Party Tools Suggestions
        tools_subtitle = QLabel('🔧 Tool Suggestions: For even more advanced audio processing, consider using third-party tools such as Audacity or Reaper!')
        tools_subtitle.setStyleSheet('color: #888888; font-size: 11px; margin-bottom: 12px; font-style: italic;')
        main_layout.addWidget(tools_subtitle)
        
        # ===== PRESET SYSTEM =====
        presets_label = QLabel('🎵 Quick Presets:')
        presets_label.setStyleSheet('color: #ffcc00; font-size: 11px; margin-top: 8px；')
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
            btn.clicked.connect(lambda checked, pid=preset_id: self.apply_preset(pid))
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
        
        # Select All / Deselect All buttons
        control_btn_row = QHBoxLayout()
        select_all_btn = QPushButton('✓ Select All')
        select_all_btn.setMaximumWidth(120)
        select_all_btn.setStyleSheet('background-color: #2d5a3d; color: #e6ecff; border-radius: 4px; padding: 4px 12px;')
        deselect_all_btn = QPushButton('✗ Deselect All')
        deselect_all_btn.setMaximumWidth(150)
        deselect_all_btn.setStyleSheet('background-color: #c41e3a; color: #e6ecff; border-radius: 4px; padding: 4px 12px; font-weight: bold;')
        control_btn_row.addWidget(select_all_btn)
        control_btn_row.addWidget(deselect_all_btn)
        control_btn_row.addStretch()
        main_layout.addLayout(control_btn_row)
        
        # Processing tools grid
        tools_grid = QGridLayout()
        tools_grid.setSpacing(8)
        tools_grid.setColumnStretch(1, 1)
        
        # Tool 1: Audio Trimmer
        trim_row = QHBoxLayout()
        self.trim_cb = QCheckBox('[1] Audio Trimmer - Precise start/end time control')
        self.trim_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        self.audio_tools_checkboxes['trim'] = self.trim_cb
        trim_row.addWidget(self.trim_cb)
        trim_start_label = QLabel('Start:')
        trim_start_label.setStyleSheet('color: #e6ecff;')
        trim_row.addWidget(trim_start_label)
        self.trim_start_time = QLineEdit('0hr0m0s')
        self.trim_start_time.setMaximumWidth(120)
        self.trim_start_time.setPlaceholderText('0hr0m0s')
        self.trim_start_time.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        trim_row.addWidget(self.trim_start_time)
        trim_end_label = QLabel('End:')
        trim_end_label.setStyleSheet('color: #e6ecff;')
        trim_row.addWidget(trim_end_label)
        self.trim_end_time = QLineEdit('0hr30m0s')
        self.trim_end_time.setMaximumWidth(120)
        self.trim_end_time.setPlaceholderText('0hr30m0s')
        self.trim_end_time.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        trim_row.addWidget(self.trim_end_time)
        trim_row.addStretch()
        tools_grid.addLayout(trim_row, 0, 0, 1, 2)
        
        # Tool 2: Silence Trimming
        self.silence_trim_cb = QCheckBox('[2] Silence Trimming - Remove quiet padding at start/end')
        self.silence_trim_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        self.audio_tools_checkboxes['silence_trim'] = self.silence_trim_cb
        tools_grid.addWidget(self.silence_trim_cb, 1, 0, 1, 2)
        
        # Silence Trimming settings row - Trim Start
        silence_start_layout = QHBoxLayout()
        silence_start_layout.addSpacing(20)  # Indent
        
        # Trim Start checkbox
        self.silence_trim_start_cb = QCheckBox('Trim Start')
        self.silence_trim_start_cb.setChecked(True)
        self.silence_trim_start_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        silence_start_layout.addWidget(self.silence_trim_start_cb)
        
        # Start threshold
        start_threshold_label = QLabel('Threshold:')
        start_threshold_label.setStyleSheet('color: #e6ecff; padding-left: 8px;')
        silence_start_layout.addWidget(start_threshold_label)
        self.silence_threshold_start = QComboBox()
        self.silence_threshold_start.addItems(['-80dB (silent)', '-70dB', '-60dB (default)', '-50dB', '-40dB (aggressive)'])
        self.silence_threshold_start.setCurrentIndex(2)
        self.silence_threshold_start.setMaximumWidth(180)
        self.silence_threshold_start.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 2px;')
        silence_start_layout.addWidget(self.silence_threshold_start)
        
        # Start duration
        start_duration_label = QLabel('Duration:')
        start_duration_label.setStyleSheet('color: #e6ecff; padding-left: 8px;')
        silence_start_layout.addWidget(start_duration_label)
        self.silence_duration_start = QLineEdit('0.1')
        self.silence_duration_start.setMaximumWidth(80)
        self.silence_duration_start.setPlaceholderText('0.1')
        self.silence_duration_start.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        silence_start_layout.addWidget(self.silence_duration_start)
        
        start_duration_note = QLabel('sec')
        start_duration_note.setStyleSheet('color: #888888;')
        silence_start_layout.addWidget(start_duration_note)
        silence_start_layout.addStretch()
        
        tools_grid.addLayout(silence_start_layout, 2, 0, 1, 2)
        
        # Silence Trimming settings row - Trim End
        silence_end_layout = QHBoxLayout()
        silence_end_layout.addSpacing(20)  # Indent
        
        # Trim End checkbox
        self.silence_trim_end_cb = QCheckBox('Trim End')
        self.silence_trim_end_cb.setChecked(True)
        self.silence_trim_end_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        silence_end_layout.addWidget(self.silence_trim_end_cb)
        
        # End threshold
        end_threshold_label = QLabel('Threshold:')
        end_threshold_label.setStyleSheet('color: #e6ecff; padding-left: 8px;')
        silence_end_layout.addWidget(end_threshold_label)
        self.silence_threshold_end = QComboBox()
        self.silence_threshold_end.addItems(['-80dB (silent)', '-70dB', '-60dB (default)', '-50dB', '-40dB (aggressive)'])
        self.silence_threshold_end.setCurrentIndex(2)
        self.silence_threshold_end.setMaximumWidth(180)
        self.silence_threshold_end.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 2px;')
        silence_end_layout.addWidget(self.silence_threshold_end)
        
        # End duration
        end_duration_label = QLabel('Duration:')
        end_duration_label.setStyleSheet('color: #e6ecff; padding-left: 8px;')
        silence_end_layout.addWidget(end_duration_label)
        self.silence_duration_end = QLineEdit('0.1')
        self.silence_duration_end.setMaximumWidth(80)
        self.silence_duration_end.setPlaceholderText('0.1')
        self.silence_duration_end.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        silence_end_layout.addWidget(self.silence_duration_end)
        
        end_duration_note = QLabel('sec')
        end_duration_note.setStyleSheet('color: #888888;')
        silence_end_layout.addWidget(end_duration_note)
        silence_end_layout.addStretch()
        
        tools_grid.addLayout(silence_end_layout, 3, 0, 1, 2)
        
        # Tool 3: Sonic Scrubber
        self.sonic_scrubber_cb = QCheckBox('[3] Sonic Scrubber - Audio cleaning (remove rumble & hiss)')
        self.sonic_scrubber_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        self.audio_tools_checkboxes['sonic_scrubber'] = self.sonic_scrubber_cb
        tools_grid.addWidget(self.sonic_scrubber_cb, 4, 0, 1, 2)
        
        # Tool 4: Compression
        compression_row = QHBoxLayout()
        self.compression_cb = QCheckBox('[4] Compression - Balance loud/quiet volumes')
        self.compression_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        self.compression_cb.setToolTip('Works best for vocal/acoustic music. Electronic, techno, and metal genres may lose character.\nConsider disabling for these genres.')
        self.audio_tools_checkboxes['compression'] = self.compression_cb
        self.compression_preset = QComboBox()
        self.compression_preset.addItems(['Gentle (subtle)', 'Moderate (balanced)', 'Aggressive (strong)'])
        self.compression_preset.setCurrentIndex(1)  # Default to Moderate (matches vanilla)
        self.compression_preset.setMaximumWidth(200)
        self.compression_preset.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 2px;')
        compression_row.addWidget(self.compression_cb)
        compression_row.addWidget(self.compression_preset)
        compression_row.addStretch()
        tools_grid.addLayout(compression_row, 5, 0, 1, 2)
        
        # Tool 5: Soft Clipping / Limiting
        self.soft_clip_cb = QCheckBox('[5] Soft Clipping/Limiting - Prevent harsh peak clipping')
        self.soft_clip_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        self.audio_tools_checkboxes['soft_clip'] = self.soft_clip_cb
        tools_grid.addWidget(self.soft_clip_cb, 6, 0, 1, 2)
        
        # Tool 6: EQ
        eq_row = QHBoxLayout()
        self.eq_cb = QCheckBox('[6] 3-Band EQ - Tone shaping (bass/mid/treble)')
        self.eq_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        self.audio_tools_checkboxes['eq'] = self.eq_cb
        self.eq_preset = QComboBox()
        self.eq_preset.addItems(['Warm (bass-heavy)', 'Bright (crisp)', 'Dark (smooth)'])
        self.eq_preset.setMaximumWidth(200)
        self.eq_preset.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 2px;')
        eq_row.addWidget(self.eq_cb)
        eq_row.addWidget(self.eq_preset)
        eq_row.addStretch()
        tools_grid.addLayout(eq_row, 7, 0, 1, 2)
        
        # Tool 7: Normalization
        self.normalize_cb = QCheckBox('[7] Audio Normalization - Consistent loudness levels')
        self.normalize_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        self.audio_tools_checkboxes['normalize'] = self.normalize_cb
        tools_grid.addWidget(self.normalize_cb, 8, 0, 1, 2)
        
        # Tool 8: Fade In/Out
        fade_in_row = QHBoxLayout()
        self.fade_cb = QCheckBox('[8] Fade In/Out - Smooth entry/exit')
        self.fade_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        self.audio_tools_checkboxes['fade'] = self.fade_cb
        fade_in_row.addWidget(self.fade_cb)
        fade_in_label = QLabel('Fade In Duration:')
        fade_in_label.setStyleSheet('color: #e6ecff;')
        fade_in_row.addWidget(fade_in_label)
        self.fade_in_duration = QLineEdit('0hr0m0.5s')
        self.fade_in_duration.setMaximumWidth(120)
        self.fade_in_duration.setPlaceholderText('0hr0m0.5s')
        self.fade_in_duration.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        fade_in_row.addWidget(self.fade_in_duration)
        fade_in_row.addStretch()
        tools_grid.addLayout(fade_in_row, 9, 0, 1, 2)
        
        # Fade Out Start and Duration
        fade_out_row = QHBoxLayout()
        fade_out_row.addSpacing(20)  # Indent
        fade_out_info_label = QLabel('Fade out in last:')
        fade_out_info_label.setStyleSheet('color: #e6ecff;')
        fade_out_row.addWidget(fade_out_info_label)
        self.fade_out_duration = QLineEdit('0hr0m5s')
        self.fade_out_duration.setMaximumWidth(120)
        self.fade_out_duration.setPlaceholderText('0hr0m5s')
        self.fade_out_duration.setToolTip('How many seconds from the end to start fading? Example: "5s" = fade last 5 seconds. (Applied per-track with actual track lengths)')
        self.fade_out_duration.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
        fade_out_row.addWidget(self.fade_out_duration)
        fade_out_row.addStretch()
        tools_grid.addLayout(fade_out_row, 10, 0, 1, 2)
        
        # Tool 9: De-Esser
        self.de_esser_cb = QCheckBox('[9] De-Esser - Tame harsh S/T sounds (sibilance)')
        self.de_esser_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        self.audio_tools_checkboxes['de_esser'] = self.de_esser_cb
        tools_grid.addWidget(self.de_esser_cb, 11, 0, 1, 2)
        
        # Tool 10: Stereo to Mono
        self.stereo_to_mono_cb = QCheckBox('[10] Stereo to Mono - Convert stereo to single channel')
        self.stereo_to_mono_cb.setStyleSheet('QCheckBox { color: #e6ecff; }')
        self.audio_tools_checkboxes['stereo_to_mono'] = self.stereo_to_mono_cb
        tools_grid.addWidget(self.stereo_to_mono_cb, 12, 0, 1, 2)
        
        main_layout.addLayout(tools_grid)
        
        # Connect Select All / Deselect All buttons
        select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in self.audio_tools_checkboxes.values()])
        deselect_all_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in self.audio_tools_checkboxes.values()])
        
        # Match Vanilla preset button
        match_vanilla_btn = QPushButton('🎵 Match Vanilla Profile')
        match_vanilla_btn.setStyleSheet('background-color: #3a5a4a; color: #00d4ff; border-radius: 4px; padding: 6px 16px; font-weight: bold;')
        match_vanilla_btn.setToolTip('One-click setup: Enable optimal settings to match vanilla Starbound music')
        match_vanilla_btn.clicked.connect(self.apply_match_vanilla_preset)
        main_layout.addWidget(match_vanilla_btn)
        
        # Buttons at bottom
        button_row = QHBoxLayout()
        apply_btn = QPushButton('✓ Apply')
        apply_btn.setStyleSheet('background-color: #2d5a3d; color: #e6ecff; border-radius: 4px; padding: 6px 16px; font-weight: bold;')
        apply_btn.clicked.connect(self.on_apply_clicked)
        
        cancel_btn = QPushButton('✗ Cancel')
        cancel_btn.setStyleSheet('background-color: #c41e3a; color: #e6ecff; border-radius: 4px; padding: 6px 16px; font-weight: bold;')
        cancel_btn.clicked.connect(self.reject)
        
        button_row.addStretch()
        button_row.addWidget(apply_btn)
        button_row.addWidget(cancel_btn)
        button_row.addStretch()
        
        main_layout.addLayout(button_row)
    
    def apply_match_vanilla_preset(self):
        """
        Apply optimal settings to match vanilla Starbound music characteristics.
        Based on analysis: 160 kbps, 44.1 kHz, stereo, Moderate compression, Warm EQ, EBU R128 normalization.
        """
        # Disable all tools first
        for cb in self.audio_tools_checkboxes.values():
            cb.setChecked(False)
        
        # Enable optimal tools for vanilla matching
        self.trim_cb.setChecked(True)                    # [1] Clean up edges
        self.silence_trim_cb.setChecked(True)            # [2] Remove DC offset
        self.sonic_scrubber_cb.setChecked(True)          # [3] Clean audio
        self.compression_cb.setChecked(True)             # [4] Controlled dynamics
        self.soft_clip_cb.setChecked(True)               # [5] Prevent clipping
        self.eq_cb.setChecked(True)                      # [6] Tone match
        self.normalize_cb.setChecked(True)               # [7] Loudness normalization
        self.fade_cb.setChecked(True)                    # [8] Smooth edges
        # [9] De-esser disabled (vanilla already clean)
        # [10] Stereo to Mono disabled (keep stereo)
        
        # Set optimal preset values
        self.compression_preset.setCurrentIndex(1)       # Moderate compression
        self.eq_preset.setCurrentIndex(0)                # Warm EQ
        
        # Show confirmation
        QMessageBox.information(
            self,
            "Match Vanilla Preset Applied",
            "Optimal settings for vanilla-style music:\n\n"
            "✓ Audio Trimmer: Remove silent regions\n"
            "✓ Silence Trimming: Clean DC offset\n"
            "✓ Sonic Scrubber: Remove hum/hiss\n"
            "✓ Compression: Moderate (balanced dynamics)\n"
            "✓ Soft Clipping: Prevent harsh peaks\n"
            "✓ 3-Band EQ: Warm (bass-forward)\n"
            "✓ Normalization: EBU R128 loudness\n"
            "✓ Fade In/Out: 0.5s fade in, starts fade out at 25m\n\n"
            "Your music will sound native to Starbound!\n\n"
            "💡 TIP: If your music is electronic, techno, or metal, consider disabling\n"
            "Compression to preserve the intentional dynamics and character of your track."
        )
    
    def on_apply_clicked(self):
        """
        Handle Apply button click. Show confirmation dialog with enabled tools.
        """
        # Build list of enabled tools
        enabled_tools = []
        
        if self.trim_cb.isChecked():
            enabled_tools.append(f"[1] Audio Trimmer ({self.trim_start_time.text()} → {self.trim_end_time.text()})")
        
        if self.silence_trim_cb.isChecked():
            silence_parts = []
            if self.silence_trim_start_cb.isChecked():
                silence_parts.append(f"Start: {self.silence_threshold_start.currentText()}")
            if self.silence_trim_end_cb.isChecked():
                silence_parts.append(f"End: {self.silence_threshold_end.currentText()}")
            enabled_tools.append(f"[2] Silence Trimming ({', '.join(silence_parts)})")
        
        if self.sonic_scrubber_cb.isChecked():
            enabled_tools.append("[3] Sonic Scrubber (rumble & hiss removal)")
        
        if self.compression_cb.isChecked():
            enabled_tools.append(f"[4] Compression ({self.compression_preset.currentText()})")
        
        if self.soft_clip_cb.isChecked():
            enabled_tools.append("[5] Soft Clipping/Limiting")
        
        if self.eq_cb.isChecked():
            enabled_tools.append(f"[6] 3-Band EQ ({self.eq_preset.currentText()})")
        
        if self.normalize_cb.isChecked():
            enabled_tools.append("[7] Audio Normalization")
        
        if self.fade_cb.isChecked():
            enabled_tools.append(f"[8] Fade In/Out (In: {self.fade_in_duration.text()}, Out in last: {self.fade_out_duration.text()})")
        
        if self.de_esser_cb.isChecked():
            enabled_tools.append("[9] De-Esser (sibilance reduction)")
        
        if self.stereo_to_mono_cb.isChecked():
            enabled_tools.append("[10] Stereo to Mono")
        
        # Build confirmation message
        if enabled_tools:
            message = "Audio Processing Configuration Applied:\n\n" + "\n".join(enabled_tools)
            # Add warning if Compression is enabled
            if self.compression_cb.isChecked():
                message += "\n\n⚠️  COMPRESSION NOTE:\nCompression works best for vocals and acoustic music.\nElectronic, techno, and metal may lose their character.\nDisable it if you're processing these genres."
        else:
            message = "No audio processing tools enabled.\n\nYour audio will be converted without any effects."
        
        # Show confirmation
        QMessageBox.information(self, "Audio Processing Settings Applied", message)
        
        # Close the dialog
        self.accept()
    
    def apply_preset(self, preset_id: str):
        """
        Apply a genre-specific audio processing preset.
        
        Presets:
        - lofi: Minimal processing (just normalization + fade)
        - orchestral: Full processing for classical music
        - electronic: Moderate processing with compression
        - ambient: Minimal processing (preserve character)
        - metal: Aggressive compression + EQ
        - none: Disable all processing
        - all: Enable all processing (default)
        """
        presets = {
            'lofi': {
                'trim': False,
                'silence_trim': False,
                'sonic_scrubber': False,
                'compression': False,
                'soft_clip': False,
                'eq': False,
                'de_esser': False,
                'normalize': True,
                'stereo_to_mono': False,
                'fade': True,
            },
            'orchestral': {
                'trim': False,
                'silence_trim': True,
                'sonic_scrubber': True,
                'compression': True,
                'soft_clip': True,
                'eq': True,
                'de_esser': True,
                'normalize': True,
                'stereo_to_mono': False,
                'fade': True,
            },
            'electronic': {
                'trim': False,
                'silence_trim': False,
                'sonic_scrubber': False,
                'compression': False,  # ✗ NO compression (sounds blown out)
                'soft_clip': True,     # ✓ Light soft clip for safety
                'eq': True,            # ✓ Bright EQ for electronic
                'de_esser': False,
                'normalize': True,
                'stereo_to_mono': False,
                'fade': True,
            },
            'ambient': {
                'trim': False,
                'silence_trim': False,
                'sonic_scrubber': False,
                'compression': False,
                'soft_clip': False,
                'eq': False,
                'de_esser': False,
                'normalize': True,
                'stereo_to_mono': False,
                'fade': True,
            },
            'metal': {
                'trim': False,
                'silence_trim': False,
                'sonic_scrubber': True,
                'compression': True,
                'soft_clip': True,
                'eq': True,
                'de_esser': True,
                'normalize': True,
                'stereo_to_mono': False,
                'fade': True,
            },
            'acoustic': {
                'trim': False,
                'silence_trim': False,
                'sonic_scrubber': False,
                'compression': False,  # ✗ NO compression (preserve natural dynamics)
                'soft_clip': False,
                'eq': True,            # ✓ Warm EQ for acoustic instruments
                'de_esser': False,
                'normalize': True,
                'stereo_to_mono': False,
                'fade': True,
            },
            'pop': {
                'trim': False,
                'silence_trim': False,
                'sonic_scrubber': False,
                'compression': False,  # ✗ NO compression (avoid blown-out sound)
                'soft_clip': False,
                'eq': True,            # ✓ Bright EQ for pop
                'de_esser': False,
                'normalize': True,
                'stereo_to_mono': False,
                'fade': True,
            },
            'none': {
                'trim': False,
                'silence_trim': False,
                'sonic_scrubber': False,
                'compression': False,
                'soft_clip': False,
                'eq': False,
                'de_esser': False,
                'normalize': False,
                'stereo_to_mono': False,
                'fade': False,
            },
            'all': {
                'trim': False,
                'silence_trim': True,
                'sonic_scrubber': True,
                'compression': True,
                'soft_clip': True,
                'eq': True,
                'de_esser': True,
                'normalize': True,
                'stereo_to_mono': False,
                'fade': True,
            },
        }
        
        preset_config = presets.get(preset_id, {})
        
        # Apply preset settings to UI controls
        for tool_name, enabled in preset_config.items():
            if tool_name in self.audio_tools_checkboxes:
                self.audio_tools_checkboxes[tool_name].setChecked(enabled)
        
        # Set appropriate compression preset
        if hasattr(self, 'compression_preset'):
            if preset_id == 'orchestral':
                preset_name = 'Moderate (balanced)'
            elif preset_id == 'metal':
                preset_name = 'Aggressive (strong)'
            else:
                preset_name = 'Gentle (subtle)'
            index = self.compression_preset.findText(preset_name)
            if index >= 0:
                self.compression_preset.setCurrentIndex(index)
        
        # Set appropriate EQ preset
        if hasattr(self, 'eq_preset'):
            if preset_id == 'lofi':
                preset_name = 'Warm (bass-heavy)'  # Lo-fi loves bass
            elif preset_id == 'orchestral':
                preset_name = 'Dark (smooth)'  # Classical is smooth
            elif preset_id == 'electronic':
                preset_name = 'Bright (crisp)'  # Electronic loves brightness
            elif preset_id == 'ambient':
                preset_name = 'Dark (smooth)'  # Ambient is smooth
            elif preset_id == 'metal':
                preset_name = 'Bright (crisp)'  # Metal pierces
            elif preset_id == 'acoustic':
                preset_name = 'Warm (bass-heavy)'  # Acoustic is natural & warm
            elif preset_id == 'pop':
                preset_name = 'Bright (crisp)'  # Pop is punchy & bright
            else:
                preset_name = 'Warm (bass-heavy)'  # Default
            index = self.eq_preset.findText(preset_name)
            if index >= 0:
                self.eq_preset.setCurrentIndex(index)
    
    def get_audio_processing_options(self) -> dict:
        """
        Extract all audio processing settings from UI controls.
        
        Returns:
            dict: Audio processing options formatted for audio_utils.build_audio_filter_chain()
        """
        options = {
            # Tool 1: Audio Trimmer
            'trim': self.trim_cb.isChecked(),
            'trim_start_time': self.trim_start_time.text(),
            'trim_end_time': self.trim_end_time.text(),
            
            # Tool 2: Silence Trimming
            'silence_trim': self.silence_trim_cb.isChecked(),
            'silence_trim_start': self.silence_trim_start_cb.isChecked(),
            'silence_threshold_start': self.silence_threshold_start.currentText(),
            'silence_duration_start': self.silence_duration_start.text(),
            'silence_trim_end': self.silence_trim_end_cb.isChecked(),
            'silence_threshold_end': self.silence_threshold_end.currentText(),
            'silence_duration_end': self.silence_duration_end.text(),
            
            # Tool 3: Sonic Scrubber
            'sonic_scrubber': self.sonic_scrubber_cb.isChecked(),
            
            # Tool 4: Compression
            'compression': self.compression_cb.isChecked(),
            'compression_preset': self.compression_preset.currentText(),
            
            # Tool 5: Soft Clipping
            'soft_clip': self.soft_clip_cb.isChecked(),
            
            # Tool 6: EQ
            'eq': self.eq_cb.isChecked(),
            'eq_preset': self.eq_preset.currentText(),
            
            # Tool 7: Normalization
            'normalize': self.normalize_cb.isChecked(),
            
            # Tool 8: Fade In/Out
            'fade': self.fade_cb.isChecked(),
            'fade_in_duration': self.fade_in_duration.text(),
            'fade_out_duration': self.fade_out_duration.text(),
            
            # Tool 9: De-Esser
            'de_esser': self.de_esser_cb.isChecked(),
            
            # Tool 10: Stereo to Mono
            'stereo_to_mono': self.stereo_to_mono_cb.isChecked(),
            
            # OGG Bitrate
            'bitrate': self.bitrate_combo.currentText(),
        }
        
        return options
