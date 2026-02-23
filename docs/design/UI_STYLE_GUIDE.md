# 🎨 StarSound UI Style Guide

**Audience:** Copilot/AI Assistant for code consistency and maintainability  
**Last Updated:** 2026-02-19  
**Framework:** PyQt5 with QSS (Qt Style Sheets)

---

## 🎯 Quick Reference

### Color Palette

| Element | Hex Code | Usage |
|---------|----------|-------|
| **Background** | `#1a1f2e` | Main dialog/window background (dark navy) |
| **Primary Text** | `#e6ecff` | Standard text, labels, normal content |
| **Accent (Cyan)** | `#00d4ff` | Titles, highlights, active states |
| **Accent (Gold)** | `#ffcc00` | Section headers, important labels |
| **Secondary Text** | `#888888` | Subtitles, hints, descriptive text |
| **Input Background** | `#283046` | ComboBox, LineEdit, input fields |
| **Border** | `#3a4a6a` | Normal borders, dividers |
| **Border Hover** | `#5a8ed5` | Focus state, hover highlight |
| **Button (Neutral)** | `#2a3a4a` | Standard preset/action buttons |
| **Button Hover** | `#3a4a5a` | Preset button hover state |
| **Button Success** | `#2d5a3d` | Confirm/Apply buttons (green) |
| **Button Danger** | `#c41e3a` | Cancel/Decline buttons (crimson red) |

---

## 📝 Typography Standards

### Font Sizes
- **Main Titles:** `14px` | bold | `#00d4ff` (Cyan accent)
- **Section Headers:** `11px` | bold | `#ffcc00` (Gold accent)
- **Subtitle/Hint:** `11px` | italic | `#888888` (Secondary text)
- **Normal Text:** `12px` | regular | `#e6ecff` (Primary text)
- **Small Text:** `10px` | regular | `#888888` (Secondary text)

### Font Weight
- `normal` - Default for body text
- `bold` - Titles, headers, important labels
- `italic` - Subtitles, hints, descriptive text

---

## 🧩 Component Styles

### Dialog Windows

```python
# Root dialog background
self.setStyleSheet('''
    QDialog {
        background-color: #1a1f2e;
    }
    QLabel {
        color: #e6ecff;
    }
''')
```

### Titles (Section Headers)

```python
title = QLabel('🎛️ Audio Processing Options')
title.setStyleSheet('color: #00d4ff; font-size: 14px; font-weight: bold; margin-bottom: 8px;')
```

**Key:** Cyan accent (`#00d4ff`), 14px, bold

### Subtitles/Hints

```python
subtitle = QLabel('💡 Global Preset: Configure default settings below...')
subtitle.setStyleSheet('color: #888888; font-size: 11px; margin-bottom: 12px; font-style: italic;')
```

**Key:** Secondary gray (`#888888`), 11px, italic, margin-bottom 12px

### Regular Labels

```python
label = QLabel('OGG Bitrate:')
label.setStyleSheet('color: #e6ecff;')
```

**Key:** Primary text (`#e6ecff`), no size specified (uses default 12px)

### Preset/Action Buttons (Neutral)

```python
btn = QPushButton('🎧 Lo-Fi')
btn.setMaximumWidth(110)
btn.setStyleSheet('''
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
''')
```

**Key:**
- Background: `#2a3a4a` (neutral dark)
- Hover: `#3a4a5a` (lighter) + `#00d4ff` border (cyan accent)
- Padding: `4px 8px`
- Border radius: `4px`
- Font size: `11px`

### Main Action Buttons (Primary)

```python
action_btn = QPushButton('Step 5: Action Button')
action_btn.setStyleSheet('''
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
''')
```

**Key:**
- Background: `#3a6ea5` (primary action blue)
- Hover: `#4e8cff` (brighter) + `#6bbcff` border (bright cyan)
- Padding: `6px 18px`
- Border radius: `8px`
- Font size: `13px` or larger
- **IMPORTANT:** Always include `:hover` pseudo-selector for user feedback

### Confirm/Apply Buttons (Success)

```python
confirm_btn = QPushButton('✓ Apply & Continue')
confirm_btn.setStyleSheet('''
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
''')
```

**Key:**
- Background: `#2d5a3d` (dark green)
- Hover: `#3d7a4d` (lighter green)
- Padding: `8px 16px` (larger for prominence)
- Font weight: `bold`
- Min-width: `120px`

### Cancel/Decline Buttons (Danger)

```python
cancel_btn = QPushButton('✗ Cancel')
cancel_btn.setStyleSheet('''
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
''')
```

**Key:**
- Background: `#c41e3a` (crimson red)
- Hover: `#e63235` (vibrant red)
- Padding: `8px 16px`
- Font weight: `bold`

### ComboBox / Dropdown

```python
combo = QComboBox()
combo.setStyleSheet(
    'QComboBox { background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px; }'
    'QComboBox QAbstractItemView { background: #283046; color: #e6ecff; selection-background-color: #3a4a6a; }'
    'QComboBox::drop-down { border: none; }'
    'QComboBox:focus { border: 1px solid #5a8ed5; }'
)
```

**Key:**
- Background: `#283046` (input field color)
- Border: `1px solid #3a4a6a` (normal) → `#5a8ed5` (focus)
- Dropdown border: `none` (cleaner look)
- Item hover: `#3a4a6a` (selection background)

### LineEdit / Text Input

```python
input_field = QLineEdit()
input_field.setStyleSheet('background: #283046; color: #e6ecff; border: 1px solid #3a4a6a; border-radius: 4px; padding: 4px;')
```

**Key:**
- Background: `#283046` (input field color)
- Border: `1px solid #3a4a6a` (normal state)
- Padding: `4px`
- Border radius: `4px`

### CheckBox

```python
checkbox = QCheckBox('[1] Audio Trimmer - Precise start/end time control')
checkbox.setStyleSheet('QCheckBox { color: #e6ecff; }')
```

**Key:** Primary text color (`#e6ecff`), no special formatting needed

---

## 📏 Spacing & Layout Standards

### Margins & Padding

| Element | Value | Notes |
|---------|-------|-------|
| Dialog margins | `12px` | Main layout container margins |
| Layout spacing | `10px` | Space between elements in vertical layouts |
| Button padding | `4px 8px` (preset) \| `8px 16px` (confirm) | Horizontal × Vertical |
| Element margins | `8px` (top), `12px` (bottom) | For visual separation |

### Layout Proportions

- **Horizontal splitter (per-track dialog):** `300px` left (track list) | `900px` right (controls)
- **Dialog minimum sizes:**
  - Audio Processing: `900w × 700h`
  - Per-Track Config: `1400w × 850h`
  - Split Config: `700w × 500h`

---

## 🎭 Icon/Emoji Conventions

Use emojis as prefixes for clear visual scanning. Order by category:

### Toolbars & Global
- 📸 Screenshot
- 🩺 Config Health
- 🚨 Emergency Beacon
- 🎛️ Audio Processing

### Audio Processing
- 🎵 Quick Presets
- 🎧 Lo-Fi preset
- 🎼 Orchestral preset
- 🎹 Electronic preset
- ☁️ Ambient preset
- 🤘 Metal preset
- 🎸 Acoustic preset
- 🎵 Pop preset
- ✗ None preset
- ✓ All preset

### File Management
- 📁 Folder/parent file indicator
- ├─ Segment child indicator (visual tree)
- 📋 Track list
- 🎵 Configure Audio Processing Per Track

### Actions
- ✓ Confirm/Apply (green background)
- ✗ Cancel/Decline (red background)
- 🔄 Reset to Default
- 📋 Apply to All

### Status/Info
- 💡 Hint/suggestion (secondary text)
- ⚠️ Warning (yellow accent)
- 🔧 Tools/settings

---

## ✅ Best Practices (For Copilot Reference)

### DO:
1. ✓ Use `#1a1f2e` for all dialog backgrounds
2. ✓ Use `#e6ecff` for primary/normal text
3. ✓ Use `#00d4ff` for all titles/section headers
4. ✓ Use `#ffcc00` for subsection labels/presets header
5. ✓ Use `#888888` for subtitles, hints, secondary text
6. ✓ Use cyan hover (`#00d4ff` border) for interactive preset buttons
7. ✓ Use blue hover (`#4e8cff` bg + `#6bbcff` border) for main action buttons
8. ✓ Use green success buttons (`#2d5a3d` → `#3d7a4d`)
9. ✓ Use crimson red danger buttons (`#c41e3a` → `#e63235`)
10. ✓ Use `#283046` for input fields (ComboBox, LineEdit)
11. ✓ Use `4px` border radius for all rounded elements (8px for main action buttons)
12. ✓ Add emojis for visual clarity and scannability
13. ✓ Use italic + gray (`#888888`) for helper/hint text
14. ✓ Use crimson red (`#c41e3a`) for danger/cancel actions—NOT brownish reds
15. ✓ **Always include `:hover` pseudo-selector on all interactive buttons**

### DON'T:
1. ✗ Mix background colors (always `#1a1f2e` for dialogs)
2. ✗ Use default blue/gray colors from Qt (override with palette)
3. ✗ Forget hover states on interactive elements (ALWAYS include `:hover`)
4. ✗ Use square corners (always `border-radius: 4px` for small buttons, `8px` for main actions)
5. ✗ Use inconsistent button sizes (preset: 110px wide, action: larger with more padding)
6. ✗ Add buttons without clear intent (success/danger/neutral/primary color)
7. ✗ Forget to set minimum/maximum widths on buttons (ensures alignment)
8. ✗ Use bold text for regular content (only titles, headers, buttons)
9. ✗ Exceed `#00d4ff` or `#ffcc00` for text (use sparingly—reserved for emphasis)
10. ✗ Create custom colors not in this palette (maintains cohesion)
11. ✗ Use brownish reds like `#5a2d2d`—always use true crimsons like `#c41e3a`

---

## 🔍 Common Patterns (Copy-Paste Templates)

### New Dialog Template

```python
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('🎛️ My Feature')
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        
        # Dark theme
        self.setStyleSheet('''
            QDialog {
                background-color: #1a1f2e;
            }
            QLabel {
                color: #e6ecff;
            }
        ''')
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Title
        title = QLabel('🎛️ Section Title')
        title.setStyleSheet('color: #00d4ff; font-size: 14px; font-weight: bold; margin-bottom: 8px;')
        main_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel('💡 Hint or description text.')
        subtitle.setStyleSheet('color: #888888; font-size: 11px; margin-bottom: 12px; font-style: italic;')
        main_layout.addWidget(subtitle)
```

### New Button (Preset/Neutral)

```python
btn = QPushButton('🎧 Preset Name')
btn.setMaximumWidth(110)
btn.setStyleSheet('''
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
''')
```

### New Button (Main Action/Primary)

```python
action_btn = QPushButton('Step 5: Action Button')
action_btn.setStyleSheet('''
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
''')
```

### New Button (Confirm/Success)

```python
apply_btn = QPushButton('✓ Apply')
apply_btn.setMinimumWidth(120)
apply_btn.setStyleSheet('''
    QPushButton {
        background-color: #2d5a3d;
        color: #e6ecff;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #3d7a4d;
    }
''')
```

### New Button (Cancel/Danger)

```python
cancel_btn = QPushButton('✗ Cancel')
cancel_btn.setMinimumWidth(100)
cancel_btn.setStyleSheet('''
    QPushButton {
        background-color: #c41e3a;
        color: #e6ecff;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #e63235;
    }
''')
```

---

## 🚀 Applying This Guide

When adding UI elements, before coding:
1. Identify the element type (button, label, input, dialog)
2. Find the matching pattern in this guide
3. Copy template code and customize strings/callbacks
4. Verify colors match palette (use Ctrl+F to search hex codes)
5. Test hover states and focus interactions
6. Ensure spacing/sizing matches standards above

**Consistency = Professional appearance + Maintainability** 🎯
