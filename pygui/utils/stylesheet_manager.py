"""
Centralized stylesheet manager for StarSound UI consistency.

This module applies the UI_STYLE_GUIDE standards across the entire application.
All button styles, colors, fonts, and UI element styling is defined HERE.

Source of truth: See UI_STYLE_GUIDE.md for design specifications.

Usage:
    from utils.stylesheet_manager import apply_global_stylesheet
    app = QApplication(sys.argv)
    apply_global_stylesheet(app)
"""

from PyQt5.QtWidgets import QApplication


def apply_global_stylesheet(app: QApplication) -> None:
    """
    Apply comprehensive stylesheet to entire application.
    
    This ensures ALL UI elements follow UI_STYLE_GUIDE standards:
    - Dialog backgrounds (#1a1f2e)
    - Primary text (#e6ecff)
    - All button styles with hover effects
    - Input field styling
    - ComboBox/dropdown styling
    - Proper spacing and borders
    """
    
    stylesheet = """
    /* ======================
       DIALOG & MAIN WINDOWS
       ====================== */
    QDialog, QMainWindow {
        background-color: #1a1f2e;
    }
    
    /* ======================
       TEXT ELEMENTS
       ====================== */
    QLabel {
        color: #e6ecff;
    }
    
    /* ======================
       PRIMARY ACTION BUTTONS
       (default main action style)
       ====================== */
    QPushButton {
        background-color: #3a6ea5;
        color: #e6ecff;
        border: 1px solid #4e8cff;
        border-radius: 8px;
        padding: 6px 18px;
        font-size: 13px;
        font-family: "Hobo", "Arial";
    }
    
    QPushButton:hover {
        background-color: #4e8cff;
        border: 1px solid #6bbcff;
    }
    
    QPushButton:pressed {
        background-color: #3a5a95;
    }
    
    /* ======================
       INPUT FIELDS
       ====================== */
    QLineEdit {
        background-color: #283046;
        color: #e6ecff;
        border: 1px solid #3a4a6a;
        border-radius: 4px;
        padding: 4px;
        font-size: 12px;
    }
    
    QLineEdit:focus {
        border: 1px solid #5a8ed5;
    }
    
    /* ======================
       COMBOBOX / DROPDOWNS
       ====================== */
    QComboBox {
        background-color: #283046;
        color: #e6ecff;
        border: 1px solid #3a4a6a;
        border-radius: 4px;
        padding: 4px;
        font-size: 12px;
    }
    
    QComboBox:focus {
        border: 1px solid #5a8ed5;
    }
    
    QComboBox::drop-down {
        border: none;
        background: transparent;
    }
    
    QComboBox QAbstractItemView {
        background-color: #283046;
        color: #e6ecff;
        selection-background-color: #3a4a6a;
        border: 1px solid #3a4a6a;
    }
    
    /* ======================
       CHECKBOXES & RADIO BUTTONS
       ====================== */
    QCheckBox, QRadioButton {
        color: #e6ecff;
        spacing: 6px;
    }
    
    QCheckBox::indicator, QRadioButton::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #3a4a6a;
        border-radius: 3px;
        background-color: #283046;
    }
    
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {
        background-color: #4e8cff;
        border: 1px solid #6bbcff;
    }
    
    /* ======================
       SCROLLBARS
       ====================== */
    QScrollBar:vertical {
        width: 14px;
        background: #0f1620;
        border-radius: 7px;
        margin: 0px;
    }
    
    QScrollBar::handle:vertical {
        background: #3a6ea5;
        border-radius: 7px;
        min-height: 15px;
        margin: 2px 2px 2px 2px;
    }
    
    QScrollBar::handle:vertical:hover {
        background: #5a8ed5;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        border: none;
    }
    
    /* ======================
       TEXT EDIT & TEXT BROWSER
       ====================== */
    QTextEdit, QPlainTextEdit {
        background-color: #181c2a;
        color: #e6ecff;
        border: 1px solid #3a4a6a;
        border-radius: 6px;
        padding: 4px;
        font-size: 12px;
    }
    
    QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #5a8ed5;
    }
    
    /* ======================
       MENUS & MENUBAR
       ====================== */
    QMenuBar {
        background-color: #1a1f2e;
        color: #e6ecff;
        border-bottom: 1px solid #3a4a6a;
    }
    
    QMenuBar::item:selected {
        background-color: #3a4a6a;
    }
    
    QMenu {
        background-color: #1a1f2e;
        color: #e6ecff;
        border: 1px solid #3a4a6a;
    }
    
    QMenu::item:selected {
        background-color: #3a4a6a;
    }
    
    /* ======================
       TOOLBAR & TOOLBAR BUTTONS
       ====================== */
    QToolBar {
        background-color: #1a1f2e;
        border-bottom: 1px solid #3a4a6a;
        spacing: 6px;
    }
    
    QToolButton {
        background-color: transparent;
        color: #e6ecff;
        padding: 4px;
        border: none;
        border-radius: 4px;
    }
    
    QToolButton:hover {
        background-color: #3a4a6a;
        border-radius: 4px;
    }
    
    QToolButton:pressed {
        background-color: #2a3a5a;
    }
    
    /* ======================
       LIST WIDGET
       ====================== */
    QListWidget {
        background-color: #283046;
        color: #e6ecff;
        border: 1px solid #3a4a6a;
        border-radius: 4px;
    }
    
    QListWidget::item:selected {
        background-color: #3a4a6a;
        border-left: 2px solid #4e8cff;
    }
    
    QListWidget::item:hover {
        background-color: #3a5a7a;
    }
    
    /* ======================
       TREE WIDGET
       ====================== */
    QTreeWidget {
        background-color: #283046;
        color: #e6ecff;
        border: 1px solid #3a4a6a;
        border-radius: 4px;
    }
    
    QTreeWidget::item:selected {
        background-color: #3a4a6a;
    }
    
    /* ======================
       TABLE WIDGET
       ====================== */
    QTableWidget {
        background-color: #283046;
        color: #e6ecff;
        border: 1px solid #3a4a6a;
        gridline-color: #3a4a6a;
    }
    
    QTableWidget::item:selected {
        background-color: #3a4a6a;
    }
    
    QHeaderView::section {
        background-color: #1a1f2e;
        color: #e6ecff;
        padding: 4px;
        border: 1px solid #3a4a6a;
    }
    """
    
    app.setStyle('Fusion')
    app.setStyleSheet(stylesheet)


def get_button_style(button_type: str = 'primary') -> str:
    """
    Get predefined button stylesheet by type.
    
    Args:
        button_type: One of 'primary', 'small', 'success', 'danger', 'neutral'
    
    Returns:
        Stylesheet string for use with QPushButton.setStyleSheet()
    
    Example:
        btn = QPushButton('Click Me')
        btn.setStyleSheet(get_button_style('primary'))
    """
    
    styles = {
        'primary': '''
            QPushButton {
                background-color: #3a6ea5;
                color: #e6ecff;
                border: 1px solid #4e8cff;
                border-radius: 8px;
                padding: 6px 18px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4e8cff;
                border: 1px solid #6bbcff;
            }
            QPushButton:pressed {
                background-color: #3a5a95;
            }
        ''',
        
        'small': '''
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
        ''',
        
        'success': '''
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
        ''',
        
        'danger': '''
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
        ''',
        
        'neutral': '''
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
        ''',
    }
    
    return styles.get(button_type, styles['primary'])


def get_label_style(label_type: str = 'normal') -> str:
    """
    Get predefined label stylesheet by type.
    
    Args:
        label_type: One of 'normal', 'title', 'subtitle', 'hint'
    
    Returns:
        Stylesheet string for use with QLabel.setStyleSheet()
    
    Example:
        label = QLabel('Section Title')
        label.setStyleSheet(get_label_style('title'))
    """
    
    styles = {
        'normal': 'color: #e6ecff; font-size: 12px;',
        'title': 'color: #00d4ff; font-size: 14px; font-weight: bold; margin-bottom: 8px;',
        'subtitle': 'color: #888888; font-size: 11px; font-style: italic; margin-bottom: 12px;',
        'hint': 'color: #888888; font-size: 11px; font-style: italic;',
        'gold': 'color: #ffcc00; font-size: 11px; font-weight: bold;',
    }
    
    return styles.get(label_type, styles['normal'])

def get_toolbar_style():
    """
    Returns QSS stylesheet for toolbar and its buttons.
    Use this for toolbar-specific styling that needs explicit control.
    
    Returns:
        str: Complete QSS stylesheet for toolbar with buttons
        
    Example:
        toolbar.setStyleSheet(get_toolbar_style())
    """
    return '''
    QToolBar {
        background-color: #1a1f2e;
        border-bottom: 1px solid #3a4a6a;
        spacing: 6px;
    }
    
    QToolButton {
        background-color: transparent;
        color: #e6ecff;
        padding: 4px;
        border: 0px;
        border-radius: 4px;
        font-size: 15px;
    }
    
    QToolButton:hover {
        background-color: #3a4a6a;
        border-radius: 4px;
    }
    
    QToolButton:pressed {
        background-color: #2a3a5a;
    }
    
    QPushButton {
        background-color: transparent;
        color: #e6ecff;
        padding: 4px;
        border: 0px;
        border-radius: 4px;
        font-size: 15px;
    }
    
    QPushButton:hover {
        background-color: #3a4a6a;
        border-radius: 4px;
    }
    
    QPushButton:pressed {
        background-color: #2a3a5a;
    }
    '''