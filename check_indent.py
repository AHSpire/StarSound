with open(r'C:\Projects\StarSound\pygui\starsound_gui.py', encoding='utf-8') as f:
    lines = f.readlines()
    for i in range(950, 970):
        line = lines[i]
        indent = len(line) - len(line.lstrip())
        print(f'{i+1}: indent={indent:2d} | {line.rstrip()[:80]}')
