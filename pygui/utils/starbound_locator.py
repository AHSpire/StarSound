# Starbound folder auto-detection utility
import os
from pathlib import Path
from utils.atomicwriter import get_platform, get_default_starbound_path

def find_steam_install():
    plat = get_platform()
    # Always return a string or None
    if plat == 'windows':
        import winreg
        import string
        # 1. Check common install locations
        possible_roots = [
            os.path.expandvars(r'%PROGRAMFILES(X86)%\Steam'),
            os.path.expandvars(r'%PROGRAMFILES%\Steam'),
            os.path.expandvars(r'%LOCALAPPDATA%\Steam'),
            os.path.expandvars(r'%USERPROFILE%\Steam')
        ]
        # 2. Add Steam root from all available drives
        for d in string.ascii_uppercase:
            drive = f"{d}:\\Steam"
            if os.path.isdir(drive):
                possible_roots.append(drive)
        # 3. Try registry
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\\Valve\\Steam') as key:
                val, _ = winreg.QueryValueEx(key, 'SteamPath')
                if os.path.isdir(val):
                    possible_roots.insert(0, val)
        except Exception:
            pass
        # 4. Return first valid Steam root
        for root in possible_roots:
            if os.path.isdir(root):
                return str(root)
        return None
    elif plat == 'linux':
        # Linux/Steam Deck default Steam path
        default_steam = Path.home() / '.steam' / 'steam'
        if default_steam.is_dir():
            return str(default_steam)
        # Try flatpak Steam path
        flatpak_steam = Path.home() / '.var' / 'app' / 'com.valvesoftware.Steam' / '.steam' / 'steam'
        if flatpak_steam.is_dir():
            return str(flatpak_steam)
        return None
    else:
        return None

def find_starbound_folder():
    plat = get_platform()
    print("[DEBUG] Trying Steam-based detection...")
    steam = find_steam_install()
    library_folders = []
    if steam:
        # Always check main steamapps
        main_steamapps = Path(steam) / 'steamapps'
        library_folders.append(main_steamapps)
        # On Windows, parse libraryfolders.vdf for custom Steam libraries
        if plat == 'windows':
            vdf_path = main_steamapps / 'libraryfolders.vdf'
            if vdf_path.is_file():
                try:
                    with open(vdf_path, encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if '"path"' in line:
                                parts = line.split('"')
                                for p in parts:
                                    p = p.strip().replace('\\\\', '\\')
                                    if ':' in p and os.path.isdir(p):
                                        library_folders.append(Path(p) / 'steamapps')
                except Exception as e:
                    print(f"[DEBUG] Failed to parse libraryfolders.vdf: {e}")
        # On Linux, also check flatpak and other common library locations
        if plat == 'linux':
            alt1 = Path.home() / '.local' / 'share' / 'Steam' / 'steamapps'
            if alt1.is_dir():
                library_folders.append(alt1)
            alt2 = Path.home() / '.var' / 'app' / 'com.valvesoftware.Steam' / '.local' / 'share' / 'Steam' / 'steamapps'
            if alt2.is_dir():
                library_folders.append(alt2)
        # Search all found libraries for Starbound
        for lib in library_folders:
            sb_path = lib / 'common' / 'Starbound'
            print(f"[DEBUG] Checking {sb_path}")
            if sb_path.is_dir():
                print(f"[DEBUG] Autodetected Starbound at {sb_path}")
                return str(sb_path)
    # Fallback: use default helper
    default_path = get_default_starbound_path()
    if default_path and default_path.is_dir():
        print(f"[DEBUG] Default Starbound path found: {default_path}")
        return str(default_path)
    print("[DEBUG] Starbound folder not found.")
    return None

def get_mods_folder():
    sb = find_starbound_folder()
    if not sb:
        print("[DEBUG] get_mods_folder: Starbound folder not found.")
        return None
    mods = Path(sb) / 'mods'
    return str(mods)

def get_storage_folder():
    sb = find_starbound_folder()
    if not sb:
        print("[DEBUG] get_storage_folder: Starbound folder not found.")
        return None
    storage = Path(sb) / 'storage'
    return str(storage)
