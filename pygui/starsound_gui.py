"""
[SYSTEM] StarSound GUI - Main Application Window
[VERSION] 1.0
[ROLE] UI Coordinator + Auto-Save Orchestra

[ARCHITECTURE_IDENTIFIER] SAVE_SYSTEM_v3
[COMPONENT_TYPE] Primary Orchestrator

[SAVE_MECHANISMS] 3-TIER SYSTEM
├─ [TIER_1] STAGING_FOLDER
│  ├─ [PATH] StarSound/staging/
│  ├─ [MANAGER] atomicwriter.py
│  ├─ [PURPOSE] Temporary build working directory
│  ├─ [WRITE_TRIGGER] Audio selection, Audio conversion, Generate Mod
│  ├─ [LIFECYCLE] Session-based (survives restarts)
│  └─ [DATA] Raw files, converted OGG, in-progress structures
│
├─ [TIER_2] MOD_SAVES_FOLDER (PRIMARY CONFIG STORAGE)
│  ├─ [PATH] StarSound/mod_saves/
│  ├─ [MANAGER_CLASS] ModSaveManager
│  ├─ [PURPOSE] Persistent mod configuration snapshots
│  ├─ [WRITE_TRIGGER] AUTO_SAVE_MOD_STATE() called from multiple UI events
│  ├─ [LIFECYCLE] User-controlled (persists indefinitely)
│  ├─ [FORMAT] JSON: {mod_name}.json
│  ├─ [DATA_SCHEMA] {"mod_name", "saved_at", "config": {patch_mode, biomes, tracks...}}
│  └─ [AUTO_SAVE_HOOKS] (see [AUTO_SAVE_EVENTS] below)
│
└─ [TIER_3] SETTINGS_JSON (GLOBAL STATE)
   ├─ [PATH] StarSound/mod_saves/settings.json
   ├─ [MANAGER_CLASS] SettingsManager
   ├─ [PURPOSE] App-level preferences + last-used state
   ├─ [WRITE_PATTERN] Immediate write on set() call
   ├─ [LIFECYCLE] Global config (loaded on startup)
   ├─ [FORMAT] JSON key-value pairs
   ├─ [KEYS] last_mod_name, last_patch_mode, crt_effects_enabled
   └─ [AUTO_SAVE_HOOKS] Called during CONFIG_CONFIRM_EVENTS

[AUTO_SAVE_EVENTS] COMPLETE LIST
Event_ID | Event_Name | Trigger_Location | Save_Target | Condition
─────────────────────────────────────────────────────────────────────
ASE_001  | MOD_NAME_CONFIRM | on_modname_focus_out | MOD_SAVES | !empty
ASE_002  | DICE_NAME_CONFIRM | on_checkbox_toggled | MOD_SAVES | checked==True
ASE_003  | AUDIO_FILES_SELECT | browse_audio() | MOD_SAVES | files_selected
ASE_004  | AUDIO_FILES_CLEAR | clear_audio() | MOD_SAVES | (always saves state)
ASE_005  | AUDIO_CONVERT | convert_audio() | MOD_SAVES | converted_count>0
ASE_006  | PATCH_MODE_ADD | on_add_to_game() | MOD_SAVES | (always)
ASE_007  | PATCH_MODE_REPLACE | on_replace() | MOD_SAVES | (after selections)
ASE_008  | PATCH_MODE_REPLACE_ADD | on_replace_and_add() | MOD_SAVES | (always)
ASE_009  | BIOME_SELECT | _show_biome_dialog() | MOD_SAVES | biomes_selected>0
ASE_010  | REPLACE_SELECT | ReplaceTracksDialog | MOD_SAVES | (on_track_sel_done)
ASE_011  | GENERATE_MOD | generate_patch_file() | MOD_SAVES | mod_name_exists
ASE_012  | APP_CLOSE | closeEvent() | MOD_SAVES | mod_name_set

[METHOD_REFERENCE] _auto_save_mod_state(action: str = '')
└─ [FUNCTION] Saves MainWindow state to MOD_SAVES
   ├─ [INPUT] action: str (event identifier for logging)
   ├─ [CONDITION] if (mod_name.strip() and mod_name != 'blank_mod')
   ├─ [CALL_CHAIN] self._gather_current_mod_state() → self.mod_save_manager.save_mod()
   └─ [LOGGING] [PERSIST] Auto-saved mod on {action}: {mod_name}

[DATA_DEPENDENCY_GRAPH]
ModName (QLineEdit) ──→ modname_input.text()
        ├──→ mod_save_manager.save_mod(mod_name, state)
        ├──→ settings.set('last_mod_name', mod_name)
        └──→ logger.update_metadata(mod_name=mod_name)

PatchMode (Enum) ────→ self.patch_mode ∈ {add, replace, both}
        ├──→ settings.set('last_patch_mode', mode)
        ├──→ _auto_save_mod_state('patch mode: {mode}')
        └──→ state_dict['patch_mode'] → mod_saves/{mod_name}.json

SelectedBiomes (List) → self.selected_biomes: List[Tuple[str, str]]
        ├──→ state_dict['selected_biomes']
        ├──→ mod_saves/{mod_name}.json
        └──→ on Generate: passed to patch_generator.generate_patch()

AudioFiles (List) ───→ self.selected_audio_files: List[Path]
        ├──→ state_dict['day_tracks'] / 'night_tracks'
        ├──→ copied to staging/music/
        ├──→ mod_saves/{mod_name}.json
        └──→ on Convert: processed by backup_and_convert_audio()

[INITIALIZATION_ORDER]
Step 1: SettingsManager.__init__() → loads settings.json
Step 2: ModSaveManager.__init__() → indexes mod_saves/
Step 3: self.selected_biomes = []
Step 4: self.patch_mode = settings.get('last_patch_mode', 'add')
Step 5: UI components created
Step 6: Signal-slot connections established
Step 7: Auto-save hooks registered

[CRITICAL_INVARIANTS]
INV_001: mod_name must pass .strip() and != 'blank_mod' before any save
INV_002: state_dict always contains: mod_name, patch_mode, day_tracks, night_tracks, selected_biomes, folder_path
INV_003: settings.json is separate from mod_saves/{mod_name}.json (never mixed)
INV_004: staging/ and mod_saves/ are independent write paths
INV_005: Audio conversion runs in thread → main thread calls _auto_save_mod_state()
"""

# For UI styling standards, see ../UI_STYLE_GUIDE.md

import sys
import os
import math
import random
import webbrowser
from pathlib import Path
from functools import partial

# ⚡ CRITICAL FIX: Add pygui directory to Python path so imports work from ANY working directory
# This allows running: python starsound_gui.py from ANY folder, not just from pygui/
pygui_dir = Path(__file__).parent.absolute()
if str(pygui_dir) not in sys.path:
    sys.path.insert(0, str(pygui_dir))
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QMenuBar, QAction, QToolBar, QWidgetAction, QStackedLayout, QTextEdit, QDialog, QListWidget, QListWidgetItem, QButtonGroup, QRadioButton, QInputDialog, QComboBox, QCheckBox, QProgressBar
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QBrush, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QCoreApplication
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
from utils.patch_generator import generate_patch, get_all_biomes_by_category
from utils.audio_utils import validate_file_exists, validate_file_duration, validate_file_format, convert_to_ogg
from utils.logger import get_logger
from utils.starbound_locator import get_mods_folder, get_storage_folder
from utils.screenshot_manager import take_screenshot
from utils.settings_manager import SettingsManager
from utils.mod_save_manager import ModSaveManager
from utils.stylesheet_manager import apply_global_stylesheet, get_toolbar_style
from utils import emergency_beacon
from dialogs.replace_tracks_dialog import ReplaceTracksDialog
from dialogs.audio_processing_dialog import AudioProcessingDialog
from dialogs.per_track_audio_config_dialog import PerTrackAudioConfigDialog
from dialogs.split_progress_dialog import SplitProgressDialog
from dialogs.split_preview_dialog import SplitPreviewDialog
from dialogs.help_window import HelpWindow

class EmergencyBeaconDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle('Emergency Beacon - Log Analyzer')
        # Make the Emergency Beacon window large by default
        self.setGeometry(100, 100, 1100, 900)
        self.setMinimumSize(1100, 900)
        self.resize(1100, 900)
        layout = QVBoxLayout(self)

        self.status_label = QLabel('')
        layout.addWidget(self.status_label)

        self.error_list = QListWidget()
        self.error_list.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(self.error_list, 1)

        # ...existing code...

        self.current_log_path = None
        # Add button row for user actions
        button_row = QHBoxLayout()
        autodetect_btn = QPushButton('Auto Detect Log')
        autodetect_btn.setToolTip('Scan for starbound.log in common locations')
        autodetect_btn.clicked.connect(self.auto_detect_log)
        button_row.addWidget(autodetect_btn)
        load_btn = QPushButton('Manually Select Log...')
        load_btn.setToolTip('Manually select a starbound.log file')
        load_btn.clicked.connect(self.load_log_file)
        button_row.addWidget(load_btn)
        layout.addLayout(button_row)
        self.show_status('Ready.')
        # Auto-detect log on open
        self.auto_detect_log()

    def show_status(self, msg):
        self.status_label.setText(msg)

    def auto_detect_log(self):
        self.show_status('🔍 Scanning for starbound.log...')
        self.error_list.clear()
        result = emergency_beacon.auto_detect_log()
        if result['success']:
            self.current_log_path = result['logPath']
            self.show_status(f'✅ Found log at: {self.current_log_path}')
            self.analyze_log(self.current_log_path)
        else:
            self.show_status(f'❌ {result["message"]}')

    def load_log_file(self):
        self.error_list.clear()
        file, _ = QFileDialog.getOpenFileName(self, 'Select starbound.log', '', 'Log Files (*.log);;All Files (*)')
        if file:
            self.current_log_path = file
            self.show_status(f'✅ Analyzing: {file}')
            self.analyze_log(file)
        else:
            self.show_status('📁 File selection cancelled')

    def analyze_log(self, log_path):
        log_data = emergency_beacon.read_starbound_log(log_path)
        self.error_list.clear()
        if not log_data['success']:
            self.show_status(f'❌ {log_data.get("message", "Failed to read log.")}')
            return
        crit = log_data['criticalErrors']
        benign = log_data['benignErrors']
        if not crit and not benign:
            self.show_status('✅ No errors found in log!')
            return
        if crit:
            for err in crit:
                explanation = emergency_beacon.explain_starbound_error(err)
                item = QListWidgetItem()
                item.setText(f'CRITICAL: {err}\n{explanation}')
                item.setForeground(Qt.red)
                # Tooltip with explanation
                if explanation:
                    item.setToolTip(explanation)
                else:
                    item.setToolTip('Critical error (hover for details)')
                self.error_list.addItem(item)
        if benign:
            for err in benign:
                explanation = emergency_beacon.get_benign_error_explanation(err)
                item = QListWidgetItem()
                item.setText(f'Benign: {err}')
                item.setForeground(Qt.gray)
                if explanation:
                    item.setToolTip(explanation)
                else:
                    item.setToolTip('✓ Normal Starbound error (hover for details)')
                self.error_list.addItem(item)
        self.show_status(f'Found {len(crit)} critical, {len(benign)} benign errors.')


class SplitAudioWorker(QThread):
    """Worker thread for non-blocking audio splitting with large files."""
    finished = pyqtSignal(dict)  # Emit split results data
    progress_update = pyqtSignal(str, int, int)  # filename, current_file_num, total_files
    error = pyqtSignal(str)
    
    def __init__(self, main_window, segment_length, files_to_split):
        super().__init__()
        self.main_window = main_window
        self.segment_length = segment_length
        self.files_to_split = files_to_split
        self.split_results = {}  # Accumulate results
    
    def run(self):
        """Run audio splitting in background thread."""
        try:
            # Call the actual splitting logic (no dialogs created here)
            results = self.main_window._perform_file_splitting_worker(
                self.segment_length,
                self.files_to_split,
                progress_callback=self._emit_progress
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(f"Audio splitting failed: {str(e)}")
    
    def _emit_progress(self, filename, current_num, total_num):
        """Emit progress signal - called from worker thread."""
        self.progress_update.emit(filename, current_num, total_num)


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Explicitly disable Windows native help button on main window
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Initialize settings manager early
        starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
        self.settings = SettingsManager(starsound_dir)
        
        # Anti-duplicate guard: track last font applied to prevent rapid re-application
        self._last_font_applied = None
        self._last_font_time = 0

        
        # Initialize mod save manager for saving/loading mod configurations
        self.mod_save_manager = ModSaveManager(starsound_dir)
        
        # Initialize track lists FIRST - before any method that uses them
        self.selected_track_type = None
        self.day_tracks = []
        self.night_tracks = []
        self.selected_biomes = []  # Store selected biomes for persistence
        self.remove_vanilla_tracks = False  # 🆕 Track whether user selected "Remove vanilla tracks" checkbox
        # Track whether user has confirmed a patch mode in THIS session (for first-time confirmation dialogs)
        self._mode_confirmed_this_session = False
        # Initialize audio processing dialog (will be created on demand)
        self.audio_dialog = None
        # Load saved patch mode from settings, default to None (unconfirmed)
        self.patch_mode = self.settings.get('last_patch_mode', None)
        # Load saved output format from settings, default to 'pak'
        self.output_format = self.settings.get('last_output_format', 'pak')
        self.replace_selections = {}  # Store Replace selections: {(category, biome): {'day': {idx: path}, 'night': {...}}, ...}
        self.add_selections = {}  # Store Add selections (NEW): {(category, biome): {'day': [path, path, ...], 'night': [...]}, ...}
        self.day_tracks = []  # Legacy: for backward compat, derived from add_selections
        self.night_tracks = []  # Legacy: for backward compat, derived from add_selections
        self.files_needing_split = {}  # Track files >30 min: {file_path: duration_minutes}
        self.split_decisions = {}  # Track user split decisions: {file_path: "ACCEPT" | "DENY"}
        self._skip_config_restore = False  # Flag to prevent loading old config when starting fresh mod
        self.replace_was_selected = False  # Track if Replace mode was ever selected - permanently hides Step 6
        self.crt_effects_enabled = self.settings.get('crt_effects_enabled', False)  # Load saved CRT preference
        print(f'[CRT DEBUG] CRT Effects loaded from settings on startup: {self.crt_effects_enabled}')
        
        # Initialize output format radio buttons (will be populated by show_output_format_selection)
        # Note: These are set during output format selection creation, not persisted as class attributes at init
        self.pak_radio = None
        self.loose_radio = None
        self.output_format_group = None
        
        # Now initialize the GUI components and logger
        self.selected_tracks_label = QLabel('No tracks selected yet.')
        self.selected_tracks_label.setStyleSheet('color: #e6ecff; font-size: 13px; margin-top: 8px; background: transparent; border: none;')  # Font inherited from global stylesheet
        self.selected_tracks_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        
        # Initialize scanline overlay and logger
        self._init_scanline_overlay()
        self.logger = get_logger()
        
        # Check if vanilla tracks are available at startup
        self._check_vanilla_tracks_on_startup()
        # Always set screenshot folder to StarSound/pygui/screenshots
        from utils.screenshot_manager import set_screenshot_folder
        screenshot_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
        set_screenshot_folder(screenshot_dir)
        self.logger.log('App launched')
        
        # PRE-LOAD all custom fonts FIRST so they're available when we apply saved font
        self._preload_custom_fonts()
        
        # Load saved font preference from settings, default to 'Hobo'
        from PyQt5.QtGui import QFontDatabase, QFont
        saved_font = self.settings.get('current_font', 'Hobo')
        self.current_font = saved_font  # Track current font for dialogs
        self.logger.log(f'Loading font from settings on startup: {saved_font}')

        # Connect completed files signal
        self.completed_files_signal.connect(self.append_completed_file)
        self.setWindowTitle('StarSound - Music Mod Generator')
        # Make the app larger by default (e.g., 1100x900)
        self.setGeometry(100, 100, 1100, 900)
        self.setMinimumSize(1100, 900)
        self.setMaximumSize(1600, 1200)
        self.resize(1100, 900)

        # Connect signals for thread-safe GUI updates
        self.ffmpeg_log_signal.connect(self.ffmpeg_log_box_append)
        self.audio_status_signal.connect(self.set_audio_status_label)

        # Modern dark mode stylesheet with rounded buttons and improved scaling
        # Apply stylesheet and font (consolidated into one place)
        self._apply_stylesheet_with_font(saved_font)
        self._apply_font_to_app(saved_font)

        # High-DPI attributes are set at the top of the script before QApplication is created

        # Add a QMenuBar for diagnostic visibility
        menubar = QMenuBar(self)
        
        # File Menu - Mod Management
        file_menu = menubar.addMenu('File')
        
        save_mod_action = QAction('Save Current Mod', self)
        save_mod_action.triggered.connect(self.on_save_mod)
        file_menu.addAction(save_mod_action)
        
        load_mod_action = QAction('Load Mod...', self)
        load_mod_action.triggered.connect(self.on_load_mod)
        file_menu.addAction(load_mod_action)
        
        new_mod_action = QAction('New Mod', self)
        new_mod_action.triggered.connect(self.on_new_mod)
        file_menu.addAction(new_mod_action)
        
        file_menu.addSeparator()
        
        browse_saves_action = QAction('Browse Mod Saves Folder', self)
        browse_saves_action.triggered.connect(self.on_browse_mod_saves)
        file_menu.addAction(browse_saves_action)
        
        # Info Menu
        info_menu = menubar.addMenu('Info')
        
        # Guide action - opens comprehensive help system
        guide_action = QAction('📖 Guide && Documentation', self)
        guide_action.setToolTip('Open comprehensive help and documentation')
        def show_guide():
            try:
                help_dialog = HelpWindow(self, 'intro')
                help_dialog.exec_()
            except Exception as e:
                QMessageBox.warning(self, 'Help Error', f'Could not open help:\n{str(e)}')
        guide_action.triggered.connect(show_guide)
        info_menu.addAction(guide_action)
        
        info_menu.addSeparator()
        
        shortcuts_action = QAction('⌨️ Keyboard Shortcuts', self)
        def show_shortcuts():
            dlg = QDialog(self)
            dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            dlg.setWindowTitle('Keyboard Shortcuts')
            dlg.setMinimumSize(400, 260)
            layout = QVBoxLayout(dlg)
            label = QLabel('''<b>Keyboard Shortcuts</b><br><br>
            <span style="color:#4e8cff;">Ctrl+S</span>: Take screenshot<br>
            <span style="color:#4e8cff;">Ctrl+R</span>: Random Mod Name<br>
            <span style="color:#4e8cff;">Ctrl+F</span>: Browse Mod Folder<br>
            <span style="color:#6bffb0;">Ctrl+O</span>: Browse Audio File<br>
            <span style="color:#ff6b6b;">Esc</span>: Close popups<br>
            ''')
            label.setStyleSheet('''
                color: #e6ecff;
                font-family: "Hobo";
                font-size: 16px;
                background: #181c2a;
                border-radius: 12px;
                padding: 18px;
                margin-top: 12px;
            ''')
            layout.addWidget(label)
            close_btn = QPushButton('Close')
            close_btn.setToolTip('Close this shortcuts guide')
            close_btn.clicked.connect(dlg.accept)
            layout.addWidget(close_btn)
            dlg.exec_()
        shortcuts_action.triggered.connect(show_shortcuts)
        info_menu.addAction(shortcuts_action)
        
        info_menu.addSeparator()
        
        # GitHub Issues action - opens issue tracker in browser
        github_action = QAction('🐛 Report || Suggest (GitHub)', self)
        github_action.setToolTip('Report bugs or suggest features on GitHub')
        def open_github_issues():
            try:
                webbrowser.open('https://github.com/AHSpire/StarSound/issues')
            except Exception as e:
                QMessageBox.warning(self, 'Browser Error', f'Could not open GitHub issues page:\n{str(e)}')
        github_action.triggered.connect(open_github_issues)
        info_menu.addAction(github_action)
        
        # Add a 'CRT Effects' menu with a toggle action for accessibility
        # Note: crt_effects_enabled was already loaded from settings on line 264
        crt_menu = menubar.addMenu('CRT Effects')
        # Set initial menu text based on saved state
        initial_text = 'Disable CRT Effects' if self.crt_effects_enabled else 'Enable CRT Effects'
        self.toggle_crt_action = QAction(initial_text, self)
        self.toggle_crt_action.setCheckable(True)
        self.toggle_crt_action.setChecked(self.crt_effects_enabled)
        def toggle_crt_effects():
            self.crt_effects_enabled = not self.crt_effects_enabled
            action_str = 'ENABLED' if self.crt_effects_enabled else 'DISABLED'
            print(f'[CRT DEBUG] User toggled CRT Effects: {action_str}')
            if hasattr(self, 'settings'):
                self.settings.set('crt_effects_enabled', self.crt_effects_enabled)
                print(f'[CRT DEBUG] CRT Effects saved to settings: {self.crt_effects_enabled}')
            if hasattr(self, '_scanline_overlay') and self._scanline_overlay:
                self._scanline_overlay.setVisible(self.crt_effects_enabled)
                print(f'[CRT DEBUG] Scanline overlay visibility set to: {self.crt_effects_enabled}')
            self.toggle_crt_action.setText('Enable CRT Effects' if not self.crt_effects_enabled else 'Disable CRT Effects')
            self.toggle_crt_action.setChecked(self.crt_effects_enabled)
        self.toggle_crt_action.triggered.connect(toggle_crt_effects)
        crt_menu.addAction(self.toggle_crt_action)
        
        # Add a 'Fonts' menu for font selection
        fonts_menu = menubar.addMenu('Fonts')
        # Get available system fonts (filters out fonts that don't exist)
        available_fonts = self._get_available_fonts()
        current_font = self.settings.get('current_font', 'Hobo')
        
        # Create a font action for each available font
        for font_name in available_fonts:
            font_action = QAction(font_name, self)
            font_action.setCheckable(True)
            font_action.setChecked(font_name == current_font)
            # Store font name as data on the action for comparison
            font_action.setData(font_name)
            # Preview the font by displaying its name in the actual font
            from PyQt5.QtGui import QFont
            preview_font = QFont(font_name, 10)
            font_action.setFont(preview_font)
            # Create closure to capture font_name for the lambda
            def create_font_setter(fname):
                def set_font_and_save():
                    self._apply_font_to_app(fname)
                    self.settings.set('current_font', fname)
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.log(f'Font changed to: {fname}')
                    # Update all font actions to reflect the new selection
                    # IMPORTANT: Block signals while updating to prevent recursive triggering
                    for action in fonts_menu.actions():
                        action.blockSignals(True)
                    
                    for action in fonts_menu.actions():
                        action_font = action.data()
                        action.setChecked(action_font == fname)
                    
                    for action in fonts_menu.actions():
                        action.blockSignals(False)
                return set_font_and_save
            
            font_action.triggered.connect(create_font_setter(font_name))

            fonts_menu.addAction(font_action)
        
        self.setMenuBar(menubar)

        # --- QToolBar with Screenshot Button ---
        toolbar = QToolBar('Main Toolbar')
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        # Add Starbound logo/icon placeholder (replace with actual logo if available)
        logo_label = QLabel('★')
        logo_label.setStyleSheet('font-size: 22px; color: #4e8cff; padding-right: 8px;')
        toolbar.addWidget(logo_label)
        toolbar.addWidget(QLabel('StarSound Toolbar:'))
        screenshot_action = QAction('📸 Screenshot', self)
        screenshot_action.setToolTip('Take a screenshot of the app window')
        screenshot_action.triggered.connect(lambda: [self.play_click_sound(), self.take_screenshot_action()])
        toolbar.addAction(screenshot_action)

        # Add Config Health and Emergency Beacon buttons to toolbar
        config_health_action = QAction('🩺 Config Health', self)
        config_health_action.setToolTip('Check Starbound config health')
        config_health_action.triggered.connect(lambda: [self.play_click_sound(), self.show_config_health_checker()])
        toolbar.addAction(config_health_action)
        # QToolBar styling is handled by global stylesheet (stylesheet_manager.py)

        emergency_beacon_action = QAction('🚨 Emergency Beacon', self)
        emergency_beacon_action.setToolTip('Scan Starbound logs for errors and explanations')
        emergency_beacon_action.triggered.connect(lambda: [self.play_click_sound(), self.show_emergency_beacon()])
        toolbar.addAction(emergency_beacon_action)
        
        # Audio Processing Settings action
        audio_config_action = QAction('🎛️ Audio Processing', self)
        audio_config_action.setToolTip('Configure audio processing settings:\n✓ Compression • EQ • Normalization • Fade • and more!\n✓ Genre-specific presets available')
        audio_config_action.triggered.connect(lambda: [self.play_click_sound(), self.show_audio_config_dialog()])
        toolbar.addAction(audio_config_action)
        
        # Help button - opens comprehensive guide
        help_action = QAction('🛟 Help', self)
        help_action.setToolTip('Open StarSound guide and documentation')
        def show_main_help():
            try:
                help_dialog = HelpWindow(self, 'intro')
                help_dialog.exec_()
            except Exception as e:
                QMessageBox.warning(self, 'Help Error', f'Could not open help:\n{str(e)}')
        help_action.triggered.connect(show_main_help)
        toolbar.addAction(help_action)
        
        # Apply toolbar stylesheet for proper button styling and hover/pressed states
        toolbar.setStyleSheet(get_toolbar_style())
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # Central widget and scroll area (QWidget as central, scroll area inside)
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        # Screenshot status label (for screenshot feedback, small and at top)
        self.screenshot_status_label = QLabel('')
        self.screenshot_status_label.setAlignment(Qt.AlignLeft)
        self.screenshot_status_label.setWordWrap(True)
        self.screenshot_status_label.setStyleSheet('color: #e6ecff; font-size: 13px; background: #23283b; border-radius: 6px; padding: 4px; margin-bottom: 2px;')
        self.screenshot_status_label.setFixedHeight(24)
        main_layout.addWidget(self.screenshot_status_label)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            'QScrollArea { background-color: #23283b; border: none; } '
            'QScrollBar:vertical { '
            '  width: 16px; '
            '  background: #23283b; '
            '  border-radius: 8px; '
            '  margin: 0px; '
            '} '
            'QScrollBar::handle:vertical { '
            '  background: #3a6ea5; '
            '  border-radius: 8px; '
            '  min-height: 20px; '
            '  margin: 4px 4px 4px 4px; '
            '} '
            'QScrollBar::handle:vertical:hover { '
            '  background: #5a8ed5; '
            '} '
            'QScrollBar::handle:vertical:pressed { '
            '  background: #2a5e95; '
            '} '
            'QScrollBar::add-line:vertical { border: none; background: none; } '
            'QScrollBar::sub-line:vertical { border: none; background: none; } '
        )
        scroll_content = QWidget()
        self.scroll_area.setWidget(scroll_content)
        scroll_layout = QVBoxLayout(scroll_content)
        # ...existing code...
        # No patch status label here; only audio_status_label is shown below Completed Files

        # Mod Folder Section
        mod_grid = QGridLayout()
        mod_grid.setHorizontalSpacing(0)  # Remove horizontal gap between columns
        self.folder_input = QLineEdit()
        detected_mods = get_mods_folder() or ''
        if detected_mods:
            self.folder_input.setText(detected_mods)
        self.browse_btn = QPushButton('Browse')
        self.browse_btn.setToolTip('Shortcut: Ctrl+F')
        self.browse_btn.clicked.connect(lambda: [self.play_click_sound(), self.browse_folder()])
        # Group Mod Folder input and Browse button in a horizontal layout
        modfolder_row = QHBoxLayout()
        modfolder_row.setSpacing(4)
        modfolder_row.setContentsMargins(0, 0, 0, 0)
        modfolder_row.addWidget(self.folder_input)
        modfolder_row.addWidget(self.browse_btn)
        # --- Import atomicwriter for staging save ---
        from utils.atomicwriter import save_mod_to_staging
        from utils.random_mod_name import generate_random_mod_name
        
        # Try to load saved mod name from settings, use random if not available
        # NOTE: Always start fresh with a new random name on app startup
        # Users can explicitly load a saved mod via File → Load Mod...
        saved_mod_name = ''  # Disable auto-loading of last mod on startup
        name = generate_random_mod_name()
        is_auto_generated = True  # Always treat as auto-generated on startup
        print('[DEBUG] Generated mod name:', name)
        
        # 🆕 FIX: Fresh start on every app launch - always with a random name
        # Users can load saved mods explicitly via File → Load Mod...
        print(f'[PERSIST] Auto-generated fresh name on startup: {name}')
        
        # Track the current auto-generated name so we can detect user edits
        self._current_autogen_name = name if is_auto_generated else None
        
        self.modname_input = QLineEdit(name)
        print('[DEBUG] ModName QLineEdit after creation:', self.modname_input.text())
        print(f'[DEBUG] LINE 1507: Skipping logger.update_metadata() for now to unblock initialization', flush=True)
        # TODO: Fix whatever is hanging in logger.update_metadata()
        # self.logger.update_metadata(
        #     mod_name=self.modname_input.text().strip(),
        #     mod_path=self.folder_input.text().strip(),
        #     game_path=None,
        #     ffmpeg_path=None,
        #     gui_theme='dark',
        #     last_action='App Launched'
        # )
        print(f'[DEBUG] LINE 1520: Skipped logger call, continuing initialization', flush=True)

        # Only grey out TRULY auto-generated names; saved names should appear normal
        if is_auto_generated:
            self.modname_input.setStyleSheet('color: #888888; background: #283046; border-radius: 8px; border: 1px solid #3a4a6a; font-size: 15px;')
            self._modname_autofill = True
        else:
            self.modname_input.setStyleSheet('color: #e6ecff; background: #283046; border-radius: 8px; border: 1px solid #3a4a6a; font-size: 15px;')
            self._modname_autofill = False
        def on_modname_focus_in(event):
            if self._modname_autofill:
                self.modname_input.clear()
                self.modname_input.setStyleSheet('color: #e6ecff; background: #283046; border-radius: 8px; border: 1px solid #3a4a6a; font-size: 15px;')
                self._modname_autofill = False
            QLineEdit.focusInEvent(self.modname_input, event)
        self.modname_input.focusInEvent = on_modname_focus_in

        # --- Save to staging when mod name changes ---
        self._last_saved_modname = None
        def get_current_mod_data():
            return {
                'biome': '',
                'dayTracks': [],
                'nightTracks': [],
                'modName': self.modname_input.text().strip() or 'blank_mod',
                'patchMode': ''
            }
        def save_current_mod_to_staging():
            mod_name = self.modname_input.text().strip() or 'blank_mod'
            if mod_name == self._last_saved_modname:
                return  # Don't save duplicate names
            starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
            mod_folder = save_mod_to_staging(get_current_mod_data(), mod_name, starsound_dir)
            self._last_saved_modname = mod_name
        # Only save to staging when Mod Name field loses focus (focus out)
        def on_modname_focus_out(event):
            save_current_mod_to_staging()
            new_name = self.modname_input.text().strip()
            self.logger.update_metadata(mod_name=new_name)
            self.logger.log(f'Mod name edited and focus lost: {new_name}')
            
            # Save the new name to settings so it persists on app restart
            if new_name and new_name != 'blank_mod':
                self.settings.set('last_mod_name', new_name)
            
            # NEW: When mod name changes, attempt to restore from that mod's saved config
            if new_name and new_name != 'blank_mod' and not self._skip_config_restore:
                print(f'[PERSIST] Mod name changed to: {new_name}')
                # Try to restore from the new mod name
                config = self.mod_save_manager.load_mod(new_name + '.json')
                if config:
                    print(f'[PERSIST] Found saved config for "{new_name}", restoring...')
                    # Copy config to UI (without triggering a save)
                    self.day_tracks = config.get('day_tracks', [])
                    self.night_tracks = config.get('night_tracks', [])
                    self.add_selections = config.get('add_selections', {})  # Restore per-biome Add selections (NEW)
                    self.selected_biomes = config.get('selected_biomes', [])
                    
                    # Sync: if add_selections has biomes but selected_biomes is empty, populate it
                    if self.add_selections and not self.selected_biomes:
                        self.selected_biomes = list(self.add_selections.keys())
                        print(f'[PERSIST] Synced selected_biomes from add_selections during mod name change')
                    
                    self.patch_mode = config.get('patch_mode', None)
                    # If we're restoring a saved patch_mode, mark it as confirmed (was confirmed in previous session)
                    if config.get('patch_mode'):
                        self._mode_confirmed_this_session = True
                    self.replace_selections = config.get('replace_selections', {})
                    self.selected_track_type = config.get('selected_track_type', None)
                    print(f'[PERSIST] Restored from config: {len(self.day_tracks)} day tracks, {len(self.night_tracks)} night tracks, {len(self.selected_biomes)} biomes')
                    # Update UI display
                    self.update_selected_tracks_label()
                    self.update_patch_btn_state()
                else:
                    print(f'[PERSIST] No saved config for "{new_name}", cleared UI')
                    # Clear UI for new mod name
                    self.day_tracks = []
                    self.night_tracks = []
                    self.add_selections = {}  # Clear per-biome Add selections (NEW)
                    self.night_tracks = []
                    self.selected_biomes = []
                    self.patch_mode = None
                    self._mode_confirmed_this_session = False  # Reset flag for new mod
                    self.replace_selections = {}
                    self.selected_track_type = None
                    self.update_selected_tracks_label()
                    self.update_patch_btn_state()
            elif self._skip_config_restore:
                print(f'[PERSIST] Skipping config restore (within "New Mod" session), clearing UI')
                # Fresh start - clear everything
                self.day_tracks = []
                self.night_tracks = []
                self.add_selections = {}
                self.selected_biomes = []
                self.patch_mode = None
                self._mode_confirmed_this_session = False
                self.replace_selections = {}
                self.selected_track_type = None
                self.update_selected_tracks_label()
                self.update_patch_btn_state()
            
            QLineEdit.focusOutEvent(self.modname_input, event)
        self.modname_input.focusOutEvent = on_modname_focus_out
        # If user rolls a new name, reset autofill state and style
        def set_autofill_name(new_name):
            self.modname_input.setText(new_name)
            self._current_autogen_name = new_name  # Track it for comparison
            self.modname_input.setStyleSheet('color: #888888; background: #283046; border-radius: 8px; border: 1px solid #3a4a6a; font-size: 15px; font-family: "Hobo";')
            self._modname_autofill = True
            # Note: Save only happens when user checks the checkbox to confirm
            self.logger.update_metadata(mod_name=new_name)
            self.logger.log(f'Mod name rolled: {new_name} (awaiting checkbox confirmation)')
        # Patch dice_btn click to use set_autofill_name
        def roll_mod_name():
            self.play_click_sound()
            
            # SAFETY CHECK: If current mod name exists in staging, warn user
            current_name = self.modname_input.text().strip()
            if current_name:
                from pathlib import Path
                starsound_dir = Path(__file__).parent.parent
                staging_dir = starsound_dir / 'staging'
                current_mod_path = staging_dir / current_name
                
                if current_mod_path.exists():
                    # Current mod is saved - warn before rolling new name
                    reply = QMessageBox.warning(
                        self,
                        '⚠️ Existing Mod Detected',
                        f'You have an existing mod named "{current_name}" in staging.\n\n'
                        f'Rolling a new random name will create a NEW mod, abandoning the current one.\n\n'
                        f'Are you sure you want to continue?',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No  # Default to NO (safe default)
                    )
                    
                    if reply != QMessageBox.Yes:
                        return  # User cancelled - don't change the name
            
            # Safe to roll - generate new name
            from utils.random_mod_name import generate_random_mod_name
            new_name = generate_random_mod_name()
            
            # SAFETY: Uncheck the confirmation checkbox to prevent accidental saves
            self.modname_confirm_checkbox.setChecked(False)
            
            set_autofill_name(new_name)
        # Add dice icon next to Mod Name, visually grouped
        print(f'[DEBUG] Starting dice icon setup')
        from PyQt5.QtGui import QPixmap
        # Dice icon as QLabel, transparent QPushButton overlay for click
        print(f'[DEBUG] Loading dice icon from assets')
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'photos', 'diceicon.png')
        print(f'[DEBUG] Icon path: {icon_path}')
        dice_icon = QPixmap(icon_path)
        print(f'[DEBUG] QPixmap loaded, isNull: {dice_icon.isNull()}')
        dice_label = QLabel()
        if not dice_icon.isNull():
            dice_label.setPixmap(dice_icon)
            dice_label.setFixedSize(dice_icon.size())
        else:
            dice_label.setText('🎲')
            dice_label.setStyleSheet('color: #4e8cff; font-size: 18px; border: none; background: transparent;')
            dice_label.setFixedSize(22, 22)
            print(f'[ERROR] Dice icon failed to load: {icon_path}')
        dice_btn = QPushButton()
        dice_btn.setToolTip('Shortcut: Ctrl+R')
        dice_btn.setFixedSize(dice_label.size())
        dice_btn.setStyleSheet('background: transparent; border: none;')
        dice_btn.setCursor(Qt.PointingHandCursor)
        dice_btn.setFocusPolicy(Qt.NoFocus)
        dice_btn.setFlat(True)
        dice_btn.setText('')
        dice_btn.raise_()
        # Add QCheckBox for confirming random name
        from PyQt5.QtWidgets import QCheckBox
        self.modname_confirm_checkbox = QCheckBox()
        self.modname_confirm_checkbox.setChecked(False)  # Start UNCHECKED so field is editable by default
        self.modname_confirm_checkbox.setText('Use Random Name')  # Make it explicit what the checkbox does
        self.modname_confirm_checkbox.setToolTip('Check to accept the random name. Uncheck to enter your own.')
        self.modname_confirm_checkbox.setStyleSheet('QCheckBox { color: #e6ecff; font-size: 14px; margin-left: 8px; }')
        self.modname_input.setReadOnly(False)  # Field is editable by default
        def on_checkbox_toggled(checked):
            if checked:
                # User confirms to use this name - lock it in and turn WHITE (confirmed state)
                self.modname_input.setReadOnly(True)
                # Clear the autofill flag so focus handler won't clear the field
                self._modname_autofill = False
                # Always turn WHITE when confirmed (regardless of whether it was auto-generated)
                self.modname_input.setStyleSheet('color: #e6ecff; background: #283046; border-radius: 8px; border: 1px solid #3a4a6a; font-size: 15px;')
                current_name = self.modname_input.text().strip()
                print(f'[PERSIST] Checkbox checked: {current_name}')
                save_current_mod_to_staging()  # Save when user confirms
                print(f'[PERSIST] Saved to staging')
                self.settings.set('last_mod_name', current_name)  # Save to persistent settings
                print(f'[PERSIST] Saved to settings.json: last_mod_name={current_name}')
                # Allow normal config restore on future name changes (fresh start is done)
                self._skip_config_restore = False
                print(f'[PERSIST] Reset _skip_config_restore flag - normal mode restore enabled')
            else:
                # User unchecks - allow editing
                self.modname_input.setReadOnly(False)
                # Keep grey if it's an auto-generated placeholder, change to white if user already typed something
                if self._modname_autofill:
                    self.modname_input.setStyleSheet('color: #888888; background: #283046; border-radius: 8px; border: 1px solid #3a4a6a; font-size: 15px;')
                else:
                    self.modname_input.setStyleSheet('color: #e6ecff; background: #283046; border-radius: 8px; border: 1px solid #3a4a6a; font-size: 15px;')
        self.modname_confirm_checkbox.toggled.connect(on_checkbox_toggled)
        
        # When user types in the name field, turn it white if they've changed it from the auto-generated name
        def on_modname_text_changed(text):
            # If field is empty, don't change styling yet
            if not text.strip():
                return
            # If user has edited the auto-generated name, turn it white and mark as custom
            if self._modname_autofill and text.strip() != self._current_autogen_name:
                self._modname_autofill = False
                if not self.modname_input.isReadOnly():
                    self.modname_input.setStyleSheet('color: #e6ecff; background: #283046; border-radius: 8px; border: 1px solid #3a4a6a; font-size: 15px; font-family: "Hobo";')
        self.modname_input.textChanged.connect(on_modname_text_changed)
        
        def roll_mod_name():
            self.play_click_sound()
            
            # SAFETY CHECK: If current mod name exists in staging, warn user
            current_name = self.modname_input.text().strip()
            if current_name:
                from pathlib import Path
                starsound_dir = Path(__file__).parent.parent
                staging_dir = starsound_dir / 'staging'
                current_mod_path = staging_dir / current_name
                
                if current_mod_path.exists():
                    # Current mod is saved - warn before rolling new name
                    reply = QMessageBox.warning(
                        self,
                        '⚠️ Existing Mod Detected',
                        f'You have an existing mod named "{current_name}" in staging.\n\n'
                        f'Rolling a new random name will create a NEW mod, abandoning the current one.\n\n'
                        f'Are you sure you want to continue?',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No  # Default to NO (safe default)
                    )
                    
                    if reply != QMessageBox.Yes:
                        return  # User cancelled - don't change the name
            
            # Safe to roll - generate new name
            from utils.random_mod_name import generate_random_mod_name
            new_name = generate_random_mod_name()
            
            # SAFETY: Uncheck the confirmation checkbox to prevent accidental saves
            self.modname_confirm_checkbox.setChecked(False)
            
            set_autofill_name(new_name)
        dice_btn.clicked.connect(roll_mod_name)
        # Group icon, checkbox, and input in a horizontal layout
        modname_row = QHBoxLayout()
        modname_row.setSpacing(4)
        modname_row.setContentsMargins(0, 0, 0, 0)
        icon_container = QWidget()
        icon_container.setFixedSize(dice_label.size())
        icon_container_layout = QHBoxLayout(icon_container)
        icon_container_layout.setContentsMargins(0, 0, 0, 0)
        icon_container_layout.setSpacing(0)
        # Absolute positioning: QLabel and transparent QPushButton overlap
        dice_label.setParent(icon_container)
        dice_btn.setParent(icon_container)
        dice_label.move(0, 0)
        dice_btn.move(0, 0)
        dice_label.show()
        dice_btn.show()
        modname_row.addWidget(icon_container)
        modname_row.addWidget(self.modname_confirm_checkbox)
        modname_row.addWidget(self.modname_input)
        mod_name_label = QLabel('Step 1: Mod Name:')
        mod_name_label.setContentsMargins(0, 0, 0, 0)
        # --- SWAPPED ORDER, now with grouped Mod Folder row ---
        mod_grid.addWidget(mod_name_label, 0, 0)
        mod_grid.addLayout(modname_row, 0, 1, 1, 2)
        mod_grid.addWidget(QLabel('Step 2: Mod Folder:'), 1, 0)
        mod_grid.addLayout(modfolder_row, 1, 1, 1, 2)
        mod_grid.setColumnMinimumWidth(0, 80)
        mod_grid.setColumnStretch(1, 1)
        mod_grid.setHorizontalSpacing(2)
        scroll_layout.addLayout(mod_grid)

        # Audio Validation Section
        audio_grid = QGridLayout()
        audio_grid.addWidget(QLabel('Step 3: Audio File(s):'), 0, 0)
        self.audio_browse_btn = QPushButton('Browse')
        self.audio_browse_btn.setToolTip('Shortcut: Ctrl+O')
        self.audio_browse_btn.clicked.connect(lambda: [self.play_click_sound(), self.browse_audio()])
        audio_grid.addWidget(self.audio_browse_btn, 0, 1)
        self.audio_clear_btn = QPushButton('Clear Selected Files')
        self.audio_clear_btn.setToolTip('Remove all selected audio files and start over')
        self.audio_clear_btn.clicked.connect(lambda: [self.play_click_sound(), self.clear_audio()])
        audio_grid.addWidget(self.audio_clear_btn, 0, 2)

        # Add label to show selected audio files (filenames only)
        self.selected_files_label = QLabel('')
        self.selected_files_label.setStyleSheet('color: #e6ecff; font-size: 12px; margin: 2px 0 2px 0; background: transparent; border: none;')
        audio_grid.addWidget(self.selected_files_label, 1, 0, 1, 4)
        
        scroll_layout.addLayout(audio_grid)
        
        # ===== CONVERT TO OGG BUTTON =====
        audio_btn_row = QHBoxLayout()
        self.convert_audio_btn = QPushButton('Step 4: Convert to OGG')
        self.convert_audio_btn.setToolTip('Convert selected audio files to OGG format for Starbound compatibility')
        self.convert_audio_btn.clicked.connect(lambda: [self.play_click_sound(), self.convert_audio()])
        audio_btn_row.addWidget(self.convert_audio_btn)
        scroll_layout.addLayout(audio_btn_row)

        # Add a small, scrollable log box for FFmpeg output
        # Group Active Log and Completed Files tightly together
        log_group = QVBoxLayout()
        log_group.setSpacing(2)
        log_group.setContentsMargins(0, 0, 0, 0)

        # Active Log
        log_row = QHBoxLayout()
        log_label = QLabel('Active Log')
        log_label.setStyleSheet('color: #e6ecff; font-size: 13px; padding-right: 12px;')
        log_row.addWidget(log_label)
        from PyQt5.QtWidgets import QSizePolicy
        self.ffmpeg_log_box = QTextEdit()
        self.ffmpeg_log_box.setReadOnly(True)
        self.ffmpeg_log_box.setFixedHeight(80)
        self.ffmpeg_log_box.setStyleSheet(
            'QTextEdit { '
            '  background: #181c2a; '
            '  color: #e6ecff; '
            '  font-size: 12px; '
            '  border-radius: 6px; '
            '  border: 1px solid #3a4a6a; '
            '  padding: 4px; '
            '} '
            'QTextEdit:scrollarea { background: #181c2a; } '
            'QScrollBar:vertical { '
            '  width: 14px; '
            '  background: #0f1620; '
            '  border-radius: 7px; '
            '  margin: 0px; '
            '} '
            'QScrollBar::handle:vertical { '
            '  background: #3a6ea5; '
            '  border-radius: 7px; '
            '  min-height: 15px; '
            '  margin: 2px 2px 2px 2px; '
            '} '
            'QScrollBar::handle:vertical:hover { background: #5a8ed5; } '
            'QScrollBar::add-line:vertical { border: none; } '
            'QScrollBar::sub-line:vertical { border: none; } '
        )
        self.ffmpeg_log_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        log_row.addWidget(self.ffmpeg_log_box, 1)
        log_group.addLayout(log_row)

        # Completed Files
        completed_row = QHBoxLayout()
        completed_label = QLabel('Completed\nFiles')
        completed_label.setStyleSheet('color: #e6ecff; font-size: 13px; padding-right: 12px;')
        completed_label.setFixedWidth(90)
        completed_label.setAlignment(Qt.AlignCenter)
        completed_row.addWidget(completed_label)
        self.completed_files_box = QTextEdit()
        self.completed_files_box.setReadOnly(True)
        self.completed_files_box.setFixedHeight(80)
        self.completed_files_box.setStyleSheet(
            'QTextEdit { '
            '  background: #181c2a; '
            '  color: #e6ecff; '
            '  font-size: 12px; '
            '  border-radius: 6px; '
            '  border: 1px solid #3a4a6a; '
            '  padding: 4px; '
            '} '
            'QTextEdit:scrollarea { background: #181c2a; } '
            'QScrollBar:vertical { '
            '  width: 14px; '
            '  background: #0f1620; '
            '  border-radius: 7px; '
            '  margin: 0px; '
            '} '
            'QScrollBar::handle:vertical { '
            '  background: #3a6ea5; '
            '  border-radius: 7px; '
            '  min-height: 15px; '
            '  margin: 2px 2px 2px 2px; '
            '} '
            'QScrollBar::handle:vertical:hover { background: #5a8ed5; } '
            'QScrollBar::add-line:vertical { border: none; } '
            'QScrollBar::sub-line:vertical { border: none; } '
        )
        self.completed_files_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        completed_row.addWidget(self.completed_files_box, 1)

        log_group.addLayout(completed_row)
        scroll_layout.addLayout(log_group)

        # Add Open Music Folder button directly underneath Completed Files box
        self.open_music_btn = QPushButton('Open Music Folder')
        self.open_music_btn.setStyleSheet('''QPushButton {
            background-color: #3a6ea5;
            color: #e6ecff;
            border-radius: 8px;
            font-size: 14px;
            margin: 4px 0 4px 0;
            border: 1px solid #4e8cff;
        }
        QPushButton:hover {
            background-color: #4e8cff;
            border: 1px solid #6bbcff;
        }''')
        self.open_music_btn.setToolTip('Open the music folder for the current mod including any converted audio files')
        self.open_music_btn.setEnabled(False)
        scroll_layout.addWidget(self.open_music_btn)

        def enable_open_music_btn():
            mod_name = self.modname_input.text().strip()
            self.open_music_btn.setEnabled(bool(mod_name))
        self.modname_input.textChanged.connect(enable_open_music_btn)
        enable_open_music_btn()

        def open_music_folder():
            mod_name = self.modname_input.text().strip()
            if not mod_name:
                return
            import os
            from pathlib import Path
            starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
            staging_dir = starsound_dir / 'staging'
            safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
            music_folder = staging_dir / safe_mod_name / 'music'
            if not music_folder.exists():
                QMessageBox.warning(self, 'Open Music Folder', f'Music folder does not exist: {music_folder}')
                return
            os.startfile(str(music_folder))
        self.open_music_btn.clicked.connect(open_music_folder)

        # Add status label directly under Open Music Folder
        self.audio_status_label = QLabel('')
        self.audio_status_label.setAlignment(Qt.AlignCenter)
        self.audio_status_label.setWordWrap(True)
        # Plain text, no box styling
        self.audio_status_label.setStyleSheet('color: #e6ecff; font-size: 15px; margin: 2px 0 2px 0; background: transparent; border: none;')
        scroll_layout.addWidget(self.audio_status_label)


        # Set scroll_content to minimum vertical size policy so it doesn't stretch
        scroll_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # Add the scroll area to the main layout (fills the window)
        main_layout.addWidget(self.scroll_area)
        print(f'[DEBUG] Added scroll area to main layout')

        # Add user choice buttons directly below Open Music Folder (inside scroll area)
        # Step 5 label centered above the buttons
        print(f'[DEBUG] Beginning Step 5 setup')
        step5_label = QLabel('Step 5: Select Patching Method')
        step5_label.setStyleSheet('color: #e6ecff; font-size: 13px; margin-bottom: 6px;')
        step5_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        scroll_layout.addWidget(step5_label, alignment=Qt.AlignHCenter)

        user_btn_row = QHBoxLayout()

        self.add_to_game_btn = QPushButton('Add to Game')
        self.add_to_game_btn.setToolTip('Add your music to the game alongside the original tracks.')
        self.add_to_game_btn.setStyleSheet('''QPushButton {
            background-color: #3a6ea5;
            color: #e6ecff;
            border-radius: 8px;
            font-size: 13px;
            margin: 4px 8px 4px 0;
            border: 1px solid #4e8cff;
        }
        QPushButton:hover {
            background-color: #4e8cff;
            border: 1px solid #6bbcff;
        }''')
        self.add_to_game_btn.clicked.connect(lambda: [self.play_click_sound(), self.on_add_to_game()])
        user_btn_row.addWidget(self.add_to_game_btn)

        self.replace_btn = QPushButton('Replace Base Game Music')
        self.replace_btn.setToolTip('Replace all original music with your selected tracks.')
        self.replace_btn.setStyleSheet('''QPushButton {
            background-color: #3a6ea5;
            color: #e6ecff;
            border-radius: 8px;
            font-size: 13px;
            margin: 4px 8px 4px 0;
            border: 1px solid #4e8cff;
        }
        QPushButton:hover {
            background-color: #4e8cff;
            border: 1px solid #6bbcff;
        }''')
        self.replace_btn.clicked.connect(lambda: [self.play_click_sound(), self.on_replace()])
        user_btn_row.addWidget(self.replace_btn)

        self.replace_and_add_btn = QPushButton('Both: Replace and Add Music')
        self.replace_and_add_btn.setToolTip('Replace specific tracks AND add new tracks to the music pool.')
        self.replace_and_add_btn.setStyleSheet('''QPushButton {
            background-color: #3a6ea5;
            color: #e6ecff;
            border-radius: 8px;
            font-size: 13px;
            margin: 4px 0 4px 0;
            border: 1px solid #4e8cff;
        }
        QPushButton:hover {
            background-color: #4e8cff;
            border: 1px solid #6bbcff;
        }''')
        self.replace_and_add_btn.clicked.connect(lambda: [self.play_click_sound(), self.on_replace_and_add()])
        user_btn_row.addWidget(self.replace_and_add_btn)

        scroll_layout.addLayout(user_btn_row)
        print(f'[DEBUG] Completed Step 5 buttons setup')
        
        # Insert track selection (Day/Night) immediately after patching method selection
        print(f'[DEBUG] Calling show_step6_track_choice()')
        self.show_step6_track_choice()
        print(f'[DEBUG] show_step6_track_choice() completed')
        if hasattr(self, 'step6_widget') and self.step6_widget:
            scroll_layout.addWidget(self.step6_widget)
        
        # Create "View All Tracks" button (SEPARATE from Step 6, so it's visible in Replace mode)
        self.view_tracks_btn = QPushButton('📋 View All Tracks')
        self.view_tracks_btn.setToolTip('Open a detailed view of all selected tracks and their assignments')
        self.view_tracks_btn.setMinimumHeight(32)
        self.view_tracks_btn.setStyleSheet('''QPushButton {
            background-color: #3a6ea5;
            color: #e6ecff;
            border-radius: 8px;
            font-size: 12px;
            padding: 8px;
            margin-top: 4px;
        }
        QPushButton:hover {
            background-color: #4e8cff;
            border: 1px solid #6bbcff;
        }
        ''')
        self.view_tracks_btn.clicked.connect(self._open_tracks_viewer)
        scroll_layout.addWidget(self.view_tracks_btn)
        
        # Format selection moved to dialog on Generate button click (not in main UI)
        # This prevents users from accidentally skipping the format choice
        
        # Create patch button FIRST (before restore) so button state can be updated
        btn_row = QHBoxLayout()
        self.patch_btn = QPushButton('Final Step: Generate Mod')
        self.patch_btn.setToolTip('Generate the mod file with all your selected music and settings')
        self.patch_btn.setStyleSheet('''QPushButton {
            background-color: #3a6ea5;
            color: #e6ecff;
            border-radius: 8px;
            font-size: 14px;
            margin: 4px 0 4px 0;
            border: 1px solid #4e8cff;
        }
        QPushButton:hover {
            background-color: #4e8cff;
            border: 1px solid #6bbcff;
        }''')
        self.patch_btn.clicked.connect(lambda: [self.play_click_sound(), self.generate_patch_file()])
        btn_row.addWidget(self.patch_btn)
        main_layout.addLayout(btn_row)
        self.patch_btn.setEnabled(False)
        # Update button state when audio or biome selection changes
        if hasattr(self, 'modname_input'):
            self.modname_input.textChanged.connect(self.update_patch_btn_state)
        
        # NOW auto-restore mod state - patch_btn exists so button state can be updated
        print(f'[DEBUG] About to call _restore_mod_state_on_startup()')
        self._restore_mod_state_on_startup()
        print(f'[DEBUG] Finished _restore_mod_state_on_startup()')


    ffmpeg_log_signal = pyqtSignal(str)
    audio_status_signal = pyqtSignal(str)
    completed_files_signal = pyqtSignal(str)

    def show_output_format_selection(self):
        """Create Output Format Selection (Loose Files vs Pak File)"""
        print(f'[DEBUG] show_output_format_selection() called')
        try:
            self.output_format_widget = QWidget()
            self.output_format_widget.setMinimumHeight(100)
            layout = QVBoxLayout(self.output_format_widget)
            layout.setContentsMargins(0, 8, 0, 8)
            
            format_label = QLabel('Output Format:')
            format_label.setStyleSheet('color: #e6ecff; font-size: 13px; margin-bottom: 6px; font-weight: bold;')
            format_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            layout.addWidget(format_label, alignment=Qt.AlignHCenter)
            
            info_label = QLabel('How would you like your mod packaged?')
            info_label.setStyleSheet('color: #b19cd9; font-size: 11px; margin-bottom: 8px;')
            info_label.setAlignment(Qt.AlignHCenter)
            layout.addWidget(info_label, alignment=Qt.AlignHCenter)
            
            # Radio buttons
            format_layout = QVBoxLayout()
            format_layout.setSpacing(6)
            
            # Loose Files option
            self.loose_radio = QRadioButton('📁 Loose Files (editable folder)')
            self.loose_radio.setStyleSheet('color: #e6ecff; font-size: 12px; padding: 4px;')
            self.loose_radio.setToolTip('Easy to edit mod files after installation')
            format_layout.addWidget(self.loose_radio)
            print(f'  - Created loose_radio')
            
            # Pak File option (default)
            self.pak_radio = QRadioButton('📦 Pak File (single package)')
            self.pak_radio.setStyleSheet('color: #e6ecff; font-size: 12px; padding: 4px;')
            self.pak_radio.setToolTip('Compact file, easy to share with friends')
            format_layout.addWidget(self.pak_radio)
            print(f'  - Created pak_radio')
            
            # Store reference for later access
            self.output_format_group = QButtonGroup()
            self.output_format_group.addButton(self.loose_radio, 0)
            self.output_format_group.addButton(self.pak_radio, 1)
            
            # Restore saved format choice from settings
            try:
                saved_format = self.settings.get('last_output_format', 'pak')
            except:
                saved_format = 'pak'
            
            print(f'  - Saved format: {saved_format}')
            if saved_format == 'loose':
                self.loose_radio.setChecked(True)
                print(f'  - Set loose_radio to checked')
            else:
                self.pak_radio.setChecked(True)  # Default to pak
                print(f'  - Set pak_radio to checked')
            
            print(f'  - pak_radio.isChecked(): {self.pak_radio.isChecked()}')
            print(f'  - loose_radio.isChecked(): {self.loose_radio.isChecked()}')
            
            # Save choice when changed
            self.loose_radio.toggled.connect(lambda: self._on_output_format_changed())
            
            layout.addLayout(format_layout)
            layout.addSpacing(8)
            layout.addStretch()
            
            self.output_format_widget.setLayout(layout)
            print(f'[DEBUG] show_output_format_selection() completed successfully')
        except Exception as e:
            print(f'[ERROR] show_output_format_selection() failed: {e}')
            import traceback
            traceback.print_exc()

    def _on_output_format_changed(self):
        """Save output format choice to settings"""
        format_choice = 'loose' if self.loose_radio.isChecked() else 'pak'
        self.settings.set('last_output_format', format_choice)
        print(f'[PERSIST] Output format changed to: {format_choice}')

    def show_step6_track_choice(self):
        self.step6_widget = QWidget()  # Initialize Step 6 widget
        layout = QVBoxLayout(self.step6_widget)
        step6_label = QLabel('Step 6: Select When Your Tracks Should Play')
        step6_label.setStyleSheet('color: #e6ecff; font-size: 13px; margin-bottom: 6px;')
        step6_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(step6_label, alignment=Qt.AlignHCenter)
        day_btn = QPushButton('Add to Day')
        day_btn.setToolTip('Select music tracks to play during daytime')
        night_btn = QPushButton('Add to Night')
        night_btn.setToolTip('Select music tracks to play during nighttime')
        day_btn.setStyleSheet('''QPushButton {
            background-color: #3a6ea5;
            color: #e6ecff;
            border-radius: 8px;
            font-size: 13px;
            margin: 4px 8px 4px 0;
        }
        QPushButton:hover {
            background-color: #4e8cff;
            border: 1px solid #6bbcff;
        }
        ''')
        night_btn.setStyleSheet('''QPushButton {
            background-color: #3a6ea5;
            color: #e6ecff;
            border-radius: 8px;
            font-size: 13px;
            margin: 4px 0 4px 0;
        }
        QPushButton:hover {
            background-color: #4e8cff;
            border: 1px solid #6bbcff;
        }
        ''')
        btn_row = QHBoxLayout()
        btn_row.addWidget(day_btn)
        btn_row.addWidget(night_btn)
        # Only add btn_row and selected_tracks_label once
        day_btn.clicked.connect(lambda: self.select_music_files('Day'))
        night_btn.clicked.connect(lambda: self.select_music_files('Night'))
        # Only initialize selected_track_type if it hasn't been set yet (preserve restored value)
        if not hasattr(self, 'selected_track_type') or self.selected_track_type is None:
            self.selected_track_type = None
        
        # Create a scrollable widget for tracks display with clear buttons
        self.tracks_display_widget = QWidget()
        self.tracks_display_layout = QVBoxLayout(self.tracks_display_widget)
        self.tracks_display_layout.setContentsMargins(8, 8, 8, 8)
        self.tracks_display_layout.setSpacing(6)
        
        self.tracks_scroll_area = QScrollArea()
        self.tracks_scroll_area.setWidget(self.tracks_display_widget)
        self.tracks_scroll_area.setWidgetResizable(True)
        self.tracks_scroll_area.setStyleSheet('border: 1px solid #3a4a6a; border-radius: 4px; background: transparent;')
        self.tracks_scroll_area.setMaximumHeight(80)  # Much smaller since detailed view is in separate window
        
        layout.addLayout(btn_row)
        
        layout.addWidget(self.tracks_scroll_area)
        
        # Add biome display label
        self.selected_biomes_label = QLabel('No biomes selected yet.')
        self.selected_biomes_label.setStyleSheet('color: #b19cd9; font-size: 11px; margin-top: 4px; background: transparent; border: none;')
        self.selected_biomes_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.addWidget(self.selected_biomes_label, alignment=Qt.AlignHCenter)
        
        # Refresh display
        self.update_selected_tracks_label()
    
    def _set_step6_visible(self, visible: bool):
        """Show or hide Step 6 based on patch mode"""
        # In Both mode, always show Step 6 (for Day/Night Add selections)
        if self.patch_mode == 'both':
            visible = True
        # In other modes, hide Step 6 if Replace was selected
        elif self.replace_was_selected:
            visible = False
        
        if hasattr(self, 'step6_widget') and self.step6_widget:
            if visible:
                self.step6_widget.show()
            else:
                self.step6_widget.hide()

    def update_selected_tracks_label(self):
        """Refresh the tracks display with clear buttons for individual tracks (per-biome) - NOW SHOWS BRIEF SUMMARY"""
        add_selections = getattr(self, 'add_selections', {})
        selected_track_type = getattr(self, 'selected_track_type', None)
        
        # Recreate the display widget entirely to avoid remnants
        if hasattr(self, 'tracks_scroll_area'):
            old_widget = self.tracks_scroll_area.takeWidget()
            if old_widget:
                old_widget.deleteLater()
        
        # Create fresh display widget
        self.tracks_display_widget = QWidget()
        self.tracks_display_layout = QVBoxLayout(self.tracks_display_widget)
        self.tracks_display_layout.setContentsMargins(8, 8, 8, 8)
        self.tracks_display_layout.setSpacing(4)
        self.tracks_scroll_area.setWidget(self.tracks_display_widget)
        
        # Note: Track summary is displayed in audio_status_label and selected_biomes_label
        # This section intentionally kept minimal to avoid redundancy
        if not add_selections:
            empty_label = QLabel('No tracks selected yet')
            empty_label.setStyleSheet('color: #b19cd9; font-size: 10px; font-style: italic;')
            self.tracks_display_layout.addWidget(empty_label)
        
        self.tracks_display_layout.addStretch()
    
    def _open_tracks_viewer(self):
        """Open the separate tracks viewer window"""
        viewer = TracksViewerWindow(self, self)
        viewer.refresh_display()
        viewer.exec_()

    def select_music_files(self, track_type):
        """Select music files with option for blanket or individual biome assignment"""
        # Check biome selection first
        if not self.selected_biomes:
            QMessageBox.warning(self, 'Select Music Files', 'Please select at least one biome first.')
            return
        
        # If only one biome, skip the choice dialog and go straight to file selection
        if len(self.selected_biomes) == 1:
            return self._add_tracks_to_biome(track_type, self.selected_biomes[0])
        
        # Multiple biomes selected: ask blanket or individual
        dlg = QDialog(self)
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dlg.setWindowTitle('How to Add Music')
        dlg.setMinimumSize(400, 200)
        layout = QVBoxLayout(dlg)
        
        label = QLabel(f'You have {len(self.selected_biomes)} biomes selected.\n\nHow would you like to add music?')
        label.setStyleSheet('color: #e6ecff; font-size: 12px;')
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Blanket option
        blanket_btn = QPushButton('🎵 Blanket: Add same tracks to ALL biomes')
        blanket_btn.setToolTip('Use the same music tracks for all selected biomes')
        blanket_btn.setStyleSheet('''QPushButton {
            background-color: #2d5a3d;
            color: #e6ecff;
            padding: 8px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #3a8a55;
        }
        ''')
        blanket_btn.clicked.connect(lambda: self._blanket_add_flow(track_type, dlg))
        layout.addWidget(blanket_btn)
        
        # Individual option
        individual_btn = QPushButton('🎯 Individual: Add different tracks to each biome')
        individual_btn.setToolTip('Assign different music tracks to different biomes')
        individual_btn.setStyleSheet('''QPushButton {
            background-color: #3d5a6a;
            color: #e6ecff;
            padding: 8px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #4e7a9a;
        }
        ''')
        individual_btn.clicked.connect(lambda: self._individual_add_flow(track_type, dlg))
        layout.addWidget(individual_btn)
        
        layout.addStretch()
        dlg.setLayout(layout)
        dlg.exec_()

    def _blanket_add_flow(self, track_type, dialog):
        """Add same tracks to all selected biomes"""
        import shutil
        
        dialog.accept()
        
        mod_name = self.modname_input.text().strip()
        if not mod_name:
            QMessageBox.warning(self, 'Select Music Files', 'Please enter a mod name first.')
            return
        
        starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
        staging_dir = starsound_dir / 'staging'
        safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        music_folder = staging_dir / safe_mod_name / 'music'
        if not music_folder.exists():
            QMessageBox.warning(self, 'Select Music Files', f'Music folder does not exist: {music_folder}')
            return
        
        files, _ = QFileDialog.getOpenFileNames(self, f'Select music files for {track_type} (blanket)', str(music_folder), 'Audio Files (*.ogg *.mp3 *.wav);;All Files (*)')
        if files:
            print(f'[ADD] Blanket adding {len(files)} {track_type} tracks to {len(self.selected_biomes)} biomes')
            
            # Copy files to mod music folder and backup originals (in root backups folder)
            backup_root = self._get_backup_path(safe_mod_name)
            originals_folder = backup_root / 'originals'
            converted_folder = backup_root / 'converted'
            originals_folder.mkdir(parents=True, exist_ok=True)
            converted_folder.mkdir(parents=True, exist_ok=True)
            
            filenames_to_add = []
            for f in files:
                try:
                    src = Path(f)
                    dest = music_folder / src.name
                    if not dest.exists():
                        shutil.copy2(f, dest)
                        self.logger.log(f'Copied {src.name} to {music_folder}')
                    
                    # Backup original file
                    if not src.name.lower().endswith('.ogg'):
                        backup_dest = originals_folder / src.name
                        if not backup_dest.exists():
                            shutil.copy2(f, backup_dest)
                    else:
                        # Converted .ogg goes to converted folder
                        converted_dest = converted_folder / src.name
                        if not converted_dest.exists():
                            shutil.copy2(f, converted_dest)
                    
                    filenames_to_add.append(src.name)
                except Exception as e:
                    self.logger.error(f'Failed to copy file {f}: {e}')
            
            # Now add the filenames to all selected biomes
            for biome in self.selected_biomes:
                if biome not in self.add_selections:
                    self.add_selections[biome] = {'day': [], 'night': []}
                
                key = 'day' if track_type == 'Day' else 'night'
                for filename in filenames_to_add:
                    if filename not in self.add_selections[biome][key]:
                        self.add_selections[biome][key].append(filename)
                        print(f'[ADD] Added {filename} to {biome} {key}')
            
            self.selected_track_type = track_type
            self.update_selected_tracks_label()
            self.update_patch_btn_state()
            msg = f'Added {len(filenames_to_add)} file(s) to {track_type} tracks for all {len(self.selected_biomes)} biome(s).'
            self.audio_status_label.setText(msg)
            self._auto_save_mod_state(action=f'{track_type} tracks added (blanket)')
            QMessageBox.information(self, 'Music Added', msg)

    def _individual_add_flow(self, track_type, dialog):
        """Add tracks to individual biomes"""
        dialog.accept()
        
        # Ask which biome to add to
        biome_names = [f"{cat}: {bio}" for cat, bio in self.selected_biomes]
        biome_choice, ok = QInputDialog.getItem(
            self,
            'Select Biome',
            'Which biome should these tracks be added to?',
            biome_names,
            0,
            False
        )
        
        if not ok or not biome_choice:
            return
        
        # Find the selected biome tuple
        selected_biome = self.selected_biomes[[f"{cat}: {bio}" for cat, bio in self.selected_biomes].index(biome_choice)]
        
        # Now add tracks to this biome
        self._add_tracks_to_biome(track_type, selected_biome)

    def _add_tracks_to_biome(self, track_type, biome):
        """Add tracks to a specific biome"""
        import shutil
        
        mod_name = self.modname_input.text().strip()
        if not mod_name:
            QMessageBox.warning(self, 'Select Music Files', 'Please enter a mod name first.')
            return
        
        starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
        staging_dir = starsound_dir / 'staging'
        safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        music_folder = staging_dir / safe_mod_name / 'music'
        if not music_folder.exists():
            QMessageBox.warning(self, 'Select Music Files', f'Music folder does not exist: {music_folder}')
            return
        
        files, _ = QFileDialog.getOpenFileNames(self, f'Select music files for {track_type}', str(music_folder), 'Audio Files (*.ogg *.mp3 *.wav);;All Files (*)')
        if files:
            category, biome_name = biome
            print(f'[ADD] Adding {len(files)} {track_type} tracks to {category}: {biome_name}')
            
            if biome not in self.add_selections:
                self.add_selections[biome] = {'day': [], 'night': []}
            
            key = 'day' if track_type == 'Day' else 'night'
            
            # Copy files to mod music folder and backup originals (in root backups folder)
            backup_root = self._get_backup_path(safe_mod_name)
            originals_folder = backup_root / 'originals'
            converted_folder = backup_root / 'converted'
            originals_folder.mkdir(parents=True, exist_ok=True)
            converted_folder.mkdir(parents=True, exist_ok=True)
            
            files_added = []
            for f in files:
                try:
                    # Copy file to mod music folder
                    src = Path(f)
                    dest = music_folder / src.name
                    if not dest.exists():
                        shutil.copy2(f, dest)
                        self.logger.log(f'Copied {src.name} to {music_folder}')
                    
                    # Backup original file
                    if not src.name.lower().endswith('.ogg'):
                        backup_dest = originals_folder / src.name
                        if not backup_dest.exists():
                            shutil.copy2(f, backup_dest)
                    else:
                        # Converted .ogg goes to converted folder
                        converted_dest = converted_folder / src.name
                        if not converted_dest.exists():
                            shutil.copy2(f, converted_dest)
                    
                    # Store just the filename, not the full path (compatible with patch_generator)
                    filename = src.name
                    if filename not in self.add_selections[biome][key]:
                        self.add_selections[biome][key].append(filename)
                        files_added.append(filename)
                        print(f'[ADD] Added {filename} to {category}: {biome_name}')
                except Exception as e:
                    self.logger.error(f'Failed to copy file {f}: {e}')
                    QMessageBox.warning(self, 'Copy Failed', f'Failed to copy {Path(f).name}: {str(e)[:100]}')
            
            if files_added:
                self.selected_track_type = track_type
                self.update_selected_tracks_label()
                self.update_patch_btn_state()
                msg = f'Added {len(files_added)} file(s) to {track_type} tracks for {category}: {biome_name}.'
                self.audio_status_label.setText(msg)
                self._auto_save_mod_state(action=f'{track_type} tracks added to {biome_name}')
                QMessageBox.information(self, 'Music Added', msg)
            else:
                QMessageBox.warning(self, 'No Files Added', 'No new files were added (files may have already been in the mod).')
            self.update_selected_tracks_label()
        else:
            QMessageBox.information(self, 'No Selection', 'No files were selected.')
            self.update_selected_tracks_label()

    def remove_biome_track(self, biome, track_type, track_path):
        """Remove a single track from a specific biome"""
        if biome in self.add_selections:
            key = 'day' if track_type == 'day' else 'night'
            if track_path in self.add_selections[biome][key]:
                self.add_selections[biome][key].remove(track_path)
                print(f'[ADD] Removed {track_type} track from {biome}: {Path(track_path).name}')
                
                # If biome now has 0 tracks, remove it from add_selections
                if not self.add_selections[biome]['day'] and not self.add_selections[biome]['night']:
                    del self.add_selections[biome]
                    print(f'[ADD] Removed empty biome entry from add_selections: {biome}')
                    # Also remove from selected_biomes to keep them in sync
                    if biome in self.selected_biomes:
                        self.selected_biomes.remove(biome)
                        print(f'[ADD] Removed {biome} from selected_biomes')
                
                self.update_selected_tracks_label()
                self.update_patch_btn_state()
                self._auto_save_mod_state(action=f'Removed {track_type} track from {biome[1]}')

    def clear_biome_tracks(self, biome, track_type):
        """Clear all tracks of a type from a specific biome"""
        if biome in self.add_selections:
            key = 'day' if track_type == 'day' else 'night'
            count = len(self.add_selections[biome][key])
            self.add_selections[biome][key].clear()
            print(f'[ADD] Cleared all {count} {track_type} tracks from {biome}')
            
            # If biome now has 0 tracks, remove it from add_selections
            if not self.add_selections[biome]['day'] and not self.add_selections[biome]['night']:
                del self.add_selections[biome]
                print(f'[ADD] Removed empty biome entry from add_selections: {biome}')
                # Also remove from selected_biomes to keep them in sync
                if biome in self.selected_biomes:
                    self.selected_biomes.remove(biome)
                    print(f'[ADD] Removed {biome} from selected_biomes')
            
            self.update_selected_tracks_label()
            self.update_patch_btn_state()
            self._auto_save_mod_state(action=f'Cleared all {track_type} tracks from {biome[1]}')

    def remove_track(self, track_type, track_path):
        """Remove a single global track (legacy, kept for compatibility)"""
        if track_type == 'day' and track_path in self.day_tracks:
            self.day_tracks.remove(track_path)
            print(f'[ADD] Removed day track: {Path(track_path).name}')
        elif track_type == 'night' and track_path in self.night_tracks:
            self.night_tracks.remove(track_path)
            print(f'[ADD] Removed night track: {Path(track_path).name}')
        
        self.update_selected_tracks_label()
        self.update_patch_btn_state()
        self._auto_save_mod_state(action=f'Removed {track_type} track')

    def clear_all_day_tracks(self):
        """Clear all day tracks"""
        if self.day_tracks:
            count = len(self.day_tracks)
            self.day_tracks.clear()
            print(f'[ADD] Cleared all {count} day tracks')
            self.update_selected_tracks_label()
            self.update_patch_btn_state()
            self._auto_save_mod_state(action='Cleared all day tracks')

    def clear_all_night_tracks(self):
        """Clear all night tracks"""
        if self.night_tracks:
            count = len(self.night_tracks)
            self.night_tracks.clear()
            print(f'[ADD] Cleared all {count} night tracks')
            self.update_selected_tracks_label()
            self.update_patch_btn_state()
            self._auto_save_mod_state(action='Cleared all night tracks')

    def update_patch_btn_state(self):
        print(f'[DEBUG] update_patch_btn_state() called')
        # Defensive: patch_btn might not exist yet during initialization
        if not hasattr(self, 'patch_btn') or self.patch_btn is None:
            print(f'[DEBUG] patch_btn not ready yet, skipping update')
            return
        
        # Enable if:
        # 1. Replace path: replace_selections has entries AND at least one biome is selected
        # 2. Add path (new): add_selections has entries AND at least one biome is selected
        # 3. Add path (legacy): day_tracks OR night_tracks exists AND at least one biome is selected
        
        day_tracks_selected = (hasattr(self, 'day_tracks') and len(self.day_tracks) > 0)
        night_tracks_selected = (hasattr(self, 'night_tracks') and len(self.night_tracks) > 0)
        biome_selected = (hasattr(self, 'selected_biomes') and len(self.selected_biomes) > 0)
        
        # Check for Replace feature selections
        replace_selections = getattr(self, 'replace_selections', {})
        has_replace_selections = bool(replace_selections)
        
        # Check for new per-biome Add feature selections
        add_selections = getattr(self, 'add_selections', {})
        has_add_selections = False
        if add_selections:
            # Count total tracks across all biomes
            total_add_tracks = sum(
                len(tracks_dict.get('day', [])) + len(tracks_dict.get('night', []))
                for tracks_dict in add_selections.values()
            )
            has_add_selections = total_add_tracks > 0
        
        # DEBUG output
        print(f'  - day_tracks_selected: {day_tracks_selected} ({len(getattr(self, "day_tracks", []))} tracks)')
        print(f'  - night_tracks_selected: {night_tracks_selected} ({len(getattr(self, "night_tracks", []))} tracks)')
        print(f'  - has_add_selections: {has_add_selections}')
        print(f'  - biome_selected: {biome_selected} ({len(getattr(self, "selected_biomes", []))} biomes)')
        print(f'  - has_replace_selections: {has_replace_selections} ({len(replace_selections)} entries)')
        
        # Enable button if:
        # (Legacy Add: tracks + biome) OR (Replace: replace_selections + biome) OR (New Add: add_selections + biome)
        can_generate = (
            ((day_tracks_selected or night_tracks_selected) and biome_selected) or
            (has_replace_selections and biome_selected) or
            (has_add_selections and biome_selected)
        )
        
        print(f'  - can_generate: {can_generate}')
        
        self.patch_btn.setEnabled(bool(can_generate))
        if not can_generate:
            self.patch_btn.setToolTip('Select tracks, a biome, and track type to enable mod generation.')
        else:
            self.patch_btn.setToolTip('Ready to generate your StarSound mod!')
        # Force update of selected_tracks_label if it exists
        if hasattr(self, 'update_selected_tracks_label'):
            try:
                self.update_selected_tracks_label()
            except Exception:
                pass


    def append_completed_file(self, text):
        self.completed_files_box.append(text)

    def show_config_health_checker(self):
        from utils import config_health_detailed
        dlg = QDialog(self)
        # Explicitly disable Windows help button on this dialog
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dlg.setWindowTitle('Config Health Checker')
        dlg.setMinimumSize(1100, 900)
        from utils.starbound_locator import get_storage_folder
        detected = get_storage_folder() or ''
        dlg.setStyleSheet(f'''
                QDialog {{
                    background-color: #23283b;
                    font-family: "Hobo";
                }}
                QLabel {{
                    color: #e6ecff;
                    font-size: 16px;
                    background: #181c2a;
                    border-radius: 12px;
                    padding: 18px;
                    margin-top: 12px;
                }}
                QPushButton {{
                    background-color: #3a6ea5;
                    color: #e6ecff;
                    border-radius: 10px;
                    border: 1px solid #4e8cff;
                    padding: 6px 18px;
                    font-size: 15px;
                    font-family: "Hobo";
                }}
                QPushButton:hover {{
                    background-color: #4e8cff;
                    border: 1px solid #6bbcff;
                }}
            ''')
        layout = QVBoxLayout(dlg)
        # Add folder selection and re-scan buttons
        button_row = QHBoxLayout()
        folder_btn = QPushButton('Choose Folder...')
        folder_btn.setToolTip('Select a different Starbound storage folder')
        button_row.addWidget(folder_btn)
        rescan_btn = QPushButton('Re-Scan')
        rescan_btn.setToolTip('Re-run config health check')
        button_row.addWidget(rescan_btn)
        layout.addLayout(button_row)
        # Add results display
        from PyQt5.QtWidgets import QTextEdit
        results_box = QTextEdit()
        results_box.setReadOnly(True)
        results_box.setStyleSheet('background: #181c2a; color: #e6ecff; font-size: 15px; border-radius: 8px;')
        layout.addWidget(results_box, 1)
        # Health check logic
        def run_health_check(folder):
            report = config_health_detailed.check_starbound_config(folder)
            results_box.setText(report['summary'])
        # Button actions
        def choose_folder():
            folder = QFileDialog.getExistingDirectory(dlg, 'Select Starbound Storage Folder', detected)
            if folder:
                run_health_check(folder)
        folder_btn.clicked.connect(choose_folder)
        rescan_btn.clicked.connect(lambda: run_health_check(detected))
        # Run on open
        run_health_check(detected)
        dlg.exec_()

    def set_audio_status_label(self, text):
        self.audio_status_label.setText(text)

    def ffmpeg_log_box_append(self, text):
        self.ffmpeg_log_box.append(text)

    class ScanlineOverlay(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.setAttribute(Qt.WA_NoSystemBackground)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
            from PyQt5.QtCore import QTimer
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._on_timer)
            self._timer.start(16)  # ~60 FPS

            # Animation state
            self._jitter_phase = 0
            self._offset = 0
            self._frame = 0

        def _on_timer(self):
            # Animate scanline offset and jitter phase
            self._frame += 1
            self._jitter_phase += 1
            self._offset = (self._offset + 1) % 6  # Move scanlines
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, False)
            h = self.height()
            w = self.width()
            spacing = 6
            thickness = 3
            offset = self._offset
            barrel_strength = 0.08
            cx = w / 2
            cy = h / 2
            maxr = math.sqrt(cx*cx + cy*cy)
            flicker = random.randint(-8, 8)
            jitter = 0
            if hasattr(self, '_jitter_phase'):
                jitter = int(math.sin(self._jitter_phase / 19.0) * 2)
            sync_phase = getattr(self, '_jitter_phase', 0)
            sync_bar_y = int((sync_phase * 2) % h)
            sync_bar_height = 10
            if not hasattr(self, '_crt_glitch_state'):
                self._crt_glitch_state = {'freeze': False, 'freeze_count': 0, 'offset': 0}
            if not self._crt_glitch_state['freeze'] and random.random() < 0.02:
                self._crt_glitch_state['freeze'] = True
                self._crt_glitch_state['freeze_count'] = random.randint(2, 5)
                self._crt_glitch_state['offset'] = random.choice([-8, -4, 0, 4, 8])
            if self._crt_glitch_state['freeze']:
                self._crt_glitch_state['freeze_count'] -= 1
                if self._crt_glitch_state['freeze_count'] <= 0:
                    self._crt_glitch_state['freeze'] = False
                    self._crt_glitch_state['offset'] = 0
                painter.translate(self._crt_glitch_state['offset'], 0)
            if hasattr(self, '_crt_afterimage') and self._crt_afterimage is not None:
                painter.setOpacity(0.18)
                painter.drawPixmap(0, 0, self._crt_afterimage)
                painter.setOpacity(1.0)
            jitter_band_height = 18
            for y in range(0, h, spacing):
                ymid = y + offset + thickness // 2
                norm_y = (ymid - cy) / cy
                curve = int(barrel_strength * (norm_y ** 2) * cy)
                y_curve = y + offset + curve + jitter
                band = (y // jitter_band_height)
                jitter_offset = 0
                if band % 4 == 2:
                    jitter_offset = random.choice([-2, 0, 2])
                edge_strength = int(10 + 30 * abs((y_curve-cy)/cy))
                bleed_alpha = 14
                painter.setBrush(QColor(180, 160, 230, bleed_alpha))
                painter.setPen(Qt.NoPen)
                painter.drawRect(-8 + jitter_offset, y_curve-1, w+16, thickness+2)
                for rgb, dx, alpha in [((255,0,0),-1,edge_strength), ((180,160,230),0,8), ((0,0,255),1,edge_strength)]:
                    painter.setBrush(QColor(*rgb, alpha))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(dx + jitter_offset, y_curve, w, 1)
                glow_alpha = 10
                painter.setBrush(QColor(220, 220, 220, glow_alpha))
                painter.setPen(Qt.NoPen)
                painter.drawRect(-2 + jitter_offset, y_curve-2, w+4, thickness+4)
                grad = QLinearGradient(0, y_curve, 0, y_curve + thickness)
                grad.setColorAt(0.0, QColor(0, 0, 0, 32))
                grad.setColorAt(0.4, QColor(0, 0, 0, 12))
                grad.setColorAt(0.5, QColor(0, 0, 0, 6))
                grad.setColorAt(0.6, QColor(0, 0, 0, 12))
                grad.setColorAt(1.0, QColor(0, 0, 0, 36))
                painter.setBrush(QBrush(grad))
                painter.drawRect(jitter_offset, y_curve, w, thickness)
            sync_grad = QLinearGradient(0, sync_bar_y, 0, sync_bar_y + sync_bar_height)
            sync_grad.setColorAt(0.0, QColor(255,255,255,0))
            sync_grad.setColorAt(0.5, QColor(255,255,255,32))
            sync_grad.setColorAt(1.0, QColor(255,255,255,0))
            painter.setBrush(QBrush(sync_grad))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, sync_bar_y, w, sync_bar_height)
            if random.random() < 0.12:
                for _ in range(random.randint(1, 2)):
                    ty = random.randint(0, h-2)
                    t_height = random.randint(1, 3)
                    t_alpha = random.randint(60, 120)
                    painter.setBrush(QColor(255,255,255,t_alpha))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(0, ty, w, t_height)
            # --- Speaker Grille Lines: vertical lines at far left/right edges ---
            grille_alpha = 38
            for gx in range(0, 12, 3):
                painter.setPen(QColor(80,80,80,grille_alpha))
                painter.drawLine(gx, 0, gx, h)
                painter.drawLine(w-1-gx, 0, w-1-gx, h)
            # --- Vignette: darken corners/edges ---
            vignette_alpha = 160  # much darker
            vignette = QLinearGradient(0, 0, w, h)
            vignette.setColorAt(0.0, QColor(0,0,0,vignette_alpha))
            vignette.setColorAt(0.15, QColor(0,0,0,0))
            vignette.setColorAt(0.85, QColor(0,0,0,0))
            vignette.setColorAt(1.0, QColor(0,0,0,vignette_alpha))
            painter.setBrush(QBrush(vignette))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, w, h)
            painter.end()
    def _init_scanline_overlay(self):
        # Always attach overlay to the main window, not central widget
        self._scanline_overlay = self.ScanlineOverlay(self)
        self._scanline_overlay.setGeometry(0, 0, self.width(), self.height())
        self._scanline_overlay.setVisible(getattr(self, 'crt_effects_enabled', False))
        if self.crt_effects_enabled:
            print(f'[CRT DEBUG] Scanline overlay initialized and made visible')
            self._scanline_overlay.show()
            self._scanline_overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_scanline_overlay'):
            self._scanline_overlay.setGeometry(0, 0, self.width(), self.height())
            self._scanline_overlay.raise_()


    def play_click_sound(self):
        try:
            from PyQt5.QtMultimedia import QSoundEffect
            from PyQt5.QtCore import QUrl
            import pathlib
            sound_path = pathlib.Path(os.path.dirname(__file__)) / 'assets' / 'sfx' / 'ship_confirm.wav'
            if not hasattr(self, 'click_sound'):
                self.click_sound = QSoundEffect()
                self.click_sound.setSource(QUrl.fromLocalFile(str(sound_path)))
                self.click_sound.setVolume(0.3)
            self.click_sound.play()
        except Exception as e:
            print(f'Click sound error: {e}')

    def _get_backup_path(self, mod_name):
        """Get the backup folder path for a mod (root-level backups)"""
        starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
        safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        backup_dir = starsound_dir / 'backups' / safe_mod_name
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def _setup_ui_legacy(self):
        # Load custom font from assets/font/hobo.ttf
        from PyQt5.QtGui import QFontDatabase, QFont
        font_path = os.path.join(os.path.dirname(__file__), 'assets', 'font', 'hobo.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app_font = QFont(family, 15)
            self.setFont(app_font)
        else:
            print('Warning: Failed to load custom font hobo.ttf')
        self.logger = get_logger()

        # Connect completed files signal
        self.completed_files_signal.connect(self.append_completed_file)
        self.setWindowTitle('StarSound')
        # Make the app larger by default (e.g., 1100x900)
        self.setGeometry(100, 100, 1100, 900)
        self.setMinimumSize(1100, 900)
        self.setMaximumSize(1600, 1200)
        self.resize(1100, 900)

        # Connect signals for thread-safe GUI updates
        self.ffmpeg_log_signal.connect(self.ffmpeg_log_box_append)
        self.audio_status_signal.connect(self.set_audio_status_label)

        # Modern dark mode stylesheet with rounded buttons and improved scaling
        # Set starfield background image for main window (using assets/photos/starfield1.png)
        from pathlib import Path
        self.setStyleSheet(f'''
QMainWindow, QWidget {{
    background-color: #23283b;
    font-family: "Hobo";
}}
QLabel, QMenuBar, QToolBar {{
    color: #e6ecff;
    font-family: "Hobo";
    font-size: 15px;
}}
QLineEdit, QTextEdit {{
    background: #283046;
    color: #e6ecff;
    border-radius: 8px;
    border: 1px solid #3a4a6a;
    font-size: 15px;
    font-family: "Hobo";
}}
QPushButton {{
    background-color: #3a6ea5;
    color: #e6ecff;
    border-radius: 10px;
    border: 1px solid #4e8cff;
    padding: 6px 18px;
    font-size: 15px;
    font-family: "Hobo";
}}
QPushButton:hover {{
    background-color: #4e8cff;
    border: 1px solid #6bbcff;
}}
QScrollArea {{
    background: #23283b;
    border-radius: 8px;
    font-family: "Hobo";
}}
QMessageBox {{
    background: #23283b;
    color: #e6ecff;
    font-family: "Hobo";
}}
QGroupBox {{
    background-color: #283046;
    border: 1px solid #3a4a6a;
    border-radius: 8px;
    margin-top: 10px;
    font-family: "Hobo";
}}
        ''')

        # High-DPI attributes are set at the top of the script before QApplication is created

        # Add a QMenuBar for diagnostic visibility
        # Removed local import of QLabel as QtLabel
        menubar = QMenuBar(self)
        menubar.addMenu('File')
        help_menu = menubar.addMenu('Help')
        shortcuts_action = QAction('Shortcuts', self)
        def show_shortcuts():
            dlg = QDialog(self)
            dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            dlg.setWindowTitle('Keyboard Shortcuts')
            dlg.setMinimumSize(400, 260)
            layout = QVBoxLayout(dlg)
            label = QLabel('''<b>Keyboard Shortcuts</b><br><br>
            <span style="color:#4e8cff;">Ctrl+S</span>: Take screenshot<br>
            <span style="color:#4e8cff;">Ctrl+R</span>: Random Mod Name<br>
            <span style="color:#4e8cff;">Ctrl+F</span>: Browse Mod Folder<br>
            <span style="color:#6bffb0;">Ctrl+O</span>: Browse Audio File<br>
            <span style="color:#ff6b6b;">Esc</span>: Close popups<br>
            ''')
            label.setStyleSheet('''
                color: #e6ecff;
                font-family: "Hobo";
                font-size: 16px;
                background: #181c2a;
                border-radius: 12px;
                padding: 18px;
                margin-top: 12px;
            ''')
            layout.addWidget(label)
            close_btn = QPushButton('Close')
            close_btn.setToolTip('Close this shortcuts guide')
            close_btn.clicked.connect(dlg.accept)
            layout.addWidget(close_btn)
            dlg.exec_()
        shortcuts_action.triggered.connect(show_shortcuts)
        help_menu.addAction(shortcuts_action)
        # Add a 'CRT Effects' menu with a toggle action for accessibility
        self.crt_effects_enabled = False
        crt_menu = menubar.addMenu('CRT Effects')
        self.toggle_crt_action = QAction('Disable CRT Effects', self)
        self.toggle_crt_action.setCheckable(True)
        self.toggle_crt_action.setChecked(False)
        def toggle_crt_effects():
            self.crt_effects_enabled = not self.crt_effects_enabled
            if hasattr(self, '_scanline_overlay') and self._scanline_overlay:
                self._scanline_overlay.setVisible(self.crt_effects_enabled)
            self.toggle_crt_action.setText('Enable CRT Effects' if not self.crt_effects_enabled else 'Disable CRT Effects')
            self.toggle_crt_action.setChecked(self.crt_effects_enabled)
        self.toggle_crt_action.triggered.connect(toggle_crt_effects)
        crt_menu.addAction(self.toggle_crt_action)
        self.setMenuBar(menubar)

        # --- QToolBar with Screenshot Button ---
        toolbar = QToolBar('Main Toolbar')
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        # Add Starbound logo/icon placeholder (replace with actual logo if available)
        logo_label = QLabel('★')
        logo_label.setStyleSheet('font-size: 22px; color: #4e8cff; padding-right: 8px;')
        toolbar.addWidget(logo_label)
        toolbar.addWidget(QLabel('StarSound Toolbar:'))
        screenshot_action = QAction('📸 Screenshot', self)
        screenshot_action.setToolTip('Take a screenshot of the app window')
        screenshot_action.triggered.connect(lambda: [self.play_click_sound(), self.take_screenshot_action()])
        toolbar.addAction(screenshot_action)

        # Add Config Health and Emergency Beacon buttons to toolbar
        config_health_action = QAction('🩺 Config Health', self)
        config_health_action.setToolTip('Check Starbound config health')
        config_health_action.triggered.connect(lambda: [self.play_click_sound(), self.show_config_health_checker()])
        toolbar.addAction(config_health_action)
        # QToolBar styling is handled by global stylesheet (stylesheet_manager.py)

        emergency_beacon_action = QAction('🚨 Emergency Beacon', self)
        emergency_beacon_action.setToolTip('Scan Starbound logs for errors and explanations')
        emergency_beacon_action.triggered.connect(lambda: [self.play_click_sound(), self.show_emergency_beacon()])
        toolbar.addAction(emergency_beacon_action)
        
        # Apply toolbar stylesheet for proper button styling and hover/pressed states
        toolbar.setStyleSheet(get_toolbar_style())
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        # RE-APPLY font after all UI widgets are created
        # This ensures all widgets created during init receive the correct font from settings
        saved_font = self.settings.get('current_font', 'Hobo')
        self._apply_font_to_app(saved_font)

    def on_add_to_game(self):
        print(f'[ADD_MODE] on_add_to_game() called')
        print(f'[ADD_MODE] Current state: patch_mode={getattr(self, "patch_mode", None)}, _mode_confirmed_this_session={getattr(self, "_mode_confirmed_this_session", False)}')
        
        # Skip confirmation if already in Add mode AND confirmed in this session, but still allow biome selection
        if self.patch_mode == 'add' and self._mode_confirmed_this_session:
            print(f'[ADD_MODE] Already in Add mode and confirmed - skipping confirmation dialog')
            self._show_biome_dialog()
            return
        
        # Store original patch_mode in case user cancels
        original_patch_mode = self.patch_mode
        
        # Confirm before committing to Add mode (first time)
        print(f'[ADD_MODE] Showing first-time Add mode confirmation dialog')
        reply = QMessageBox.question(
            self,
            'Confirm: Add to Game',
            'Add your music to the game alongside vanilla tracks.\n\n'
            'This mode will:\n'
            '  • Keep all original Starbound music\n'
            '  • Add your music to the music pool\n\n'
            'You will need to create a new mod to use a different mode.\n\n'
            'Proceed with Add mode?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            print(f'[ADD_MODE] User declined Add mode confirmation')
            # Restore original mode and return
            self.patch_mode = original_patch_mode
            return
        
        # Save current mod name before changing mode
        current_name = self.modname_input.text().strip()
        if current_name:
            self.settings.set('last_mod_name', current_name)
        
        self.patch_mode = 'add'
        self._mode_confirmed_this_session = True  # Mark that user confirmed mode in THIS session
        self.settings.set('last_patch_mode', 'add')  # Save patch mode to persistent settings
        self._auto_save_mod_state('patch mode: add')
        self.audio_status_label.setText('✅ Mode: Add to Game (⭐ Check "Remove vanilla" for safest option, or add alongside vanilla)')
        print(f'[ADD_MODE] Set patch_mode to add and _mode_confirmed_this_session to True')
        
        # Hide the Replace buttons to prevent mode mixing, but keep Add button visible to show current mode
        self.replace_btn.hide()
        self.replace_and_add_btn.hide()
        print(f'[ADD_MODE] Hid Replace buttons - Add mode is now locked in')
        
        # Only show Step 6 if Replace hasn't been selected yet
        if not self.replace_was_selected:
            self._set_step6_visible(True)
        
        # Show biome selection dialog
        print(f'[ADD_MODE] Showing biome selection dialog')
        self._show_biome_dialog()

    def on_replace(self):
        # Skip confirmation if already in Replace mode AND confirmed in this session (e.g., restoring saved mod)
        if self.patch_mode == 'replace' and self._mode_confirmed_this_session:
            print(f'[REPLACE] Already in Replace mode, skipping confirmation dialog')
            self._show_replace_dialog_directly()
            return
        
        # Store original patch_mode in case user cancels
        original_patch_mode = self.patch_mode
        
        # Confirm before committing to Replace mode (first time only)
        reply = QMessageBox.question(
            self,
            'Confirm: Replace Base Game Music',
            'Replace original Starbound music with your own (one track at a time).\n\n'
            'This mode will:\n'
            '  • Let you select individual vanilla tracks to replace\n'
            '  • Remove those vanilla tracks and add your own\n'
            '  • Hide the "Add to Game" option for this session\n\n'
            'You will need to create a new mod to use a different mode.\n\n'
            'Proceed with Replace mode?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            # Restore original mode and return
            self.patch_mode = original_patch_mode
            return
        
        # Mark that Replace was selected - this permanently hides Step 6 for this session
        self.replace_was_selected = True
        self._set_step6_visible(False)  # Hide Step 6 permanently
        
        # Hide Add buttons to prevent mode switching
        if hasattr(self, 'add_to_game_btn'):
            self.add_to_game_btn.hide()
        if hasattr(self, 'replace_and_add_btn'):
            self.replace_and_add_btn.hide()
        
        # Save current mod name before changing mode
        current_name = self.modname_input.text().strip()
        if current_name:
            self.settings.set('last_mod_name', current_name)
        
        self.patch_mode = 'replace'
        self._mode_confirmed_this_session = True  # Mark that user confirmed mode in THIS session
        self.settings.set('last_patch_mode', 'replace')  # Save patch mode to persistent settings
        self._auto_save_mod_state('patch mode: replace')
        self.audio_status_label.setText('✅ Mode: Replace Base Game Music (one track at a time)')
        self._show_replace_dialog_directly()
    
    def _show_replace_dialog_directly(self):
        """Show Replace tracks dialog (used by on_replace and when restoring)"""
        # Show Replace tracks dialog - pass existing selections so user can modify them
    def _show_replace_dialog_directly(self):
        """Show Replace tracks dialog (used by on_replace and when restoring)"""
        # Show Replace tracks dialog - pass existing selections so user can modify them
        mod_name = self.modname_input.text().strip() if hasattr(self, 'modname_input') else ''
        replace_dlg = ReplaceTracksDialog(self, self.logger, 'replace', mod_name=mod_name, existing_selections=self.replace_selections)
        if replace_dlg.exec_() == QDialog.Accepted:
            # Store selections for use in generate_patch_file()
            self.replace_selections = replace_dlg.replace_selections
            
            # Check if ANY tracks actually have files assigned (not just if biomes are in dict)
            has_actual_selections = False
            for biome_data in self.replace_selections.values():
                if biome_data.get('day') or biome_data.get('night'):
                    has_actual_selections = True
                    break
            
            if has_actual_selections:
                # Automatically set selected_biomes from replace_selections
                self.selected_biomes = list(self.replace_selections.keys())
                self.logger.log(f'Replace selections saved for generate_patch_file()', context='Replace')
                # Save after selections are made
                self._auto_save_mod_state('replace track selections')
                
                # Show Replace selections in main UI (no dialog)
                if hasattr(self, 'view_tracks_btn'):
                    self.view_tracks_btn.show()
                
                # Update status label with confirmation
                biome_count = len(self.replace_selections)
                total_replacements = sum(
                    len(d.get('day', {})) + len(d.get('night', {}))
                    for d in self.replace_selections.values()
                )
                status_text = f'✅ {biome_count} biome(s), {total_replacements} replacement(s) ready'
                self.audio_status_label.setText(status_text)
                
                # Save again after selections confirmed
                self._auto_save_mod_state('replace summary confirmed')
                # Enable the Generate Mod button since we now have replace_selections and selected_biomes
                self.update_patch_btn_state()
            else:
                self.audio_status_label.setText('❌ No tracks selected for replacement')
                self.logger.warn('Replace dialog accepted but no selections made')

    def _generate_replace_summary_text(self):
        """Generate the summary text for replacement selections (used in both dialog and status label)"""
        summary_lines = ['🎵 REPLACEMENT SUMMARY']
        summary_lines.append('=' * 60)
        
        # Sort biomes for consistent display
        for (category, biome_name) in sorted(self.replace_selections.keys()):
            biome_data = self.replace_selections[(category, biome_name)]
            summary_lines.append(f'\n📍 {category.title()} → {biome_name}')
            summary_lines.append('-' * 50)
            
            # Show day replacements
            day_tracks = biome_data.get('day', {})
            if day_tracks:
                summary_lines.append('  🌅 DAY TRACKS:')
                for track_idx, file_path in sorted(day_tracks.items()):
                    file_name = Path(file_path).name
                    summary_lines.append(f'     Track #{track_idx} → {file_name}')
            
            # Show night replacements
            night_tracks = biome_data.get('night', {})
            if night_tracks:
                summary_lines.append('  🌙 NIGHT TRACKS:')
                for track_idx, file_path in sorted(night_tracks.items()):
                    file_name = Path(file_path).name
                    summary_lines.append(f'     Track #{track_idx} → {file_name}')
            
            if not day_tracks and not night_tracks:
                summary_lines.append('  (No replacements selected)')
        
        summary_lines.append('\n' + '=' * 60)
        return '\n'.join(summary_lines)

    def _show_replace_selections_summary(self):
        """Display a summary of which tracks are being replaced and in which biomes"""
        try:
            summary_text = self._generate_replace_summary_text()
            
            # Create a large, scalable dialog
            dlg = QDialog(self)
            dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            dlg.setWindowTitle('Replace Selections Confirmed')
            dlg.setMinimumSize(1000, 700)  # Large minimum size
            dlg.resize(1000, 700)  # Default size
            
            layout = QVBoxLayout(dlg)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)
            
            # Title
            title = QLabel('Your Replacement Selections Have Been Saved!')
            title_font = QFont('Hobo', 16)
            title_font.setBold(True)
            title.setFont(title_font)
            title.setStyleSheet('color: #00d4ff;')
            layout.addWidget(title)
            
            # Scrollable text area with details
            text_display = QTextEdit()
            text_display.setReadOnly(True)
            text_display.setText(summary_text)
            text_display.setStyleSheet(
                'QTextEdit { '
                '  background-color: #0f3460; '
                '  color: #00d4ff; '
                '  font-family: "Courier New"; '
                '  font-size: 12px; '
                '  border: 1px solid #3a6ea5; '
                '  border-radius: 6px; '
                '  padding: 8px; '
                '} '
                'QTextEdit:scrollarea { '
                '  background-color: #0f3460; '
                '} '
                'QScrollBar:vertical { '
                '  width: 16px; '
                '  background: #1a2a4e; '
                '  border-radius: 8px; '
                '} '
                'QScrollBar::handle:vertical { '
                '  background: #3a6ea5; '
                '  border-radius: 8px; '
                '  min-height: 20px; '
                '} '
                'QScrollBar::handle:vertical:hover { '
                '  background: #5a8ed5; '
                '}'
            )
            text_display.setFont(QFont('Courier New', 11))
            text_display.verticalScrollBar().setContextMenuPolicy(Qt.NoContextMenu)
            layout.addWidget(text_display)
            
            # OK button
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            
            view_btn = QPushButton('📋 View All Tracks')
            view_btn.setToolTip('Open a detailed view of all replacement selections')
            view_btn.setMinimumWidth(150)
            view_btn.setMinimumHeight(40)
            view_btn.setFont(QFont('Hobo', 12))
            view_btn.setStyleSheet(
                'QPushButton { '
                '  background-color: #3a6ea5; '
                '  color: #e6ecff; '
                '  border-radius: 8px; '
                '  font-weight: bold; '
                '} '
                'QPushButton:hover { '
                '  background-color: #5a8ed5; '
                '}'
            )
            view_btn.clicked.connect(self._open_tracks_viewer)
            btn_layout.addWidget(view_btn)
            
            ok_btn = QPushButton('OK')
            ok_btn.setToolTip('Confirm and close this dialog')
            ok_btn.setMinimumWidth(120)
            ok_btn.setMinimumHeight(40)
            ok_btn.setFont(QFont('Hobo', 13))
            ok_btn.setStyleSheet(
                'QPushButton { '
                '  background-color: #3a6ea5; '
                '  color: #e6ecff; '
                '  border-radius: 8px; '
                '  font-weight: bold; '
                '} '
                'QPushButton:hover { '
                '  background-color: #5a8ed5; '
                '}'
            )
            ok_btn.clicked.connect(dlg.accept)
            btn_layout.addWidget(ok_btn)
            layout.addLayout(btn_layout)
            
            # Dark background
            dlg.setStyleSheet('QDialog { background-color: #1a1a2e; }')
            
            dlg.exec_()
            
            # Create a SHORT summary for the status label (one line, counts only)
            biome_count = len(self.replace_selections)
            total_replacements = 0
            for biome_data in self.replace_selections.values():
                total_replacements += len(biome_data.get('day', {})) + len(biome_data.get('night', {}))
            
            short_summary = f'✅ {biome_count} biome(s), {total_replacements} track replacement(s) ready'
            self.audio_status_label.setText(short_summary)
            print(f'[REPLACE] Set status label: {short_summary}')
            
        except Exception as e:
            self.logger.error(f'Error showing replace summary: {str(e)}')
            print(f'[REPLACE] Error: {e}')




    def on_replace_and_add(self):
        # Skip confirmation if already confirmed in this session (even if mode was temporarily switched)
        if self._mode_confirmed_this_session:
            print(f'[BOTH] Both mode already confirmed this session, restarting chained dialog flow')
            self._on_both_mode_chain_step1_replace()
            return
        
        # Store original patch_mode in case user cancels
        original_patch_mode = self.patch_mode
        
        # Confirm before committing to Replace + Add mode (first time)
        reply = QMessageBox.question(
            self,
            'Confirm: Replace and Add Mode',
            'Replace vanilla music and add your own tracks to the pool.\n\n'
            'This mode will:\n'
            '  • Let you REPLACE specific vanilla tracks\n'
            '  • Let you ADD new tracks to the music pool\n'
            '  • Both features will apply to the same biome(s)\n'
            '  • Hide the "Add to Game" and "Replace Only" options for this session\n\n'
            'You will need to create a new mod to use a different mode.\n\n'
            'Proceed with Replace + Add mode?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            # User clicked No - restore original mode and return
            self.patch_mode = original_patch_mode
            return
        
        # Hide Add button and Replace button to lock in this mode
        if hasattr(self, 'add_to_game_btn'):
            self.add_to_game_btn.hide()
        # Hide the replace button so user can't switch to pure Replace mode
        if hasattr(self, 'replace_btn'):
            self.replace_btn.hide()
        
        # Save current mod name before changing mode
        current_name = self.modname_input.text().strip()
        if current_name:
            self.settings.set('last_mod_name', current_name)
        
        self.patch_mode = 'both'
        self._mode_confirmed_this_session = True  # Mark that user confirmed mode in THIS session
        self._original_patch_mode_before_both = original_patch_mode  # Store for potential restore
        self.settings.set('last_patch_mode', 'both')  # Save patch mode to persistent settings
        self._auto_save_mod_state('patch mode: replace+add')
        self.audio_status_label.setText('✅ Mode: Replace and Add (step 1/3: select tracks to replace)')
        # Show Step 6 for both Add selections
        self._set_step6_visible(True)
        
        # Start the chained dialog flow: Replace → Biomes → Step 6
        self._on_both_mode_chain_step1_replace()
    
    def _on_both_mode_chain_step1_replace(self):
        """BOTH MODE - Step 1: Show Replace dialog to select replacement tracks"""
        print(f'[BOTH_CHAIN] Step 1: Showing Replace dialog')
        mod_name = self.modname_input.text().strip() if hasattr(self, 'modname_input') else ''
        replace_dlg = ReplaceTracksDialog(self, self.logger, 'both', mod_name=mod_name, existing_selections=self.replace_selections)
        
        if replace_dlg.exec_() == QDialog.Accepted:
            # Store Replace selections
            self.replace_selections = replace_dlg.replace_selections
            has_actual_selections = False
            for biome_data in self.replace_selections.values():
                if biome_data.get('day') or biome_data.get('night'):
                    has_actual_selections = True
                    break
            
            if has_actual_selections:
                self.logger.log('Both mode: Replace selections saved', context='BothMode')
                self._auto_save_mod_state('both mode: replace selections')
                # Move to Step 2: Biome selection for ADD
                self._on_both_mode_chain_step2_biome()
            else:
                self.audio_status_label.setText('❌ No tracks selected for replacement. Cancelling Both mode.')
                self.logger.warn('Both mode: Replace dialog accepted but no selections')
                # Restore original patch_mode instead of forcing 'add'
                if hasattr(self, '_original_patch_mode_before_both'):
                    self.patch_mode = self._original_patch_mode_before_both
                # Re-enable and re-show Step 5 buttons since Both mode is being cancelled
                if hasattr(self, 'add_to_game_btn'):
                    self.add_to_game_btn.show()
                    self.add_to_game_btn.setEnabled(True)
                    self.add_to_game_btn.setToolTip('Add your music to the game alongside the original tracks.')
                if hasattr(self, 'replace_btn'):
                    self.replace_btn.show()
                    self.replace_btn.setEnabled(True)
                    self.replace_btn.setToolTip('Replace all original music with your selected tracks.')
                if hasattr(self, 'replace_and_add_btn'):
                    self.replace_and_add_btn.show()
                    self.replace_and_add_btn.setEnabled(True)
                    self.replace_and_add_btn.setToolTip('Replace specific tracks AND add new tracks to the music pool.')
                # Keep _mode_confirmed_this_session=True so confirmation doesn't appear again this session
        else:
            # User cancelled Replace dialog - abort Both mode flow
            print(f'[BOTH_CHAIN] User cancelled Replace dialog, aborting Both mode')
            self.audio_status_label.setText('❌ Both mode cancelled (Replace step)')
            # Restore original patch_mode instead of forcing 'add'
            if hasattr(self, '_original_patch_mode_before_both'):
                self.patch_mode = self._original_patch_mode_before_both
            # Hide Step 6 since Both mode is being cancelled
            self._set_step6_visible(False)
            # Re-enable and re-show Step 5 buttons since Both mode is being cancelled
            if hasattr(self, 'add_to_game_btn'):
                self.add_to_game_btn.show()
                self.add_to_game_btn.setEnabled(True)
                self.add_to_game_btn.setToolTip('Add your music to the game alongside the original tracks.')
            if hasattr(self, 'replace_btn'):
                self.replace_btn.show()
                self.replace_btn.setEnabled(True)
                self.replace_btn.setToolTip('Replace all original music with your selected tracks.')
            if hasattr(self, 'replace_and_add_btn'):
                self.replace_and_add_btn.show()
                self.replace_and_add_btn.setEnabled(True)
                self.replace_and_add_btn.setToolTip('Replace specific tracks AND add new tracks to the music pool.')
            # Keep _mode_confirmed_this_session=True so confirmation doesn't appear again this session
    
    def _on_both_mode_chain_step2_biome(self):
        """BOTH MODE - Step 2: Show Biome dialog to select where to ADD new tracks"""
        print(f'[BOTH_CHAIN] Step 2: Showing Biome dialog for ADD selection')
        self.audio_status_label.setText('✅ Mode: Replace and Add (step 2/3: select biomes for new tracks)')
        self._show_biome_dialog(caller='both_mode_biome')
        # Note: _show_biome_dialog will call _on_both_mode_chain_step3_step6 on success
    
    def _on_both_mode_chain_step3_step6(self):
        """BOTH MODE - Step 3: Show Step 6 dialog to select day/night tracks to ADD"""
        print(f'[BOTH_CHAIN] Step 3: Initiating Step 6 track selection for ADD')
        self.audio_status_label.setText('✅ Mode: Replace and Add (step 3/3: select tracks to add)')
        
        # Ensure Step 5 buttons are hidden/disabled during ADD track selection in Both mode
        # User has already committed to Replace + Add, so they can't change modes
        if hasattr(self, 'add_to_game_btn'):
            self.add_to_game_btn.hide()  # Hide instead of just disable for clarity
        if hasattr(self, 'replace_btn'):
            self.replace_btn.hide()  # Hide instead of just disable for clarity
        if hasattr(self, 'replace_and_add_btn'):
            self.replace_and_add_btn.hide()  # Hide instead of just disable for clarity
        
        # Show Step 6 UI (already visible, just ensure user interacts with it)
        self._set_step6_visible(True)
        
        # Scroll to Step 6 on the UI
        if hasattr(self, 'main_scroll_area'):
            try:
                # Find the Step 6 widget and scroll to it
                self.main_scroll_area.ensureWidgetVisible(self.step6_widget)
            except Exception as e:
                self.logger.warn(f'Could not scroll to Step 6: {e}')
        
        self.logger.log('Both mode: Step 6 shown, waiting for track selection', context='BothMode')
        # User will now interact with Step 6 buttons (Add to Day / Add to Night)
        # When Generate Mod is clicked, it will use all three stored states:
        # - self.replace_selections
        # - self.selected_biomes
        # - self.day_tracks / self.night_tracks
        
        # ============================================================================
        # BOTH MODE IMPROVEMENT SUGGESTIONS (Future Polish)
        # ============================================================================
        # 
        # VISUAL / UX NITPICKS (Cosmetic improvements):
        # 1. Dialog chaining transitions could have subtle fade effects or animations
        #    to make the flow feel more polished (not crucial, but nice to have)
        # 2. Button labeling on Step 6 should be clearer that these are for "Add" tracks,
        #    not replacement (consider: "Add to Day" vs current labeling)
        # 3. Visual indicator showing "Progress: Step 1/3 ✓ → Step 2/3 ✓ → Step 3/3 (Active)"
        #    could help users understand where they are in the process more clearly
        # 4. The Replace dialog title/header could indicate it's part of "Both Mode: Step 1"
        # 5. Consider adding a visual separator or highlight to make the Both Mode chain feel distinct
        #
        # SUCCESS FEEDBACK IMPROVEMENTS (UX Polish):
        # 1. After Replace dialog closes successfully, show explicit message:
        #    "✓ Replacement tracks selected: X biome(s) with X day + X night tracks"
        # 2. After Biome selection closes successfully, show explicit message:
        #    "✓ Add destination biomes selected: X biome(s)"
        # 3. When Step 6 shows, show encouragement message:
        #    "✓ Now select which new tracks to add to the selected biomes"
        # 4. Before Generate Mod button is enabled, validate and show:
        #    "✓ Both mode ready: Replace X tracks AND Add X tracks to Y biomes"
        # 5. During Generate Mod with Both mode, show progress:
        #    "Generating mod with BOTH replacement (X tracks) and new additions (X tracks)..."
        # 6. After successful generation, show detailed summary:
        #    "✓ SUCCESS! Mod generated with Both Mode enabled:
        #     - Replaced X tracks across Y biome(s)
        #     - Added Z new tracks to A biome(s)
        #     - Total patch entries: N"
        # 
        # NOTES FOR IMPLEMENTATION:
        # - All feedback should be logged to both UI label AND logger for debugging
        # - Keep messages positive and encouraging
        # - Use emoji indicators (✓, ✓, →) for visual clarity
        # - Ensure feedback doesn't obscure error messages if validation fails
        # ============================================================================

    def _show_biome_dialog(self, caller='normal'):
        """Shared biome selection dialog for all patch modes
        
        Args:
            caller: str - 'normal' (default) or 'both_mode_biome' (chains to next step on OK)
        """
        from utils.patch_generator import get_vanilla_tracks_for_biome
        from pathlib import Path
        from PyQt5.QtWidgets import QMenu
        import subprocess
        
        logger = self.logger
        logger.log('Opening biome selection dialog', context='UI')
        logger.log(f'Patch mode: {getattr(self, "patch_mode", "unknown")}, Caller: {caller}', context='UI')
        
        # Defensive: ensure selected_biomes always exists
        if not hasattr(self, 'selected_biomes'):
            self.selected_biomes = []
        # Show biomes grouped by category for user selection
        biomes = get_all_biomes_by_category()
        dlg = QDialog(self)
        dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dlg.setWindowTitle('Select Biome(s) to Add Music')
        dlg.setMinimumSize(900, 700)
        layout = QVBoxLayout()
        
        # Show mode info
        mode_text = {
            'add': 'Add your music alongside vanilla tracks',
            'replace': 'Replace ALL vanilla tracks with your music',
            'both': 'Replace vanilla tracks, then add your music'
        }
        mode_label = QLabel(f"📋 Mode: {mode_text.get(getattr(self, 'patch_mode', 'add'), 'Unknown')}")
        mode_label.setStyleSheet('color: #e6ecff; font-weight: bold; font-size: 14px;')
        layout.addWidget(mode_label)
        
        # ===== NEW: Optional checkbox for removing vanilla tracks =====
        # Only show in Add mode (Replace/Both modes already replace vanilla)
        remove_vanilla_layout = QHBoxLayout()
        remove_vanilla_layout.setContentsMargins(0, 4, 0, 4)
        
        self.remove_vanilla_checkbox = QCheckBox('🗑️ Remove vanilla tracks first?')
        self.remove_vanilla_checkbox.setToolTip(
            '⭐ THE SAFEST && SIMPLEST OPTION FOR MOST PLAYERS\n\n'
            'Perfect for: Multi-part tracks, album soundtracks, complete theme replacements.\n'
            'Simplest workflow - just check the box! No need for Replace/Both modes.\n\n'
            'WHAT HAPPENS if CHECKED:\n'
            '• ALL vanilla Starbound tracks removed from your chosen biome(s)\n'
            '• Only your custom music will play (100% guaranteed)\n'
            '• Game will never play original biome music (even if mod disabled)\n'
            '• This affects ONLY the selected biome(s)\n\n'
            'MOD COMPATIBILITY:\n'
            '✅ Compatible with ADD-based music mods (no conflict)\n'
            '⚠️ Can conflict with other REPLACE-based mods (same feature level)\n'
            '   If conflict: disable one mod or adjust mod load order\n\n'
            'If UNCHECKED (default):\n'
            '• Your tracks play randomly ALONGSIDE vanilla tracks\n'
            '• Players hear a mix of ~50-60% vanilla + ~40-50% custom (due to quantity)'
        )
        self.remove_vanilla_checkbox.setStyleSheet('''
            QCheckBox {
                color: #ffcc99;
                font-weight: bold;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2a3a4a;
                border: 1px solid #3a4a6a;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #00d4ff;
                border: 1px solid #008899;
                border-radius: 3px;
            }
        ''')
        self.remove_vanilla_checkbox.setChecked(False)  # Default: don't remove
        self.remove_vanilla_checkbox.setVisible(self.patch_mode == 'add')  # Only show in Add mode
        # Connect the checkbox to a confirmation handler
        self.remove_vanilla_checkbox.toggled.connect(self._on_remove_vanilla_toggled)
        remove_vanilla_layout.addWidget(self.remove_vanilla_checkbox)
        remove_vanilla_layout.addStretch()
        layout.addLayout(remove_vanilla_layout)
        
        # Info about what this checkbox does is now in the tooltip (hover over checkbox)

        
        # Check if vanilla tracks are available (look for organized biome folders)
        vanilla_tracks_dir = Path(__file__).parent / 'vanilla_tracks'
        has_vanilla = False
        if vanilla_tracks_dir.exists():
            # Check if any biome folder has day/night subdirectories with files
            day_folders = list(vanilla_tracks_dir.rglob('day'))
            if day_folders:
                for day_folder in day_folders[:1]:  # Just check first one
                    ogg_files = list(day_folder.glob('*.ogg'))
                    if len(ogg_files) > 0:
                        has_vanilla = True
                        break
        
        logger.log(f'Vanilla tracks available: {has_vanilla}', context='BiomeDialog')
        
        if self.patch_mode in ('replace', 'both') and not has_vanilla:
            info_label = QLabel('💡 Vanilla track previews unavailable\nTo see which vanilla tracks will be replaced, copy vanilla music to: StarSound/pygui/vanilla_tracks/music/\nSee vanilla_tracks/README.txt for setup instructions.')
            info_label.setStyleSheet('color: #ffcc99; background-color: #2a2a1a; padding: 8px; border-radius: 4px; font-size: 12px;')
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
        
        label = QLabel('Select one or more biomes:')
        label.setStyleSheet('color: white; font-weight: bold;')
        layout.addWidget(label)
        
        # Use QTreeWidget for expandable biome items with preview support
        from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
        
        class PreviewTreeWidget(QTreeWidget):
            """QTreeWidget with right-click preview support"""
            def __init__(self, parent=None):
                super().__init__(parent)
            
            def contextMenuEvent(self, event):
                """Show context menu for right-click on track items"""
                item = self.itemAt(event.pos())
                if not item:
                    return
                
                # Only show menu for track items (have file_path data)
                file_path = item.data(0, Qt.UserRole + 1)  # Custom role for file path
                if not file_path:
                    return
                
                menu = QMenu(self)
                play_action = menu.addAction('▶ Play Preview')
                action = menu.exec_(event.globalPos())
                
                if action == play_action:
                    try:
                        # Use system audio player to preview track
                        subprocess.Popen(['cmd', '/c', 'start', file_path], creationflags=subprocess.CREATE_NO_WINDOW)
                        logger.log(f'Playing preview: {Path(file_path).name}', context='Preview')
                    except Exception as e:
                        logger.error(f'Failed to play preview: {e}', context='Preview')
                        QMessageBox.warning(self.window(), 'Preview Error', f'Could not play audio: {e}')
        
        tree_widget = PreviewTreeWidget()
        tree_widget.setColumnCount(1)
        tree_widget.setHeaderHidden(True)
        # Enhanced styling for better checkbox visibility and selection
        tree_widget.setStyleSheet('''
            QTreeWidget {
                color: #e6ecff;
                background-color: #1a1f2e;
                font-size: 13px;
                border: 1px solid #3a4a6a;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #283046;
            }
            QTreeWidget::item:selected {
                background-color: #3a6ea5;
                border-left: 3px solid #4e8cff;
                padding-left: 2px;
            }
            QHeaderView::section {
                background-color: #1a1f2e;
                color: #e6ecff;
            }
        ''')
        tree_widget.setSelectionMode(QTreeWidget.NoSelection)  # Disable row selection, use checkboxes instead
        
        vanilla_biome_count = 0
        for category, biome in biomes:
            # Get vanilla tracks if in replace mode
            display_text = f'{category}: {biome}'
            
            if self.patch_mode in ('replace', 'both'):
                vanilla_data = get_vanilla_tracks_for_biome(category, biome)
                day_tracks = vanilla_data.get('dayTracks', [])
                night_tracks = vanilla_data.get('nightTracks', [])
                
                if day_tracks or night_tracks:
                    vanilla_biome_count += 1
                    # Show count inline - NO WARNING since vanilla tracks ARE available
                    day_count = len(day_tracks)
                    night_count = len(night_tracks)
                    display_text = f'{category}: {biome} ✓ [Day: {day_count}, Night: {night_count}]'
                    logger.log(f'Biome {category}/{biome}: Day={day_count}, Night={night_count}', context='BiomeDialog')
            
            # Create biome as parent item
            biome_item = QTreeWidgetItem([display_text])
            biome_item.setData(0, Qt.UserRole, (category, biome))
            # Add checkbox for biome selection
            biome_item.setFlags(biome_item.flags() | Qt.ItemIsUserCheckable)
            biome_item.setCheckState(0, Qt.Unchecked)
            tree_widget.addTopLevelItem(biome_item)
            
            # If replace mode and has vanilla tracks, add expandable track list
            if self.patch_mode in ('replace', 'both'):
                vanilla_data = get_vanilla_tracks_for_biome(category, biome)
                day_tracks = vanilla_data.get('dayTracks', [])
                night_tracks = vanilla_data.get('nightTracks', [])
                
                if day_tracks or night_tracks:
                    # Get replace_selections for this biome (if Both mode)
                    replace_selections = getattr(self, 'replace_selections', {})
                    biome_replace_data = replace_selections.get((category, biome), {}) if self.patch_mode == 'both' else {}
                    day_replacements = biome_replace_data.get('day', {})  # {index: path_to_custom_ogg}
                    night_replacements = biome_replace_data.get('night', {})
                    
                    # Add Day tracks
                    if day_tracks:
                        day_parent = QTreeWidgetItem(biome_item, [f'Day ({len(day_tracks)} tracks)'])
                        day_parent.setForeground(0, QColor('#b19cd9'))  # Light purple
                        for idx, track_path in enumerate(day_tracks):
                            track_name = track_path.split('\\')[-1] if '\\' in track_path else track_path.split('/')[-1]
                            
                            # Check if this track is replaced in Both mode
                            if self.patch_mode == 'both' and idx in day_replacements:
                                custom_path = day_replacements[idx]
                                custom_name = Path(custom_path).name
                                display_text = f'  • {track_name} → {custom_name}'
                                track_item = QTreeWidgetItem(day_parent, [display_text])
                                track_item.setForeground(0, QColor('#ff9999'))  # Red/salmon for replaced
                            else:
                                display_text = f'  • {track_name}'
                                track_item = QTreeWidgetItem(day_parent, [display_text])
                                track_item.setForeground(0, QColor('#a9a9a9'))  # Gray for vanilla
                            
                            track_item.setData(0, Qt.UserRole + 1, str(track_path))  # Store file path for playback
                    
                    # Add Night tracks
                    if night_tracks:
                        night_parent = QTreeWidgetItem(biome_item, [f'Night ({len(night_tracks)} tracks)'])
                        night_parent.setForeground(0, QColor('#b19cd9'))  # Light purple
                        for idx, track_path in enumerate(night_tracks):
                            track_name = track_path.split('\\')[-1] if '\\' in track_path else track_path.split('/')[-1]
                            
                            # Check if this track is replaced in Both mode
                            if self.patch_mode == 'both' and idx in night_replacements:
                                custom_path = night_replacements[idx]
                                custom_name = Path(custom_path).name
                                display_text = f'  • {track_name} → {custom_name}'
                                track_item = QTreeWidgetItem(night_parent, [display_text])
                                track_item.setForeground(0, QColor('#ff9999'))  # Red/salmon for replaced
                            else:
                                display_text = f'  • {track_name}'
                                track_item = QTreeWidgetItem(night_parent, [display_text])
                                track_item.setForeground(0, QColor('#a9a9a9'))  # Gray for vanilla
                            
                            track_item.setData(0, Qt.UserRole + 1, str(track_path))  # Store file path for playback
        
        logger.log(f'Total biomes with vanilla tracks: {vanilla_biome_count}', context='BiomeDialog')
        
        # Function to update item background color based on check state
        def update_item_background(item):
            """Set cyan background for checked items, default for unchecked"""
            if item.checkState(0) == Qt.Checked:
                item.setBackground(0, QColor('#1a4d6d'))  # Cyan-tinted background
                item.setForeground(0, QColor('#00ffff'))  # Bright cyan text
            else:
                item.setBackground(0, QColor('#1a1f2e'))  # Default dark background
                item.setForeground(0, QColor('#e6ecff'))  # Default light text
        
        # Apply initial styling to all biome items and connect to item changed
        def on_item_changed(item, column):
            """Handle checkbox state changes with warning for deselecting filled biomes"""
            # Only handle top-level biome items
            if tree_widget.indexOfTopLevelItem(item) < 0:
                return
            
            biome_data = item.data(0, Qt.UserRole)
            if not biome_data:
                return
            
            # Check if user is UNCHECKING a biome with tracks
            if item.checkState(0) == Qt.Unchecked:
                total_tracks = 0
                day_tracks = []
                night_tracks = []
                
                # Check per-biome selections first
                if hasattr(self, 'add_selections'):
                    tracks_in_biome = self.add_selections.get(biome_data, {})
                    day_tracks_per_biome = tracks_in_biome.get('day', [])
                    night_tracks_per_biome = tracks_in_biome.get('night', [])
                    total_tracks = len(day_tracks_per_biome) + len(night_tracks_per_biome)
                    day_tracks = day_tracks_per_biome
                    night_tracks = night_tracks_per_biome
                
                # If no per-biome tracks, check global day_tracks/night_tracks (for backwards compatibility)
                if total_tracks == 0 and hasattr(self, 'day_tracks') and hasattr(self, 'night_tracks'):
                    day_tracks = self.day_tracks if self.day_tracks else []
                    night_tracks = self.night_tracks if self.night_tracks else []
                    total_tracks = len(day_tracks) + len(night_tracks)
                
                # If this biome has tracks, warn the user
                if total_tracks > 0:
                    # Create warning dialog with track list
                    warning_dlg = QDialog(dlg)
                    warning_dlg.setWindowFlags(warning_dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
                    warning_dlg.setWindowTitle('⚠️ Tracks Will Be Removed')
                    warning_dlg.setMinimumSize(500, 350)
                    warn_layout = QVBoxLayout(warning_dlg)
                    
                    # Warning message
                    warn_text = QLabel(
                        f'<b>⚠️ Warning!</b><br><br>'
                        f'The biome <b>{biome_data[0]}: {biome_data[1]}</b> has <b>{total_tracks} track(s)</b> already assigned.<br><br>'
                        f'<b>If you uncheck this biome, all {total_tracks} track(s) will be PERMANENTLY DELETED.</b><br><br>'
                        f'<i>Tracks to be removed:</i>'
                    )
                    warn_text.setWordWrap(True)
                    warn_layout.addWidget(warn_text)
                    
                    # Scrollable track list (similar to View All Tracks)
                    tracks_display = QTextEdit()
                    tracks_display.setReadOnly(True)
                    tracks_display.setStyleSheet('background-color: #181c2a; color: #e6ecff; font-size: 11px; border-radius: 4px;')
                    
                    track_list_html = '<b>Day Tracks:</b><br>'
                    if day_tracks:
                        for track in day_tracks:
                            track_name = Path(track).name
                            track_list_html += f'  • {track_name}<br>'
                    else:
                        track_list_html += '  (none)<br>'
                    
                    track_list_html += '<br><b>Night Tracks:</b><br>'
                    if night_tracks:
                        for track in night_tracks:
                            track_name = Path(track).name
                            track_list_html += f'  • {track_name}<br>'
                    else:
                        track_list_html += '  (none)<br>'
                    
                    tracks_display.setHtml(track_list_html)
                    warn_layout.addWidget(tracks_display, 1)
                    
                    # Buttons
                    button_layout = QHBoxLayout()
                    cancel_btn = QPushButton('Cancel - Keep Biome')
                    cancel_btn.setStyleSheet('background-color: #3a6ea5; color: #e6ecff; padding: 8px;')
                    delete_btn = QPushButton('❌ Delete Tracks && Uncheck')
                    delete_btn.setStyleSheet('background-color: #c41e3a; color: #e6ecff; padding: 8px;')
                    
                    button_layout.addWidget(cancel_btn)
                    button_layout.addStretch()
                    button_layout.addWidget(delete_btn)
                    warn_layout.addLayout(button_layout)
                    
                    # Result variable
                    result = {'delete': False}
                    
                    def on_cancel():
                        result['delete'] = False
                        warning_dlg.accept()
                    
                    def on_delete():
                        result['delete'] = True
                        warning_dlg.accept()
                    
                    cancel_btn.clicked.connect(on_cancel)
                    delete_btn.clicked.connect(on_delete)
                    
                    warning_dlg.exec_()
                    
                    # If user clicked Cancel, re-check the item
                    if not result['delete']:
                        tree_widget.blockSignals(True)  # Prevent infinite recursion
                        item.setCheckState(0, Qt.Checked)
                        update_item_background(item)
                        tree_widget.blockSignals(False)
                        return
                    else:
                        # User confirmed deletion - remove per-biome tracks if they exist
                        if biome_data in self.add_selections:
                            del self.add_selections[biome_data]
                            logger.log(f'Deleted {total_tracks} tracks from {biome_data[0]}:{biome_data[1]}', context='BiomeDialog')
                        else:
                            logger.log(f'Unchecked {biome_data[0]}:{biome_data[1]} - removed from biome selection', context='BiomeDialog')
                        
                        # Also remove from selected_biomes to prevent restoration on dialog reopen
                        if biome_data in self.selected_biomes:
                            self.selected_biomes.remove(biome_data)
            
            # Update styling
            update_item_background(item)
        
        # Apply initial styling to all biome items
        for i in range(tree_widget.topLevelItemCount()):
            item = tree_widget.topLevelItem(i)
            update_item_background(item)
        
        # Connect to itemChanged to update styling when checkbox is toggled
        tree_widget.itemChanged.connect(on_item_changed)
        
        layout.addWidget(tree_widget)
        
        # Confirmation label
        confirm_label = QLabel('No biomes selected.')
        confirm_label.setStyleSheet('color: #e6ecff; font-size: 13px; margin-top: 8px;')
        layout.addWidget(confirm_label)

        # Restore previous selection from two sources:
        # 1. selected_biomes list (primary)
        # 2. add_selections keys (if biomes have tracks but selected_biomes is empty)
        
        biomes_to_check = set(self.selected_biomes) if self.selected_biomes else set()
        
        # If no biomes in selected_biomes but we have add_selections with tracks, use those
        if not biomes_to_check and hasattr(self, 'add_selections') and self.add_selections:
            biomes_to_check = set(self.add_selections.keys())
            logger.log(f'Syncing: Found {len(biomes_to_check)} biomes in add_selections, checking them', context='BiomeDialog')
        
        # Check the biomes
        if biomes_to_check:
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                if item.data(0, Qt.UserRole) in biomes_to_check:
                    item.setCheckState(0, Qt.Checked)

        # 🆕 BOTH MODE: Different button label to indicate it stays open
        ok_btn = QPushButton('OK')
        ok_btn.setToolTip('Confirm biome selection')
        
        # Create button row with Help, Screenshot, and OK
        button_row = QHBoxLayout()
        
        # Help button (lifeboat icon)
        help_btn = QPushButton('🛟')
        help_btn.setToolTip('Biome selection help')
        help_btn.setMaximumWidth(50)
        def show_help():
            help_dlg = QDialog(dlg)
            help_dlg.setWindowFlags(help_dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            help_dlg.setWindowTitle('Biome Selection Help')
            help_dlg.setMinimumSize(450, 300)
            help_layout = QVBoxLayout(help_dlg)
            help_text = QLabel(
                '<b>How to Select Biomes</b><br><br>'
                '✓ <b>Check the box</b> next to any biome you want to modify<br><br>'
                '<b>Mode-Specific Info:</b><br>'
                '• <b>Add Mode:</b> Your music plays alongside original tracks<br>'
                '• <b>Replace Mode:</b> Your music replaces original tracks<br>'
                '• <b>Both Mode:</b> Replace some, add others (select biomes for new tracks)<br><br>'
                '<b>Tips:</b><br>'
                '• Use surface_ prefix for surface biomes<br>'
                '• Use underground_ prefix for cave biomes<br>'
                '• Hover over biomes to see vanilla track counts<br>'
                '• Multi-select by checking multiple boxes<br><br>'
                '⚠️ <b>Important:</b> Selected biomes only affect your current mod. '
                'Create a new mod to customize different biomes.'
            )
            help_text.setWordWrap(True)
            help_layout.addWidget(help_text)
            close_btn = QPushButton('Close')
            close_btn.clicked.connect(help_dlg.accept)
            help_layout.addWidget(close_btn)
            help_dlg.exec_()
        help_btn.clicked.connect(show_help)
        button_row.addWidget(help_btn)
        
        # Screenshot button (icon only)
        screenshot_btn = QPushButton('📸')
        screenshot_btn.setToolTip('Take a screenshot of this dialog')
        screenshot_btn.setMaximumWidth(50)
        def take_screenshot_dialog():
            try:
                success, msg = take_screenshot(dlg)
                if success:
                    QMessageBox.information(dlg, 'Screenshot Saved', msg)
                else:
                    QMessageBox.warning(dlg, 'Screenshot Failed', msg)
            except Exception as e:
                QMessageBox.warning(dlg, 'Screenshot Failed', f'Could not save screenshot: {e}')
        screenshot_btn.clicked.connect(take_screenshot_dialog)
        button_row.addWidget(screenshot_btn)
        
        # Select All button
        select_all_btn = QPushButton('Select All')
        select_all_btn.setStyleSheet('background-color: #3a6ea5; color: #e6ecff; padding: 6px;')
        select_all_btn.setToolTip('Check all biomes')
        def select_all():
            tree_widget.blockSignals(True)
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                item.setCheckState(0, Qt.Checked)
            tree_widget.blockSignals(False)
            # Manually trigger update_confirmation to refresh label
            update_confirmation()
        select_all_btn.clicked.connect(select_all)
        button_row.addWidget(select_all_btn)
        
        # Deselect All button
        deselect_all_btn = QPushButton('Deselect All')
        deselect_all_btn.setStyleSheet('background-color: #3a6ea5; color: #e6ecff; padding: 6px;')
        deselect_all_btn.setToolTip('Uncheck all biomes and delete their tracks')
        def deselect_all():
            """Deselect all biomes and warn user about track deletion"""
            # Collect all biomes with tracks
            biomes_with_tracks = {}
            total_tracks = 0
            
            # Check each biome for tracks in add_selections
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                biome_data = item.data(0, Qt.UserRole)
                if not biome_data:
                    continue
                
                day_tracks_list = []
                night_tracks_list = []
                
                # Check per-biome selections
                if hasattr(self, 'add_selections') and biome_data in self.add_selections:
                    tracks_in_biome = self.add_selections[biome_data]
                    day_tracks_list = tracks_in_biome.get('day', [])
                    night_tracks_list = tracks_in_biome.get('night', [])
                
                # If this biome has tracks, add to warning list
                track_count = len(day_tracks_list) + len(night_tracks_list)
                if track_count > 0:
                    biomes_with_tracks[biome_data] = {
                        'day': day_tracks_list,
                        'night': night_tracks_list,
                        'count': track_count
                    }
                    total_tracks += track_count
            
            # If no tracks exist, just deselect all without warning
            if not biomes_with_tracks:
                tree_widget.blockSignals(True)
                for i in range(tree_widget.topLevelItemCount()):
                    item = tree_widget.topLevelItem(i)
                    item.setCheckState(0, Qt.Unchecked)
                tree_widget.blockSignals(False)
                update_confirmation()
                return
            
            # Show warning dialog with all biomes and tracks
            warning_dlg = QDialog(dlg)
            warning_dlg.setWindowFlags(warning_dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            warning_dlg.setWindowTitle('⚠️ Delete All Tracks?')
            warning_dlg.setMinimumSize(550, 400)
            warn_layout = QVBoxLayout(warning_dlg)
            
            # Warning message
            warn_text = QLabel(
                f'<b>⚠️ Warning!</b><br><br>'
                f'You are about to <b>PERMANENTLY DELETE ALL tracks</b> from <b>{len(biomes_with_tracks)} biome(s)</b>.<br><br>'
                f'<b>Total tracks to be deleted: {total_tracks}</b><br><br>'
                f'<i>Biomes and their tracks:</i>'
            )
            warn_text.setWordWrap(True)
            warn_layout.addWidget(warn_text)
            
            # Scrollable list of biomes with track counts
            biomes_display = QTextEdit()
            biomes_display.setReadOnly(True)
            biomes_display.setStyleSheet('background-color: #181c2a; color: #e6ecff; font-size: 11px; border-radius: 4px;')
            
            biome_list_html = ''
            for (cat, bio), track_data in sorted(biomes_with_tracks.items()):
                day_count = len(track_data['day'])
                night_count = len(track_data['night'])
                biome_list_html += f'<b>{cat}: {bio}</b> ({track_data["count"]} tracks)<br>'
                
                if track_data['day']:
                    biome_list_html += f'  <i>Day ({day_count}):</i><br>'
                    for track in track_data['day']:
                        track_name = Path(track).name
                        biome_list_html += f'    • {track_name}<br>'
                
                if track_data['night']:
                    biome_list_html += f'  <i>Night ({night_count}):</i><br>'
                    for track in track_data['night']:
                        track_name = Path(track).name
                        biome_list_html += f'    • {track_name}<br>'
                
                biome_list_html += '<br>'
            
            biomes_display.setHtml(biome_list_html)
            warn_layout.addWidget(biomes_display, 1)
            
            # Buttons
            button_layout = QHBoxLayout()
            cancel_btn = QPushButton('Cancel - Keep Biomes')
            cancel_btn.setStyleSheet('background-color: #3a6ea5; color: #e6ecff; padding: 8px;')
            delete_btn = QPushButton('❌ Delete All Tracks && Deselect')
            delete_btn.setStyleSheet('background-color: #c41e3a; color: #e6ecff; padding: 8px;')
            
            button_layout.addWidget(cancel_btn)
            button_layout.addStretch()
            button_layout.addWidget(delete_btn)
            warn_layout.addLayout(button_layout)
            
            # Result variable
            result = {'delete': False}
            
            def on_cancel():
                result['delete'] = False
                warning_dlg.accept()
            
            def on_delete():
                result['delete'] = True
                warning_dlg.accept()
            
            cancel_btn.clicked.connect(on_cancel)
            delete_btn.clicked.connect(on_delete)
            
            warning_dlg.exec_()
            
            # If user cancelled, do nothing
            if not result['delete']:
                return
            
            # User confirmed - delete all tracks from all biomes and deselect
            for biome_data in biomes_with_tracks.keys():
                # Delete per-biome tracks
                if biome_data in self.add_selections:
                    del self.add_selections[biome_data]
                    logger.log(f'Deleted {biomes_with_tracks[biome_data]["count"]} tracks from {biome_data[0]}:{biome_data[1]}', context='BiomeDialog')
                
                # Remove from selected_biomes
                if biome_data in self.selected_biomes:
                    self.selected_biomes.remove(biome_data)
            
            # Now deselect all biomes in the tree
            tree_widget.blockSignals(True)
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                item.setCheckState(0, Qt.Unchecked)
            tree_widget.blockSignals(False)
            update_confirmation()
        
        deselect_all_btn.clicked.connect(deselect_all)
        button_row.addWidget(deselect_all_btn)
        
        button_row.addStretch()
        button_row.addWidget(ok_btn)
        layout.addLayout(button_row)
        dlg.setLayout(layout)

        def update_confirmation():
            # Get checked biome items (only top-level items)
            selected = []
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                if item.checkState(0) == Qt.Checked:
                    biome_data = item.data(0, Qt.UserRole)
                    if biome_data:
                        selected.append(biome_data)
            
            if selected:
                confirm_label.setText(f'Selected biomes: {", ".join([f"{cat}:{bio}" for cat, bio in selected])}')
            else:
                confirm_label.setText('No biomes selected.')

        tree_widget.itemSelectionChanged.connect(update_confirmation)
        update_confirmation()  # Show confirmation for restored selection

        def on_ok():
            update_confirmation()
            # Get checked biome items (only top-level items, not child track items)
            selected = []
            for i in range(tree_widget.topLevelItemCount()):
                item = tree_widget.topLevelItem(i)
                if item.checkState(0) == Qt.Checked:
                    biome_data = item.data(0, Qt.UserRole)
                    if biome_data:
                        selected.append(biome_data)
            
            if not selected and caller == 'both_mode_biome':
                # In Both mode, biomes are REQUIRED
                QMessageBox.warning(self, 'No Biomes Selected', 'Please select at least one biome for your new tracks.')
                return
            
            # 🆕 VALIDATE: If "Remove vanilla tracks" is checked, verify selected biomes have vanilla tracks
            if self.remove_vanilla_checkbox.isChecked() and selected:
                from utils.patch_generator import get_vanilla_tracks_for_biome
                biomes_without_vanilla = []
                
                for biome_category, biome_name in selected:
                    vanilla_data = get_vanilla_tracks_for_biome(biome_category, biome_name)
                    day_tracks = vanilla_data.get('dayTracks', [])
                    night_tracks = vanilla_data.get('nightTracks', [])
                    
                    # If biome has no vanilla tracks, add to warning list
                    if not day_tracks and not night_tracks:
                        biomes_without_vanilla.append(f'{biome_category}:{biome_name}')
                
                # If some biomes have no vanilla tracks, warn user
                if biomes_without_vanilla:
                    biome_list = ", ".join(biomes_without_vanilla)
                    reply = QMessageBox.warning(
                        self,
                        'No Vanilla Tracks to Remove',
                        f'You checked "Remove vanilla tracks" but these biomes have NO vanilla track data:\n\n{biome_list}\n\n'
                        f'The remove operation will have nothing to remove for these biome(s).\n\n'
                        f'Continue anyway? (Your custom tracks will still be added)',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return  # Cancel dialog
                    
                    # User clicked Yes - proceed with warning in log
                    logger.warn(
                        f'Remove vanilla tracks checked, but biomes with no vanilla data selected: {biome_list}. '
                        f'Remove operations will be skipped for these biomes.'
                    )
            
            self.selected_biomes = selected  # Save selection for persistence
            
            # 🆕 CAPTURE: Store the "Remove vanilla tracks" checkbox state
            self.remove_vanilla_tracks = self.remove_vanilla_checkbox.isChecked()
            logger.log(f'Remove vanilla tracks: {self.remove_vanilla_tracks}', context='BiomeDialog')
            
            self._auto_save_mod_state('biome selection')
            self.update_patch_btn_state()  # Update patch button state
            
            # Update visual feedback labels
            if selected:
                self.audio_status_label.setText(f'✅ Biomes selected: {", ".join([f"{cat}:{bio}" for cat, bio in selected])}')
                # Update Step 6 biome label if it exists
                if hasattr(self, 'selected_biomes_label'):
                    # Format: ✓ Biomes (88): biome1, biome2, biome3, biome4, biome5, and 83 more
                    biome_names = [bio for cat, bio in selected]
                    biome_count = len(biome_names)
                    if biome_count <= 5:
                        biome_display = ", ".join(biome_names)
                    else:
                        first_five = ", ".join(biome_names[:5])
                        remaining = biome_count - 5
                        biome_display = f'{first_five}, and {remaining} more'
                    self.selected_biomes_label.setText(f'✓ Biomes ({biome_count}): {biome_display}')
            else:
                self.audio_status_label.setText('No biomes selected.')
                if hasattr(self, 'selected_biomes_label'):
                    self.selected_biomes_label.setText('No biomes selected yet.')
            
            dlg.accept()
        ok_btn.clicked.connect(on_ok)
        dlg.exec_()

    def _on_remove_vanilla_toggled(self, checked):
        """Show confirmation dialog when user tries to enable 'Remove vanilla tracks'"""
        if checked and hasattr(self, 'remove_vanilla_checkbox'):
            # User is trying to ENABLE the checkbox - show confirmation
            reply = QMessageBox.question(
                self,
                '⚠️ Remove All Vanilla Tracks?',
                (
                    'Are you SURE? This will:\n\n'
                    'CLEAR all vanilla Starbound tracks from selected biome(s)\n'
                    '• Replaces vanilla track arrays with empty arrays\n'
                    '• Adds only YOUR custom music to the biome\n'
                    '• Only YOUR music will play in these biomes (100% guaranteed)\n'
                    '• This change applies ONLY to selected biome(s)\n\n'
                    'CONFLICT WARNING ⚠️ MOD COMPATIBILITY:\n'
                    '• Remove Mode uses REPLACE operations (like Replace Mode)\n'
                    '• WILL conflict with other REPLACE-based music mods\n'
                    '• ADD-based mods are fine (no conflict)\n'
                    '• If conflict occurs: only one mod\'s music will play\n'
                    '• Solution: Disable one mod, or adjust mod load order\n\n'
                    'CONSEQUENCE if mod is later disabled/removed:\n'
                    '• Affected biomes will never play original music again unless mod is reinstalled\n'
                    'RECOMMENDATION:\n'
                    '• Ideal when you want FULL control and ONLY your music to play\n'
                    '• Perfect for complete thematic replacements or multi-part tracks\n'
                    '• Keep backup of mod for easy recovery\n'
                    '• Check if other music mods use ADD mode (safe together)\n\n'
                    'This is the SAFEST option for most players (simplest && fastest).\n'
                    'Once a world/save is loaded with this mode enabled, that world/save will only play your custom music.\n'
                    '\n'
                    'Continue with Remove Mode?'
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                # User said No - uncheck the box
                self.remove_vanilla_checkbox.blockSignals(True)
                self.remove_vanilla_checkbox.setChecked(False)
                self.remove_vanilla_checkbox.blockSignals(False)

    def _check_vanilla_tracks_on_startup(self):
        """Check if vanilla tracks are available, offer to set up if missing"""
        from pathlib import Path
        
        vanilla_tracks_dir = Path(__file__).parent / 'vanilla_tracks'
        
        # Check if vanilla tracks exist (by looking for day folders)
        has_vanilla = False
        if vanilla_tracks_dir.exists():
            day_folders = list(vanilla_tracks_dir.rglob('day'))
            if day_folders:
                for day_folder in day_folders[:1]:
                    if len(list(day_folder.glob('*.ogg'))) > 0:
                        has_vanilla = True
                        break
        
        if not has_vanilla:
            # Ask user if they want to set up vanilla tracks
            reply = QMessageBox.question(
                self,
                'StarSound - Vanilla Music Replacer Setup',
                'Do you want to replace original Starbound music with your own? (Safely, no actual game files will be modified)\n\n'
                'If so, StarSound needs to unpack original Starbound music files so you can preview them when you select tracks.\n\n'
                'Quick setup takes 1-2 minutes:\n'
                '• Safely backs up your game files before unpacking.\n'
                '• Extracts original Starbound music to StarSound\'s vanilla_tracks folder.\n'
                '• Lets you preview original Starbound tracks if you decide to replace them with your music.\n\n'
                'Want to set it up now?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Show setup wizard
                from utils.vanilla_setup_wizard import VanillaSetupWizard
                from utils.starbound_locator import find_starbound_folder
                
                game_path = find_starbound_folder()
                if not game_path:
                    QMessageBox.warning(
                        self,
                        'Oops!',
                        'We couldn\'t find your Starbound installation.\n\n'
                        'Make sure Starbound is installed in the usual place,\n'
                        'then try again.'
                    )
                    return
                
                starsound_dir = Path(__file__).parent.parent
                wizard = VanillaSetupWizard(self, str(game_path), str(starsound_dir))
                wizard.exec_()

    def show_emergency_beacon(self):
        dlg = EmergencyBeaconDialog(self)
        dlg.exec_()

    def _preload_custom_fonts(self):
        """Pre-register all custom fonts from assets/font/ folder.
        
        This must be called BEFORE _apply_font_to_app() so that custom fonts
        like FOT-PopHappiness are available in QFontDatabase when we try to use them.
        """
        from PyQt5.QtGui import QFontDatabase
        from pathlib import Path
        
        font_folder = Path(__file__).parent / 'assets' / 'font'
        if font_folder.exists():
            # Load both .ttf and .otf files
            font_files = list(font_folder.glob('*.ttf')) + list(font_folder.glob('*.otf'))
            for font_file in font_files:
                try:
                    font_id = QFontDatabase.addApplicationFont(str(font_file))
                    if font_id != -1:
                        families = QFontDatabase.applicationFontFamilies(font_id)
                        # Silently succeed
                except Exception as e:
                    pass  # Silently fail

    def _get_available_fonts(self):
        """Get list of fonts actually available on the system.
        
        Also loads custom fonts from pygui/assets/font/ folder.
        
        Returns:
            List of font names that can actually be rendered
        """
        from PyQt5.QtGui import QFontDatabase, QFont
        from pathlib import Path
        
        # Always include Hobo first (custom bundled font)
        available = ['Hobo']
        
        # Load any .ttf or .otf files from the fonts folder as custom application fonts
        font_folder = Path(__file__).parent / 'assets' / 'font'
        if font_folder.exists():
            # Support both TrueType (.ttf) and OpenType (.otf) fonts
            for font_file in list(font_folder.glob('*.ttf')) + list(font_folder.glob('*.otf')):
                if font_file.name.lower() != 'hobo.ttf':  # Skip Hobo, already handled
                    font_id = QFontDatabase.addApplicationFont(str(font_file))
                    if font_id >= 0:
                        families = QFontDatabase.applicationFontFamilies(font_id)
                        if families:
                            available.append(families[0])
                            print(f'[FONT DEBUG] Loaded custom font: {families[0]} from {font_file.name}')
                    else:
                        print(f'[FONT DEBUG] Failed to load custom font: {font_file.name} (font_id={font_id})')
        
        # System fonts that Windows typically has
        # Note: Some fonts may appear in QFontDatabase but not render properly
        candidate_fonts = [
            'Segoe UI',
            'Arial',
            'Verdana',
            'Georgia',
            'Times New Roman',
            'Courier New',
            'Calibri',
            'Consolas',
            'Trebuchet MS',
            'Tahoma',
            'Comic Sans MS',
            'Wingdings',  # 🎨 Chaos font - symbols instead of letters
            'Impact'      # 📢 Meme font energy
        ]
        
        db = QFontDatabase()
        available_families = set(db.families())
        
        # Add only fonts that are actually in the database
        # (This is a better check than before)
        for font_name in candidate_fonts:
            if any(font_name.lower() == fam.lower() for fam in available_families):
                available.append(font_name)
        
        # If we only have Hobo, add system fallbacks
        if len(available) == 1:
            available.extend(['Arial', 'Times New Roman', 'Courier New'])
        
        return available

    def _apply_stylesheet_with_font(self, font_name: str):
        """Generate and apply stylesheet WITH font-family.
        
        Font-family MUST be in the stylesheet for proper rendering with stylesheets.
        Qt cascading: stylesheets > programmatic setFont(), so we include font here.
        
        Args:
            font_name: Font family name to include in stylesheet
        """
        stylesheet = f'''
* {{
    font-family: "{font_name}";
}}
QMainWindow {{
    background-color: #23283b;
}}
QWidget {{
    background-color: #23283b;
}}
QWidget#centralWidget {{
    background-color: transparent;
}}
QScrollArea {{
    background-color: #23283b;
    border: 1px solid #3a4a6a;
}}
QGroupBox, QFrame {{
    background-color: #23283b;
    border: none;
}}
QDialog {{
    background-color: #23283b;
}}
QLabel, QMenuBar, QToolBar {{
    color: #e6ecff;
    font-family: "{font_name}";
    font-size: 15px;
    background-color: transparent;
}}
QMenuBar {{
    background-color: #23283b;
    color: #e6ecff;
    border: none;
}}
QMenuBar::item:selected {{
    background-color: #3a6ea5;
    color: #e6ecff;
}}
QMenuBar::item:pressed {{
    background-color: #3a6ea5;
    color: #e6ecff;
}}
QMenu {{
    background-color: #283046;
    color: #e6ecff;
    border: 1px solid #3a4a6a;
}}
QMenu::item:selected {{
    background-color: #3a6ea5;
    color: #e6ecff;
}}
QLineEdit, QTextEdit {{
    background: #283046;
    color: #e6ecff;
    border-radius: 8px;
    border: 1px solid #3a4a6a;
    font-family: "{font_name}";
    font-size: 15px;
}}
QPushButton {{
    background-color: #3a6ea5;
    color: #e6ecff;
    border-radius: 10px;
    border: 1px solid #4e8cff;
    padding: 6px 18px;
    font-family: "{font_name}";
    font-size: 15px;
}}
QPushButton:hover {{
    background-color: #4e8cff;
    border: 1px solid #6bbcff;
}}
QMessageBox {{
    background: #23283b;
    color: #e6ecff;
}}
QGroupBox {{
    background-color: #283046;
    border: 1px solid #3a4a6a;
    border-radius: 8px;
    margin-top: 10px;
}}
        '''
        # Apply stylesheet with fonts included
        super(MainWindow, self).setStyleSheet(stylesheet)

    def _apply_font_to_app(self, font_name: str):
        """Apply a font to the entire application via stylesheets.
        
        Fonts are now applied through stylesheets for better reliability
        than programmatic setFont() calls in the presence of stylesheets.
        
        Args:
            font_name: Name of the font to apply (e.g., 'Hobo', 'Segoe UI', 'Arial')
        """
        from PyQt5.QtWidgets import QApplication
        import time
        
        # Guard against duplicate applications of the same font
        current_time = time.time()
        if (self._last_font_applied == font_name and 
            (current_time - self._last_font_time) < 0.5):
            # Same font applied within last 500ms, skip
            return
        
        self._last_font_applied = font_name
        self._last_font_time = current_time
        self.current_font = font_name  # Track for dialogs
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.log(f'Applying font to entire app: {font_name}')
        
        # Re-apply stylesheet with new font
        self._apply_stylesheet_with_font(font_name)
        
        # Force Qt to re-evaluate stylesheet styles
        QApplication.instance().setStyle(QApplication.instance().style())
        
        # Restore font previews on menu items
        self._restore_font_menu_previews()
        
        # Force repaint
        self.update()
        self.repaint()
        
        if hasattr(self, 'logger') and self.logger:
            self.logger.log(f'Font application complete: {font_name}')

    def _set_font_recursive(self, widget, font):
        """Recursively set font on widget and all children.
        
        Args:
            widget: The widget to update
            font: The QFont to apply
        """
        widget.setFont(font)
        for child in widget.findChildren(object):
            try:
                child.setFont(font)
            except:
                # Some objects might not have setFont, skip them
                pass

    def _restore_font_menu_previews(self):
        """Re-apply individual font previews to menu items.
        
        When we apply a font to the entire app, menu items get overridden.
        This function restores each menu item to display in its own font
        so the Fonts menu shows a preview of what each font looks like.
        """
        available_fonts = self._get_available_fonts()
        
        # Find the Fonts menu action in the menubar
        for action in self.menuBar().actions():
            if action.text() == 'Fonts':
                fonts_menu = action.menu()
                if fonts_menu:
                    # Get all menu actions in the Fonts menu
                    for font_action in fonts_menu.actions():
                        # Get font name from stored data instead of text
                        font_name = font_action.data()
                        
                        # Only restore if it's a valid font
                        if font_name and font_name in available_fonts:
                            preview_font = QFont(font_name, 10)
                            font_action.setFont(preview_font)

    def take_screenshot_action(self):
        import time
        now = time.time()
        if not hasattr(self, 'last_screenshot_time'):
            self.last_screenshot_time = 0
        if now - self.last_screenshot_time < 1.0:
            QMessageBox.warning(self, 'Screenshot', 'You are taking screenshots too quickly! Please wait a moment.')
            return
        self.last_screenshot_time = now
        # Pass self to take_screenshot so only the app window is captured
        success, msg = take_screenshot(self)
        if success:
            self.screenshot_status_label.setText(msg)
            self.logger.log(f'Screenshot taken: {msg}')
        else:
            self.screenshot_status_label.setText(f'Error: {msg}')
            self.logger.error(f'Screenshot failed: {msg}')
            QMessageBox.warning(self, 'Screenshot', msg)

    def browse_folder(self):
            # Log folder browse action
        folder = QFileDialog.getExistingDirectory(self, 'Select Mod Folder')
        if folder:
            self.folder_input.setText(folder)
            self.settings.set('last_mod_folder', folder)  # Save to persistent settings
            self.logger.update_metadata(mod_path=folder)
            self.logger.log(f'User browsed and selected mod folder: {folder}')
        else:
            self.logger.log('User cancelled mod folder browse dialog')

    def _refresh_selected_files_display(self):
        """Refresh the selected files display label to show current selected_audio_files list."""
        if hasattr(self, 'selected_audio_files') and self.selected_audio_files:
            filenames = [os.path.basename(f) for f in self.selected_audio_files]
            bullet_lines = ['<span style="font-size:13px">Selected:</span>']
            
            self.files_needing_split.clear()
            self.split_decisions.clear()
            
            from utils.audio_utils import get_audio_duration
            for file_path, basename in zip(self.selected_audio_files, filenames):
                duration_minutes = get_audio_duration(file_path)
                
                if duration_minutes and duration_minutes > 30:
                    self.files_needing_split[file_path] = duration_minutes
                    display_label = f'&bull; {basename} <span style="color: #ffcc00;">⚠️ {duration_minutes:.1f} min</span>'
                else:
                    display_label = f'&bull; {basename}'
                
                bullet_lines.append(display_label)
            
            self.selected_files_label.setText('<br>'.join(bullet_lines))
        else:
            self.selected_files_label.setText('')

    def _check_for_duplicate_tracks(self, files: list, mod_music_path: Path) -> list:
        """
        Check if any selected files would create duplicate OGG files in the mod folder.
        Shows dialog if duplicates found, returns files user selected to process.
        
        Args:
            files: List of file paths to check
            mod_music_path: Path to mod's music folder
            
        Returns:
            List of files to process (may be subset if user chose Skip)
        """
        if not mod_music_path.exists():
            return files  # No duplicates possible if folder doesn't exist yet
        
        from utils.audio_utils import sanitize_filename
        import os
        
        duplicates = []
        new_files = []
        
        for file_path in files:
            # Match the exact logic from atomicwriter.py:
            # 1. Remove extension first (os.path.splitext)
            # 2. Sanitize the base name
            # 3. Add .ogg extension
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            sanitized_base = sanitize_filename(base_name)
            ogg_filename = f"{sanitized_base}.ogg"
            ogg_path = mod_music_path / ogg_filename
            
            # Check for main file OR any split parts (_part1, _part2, etc.)
            is_duplicate = False
            if ogg_path.exists():
                is_duplicate = True
            else:
                # Check for split files: base_part1.ogg, base_part2.ogg, etc.
                part_num = 1
                while True:
                    part_path = mod_music_path / f"{sanitized_base}_part{part_num}.ogg"
                    if part_path.exists():
                        is_duplicate = True
                        break
                    part_num += 1
                    if part_num > 20:  # Safety limit - don't check more than 20 parts
                        break
            
            if is_duplicate:
                duplicates.append({
                    'original': os.path.basename(file_path),
                    'converted': ogg_filename,
                    'full_path': file_path
                })
            else:
                new_files.append(file_path)
        
        if not duplicates:
            return files  # No duplicates found
        
        # Show dialog with duplicate conflicts
        dup_message = (
            f'⚠️ These {len(duplicates)} file(s) already exist in your mod:\n\n'
        )
        
        for i, dup in enumerate(duplicates[:5], 1):  # Show first 5
            dup_message += f'{i}. {dup["converted"]}\n'
        
        if len(duplicates) > 5:
            dup_message += f'\n... and {len(duplicates) - 5} more'
        
        # Create message box with custom button labels
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle('🔄 Duplicate OGG Files Detected')
        msg_box.setText(dup_message)
        
        skip_btn = msg_box.addButton('Skip', QMessageBox.NoRole)
        overwrite_btn = msg_box.addButton('Overwrite', QMessageBox.AcceptRole)
        cancel_btn = msg_box.addButton('Cancel', QMessageBox.RejectRole)
        msg_box.setDefaultButton(cancel_btn)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == skip_btn:
            # Skip - remove duplicates from selected list, keep new files to add
            duplicate_paths = [d['full_path'] for d in duplicates]
            duplicate_basenames = [os.path.basename(d['full_path']).lower() for d in duplicates]
            
            if hasattr(self, 'selected_audio_files'):
                # Remove by both full path AND basename (handles path format differences)
                self.selected_audio_files = [
                    f for f in self.selected_audio_files 
                    if f not in duplicate_paths and os.path.basename(f).lower() not in duplicate_basenames
                ]
                # Refresh UI immediately to show removed duplicates
                self._refresh_selected_files_display()
            
            self.logger.log(f'[DUPLICATES] Skipped {len(duplicates)} duplicate files. Keeping {len(new_files)} new file(s).')
            return new_files  # Add only the new files, not the duplicates
        
        elif msg_box.clickedButton() == overwrite_btn:
            # Overwrite - keep all files for conversion (duplicates + new)
            self.logger.log(f'[DUPLICATES] User will overwrite {len(duplicates)} existing OGG files')
            return files  # Add all files (duplicates will overwrite, new will be added)
        
        else:  # Cancel
            self.logger.log(f'[DUPLICATES] User cancelled file selection ({len(duplicates)} duplicates found)')
            return []  # Cancel - don't add any files

    def browse_audio(self):
        # Log audio file browse action
        # Use HOME directory as default, or last used directory if available
        if not hasattr(self, '_last_audio_dir'):
            from pathlib import Path
            self._last_audio_dir = str(Path.home())
        
        # File filter: Audio formats that need conversion (not OGG - those go directly to mod folder)
        file_filter = (
            'Audio Files (*.mp3 *.wav *.flac *.aac *.wma *.m4a *.ogg);;'
            'MP3 Files (*.mp3);;'
            'WAV Files (*.wav);;'
            'FLAC Files (*.flac);;'
            'All Files (*.*)'
        )
        files, _ = QFileDialog.getOpenFileNames(self, 'Select Audio File(s)', self._last_audio_dir, file_filter)
        if files:
            import os
            self._last_audio_dir = os.path.dirname(files[0])
            
            # FILTER: Separate OGG files from other audio formats
            ogg_files = [f for f in files if f.lower().endswith('.ogg')]
            non_ogg_files = [f for f in files if not f.lower().endswith('.ogg')]
            
            # If user selected OGG files, show explanation pop-up with copy option
            if ogg_files:
                # Get the actual mod folder path
                mod_name = self.modname_input.text().strip()
                if mod_name:
                    from pathlib import Path
                    import shutil
                    starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
                    staging_dir = starsound_dir / 'staging'
                    safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                    mod_music_path = staging_dir / safe_mod_name / 'music'
                    
                    ogg_message = (
                        'OGG files are already in the correct format for Starbound!\n\n'
                        '✓ Your mod\'s music folder is ready:\n'
                        f'  📁 {mod_music_path}\n\n'
                        f'🎵 You selected {len(ogg_files)} OGG file(s):\n'
                        f'  {", ".join([os.path.basename(f) for f in ogg_files[:3]])}{"..." if len(ogg_files) > 3 else ""}\n\n'
                        '❌ DO NOT use this converter for OGG files.They\'re already in the correct format!\n'
                        '💡 Only select MP3, WAV, FLAC, or other formats that need conversion.'
                    )
                    
                    # Show confirmation dialog with Copy option
                    reply = QMessageBox.question(
                        self,
                        '📋 Copy OGG Files to Mod Folder?',
                        ogg_message + '\n\nWould you like me to copy these OGG files to your mod\'s music folder?',
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        # Copy OGG files to mod music folder
                        try:
                            mod_music_path.mkdir(parents=True, exist_ok=True)
                            copied_count = 0
                            failed_files = []
                            
                            for ogg_file in ogg_files:
                                try:
                                    dest_file = mod_music_path / os.path.basename(ogg_file)
                                    shutil.copy2(ogg_file, dest_file)
                                    copied_count += 1
                                    self.logger.log(f'Copied OGG file: {os.path.basename(ogg_file)} → {mod_music_path}')
                                except Exception as e:
                                    failed_files.append(os.path.basename(ogg_file))
                                    self.logger.error(f'Failed to copy {ogg_file}: {e}')
                            
                            # Show success/status message
                            if copied_count == len(ogg_files):
                                QMessageBox.information(
                                    self,
                                    '✅ Success!',
                                    f'✓ Copied {copied_count} OGG file(s) to your mod folder!\n\n'
                                    f'📁 Location: {mod_music_path}\n\n'
                                    'Your OGG files are now ready to be integrated into your mod! Proceed with Step 5 if you are done adding tracks, or continue to add more tracks using Step 3. Remember, OGG files do NOT need conversion, just copy them directly to your mod\'s music folder.'
                                )
                            else:
                                QMessageBox.warning(
                                    self,
                                    '⚠️ Partial Success',
                                    f'✓ Copied {copied_count}/{len(ogg_files)} OGG file(s)\n\n'
                                    f'❌ Failed: {", ".join(failed_files)}\n\n'
                                    'Check the log for details.'
                                )
                        except Exception as e:
                            QMessageBox.critical(
                                self,
                                '❌ Copy Failed',
                                f'Could not copy OGG files:\n{e}\n\n'
                                'Please copy them manually to the music folder.'
                            )
                            self.logger.error(f'OGG copy operation failed: {e}')
                else:
                    # No mod name - show simpler message
                    ogg_message = (
                        'OGG files are already in the correct format for Starbound!\n\n'
                        '✓ For OGG files, copy them directly to your mod\'s music folder.\n'
                        '  (First enter a mod name in Step 1 to copy automatically)\n\n'
                        f'🎵 You selected {len(ogg_files)} OGG file(s):\n'
                        f'  {", ".join([os.path.basename(f) for f in ogg_files[:3]])}{"..." if len(ogg_files) > 3 else ""}\n\n'
                        '❌ DO NOT use this converter for OGG files.\n'
                        '💡 Only select MP3, WAV, FLAC, or other formats that need conversion.'
                    )
                    
                    QMessageBox.information(
                        self,
                        '📋 OGG Files Cannot Be Selected Here',
                        ogg_message
                    )
            
            # Only process non-OGG files
            if not non_ogg_files:
                return  # No valid files selected
            
            # CHECK FOR DUPLICATE OGG FILES in mod folder
            mod_name = self.modname_input.text().strip()
            if mod_name:
                from pathlib import Path
                starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
                staging_dir = starsound_dir / 'staging'
                safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                mod_music_path = staging_dir / safe_mod_name / 'music'
                
                # Check for duplicates and filter based on user choice
                if mod_music_path.exists():
                    self.logger.log(f'[DUPLICATES] Checking {len(non_ogg_files)} file(s) for duplicates in {mod_music_path}')
                    non_ogg_files = self._check_for_duplicate_tracks(non_ogg_files, mod_music_path)
                else:
                    self.logger.log(f'[DUPLICATES] Mod music folder does not exist yet ({mod_music_path}) - no duplicates possible')
                
                if not non_ogg_files:
                    self.logger.log('[SELECT_AUDIO] No files to add after duplicate check')
                    # Update UI display even if no new files added
                    if hasattr(self, 'selected_audio_files') and self.selected_audio_files:
                        filenames = [os.path.basename(f) for f in self.selected_audio_files]
                        bullet_lines = ['<span style="font-size:13px">Selected:</span>']
                        from utils.audio_utils import get_audio_duration
                        for file_path, basename in zip(self.selected_audio_files, filenames):
                            duration_minutes = get_audio_duration(file_path)
                            if duration_minutes and duration_minutes > 30:
                                self.files_needing_split[file_path] = duration_minutes
                                display_label = f'&bull; {basename} <span style="color: #ffcc00;">⚠️ {duration_minutes:.1f} min</span>'
                            else:
                                display_label = f'&bull; {basename}'
                            bullet_lines.append(display_label)
                        self.selected_files_label.setText('<br>'.join(bullet_lines))
                    else:
                        self.selected_files_label.setText('')
                    return
            
            # CUMULATIVE SELECTION: Add new files to existing selection (avoid duplicates with previously selected files)
            if not hasattr(self, 'selected_audio_files'):
                self.selected_audio_files = []
            
            # Convert to set for deduplication, then back to list
            existing_paths = set(self.selected_audio_files)
            new_files = [f for f in non_ogg_files if f not in existing_paths]
            
            if new_files:
                self.selected_audio_files.extend(new_files)
                self.logger.log(f'[SELECT_AUDIO] Added {len(new_files)} new file(s). Total: {len(self.selected_audio_files)}')
            else:
                self.logger.log(f'[SELECT_AUDIO] All {len(non_ogg_files)} selected file(s) already in list (duplicates skipped)')
            
            # Show only filenames, not full paths
            filenames = [os.path.basename(f) for f in self.selected_audio_files]
            if filenames:
                # Format as a bulleted list for readability
                bullet_lines = ['<span style="font-size:13px">Selected:</span>']
                
                # Check each file for duration to detect files needing splitting
                self.files_needing_split.clear()
                self.split_decisions.clear()
                
                from utils.audio_utils import get_audio_duration
                for file_path, basename in zip(self.selected_audio_files, filenames):
                    duration_minutes = get_audio_duration(file_path)
                    
                    # Build display label with split warning if needed
                    if duration_minutes and duration_minutes > 30:
                        self.files_needing_split[file_path] = duration_minutes
                        display_label = f'&bull; {basename} <span style="color: #ffcc00;">⚠️ {duration_minutes:.1f} min</span>'
                    else:
                        display_label = f'&bull; {basename}'
                    
                    bullet_lines.append(display_label)
                
                self.selected_files_label.setText('<br>'.join(bullet_lines))
            else:
                self.selected_files_label.setText('')
            
            # Back up original files BEFORE conversion (don't copy to /music/ yet)
            mod_name = self.modname_input.text().strip()
            backed_up = False
            if mod_name:
                from pathlib import Path
                import shutil
                starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
                staging_dir = starsound_dir / 'staging'
                safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                backup_root = self._get_backup_path(safe_mod_name)
                originals_folder = backup_root / 'originals'
                originals_folder.mkdir(parents=True, exist_ok=True)
                for f in self.selected_audio_files:
                    try:
                        # Back up original file to originals folder (pre-conversion backup)
                        basename = os.path.basename(f)
                        backup_dest = originals_folder / basename
                        if not backup_dest.exists():
                            shutil.copy2(f, backup_dest)
                            self.logger.log(f'Backed up original file to originals folder: {basename}')
                        backed_up = True
                    except Exception as e:
                        self.logger.error(f'Failed to back up file: {f} ({e})')
            
            # Show status
            if self.files_needing_split:
                split_count = len(self.files_needing_split)
                self.audio_status_label.setText(f'⚠️ {split_count} file(s) need splitting. Click "Convert to OGG" to continue.')
            elif backed_up:
                self.audio_status_label.setText('Files backed up. Click "Convert to OGG" to process them.')
            else:
                self.audio_status_label.setText('Selected! Click "Convert to OGG" to process your files.')
            
            # Check audio quality in background (don't block UI)
            def check_quality_async():
                from utils.audio_utils import check_audio_quality
                for file_path in files:
                    try:
                        has_issues, warnings = check_audio_quality(file_path)
                        if warnings:
                            for warning in warnings:
                                self.logger.log(f"Audio Quality: {warning}")
                    except Exception as e:
                        self.logger.log(f"Audio quality check error: {e}")
            
            import threading
            quality_thread = threading.Thread(target=check_quality_async, daemon=True)
            quality_thread.start()
            
            self.logger.update_metadata(last_action='Audio files selected')
            if self.files_needing_split:
                self.logger.log(f'User selected {len(files)} audio files. {len(self.files_needing_split)} require splitting.')
            else:
                self.logger.log(f'User selected {len(files)} audio files.')
            self._auto_save_mod_state('audio files selected')
        else:
            self.selected_audio_files = []
            self.selected_files_label.setText('')
            self.files_needing_split.clear()
            self.split_decisions.clear()
            self.logger.log('User cancelled audio file browse dialog')

    def validate_audio(self):
        self.logger.log('validate_audio() called')
        files = getattr(self, 'selected_audio_files', None)
        if not files:
            QMessageBox.warning(self, 'Input Error', 'Please select an audio file.')
            self.logger.warn('Validate Audio: No file selected.')
            return
        valid_count = 0
        for file_path in files:
            self.logger.log(f'User started audio validation for: {file_path}')
            if not validate_file_exists(file_path):
                self.audio_status_label.setText(f'File does not exist: {file_path}')
                self.logger.warn(f'Validate Audio: File does not exist: {file_path}')
                continue
            valid, duration, msg = validate_file_duration(file_path)
            if not valid:
                self.audio_status_label.setText(f'Duration error: {msg} ({file_path})')
                self.logger.warn(f'Validate Audio: Duration error: {msg} ({file_path})')
                continue
            valid, msg = validate_file_format(file_path)
            if not valid:
                self.audio_status_label.setText(f'Format error: {msg} ({file_path})')
                self.logger.warn(f'Validate Audio: Format error: {msg} ({file_path})')
                continue
            valid_count += 1
        if valid_count == len(files):
            self.audio_status_label.setText('All audio files are valid!')
            self.logger.log(f'All audio files validated: {files}')
        elif valid_count > 0:
            self.audio_status_label.setText(f'{valid_count}/{len(files)} audio files are valid.')
        else:
            self.audio_status_label.setText('No valid audio files.')

    def process_split_confirmations(self) -> bool:
        """
        Process split confirmation dialog for all files >30 minutes.
        Shows ONE consolidated confirmation for all long files.
        
        Returns:
            bool: True if user chose to continue with conversion,
                  False if user cancelled/went back
        """
        if not self.files_needing_split:
            # No files need splitting
            return True
        
        from dialogs.split_confirmation_dialog import SplitConfirmationDialog
        from dialogs.denial_confirmation_dialog import DenialConfirmationDialog
        import os
        
        # Collect ALL files that need splitting
        filenames = [os.path.basename(file_path) for file_path in self.files_needing_split.keys()]
        durations = list(self.files_needing_split.values())
        
        # Show ONE confirmation dialog for all files
        split_dialog = SplitConfirmationDialog(filenames, durations, self)
        split_dialog.exec_()
        choice = split_dialog.get_choice()
        
        if choice == "ACCEPT":
            # User wants to split all files
            for file_path in self.files_needing_split.keys():
                self.split_decisions[file_path] = "ACCEPT"
            self.logger.log(f'User accepted splitting for {len(self.files_needing_split)} file(s)')
            return True
        else:  # DENY
            # User wants to skip splitting - show denial confirmation
            # Use first file name for denial dialog (it's for all files)
            denial_dialog = DenialConfirmationDialog(filenames[0], durations[0], self)
            denial_dialog.exec_()
            denial_choice = denial_dialog.get_choice()
            
            if denial_choice == "SPLIT_IT":
                # User changed mind, go back and accept splitting
                self.logger.log('User reconsidered, accepting splitting for all files')
                for file_path in self.files_needing_split.keys():
                    self.split_decisions[file_path] = "ACCEPT"
                return True
            else:  # "ACCEPT_RISK"
                # User refuses to split - mark for no split, proceed at user's risk
                self.logger.log('User refused to split long files, proceeding at risk')
                for file_path in self.files_needing_split.keys():
                    self.split_decisions[file_path] = "DENY"
                return True

    def perform_file_splitting(self, segment_length: int | dict = 25) -> bool:
        """
        Perform actual FFmpeg splitting for files user accepted.
        Called after split confirmations are complete.
        
        Workflow:
        1. Create WAV segments (lossless, no quality loss during split)
        2. Replace original file in list with all its WAV segments
        3. Show preview of splits created
        4. NEXT STEP: Per-segment audio config available via per-track dialog
           (compression, EQ, normalization, etc.) customized per segment
        5. FINAL STEP: Processed WAV segments convert to OGG
        
        SEGMENT TRACKING:
        - Stores mapping of segment → original file in self.segment_origins
        - Per-track dialog uses this to group segments by parent track
        - Allows per-segment customization of audio processing
        
        Args:
            segment_length: Either:
                - int: Single segment length in minutes (applied to all files)
                - dict: Per-file segment lengths {file_path: segment_length_minutes}
        
        Returns:
            bool: True if all splits successful or no splits needed,
                  False if any split failed
        
        NOTE: Creates and manages dialogs on GUI thread only. Uses worker thread
        for actual FFmpeg processing to prevent UI freeze.
        """
        if not self.split_decisions:
            # No splitting needed
            return True
        
        # Prepare file list and segment lengths (stored on main window for worker to access)
        if isinstance(segment_length, int):
            self.per_file_segment_lengths = {
                file_path: segment_length 
                for file_path in self.split_decisions.keys()
            }
        else:
            self.per_file_segment_lengths = segment_length
        
        # Track files to split
        files_to_split = [fp for fp, d in self.split_decisions.items() if d == "ACCEPT"]
        if not files_to_split:
            return True
        
        # CREATE PROGRESS DIALOG ON GUI THREAD (not worker thread)
        self.progress_dialog = SplitProgressDialog(self)
        self.progress_dialog.setWindowModality(Qt.ApplicationModal)
        self.progress_dialog.start_animation()
        self.progress_dialog.show()
        
        # CREATE AND START WORKER THREAD
        self.split_worker = SplitAudioWorker(self, segment_length, files_to_split)
        self.split_worker.progress_update.connect(self._on_split_progress_update)
        self.split_worker.finished.connect(self._on_split_finished)
        self.split_worker.error.connect(self._on_split_error)
        self.split_worker.start()
        
        return True
    
    def _on_split_progress_update(self, filename: str, current_num: int, total_num: int):
        """Update progress dialog from worker thread signal."""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.update_current_file(filename, current_num, total_num)
        self.audio_status_label.setText(f'Splitting: {filename}...')
    
    def _on_split_finished(self, results: dict):
        """Worker thread finished successfully. Update UI and continue conversion if needed."""
        # Close progress dialog
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.stop_animation()
            self.progress_dialog.close()
        
        # Extract results from worker
        files_to_remove = results.get('files_to_remove', [])
        files_to_add = results.get('files_to_add', [])
        split_metadata = results.get('split_metadata', {})
        success = results.get('success', False)
        
        if not success:
            error_msg = results.get('error', 'Unknown split error')
            QMessageBox.critical(self, 'Split Failed', f'Could not split audio:\n\n{error_msg}')
            self.logger.error(f'File splitting failed: {error_msg}')
            self.converter_state = None
            return
        
        # Update selected files list
        for original in files_to_remove:
            if original in self.selected_audio_files:
                self.selected_audio_files.remove(original)
        
        self.selected_audio_files.extend(files_to_add)
        
        if files_to_remove:
            self.logger.log(f'File list updated: {len(files_to_remove)} files split into {len(files_to_add)} segments')
            self.logger.log(f'[SEGMENT_TRACK] Segment origin map initialized with {len(self.segment_origins)} segment(s)')
            
            # Show preview dialog if any splits were created
            if split_metadata:
                self._show_split_preview(split_metadata, files_to_add)
        
        # === CONTINUE CONVERTER WORKFLOW IF PENDING ===
        # If convert_audio() started a split, continue with per-track config now that split is complete
        if hasattr(self, 'converter_state') and self.converter_state:
            self.logger.log('[CONVERT_FLOW] Split complete! Continuing with per-track configuration...')
            self._continue_converter_after_split()
            self.converter_state = None
    
    def _continue_converter_after_split(self):
        """Continue audio conversion after splitting completes (called from _on_split_finished)."""
        if not hasattr(self, 'converter_state') or not self.converter_state:
            return
        
        state = self.converter_state
        files = state['files']
        mod_name = state['mod_name']
        bitrate_value = state['bitrate_value']
        
        self.logger.log(f'[CONVERT_FLOW] Continuing: Per-track config for {len(files)} file(s)')
        
        # Show per-track audio config for segments grouped by original file
        # Use sensible defaults matching audio_processing_dialog (trim/silence_trim will be auto-disabled for split audio)
        audio_processing_options = {
            'trim': True,
            'silence_trim': True,
            'sonic_scrubber': True,
            'compression': True,
            'compression_preset': 'Moderate (balanced)',
            'soft_clip': True,
            'eq': True,
            'eq_preset': 'Warm (bass-heavy)',
            'normalize': True,
            'fade': True,  # CRITICAL: Must be enabled for proper audio processing
            'fade_in_duration': '0hr0m0.5s',
            'fade_out_duration': '0hr0m5s',
            'de_esser': False,
            'stereo_to_mono': False,
        }
        
        segment_origins = getattr(self, 'segment_origins', {})
        if segment_origins:
            self.logger.log(f'[CONVERT_FLOW] Segment grouping enabled: {len(segment_origins)} segment(s)')
        
        per_track_dialog = PerTrackAudioConfigDialog(
            files, audio_processing_options, self, segment_origins=segment_origins
        )
        per_track_result = per_track_dialog.exec_()
        if per_track_result == 0:
            self.logger.log('[CONVERT_FLOW] User cancelled per-track config - aborting conversion')
            return
        
        per_track_settings = per_track_dialog.get_per_track_settings()
        self.logger.log(f'[CONVERT_FLOW] Per-track settings received for {len(per_track_settings)} files')
        
        # Extract bitrate from per-track dialog
        bitrate_text = per_track_dialog.get_bitrate()
        if bitrate_text:
            bitrate_value = bitrate_text.split()[0] + 'k'
        self.logger.log(f'[CONVERT_FLOW] Bitrate from per-track dialog: {bitrate_value}')
        
        # Build filter chains with actual file durations
        from utils.audio_utils import build_audio_filter_chain, get_audio_duration
        per_track_filters = {}
        for file_path, track_settings in per_track_settings.items():
            converted_settings = self._convert_per_track_to_audio_options(track_settings)
            # Get actual file duration for proper fade-out calculation
            file_duration_minutes = get_audio_duration(file_path)
            audio_filter = build_audio_filter_chain(converted_settings, file_duration_minutes=file_duration_minutes)
            per_track_filters[file_path] = audio_filter
        
        self.logger.log(f'[CONVERT_FLOW] Per-track filters built: {len(per_track_filters)} filter(s)')
        
        # Now run the actual conversion with the per-track filters
        self._run_audio_conversion(files, mod_name, bitrate_value, per_track_filters)
    
    def _on_split_error(self, error_msg: str):
        """Worker thread encountered error."""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.stop_animation()
            self.progress_dialog.close()
        
        QMessageBox.critical(self, 'Audio Splitting Error', error_msg)
        self.logger.error(error_msg)
    
    def _show_split_preview(self, split_metadata: dict, files_to_add: list):
        """Show split preview dialog on GUI thread."""
        preview_dialog = SplitPreviewDialog(
            parent=self,
            split_metadata=split_metadata
        )
        preview_dialog.exec_()
        choice = preview_dialog.get_choice()
        
        if choice != "PROCEED":
            self.logger.log('User cancelled after split preview - cleaning up temporary WAV segments')
            # Cleanup WAV files since conversion won't happen
            import shutil
            temp_dirs_to_remove = set()
            
            for wav_file in files_to_add:
                if wav_file.endswith('.wav') and os.path.isfile(wav_file):
                    try:
                        # Track temp directory for cleanup
                        wav_dir = os.path.dirname(wav_file)
                        temp_dir = os.path.join(wav_dir, '.starsound_splits_temp')
                        if os.path.isdir(temp_dir):
                            temp_dirs_to_remove.add(temp_dir)
                        
                        # Remove the WAV file
                        os.remove(wav_file)
                        self.logger.log(f'[CLEANUP] Removed cancelled segment: {os.path.basename(wav_file)}')
                    except Exception as e:
                        self.logger.warn(f'[CLEANUP] Could not remove WAV file {os.path.basename(wav_file)}: {e}')
            
            # Cleanup temp directories
            for temp_dir in temp_dirs_to_remove:
                try:
                    if os.path.isdir(temp_dir):
                        shutil.rmtree(temp_dir)
                        self.logger.log(f'[CLEANUP] Removed temp directory: {os.path.basename(temp_dir)}')
                except Exception as e:
                    self.logger.warn(f'[CLEANUP] Could not remove temp directory {temp_dir}: {e}')

    def _perform_file_splitting_worker(
        self,
        segment_length: int | dict = 25,
        files_to_split: list = None,
        progress_callback=None
    ) -> dict:
        """
        Perform actual FFmpeg splitting for files (WORKER THREAD ONLY).
        This method runs on the worker thread - NO Qt objects created here.
        All progress updates use progress_callback to emit signals to GUI thread.
        
        Args:
            segment_length: Either int (single value) or dict (per-file values)
            files_to_split: List of file paths to split
            progress_callback: Function(filename, current_num, total_num) to report progress
        
        Returns:
            dict with keys:
                - success: bool (True if all splits successful)
                - files_to_remove: list of original file paths
                - files_to_add: list of split segment paths
                - split_metadata: dict of metadata for preview
                - segment_origins: dict mapping segments to original files
                - error: str (error message if success=False)
        """
        from utils.audio_utils import split_audio_file, get_audio_duration
        import os
        
        # Initialize segment origin tracking
        if not hasattr(self, 'segment_origins'):
            self.segment_origins = {}
        
        # Track results to return to GUI thread
        files_to_remove = []
        files_to_add = []
        split_metadata = {}
        
        # Prepare segment lengths
        if isinstance(segment_length, int):
            per_file_segment_lengths = {
                file_path: segment_length
                for file_path in (files_to_split or [])
            }
        else:
            per_file_segment_lengths = segment_length or {}
        
        # Process each file that needs splitting
        if not files_to_split:
            return {'success': True, 'files_to_remove': [], 'files_to_add': [],
                    'split_metadata': {}, 'segment_origins': self.segment_origins}
        
        total_files = len(files_to_split)
        file_count = 0
        
        for file_path in files_to_split:
            filename = os.path.basename(file_path)
            file_count += 1
            
            # Report progress via callback (emits signal to GUI thread)
            if progress_callback:
                progress_callback(filename, file_count, total_files)
            
            # Get segment length for this file
            segment_length_minutes = per_file_segment_lengths.get(file_path, 25)
            self.logger.log(
                f'Starting FFmpeg split: {filename} ({segment_length_minutes} min segments)'
            )
            
            # Perform the split (this is the actual FFmpeg work)
            result = split_audio_file(
                file_path,
                segment_length_minutes=segment_length_minutes,
                logger=self.logger
            )
            
            if result['success']:
                self.logger.log(
                    f'Split successful: {result["segment_count"]} segments created'
                )
                files_to_remove.append(file_path)
                files_to_add.extend(result['split_files'])
                
                # SEGMENT TRACKING: Map each segment back to original
                for segment_path in result['split_files']:
                    self.segment_origins[segment_path] = file_path
                    segment_name = os.path.basename(segment_path)
                    self.logger.log(
                        f'[SEGMENT_TRACK] {segment_name} origin: {filename}'
                    )
                
                # Store metadata for preview
                original_duration = get_audio_duration(file_path)
                split_metadata[filename] = {
                    'original_duration': original_duration,
                    'segments': result['split_files'],
                    'segment_durations': result['segment_durations']
                }
            else:
                # Split failed - return error
                error_msg = f"Split failed for {filename}: {result['message']}"
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'message': result['message'],
                    'files_to_remove': [],
                    'files_to_add': [],
                    'split_metadata': {}
                }
        
        # All splits completed successfully
        return {
            'success': True,
            'files_to_remove': files_to_remove,
            'files_to_add': files_to_add,
            'split_metadata': split_metadata,
            'segment_origins': self.segment_origins
        }

    def convert_audio(self):
        import os
        self.logger.log('convert_audio() called')
        
        files = getattr(self, 'selected_audio_files', None)
        if not files:
            QMessageBox.warning(self, 'Input Error', 'Please select an audio file.')
            self.logger.warn('Convert Audio: No file selected.')
            return
        mod_name = self.modname_input.text().strip()
        if not mod_name:
            QMessageBox.warning(self, 'Input Error', 'Please enter a mod name in Step 1.')
            self.logger.warn('Convert Audio: No mod name selected.')
            return
        
        # ===== BRANCHING WORKFLOW =====
        # Determine appropriate dialog flow based on file count and splitting needs:
        # - Single regular file: Show audio processing dialog
        # - Multiple regular files: Skip first dialog, go to per-track dialog
        # - Long files (splitting): Show split config, then per-track dialog
        self.logger.log(f'[CONVERT_FLOW] BRANCHING: {len(files)} file(s), splitting needed: {bool(self.files_needing_split)}')
        
        bitrate_value = '192k'  # Default bitrate
        per_file_segment_lengths = {}
        split_config_shown = False
        
        if self.files_needing_split:
            # SPLIT WORKFLOW: Show confirmation dialogs first, then config
            self.logger.log(f'[CONVERT_FLOW] SPLIT MODE: {len(self.files_needing_split)} file(s) need splitting')
            self.logger.log('[CONVERT_FLOW] SKIPPING first audio processing dialog (will configure per-track after split)')
            
            # STEP 1: Show split confirmation dialogs for each file
            self.logger.log('[CONVERT_FLOW] STEP 1: Showing split confirmation dialogs')
            proceed = self.process_split_confirmations()
            if not proceed:
                self.logger.log('[CONVERT_FLOW] User cancelled during split confirmation workflow')
                return
            
            # STEP 2: Show split configuration dialog (per-file segment lengths)
            self.logger.log('[CONVERT_FLOW] STEP 2: Showing per-file split configuration dialog')
            from dialogs.per_file_split_config_dialog import PerFileSplitConfigDialog
            split_config_dialog = PerFileSplitConfigDialog(self.files_needing_split, self)
            split_config_dialog.exec_()
            
            choice = split_config_dialog.get_choice()
            if choice == "CANCEL":
                self.logger.log('[CONVERT_FLOW] User cancelled split configuration')
                return
            
            per_file_segment_lengths = split_config_dialog.get_per_file_segment_lengths()
            split_config_shown = True
            self.logger.log(f'[CONVERT_FLOW] User configured individual segment lengths for {len(per_file_segment_lengths)} file(s)')
        elif len(files) > 1:
            # MULTIPLE REGULAR FILES: Skip first dialog, go straight to per-track config
            self.logger.log(f'[CONVERT_FLOW] MULTIPLE FILES MODE: {len(files)} regular files selected')
            self.logger.log('[CONVERT_FLOW] SKIPPING first audio processing dialog (will configure per-track)')
            # Bitrate will be extracted from per-track dialog later
        else:
            # SINGLE FILE WORKFLOW: Show audio processing dialog first
            self.logger.log('[CONVERT_FLOW] SINGLE FILE MODE: Showing audio processing dialog')
            self.logger.log('[CONVERT_FLOW] STEP 1: Showing audio processing dialog')
            dialog_result = self.show_audio_config_dialog()
            if dialog_result == 0:  # QDialog.Rejected (Cancel clicked)
                self.logger.log('[CONVERT_FLOW] User cancelled audio processing - aborting conversion')
                return
            self.logger.log('[CONVERT_FLOW] STEP 1 COMPLETE: Audio config dialog has closed')
            
            # Extract bitrate from audio processing options
            audio_options = self.audio_dialog.get_audio_processing_options()
            bitrate_text = audio_options.get('bitrate', '192 kbps (default)')
            if bitrate_text:
                bitrate_value = bitrate_text.split()[0] + 'k'
        
        self.logger.log(f'Audio processing bitrate selected: {bitrate_value}')
        
        # ===== STEP 3: PERFORM SPLITTING =====
        # Perform actual splitting with per-file segment lengths
        if self.files_needing_split:
            self.logger.log('[CONVERT_FLOW] STEP 3: Performing file splitting with per-file configuration')
            # Store converter state so we can continue AFTER split completes (split runs in worker thread)
            self.converter_state = {
                'files': files,
                'mod_name': mod_name,
                'bitrate_value': bitrate_value,
                'files_needing_split': True
            }
            proceed = self.perform_file_splitting(per_file_segment_lengths)
            if not proceed:
                self.logger.log('File splitting failed, aborting conversion')
                self.converter_state = None
                return
            # Code stops here; conversion continues in _on_split_finished() when worker finishes
            self.logger.log('[CONVERT_FLOW] Split worker started in background. Waiting for completion...')
            return
        else:
            self.logger.log('[CONVERT_FLOW] No files need splitting, proceeding to conversion')
        
        # ===== STEP 2.5: SHOW PER-TRACK AUDIO CONFIG (IF MULTIPLE FILES) =====
        # Allow users to customize audio processing for each track individually
        # If files were split, shows segments grouped by parent file
        self.logger.log('[CONVERT_FLOW] STEP 2.5: Checking if per-track config needed')
        per_track_filters = {}  # Will map file_path -> audio_filter
        
        if len(files) > 1:
            self.logger.log(f'[CONVERT_FLOW] Multiple files ({len(files)}) detected - showing per-track config')
            
            # Use sensible defaults for multiple files mode (first audio dialog was skipped)
            # Defaults match audio_processing_dialog values
            audio_processing_options = {
                'trim': True,
                'silence_trim': True,
                'sonic_scrubber': True,
                'compression': True,
                'compression_preset': 'Moderate (balanced)',
                'soft_clip': True,
                'eq': True,
                'eq_preset': 'Warm (bass-heavy)',
                'normalize': True,
                'fade': True,  # CRITICAL: Must be enabled for proper audio processing
                'fade_in_duration': '0hr0m0.5s',
                'fade_out_duration': '0hr0m5s',
                'de_esser': False,
                'stereo_to_mono': False,
            }
            self.logger.log('[CONVERT_FLOW] Multiple files mode - using full defaults for per-track dialog (including fade)')
            
            # Pass segment_origins if they exist (enables segment grouping in dialog)
            segment_origins = getattr(self, 'segment_origins', {})
            if segment_origins:
                self.logger.log(f'[CONVERT_FLOW] Segment grouping enabled: {len(segment_origins)} segment(s)')
            
            # Show per-track audio configuration dialog
            per_track_dialog = PerTrackAudioConfigDialog(
                files, audio_processing_options, self, segment_origins=segment_origins
            )
            per_track_result = per_track_dialog.exec_()
            if per_track_result == 0:  # QDialog.Rejected (Cancel clicked)
                self.logger.log('[CONVERT_FLOW] User cancelled per-track audio configuration - aborting conversion')
                return
            
            per_track_settings = per_track_dialog.get_per_track_settings()
            self.logger.log(f'[CONVERT_FLOW] Per-track settings received for {len(per_track_settings)} files')
            
            # Extract bitrate from per-track dialog if split workflow
            if self.files_needing_split:
                bitrate_text = per_track_dialog.get_bitrate()
                if bitrate_text:
                    bitrate_value = bitrate_text.split()[0] + 'k'
                self.logger.log(f'[CONVERT_FLOW] Bitrate selected from per-track dialog: {bitrate_value}')
            
            # Build individual filter chain for each file with actual file durations
            from utils.audio_utils import build_audio_filter_chain, get_audio_duration
            for file_path, track_settings in per_track_settings.items():
                # Convert from per-track format (with _enabled suffix) to audio_processing_dialog format
                converted_settings = self._convert_per_track_to_audio_options(track_settings)
                
                # Get actual file duration for proper fade-out calculation
                file_duration_minutes = get_audio_duration(file_path)
                audio_filter = build_audio_filter_chain(converted_settings, file_duration_minutes=file_duration_minutes)
                per_track_filters[file_path] = audio_filter
            
            self.logger.log(f'[CONVERT_FLOW] Per-track filters built: {len(per_track_filters)} filter(s) ready')
        else:
            # Single file or no files - use uniform settings
            self.logger.log('[CONVERT_FLOW] Single file or no files - using uniform audio processing')
            audio_processing_options = self.audio_dialog.get_audio_processing_options()
            from utils.audio_utils import build_audio_filter_chain, get_audio_duration
            for file_path in files:
                # Get actual file duration for proper fade-out calculation
                file_duration_minutes = get_audio_duration(file_path)
                audio_filter = build_audio_filter_chain(audio_processing_options, file_duration_minutes=file_duration_minutes)
                per_track_filters[file_path] = audio_filter
            self.logger.log(f'[CONVERT_FLOW] Uniform filter chain applied to all {len(files)} file(s) with actual durations')
        
        # ===== PERFORM CONVERSION =====
        self._run_audio_conversion(files, mod_name, bitrate_value, per_track_filters)
    
    def _run_audio_conversion(self, files: list, mod_name: str, bitrate_value: str, per_track_filters: dict):
        """
        Run audio conversion in parallel using ThreadPoolExecutor.
        Converts 2-3 files simultaneously for ~2-3x speedup.
        Used by both normal convert_audio() and post-split conversion workflow.
        """
        import os
        import threading
        from pathlib import Path
        from utils.atomicwriter import backup_and_convert_audio, create_mod_folder_structure
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Setup conversion environment
        starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
        staging_dir = starsound_dir / 'staging'
        safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        mod_path = staging_dir / safe_mod_name
        backup_root = self._get_backup_path(mod_name)  # Get root backup path
        
        # Clean up any old backups folder in staging (now centralized in root)
        try:
            old_staging_backups = mod_path / 'backups'
            if old_staging_backups.exists():
                import shutil
                shutil.rmtree(old_staging_backups)
                self.logger.log(f'[CLEANUP] Removed old staging backups: {old_staging_backups}')
        except Exception as e:
            self.logger.warn(f'[CLEANUP] Could not remove old staging backups: {e}')
        
        self.logger.update_metadata(mod_path=str(mod_path))
        create_mod_folder_structure(staging_dir, safe_mod_name)
        
        self.logger.log(f'[CONVERSION_START] About to convert {len(files)} file(s) in parallel:')
        for idx, fp in enumerate(files):
            self.logger.log(f'  [{idx+1}] {os.path.basename(fp)}')
        
        def convert_single_file(file_path):
            """
            Convert a single file to OGG. Returns tuple: (success, msg, ogg_path, is_wav).
            This runs in the thread pool (one file per thread).
            """
            def ffmpeg_log_callback(text):
                self.ffmpeg_log_signal.emit(text)
            
            self.logger.log(f'[PARALLEL] Starting conversion: {os.path.basename(file_path)}')
            
            # Get audio filter for this file
            audio_filter = per_track_filters.get(file_path, '')
            if not audio_filter:
                self.logger.warn(f'[MISMATCH] No filter for {os.path.basename(file_path)}')
            
            # Perform conversion
            success, msg, ogg_path = backup_and_convert_audio(
                file_path, str(mod_path), bitrate=bitrate_value,
                audio_filter=audio_filter, ffmpeg_log_callback=ffmpeg_log_callback,
                backup_path=str(backup_root)
            )
            
            is_wav = file_path.endswith('.wav')
            self.logger.log(f'[PARALLEL] Completed: {os.path.basename(file_path)} - {"✓ Success" if success else "✗ Failed"}')
            
            return (success, msg, ogg_path, is_wav, file_path)
        
        def run_parallel_conversion():
            converted_count = 0
            failed_count = 0
            error_messages = []
            wav_files_to_cleanup = []
            
            self.ffmpeg_log_signal.emit('CLEAR')
            
            # Use ThreadPoolExecutor for parallel conversion (2-3 files at once)
            max_workers = min(3, len(files))  # Limit to 3 parallel conversions, or fewer if less files
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all file conversions to the thread pool
                futures = {
                    executor.submit(convert_single_file, file_path): file_path
                    for file_path in files
                }
                
                self.logger.log(f'[PARALLEL] Started {max_workers} parallel conversion worker(s)')
                
                # Process completions as they finish (not in order)
                for future in as_completed(futures):
                    try:
                        success, msg, ogg_path, is_wav, file_path = future.result()
                        
                        # Track WAV files for cleanup
                        if is_wav:
                            wav_files_to_cleanup.append(file_path)
                        
                        if success:
                            converted_count += 1
                            original_filename = os.path.basename(file_path)
                            ogg_filename = os.path.basename(ogg_path) if ogg_path else original_filename
                            
                            # Show both original and converted if they differ significantly
                            # (handles Unicode/special character files that get sanitized)
                            if ogg_filename != original_filename.replace('.mp3', '.ogg').replace('.wav', '.ogg'):
                                display_text = f'{original_filename} → {ogg_filename}'
                            else:
                                display_text = ogg_filename
                            
                            self.completed_files_signal.emit(display_text)
                        else:
                            failed_count += 1
                            file_display = os.path.basename(file_path)
                            error_msg = f'{file_display}: {msg}' if msg else f'{file_display}: Conversion failed'
                            error_messages.append(error_msg)
                            self.logger.error(error_msg)
                    
                    except Exception as e:
                        failed_count += 1
                        self.logger.error(f'[PARALLEL] Conversion thread error: {e}')
                        error_messages.append(f'Thread error: {str(e)[:50]}')
            
            self.logger.log(f'[PARALLEL] All conversions complete: {converted_count} success, {failed_count} failed')
            
            # Cleanup temporary WAV segments
            if wav_files_to_cleanup:
                import shutil
                cleanup_count = 0
                temp_dirs_to_remove = set()
                
                for wav_file in wav_files_to_cleanup:
                    try:
                        wav_dir = os.path.dirname(wav_file)
                        temp_dir = os.path.join(wav_dir, '.starsound_splits_temp')
                        if os.path.isdir(temp_dir):
                            temp_dirs_to_remove.add(temp_dir)
                        
                        if os.path.isfile(wav_file):
                            os.remove(wav_file)
                            cleanup_count += 1
                            self.logger.log(f'[CLEANUP] Removed temporary WAV: {os.path.basename(wav_file)}')
                    except Exception as e:
                        self.logger.warn(f'[CLEANUP] Could not remove WAV: {os.path.basename(wav_file)}: {e}')
                
                for temp_dir in temp_dirs_to_remove:
                    try:
                        if os.path.isdir(temp_dir):
                            shutil.rmtree(temp_dir)
                            self.logger.log(f'[CLEANUP] Removed temp directory')
                    except Exception as e:
                        self.logger.warn(f'[CLEANUP] Could not remove temp dir: {e}')
            
            # Summary
            if converted_count and failed_count:
                summary = f'{converted_count} file(s) converted, {failed_count} failed.'
                if error_messages:
                    summary += '\n\nErrors:\n' + '\n'.join(error_messages[:5])
                    if len(error_messages) > 5:
                        summary += f'\n... and {len(error_messages) - 5} more error(s).'
            elif failed_count:
                summary = f'All conversions failed. ({failed_count})'
                if error_messages:
                    summary += '\n\nErrors:\n' + '\n'.join(error_messages[:5])
                    if len(error_messages) > 5:
                        summary += f'\n... and {len(error_messages) - 5} more error(s).'
            elif converted_count:
                summary = f'All files converted successfully! ({converted_count})'
            else:
                summary = 'No files converted.'
            
            self.audio_status_signal.emit(summary)
            if converted_count > 0:
                self._auto_save_mod_state('audio conversion')
        
        # Run parallel conversion in background thread
        threading.Thread(target=run_parallel_conversion, daemon=True).start()

    def _convert_per_track_to_audio_options(self, per_track_settings: dict) -> dict:
        """
        Convert per-track audio settings format back to audio_processing_dialog format.
        
        Per-track format uses _enabled suffixes (from PerTrackAudioConfigDialog):
            {'fade_enabled': True, 'fade_in_duration': '0.5', ...}
        
        Audio dialog format uses plain tool names:
            {'fade': True, 'fade_in_duration': '0.5', ...}
        
        Args:
            per_track_settings: Settings dict with _enabled suffixes
        
        Returns:
            dict: Settings dict without _enabled suffixes, ready for build_audio_filter_chain()
        """
        converted = {}
        
        # Tool names that use _enabled suffix in per-track format
        tool_keys = ['trim', 'silence_trim', 'sonic_scrubber', 'compression',
                     'soft_clip', 'eq', 'normalize', 'fade', 'de_esser', 'stereo_to_mono']
        
        for key, value in per_track_settings.items():
            # Convert {tool}_enabled back to plain {tool}
            if key.endswith('_enabled'):
                tool_name = key[:-8]  # Remove '_enabled' suffix
                if tool_name in tool_keys:
                    converted[tool_name] = value
            else:
                # Copy other keys as-is (parameters like 'fade_in_duration')
                converted[key] = value
        
        return converted

    def show_audio_config_dialog(self):
        """
        Show the audio processing configuration dialog (modal).
        
        Dialog allows the user to enable/disable audio tools and configure
        their parameters. Settings are stored and used during audio conversion.
        """
        self.logger.log('[AUDIO_CONFIG] Initializing audio processing dialog')
        
        if self.audio_dialog is None:
            self.logger.log('[AUDIO_CONFIG] Creating new AudioProcessingDialog instance')
            self.audio_dialog = AudioProcessingDialog(self)
        
        # Ensure dialog is on top and visible
        self.logger.log('[AUDIO_CONFIG] Showing audio config dialog (modal, blocking)')
        self.audio_dialog.raise_()
        self.audio_dialog.activateWindow()
        
        # Show the modal dialog - this BLOCKS until user closes it
        result = self.audio_dialog.exec_()
        self.logger.log(f'[AUDIO_CONFIG] Audio dialog closed with result: {result}')
        if result == 0:  # QDialog.Rejected (Cancel clicked)
            self.logger.log('[AUDIO_CONFIG] User cancelled audio processing dialog')
        else:
            self.logger.log('[AUDIO_CONFIG] User applied audio processing settings')
        return result

    def generate_patch_file(self):
        # Defensive: ensure audio_status_label always exists
        if not hasattr(self, 'audio_status_label'):
            self.audio_status_label = QLabel('')
        
        # CLEANUP & VALIDATION: Pre-generation setup
        try:
            mod_name = self.modname_input.text().strip() if hasattr(self, 'modname_input') else ''
            if mod_name:
                starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
                staging_dir = starsound_dir / 'staging'
                safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                
                # Validate and fix backups folder structure (located at root backups/)
                backup_root = self._get_backup_path(safe_mod_name)
                backups_originals = backup_root / 'originals'
                backups_converted = backup_root / 'converted'
                
                if backups_originals.exists():
                    for ogg_file in backups_originals.glob('*.ogg'):
                        try:
                            converted_dest = backups_converted / ogg_file.name
                            ogg_file.rename(converted_dest)
                            self.logger.log(f'[MIGRATE] Moved OGG from originals to converted: {ogg_file.name}')
                        except Exception as e:
                            self.logger.warn(f'[MIGRATE] Could not move OGG: {ogg_file.name} ({e})')
                    
                    for ogg_file in backups_originals.glob('*.ogg'):
                        try:
                            ogg_file.unlink()
                            self.logger.log(f'[CLEANUP] Removed leftover OGG from originals: {ogg_file.name}')
                        except Exception as e:
                            self.logger.warn(f'[CLEANUP] Could not remove OGG: {ogg_file.name} ({e})')
        except Exception as e:
            self.logger.warn(f'[VALIDATION] Pre-generation validation had issues: {e}')
        
        # Ask user for output format
        format_choice = self._show_format_selection_dialog()
        if not format_choice:
            return
        
        self.output_format = format_choice
        self.settings.set('last_output_format', format_choice)
        
        self.audio_status_label.setText('🔔 Generate Mod button clicked!')
        self.update_selected_tracks_label()
        self.logger.log('generate_patch_file() called - launching threaded worker')
        self.logger.log('User started patch generation')
        self.logger.update_metadata(last_action='Generate Patch Clicked')
        
        # Validate inputs before launching thread
        mod_name = self.modname_input.text().strip() if hasattr(self, 'modname_input') else ''
        if not mod_name:
            self.audio_status_label.setText('❌ Please enter a mod name in Step 1.')
            self.update_selected_tracks_label()
            QMessageBox.warning(self, 'Input Error', 'Please enter a mod name in Step 1.')
            self.logger.warn('Generate Patch: No mod name selected.')
            return
        
        biomes = getattr(self, 'selected_biomes', [])
        if not biomes:
            self.audio_status_label.setText('❌ Please select a biome.')
            self.update_selected_tracks_label()
            QMessageBox.warning(self, 'Input Error', 'Please select a biome.')
            self.logger.warn('Generate Patch: No biome selected.')
            return
        
        patch_mode = getattr(self, 'patch_mode', 'add')
        replace_selections = getattr(self, 'replace_selections', {})
        add_selections = getattr(self, 'add_selections', {})
        day_tracks = getattr(self, 'day_tracks', [])
        night_tracks = getattr(self, 'night_tracks', [])
        
        # Validate we have tracks
        has_tracks = bool(day_tracks or night_tracks or add_selections or replace_selections)
        if not has_tracks:
            self.audio_status_label.setText('❌ Please add at least one track.')
            self.update_selected_tracks_label()
            QMessageBox.warning(self, 'Input Error', 'Please add at least one track.')
            self.logger.warn('Generate Patch: No tracks selected.')
            return
        
        # Save mod state before starting
        try:
            mod_state = self._gather_current_mod_state()
            self.mod_save_manager.save_mod(mod_name, mod_state)
            self.logger.log('Saved mod config to mod_saves before generation')
        except Exception as e:
            self.logger.warn(f'Failed to save mod config: {e}')
        
        # Launch worker thread with progress dialog
        self._launch_patch_generation_worker(mod_name, format_choice)
    
    def _launch_patch_generation_worker(self, mod_name, format_choice):
        """Launch patch generation in a background thread with progress dialog"""
        # Create and launch worker
        self.patch_worker = PatchGenerationWorker(self, mod_name, format_choice)
        
        # Create progress dialog
        progress_dialog = QMessageBox(self)
        progress_dialog.setWindowFlags(progress_dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        progress_dialog.setWindowTitle('🔧 Generating Mod...')
        progress_dialog.setText('⏳ Generating patch files...\n(This window will close when done)')
        progress_dialog.setStandardButtons(QMessageBox.NoButton)  # No buttons while working
        progress_dialog.setMinimumWidth(400)
        
        # Status label for updates
        status_label = QLabel('Initializing...')
        layout = progress_dialog.layout()
        layout.addWidget(status_label, 1, 1)
        
        # Connect signals
        self.patch_worker.progress_update.connect(lambda msg: status_label.setText(msg))
        self.patch_worker.generation_complete.connect(
            lambda result: self._on_patch_generation_complete(result, progress_dialog, mod_name)
        )
        
        # Start worker
        self.patch_worker.start()
        progress_dialog.exec_()
    
    def _on_patch_generation_complete(self, result, progress_dialog, mod_name):
        """Handle patch generation completion"""
        # Close progress dialog
        progress_dialog.accept()  # Use accept() for modal dialogs instead of close()
        
        # Process results
        success = result.get('success', False)
        patch_results = result.get('results', [])
        error_msg = result.get('error_msg', None)
        
        self.update_selected_tracks_label()
        
        if error_msg:
            self.audio_status_label.setText(f'❌ Generation Error: {error_msg}')
            self.logger.error(f'Patch generation error: {error_msg}')
            QMessageBox.critical(self, 'Generation Error', f'Patch generation failed:\n\n{error_msg}')
            return
        
        if not patch_results:
            self.audio_status_label.setText('❌ No patches were generated')
            self.logger.error('No patches generated')
            QMessageBox.warning(self, 'Generation Failed', 'No patches were generated. Please check your selections.')
            return
        
        # Check if all successful
        all_success = all(r.get('success') for r in patch_results)
        
        if all_success:
            paths = [r['patchPath'] for r in patch_results]
            total_files = sum(len(r.get('filesCopied', [])) for r in patch_results)
            if total_files == 0:
                add_selections = getattr(self, 'add_selections', {})
                if add_selections:
                    total_files = 0
                    for biome_key, tracks_dict in add_selections.items():
                        total_files += len(tracks_dict.get('day', [])) + len(tracks_dict.get('night', []))
                else:
                    day_tracks = self.day_tracks if hasattr(self, 'day_tracks') else []
                    night_tracks = self.night_tracks if hasattr(self, 'night_tracks') else []
                    total_files = len(day_tracks) + len(night_tracks)
            
            status_text = f"✅ Patches created for {len(paths)} biome(s) with {total_files} music file(s)"
            self.audio_status_label.setText(status_text)
            self.logger.log(status_text)
            
            for path in paths:
                self.logger.log(f"  • {path}")
            for r in patch_results:
                for filename in r.get('filesCopied', []):
                    self.logger.log(f"    ✓ Copied: {filename}")
                for error in r.get('copyErrors', []):
                    self.logger.warn(f"    ✗ {error}")
            
            # Show completion message and export dialog
            QMessageBox.information(
                self,
                'Generation Complete! ✅',
                '🌍 IMPORTANT: Music Patches && New Worlds\n\n'
                'Starbound bakes music into world files at generation time.\n\n'
                '✓ Your music will appear in: NEW worlds created AFTER installing\n'
                '✗ Your music will NOT appear in: EXISTING worlds created before\n\n'
                '📝 To update existing worlds: Use the Terraformer tool\n\n'
                'For testing: Create a new world to hear your music!\n\n'
                'Your mod is ready to install!'
            )
            self._show_export_confirmation_dialog(mod_name)
        else:
            error_msg = "Patch generation failed for some biomes"
            self.audio_status_label.setText(f"❌ {error_msg}")
            self.logger.error(error_msg)
            for r in patch_results:
                if not r.get('success'):
                    self.logger.error(f"  • {r.get('message', 'Unknown error')}")
            if patch_results:
                QMessageBox.critical(self, 'Patch Error', patch_results[0].get('message', 'Unknown error'))

    def _show_format_selection_dialog(self):
        """
        Show dialog to ask user whether to export as Pak File or Loose Files.
        Returns 'pak' or 'loose', or None if user cancelled.
        
        This dialog appears RIGHT BEFORE generation so users can't accidentally skip it.
        """
        dialog = QDialog(self)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dialog.setWindowTitle('Choose Output Format')
        dialog.setModal(True)
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel('How should your mod be packaged?')
        title.setStyleSheet('color: #e6ecff; font-size: 16px; font-family: "Hobo"; font-weight: bold; margin-bottom: 12px;')
        layout.addWidget(title)
        
        # Instructions
        instruction = QLabel('Choose how you want to install your mod to Starbound:')
        instruction.setStyleSheet('color: #b19cd9; font-size: 12px; margin-bottom: 16px;')
        layout.addWidget(instruction)
        
        # Radio buttons in a group
        format_group = QButtonGroup()
        
        # Pak option
        pak_radio = QRadioButton('📦 Pak File (Recommended)')
        pak_radio.setToolTip('Single compact file - easy to share, easy to install')
        pak_radio.setStyleSheet('color: #e6ecff; font-size: 13px; padding: 6px; margin-bottom: 8px;')
        format_group.addButton(pak_radio, 0)
        layout.addWidget(pak_radio)
        
        pak_desc = QLabel('✓ Single file - easy to share with friends\n✓ Fast installation\n✓ Compact storage')
        pak_desc.setStyleSheet('color: #a0a8ff; font-size: 11px; margin-left: 24px; margin-bottom: 12px;')
        layout.addWidget(pak_desc)
        
        # Loose option
        loose_radio = QRadioButton('📁 Loose Files (Editable)')
        loose_radio.setToolTip('Folder with individual files - good for tweaking and modding')
        loose_radio.setStyleSheet('color: #e6ecff; font-size: 13px; padding: 6px; margin-bottom: 8px;')
        format_group.addButton(loose_radio, 1)
        layout.addWidget(loose_radio)
        
        loose_desc = QLabel('✓ Folder format - easy to edit\n✓ Good for development\n✓ Larger file size')
        loose_desc.setStyleSheet('color: #a0a8ff; font-size: 11px; margin-left: 24px; margin-bottom: 16px;')
        layout.addWidget(loose_desc)
        
        # Restore user's last choice from settings
        try:
            last_format = self.settings.get('last_output_format', 'pak')
        except:
            last_format = 'pak'
        
        if last_format == 'loose':
            loose_radio.setChecked(True)
        else:
            pak_radio.setChecked(True)
        
        layout.addSpacing(12)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton('Cancel')
        cancel_btn.setStyleSheet('''QPushButton {
            background-color: #3a4a6a;
            color: #e6ecff;
            border-radius: 6px;
            padding: 6px 16px;
            font-family: "Hobo";
        }
        QPushButton:hover {
            background-color: #4a6a9a;
        }
        ''')
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton('Continue with Generation')
        ok_btn.setStyleSheet('''QPushButton {
            background-color: #3a6ea5;
            color: #e6ecff;
            border-radius: 6px;
            padding: 6px 20px;
            font-family: "Hobo";
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #4e8cff;
            border: 1px solid #6bbcff;
        }
        ''')
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # Show dialog
        if dialog.exec() == QDialog.Accepted:
            if loose_radio.isChecked():
                return 'loose'
            else:
                return 'pak'
        else:
            return None  # User cancelled

    def _show_export_confirmation_dialog(self, mod_name: str):
        """Show confirmation dialog for mod export using the format choice stored in self.output_format"""
        # Use format choice that was set during Generate button click
        use_pak = (self.output_format == 'pak') if hasattr(self, 'output_format') else True
        format_name = 'Pak File' if use_pak else 'Loose Files'
        self.logger.log(f'Format selected: {format_name}', context='Export')
        
        dialog = QMessageBox(self)
        dialog.setWindowTitle('Install Mod to Starbound')
        dialog.setIcon(QMessageBox.Information)
        dialog.setText('✅ Mod patches created successfully!')
        dialog.setInformativeText(
            f'Mod Name: {mod_name}\n'
            f'Output Format: {format_name}\n\n'
            f'Ready to install to Starbound/mods/ folder?'
        )
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        dialog.setDefaultButton(QMessageBox.Yes)
        
        reply = dialog.exec()
        if reply == QMessageBox.Yes:
            self._launch_export_worker(mod_name, use_pak)
        else:
            self.audio_status_label.setText('⏸️  Mod ready in staging. Installation skipped.')
            self.logger.log('User cancelled mod installation')
    
    def _launch_export_worker(self, mod_name, use_pak):
        """Launch mod export in a background thread"""
        from PyQt5.QtCore import QTimer
        
        # Create and launch worker
        self.export_worker = ExportWorker(self, mod_name, use_pak)
        
        # Create progress dialog
        progress_dialog = QMessageBox(self)
        progress_dialog.setWindowFlags(progress_dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        progress_dialog.setWindowTitle('📦 Installing Mod...')
        progress_dialog.setText('Copying mod to Starbound/mods folder...\n(This window will close when done)')
        progress_dialog.setStandardButtons(QMessageBox.NoButton)  # No buttons while working
        progress_dialog.setFixedSize(600, 220)  # Fixed width AND height to prevent any resizing
        
        # Status label for updates
        status_label = QLabel('Initializing...')
        status_label.setWordWrap(True)
        status_label.setFixedWidth(560)  # Keep label from expanding dialog
        status_label.setMaximumHeight(40)  # Limit height so text wraps instead of expanding
        
        # Progress bar with cyan styling
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setFixedHeight(25)
        progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #00d4ff; background-color: #0d1117; border-radius: 4px; }"
            "QProgressBar::chunk { background-color: #00d4ff; border-radius: 3px; }"
        )
        
        layout = progress_dialog.layout()
        layout.addWidget(progress_bar, 1, 1)
        layout.addWidget(status_label, 2, 1)
        
        # Animated hourglass for visual feedback
        hourglass_frames = ['⏳', '⌛']
        hourglass_index = [0]
        
        def animate_hourglass():
            hourglass_index[0] = (hourglass_index[0] + 1) % len(hourglass_frames)
            current_frame = hourglass_frames[hourglass_index[0]]
            progress_dialog.setText(f'{current_frame} Copying mod to Starbound/mods folder...\n(This window will close when done)')
        
        # Timer for hourglass animation
        hourglass_timer = QTimer()
        hourglass_timer.timeout.connect(animate_hourglass)
        hourglass_timer.start(500)  # Animate every 500ms
        
        # Connect signals
        self.export_worker.progress_update.connect(
            lambda data: (
                status_label.setText(data.get('message', '')),
                progress_bar.setValue(data.get('percentage', 0))
            )
        )
        self.export_worker.export_complete.connect(
            lambda result: (
                hourglass_timer.stop(),
                self._on_export_complete(result, progress_dialog, mod_name)
            )
        )
        
        # Start worker
        self.export_worker.start()
        progress_dialog.exec_()
    
    def _on_export_complete(self, result, progress_dialog, mod_name):
        """Handle mod export completion"""
        # Close progress dialog
        progress_dialog.accept()
        
        # Process results
        success = result.get('success', False)
        message = result.get('message', '')
        installed_path = result.get('installed_path', '')
        error_msg = result.get('error_msg', None)
        
        if error_msg:
            self.audio_status_label.setText(f'❌ Installation failed: {error_msg}')
            self.logger.error(f'Mod export error: {error_msg}')
            QMessageBox.critical(self, 'Installation Error', f'Could not install mod:\n{error_msg}')
            return
        
        if success:
            self.audio_status_label.setText(f'✅ {message}')
            self.logger.log(f'Mod installed successfully: {installed_path}')
            
            # Show success dialog with location
            QMessageBox.information(
                self,
                'Mod Installed! ✅',
                f'{message}\n\nMod is now ready to use in Starbound!\n\nLocation:\n{installed_path}'
            )
        else:
            self.audio_status_label.setText(f'❌ Installation failed: {message}')
            self.logger.error(f'Mod installation failed: {message}')
            QMessageBox.warning(self, 'Installation Failed', f'Could not install mod:\n{message}')

    def _gather_current_mod_state(self) -> dict:
        """Gather current mod configuration into a saveable state dict"""
        state = {
            'mod_name': self.modname_input.text() or 'Untitled Mod',
            'patch_mode': getattr(self, 'patch_mode', 'add'),
            'day_tracks': getattr(self, 'day_tracks', []),
            'night_tracks': getattr(self, 'night_tracks', []),
            'add_selections': getattr(self, 'add_selections', {}),  # Save per-biome Add selections (NEW)
            'selected_biomes': getattr(self, 'selected_biomes', []),
            'replace_selections': getattr(self, 'replace_selections', {}),
            'selected_track_type': getattr(self, 'selected_track_type', None),  # ← Save Day/Night/Both choice
            'folder_path': self.mod_folder_display.text() if hasattr(self, 'mod_folder_display') else ''
        }
        replace_sel_count = sum(len(v.get('day', {})) + len(v.get('night', {})) for v in state['replace_selections'].values())
        add_sel_count = sum(len(v.get('day', [])) + len(v.get('night', [])) for v in state['add_selections'].values())
        print(f'[PERSIST] _gather_current_mod_state() = mod_name={state["mod_name"]}, patch_mode={state["patch_mode"]}, day_tracks={len(state["day_tracks"])}, night_tracks={len(state["night_tracks"])}, biomes={len(state["selected_biomes"])}, replace_selections={replace_sel_count}, add_selections={add_sel_count}, track_type={state["selected_track_type"]}')
        return state

    def _auto_save_mod_state(self, action: str = ''):
        """Auto-save current mod state to mod_saves (only if mod name is set)."""
        try:
            mod_name = self.modname_input.text().strip() if hasattr(self, 'modname_input') else ''
            if mod_name and mod_name != 'blank_mod':
                mod_state = self._gather_current_mod_state()
                success = self.mod_save_manager.save_mod(mod_name, mod_state)
                if action:
                    if success:
                        print(f'[PERSIST] ✅ Auto-saved mod on {action}: {mod_name}')
                    else:
                        print(f'[PERSIST] [FAIL] FAILED to auto-save mod on {action}: {mod_name}')
        except Exception as e:
            print(f'[ERROR] Failed to auto-save mod: {e}')

    def _restore_mod_state_on_startup(self):
        """Restore mod state from saved config when starting with a saved mod name."""
        print(f'[DEBUG] _restore_mod_state_on_startup() called')
        try:
            mod_name = self.modname_input.text().strip() if hasattr(self, 'modname_input') else ''
            print(f'[DEBUG] Retrieved mod_name: "{mod_name}"')
            if not mod_name or mod_name == 'blank_mod':
                print(f'[PERSIST] No mod name to restore from')
                return
            
            # Try to load saved config for this mod
            print(f'[PERSIST] Attempting to restore mod: {mod_name}')
            config = self.mod_save_manager.load_mod(mod_name + '.json')
            if not config:
                print(f'[PERSIST] No config found for {mod_name}')
                return
            
            print(f'[PERSIST] Config loaded: {list(config.keys())}')
            
            # Restore patch_mode
            if 'patch_mode' in config:
                mode = config['patch_mode']
                self.patch_mode = mode
                # If we're restoring a saved patch_mode, mark it as confirmed (was confirmed in previous session)
                self._mode_confirmed_this_session = True
                self.settings.set('last_patch_mode', mode)
                print(f'[PERSIST] Restored patch_mode: {mode}')
            
            # Restore day/night tracks
            if 'day_tracks' in config:
                self.day_tracks = config['day_tracks']
                print(f'[PERSIST] Restored {len(self.day_tracks)} day tracks: {[Path(t).name for t in self.day_tracks]}')
            else:
                print(f'[PERSIST] No day_tracks in config')
            
            if 'night_tracks' in config:
                self.night_tracks = config['night_tracks']
                print(f'[PERSIST] Restored {len(self.night_tracks)} night tracks: {[Path(t).name for t in self.night_tracks]}')
            else:
                print(f'[PERSIST] No night_tracks in config')
            
            # Restore replace_selections (for Replace mode)
            if 'replace_selections' in config:
                self.replace_selections = config['replace_selections']
                print(f'[PERSIST] Restored replace_selections for {len(self.replace_selections)} biome(s)')
            
            # Restore add_selections (for Add mode) (NEW)
            if 'add_selections' in config:
                self.add_selections = config['add_selections']
                print(f'[PERSIST] Restored add_selections for {len(self.add_selections)} biome(s)')
                
                # If add_selections has biomes but selected_biomes is empty, sync them
                if self.add_selections and not self.selected_biomes:
                    self.selected_biomes = list(self.add_selections.keys())
                    print(f'[PERSIST] Synced selected_biomes from add_selections: {len(self.selected_biomes)} bimes')
            
            # Restore selected biomes and update display
            if 'selected_biomes' in config:
                self.selected_biomes = config['selected_biomes']
                print(f'[PERSIST] Restored {len(self.selected_biomes)} selected biomes: {self.selected_biomes}')
                
                # Update status label - show tracks count if in Replace mode
                if self.selected_biomes:
                    biome_names = ", ".join([bio for cat, bio in self.selected_biomes])
                    
                    # For Replace mode, also show track count
                    if self.patch_mode == 'replace' and self.replace_selections:
                        total_tracks = sum(len(v.get('day', {})) + len(v.get('night', {})) 
                                         for v in self.replace_selections.values())
                        status_text = f'✅ Biomes: {biome_names} | {total_tracks} track replacements'
                    # For Add mode, show added tracks count
                    elif self.patch_mode == 'add' and (self.day_tracks or self.night_tracks):
                        total_added = len(self.day_tracks) + len(self.night_tracks)
                        status_text = f'✅ Biomes: {biome_names} | {total_added} tracks added'
                    else:
                        status_text = f'✅ Biomes selected: {biome_names}'
                    
                    self.audio_status_label.setText(status_text)
                    print(f'[PERSIST] Updated audio_status_label: {status_text}')
                
                # Update biome display label if it exists
                if hasattr(self, 'selected_biomes_label') and self.selected_biomes:
                    biome_display_list = [bio for cat, bio in self.selected_biomes]
                    biome_count = len(biome_display_list)
                    if biome_count <= 5:
                        biome_display = ", ".join(biome_display_list)
                    else:
                        first_five = ", ".join(biome_display_list[:5])
                        remaining = biome_count - 5
                        biome_display = f'{first_five}, and {remaining} more'
                    
                    # Add track count to biome label
                    track_count = len(self.day_tracks) + len(self.night_tracks) if (self.day_tracks or self.night_tracks) else 0
                    if track_count > 0:
                        self.selected_biomes_label.setText(f'✓ Biomes ({biome_count}): {biome_display} | {track_count} tracks')
                    else:
                        self.selected_biomes_label.setText(f'✓ Biomes ({biome_count}): {biome_display}')
                    print(f'[PERSIST] Updated selected_biomes_label')
            
            # Restore selected_track_type (Day/Night/Both choice)
            if 'selected_track_type' in config:
                self.selected_track_type = config['selected_track_type']
                print(f'[PERSIST] Restored selected_track_type: {self.selected_track_type}')
            
            # 🆕 AUTO-DETECT BOTH MODE: If patch_mode is None but we have both replace_selections AND add selections,
            # this is a Both mode workflow that needs to be recognized
            has_replace = bool(self.replace_selections)
            has_add = bool(self.add_selections or self.day_tracks or self.night_tracks)
            
            if self.patch_mode is None and has_replace and has_add:
                # Auto-detect Both mode from the presence of both replace and add data
                self.patch_mode = 'both'
                self._mode_confirmed_this_session = True
                self.settings.set('last_patch_mode', 'both')
                print(f'[PERSIST] ✅ AUTO-DETECTED Both mode (replace_selections={len(self.replace_selections)} biomes, add_selections={len(self.add_selections)} biomes)')
            
            # Update tracks display label if it exists
            if hasattr(self, 'selected_tracks_label'):
                self.update_selected_tracks_label()
                print(f'[PERSIST] Updated selected_tracks_label')
            
            # Check what we restored before updating button
            print(f'[DEBUG] Before button update: day_tracks={len(getattr(self, "day_tracks", []))}, night_tracks={len(getattr(self, "night_tracks", []))}, selected_biomes={len(getattr(self, "selected_biomes", []))}, patch_mode={getattr(self, "patch_mode", None)}')
            
            # Apply button visibility based on restored patch_mode
            # (Match what on_add_to_game/on_replace/on_replace_and_add do when initially selected)
            # IMPORTANT: Only hide buttons if patch_mode is explicitly set (not None)
            restored_mode = getattr(self, 'patch_mode', None)
            if restored_mode == 'add':
                # Hide Replace buttons when Add mode is restored
                if hasattr(self, 'replace_btn'):
                    self.replace_btn.hide()
                if hasattr(self, 'replace_and_add_btn'):
                    self.replace_and_add_btn.hide()
                # Show Step 6 for Add mode (users need to see day/night track selection area)
                self._set_step6_visible(True)
                print(f'[PERSIST] Applied Add mode button visibility (Replace buttons hidden, Step 6 shown)')
            elif restored_mode == 'replace':
                # Hide Add buttons when Replace mode is restored
                if hasattr(self, 'add_to_game_btn'):
                    self.add_to_game_btn.hide()
                if hasattr(self, 'replace_and_add_btn'):
                    self.replace_and_add_btn.hide()
                # Show View All Tracks button for Replace mode
                if hasattr(self, 'view_tracks_btn'):
                    self.view_tracks_btn.show()
                self.replace_was_selected = True  # Mark that Replace was selected
                self._set_step6_visible(False)  # Hide Step 6
                print(f'[PERSIST] Applied Replace mode button visibility')
            elif restored_mode == 'both':
                # Hide Add buttons when Both mode is restored
                if hasattr(self, 'add_to_game_btn'):
                    self.add_to_game_btn.hide()
                if hasattr(self, 'replace_btn'):
                    self.replace_btn.hide()
                # For Both mode, SHOW Step 6 because users need to select ADD tracks
                self._set_step6_visible(True)
                print(f'[PERSIST] Applied Both mode button visibility (Step 6 shown for ADD track selection)')
            else:
                # No patch mode selected yet - show all buttons for user to choose
                if hasattr(self, 'add_to_game_btn'):
                    self.add_to_game_btn.show()
                if hasattr(self, 'replace_btn'):
                    self.replace_btn.show()
                if hasattr(self, 'replace_and_add_btn'):
                    self.replace_and_add_btn.show()
                # Hide Step 6 until a mode is selected
                self._set_step6_visible(False)
                self.replace_was_selected = False
                print(f'[PERSIST] No patch mode selected yet - showing all Step 5 buttons, hiding Step 6')
            
            # Update patch button state after restoring everything
            if hasattr(self, 'patch_btn') and self.patch_btn:
                self.update_patch_btn_state()
                print(f'[PERSIST] Updated patch button state')
            else:
                print(f'[PERSIST] patch_btn not ready yet, skipping button state update')
            
        except Exception as e:
            print(f'[PERSIST] Could not restore mod state: {e}')
            import traceback
            traceback.print_exc()

    def clear_audio(self):
        """Clear all selected audio files with confirmation"""
        if not hasattr(self, 'selected_audio_files') or not self.selected_audio_files:
            return  # Nothing to clear
        
        file_count = len(self.selected_audio_files)
        reply = QMessageBox.question(
            self,
            '🗑️ Clear Selected Files?',
            f'Are you sure you want to remove all {file_count} selected file(s)?\n\nThis cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.selected_audio_files = []
            self.selected_files_label.setText('')
            self.files_needing_split.clear()
            self.split_decisions.clear()
            print('[PERSIST] Audio files cleared')
            self._auto_save_mod_state('audio clear')
            self.logger.log(f'Audio files cleared ({file_count} file(s) removed)')

    def on_new_mod(self):
        """Start a new mod configuration from scratch"""
        try:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                'New Mod',
                'Start a new mod configuration? (Current data will be cleared)',
                QMessageBox.Yes | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                return
            
            # Set flag to prevent auto-loading old config when mod name is generated
            self._skip_config_restore = True
            
            # Generate a new random name for the fresh mod
            from utils.random_mod_name import generate_random_mod_name
            new_name = generate_random_mod_name()
            self.modname_input.setText(new_name)
            self._current_autogen_name = new_name  # Track for comparison
            self.modname_input.setStyleSheet('color: #888888; background: #283046; border-radius: 8px; border: 1px solid #3a4a6a; font-size: 15px; font-family: "Hobo";')
            self._modname_autofill = True
            self.modname_input.setReadOnly(False)  # Keep editable so user can type own name
            self.modname_confirm_checkbox.setChecked(False)  # Unchecked = user can edit
            self.settings.set('last_mod_name', new_name)
            print(f'[NEW_MOD] Generated new random name: {new_name}')
            
            # Reset patch mode to None (no mode selected yet - user should choose)
            self.patch_mode = None
            self.settings.set('last_patch_mode', None)
            print(f'[NEW_MOD] Reset patch_mode to: {self.patch_mode}')
            
            # Reset Replace flag so buttons can be shown
            self.replace_was_selected = False
            self._set_step6_visible(False)
            print(f'[NEW_MOD] Reset replace_was_selected and hid Step 6')
            
            # Show ALL patching mode buttons (fresh slate - user hasn't chosen yet)
            if hasattr(self, 'add_to_game_btn'):
                self.add_to_game_btn.show()
                print(f'[NEW_MOD] Showed add_to_game_btn')
            if hasattr(self, 'replace_btn'):
                self.replace_btn.show()
                print(f'[NEW_MOD] Showed replace_btn')
            if hasattr(self, 'replace_and_add_btn'):
                self.replace_and_add_btn.show()
                print(f'[NEW_MOD] Showed replace_and_add_btn')
            
            # Force layout update to make buttons visible
            if hasattr(self, 'scroll_area'):
                self.scroll_area.update()
                self.scroll_area.repaint()
                print(f'[NEW_MOD] Updated scroll area layout')
            self.update()
            self.repaint()
            print(f'[NEW_MOD] Updated and repainted main window')
            
            # Clear track lists
            self.day_tracks = []
            self.night_tracks = []
            self.add_selections = {}  # Clear per-biome Add selections (NEW)
            self.selected_track_type = None
            
            # Clear replace selections
            self.replace_selections = {}
            
            # Clear selected biomes
            self.selected_biomes = []
            
            # Reset mode confirmation flag for new mod
            self._mode_confirmed_this_session = False
            print(f'[NEW_MOD] Reset mode confirmation flag')
            
            # Clear folder display if it exists
            if hasattr(self, 'mod_folder_display'):
                self.mod_folder_display.setText('')
            
            # Clear UI labels that display tracks and biomes
            self.update_selected_tracks_label()
            if hasattr(self, 'selected_biomes_label'):
                self.selected_biomes_label.setText('No biomes selected yet.')
            self.audio_status_label.setText('')
            print(f'[NEW_MOD] Cleared all UI labels and status')
            
            # Disable Generate button since we cleared everything
            self.patch_btn.setEnabled(False)
            print(f'[NEW_MOD] Disabled Generate button')
            
            print(f'[NEW_MOD] NEW MOD RESET COMPLETE - Ready for fresh start')
            QMessageBox.information(self, 'New Mod', 'Ready to create a new mod!')
            self.logger.log('Started new mod configuration')
        
        except Exception as e:
            self.logger.error(f'Error creating new mod: {str(e)}')
            QMessageBox.critical(self, 'Error', f'Error creating new mod:\n{str(e)}')

    def on_save_mod(self):
        """Save current mod configuration to file"""
        try:
            mod_name = self.modname_input.text().strip()
            if not mod_name:
                QMessageBox.warning(self, 'Save Mod', 'Please enter a mod name first.')
                return
            
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                'Save Mod Configuration',
                f'Save mod configuration as:\n"{mod_name}"?',
                QMessageBox.Yes | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                return
            
            # Gather current state
            config = self._gather_current_mod_state()
            
            # Save it
            success = self.mod_save_manager.save_mod(mod_name, config)
            
            if success:
                QMessageBox.information(
                    self,
                    'Mod Saved',
                    f'Mod configuration saved successfully.\n\nLocation:\n{self.mod_save_manager.get_save_path()}'
                )
                self.logger.log(f'Saved mod configuration: {mod_name}')
            else:
                QMessageBox.critical(self, 'Save Failed', 'Could not save mod configuration.')
                self.logger.error(f'Failed to save mod: {mod_name}')
        
        except Exception as e:
            self.logger.error(f'Error saving mod: {str(e)}')
            QMessageBox.critical(self, 'Error', f'Error saving mod:\n{str(e)}')

    def on_load_mod(self):
        """Load a saved mod configuration from file"""
        try:
            saved_mods = self.mod_save_manager.list_saved_mods()
            
            if not saved_mods:
                QMessageBox.information(self, 'No Saved Mods', 'No saved mod configurations found.')
                return
            
            # Create selection dialog
            dlg = QDialog(self)
            dlg.setWindowFlags(dlg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            dlg.setWindowTitle('Load Mod Configuration')
            dlg.setMinimumSize(400, 300)
            dlg.setStyleSheet('background-color: #23283b; color: #e6ecff;')
            layout = QVBoxLayout()
            
            # Instructions
            info = QLabel('Select a saved mod configuration to load:')
            info.setStyleSheet('color: #e6ecff;')
            layout.addWidget(info)
            
            # List widget for mod selection
            mod_list = QListWidget()
            mod_list.setStyleSheet('color: #e6ecff; background-color: #283046; border: 1px solid #3a4a6a; border-radius: 4px;')
            for filename, mod_name in saved_mods:
                item_text = f"{mod_name}"
                mod_list.addItem(item_text)
                mod_list.item(mod_list.count() - 1).setData(Qt.UserRole, filename)
            
            layout.addWidget(mod_list)
            
            # Buttons
            btn_layout = QHBoxLayout()
            load_btn = QPushButton('Load')
            load_btn.setStyleSheet('''QPushButton {
                background-color: #3a6ea5;
                color: #e6ecff;
                border-radius: 6px;
                border: 1px solid #4e8cff;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #4e8cff;
                border: 1px solid #6bbcff;
            }
            ''')
            cancel_btn = QPushButton('Cancel')
            cancel_btn.setStyleSheet('''QPushButton {
                background-color: #3a4a6a;
                color: #e6ecff;
                border-radius: 6px;
                border: 1px solid #555;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #4a6a9a;
            }
            ''')
            btn_layout.addWidget(load_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            
            dlg.setLayout(layout)
            
            # Connect buttons
            selected_filename = [None]
            
            def on_load_clicked():
                current = mod_list.currentItem()
                if current:
                    selected_filename[0] = current.data(Qt.UserRole)
                    dlg.accept()
            
            load_btn.clicked.connect(on_load_clicked)
            cancel_btn.clicked.connect(dlg.reject)
            
            # Show dialog
            if dlg.exec_() == QDialog.Accepted and selected_filename[0]:
                # FIRST: Completely reset all old UI state to prevent previous mod's data from showing
                print(f'[LOAD_MOD] Clearing all old state before loading new mod')
                self.day_tracks = []
                self.night_tracks = []
                self.add_selections = {}  # Clear per-biome Add selections
                self.selected_track_type = None
                self.replace_selections = {}
                self.selected_biomes = []
                self.patch_mode = None  # Reset to None, will be set by loaded config
                self._mode_confirmed_this_session = False
                self.replace_was_selected = False
                
                # Reset ALL button visibility to initial state (all visible)
                print(f'[LOAD_MOD] Resetting button visibility to initial state')
                if hasattr(self, 'add_to_game_btn'):
                    self.add_to_game_btn.show()
                if hasattr(self, 'replace_btn'):
                    self.replace_btn.show()
                if hasattr(self, 'replace_and_add_btn'):
                    self.replace_and_add_btn.show()
                if hasattr(self, 'view_tracks_btn'):
                    self.view_tracks_btn.show()
                
                # Reset UI labels and display elements
                if hasattr(self, 'audio_status_label'):
                    self.audio_status_label.setText('Select a patching method above')
                if hasattr(self, 'selected_biomes_label'):
                    self.selected_biomes_label.setText('No biomes selected yet.')
                self.update_selected_tracks_label()  # Reset track display
                self._set_step6_visible(False)  # Hide Step 6 initially
                
                # THEN: Load the mod
                config = self.mod_save_manager.load_mod(selected_filename[0])
                
                if config:
                    # After loading mod, validate backup folders
                    if 'mod_name' in config:
                        mod_name_to_validate = config['mod_name']
                        
                        # 🆕 CRITICAL: Save the loaded mod name to settings so it persists on app restart
                        self.settings.set('last_mod_name', mod_name_to_validate)
                        print(f'[LOAD_MOD] Saved loaded mod to settings: {mod_name_to_validate}')
                        
                        try:
                            starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
                            staging_dir = starsound_dir / 'staging'
                            safe_mod_name = "".join(c for c in mod_name_to_validate if c.isalnum() or c in (' ', '_', '-')).rstrip()
                            
                            # Backups are at root-level backups/
                            backup_root = self._get_backup_path(mod_name_to_validate)
                            backups_originals = backup_root / 'originals'
                            backups_converted = backup_root / 'converted'
                            
                            if backups_originals.exists():
                                # Move any .ogg files from originals to converted
                                for ogg_file in backups_originals.glob('*.ogg'):
                                    try:
                                        converted_dest = backups_converted / ogg_file.name
                                        ogg_file.rename(converted_dest)
                                        self.logger.log(f'[AUTO-FIX] Moved misplaced OGG from originals to converted: {ogg_file.name}')
                                    except Exception as e:
                                        self.logger.warn(f'[AUTO-FIX] Could not move OGG: {ogg_file.name} ({e})')
                        except Exception as e:
                            self.logger.warn(f'[AUTO-FIX] Error validating backup folders: {e}')
                    
                    # Restore state from config
                    if 'mod_name' in config:
                        self.modname_input.setText(config['mod_name'])
                    
                    # 🆕 Restore add_selections (per-biome Add mode selections)
                    if 'add_selections' in config:
                        self.add_selections = config['add_selections']
                        print(f'[LOAD_MOD] Restored add_selections for {len(self.add_selections)} biome(s)')
                    
                    # 🆕 Restore replace_selections (per-biome Replace mode selections)
                    if 'replace_selections' in config:
                        self.replace_selections = config['replace_selections']
                        print(f'[LOAD_MOD] Restored replace_selections for {len(self.replace_selections)} biome(s)')
                    
                    if 'patch_mode' in config:
                        mode = config['patch_mode']
                        self.patch_mode = mode
                        print(f'[LOAD_MOD] Loaded patch_mode from config: {mode}')
                        # Mark as confirmed since we're loading a saved mod (was confirmed in previous session)
                        self._mode_confirmed_this_session = True
                        self.settings.set('last_patch_mode', mode)
                        
                        # Update UI based on mode - set button visibility to match the mode's lock state
                        if mode == 'add':
                            print(f'[LOAD_MOD] Setting button visibility for ADD mode')
                            self.audio_status_label.setText('✅ Mode: Add to Game (⭐ Check "Remove vanilla" for safest option, or add alongside vanilla)')
                            # Add mode: hide Replace and Both buttons, keep Add visible
                            self.replace_btn.hide()
                            self.replace_and_add_btn.hide()
                            if hasattr(self, 'add_to_game_btn'):
                                self.add_to_game_btn.show()
                            self._set_step6_visible(True)  # Show Step 6 with Day/Night buttons
                        elif mode == 'replace':
                            print(f'[LOAD_MOD] Setting button visibility for REPLACE mode')
                            self.audio_status_label.setText('🎵 Mode: Replace Base Game Music (one track at a time)')
                            # Replace mode: hide Add and Both buttons, keep Replace visible
                            if hasattr(self, 'add_to_game_btn'):
                                self.add_to_game_btn.hide()
                            self.replace_and_add_btn.hide()
                            self.replace_btn.show()
                            # Show View All Tracks button for Replace mode
                            if hasattr(self, 'view_tracks_btn'):
                                self.view_tracks_btn.show()
                            self.replace_was_selected = True  # Lock in mode for this session
                            self._set_step6_visible(False)
                        elif mode == 'both':
                            print(f'[LOAD_MOD] Setting button visibility for BOTH mode')
                            print(f'[LOAD_MOD] Both mode data: replace_selections={len(self.replace_selections)}, add_selections={len(self.add_selections)}, selected_biomes={len(self.selected_biomes)}')
                            self.audio_status_label.setText('🔄 Mode: Replace specific tracks + Add new music')
                            # Both mode: hide Add and Replace buttons, keep Both visible
                            if hasattr(self, 'add_to_game_btn'):
                                self.add_to_game_btn.hide()
                            self.replace_btn.hide()
                            self.replace_and_add_btn.show()
                            self.replace_was_selected = True  # Lock in mode for this session
                            self._set_step6_visible(True)  # Show Step 6 for Add selections
                            print(f'[LOAD_MOD] Both mode complete - Step 6 visible, buttons hidden, ready for use')
                    else:
                        # patch_mode not saved - infer from selections (for old mods)
                        has_replace = bool(config.get('replace_selections', {}))
                        has_add = bool(config.get('add_selections', {}))
                        
                        if has_replace and has_add:
                            inferred_mode = 'both'
                        elif has_replace:
                            inferred_mode = 'replace'
                        else:
                            inferred_mode = 'add'
                        
                        self.patch_mode = inferred_mode
                        print(f'[LOAD_MOD] No patch_mode in config, inferred: {inferred_mode} (replace={has_replace}, add={has_add})')
                        self.logger.log(f'[LOAD_MOD] No patch_mode in config, inferred from selections: {inferred_mode} (replace={has_replace}, add={has_add})')
                        # Update UI to match - set button visibility to match the inferred mode's lock state
                        if inferred_mode == 'add':
                            print(f'[LOAD_MOD] Setting button visibility for INFERRED ADD mode')
                            self.audio_status_label.setText('✅ Mode: Add to Game (⭐ Check "Remove vanilla" for safest option, or add alongside vanilla)')
                            # Add mode: hide Replace and Both buttons, keep Add visible
                            self.replace_btn.hide()
                            self.replace_and_add_btn.hide()
                            if hasattr(self, 'add_to_game_btn'):
                                self.add_to_game_btn.show()
                            self._set_step6_visible(True)  # Show Step 6 with Day/Night buttons
                        elif inferred_mode == 'replace':
                            print(f'[LOAD_MOD] Setting button visibility for INFERRED REPLACE mode')
                            self.audio_status_label.setText('🎵 Mode: Replace Base Game Music (one track at a time)')
                            # Replace mode: hide Add and Both buttons, keep Replace visible
                            if hasattr(self, 'add_to_game_btn'):
                                self.add_to_game_btn.hide()
                            self.replace_and_add_btn.hide()
                            self.replace_btn.show()
                            # Show View All Tracks button for Replace mode
                            if hasattr(self, 'view_tracks_btn'):
                                self.view_tracks_btn.show()
                            self.replace_was_selected = True  # Lock in mode for this session
                            self._set_step6_visible(False)
                        elif inferred_mode == 'both':
                            print(f'[LOAD_MOD] Setting button visibility for INFERRED BOTH mode')
                            print(f'[LOAD_MOD] Both mode data: replace_selections={len(self.replace_selections)}, add_selections={len(self.add_selections)}, selected_biomes={len(self.selected_biomes)}')
                            self.audio_status_label.setText('🔄 Mode: Replace specific tracks + Add new music')
                            # Both mode: hide Add and Replace buttons, keep Both visible
                            if hasattr(self, 'add_to_game_btn'):
                                self.add_to_game_btn.hide()
                            self.replace_btn.hide()
                            self.replace_and_add_btn.show()
                            self.replace_was_selected = True  # Lock in mode for this session
                            self._set_step6_visible(True)  # Show Step 6 for Add selections
                            print(f'[LOAD_MOD] Inferred Both mode complete - Step 6 visible, buttons hidden')
                    
                    if 'day_tracks' in config:
                        self.day_tracks = config['day_tracks']
                    
                    if 'night_tracks' in config:
                        self.night_tracks = config['night_tracks']
                    
                    if 'selected_biomes' in config:
                        self.selected_biomes = config['selected_biomes']
                    
                    if 'folder_path' in config and hasattr(self, 'mod_folder_display'):
                        self.mod_folder_display.setText(config['folder_path'])
                    
                    # Update all UI displays to reflect loaded mod
                    self.update_selected_tracks_label()
                    if hasattr(self, 'selected_biomes_label'):
                        if self.selected_biomes:
                            biome_display_list = [bio for cat, bio in self.selected_biomes]
                            biome_count = len(biome_display_list)
                            if biome_count <= 5:
                                biome_display = ", ".join(biome_display_list)
                            else:
                                first_five = ", ".join(biome_display_list[:5])
                                remaining = biome_count - 5
                                biome_display = f'{first_five}, and {remaining} more'
                            # Add track count to biome label
                            track_count = len(self.day_tracks) + len(self.night_tracks) if (self.day_tracks or self.night_tracks) else 0
                            if track_count > 0:
                                self.selected_biomes_label.setText(f'✓ Biomes ({biome_count}): {biome_display} | {track_count} tracks')
                            else:
                                self.selected_biomes_label.setText(f'✓ Biomes ({biome_count}): {biome_display}')
                        else:
                            self.selected_biomes_label.setText('No biomes selected yet.')
                    self.update_patch_btn_state()
                    
                    # Force complete UI refresh to ensure all state updates are visible
                    self.update()  # Repaint the window
                    
                    QMessageBox.information(self, 'Mod Loaded', 'Mod configuration loaded successfully.')
                    self.logger.log(f'Loaded mod configuration: {config.get("mod_name", "Unknown")}')
                else:
                    QMessageBox.critical(self, 'Load Failed', 'Could not load mod configuration.')
                    self.logger.error(f'Failed to load mod: {selected_filename[0]}')
        
        except Exception as e:
            self.logger.error(f'Error loading mod: {str(e)}')
            QMessageBox.critical(self, 'Error', f'Error loading mod:\n{str(e)}')

    def on_browse_mod_saves(self):
        """Open file browser to mod saves folder"""
        try:
            mod_saves_path = self.mod_save_manager.get_save_path()
            
            # Ensure folder exists
            mod_saves_path.mkdir(parents=True, exist_ok=True)
            
            # Open with OS file browser
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                subprocess.Popen(f'explorer "{mod_saves_path}"')
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', str(mod_saves_path)])
            else:  # Linux
                subprocess.Popen(['xdg-open', str(mod_saves_path)])
            
            self.logger.log(f'Opened mod saves folder: {mod_saves_path}')
        
        except Exception as e:
            self.logger.error(f'Error opening mod saves folder: {str(e)}')
            QMessageBox.critical(self, 'Error', f'Error opening mod saves folder:\n{str(e)}')

    def closeEvent(self, event):
        """Save mod state when user closes the window."""
        try:
            mod_name = self.modname_input.text().strip() if hasattr(self, 'modname_input') else ''
            # Only save if user has explicitly set a mod name
            if mod_name and mod_name != 'blank_mod':
                # 🆕 CRITICAL: Ensure the mod name is saved to settings before closing
                # This prevents the last_mod_name from being blank on next startup
                self.settings.set('last_mod_name', mod_name)
                self.logger.log(f'Saved last_mod_name to settings before close: {mod_name}')
                
                mod_state = self._gather_current_mod_state()
                self.mod_save_manager.save_mod(mod_name, mod_state)
                self.logger.log(f'Mod saved on window close: {mod_name}')
        except Exception as e:
            print(f'[ERROR] Failed to save mod on close: {e}')
        
        # Allow the window to close normally
        event.accept()


# SearchFilterWorker - background thread for fast track searching
class SearchFilterWorker(QThread):
    """Background worker for filtering tracks - keeps UI responsive during search"""
    filter_complete = pyqtSignal(list, int)  # Emits (filtered_data, total_count)
    
    def __init__(self, search_index, query):
        super().__init__()
        self.search_index = search_index  # Lightweight index of all tracks
        self.query = query.lower().strip()  # Search query
    
    def run(self):
        """Execute search in background thread"""
        try:
            if not self.query:
                # No search - return all data
                filtered_data = []
                total_count = 0
                # This shouldn't happen (called from UI), but handle it
                self.filter_complete.emit([], 0)
                return
            
            # Fast search through lightweight index
            filtered_data = []
            total_count = sum(len(entry['tracks']) for entry in self.search_index)
            
            for index_entry in self.search_index:
                biome = index_entry['biome']
                biome_text = index_entry['biome_text']
                
                # Check if biome matches
                biome_matches = self.query in biome_text
                
                # Collect matching tracks
                day_dict = {}
                night_dict = {}
                day_list = []
                night_list = []
                is_replace = None
                
                for track_name, track_path, is_day, is_replace_mode, key_idx in index_entry['tracks']:
                    # Track matches if biome matches OR track name matches
                    if biome_matches or self.query in track_name:
                        is_replace = is_replace_mode
                        
                        if is_replace_mode:
                            # Replace mode: store as dict with index
                            if is_day:
                                day_dict[key_idx] = track_path
                            else:
                                night_dict[key_idx] = track_path
                        else:
                            # Add mode: store as list
                            if is_day:
                                day_list.append(track_path)
                            else:
                                night_list.append(track_path)
                
                # Only include biome if it has matching tracks
                if day_dict or night_dict or day_list or night_list:
                    filtered_data.append({
                        'biome': biome,
                        'day': day_dict if is_replace else day_list,
                        'night': night_dict if is_replace else night_list,
                        'is_replace': is_replace
                    })
            
            # Calculate total visible (only matching tracks)
            total_visible = sum(
                len(d['day']) + len(d['night']) 
                for d in filtered_data
            )
            
            # Emit results
            self.filter_complete.emit(filtered_data, total_count)
        
        except Exception as e:
            print(f'[SEARCH_ERROR] Error in search filter: {e}')
            import traceback
            traceback.print_exc()


class TracksViewerWindow(QDialog):
    """Separate window for viewing and managing selected tracks"""
    search_filter_complete = pyqtSignal(list, int)  # (filtered_data, total_count)
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        # Explicitly disable Windows help button on this dialog
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.main_window = main_window
        self.setWindowTitle('Selected Tracks - Full View')
        self.setMinimumSize(600, 500)
        
        # Get current font from main window and apply it
        current_font = getattr(main_window, 'current_font', 'Hobo')
        self.setStyleSheet(f'background-color: #0a0e27; color: #e6ecff; font-family: "{current_font}";')
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title
        title = QLabel('🎵 Your Selected Tracks')
        title.setStyleSheet('color: #00d4ff; font-weight: bold; font-size: 14px; margin-bottom: 8px;')
        layout.addWidget(title)
        
        # 🆕 SEARCH BAR
        search_layout = QHBoxLayout()
        search_label = QLabel('🔍 Search:')
        search_label.setStyleSheet('color: #b19cd9; font-size: 11px;')
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Type track name or biome to filter...')
        self.search_input.setStyleSheet('''QLineEdit {
            background-color: #283046;
            color: #e6ecff;
            border: 1px solid #3a4a6a;
            border-radius: 4px;
            padding: 4px;
            font-size: 11px;
        }
        QLineEdit:focus {
            border: 1px solid #6bbcff;
            background-color: #2d3a4a;
        }''')
        self.search_input.textChanged.connect(self._on_search_changed)
        self.search_input.returnPressed.connect(lambda: None)  # Prevent Enter from doing anything
        search_layout.addWidget(self.search_input, 1)
        
        # Track count display
        self.count_label = QLabel('(0 / 0)')
        self.count_label.setStyleSheet('color: #b19cd9; font-size: 10px; min-width: 60px;')
        search_layout.addWidget(self.count_label)
        
        # Clear search button (X)
        self.clear_search_btn = QPushButton('✕')
        self.clear_search_btn.setMaximumWidth(28)
        self.clear_search_btn.setStyleSheet('''QPushButton {
            background-color: #3a4a6a;
            color: #ff6b6b;
            border: 1px solid #3a4a6a;
            border-radius: 3px;
            font-weight: bold;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #4a5a7a;
        }
        QPushButton:pressed {
            background-color: #2a3a5a;
        }''')
        self.clear_search_btn.clicked.connect(self._clear_search)
        search_layout.addWidget(self.clear_search_btn)
        
        layout.addLayout(search_layout)
        
        # Scrollable content area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet('''
            QScrollArea {
                border: 1px solid #3a4a6a;
                border-radius: 4px;
                background: #0a0e27;
            }
            QScrollBar:vertical {
                background-color: #1a2540;
                width: 16px;
                border-radius: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a6a9a;
                border-radius: 8px;
                min-height: 60px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6a8aba;
            }
            QScrollBar::add-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        ''')
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(6)
        self.scroll_area.setWidget(self.content_widget)
        
        layout.addWidget(self.scroll_area)
        
        # Store search query and full track data for filtering
        self.current_search = ''
        self.all_track_data = []  # Will store: (biome, type, tracks_dict, is_replace_mode)
        self.search_index = []  # Lightweight index: [{'biome': tuple, 'biome_text': str, 'tracks': [(name, path, is_day, is_replace), ...]}, ...]
        self.search_worker = None  # Background worker thread for filtering
        self.search_filter_complete = pyqtSignal(list, int)
        
        # Debounce timer - wait 800ms after user stops typing before searching
        self.search_debounce_timer = QTimer()
        self.search_debounce_timer.setSingleShot(True)
        self.search_debounce_timer.timeout.connect(self._perform_search)
        self.search_debounce_timer.setInterval(800)  # 800ms delay - gives user time to type
        
        # Track which search is "current" - prevents stale results from displaying
        self.current_search_id = 0  # Incremented when search is cleared
        
        # Refresh and close buttons
        button_layout = QHBoxLayout()
        refresh_btn = QPushButton('🔄 Refresh')
        refresh_btn.setStyleSheet('''QPushButton {
            background-color: #3a6ea5;
            color: #e6ecff;
            padding: 6px 12px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #4e8cff;
        }
        ''')
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        
        close_btn = QPushButton('Close')
        close_btn.setStyleSheet('''QPushButton {
            background-color: #2d5a3d;
            color: #e6ecff;
            padding: 6px 12px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #3a8a55;
        }
        ''')
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _on_search_changed(self, search_text):
        """Search text changed - only search on new typed text, ignore backspace"""
        new_search = search_text.lower().strip()
        
        # Check if search is getting shorter (backspacing) or longer (typing)
        is_getting_shorter = len(new_search) < len(self.current_search)
        self.current_search = new_search
        
        # If search is now EMPTY, show all tracks in simplified view (instant!)
        if not self.current_search:
            self.search_debounce_timer.stop()
            self.current_search_id += 1  # Invalidate any pending search results
            # Kill any running search worker
            if self.search_worker and self.search_worker.isRunning():
                self.search_worker.requestInterruption()
            
            # Process any pending events to ensure old widgets are fully deleted
            from PyQt5.QtCore import QCoreApplication
            QCoreApplication.processEvents()
            
            # Clear search - restore full original window with all controls (deferred to avoid visual artifacts)
            QTimer.singleShot(400, self.refresh_display)
            return
        
        # If backspacing: do nothing! Leave current filtered results visible
        if is_getting_shorter:
            self.search_debounce_timer.stop()
            return
        
        # If typing new letters: debounce and search
        self.search_debounce_timer.stop()
        self.search_debounce_timer.start()
    
    def _clear_search(self):
        """Clear search button clicked - clear the search field"""
        self.search_input.clear()
    
    def keyPressEvent(self, event):
        """Override key press to prevent Enter from closing dialog"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # If search input has focus, don't let Enter propagate
            if self.search_input.hasFocus():
                return
        # Let other keys through to parent
        super().keyPressEvent(event)
    
    def _perform_search(self):
        """Actually perform the search after debounce delay (runs in main thread)"""
        # Skip if no search query
        if not self.current_search:
            return
        
        # Capture current search ID so we can ignore stale results
        search_id = self.current_search_id
        
        # Kill previous worker if still running
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.requestInterruption()
        
        # Spawn new worker thread for filtering
        self.search_worker = SearchFilterWorker(self.search_index, self.current_search)
        # Pass search_id so we can validate results are still current
        self.search_worker.filter_complete.connect(lambda data, count: self._on_search_complete(data, count, search_id))
        self.search_worker.start()
    
    def _on_search_complete(self, filtered_data, total_count, search_id):
        """Slot called when search worker completes - only display if result is still current"""
        # Ignore stale results from old searches (e.g., if user cleared the search)
        if search_id != self.current_search_id:
            return
        
        self._display_filtered_results(filtered_data, total_count)
    
    def _on_refresh_clicked(self):
        """Refresh button clicked - rebuild display (deferred to keep UI responsive)"""
        # Show immediate feedback
        self.count_label.setText('(refreshing...)')
        self.count_label.setStyleSheet('color: #FFD700; font-size: 10px; min-width: 60px; font-weight: bold;')
        
        # Defer the heavy rebuild so UI can respond immediately
        QTimer.singleShot(50, self._do_refresh_display_deferred)
    
    def _do_refresh_display_deferred(self):
        """Actually rebuild display after UI has processed events"""
        self.refresh_display()
        
        # Update count label to show actual track count
        if self.all_track_data:
            total_count = sum(len(b['day']) + len(b['night']) for b in self.all_track_data)
            self.count_label.setText(f'({total_count} / {total_count})')
            self.count_label.setStyleSheet('color: #b19cd9; font-size: 10px; min-width: 60px;')
        
        QMessageBox.information(self, 'Refreshed', '✓ Display updated')
    
    def _remove_track_and_refresh(self, biome, track_type, track_path):
        """Remove a track and refresh display"""
        print(f'[TRACKS_VIEWER] Removing {track_type} track: {track_path}')
        self.main_window.remove_biome_track(biome, track_type, track_path)
        print(f'[TRACKS_VIEWER] Refreshing display after removal')
        self.refresh_display()
        QMessageBox.information(self, 'Track Removed', f'✓ Removed from {biome[1]}')
    
    def _remove_track_from_search_and_refresh(self, biome, track_type, track_path):
        """Remove a track from search results and refresh the search display"""
        print(f'[TRACKS_VIEWER] Removing {track_type} track from search: {track_path}')
        self.main_window.remove_biome_track(biome, track_type, track_path)
        print(f'[TRACKS_VIEWER] Re-running search after removal')
        # Re-run the current search to update filtered results
        if self.current_search:
            self._run_search(self.current_search)
        else:
            self._display_filtered_results(self.all_track_data, len(self._get_all_tracks()))
        QMessageBox.information(self, 'Track Removed', f'✓ Removed from {biome[1]}')
    
    def _clear_biome_and_refresh(self, biome, track_type):
        """Clear all tracks of a type and refresh display"""
        print(f'[TRACKS_VIEWER] Clearing {track_type} tracks for {biome}')
        self.main_window.clear_biome_tracks(biome, track_type)
        print(f'[TRACKS_VIEWER] Refreshing display after clear')
        self.refresh_display()
        QMessageBox.information(self, 'Tracks Cleared', f'✓ All {track_type} tracks cleared from {biome[1]}')
    
    def _remove_biome_and_refresh(self, biome):
        """Remove biome from selected_biomes and refresh"""
        print(f'[TRACKS_VIEWER] Removing biome from selection: {biome}')
        removed_from_selections = False
        removed_from_add_selections = False
        
        if biome in self.main_window.selected_biomes:
            self.main_window.selected_biomes.remove(biome)
            removed_from_selections = True
            print(f'[TRACKS_VIEWER] Removed from selected_biomes: {biome}')
        
        # Also clean up add_selections for this biome
        if biome in self.main_window.add_selections:
            del self.main_window.add_selections[biome]
            removed_from_add_selections = True
            print(f'[TRACKS_VIEWER] Removed from add_selections: {biome}')
        
        print(f'[TRACKS_VIEWER] Removal summary - selected_biomes: {removed_from_selections}, add_selections: {removed_from_add_selections}')
        
        self.main_window._auto_save_mod_state(f'Removed biome {biome[1]}')
        self.main_window.update_selected_tracks_label()
        self.main_window.update_patch_btn_state()
        print(f'[TRACKS_VIEWER] Biome removed, refreshing display')
        self.refresh_display()
        QMessageBox.information(self, 'Biome Removed', f'✓ {biome[1]} removed from selection')
    
    def _remove_replace_biome_and_refresh(self, biome):
        """Remove biome from replace_selections and refresh"""
        print(f'[TRACKS_VIEWER] Removing biome from replace_selections: {biome}')
        if biome in self.main_window.replace_selections:
            del self.main_window.replace_selections[biome]
            print(f'[TRACKS_VIEWER] Removed from replace_selections: {biome}')
        
        self.main_window._auto_save_mod_state(f'Removed biome {biome[1]} from Replace')
        self.main_window.update_selected_tracks_label()
        self.main_window.update_patch_btn_state()
        print(f'[TRACKS_VIEWER] Biome removed from replace, refreshing display')
        self.refresh_display()
        QMessageBox.information(self, 'Biome Removed', f'✓ {biome[1]} removed from Replace selection')
    
    def _remove_replace_track_and_refresh(self, biome, track_type, track_idx):
        """Remove a specific replacement track (by index) and refresh display"""
        print(f'[TRACKS_VIEWER] Removing {track_type} replacement track at index {track_idx}')
        if biome in self.main_window.replace_selections:
            biome_data = self.main_window.replace_selections[biome]
            if track_type in biome_data and track_idx in biome_data[track_type]:
                del biome_data[track_type][track_idx]
                print(f'[TRACKS_VIEWER] Removed {track_type} replacement at index {track_idx}')
                
                # If both day and night are empty, remove the entire biome
                if not biome_data.get('day') and not biome_data.get('night'):
                    del self.main_window.replace_selections[biome]
                    print(f'[TRACKS_VIEWER] Biome now empty, removing entirely from replace_selections')
        
        self.main_window._auto_save_mod_state(f'Removed replacement track from {biome[1]}')
        self.main_window.update_selected_tracks_label()
        self.main_window.update_patch_btn_state()
        print(f'[TRACKS_VIEWER] Refreshing display after track removal')
        self.refresh_display()
        QMessageBox.information(self, 'Track Removed', f'✓ Removed from {biome[1]} Replace')
    
    def _on_cancel_remove_vanilla(self):
        """Cancel the 'Remove vanilla tracks' setting and refresh display"""
        print(f'[TRACKS_VIEWER] Cancelling Remove Vanilla Tracks')
        self.main_window.remove_vanilla_tracks = False
        # Also uncheck the checkbox on the main window if it exists
        if hasattr(self.main_window, 'remove_vanilla_checkbox'):
            self.main_window.remove_vanilla_checkbox.setChecked(False)
        self.main_window._auto_save_mod_state('Cancelled Remove Vanilla Tracks from View All Tracks')
        self.refresh_display()
    
    def _display_add_tracks_section(self):
        """Display the 'NEW TRACKS WILL BE ADDED' section with all buttons and controls (shared by Both mode and Add mode)"""
        from PyQt5.QtCore import QCoreApplication
        
        add_selections = getattr(self.main_window, 'add_selections', {})
        
        # Add header
        add_header = QLabel('➕ NEW TRACKS WILL BE ADDED')
        add_header.setStyleSheet('color: #99ff99; font-weight: bold; font-size: 13px; margin-bottom: 4px; margin-top: 8px;')
        self.content_layout.addWidget(add_header)
        
        if not add_selections:
            empty_label = QLabel('No tracks selected yet.')
            empty_label.setStyleSheet('color: #b19cd9; font-style: italic; font-size: 11px;')
            empty_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(empty_label)
        else:
            total_tracks = 0
            print(f'[TRACKS_VIEWER] Building Add display for {len(add_selections)} biome(s)')
            
            for (category, biome_name) in sorted(add_selections.keys()):
                biome_data = add_selections[(category, biome_name)]
                day_tracks = biome_data.get('day', [])
                night_tracks = biome_data.get('night', [])
                
                biome_count = len(day_tracks) + len(night_tracks)
                
                print(f'[TRACKS_VIEWER] Add: {category}/{biome_name}: {len(day_tracks)} day, {len(night_tracks)} night')
                
                # Biome header with count and remove button
                biome_header = QHBoxLayout()
                biome_label = QLabel(f'📍 {category.upper()}: {biome_name}')
                biome_label.setStyleSheet('color: #00d4ff; font-weight: bold; font-size: 12px;')
                biome_header.addWidget(biome_label)
                
                count_label = QLabel(f'({biome_count} track{"" if biome_count == 1 else "s"})')
                count_label.setStyleSheet('color: #b19cd9; font-size: 10px;')
                biome_header.addWidget(count_label)
                biome_header.addStretch()
                
                # Add remove biome button
                remove_biome_btn = QPushButton('✕ Remove')
                remove_biome_btn.setFixedWidth(80)
                remove_biome_btn.setStyleSheet('''QPushButton {
                    background-color: #8b3a3a;
                    color: white;
                    font-size: 9px;
                    padding: 2px;
                    border-radius: 3px;
                    border: 1px solid #a04a4a;
                }
                QPushButton:hover {
                    background-color: #a04a4a;
                    border: 1px solid #c05a5a;
                }''')
                remove_biome_btn.setToolTip(f'Remove {biome_name} from selection')
                remove_biome_btn.clicked.connect(partial(self._remove_biome_and_refresh, (category, biome_name)))
                biome_header.addWidget(remove_biome_btn)
                
                self.content_layout.addLayout(biome_header)
                
                # If empty, show message
                if biome_count == 0:
                    empty_msg = QLabel('    (no tracks selected yet)')
                    empty_msg.setStyleSheet('color: #666; font-size: 9px; font-style: italic;')
                    self.content_layout.addWidget(empty_msg)
                else:
                    # Day tracks
                    if day_tracks:
                        print(f'[TRACKS_VIEWER] Adding {len(day_tracks)} day tracks')
                        day_section = QVBoxLayout()
                        day_title = QHBoxLayout()
                        day_label = QLabel(f'  🌅 Day ({len(day_tracks)})')
                        day_label.setStyleSheet('color: #FFD700; font-weight: bold; font-size: 11px;')
                        day_title.addWidget(day_label)
                        day_title.addStretch()
                        
                        clear_btn = QPushButton('Clear All')
                        clear_btn.setFixedWidth(70)
                        clear_btn.setStyleSheet('background-color: #c41e3a; color: white; font-size: 9px; padding: 3px; border-radius: 3px;')
                        clear_btn.clicked.connect(partial(self._clear_biome_and_refresh, (category, biome_name), 'day'))
                        day_title.addWidget(clear_btn)
                        day_section.addLayout(day_title)
                        
                        for idx, track_path in enumerate(day_tracks):
                            track_item = QHBoxLayout()
                            track_name = Path(track_path).name
                            track_label = QLabel(f'    • {track_name}')
                            track_label.setStyleSheet('color: #e6ecff; font-size: 10px;')
                            track_item.addWidget(track_label)
                            track_item.addStretch()
                            
                            delete_btn = QPushButton('✕')
                            delete_btn.setFixedSize(20, 20)
                            delete_btn.setStyleSheet('background-color: #c41e3a; color: white; font-weight: bold; padding: 0px; border-radius: 3px; font-size: 10px;')
                            delete_btn.setToolTip(f'Remove {track_name}')
                            delete_btn.clicked.connect(partial(self._remove_track_and_refresh, (category, biome_name), 'day', track_path))
                            track_item.addWidget(delete_btn)
                            day_section.addLayout(track_item)
                            
                            # Allow UI to respond every 15 widgets
                            if (idx + 1) % 15 == 0:
                                QCoreApplication.processEvents()
                        
                        self.content_layout.addLayout(day_section)
                    
                    # Night tracks
                    if night_tracks:
                        print(f'[TRACKS_VIEWER] Adding {len(night_tracks)} night tracks')
                        night_section = QVBoxLayout()
                        night_title = QHBoxLayout()
                        night_label = QLabel(f'  🌙 Night ({len(night_tracks)})')
                        night_label.setStyleSheet('color: #87CEEB; font-weight: bold; font-size: 11px;')
                        night_title.addWidget(night_label)
                        night_title.addStretch()
                        
                        clear_btn = QPushButton('Clear All')
                        clear_btn.setFixedWidth(70)
                        clear_btn.setStyleSheet('background-color: #c41e3a; color: white; font-size: 9px; padding: 3px; border-radius: 3px;')
                        clear_btn.clicked.connect(partial(self._clear_biome_and_refresh, (category, biome_name), 'night'))
                        night_title.addWidget(clear_btn)
                        night_section.addLayout(night_title)
                        
                        for idx, track_path in enumerate(night_tracks):
                            track_item = QHBoxLayout()
                            track_name = Path(track_path).name
                            track_label = QLabel(f'    • {track_name}')
                            track_label.setStyleSheet('color: #e6ecff; font-size: 10px;')
                            track_item.addWidget(track_label)
                            track_item.addStretch()
                            
                            delete_btn = QPushButton('✕')
                            delete_btn.setFixedSize(20, 20)
                            delete_btn.setStyleSheet('background-color: #c41e3a; color: white; font-weight: bold; padding: 0px; border-radius: 3px; font-size: 10px;')
                            delete_btn.setToolTip(f'Remove {track_name}')
                            delete_btn.clicked.connect(partial(self._remove_track_and_refresh, (category, biome_name), 'night', track_path))
                            track_item.addWidget(delete_btn)
                            night_section.addLayout(track_item)
                            
                            # Allow UI to respond every 15 widgets
                            if (idx + 1) % 15 == 0:
                                QCoreApplication.processEvents()
                        
                        self.content_layout.addLayout(night_section)
                
                self.content_layout.addSpacing(6)
    
    def _display_replace_tracks_section(self):
        """Display the 'TRACKS TO REPLACE' section with vanilla → custom mapping and remove buttons (shared by Both mode and Replace mode)"""
        from utils.patch_generator import get_vanilla_tracks_for_biome
        
        replace_selections = getattr(self.main_window, 'replace_selections', {})
        
        # Add header
        replace_header = QLabel('🔄 TRACKS TO REPLACE')
        replace_header.setStyleSheet('color: #ff9999; font-weight: bold; font-size: 13px; margin-bottom: 4px; margin-top: 8px;')
        self.content_layout.addWidget(replace_header)
        
        if not replace_selections:
            empty_label = QLabel('No tracks to replace.')
            empty_label.setStyleSheet('color: #b19cd9; font-style: italic; font-size: 11px;')
            empty_label.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(empty_label)
        else:
            print(f'[TRACKS_VIEWER] Building Replace display for {len(replace_selections)} biome(s)')
            
            for (category, biome_name) in sorted(replace_selections.keys()):
                biome_data = replace_selections[(category, biome_name)]
                day_replace = biome_data.get('day', {})  # dict of {index: path}
                night_replace = biome_data.get('night', {})  # dict of {index: path}
                
                replace_count = len(day_replace) + len(night_replace)
                
                print(f'[TRACKS_VIEWER] Replace: {category}/{biome_name}: {len(day_replace)} day, {len(night_replace)} night')
                
                # Get vanilla tracks for this biome
                vanilla_data = get_vanilla_tracks_for_biome(category, biome_name)
                day_vanilla = vanilla_data.get('dayTracks', [])
                night_vanilla = vanilla_data.get('nightTracks', [])
                
                # Biome header with Remove button
                biome_header = QHBoxLayout()
                biome_label = QLabel(f'  📍 {category.upper()}: {biome_name}')
                biome_label.setStyleSheet('color: #ffcccc; font-weight: bold; font-size: 11px;')
                biome_header.addWidget(biome_label)
                
                count_label = QLabel(f'({replace_count} replacement{"" if replace_count == 1 else "s"})')
                count_label.setStyleSheet('color: #ff9999; font-size: 9px;')
                biome_header.addWidget(count_label)
                biome_header.addStretch()
                
                # Add Remove biome button
                remove_biome_btn = QPushButton('✕ Remove')
                remove_biome_btn.setFixedWidth(80)
                remove_biome_btn.setStyleSheet('''QPushButton {
                    background-color: #8b3a3a;
                    color: white;
                    font-size: 9px;
                    padding: 2px;
                    border-radius: 3px;
                    border: 1px solid #a04a4a;
                }
                QPushButton:hover {
                    background-color: #a04a4a;
                    border: 1px solid #c05a5a;
                }''')
                remove_biome_btn.setToolTip(f'Remove {biome_name} from Replace selection')
                remove_biome_btn.clicked.connect(partial(self._remove_replace_biome_and_refresh, (category, biome_name)))
                biome_header.addWidget(remove_biome_btn)
                
                self.content_layout.addLayout(biome_header)
                
                # Day replacements
                if day_replace:
                    day_section = QVBoxLayout()
                    day_title = QLabel(f'    🌅 Day ({len(day_replace)})')
                    day_title.setStyleSheet('color: #FFD700; font-size: 10px;')
                    day_section.addWidget(day_title)
                    
                    for idx, track_path in day_replace.items():
                        # Get vanilla track name for this index
                        vanilla_name = Path(day_vanilla[idx]).name if idx < len(day_vanilla) else '?'
                        custom_name = Path(track_path).name
                        
                        track_item = QHBoxLayout()
                        track_label = QLabel(f'      • {vanilla_name} → {custom_name}')
                        track_label.setStyleSheet('color: #e6ecff; font-size: 9px;')
                        track_item.addWidget(track_label)
                        track_item.addStretch()
                        
                        delete_btn = QPushButton('✕')
                        delete_btn.setFixedSize(20, 20)
                        delete_btn.setStyleSheet('background-color: #c41e3a; color: white; font-weight: bold; padding: 0px; border-radius: 3px; font-size: 10px;')
                        delete_btn.setToolTip(f'Remove replacement for {vanilla_name}')
                        delete_btn.clicked.connect(partial(self._remove_replace_track_and_refresh, (category, biome_name), 'day', idx))
                        track_item.addWidget(delete_btn)
                        day_section.addLayout(track_item)
                    
                    self.content_layout.addLayout(day_section)
                
                # Night replacements
                if night_replace:
                    night_section = QVBoxLayout()
                    night_title = QLabel(f'    🌙 Night ({len(night_replace)})')
                    night_title.setStyleSheet('color: #87CEEB; font-size: 10px;')
                    night_section.addWidget(night_title)
                    
                    for idx, track_path in night_replace.items():
                        # Get vanilla track name for this index
                        vanilla_name = Path(night_vanilla[idx]).name if idx < len(night_vanilla) else '?'
                        custom_name = Path(track_path).name
                        
                        track_item = QHBoxLayout()
                        track_label = QLabel(f'      • {vanilla_name} → {custom_name}')
                        track_label.setStyleSheet('color: #e6ecff; font-size: 9px;')
                        track_item.addWidget(track_label)
                        track_item.addStretch()
                        
                        delete_btn = QPushButton('✕')
                        delete_btn.setFixedSize(20, 20)
                        delete_btn.setStyleSheet('background-color: #c41e3a; color: white; font-weight: bold; padding: 0px; border-radius: 3px; font-size: 10px;')
                        delete_btn.setToolTip(f'Remove replacement for {vanilla_name}')
                        delete_btn.clicked.connect(partial(self._remove_replace_track_and_refresh, (category, biome_name), 'night', idx))
                        track_item.addWidget(delete_btn)
                        night_section.addLayout(track_item)
                    
                    self.content_layout.addLayout(night_section)
                
                self.content_layout.addSpacing(6)

    def refresh_display(self):
        """Rebuild the tracks display"""
        try:
            print(f'[TRACKS_VIEWER] refresh_display() called')
            
            # Import for process events
            from PyQt5.QtCore import QCoreApplication
            
            # Disable updates while building - prevents visual artifacts/bleeding
            self.setUpdatesEnabled(False)
            
            # Scroll to top before clearing and rebuilding
            self.scroll_area.verticalScrollBar().setValue(0)
            
            # Clear old widgets from content_layout (recursive helper)
            def clear_all_layouts(layout):
                """Recursively clear all widgets and nested layouts"""
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        widget = item.widget()
                        widget.deleteLater()
                    elif item.layout():
                        clear_all_layouts(item.layout())
                        
            clear_all_layouts(self.content_layout)
            
            # Allow Qt to process user events (responsive UI) but don't redraw yet
            QCoreApplication.processEvents()
            
            # Clear search to show all tracks again
            self.search_input.blockSignals(True)
            self.search_input.clear()
            self.search_input.blockSignals(False)
            self.current_search = ''
            
            # Reset track data
            self.all_track_data = []
            
            # Check if we're in Both mode
            patch_mode = getattr(self.main_window, 'patch_mode', 'add')
            replace_selections = getattr(self.main_window, 'replace_selections', {})
            add_selections = getattr(self.main_window, 'add_selections', {})
            
            print(f'[TRACKS_VIEWER] patch_mode={patch_mode}, replace_selections={len(replace_selections)}, add_selections={len(add_selections)}')
            
            # 🆕 BOTH MODE: Show REPLACE tracks first, then ADD tracks
            if patch_mode == 'both' and replace_selections:
                print(f'[TRACKS_VIEWER] Both mode detected - showing Replace + Add tracks')
                
                # SECTION 1: TRACKS TO REPLACE (use shared method)
                self._display_replace_tracks_section()
                
                # SECTION 2: NEW TRACKS WILL BE ADDED (use shared method)
                self._display_add_tracks_section()
            
            # STANDARD MODE: Show ADD tracks only (Add or Replace mode)
            else:
                print(f'[TRACKS_VIEWER] Standard mode - showing Add tracks only')
                
                # 🆕 REPLACE MODE: Show TRACKS TO REPLACE
                if patch_mode == 'replace' and replace_selections:
                    print(f'[TRACKS_VIEWER] Replace mode detected - showing Replace tracks')
                    
                    # Use shared helper method for Replace tracks display
                    self._display_replace_tracks_section()
                
                # 🆕 Check if Remove Vanilla Tracks is enabled (Add mode only)
                remove_vanilla = getattr(self.main_window, 'remove_vanilla_tracks', False)
                selected_biomes = getattr(self.main_window, 'selected_biomes', [])
                
                if patch_mode == 'add' and remove_vanilla and selected_biomes:
                    # Show TRACKS REMOVED section with Cancel button
                    print(f'[TRACKS_VIEWER] Remove vanilla tracks enabled - showing removed tracks')
                    
                    # Header with title and cancel button
                    remove_header_layout = QHBoxLayout()
                    remove_header_label = QLabel('🗑️ VANILLA TRACKS WILL BE REMOVED (100% of your music guaranteed)')
                    remove_header_label.setStyleSheet('color: #ff9999; font-weight: bold; font-size: 13px;')
                    remove_header_label.setToolTip('Remove Mode: ONLY your custom music will play. ⚠️ Can conflict with other REPLACE-based music mods.')
                    remove_header_layout.addWidget(remove_header_label)
                    remove_header_layout.addStretch()
                    
                    cancel_remove_btn = QPushButton('✕ Cancel Remove')
                    cancel_remove_btn.setFixedWidth(100)
                    cancel_remove_btn.setStyleSheet('''QPushButton {
                        background-color: #8b3a3a;
                        color: white;
                        font-size: 9px;
                        padding: 3px;
                        border-radius: 3px;
                        border: 1px solid #a04a4a;
                    }
                    QPushButton:hover {
                        background-color: #a04a4a;
                        border: 1px solid #c05a5a;
                    }''')
                    cancel_remove_btn.setToolTip('Disable removing vanilla tracks')
                    cancel_remove_btn.clicked.connect(self._on_cancel_remove_vanilla)
                    remove_header_layout.addWidget(cancel_remove_btn)
                    
                    self.content_layout.addLayout(remove_header_layout)
                    
                    from utils.patch_generator import get_vanilla_tracks_for_biome
                    
                    for (category, biome_name) in sorted(selected_biomes):
                        vanilla_data = get_vanilla_tracks_for_biome(category, biome_name)
                        day_vanilla = vanilla_data.get('dayTracks', [])
                        night_vanilla = vanilla_data.get('nightTracks', [])
                        
                        vanilla_count = len(day_vanilla) + len(night_vanilla)
                        
                        if vanilla_count > 0:
                            print(f'[TRACKS_VIEWER] Remove: {category}/{biome_name}: {len(day_vanilla)} day, {len(night_vanilla)} night')
                            
                            # Biome header
                            biome_header = QHBoxLayout()
                            biome_label = QLabel(f'  📍 {category.upper()}: {biome_name}')
                            biome_label.setStyleSheet('color: #ffcccc; font-weight: bold; font-size: 11px;')
                            biome_header.addWidget(biome_label)
                            
                            count_label = QLabel(f'({vanilla_count} removal{"" if vanilla_count == 1 else "s"})')
                            count_label.setStyleSheet('color: #ff9999; font-size: 9px;')
                            biome_header.addWidget(count_label)
                            biome_header.addStretch()
                            
                            self.content_layout.addLayout(biome_header)
                            
                            # Day vanilla tracks
                            if day_vanilla:
                                day_section = QVBoxLayout()
                                day_title = QLabel(f'    🌅 Day ({len(day_vanilla)})')
                                day_title.setStyleSheet('color: #FFD700; font-size: 10px;')
                                day_section.addWidget(day_title)
                                
                                for track_path in day_vanilla:
                                    track_name = Path(track_path).name
                                    track_label = QLabel(f'      • {track_name}')
                                    track_label.setStyleSheet('color: #e6ecff; font-size: 9px;')
                                    day_section.addWidget(track_label)
                                
                                self.content_layout.addLayout(day_section)
                            
                            # Night vanilla tracks
                            if night_vanilla:
                                night_section = QVBoxLayout()
                                night_title = QLabel(f'    🌙 Night ({len(night_vanilla)})')
                                night_title.setStyleSheet('color: #87CEEB; font-size: 10px;')
                                night_section.addWidget(night_title)
                                
                                for track_path in night_vanilla:
                                    track_name = Path(track_path).name
                                    track_label = QLabel(f'      • {track_name}')
                                    track_label.setStyleSheet('color: #e6ecff; font-size: 9px;')
                                    night_section.addWidget(track_label)
                                
                                self.content_layout.addLayout(night_section)
                            
                            self.content_layout.addSpacing(6)
                    
                    # Add separator before ADD tracks
                    separator = QLabel('')
                    separator.setStyleSheet('border-top: 1px solid #3a4a6a; margin: 12px 0px;')
                    self.content_layout.addWidget(separator)
                    
                if patch_mode == 'replace':
                    # In Replace mode, show ADD header only if there are Add selections
                    if add_selections:
                        self._display_add_tracks_section()
                else:
                    # In Add mode, always show ADD header and tracks
                    self._display_add_tracks_section()
            
            # 🆕 Collect track data for search (after building full display)
            self._collect_track_data()
            
            # Add stretch at end to push content to top (prevents floating blank space)
            self.content_layout.addStretch()
            
            # Re-enable updates and redraw the completed display
            self.setUpdatesEnabled(True)
            self.update()  # Force full redraw now that we're done
            
            # Scroll to top to ensure clean display
            self.scroll_area.verticalScrollBar().setValue(0)
        except Exception as e:
            import traceback
            print(f'[TRACKS_VIEWER] Error in refresh_display: {e}')
            traceback.print_exc()
    
    def _collect_track_data(self):
        """Collect all track data for search filtering"""
        self.all_track_data = []
        self.search_index = []  # Rebuild lightweight index for searching
        
        patch_mode = getattr(self.main_window, 'patch_mode', 'add')
        replace_selections = getattr(self.main_window, 'replace_selections', {})
        add_selections = getattr(self.main_window, 'add_selections', {})
        
        # Collect Replace tracks (in Both mode)
        for biome in sorted(replace_selections.keys()):
            data = replace_selections[biome]
            biome_data = {
                'biome': biome,
                'day': data.get('day', {}),
                'night': data.get('night', {}),
                'is_replace': True
            }
            self.all_track_data.append(biome_data)
            
            # Add to search index
            category, biome_name = biome
            biome_text = f'{category} {biome_name}'.lower()
            index_entry = {
                'biome': biome,
                'biome_text': biome_text,
                'tracks': []
            }
            
            # Index day tracks
            for idx, path in data.get('day', {}).items():
                track_name = Path(str(path)).name.lower()
                index_entry['tracks'].append((track_name, path, True, True, idx))
            
            # Index night tracks
            for idx, path in data.get('night', {}).items():
                track_name = Path(str(path)).name.lower()
                index_entry['tracks'].append((track_name, path, False, True, idx))
            
            if index_entry['tracks']:
                self.search_index.append(index_entry)
        
        # Collect Add tracks (in both Add and Both mode)
        for biome in sorted(add_selections.keys()):
            data = add_selections[biome]
            biome_data = {
                'biome': biome,
                'day': data.get('day', []),
                'night': data.get('night', []),
                'is_replace': False
            }
            self.all_track_data.append(biome_data)
            
            # Add to search index
            category, biome_name = biome
            biome_text = f'{category} {biome_name}'.lower()
            index_entry = {
                'biome': biome,
                'biome_text': biome_text,
                'tracks': []
            }
            
            # Index day tracks
            for path in data.get('day', []):
                track_name = Path(str(path)).name.lower()
                index_entry['tracks'].append((track_name, path, True, False, None))
            
            # Index night tracks
            for path in data.get('night', []):
                track_name = Path(str(path)).name.lower()
                index_entry['tracks'].append((track_name, path, False, False, None))
            
            if index_entry['tracks']:
                self.search_index.append(index_entry)
    
    def _display_filtered_results(self, filtered_data, total_count):
        """Display the pre-filtered search results (called from worker thread)"""
        # Scroll to top before clearing and rebuilding
        self.scroll_area.verticalScrollBar().setValue(0)
        
        # Disable updates while building to keep UI responsive
        self.setUpdatesEnabled(False)
        
        # Clear old widgets (recursive helper)
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    clear_layout(item.layout())
        
        clear_layout(self.content_layout)
        
        total_visible = 0
        
        # Process each biome's tracks
        for biome_data in filtered_data:
            biome = biome_data['biome']
            category, biome_name = biome
            is_replace = biome_data['is_replace']
            day_data = biome_data['day']
            night_data = biome_data['night']
            
            # Count total tracks for this biome
            day_count = len(day_data)
            night_count = len(night_data)
            biome_total = day_count + night_count
            
            if biome_total == 0:
                continue  # Skip empty biomes
            
            # Display biome header
            biome_header = QHBoxLayout()
            biome_label = QLabel(f'  📍 {category.upper()}: {biome_name}')
            biome_label.setStyleSheet('color: #ccffcc; font-weight: bold; font-size: 11px;')
            biome_header.addWidget(biome_label)
            
            count_label = QLabel(f'({biome_total} track{"" if biome_total == 1 else "s"})')
            count_label.setStyleSheet('color: #99ff99; font-size: 9px;')
            biome_header.addWidget(count_label)
            biome_header.addStretch()
            
            self.content_layout.addLayout(biome_header)
            
            # Display day tracks
            if day_data:
                day_section = QVBoxLayout()
                day_title = QLabel(f'    🌅 Day')
                day_title.setStyleSheet('color: #FFD700; font-size: 10px;')
                day_section.addWidget(day_title)
                
                for idx, (key, track_path) in enumerate(day_data.items() if is_replace else enumerate(day_data)):
                    track_name = Path(str(track_path)).name
                    label_text = f'      • [{key}] {track_name}' if is_replace else f'      • {track_name}'
                    
                    # Create horizontal layout for track with delete button
                    track_row = QHBoxLayout()
                    track_row.setContentsMargins(0, 0, 0, 0)
                    track_row.setSpacing(4)
                    
                    track_label = QLabel(label_text)
                    track_label.setStyleSheet('color: #e6ecff; font-size: 9px;')
                    track_row.addWidget(track_label)
                    track_row.addStretch()
                    
                    # Add delete button for this track
                    delete_btn = QPushButton('✕')
                    delete_btn.setStyleSheet('background-color: #8B0000; color: white; border: none; font-size: 8px; padding: 1px 4px; border-radius: 2px;')
                    delete_btn.setFixedSize(16, 16)
                    delete_btn.setCursor(Qt.PointingHandCursor)
                    delete_btn.clicked.connect(lambda checked=False, b=biome, t='day', p=track_path: self._remove_track_from_search_and_refresh(b, t, p))
                    track_row.addWidget(delete_btn)
                    
                    day_section.addLayout(track_row)
                    total_visible += 1
                    
                    # Allow UI to respond every 15 widgets
                    if (idx + 1) % 15 == 0:
                        QCoreApplication.processEvents()
                
                self.content_layout.addLayout(day_section)
            
            # Display night tracks
            if night_data:
                night_section = QVBoxLayout()
                night_title = QLabel(f'    🌙 Night')
                night_title.setStyleSheet('color: #87CEEB; font-size: 10px;')
                night_section.addWidget(night_title)
                
                for idx, (key, track_path) in enumerate(night_data.items() if is_replace else enumerate(night_data)):
                    track_name = Path(str(track_path)).name
                    label_text = f'      • [{key}] {track_name}' if is_replace else f'      • {track_name}'
                    
                    # Create horizontal layout for track with delete button
                    track_row = QHBoxLayout()
                    track_row.setContentsMargins(0, 0, 0, 0)
                    track_row.setSpacing(4)
                    
                    track_label = QLabel(label_text)
                    track_label.setStyleSheet('color: #e6ecff; font-size: 9px;')
                    track_row.addWidget(track_label)
                    track_row.addStretch()
                    
                    # Add delete button for this track
                    delete_btn = QPushButton('✕')
                    delete_btn.setStyleSheet('background-color: #8B0000; color: white; border: none; font-size: 8px; padding: 1px 4px; border-radius: 2px;')
                    delete_btn.setFixedSize(16, 16)
                    delete_btn.setCursor(Qt.PointingHandCursor)
                    delete_btn.clicked.connect(lambda checked=False, b=biome, t='night', p=track_path: self._remove_track_from_search_and_refresh(b, t, p))
                    track_row.addWidget(delete_btn)
                    
                    night_section.addLayout(track_row)
                    total_visible += 1
                    
                    # Allow UI to respond every 15 widgets
                    if (idx + 1) % 15 == 0:
                        QCoreApplication.processEvents()
                
                self.content_layout.addLayout(night_section)
            
            self.content_layout.addSpacing(6)
        
        self.content_layout.addStretch()
        
        # Re-enable updates and redraw
        self.setUpdatesEnabled(True)
        self.update()
        
        # Update count display
        if self.current_search:
            self.count_label.setText(f'({total_visible} / {total_count})')
            self.count_label.setStyleSheet('color: #FFD700; font-size: 10px; min-width: 60px; font-weight: bold;')
        else:
            self.count_label.setText(f'({total_visible} / {total_count})')
            self.count_label.setStyleSheet('color: #b19cd9; font-size: 10px; min-width: 60px;')


# Worker class for threaded patch generation
class PatchGenerationWorker(QThread):
    """Background worker for patch generation - keeps UI responsive"""
    progress_update = pyqtSignal(str)  # Status message updates
    generation_complete = pyqtSignal(dict)  # Results when done: {success, results, error_msg}
    
    def __init__(self, main_window, mod_name, format_choice):
        super().__init__()
        self.main_window = main_window
        self.mod_name = mod_name
        self.format_choice = format_choice
    
    def run(self):
        """Execute patch generation in background thread"""
        try:
            self.progress_update.emit('🔧 Preparing patch generation...')
            
            # Call the actual generation logic (this is mostly the original function)
            result = self._do_generation()
            
            self.generation_complete.emit({
                'success': result.get('success', False),
                'results': result.get('patch_results', []),
                'error_msg': result.get('error', None)
            })
        except Exception as e:
            print(f'[PATCH_WORKER] Error during generation: {e}')
            import traceback
            traceback.print_exc()
            self.generation_complete.emit({
                'success': False,
                'results': [],
                'error_msg': str(e)
            })
    
    def _do_generation(self):
        """The actual patch generation logic (moved from main thread)"""
        # This is the core of generate_patch_file() but returns a dict instead of updating UI
        try:
            import shutil
            from utils.patch_generator import generate_patch
            from utils.atomicwriter import create_mod_folder_structure
            
            mod_name = self.mod_name
            biomes = getattr(self.main_window, 'selected_biomes', [])
            patch_mode = getattr(self.main_window, 'patch_mode', 'add')
            replace_selections = getattr(self.main_window, 'replace_selections', {})
            add_selections = getattr(self.main_window, 'add_selections', {})
            day_tracks = getattr(self.main_window, 'day_tracks', [])
            night_tracks = getattr(self.main_window, 'night_tracks', [])
            remove_vanilla_tracks = getattr(self.main_window, 'remove_vanilla_tracks', False)
            
            # Construct mod_path once and clear old patches before regeneration
            starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
            staging_dir = starsound_dir / 'staging'
            safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
            mod_path = staging_dir / safe_mod_name
            
            # ✅ CRITICAL: Create mod folder structure with _metadata and required directories
            self.progress_update.emit('📁 Creating mod folder structure...')
            create_mod_folder_structure(staging_dir, safe_mod_name)
            self.main_window.logger.log(f'Created mod folder structure for: {safe_mod_name}', context='PatchGen')
            
            # Clear old biomes folder to prevent patches from previous generations contaminating new ones
            biomes_folder = mod_path / 'biomes'
            if biomes_folder.exists():
                try:
                    shutil.rmtree(biomes_folder)
                    self.main_window.logger.log('Cleared old biomes folder for fresh generation', context='PatchGen')
                except Exception as e:
                    self.main_window.logger.warn(f'Could not clear old biomes folder: {e}')
            
            # Also clear any stray .patch files in the mod root (shouldn't be there, but just in case)
            try:
                for patch_file in mod_path.glob('*.patch'):
                    patch_file.unlink()
                    self.main_window.logger.log(f'Removed stray patch file: {patch_file.name}', context='PatchGen')
            except Exception as e:
                self.main_window.logger.warn(f'Could not clear stray patch files: {e}')
            
            patch_results = []
            
            # CASE A: Replace mode with individual selections
            if patch_mode == 'replace' and replace_selections:
                self.progress_update.emit(f'🔧 Processing {len(biomes)} biome(s) in Replace mode...')
                
                for idx, (biome_category, biome_name) in enumerate(biomes, 1):
                    self.progress_update.emit(f'🔧 Patching {biome_name} ({idx}/{len(biomes)})...')
                    
                    selections = replace_selections.get((biome_category, biome_name), {})
                    if not selections:
                        continue
                    
                    config = {
                        'biome': biome_name,
                        'biome_category': biome_category,
                        'modName': mod_name,
                        'patchMode': patch_mode
                    }
                    
                    result = generate_patch(str(mod_path), config, replace_selections=selections, logger=self.main_window.logger)
                    patch_results.append(result)
            
            # CASE B: Both mode
            elif patch_mode == 'both' and replace_selections:
                self.progress_update.emit(f'🔧 Processing {len(biomes)} biome(s) in Both mode...')
                
                both_mode_biomes = set(biomes) | set(replace_selections.keys())
                
                for idx, (biome_category, biome_name) in enumerate(sorted(both_mode_biomes), 1):
                    self.progress_update.emit(f'🔧 Patching {biome_name} ({idx}/{len(both_mode_biomes)})...')
                    
                    replace_sel = replace_selections.get((biome_category, biome_name), {})
                    add_sel = add_selections.get((biome_category, biome_name), {'day': [], 'night': []})
                    day_add_tracks = add_sel.get('day', [])
                    night_add_tracks = add_sel.get('night', [])
                    
                    if not day_add_tracks and not night_add_tracks:
                        day_add_tracks = day_tracks
                        night_add_tracks = night_tracks
                    
                    if not replace_sel:
                        if not (day_add_tracks or night_add_tracks):
                            continue
                    
                    config = {
                        'biome': biome_name,
                        'biome_category': biome_category,
                        'dayTracks': day_add_tracks,
                        'nightTracks': night_add_tracks,
                        'modName': mod_name,
                        'patchMode': 'both'
                    }
                    
                    result = generate_patch(str(mod_path), config, replace_selections=replace_sel, logger=self.main_window.logger)
                    patch_results.append(result)
            
            # CASE C: Standard Add/Replace
            else:
                self.progress_update.emit(f'🔧 Processing {len(biomes)} biome(s) in Add mode...')
                
                has_add_selections = bool(add_selections)
                
                for idx, (biome_category, biome_name) in enumerate(biomes, 1):
                    self.progress_update.emit(f'🔧 Patching {biome_name} ({idx}/{len(biomes)})...')
                    
                    if has_add_selections:
                        biome_key = (biome_category, biome_name)
                        biome_tracks = add_selections.get(biome_key, {'day': [], 'night': []})
                        day_biome_tracks = biome_tracks.get('day', [])
                        night_biome_tracks = biome_tracks.get('night', [])
                        
                        if not day_biome_tracks and not night_biome_tracks:
                            continue
                        
                        config = {
                            'biome': biome_name,
                            'biome_category': biome_category,
                            'dayTracks': day_biome_tracks,
                            'nightTracks': night_biome_tracks,
                            'modName': mod_name,
                            'patchMode': patch_mode,
                            'trackType': 'Both',
                            'remove_vanilla_tracks': remove_vanilla_tracks
                        }
                    else:
                        config = {
                            'biome': biome_name,
                            'biome_category': biome_category,
                            'dayTracks': day_tracks,
                            'nightTracks': night_tracks,
                            'modName': mod_name,
                            'patchMode': patch_mode,
                            'trackType': 'Both',
                            'remove_vanilla_tracks': remove_vanilla_tracks
                        }
                    
                    result = generate_patch(str(mod_path), config, logger=self.main_window.logger)
                    patch_results.append(result)
            
            self.progress_update.emit('✅ Generation complete!')
            
            # Clean up old backups folder in staging (if it exists)
            # All backups are now at root-level StarSound/backups/
            try:
                old_backups_path = mod_path / 'backups'
                if old_backups_path.exists():
                    import shutil
                    shutil.rmtree(old_backups_path)
                    self.main_window.logger.log(f'Cleaned up old backups folder from staging: {old_backups_path}')
            except Exception as e:
                self.main_window.logger.warn(f'Could not clean up old backups folder: {e}')
            
            return {
                'success': all(r.get('success') for r in patch_results) if patch_results else False,
                'patch_results': patch_results,
                'error': None
            }
        
        except Exception as e:
            return {
                'success': False,
                'patch_results': [],
                'error': str(e)
            }


# Worker class for mod export/installation
class ExportWorker(QThread):
    """Background worker for mod export to Starbound mods folder"""
    progress_update = pyqtSignal(dict)  # {message: str, percentage: int}
    export_complete = pyqtSignal(dict)  # Results: {success, message, installed_path, error_msg}
    
    def __init__(self, main_window, mod_name, use_pak):
        super().__init__()
        self.main_window = main_window
        self.mod_name = mod_name
        self.use_pak = use_pak
    
    def run(self):
        """Execute mod export in background thread"""
        try:
            self.progress_update.emit({'message': '📦 Finding Starbound installation...', 'percentage': 10})
            result = self._do_export()
            self.export_complete.emit(result)
        except Exception as e:
            print(f'[EXPORT_WORKER] Error during export: {e}')
            import traceback
            traceback.print_exc()
            self.export_complete.emit({
                'success': False,
                'message': '',
                'installed_path': '',
                'error_msg': str(e)
            })
    
    def _do_export(self):
        """The actual export logic"""
        try:
            from utils.starbound_locator import find_starbound_folder
            from utils.mod_exporter import export_mod_loose, export_mod_pak
            import shutil
            
            self.progress_update.emit({'message': '📂 Preparing mod files...', 'percentage': 15})
            
            # Locate staging and Starbound
            starsound_dir = Path(os.path.dirname(os.path.dirname(__file__)))
            staging_dir = starsound_dir / 'staging'
            safe_mod_name = "".join(c for c in self.mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
            staging_mod_path = staging_dir / safe_mod_name
            
            # Count total files for informational purposes
            total_files = sum(1 for _ in staging_mod_path.rglob('*') if _.is_file())
            
            self.progress_update.emit({'message': f'📊 {total_files} files to copy...', 'percentage': 25})
            
            # Find Starbound installation
            self.progress_update.emit({'message': '🔍 Locating Starbound installation...', 'percentage': 35})
            starbound_path = find_starbound_folder()
            if not starbound_path:
                return {
                    'success': False,
                    'message': 'Could not find Starbound installation',
                    'installed_path': '',
                    'error_msg': 'Starbound folder not found'
                }
            
            starbound_mods_path = Path(starbound_path) / 'mods'
            starbound_mods_path.mkdir(parents=True, exist_ok=True)
            
            self.progress_update.emit({'message': f'📁 Destination: {starbound_mods_path}', 'percentage': 45})
            
            # Export based on format selection
            self.progress_update.emit({'message': f'💾 Starting mod export ({total_files} files)...', 'percentage': 55})
            
            if self.use_pak:
                success, message, installed_path = export_mod_pak(
                    staging_mod_path,
                    starbound_mods_path,
                    Path(starbound_path),
                    logger=self.main_window.logger
                )
            else:
                # For loose export, do copying manually so we can track each file
                success = True
                installed_path = str(starbound_mods_path / safe_mod_name)
                message = f'Mod installed to: {installed_path}'
                
                try:
                    target_mod_path = Path(installed_path)
                    
                    # Delete existing mod folder to ensure clean installation (no old patches remain)
                    if target_mod_path.exists():
                        self.progress_update.emit({
                            'message': f'🗑️  Removing old mod version...',
                            'percentage': 57
                        })
                        import shutil
                        shutil.rmtree(target_mod_path)
                        self.main_window.logger.log(f'Deleted existing mod folder for clean reinstall: {target_mod_path}')
                    
                    target_mod_path.mkdir(parents=True, exist_ok=True)
                    
                    # Copy files and track progress
                    files_copied = 0
                    for src_file in staging_mod_path.rglob('*'):
                        if src_file.is_file():
                            files_copied += 1
                            # Calculate relative path for display
                            rel_path = src_file.relative_to(staging_mod_path)
                            file_name = src_file.name
                            
                            # Emit per-file progress
                            percentage = int(60 + (files_copied / max(total_files, 1)) * 30)  # 60-90%
                            self.progress_update.emit({
                                'message': f'📋 Copying: {file_name} ({files_copied}/{total_files})',
                                'percentage': percentage
                            })
                            
                            # Copy file
                            dst_file = target_mod_path / rel_path
                            dst_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_file, dst_file)
                    
                except Exception as e:
                    success = False
                    message = f'Failed to copy files: {e}'
                    installed_path = ''
            
            self.progress_update.emit({'message': '⏳ Finalizing installation...', 'percentage': 90})
            
            if success:
                self.progress_update.emit({'message': '✅ Installation complete!', 'percentage': 100})
            
            return {
                'success': success,
                'message': message,
                'installed_path': installed_path,
                'error_msg': None if success else message
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': '',
                'installed_path': '',
                'error_msg': str(e)
            }


if __name__ == '__main__':
    import atexit
    import traceback
    
    try:
        app = QApplication(sys.argv)
        # Apply centralized stylesheet based on UI_STYLE_GUIDE
        apply_global_stylesheet(app)
        window = MainWindow()
        window.show()
        def log_exit():
            try:
                window.logger.log('App exited')
            except Exception:
                pass
        atexit.register(log_exit)
        sys.exit(app.exec_())
    except Exception as e:
        # Display error dialog even if everything is broken
        print(f"CRITICAL ERROR at startup:\n{e}")
        print(f"\nFull traceback:\n{traceback.format_exc()}")
        
        # Try to show error in message box
        try:
            error_app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
            QMessageBox.critical(
                None,
                '❌ StarSound Startup Error',
                f'StarSound encountered a critical error and cannot start:\n\n{str(e)}\n\n'
                f'Please check the console output for more details, or contact support.\n\n'
                f'Error details:\n{traceback.format_exc()}'
            )
        except Exception as msg_err:
            print(f"Could not show error dialog: {msg_err}")
        
        sys.exit(1)


# SearchFilterWorker - background thread for fast track searching
class SearchFilterWorker(QThread):
    """Background worker for filtering tracks - keeps UI responsive during search"""
    filter_complete = pyqtSignal(list, int)  # Emits (filtered_data, total_count)
    
    def __init__(self, search_index, query):
        super().__init__()
        self.search_index = search_index  # Lightweight index of all tracks
        self.query = query.lower().strip()  # Search query
    
    def run(self):
        """Execute search in background thread"""
        try:
            if not self.query:
                # No search - return all data
                filtered_data = []
                total_count = 0
                # This shouldn't happen (called from UI), but handle it
                self.filter_complete.emit([], 0)
                return
            
            # Fast search through lightweight index
            filtered_data = []
            total_count = sum(len(entry['tracks']) for entry in self.search_index)
            
            for index_entry in self.search_index:
                biome = index_entry['biome']
                biome_text = index_entry['biome_text']
                
                # Check if biome matches
                biome_matches = self.query in biome_text
                
                # Collect matching tracks
                day_dict = {}
                night_dict = {}
                day_list = []
                night_list = []
                is_replace = None
                
                for track_name, track_path, is_day, is_replace_mode, key_idx in index_entry['tracks']:
                    # Track matches if biome matches OR track name matches
                    if biome_matches or self.query in track_name:
                        is_replace = is_replace_mode
                        
                        if is_replace_mode:
                            # Replace mode: store as dict with index
                            if is_day:
                                day_dict[key_idx] = track_path
                            else:
                                night_dict[key_idx] = track_path
                        else:
                            # Add mode: store as list
                            if is_day:
                                day_list.append(track_path)
                            else:
                                night_list.append(track_path)
                
                # Only include biome if it has matching tracks
                if day_dict or night_dict or day_list or night_list:
                    filtered_data.append({
                        'biome': biome,
                        'day': day_dict if is_replace else day_list,
                        'night': night_dict if is_replace else night_list,
                        'is_replace': is_replace
                    })
            
            # Calculate total visible (only matching tracks)
            total_visible = sum(
                len(d['day']) + len(d['night']) 
                for d in filtered_data
            )
            
            # Emit results
            self.filter_complete.emit(filtered_data, total_count)
        
        except Exception as e:
            print(f'[SEARCH_ERROR] Error in search filter: {e}')
            import traceback
            traceback.print_exc()




sys.exit(app.exec_())
