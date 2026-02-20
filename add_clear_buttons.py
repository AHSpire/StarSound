#!/usr/bin/env python3
"""Add Clear Audio buttons to both audio sections in starsound_gui.py"""

import re
from pathlib import Path

# Read the file
gui_file = Path('pygui/starsound_gui.py')
content = gui_file.read_text(encoding='utf-8')

# Pattern: Find audio_grid.addWidget(self.audio_browse_btn, 0, 2) and add Clear button after
# We'll replace it with the button plus the clear button

old_pattern = r'(        self\.audio_browse_btn = QPushButton\(\'Browse\'\)\n        self\.audio_browse_btn\.setToolTip\(\'Shortcut: Ctrl\+O\'\)\n        self\.audio_browse_btn\.clicked\.connect\(lambda: \[self\.play_click_sound\(\), self\.browse_audio\(\)\]\)\n        audio_grid\.addWidget\(self\.audio_browse_btn, 0, 2\))\n\n        # Add label to show selected audio files'

replacement = r'''\1
        self.audio_clear_btn = QPushButton('Clear')
        self.audio_clear_btn.clicked.connect(lambda: [self.play_click_sound(), self.clear_audio()])
        audio_grid.addWidget(self.audio_clear_btn, 0, 3)

        # Add label to show selected audio files'''

# Replace all occurrences (should be 2)
new_content = re.sub(old_pattern, replacement, content, flags=re.MULTILINE)

# Also update the grid colspan for self.selected_files_label from 3 to 4
# Pattern: audio_grid.addWidget(self.selected_files_label, 1, 0, 1, 3)
old_label_pattern = r'audio_grid\.addWidget\(self\.selected_files_label, 1, 0, 1, 3\)'
replacement_label = r'audio_grid.addWidget(self.selected_files_label, 1, 0, 1, 4)'

new_content = re.sub(old_label_pattern, replacement_label, new_content)

# Write back
gui_file.write_text(new_content, encoding='utf-8')
print("✅ Added Clear Audio buttons to both Step 3 audio sections")
print(f"   - Added self.audio_clear_btn to button row")
print(f"   - Updated grid colspan for audio labels from 3 to 4")
