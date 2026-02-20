#!/usr/bin/env python
"""Update the CRT toggle section in starsound_gui.py to save settings."""

import re
from pathlib import Path

file_path = Path('pygui/starsound_gui.py')
content = file_path.read_text(encoding='utf-8')

# Find the toggle_crt_effects function and add settings.set() call
# We'll search for the first occurrence which should be in __init__
pattern = r"(def toggle_crt_effects\(\):\s+self\.crt_effects_enabled = not self\.crt_effects_enabled\s+)(if hasattr\(self, '_scanline_overlay'\))"
replacement = r"\1if hasattr(self, 'settings'):\n                self.settings.set('crt_effects_enabled', self.crt_effects_enabled)\n            \2"

new_content = re.sub(pattern, replacement, content, count=1)

if new_content != content:
    file_path.write_text(new_content, encoding='utf-8')
    print("✅ Updated CRT toggle to save settings (first occurrence in __init__)")
else:
    print("❌ Pattern not found - may already be updated")
