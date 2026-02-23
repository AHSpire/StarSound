# ✨ Font Selection Feature - Implementation Summary

## What's New
A new **Fonts** menu has been added to the top menu bar (between "Help", "CRT Effects", and "File") allowing users to change the application font and save their preference globally.

---

## Features

### 1. **Font Menu** (Top Menu Bar)
- Located next to "File", "Help", and "CRT Effects"
- Displays 7 font options:
  - **Hobo** (custom font, default)
  - **Helvetica**
  - **Verdana**
  - **Arial**
  - **Times New Roman**
  - **Courier New**
  - **Georgia**

### 2. **Font Selection**
- Click any font name to apply it instantly to the entire app
- The currently selected font is marked with a checkmark (✓)
- Switching fonts updates all UI elements (buttons, labels, menus, etc.)

### 3. **Persistent Storage**
- Font preference is saved to **Global Settings** (`settings.json`)
- Independent from mod settings (stored separately)
- Font preference is restored automatically when the app restarts

---

## Files Modified

### [1] `pygui/utils/settings_manager.py`
**Change:** Added `current_font` to default settings
```python
def _get_defaults(self) -> dict:
    """Return default settings."""
    return {
        'last_game_path': '',
        'last_mod_folder': '',
        'last_mod_name': '',
        'last_patch_mode': 'add',
        'crt_effects_enabled': False,
        'current_font': 'Hobo',  # ← NEW
    }
```

---

### [2] `pygui/starsound_gui.py`

#### Change 1: Added `_apply_font_to_app()` Method
```python
def _apply_font_to_app(self, font_name: str):
    """Apply a font to the entire application.
    
    Args:
        font_name: Name of the font to apply (e.g., 'Hobo', 'Helvetica', 'Verdana')
    """
```
- Handles Hobo font loading from `assets/font/hobo.ttf`
- For system fonts, creates QFont with the requested family name
- Applies font to entire window, affecting all child widgets

#### Change 2: Updated Startup Font Loading
**Before:**
```python
# Hardcoded loading of Hobo font only
font_id = QFontDatabase.addApplicationFont(font_path)
if font_id != -1:
    family = QFontDatabase.applicationFontFamilies(font_id)[0]
    app_font = QFont(family, 15)
    self.setFont(app_font)
```

**After:**
```python
# Load saved font preference from settings, default to 'Hobo'
saved_font = self.settings.get('current_font', 'Hobo')
self._apply_font_to_app(saved_font)
```

#### Change 3: Added Fonts Menu
```python
# Add a 'Fonts' menu for font selection
fonts_menu = menubar.addMenu('Fonts')
available_fonts = ['Hobo', 'Helvetica', 'Verdana', 'Arial', 'Times New Roman', 'Courier New', 'Georgia']
current_font = self.settings.get('current_font', 'Hobo')

# Create font actions with closures to capture font name
for font_name in available_fonts:
    font_action = QAction(font_name, self)
    font_action.setCheckable(True)
    font_action.setChecked(font_name == current_font)
    
    def create_font_setter(fname):
        def set_font_and_save():
            self._apply_font_to_app(fname)
            self.settings.set('current_font', fname)
            # Update all font actions to reflect new selection
            for action in fonts_menu.actions():
                action.setChecked(action.text() == fname)
        return set_font_and_save
    
    font_action.triggered.connect(create_font_setter(font_name))
    fonts_menu.addAction(font_action)
```

---

## How It Works

### User Workflow
1. User opens StarSound
2. App loads saved font preference from `settings.json`
3. User clicks **Fonts** menu → sees available fonts
4. User selects a new font → entire app updates instantly
5. App saves selection to `settings.json`
6. Next time app opens → selected font loads automatically

### Settings Storage
**File:** `c:\Projects\StarSound\settings.json`
```json
{
  "last_game_path": "",
  "last_mod_folder": "c:\\steam\\steamapps\\common\\Starbound\\mods",
  "last_mod_name": "...",
  "last_patch_mode": "replace",
  "crt_effects_enabled": false,
  "current_font": "Arial"  ← User's font choice
}
```

---

## Testing ✅

All tests passed:
- ✓ Font menu appears in menu bar
- ✓ Fonts can be applied dynamically
- ✓ Font preference persists to `settings.json`
- ✓ App loads saved font on startup
- ✓ No syntax errors
- ✓ No import errors

---

## Notes

- **Hobo** remains the default font for new installations
- Font changes are **immediate** and affect the entire application
- System fonts fallback gracefully if unavailable on the user's system
- Font preference is **global** (shared across all mods)
- Separate from **mod settings** (which are per-mod, stored in `mod_saves/`)

