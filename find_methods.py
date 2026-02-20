import re

with open(r'C:\Projects\StarSound\pygui\starsound_gui.py', encoding='utf-8') as f:
    lines = f.readlines()

print("Methods in MainWindow:")
in_class = False
for i, line in enumerate(lines, 1):
    if 'class MainWindow' in line:
        in_class = True
        print(f"{i}: {line.rstrip()}")
        continue
    
    if in_class:
        if line.startswith('class ') and 'MainWindow' not in line:
            print(f"End of Main Window at line {i}")
            break
        
        if re.match(r'^\s{4}def ', line):
            indent = len(line) - len(line.lstrip())
            print(f"{i}: (indent={indent}) {line.rstrip()[:70]}")
