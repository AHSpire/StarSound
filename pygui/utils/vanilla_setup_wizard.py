"""
vanilla_setup_wizard.py

GUI dialog for setting up vanilla Starbound music files.
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox, QTextEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from pathlib import Path
from utils.vanilla_setup import VanillaSetup
from utils.logger import get_logger
from dialogs.help_window import HelpWindow


class UnpackWorker(QThread):
    """Worker thread for running unpacking in background"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, starbound_path: str, starsound_dir: str):
        super().__init__()
        self.starbound_path = starbound_path
        self.starsound_dir = starsound_dir
    
    def run(self):
        try:
            setup = VanillaSetup()
            success, msg = setup.run_full_setup(
                self.starbound_path,
                self.starsound_dir,
                progress_callback=self.progress.emit
            )
            self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, f"Unexpected error: {str(e)}")


class VanillaSetupWizard(QDialog):
    """Dialog for guiding users through vanilla track setup"""
    
    def __init__(self, parent=None, starbound_path: str = None, starsound_dir: str = None):
        super().__init__(parent)
        self.setWindowTitle('StarSound - Vanilla Track Setup')
        self.setModal(True)
        # Explicitly disable Windows help button hint
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Store initialization parameters
        self.starbound_path = starbound_path
        self.starsound_dir = starsound_dir
        self.logger = get_logger()
        
        self.init_ui()
    
    def show_help(self):
        """Open the help dialog showing vanilla tracks information."""
        try:
            help_dialog = HelpWindow(self, 'vanilla_tracks')
            help_dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, 'Help Error', f'Could not open help:\n{str(e)}')
    
    def init_ui(self):
        """Build the wizard UI"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('🎵 Original Music Preview and Replacer Tracks Setup')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Description
        description = QLabel(
            'StarSound will extract Starbound\'s music files so you can see '
            'which tracks you\'re replacing.\n\n'
            'Here\'s what will happen:\n'
            '  • Safe backup (copy) of your game files to StarSound\'s backup folder before extracting any music\n'
            '  • Extract the original (copied) Starbound music to StarSound\'s vanilla_tracks folder\n'
            '  • Organize all the vanilla tracks for proper preview and replacement\n'
            '  • Clean up temporary files\n\n'
            'This process will take about 1-2 minutes. Your Starbound install won\'t be affected at all!\n\n'
            'Ready to get started?'
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Status/progress text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        self.status_text.setStyleSheet('background-color: #1a1a2e; color: #a9a9a9; border: 1px solid #6c5ce7;')
        layout.addWidget(self.status_text)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.setStyleSheet(
            'QProgressBar { border: 1px solid #6c5ce7; border-radius: 4px; '
            'background-color: #22223a; } '
            'QProgressBar::chunk { background-color: #6c5ce7; }'
        )
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.setup_btn = QPushButton('▶ Start Setup')
        self.setup_btn.setStyleSheet(
            'QPushButton { background-color: #6c5ce7; color: white; padding: 8px; '
            'border-radius: 4px; font-weight: bold; } '
            'QPushButton:hover { background-color: #7d6ce8; } '
            'QPushButton:pressed { background-color: #5b4bc6; }'
        )
        self.setup_btn.clicked.connect(self.start_setup)
        button_layout.addWidget(self.setup_btn)
        
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.setStyleSheet(
            'QPushButton { background-color: #444; color: white; padding: 8px; '
            'border-radius: 4px; } '
            'QPushButton:hover { background-color: #555; } '
            'QPushButton:pressed { background-color: #333; }'
        )
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        help_btn = QPushButton('?')
        help_btn.setMaximumWidth(40)
        help_btn.setToolTip('Show help for vanilla track setup')
        help_btn.setStyleSheet('background-color: #3a5a7a; color: #e6ecff; border-radius: 4px; padding: 6px; font-weight: bold; font-size: 14px;')
        help_btn.clicked.connect(self.show_help)
        button_layout.addWidget(help_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def start_setup(self):
        """Start the unpacking process in background thread"""
        if not self.starbound_path or not self.starsound_dir:
            QMessageBox.critical(self, 'Error', 'Starbound path or StarSound directory not set')
            return
        
        # Disable button and show progress
        self.setup_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.update_status('Starting setup...')
        
        # Create and start worker thread
        self.worker = UnpackWorker(self.starbound_path, str(self.starsound_dir))
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.on_setup_finished)
        self.worker.start()
    
    def update_status(self, message: str):
        """Update status text"""
        current_text = self.status_text.toPlainText()
        if current_text:
            self.status_text.setText(current_text + '\n' + message)
        else:
            self.status_text.setText(message)
        
        # Scroll to bottom
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
    
    def on_setup_finished(self, success: bool, message: str):
        """Handle setup completion"""
        self.progress_bar.setMaximum(100)  # Make determinate
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            self.update_status('✅ Setup complete!')
            self.logger.log('Vanilla setup successful', context='SetupWizard')
            QMessageBox.information(
                self,
                'Awesome! You\'re all set!',
                'The original Starbound music is now ready to preview!\n\n'
                'What was done:\n'
                '✓ Backed up your original game files safely\n'
                '✓ Extracted Starbound\'s original music\n'
                '✓ Organized music by biome (surface, underground, core, space)\n'
                '✓ Created day/night track folders\n\n'
                'You can now preview original tracks in Replace/Both modes!\n'
                'Tip: Right-click any track to listen before replacing.'
            )
            self.accept()
        else:
            self.update_status(f'❌ Setup failed: {message}')
            self.logger.error(f'Vanilla setup failed: {message}', context='SetupWizard')
            QMessageBox.critical(
                self,
                'Setup Failed',
                f'We couldn\'t finish setting up the music:\n\n{message}\n\n'
                'Common fixes:\n'
                '• Make sure Starbound is installed correctly\n'
                '• Check that you have enough disk space\n'
                '• Try running SetupDependencies.bat if FFmpeg is missing\n\n'
                'For detailed info, check the app logs in:\n'
                'StarSound/pygui/starsoundlogs/'
            )
            self.setup_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
