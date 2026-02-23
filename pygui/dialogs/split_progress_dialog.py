"""
Progress dialog shown during FFmpeg file splitting operations.
Prevents user interaction and displays current operation status.
Integrates with app's dark blue theme.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QFont
import sys
from dialogs.help_window import HelpWindow


class SplitProgressDialog(QDialog):
    """
    Modal progress dialog shown while splitting files.
    Displays:
    - "Please wait... Splitting your tracks" message
    - Progress bar (indeterminate)
    - Current file being processed
    
    Features:
    - Centered on parent window
    - Matches app's dark blue theme
    - Animated progress bar with spinner effect
    - Blocks user interaction
    
    Usage:
        dialog = SplitProgressDialog(parent_window)
        dialog.show()  # Display before starting split
        # ... perform splitting ...
        dialog.close()  # Close when done
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing...")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setGeometry(0, 0, 500, 200)
        # Don't use native help button (causes emoji issue)
        
        # Center dialog on parent window (if parent exists)
        if parent:
            parent_geometry = parent.frameGeometry()
            center_x = parent_geometry.center().x() - (500 // 2)
            center_y = parent_geometry.center().y() - (200 // 2)
            self.move(center_x, center_y)
        
        # Apply dark blue theme stylesheet (matches main app)
        self._apply_theme_stylesheet()
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title label
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        
        title_label = QLabel("Please wait... Splitting your tracks")
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Current file label
        file_font = QFont()
        file_font.setPointSize(10)
        
        self.current_file_label = QLabel("Initializing...")
        self.current_file_label.setFont(file_font)
        self.current_file_label.setAlignment(Qt.AlignCenter)
        self.current_file_label.setStyleSheet("color: #00ffff; font-weight: bold;")
        layout.addWidget(self.current_file_label)
        
        # Progress bar (indeterminate) - bright green on dark blue background
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Indeterminate progress
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3a4a6a;
                border-radius: 5px;
                background: #1a1f2e;
                height: 25px;
            }
            QProgressBar::chunk {
                background: #00ff00;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Processing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #aaa; font-size: 9pt;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Animation timer for visual feedback
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_count = 0
    
    def _apply_theme_stylesheet(self):
        """Apply dark blue theme stylesheet matching the UI_STYLE_GUIDE.md."""
        stylesheet = """
        QDialog {
            background-color: #1a1f2e;
        }
        QLabel {
            color: #e6ecff;
        }
        QProgressBar {
            border: 1px solid #3a4a6a;
            border-radius: 4px;
            background: #1a1f2e;
            height: 25px;
        }
        QProgressBar::chunk {
            background: #00ff00;
            border-radius: 4px;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def show_help(self):
        """Open the help dialog showing split file information."""
        try:
            help_dialog = HelpWindow(self, 'split_files')
            help_dialog.exec_()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, 'Help Error', f'Could not open help:\n{str(e)}')
    
    def update_current_file(self, filename: str, file_number: int, total_files: int):
        """Update the displayed filename and progress."""
        self.current_file_label.setText(f"{filename}")
        self.status_label.setText(f"File {file_number} of {total_files}")
        QApplication.processEvents()  # Keep UI responsive
    
    def start_animation(self):
        """Start the progress bar animation."""
        self.animation_timer.start(500)
    
    def stop_animation(self):
        """Stop the progress bar animation."""
        self.animation_timer.stop()
    
    def _update_animation(self):
        """Update animation state (spinner effect)."""
        self.animation_count += 1
        status_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        char = status_chars[self.animation_count % len(status_chars)]
        current_status = self.status_label.text().split(" ")[-2:]  # Keep "File X of Y"
        self.status_label.setText(f"{char} {' '.join(current_status)}")
