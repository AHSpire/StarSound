"""
Track Splitting Confirmation Dialog
====================================

Modal dialog for confirming whether to split long audio files (>30 minutes).
Shown during conversion process for each file that exceeds Starbound's limit.

Design: Clear messaging, minimal options, modal (blocks main window).
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt


class SplitConfirmationDialog(QDialog):
    """
    Modal dialog asking user to confirm audio file splitting.
    
    Can handle single or multiple files. Shows file/files and durations,
    explains why splitting is needed, and offers Accept/Deny buttons.
    Dialog is modal and blocks until user makes a decision.
    """
    
    def __init__(self, filename: str | list, duration_minutes: float | list = None, parent=None):
        """
        Initialize split confirmation dialog.
        
        Can accept either:
        - Single file: filename (str), duration_minutes (float)
        - Multiple files: filename (list of str), duration_minutes (list of float)
        
        Args:
            filename: Name of audio file(s) or list of names
            duration_minutes: Duration in minutes or list of durations
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        
        # Handle both single and multiple files
        if isinstance(filename, str):
            self.filenames = [filename]
            self.durations = [duration_minutes]
        else:
            self.filenames = filename
            self.durations = duration_minutes
        
        self.setWindowTitle('⚠️ Long Audio File(s) Detected')
        self.setModal(True)
        self.setMinimumWidth(550)
        
        # Increase height if multiple files
        if len(self.filenames) > 1:
            self.setMinimumHeight(450)
        else:
            self.setMinimumHeight(350)
        
        self.result_choice = None  # Will be "ACCEPT" or "DENY"
        
        # See UI_STYLE_GUIDE.md for styling standards
        self.setStyleSheet('''
            QDialog {
                background-color: #1a1f2e;
            }
            QLabel {
                color: #e6ecff;
            }
        ''')
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        if len(self.filenames) == 1:
            title = QLabel('⚠️ One audio file is too long for Starbound')
        else:
            title = QLabel(f'⚠️ {len(self.filenames)} audio files are too long for Starbound')
        title.setStyleSheet('color: #ffcc00; font-size: 14px; font-weight: bold;')
        main_layout.addWidget(title)
        
        # File info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(6)
        
        # List all files that need splitting
        for fname, duration in zip(self.filenames, self.durations):
            file_line = QLabel(
                f'📁 <span style="color: #00d4ff; font-weight: bold;">{fname}</span> '
                f'<span style="color: #ffcc00;">({duration:.1f} min)</span>'
            )
            file_line.setStyleSheet('color: #e6ecff; font-size: 11px;')
            info_layout.addWidget(file_line)
        
        main_layout.addLayout(info_layout)
        
        # Explanation
        explanation = QLabel(
            'Audio files longer than 30 minutes are not supported by Starbound. '
            'StarSound can automatically split long files into shorter segments so they work in the game.\n\n'
        )
        explanation.setStyleSheet('color: #b8c5d6; font-size: 12px; line-height: 1.5;')
        explanation.setWordWrap(True)
        main_layout.addWidget(explanation)
        
        # Disclaimer section
        disclaimer_title = QLabel('❓ Why? Technical Details:')
        disclaimer_title.setStyleSheet('color: #ffcc00; font-size: 12px; font-weight: bold; margin-top: 12px;')
        main_layout.addWidget(disclaimer_title)
        
        disclaimer_reasons = QLabel(
            '• <b>Memory Limits:</b> Long files consume a lot of memory, potentially causing crashes or hanging during mod load<br>'
            '• <b>Silent Failure:</b> File loads but music player fails, resulting in silence or fallback to vanilla tracks<br>'
            '• <b>Infinite Loops:</b> Audio looping code can timeout on very long tracks, or be delayed<br>'
            '• <b>Buffer Overflow:</b> Decoder buffers may overflow during processing<br><br>'
            '<i>Splitting ensures each segment stays within Starbound\'s safe limits!</i>'
        )
        disclaimer_reasons.setStyleSheet('color: #b8c5d6; font-size: 12px; line-height: 1.5; margin-left: 10px;')
        disclaimer_reasons.setWordWrap(True)
        main_layout.addWidget(disclaimer_reasons)
        
        main_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        accept_btn = QPushButton('✓ Split It')
        accept_btn.setStyleSheet('''
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
        accept_btn.clicked.connect(self.accept_split)
        
        deny_btn = QPushButton('✗ Skip Splitting')
        deny_btn.setStyleSheet('''
            QPushButton {
                background-color: #c41e3a;
                color: #e6ecff;
                border-radius: 4px;
                padding: 8px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7a3a3a;
            }
        ''')
        deny_btn.clicked.connect(self.deny_split)
        
        button_layout.addStretch()
        button_layout.addWidget(accept_btn)
        button_layout.addWidget(deny_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
    
    def accept_split(self):
        """User chose to split the file."""
        self.result_choice = "ACCEPT"
        self.accept()
    
    def deny_split(self):
        """User chose to skip splitting."""
        self.result_choice = "DENY"
        self.reject()
    
    def closeEvent(self, event):
        """Handle window close (X button or keyboard shortcut)."""
        self.result_choice = "DENY"
        self.reject()
        event.accept()
    
    def get_choice(self) -> str:
        """
        Get the user's choice after dialog closes.
        
        Returns:
            "ACCEPT" if user clicked 'Split It'
            "DENY" if user clicked 'Skip Splitting'
        """
        return self.result_choice
