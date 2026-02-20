"""
Split Preview Dialog
====================

Modal dialog showing splits that were created, with durations and file count.
Displayed after FFmpeg splitting completes, before conversion to OGG starts.

Design: Informative, read-only preview, simple confirmation to proceed.
"""

# For UI styling standards, see ../UI_STYLE_GUIDE.md

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt


class SplitPreviewDialog(QDialog):
    """
    Modal dialog showing audio file split results.
    
    Displays original filename(s), total duration, segment count, and list
    of all segments with individual durations. Allows user to confirm
    before conversion proceeds.
    
    Supports both single file preview and multiple files preview.
    """
    
    def __init__(self, original_filename: str = None, original_duration: float = None, split_files: list = None, segment_durations: list = None, parent=None, split_metadata: dict = None):
        """
        Initialize split preview dialog.
        
        Can accept either:
        - Single file: original_filename, original_duration, split_files, segment_durations
        - Multiple files: split_metadata dict with {filename: {metadata}}
        
        Args:
            original_filename: Name of original file (for single-file preview)
            original_duration: Original total duration in minutes (for single-file preview)
            split_files: List of split file paths (for single-file preview)
            segment_durations: List of durations in minutes for each segment (for single-file preview)
            parent: Parent widget (main window)
            split_metadata: Dict of multiple files' split results {filename: {data}} (for multi-file preview)
        """
        super().__init__(parent)
        self.setWindowTitle('✓ Audio Split Complete')
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.result_choice = None
        
        # See UI_STYLE_GUIDE.md for styling standards
        self.setStyleSheet('''
            QDialog {
                background-color: #1a1f2e;
            }
            QLabel {
                color: #e6ecff;
            }
            QScrollArea {
                background-color: #1a1f2e;
                border: 1px solid #3a4a6a;
                border-radius: 4px;
            }
        ''')
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel('✓ Audio Files Successfully Split!')
        title.setStyleSheet('color: #00d4ff; font-size: 14px; font-weight: bold;')
        main_layout.addWidget(title)
        
        # Determine if showing single or multiple files
        if split_metadata:
            # Multi-file preview
            self._build_multi_file_preview(main_layout, split_metadata)
        else:
            # Single-file preview (backward compatibility)
            self._build_single_file_preview(main_layout, original_filename, original_duration, split_files, segment_durations)
        
        # Info note
        note = QLabel(
            'You will now proceed with audio processing options (compression, EQ, normalization).'
        )
        note.setStyleSheet('color: #888888; font-size: 11px; line-height: 1.4;')
        note.setWordWrap(True)
        main_layout.addWidget(note)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        proceed_btn = QPushButton('✓ Proceed')
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
        proceed_btn.clicked.connect(self.proceed_conversion)
        
        button_layout.addStretch()
        button_layout.addWidget(proceed_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
    
    def _build_single_file_preview(self, main_layout, original_filename: str, original_duration: float, split_files: list, segment_durations: list):
        """Build preview for a single file split."""
        # Summary info
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(6)
        
        original_label = QLabel(
            f'Original: <span style="color: #ffcc00; font-weight: bold;">{original_filename}</span> '
            f'({original_duration:.1f} minutes)'
        )
        original_label.setStyleSheet('color: #e6ecff; font-size: 12px;')
        summary_layout.addWidget(original_label)
        
        segment_label = QLabel(
            f'Split into: <span style="color: #00d4ff; font-weight: bold;">{len(split_files)} segments</span>'
        )
        segment_label.setStyleSheet('color: #e6ecff; font-size: 12px;')
        summary_layout.addWidget(segment_label)
        
        main_layout.addLayout(summary_layout)
        
        # Scrollable segment list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; }')
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(4)
        
        import os
        for i, (file_path, duration) in enumerate(zip(split_files, segment_durations), 1):
            filename = os.path.basename(file_path)
            segment_item = QLabel(f'  Part {i}: {filename} ({duration:.1f} min)')
            segment_item.setStyleSheet('color: #b8c5d6; font-size: 11px; padding: 2px 0;')
            scroll_layout.addWidget(segment_item)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
    
    def _build_multi_file_preview(self, main_layout, split_metadata: dict):
        """Build preview for multiple files split."""
        # Summary info
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(6)
        
        total_segments = sum(len(meta.get('segment_durations', [])) for meta in split_metadata.values())
        files_label = QLabel(
            f'Split: <span style="color: #ffcc00; font-weight: bold;">{len(split_metadata)} file(s)</span> into '
            f'<span style="color: #00d4ff; font-weight: bold;">{total_segments} segments</span> total'
        )
        files_label.setStyleSheet('color: #e6ecff; font-size: 12px;')
        summary_layout.addWidget(files_label)
        
        main_layout.addLayout(summary_layout)
        
        # Scrollable segment list with file grouping
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; }')
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        
        import os
        for i, (filename, metadata) in enumerate(split_metadata.items()):
            # File header
            original_duration = metadata.get('original_duration', 0)
            segment_count = len(metadata.get('segment_durations', []))
            
            header = QLabel(
                f'📁 {filename} ({original_duration:.1f} min) → {segment_count} segments:'
            )
            header.setStyleSheet('color: #ffcc00; font-weight: bold; font-size: 11px; margin-top: 6px;')
            scroll_layout.addWidget(header)
            
            # Segments for this file
            split_files = metadata.get('segments', [])
            segment_durations = metadata.get('segment_durations', [])
            
            for j, (file_path, duration) in enumerate(zip(split_files, segment_durations), 1):
                segment_filename = os.path.basename(file_path)
                segment_item = QLabel(f'    Part {j}: {segment_filename} ({duration:.1f} min)')
                segment_item.setStyleSheet('color: #b8c5d6; font-size: 10px; padding: 1px 0;')
                scroll_layout.addWidget(segment_item)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
    
    def proceed_conversion(self):
        """User confirmed, ready to proceed with conversion."""
        self.result_choice = "PROCEED"
        self.accept()
    
    def closeEvent(self, event):
        """Handle window close (X button or keyboard shortcut)."""
        self.result_choice = "CANCELLED"
        self.reject()
        event.accept()
    
    def get_choice(self) -> str:
        """
        Get user's choice after dialog closes.
        
        Returns:
            "PROCEED" if user clicked continue button
        """
        return self.result_choice
