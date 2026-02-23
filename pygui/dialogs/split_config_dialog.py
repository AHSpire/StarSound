"""
Split Configuration Dialog
===========================

Modal dialog allowing users to configure splitting algorithm parameters
before splitting long audio files.

Users can adjust segment length, preview segment count, etc.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpinBox, QSlider, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from dialogs.help_window import HelpWindow


class SplitConfigDialog(QDialog):
    """
    Modal dialog for configuring audio file splitting parameters.
    
    Allows users to set segment length before splitting begins.
    Shows preview of how many segments will be created.
    """
    
    def __init__(self, file_duration_minutes: float, parent=None):
        """
        Initialize split configuration dialog.
        
        Args:
            file_duration_minutes: Total duration of file in minutes
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.setWindowTitle('⚙️ Configure Splitting Algorithm')
        self.setModal(True)
        # Explicitly disable Windows help button hint
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(500)
        self.setMinimumHeight(320)
        
        # See UI_STYLE_GUIDE.md for styling standards
        self.setStyleSheet('''
            QDialog {
                background-color: #1a1f2e;
            }
            QLabel {
                color: #e6ecff;
            }
            QGroupBox {
                color: #e6ecff;
                border: 1px solid #3a4a6a;
                border-radius: 4px;
                padding-top: 8px;
                margin-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QSpinBox {
                background-color: #2a3a4a;
                color: #e6ecff;
                border: 1px solid #3a4a6a;
                border-radius: 3px;
                padding: 4px;
                selection-background-color: #00d4ff;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 18px;
            }
            QSlider::groove:horizontal {
                background-color: #3a4a6a;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #00d4ff;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 1px solid #008899;
            }
            QSlider::handle:horizontal:hover {
                background-color: #00f4ff;
            }
            QSlider::sub-page:horizontal {
                background-color: #00d4ff;
                border-radius: 3px;
            }
        ''')
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel('⚙️ Configure Audio File Splitting')
        title.setStyleSheet('color: #00d4ff; font-size: 14px; font-weight: bold;')
        main_layout.addWidget(title)
        
        # File info
        file_info_layout = QVBoxLayout()
        file_info_layout.setSpacing(4)
        
        file_duration_label = QLabel(
            f'📁 File Duration: <span style="color: #ffcc00; font-weight: bold;">'
            f'{file_duration_minutes:.1f} minutes</span>'
        )
        file_duration_label.setStyleSheet('color: #b8c5d6; font-size: 11px;')
        file_info_layout.addWidget(file_duration_label)
        
        main_layout.addLayout(file_info_layout)
        
        # Configuration group
        config_group = QGroupBox('Segment Configuration')
        config_layout = QVBoxLayout()
        config_layout.setSpacing(12)
        
        # Segment length controls
        length_label = QLabel('Segment Length:')
        length_label.setStyleSheet('color: #e6ecff; font-weight: bold;')
        config_layout.addWidget(length_label)
        
        length_input_layout = QHBoxLayout()
        
        self.segment_spinbox = QSpinBox()
        self.segment_spinbox.setMinimum(5)
        self.segment_spinbox.setMaximum(30)  # ← Cap at 30 min (Starbound limit)
        self.segment_spinbox.setValue(25)
        self.segment_spinbox.setSuffix(' minutes')
        self.segment_spinbox.valueChanged.connect(self.on_segment_changed)
        length_input_layout.addWidget(self.segment_spinbox)
        
        # Slider for easier adjustment
        self.segment_slider = QSlider(Qt.Horizontal)
        self.segment_slider.setMinimum(5)
        self.segment_slider.setMaximum(30)  # ← Cap at 30 min (Starbound limit)
        self.segment_slider.setValue(25)
        self.segment_slider.setTickPosition(QSlider.TicksBelow)
        self.segment_slider.setTickInterval(5)
        self.segment_slider.sliderMoved.connect(self.on_slider_moved)
        length_input_layout.addWidget(self.segment_slider)
        
        config_layout.addLayout(length_input_layout)
        
        # Preview info
        preview_info_layout = QVBoxLayout()
        preview_info_layout.setSpacing(6)
        
        preview_label = QLabel('Preview:')
        preview_label.setStyleSheet('color: #b8c5d6; font-size: 11px; margin-top: 8px;')
        preview_info_layout.addWidget(preview_label)
        
        self.preview_text = QLabel()
        self.preview_text.setStyleSheet('color: #00d4ff; font-size: 12px; font-weight: bold;')
        preview_info_layout.addWidget(self.preview_text)
        
        self.segment_list_label = QLabel()
        self.segment_list_label.setStyleSheet('color: #888888; font-size: 10px;')
        self.segment_list_label.setWordWrap(True)
        preview_info_layout.addWidget(self.segment_list_label)
        
        config_layout.addLayout(preview_info_layout)
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # Info note
        note = QLabel(
            '💡 Tip: Keep segments under 30 minutes for Starbound compatibility. '
            'Smaller segments = better control, but more files.'
        )
        note.setStyleSheet('color: #888888; font-size: 10px; line-height: 1.4;')
        note.setWordWrap(True)
        main_layout.addWidget(note)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton('✗ Cancel')
        cancel_btn.setStyleSheet('''
            QPushButton {
                background-color: #3a2a2a;
                color: #e6ecff;
                border-radius: 4px;
                padding: 8px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a3a3a;
            }
        ''')
        cancel_btn.clicked.connect(self.cancel_config)
        
        proceed_btn = QPushButton('✓ Apply Configuration')
        proceed_btn.setStyleSheet('''
            QPushButton {
                background-color: #2d5a3d;
                color: #e6ecff;
                border-radius: 4px;
                padding: 8px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a7a4f;
            }
        ''')
        proceed_btn.clicked.connect(self.apply_config)
        
        help_btn = QPushButton('?')
        help_btn.setMaximumWidth(40)
        help_btn.setToolTip('Show help for split configuration')
        help_btn.setStyleSheet('background-color: #3a5a7a; color: #e6ecff; border-radius: 4px; padding: 6px; font-weight: bold; font-size: 14px;')
        help_btn.clicked.connect(self.show_help)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(help_btn)
        button_layout.addStretch()
        button_layout.addWidget(proceed_btn)
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        # Initial preview update
        self.update_preview()
    
    def show_help(self):
        """Open the help dialog showing split file configuration information."""
        try:
            help_dialog = HelpWindow(self, 'split_files')
            help_dialog.exec_()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, 'Help Error', f'Could not open help window:\n{str(e)}')
    
    def on_segment_changed(self, value):
        """Spinbox changed, update slider."""
        self.segment_slider.blockSignals(True)
        self.segment_slider.setValue(value)
        self.segment_slider.blockSignals(False)
        self.update_preview()
    
    def on_slider_moved(self, value):
        """Slider moved, update spinbox."""
        self.segment_spinbox.blockSignals(True)
        self.segment_spinbox.setValue(value)
        self.segment_spinbox.blockSignals(False)
        self.update_preview()
    
    def update_preview(self):
        """Update preview text based on current segment length setting."""
        segment_length = self.segment_spinbox.value()
        self.segment_length_minutes = segment_length
        
        # Build breakdown - only include segments with actual duration
        breakdown = []
        remaining = self.file_duration_minutes
        actual_segment_count = 0
        
        while remaining > 0.1:  # Use 0.1 threshold to avoid floating-point issues
            seg_duration = min(segment_length, remaining)
            actual_segment_count += 1
            breakdown.append(f'  Part {actual_segment_count}: {seg_duration:.1f} min')
            remaining -= seg_duration
        
        # Update preview with ACTUAL segment count (no empty segments)
        self.preview_text.setText(
            f'{actual_segment_count} segment(s) of {segment_length} minutes each'
        )
        
        self.segment_list_label.setText('\n'.join(breakdown))
    
    def apply_config(self):
        """User confirmed configuration."""
        self.result_choice = "APPLY"
        self.accept()
    
    def cancel_config(self):
        """User cancelled configuration."""
        self.result_choice = "CANCEL"
        self.reject()
    
    def closeEvent(self, event):
        """Handle window close (X button or keyboard shortcut)."""
        self.result_choice = "CANCEL"
        self.reject()
        event.accept()
    
    def get_choice(self) -> str:
        """
        Get user's choice after dialog closes.
        
        Returns:
            "APPLY" if user clicked apply
            "CANCEL" if user clicked cancel
        """
        return self.result_choice
    
    def get_segment_length(self) -> int:
        """Get configured segment length in minutes."""
        return self.segment_length_minutes
