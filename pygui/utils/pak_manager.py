"""
[SYSTEM] pak_manager.py - Starbound Pak File Creation
[VERSION] 1.0
[ROLE] Pak Packer Handler
[ARCHITECTURE_ID] MOD_EXPORT_v1::PAK_CREATOR

[PURPOSE]
Wraps Starbound's native asset_packer.exe to create .pak files from mod folders.
.pak files are compressed Starbound mod packages that can be directly installed to Starbound/mods/

[KEY_PRINCIPLE]
Uses official Starbound tooling (asset_packer.exe) not third-party libraries.
This ensures compatibility and reduces external dependencies.

[FUNCTIONS]
FN_001: create_pak_from_folder(mod_folder_path, output_pak_path, logger=None) → (bool, str)
FN_002: find_asset_packer(starbound_path) → Path | None
FN_003: validate_pak_creation(pak_path) → bool

[DATA_DEPENDENCIES]
Input:  mod_folder_path (Path to staging/{ModName}/ with complete mod structure)
        output_pak_path (Path where to write {ModName}.pak)
        starbound_path (Path to Starbound installation)
Output: pak_file at output_pak_path (binary, ready to install)

[ERROR_HANDLING]
- asset_packer.exe not found → Return (False, error_message)
- Input folder missing → Return (False, error_message)
- Pak creation fails → Return (False, stderr_output)
- Permission denied → Return (False, error_message)
"""

import subprocess
from pathlib import Path
from typing import Tuple


def find_asset_packer(starbound_path: Path) -> Path | None:
    """
    Locate asset_packer.exe in Starbound installation.
    
    Expected location: {starbound_path}/win32/asset_packer.exe
    (Mirrors asset_unpacker.exe location)
    
    Returns: Path to asset_packer.exe or None if not found
    """
    if not starbound_path:
        return None
    
    potential_paths = [
        starbound_path / 'win32' / 'asset_packer.exe',
        starbound_path / 'win64' / 'asset_packer.exe',  # Fallback if win32 doesn't exist
    ]
    
    for packer_path in potential_paths:
        if packer_path.exists():
            return packer_path
    
    return None


def create_pak_from_folder(
    mod_folder_path: Path,
    output_pak_path: Path,
    starbound_path: Path,
    logger=None
) -> Tuple[bool, str]:
    """
    Create a .pak file from a mod folder using Starbound's asset_packer.exe
    
    Args:
        mod_folder_path: Path to staging/{ModName}/ (source - has music/, biomes/, etc.)
        output_pak_path: Path where to write {ModName}.pak (destination)
        starbound_path: Path to Starbound installation (to find asset_packer.exe)
        logger: Optional logger object for feedback
    
    Returns:
        (success: bool, message: str)
        - On success: (True, "Pak file created at {path}")
        - On failure: (False, "Error message explaining why")
    
    Raises:
        None (all exceptions caught and returned as (False, message))
    """
    try:
        # Validate inputs
        mod_folder_path = Path(mod_folder_path)
        if not mod_folder_path.exists():
            msg = f"Mod folder not found: {mod_folder_path}"
            if logger:
                logger.error(msg)
            return False, msg
        
        # Find asset_packer.exe
        packer_path = find_asset_packer(starbound_path)
        if not packer_path:
            msg = f"asset_packer.exe not found in {starbound_path}"
            if logger:
                logger.error(msg)
            return False, msg
        
        # Ensure output directory exists
        output_pak_path = Path(output_pak_path)
        output_pak_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build command: asset_packer.exe <input_folder> <output_pak>
        cmd = [
            str(packer_path),
            str(mod_folder_path),
            str(output_pak_path)
        ]
        
        if logger:
            logger.log(f'Creating pak file: {" ".join(cmd)}', context='PakManager')
        
        # Run asset_packer.exe
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        
        # Check result
        if process.returncode != 0:
            msg = f"asset_packer.exe failed: {stderr}"
            if logger:
                logger.error(msg)
            return False, msg
        
        # Validate pak was created
        if not output_pak_path.exists():
            msg = f"Pak file was not created at {output_pak_path}"
            if logger:
                logger.error(msg)
            return False, msg
        
        pak_size_mb = output_pak_path.stat().st_size / (1024 * 1024)
        msg = f"✓ Pak file created: {output_pak_path.name} ({pak_size_mb:.2f} MB)"
        if logger:
            logger.log(msg)
        
        return True, msg
        
    except Exception as e:
        msg = f"Exception creating pak file: {str(e)}"
        if logger:
            logger.error(msg)
        return False, msg


def validate_pak_creation(pak_path: Path) -> bool:
    """
    Verify that a pak file exists and has reasonable size (> 1KB).
    
    Args:
        pak_path: Path to .pak file to validate
    
    Returns:
        True if pak exists and is > 1KB, False otherwise
    """
    pak_path = Path(pak_path)
    if not pak_path.exists():
        return False
    
    if pak_path.stat().st_size < 1024:  # Less than 1KB indicates empty/corrupted
        return False
    
    return True
