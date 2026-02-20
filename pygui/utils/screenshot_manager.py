# screenshot_manager.py

# Screenshot manager for Starbound Music Mod Generator (Python)
import os
from datetime import datetime
try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

_screenshot_folder = os.path.abspath('screenshots')

def set_screenshot_folder(folder):
    global _screenshot_folder
    _screenshot_folder = os.path.abspath(folder)

def get_screenshot_folder():
    return _screenshot_folder

def take_screenshot(save_dir=None):
    if ImageGrab is None:
        return False, 'Pillow (PIL) is not installed. Install with: pip install pillow'
    # If save_dir is a QWidget, use _screenshot_folder as folder and save window screenshot
    folder = _screenshot_folder
    window = None
    if hasattr(save_dir, 'grab'):
        window = save_dir
    elif isinstance(save_dir, str) and save_dir:
        folder = save_dir
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    # Count existing screenshots for sequential numbering
    all_files = os.listdir(folder)
    screenshots = [f for f in all_files if f.startswith('screenshot') and f.endswith('.png') and f != 'ascreenshot_current.png']
    # Find the highest N used so far
    max_n = 0
    for f in screenshots:
        parts = f.split('_', 1)
        if parts[0].startswith('screenshot'):
            num_part = parts[0][10:]
            try:
                n = int(num_part)
                if n > max_n:
                    max_n = n
            except Exception:
                pass
    next_n = max_n + 1
    filename = f'screenshot{next_n}_{timestamp}.png'
    path = os.path.join(folder, filename)
    current_path = os.path.join(folder, 'ascreenshot_current.png')
    # Prevent duplicate screenshot for the same second
    if os.path.exists(path):
        return False, 'Screenshot already taken for this second. Please wait a moment before taking another.'

    # After saving, keep only the 10 most recent screenshots (by mtime)
    # (This replaces the old cleanup logic for robustness)
    try:
        img = None
        if window is not None:
            # Use QWidget.grab() for window screenshot
            pixmap = window.grab()
            img = pixmap.toImage()
            from PyQt5.QtGui import QImage
            img.save(path)
            img.save(current_path)
        else:
            img = ImageGrab.grab()
            img.save(path)
            img.save(current_path)
        # Cleanup: keep only the 10 most recent screenshots (excluding ascreenshot_current.png)
        all_files = os.listdir(folder)
        screenshots = [f for f in all_files if f.startswith('screenshot') and f.endswith('.png') and f != 'ascreenshot_current.png']
        # Sort by mtime, newest first
        screenshots.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
        # Delete any beyond the 10 newest
        for old_file in screenshots[10:]:
            try:
                os.remove(os.path.join(folder, old_file))
            except Exception:
                pass
        # Renumber the remaining screenshots in order (screenshot1_, screenshot2_, ...)
        for idx, fname in enumerate(screenshots[:10], 1):
            old_path = os.path.join(folder, fname)
            # Extract the date/time part from the original filename
            parts = fname.split('_', 1)
            date_part = parts[1] if len(parts) > 1 else ''
            new_name = f'screenshot{idx}_{date_part}'
            new_path = os.path.join(folder, new_name)
            if fname != new_name:
                if os.path.exists(new_path):
                    # If the target exists, skip renaming and optionally log or warn
                    continue
                os.rename(old_path, new_path)
        return True, f'Screenshot saved: {path}'
    except Exception as e:
        return False, f'Error taking screenshot: {e}'

# Usage:
# success, path_or_error = take_screenshot()
