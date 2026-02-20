"""
[SYSTEM] mod_exporter.py - Mod Installation to Starbound/mods/
[VERSION] 1.0
[ROLE] Final Mod Export Handler
[ARCHITECTURE_ID] MOD_EXPORT_v1::FINAL_INSTALLER

[PURPOSE]
Handles final installation of completed mods to Starbound/mods/ folder.
Supports two formats:
  1. LOOSE_FILES - Folder structure (easy to edit)
  2. PAK_FILE - Single .pak file (easy to share)

[WORKFLOW]
1. Staging contains fully-built mod: staging/{ModName}/ with biomes/, music/, _metadata
2. Export process copies/packages staging to Starbound/mods/:
   - If LOOSE: staging/{ModName}/ → Copy entire to Starbound/mods/{ModName}/
   - If PAK: staging/{ModName}/ → Pack via asset_packer.exe → Starbound/mods/{ModName}.pak
3. Result: ONE mod in Starbound/mods/ (either folder or .pak, never both)

[KEY_INVARIANT]
Only ONE format appears in Starbound/mods/ - mutually exclusive.
If user re-exports with different format, old one is REMOVED first.

[FUNCTIONS]
FN_001: export_mod_loose(staging_mod_path, starbound_mods_path, logger=None) → (bool, str, str)
FN_002: export_mod_pak(staging_mod_path, starbound_mods_path, starbound_path, logger=None) → (bool, str, str)
FN_003: get_mod_name_from_path(path) → str
FN_004: remove_existing_mod(starbound_mods_path, mod_name, all_variations=True) → bool

[RETURN_VALUES]
All exports return: (success: bool, message: str, installed_path: str)
- success: False if failed
- message: Human-readable status/error
- installed_path: Path where mod was installed (or empty string on failure)
"""

import shutil
from pathlib import Path
from typing import Tuple


def get_mod_name_from_path(path: Path) -> str:
    """
    Extract mod name from staging mod path.
    
    Example: Path('staging/My Awesome Mod') → 'My Awesome Mod'
    """
    return Path(path).name


def remove_existing_mod(
    starbound_mods_path: Path,
    mod_name: str,
    all_variations: bool = True,
    logger=None
) -> bool:
    """
    Remove existing mod with same name from Starbound/mods/ folder.
    
    Handles both formats:
    - Loose: Remove {ModName}/ folder
    - Pak: Remove {ModName}.pak file
    
    Args:
        starbound_mods_path: Path to Starbound/mods/
        mod_name: Name of mod to remove (without .pak extension)
        all_variations: If True, remove both folder AND .pak (cleanup both formats)
        logger: Optional logger
    
    Returns:
        True if removed or didn't exist, False on error
    """
    try:
        starbound_mods_path = Path(starbound_mods_path)
        
        # Check for loose files version
        loose_path = starbound_mods_path / mod_name
        if loose_path.exists() and loose_path.is_dir():
            if logger:
                logger.log(f"Removing existing loose mod: {loose_path}")
            shutil.rmtree(loose_path)
        
        # Check for pak file version
        pak_path = starbound_mods_path / f"{mod_name}.pak"
        if pak_path.exists() and pak_path.is_file():
            if logger:
                logger.log(f"Removing existing pak file: {pak_path}")
            pak_path.unlink()
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to remove existing mod: {e}")
        return False


def export_mod_loose(
    staging_mod_path: Path,
    starbound_mods_path: Path,
    logger=None
) -> Tuple[bool, str, str]:
    """
    Export mod as loose files to Starbound/mods/
    
    Action: Copy staging/{ModName}/ → Starbound/mods/{ModName}/
    
    Args:
        staging_mod_path: Path to staging/{ModName}/ (source)
        starbound_mods_path: Path to Starbound/mods/ (destination parent)
        logger: Optional logger
    
    Returns:
        (success, message, installed_path)
    """
    try:
        staging_mod_path = Path(staging_mod_path)
        starbound_mods_path = Path(starbound_mods_path)
        
        if not staging_mod_path.exists():
            msg = f"Staging mod not found: {staging_mod_path}"
            if logger:
                logger.error(msg)
            return False, msg, ""
        
        mod_name = get_mod_name_from_path(staging_mod_path)
        destination = starbound_mods_path / mod_name
        
        # Remove any existing version (loose or pak)
        remove_existing_mod(starbound_mods_path, mod_name, all_variations=True, logger=logger)
        
        # Copy entire folder
        if logger:
            logger.log(f"Copying loose mod: {staging_mod_path} → {destination}")
        
        shutil.copytree(staging_mod_path, destination, dirs_exist_ok=False)
        
        if not destination.exists():
            msg = f"Loose mod installation failed: folder not created at {destination}"
            if logger:
                logger.error(msg)
            return False, msg, ""
        
        msg = f"✓ Mod installed as loose files: {mod_name}/"
        if logger:
            logger.log(msg)
        
        return True, msg, str(destination)
        
    except Exception as e:
        msg = f"Exception exporting loose mod: {str(e)}"
        if logger:
            logger.error(msg)
        return False, msg, ""


def export_mod_pak(
    staging_mod_path: Path,
    starbound_mods_path: Path,
    starbound_path: Path,
    logger=None
) -> Tuple[bool, str, str]:
    """
    Export mod as .pak file to Starbound/mods/
    
    Action:
    1. Create pak from staging/{ModName}/ using asset_packer.exe
    2. Install to Starbound/mods/{ModName}.pak
    
    Args:
        staging_mod_path: Path to staging/{ModName}/ (source)
        starbound_mods_path: Path to Starbound/mods/ (destination parent)
        starbound_path: Path to Starbound root (to find asset_packer.exe)
        logger: Optional logger
    
    Returns:
        (success, message, installed_path)
    """
    try:
        staging_mod_path = Path(staging_mod_path)
        starbound_mods_path = Path(starbound_mods_path)
        starbound_path = Path(starbound_path)
        
        if not staging_mod_path.exists():
            msg = f"Staging mod not found: {staging_mod_path}"
            if logger:
                logger.error(msg)
            return False, msg, ""
        
        mod_name = get_mod_name_from_path(staging_mod_path)
        pak_destination = starbound_mods_path / f"{mod_name}.pak"
        
        # Remove any existing version (loose or pak)
        remove_existing_mod(starbound_mods_path, mod_name, all_variations=True, logger=logger)
        
        # Create pak file
        from .pak_manager import create_pak_from_folder
        success, pak_msg = create_pak_from_folder(
            staging_mod_path,
            pak_destination,
            starbound_path,
            logger=logger
        )
        
        if not success:
            msg = f"Pak creation failed: {pak_msg}"
            if logger:
                logger.error(msg)
            return False, msg, ""
        
        if not pak_destination.exists():
            msg = f"Pak installation failed: file not created at {pak_destination}"
            if logger:
                logger.error(msg)
            return False, msg, ""
        
        pak_size_mb = pak_destination.stat().st_size / (1024 * 1024)
        msg = f"✓ Mod installed as pak file: {mod_name}.pak ({pak_size_mb:.2f} MB)"
        if logger:
            logger.log(msg)
        
        return True, msg, str(pak_destination)
        
    except Exception as e:
        msg = f"Exception exporting pak mod: {str(e)}"
        if logger:
            logger.error(msg)
        return False, msg, ""
