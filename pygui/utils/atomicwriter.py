import shutil
from utils.audio_utils import convert_to_ogg, get_audio_duration
from utils.logger import get_logger

# Backup, convert, and copy audio for a mod
def backup_and_convert_audio(file_path: str, mod_folder: str, bitrate: str = '192k', audio_filter: str = '', ffmpeg_log_callback=None, backup_path: str = None) -> tuple:
    """
    1. Backup the original file to backups/originals
    2. Convert to OGG in backups/converted with specified bitrate and audio processing
    3. Check output duration (warn if suspiciously short - may indicate audio processing issue)
    4. Copy OGG to music folder
    
    Args:
        file_path: Path to source audio file
        mod_folder: Destination mod folder (for music output)
        bitrate: OGG bitrate (default '192k', e.g., '128k', '256k', '320k')
        audio_filter: FFmpeg audio filter chain (from build_audio_filter_chain)
        ffmpeg_log_callback: Optional callback for FFmpeg output logging
        backup_path: Optional path to root backups folder (e.g., StarSound/backups/{mod_name}). If None, uses legacy staging location.
    
    Returns (success: bool, message: str, ogg_path: str)
    """
    import os
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    from utils.audio_utils import sanitize_filename
    sanitized_base = sanitize_filename(base_name)
    # 1. Backup original file
    logger = get_logger()
    logger.log(f'[DEBUG] backup_and_convert_audio: mod_folder={mod_folder}, backup_path={backup_path}')
    
    # Use provided backup_path (root location) or fallback to legacy staging location
    if backup_path:
        originals_dir = os.path.join(backup_path, 'originals')
    else:
        originals_dir = os.path.join(mod_folder, 'backups', 'originals')
    
    os.makedirs(originals_dir, exist_ok=True)
    logger.log(f'[DEBUG] Attempting backup: {file_path} → {originals_dir}')
    try:
        backup_file_path = os.path.join(originals_dir, os.path.basename(file_path))
        shutil.copy2(file_path, backup_file_path)
        logger.log(f'[DEBUG] ✓ Backup successful: {backup_file_path}')
    except Exception as e:
        logger.error(f'Failed to backup original: {e}')
        return False, f'Failed to backup original: {e}', ''
    # 2. Convert to OGG in backups/converted
    if backup_path:
        converted_dir = os.path.join(backup_path, 'converted')
    else:
        converted_dir = os.path.join(mod_folder, 'backups', 'converted')
    
    os.makedirs(converted_dir, exist_ok=True)
    ogg_path = os.path.join(converted_dir, sanitized_base + '.ogg')
    logger.log(f'[DEBUG] Converting to: {ogg_path}')
    success, msg = convert_to_ogg(file_path, ogg_path, bitrate=bitrate, audio_filter=audio_filter, log_callback=ffmpeg_log_callback)
    if not success:
        logger.error(f'Conversion failed: {msg}')
        return False, f'Conversion failed: {msg}', ''
    logger.log(f'[DEBUG] ✓ Conversion successful: {ogg_path}')
    
    # 2.5. CHECK OUTPUT DURATION (detect audio processing issues)
    output_duration = get_audio_duration(ogg_path)
    input_duration = get_audio_duration(file_path)
    logger.log(f'[DEBUG] Output duration check: input={input_duration:.1f}min, output={output_duration:.1f}min')
    
    if output_duration is not None and output_duration < 0.1:
        # Output is suspiciously short (less than 6 seconds)
        msg_warning = f'⚠️ WARNING: Output is {output_duration:.1f}min (very short). Audio processing may have removed all content. Check Silence Trimming settings.'
        logger.warn(f'[CONVERSION_ISSUE] {msg_warning}')
        return False, msg_warning, ogg_path
    elif output_duration is not None and input_duration is not None:
        # Check if output is MUCH shorter than input (e.g., < 50% of original)
        if output_duration < (input_duration * 0.5):
            msg_warning = f'⚠️ WARNING: Output is {output_duration:.1f}min (was {input_duration:.1f}min). Audio processing removed {100 - (output_duration/input_duration*100):.0f}% of content. Consider adjusting Silence Trimming settings.'
            logger.warn(f'[CONVERSION_ISSUE] {msg_warning}')
            # Don't fail here, just warn - user might intentionally trim
    
    # 3. Copy OGG to music folder
    music_dir = os.path.join(mod_folder, 'music')
    os.makedirs(music_dir, exist_ok=True)
    logger.log(f'[DEBUG] backup_and_convert_audio: music_dir={music_dir}')
    music_ogg_path = os.path.join(music_dir, sanitized_base + '.ogg')
    logger.log(f'[DEBUG] Copying OGG to: {music_ogg_path}')
    try:
        shutil.copy2(ogg_path, music_ogg_path)
        logger.log(f'[DEBUG] ✓ OGG copied to music folder: {music_ogg_path}')
    except Exception as e:
        logger.error(f'Failed to copy OGG to music: {e}')
        return False, f'Failed to copy OGG to music: {e}', music_ogg_path
    logger.log(f'[DEBUG] ✓ Audio converted and copied to music: {music_ogg_path}')
    return True, f'Audio converted and copied to music: {music_ogg_path}', music_ogg_path
# --- Platform Helper for Cross-Platform Support ---
import platform

def get_platform():
    """
    Returns a string identifying the current platform: 'windows', 'linux', 'darwin' (macOS), or 'unknown'.
    """
    sys_platform = platform.system().lower()
    if 'windows' in sys_platform:
        return 'windows'
    elif 'linux' in sys_platform:
        return 'linux'
    elif 'darwin' in sys_platform:
        return 'darwin'
    else:
        return 'unknown'

def get_default_starbound_path():
    """
    Returns the default Starbound install path for the current platform.
    """
    plat = get_platform()
    if plat == 'windows':
        return Path.home() / 'AppData' / 'Local' / 'Steam' / 'steamapps' / 'common' / 'Starbound'
    elif plat == 'linux':
        # Steam Deck and Linux default Steam library location
        return Path.home() / '.steam' / 'steam' / 'steamapps' / 'common' / 'Starbound'
    elif plat == 'darwin':
        # macOS (rare, but possible)
        return Path.home() / 'Library' / 'Application Support' / 'Steam' / 'steamapps' / 'common' / 'Starbound'
    else:
        return None
import getpass
# --- New function: create_mod_folder_structure ---
def create_mod_folder_structure(final_destination: Path, mod_name: str) -> Path:
    """
    Creates the full mod folder structure for a new mod, including subfolders and a _metadata file.
    Returns the path to the created mod folder.
    """
    import os
    mod_folder = final_destination / mod_name
    directories = [
        'biomes/surface',
        'biomes/underground',
        'biomes/space',
        'music',
        'music_replacers',
        'music_add_and_replace',
        'outputs'
    ]
    for dir in directories:
        (mod_folder / dir).mkdir(parents=True, exist_ok=True)
    
    # NOTE: backups/originals and backups/converted are no longer created in staging
    # They are now centralized in StarSound/backups/{mod_name}/ (root location)

    # Create _metadata file
    internal_name = mod_name.replace(' ', '_')
    computer_user_name = getpass.getuser()
    metadata = {
        'name': internal_name,
        'friendlyName': mod_name,
        'author': 'StarSound User',
        'description': 'StarSound Generated Mod - Edit the description in _metadata',
        'version': '1.0.0',
        'priority': 9999
    }
    metadata_path = mod_folder / '_metadata'
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(metadata, f, indent=2)
    except Exception as e:
        print(f"[AtomicWriter] Failed to write _metadata: {e}")
    return mod_folder
"""
atomicwriter.py

Handles automatic saving of mod progress into a 'staging' folder inside the StarSound directory.
Ensures that mod data is backed up before generation for recovery and safety.
"""

import json
from pathlib import Path
from datetime import datetime


def save_mod_to_staging(mod_data: dict, mod_name: str, starsound_dir: Path) -> Path:
    """
    Saves the current mod progress to a folder in the 'staging' directory inside the StarSound directory.
    The folder is named with the mod name (no timestamp).
    The full mod folder structure is created, including _metadata and subfolders.
    The mod data is saved as 'modinfo.json' inside that folder.
    Returns the path to the saved folder.
    """
    staging_dir = starsound_dir / 'staging'
    staging_dir.mkdir(parents=True, exist_ok=True)

    safe_mod_name = "".join(c for c in mod_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
    folder_name = safe_mod_name
    mod_folder = staging_dir / folder_name
    # Handle duplicates: add ' Copy', ' Copy1', ' Copy2', etc.
    copy_index = 0
    while mod_folder.exists():
            copy_index += 1
            if copy_index == 1:
                folder_name = f"{safe_mod_name} Copy"
            else:
                folder_name = f"{safe_mod_name} Copy{copy_index}"
            mod_folder = staging_dir / folder_name

        # Create full mod folder structure and _metadata
    create_mod_folder_structure(staging_dir, folder_name)

    return mod_folder
