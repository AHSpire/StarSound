"""
Per-File Split Configuration Dialog
====================================

Modal dialog allowing users to configure individual splitting parameters
for each long audio file (30+ minutes).

Similar to per-track audio config - allows customization of each file independently.
"""

# For UI styling standards, see ../UI_STYLE_GUIDE.md

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpinBox, QSlider, QGroupBox, QListWidget, QListWidgetItem, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont


class PerFileSplitConfigDialog(QDialog):
    """
    Modal dialog for configuring splitting parameters for each file individually.
    
    Allows users to set unique segment length for each file that needs splitting.
    Shows total segments that will be created per file.
    """
    
    def __init__(self, files_needing_split: dict, parent=None):
        """
        Initialize per-file split configuration dialog.
        
        Args:
            files_needing_split: Dict mapping {file_path: duration_in_minutes}
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.setWindowTitle('⚙️ Configure Splitting for Each Track')
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        
        self.files_needing_split = files_needing_split  # {file_path: duration}
        self.per_file_segment_length = {}  # {file_path: segment_length}
        
        # Initialize all files with default 25-minute segments
        for file_path in files_needing_split.keys():
            self.per_file_segment_length[file_path] = 25
        
        self.current_file_index = 0
        self.result_choice = None
        
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
            QListWidget {
                background-color: #283046;
                color: #e6ecff;
                border: 1px solid #3a4a6a;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #00d4ff;
                color: #1a1f2e;
                font-weight: bold;
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
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Left side: File list
        left_layout = QVBoxLayout()
        
        title_left = QLabel('Select Track to Configure')
        title_left.setStyleSheet('color: #00d4ff; font-size: 13px; font-weight: bold;')
        left_layout.addWidget(title_left)
        
        self.file_list_widget = QListWidget()
        self.file_list_widget.itemSelectionChanged.connect(self.on_file_selected)
        
        # Populate file list
        import os
        for i, file_path in enumerate(files_needing_split.keys()):
            filename = os.path.basename(file_path)
            duration = files_needing_split[file_path]
            item_text = f'{filename}\n({duration:.1f} min)'
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, file_path)  # Store full path in UserRole
            self.file_list_widget.addItem(item)
            
            # Style the item
            font = QFont()
            font.setPointSize(10)
            item.setFont(font)
            if i == 0:
                item.setSelected(True)
        
        left_layout.addWidget(self.file_list_widget)
        
        # Right side: Configuration controls
        right_layout = QVBoxLayout()
        
        title_right = QLabel('Segment Configuration')
        title_right.setStyleSheet('color: #00d4ff; font-size: 13px; font-weight: bold;')
        right_layout.addWidget(title_right)
        
        # File info
        self.file_info_label = QLabel()
        self.file_info_label.setStyleSheet('color: #ffcc00; font-weight: bold; margin-bottom: 12px;')
        right_layout.addWidget(self.file_info_label)
        
        # Configuration group
        config_group = QGroupBox('Segment Length')
        config_layout = QVBoxLayout()
        config_layout.setSpacing(12)
        
        length_label = QLabel('Set segment length:')
        length_label.setStyleSheet('color: #e6ecff; font-weight: bold;')
        config_layout.addWidget(length_label)
        
        length_input_layout = QHBoxLayout()
        
        self.segment_spinbox = QSpinBox()
        self.segment_spinbox.setMinimum(5)
        self.segment_spinbox.setMaximum(30)
        self.segment_spinbox.setValue(25)
        self.segment_spinbox.setSuffix(' minutes')
        self.segment_spinbox.valueChanged.connect(self.on_segment_changed)
        length_input_layout.addWidget(self.segment_spinbox)
        
        self.segment_slider = QSlider(Qt.Horizontal)
        self.segment_slider.setMinimum(5)
        self.segment_slider.setMaximum(30)
        self.segment_slider.setValue(25)
        self.segment_slider.setTickPosition(QSlider.TicksBelow)
        self.segment_slider.setTickInterval(5)
        self.segment_slider.sliderMoved.connect(self.on_slider_moved)
        length_input_layout.addWidget(self.segment_slider)
        
        config_layout.addLayout(length_input_layout)
        
        # Preview
        preview_label = QLabel('Preview:')
        preview_label.setStyleSheet('color: #b8c5d6; font-size: 11px; margin-top: 12px;')
        config_layout.addWidget(preview_label)
        
        self.preview_text = QLabel()
        self.preview_text.setStyleSheet('color: #00d4ff; font-size: 12px; font-weight: bold;')
        config_layout.addWidget(self.preview_text)
        
        self.segment_breakdown_label = QLabel()
        self.segment_breakdown_label.setStyleSheet('color: #888888; font-size: 10px;')
        self.segment_breakdown_label.setWordWrap(True)
        config_layout.addWidget(self.segment_breakdown_label)
        
        config_group.setLayout(config_layout)
        right_layout.addWidget(config_group)
        
        # Tip
        note = QLabel(
            '💡 Each track can have different segment lengths. '
            'Keep all segments under 30 minutes for Starbound compatibility.'
        )
        note.setStyleSheet('color: #888888; font-size: 10px; line-height: 1.4;')
        note.setWordWrap(True)
        right_layout.addWidget(note)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton('✗ Cancel')
        cancel_btn.setStyleSheet('''
            QPushButton {
                background-color: #c41e3a;
                color: #e6ecff;
                border-radius: 4px;
                padding: 8px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e63235;
            }
        ''')
        cancel_btn.clicked.connect(self.cancel_config)
        
        proceed_btn = QPushButton('Proceed To Next Step ✓')
        proceed_btn.setStyleSheet('''
            QPushButton {
                background-color: #2d5a3d;
                color: #e6ecff;
                border-radius: 4px;
                padding: 8px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d7a4d;
            }
        ''')
        proceed_btn.clicked.connect(self.apply_config)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(proceed_btn)
        
        right_layout.addLayout(button_layout)
        right_layout.addStretch()
        
        # Add sides to main layout
        main_layout.addLayout(left_layout, 1)  # 1 = stretch factor
        main_layout.addLayout(right_layout, 2)  # 2 = stretch factor (more space for config)
        
        # Initial load
        self.on_file_selected()
    
    def on_file_selected(self):
        """User selected a different file from list."""
        current_item = self.file_list_widget.currentItem()
        if not current_item:
            return
        
        file_path = current_item.data(Qt.UserRole)
        duration = self.files_needing_split[file_path]
        
        import os
        filename = os.path.basename(file_path)
        self.file_info_label.setText(f'📁 {filename}\nDuration: {duration:.1f} minutes')
        
        # Load this file's current segment length
        current_length = self.per_file_segment_length.get(file_path, 25)
        
        self.segment_spinbox.blockSignals(True)
        self.segment_slider.blockSignals(True)
        
        self.segment_spinbox.setValue(current_length)
        self.segment_slider.setValue(current_length)
        
        self.segment_spinbox.blockSignals(False)
        self.segment_slider.blockSignals(False)
        
        self.update_preview()
    
    def on_segment_changed(self, value):
        """Spinbox changed, update slider."""
        self.segment_slider.blockSignals(True)
        self.segment_slider.setValue(value)
        self.segment_slider.blockSignals(False)
        
        # Save this value for current file
        current_item = self.file_list_widget.currentItem()
        if current_item:
            file_path = current_item.data(Qt.UserRole)
            self.per_file_segment_length[file_path] = value
        
        self.update_preview()
    
    def on_slider_moved(self, value):
        """Slider moved, update spinbox."""
        self.segment_spinbox.blockSignals(True)
        self.segment_spinbox.setValue(value)
        self.segment_spinbox.blockSignals(False)
        
        # Save this value for current file
        current_item = self.file_list_widget.currentItem()
        if current_item:
            file_path = current_item.data(Qt.UserRole)
            self.per_file_segment_length[file_path] = value
        
        self.update_preview()
    
    def update_preview(self):
        """Update preview based on current segment length."""
        current_item = self.file_list_widget.currentItem()
        if not current_item:
            return
        
        file_path = current_item.data(Qt.UserRole)
        duration = self.files_needing_split[file_path]
        segment_length = self.segment_spinbox.value()
        
        # Build breakdown
        breakdown = []
        remaining = duration
        actual_segment_count = 0
        
        while remaining > 0.1:
            seg_duration = min(segment_length, remaining)
            actual_segment_count += 1
            breakdown.append(f'  Part {actual_segment_count}: {seg_duration:.1f} min')
            remaining -= seg_duration
        
        self.preview_text.setText(f'{actual_segment_count} segment(s) of {segment_length} minutes each')
        self.segment_breakdown_label.setText('\n'.join(breakdown))
    
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
        """Get user's choice after dialog closes."""
        return self.result_choice
    
    def get_per_file_segment_lengths(self) -> dict:
        """
        Get configured segment length for each file.
        
        Returns:
            Dict mapping {file_path: segment_length_in_minutes}
        """
        return self.per_file_segment_length.copy()
