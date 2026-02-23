import re

# Read the file
with open(r'c:\Projects\StarSound\pygui\starsound_gui.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where __init__ ends (look for "self.addToolBar")
init_end = None
for i, line in enumerate(lines):
    if 'self.addToolBar(Qt.TopToolBarArea, toolbar)' in line:
        init_end = i + 1
        break

# Find where class-level signals start (4-space indent after __init__)
signal_start = None
for i in range(init_end, len(lines)):
    if lines[i].strip().startswith('ffmpeg_log_signal') and not lines[i].startswith('        '):
        signal_start = i
        break

# Find where the orphaned UI setup starts (8-space indent "# Central widget")
orphaned_ui_start = None
for i in range(signal_start, len(lines)):
    if '# Central widget and scroll area' in lines[i]:
        orphaned_ui_start = i
        break

# Find where the orphaned UI setup ends (look for "def on_add_to_game")
orphaned_ui_end = None
for i in range(orphaned_ui_start, len(lines)):
    if lines[i].strip().startswith('def on_add_to_game'):
        orphaned_ui_end = i
        break

print(f"__init__ ends at line: {init_end}")
print(f"Signals start at line: {signal_start}")
print(f"Orphaned UI starts at line: {orphaned_ui_start}")
print(f"Orphaned UI ends at line: {orphaned_ui_end}")

if init_end and signal_start and orphaned_ui_start and orphaned_ui_end:
    # Extract the orphaned UI code
    orphaned_ui_code = lines[orphaned_ui_start:orphaned_ui_end]
    
    # Build the corrected file
    corrected = (
        lines[:init_end] +  # Keep everything up to end of __init__
        ['\n'] +            # Add a newline
        orphaned_ui_code +  # Insert the UI setup code into __init__
        ['\n'] +            # Add a newline
        lines[signal_start:orphaned_ui_start] +  # Keep signals (no longer orphaned)
        lines[orphaned_ui_end:]  # Keep everything after orphaned UI
    )
    
    # Write back
    with open(r'c:\Projects\StarSound\pygui\starsound_gui.py', 'w', encoding='utf-8') as f:
        f.writelines(corrected)
    
    print("File restructured successfully")
else:
    print("ERROR: Could not find required markers in the file")
