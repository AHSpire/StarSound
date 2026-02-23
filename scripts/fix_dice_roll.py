import re

with open(r'pygui/starsound_gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the first __init__ method's set_autofill_name and remove the save_current_mod_to_staging call
# Start from the beginning - find the section with "[DEBUG] Generated mod name"
init_start = content.find("print('[DEBUG] Generated mod name:'")
if init_start == -1:
    print("ERROR: Could not find __init__ marker")
    exit(1)

# Find the next method definition after __init__ to know where it ends
next_method = content.find("\n    def ", init_start + 100)
init_end = next_method if next_method > 0 else len(content)

# Extract just the __init__ section
init_section = content[init_start:init_end]

# Replace the first occurrence of "save_current_mod_to_staging()" in set_autofill_name with nothing
# Find the set_autofill_name function in this section
pattern = r'(def set_autofill_name\(new_name\):.*?self\._modname_autofill = True\n)            save_current_mod_to_staging\(\)\n'
init_section_fixed = re.sub(pattern, r'\1', init_section, count=1, flags=re.DOTALL)

# Now add save_current_mod_to_staging() to the checkbox handler
# Find the checkbox handler and add the save call when checked=True
checkbox_pattern = r'(def on_checkbox_toggled\(checked\):\n            if checked:.*?self\.modname_input\.setStyleSheet\(\'color: #888888[^)]+\))\n'
init_section_fixed = re.sub(
    checkbox_pattern,
    r'\1\n                save_current_mod_to_staging()  # Only save mod folder when user confirms\n',
    init_section_fixed,
    count=1,
    flags=re.DOTALL
)

# Reconstruct the full file
new_content = content[:init_start] + init_section_fixed + content[init_end:]

with open(r'pygui/starsound_gui.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Updated dice roll behavior - mod folder now created only on checkbox confirmation")
