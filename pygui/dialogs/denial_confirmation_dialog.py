"""
Split Denial Confirmation Dialog
=================================

Modal dialog warning user about consequences of not splitting long audio files.
Shown after user initially denies splitting, to confirm they really want to proceed.

Design: Clear warning, final confirmation before proceeding with oversized file.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt
from dialogs.help_window import HelpWindow


class DenialConfirmationDialog(QDialog):
    """
    Modal dialog confirming user's decision to NOT split a long audio file.
    
    Warns about consequences and asks final confirmation. User can either
    proceed with conversion (file likely won't work in Starbound) or go
    back and accept splitting.
    """
    
    def __init__(self, filename: str, duration_minutes: float, parent=None):
        """
        Initialize denial confirmation dialog.
        
        Args:
            filename: Name of the audio file (for display)
            duration_minutes: Duration in minutes (float)
            parent: Parent widget (main window)
        """
        super().__init__(parent)
        self.setWindowTitle('⚠️ Confirm: Do Not Split')
        self.setModal(True)
        # Explicitly disable Windows help button hint
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(500)
        self.setMinimumHeight(220)
        
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
        
        # Large warning
        title = QLabel('⚠️ ⚠️ Are you sure?')
        title.setStyleSheet('color: #ff6b6b; font-size: 16px; font-weight: bold;')
        main_layout.addWidget(title)
        
        # Explanation
        explanation = QLabel(
            f'<b>{filename}</b> is <b>{duration_minutes:.1f} minutes</b> long.\n\n'
            'Starbound will <b>NOT play this file</b> in-game because it exceeds the 30-minute limit. '
            'The game engine will either:\n'
            '  • Skip it entirely\n'
            '  • Cause music/performance issues\n'
            '  • Not include it in the mod at all\n\n'
            'You really should split it. Want to split it now?'
        )
        explanation.setStyleSheet('color: #e6ecff; font-size: 12px; line-height: 1.6;')
        explanation.setWordWrap(True)
        main_layout.addWidget(explanation)
        
        main_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        back_btn = QPushButton('← Split It (Better Idea)')
        back_btn.setStyleSheet('''
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
        back_btn.clicked.connect(self.split_it)
        
        proceed_btn = QPushButton('  Continue Anyway')
        proceed_btn.setStyleSheet('''
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
        proceed_btn.clicked.connect(self.proceed_anyway)
        
        help_btn = QPushButton('?')
        help_btn.setMaximumWidth(40)
        help_btn.setToolTip('Show help for split confirmation')
        help_btn.setStyleSheet('background-color: #3a5a7a; color: #e6ecff; border-radius: 4px; padding: 6px; font-weight: bold; font-size: 14px;')
        help_btn.clicked.connect(self.show_help)
        
        button_layout.addStretch()
        button_layout.addWidget(back_btn)
        button_layout.addWidget(proceed_btn)
        button_layout.addWidget(help_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
    
    def show_help(self):
        """Open the help dialog showing split file information."""
        try:
            help_dialog = HelpWindow(self, 'split_files')
            help_dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, 'Help Error', f'Could not open help:\n{str(e)}')
    
    def split_it(self):
        """User changed their mind, want to split after all."""
        self.result_choice = "SPLIT_IT"
        self.accept()
    
    def proceed_anyway(self):
        """User confirmed they want to proceed without splitting."""
        self.result_choice = "PROCEED_ANYWAY"
        self.reject()
    
    def closeEvent(self, event):
        """Handle window close (X button or keyboard shortcut)."""
        self.result_choice = "SPLIT_IT"
        self.reject()
        event.accept()
    
    def get_choice(self) -> str:
        """
        Get the user's final choice after dialog closes.
        
        Returns:
            "SPLIT_IT" if user clicked back button (go back and split)
            "PROCEED_ANYWAY" if user confirmed proceeding without split
        """
        return self.result_choice
