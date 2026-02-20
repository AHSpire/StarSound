"""
vanilla_setup.py

Handles automatic setup of vanilla Starbound music files for track previewing.
Uses the Starbound asset_unpacker.exe to unpack packed.pak and organize music files.
"""

import subprocess
import shutil
import json
from pathlib import Path
from utils.logger import get_logger


class VanillaSetup:
    """Manages unpacking and organizing vanilla Starbound music files"""
    
    def __init__(self):
        self.logger = get_logger()
        self.starbound_path = None
        self.unpacker_path = None
        self.packed_pak_path = None
        self.vanilla_tracks_dir = None
        self.biome_tracks_json = None
    
    def initialize_paths(self, starbound_path: str, starsound_dir: str):
        """Set up all directory paths"""
        self.starbound_path = Path(starbound_path)
        self.unpacker_path = self.starbound_path / 'win32' / 'asset_unpacker.exe'
        self.packed_pak_path = self.starbound_path / 'assets' / 'packed.pak'
        self.vanilla_tracks_dir = Path(starsound_dir) / 'pygui' / 'vanilla_tracks'
        # Load biome_tracks.json from main pygui folder (always available, not dependent on vanilla_tracks)
        self.biome_tracks_json = Path(starsound_dir) / 'pygui' / 'biome_tracks.json'
    
    def check_requirements(self):
        """Check if all files needed for unpacking are available"""
        checks = {
            'unpacker': self.unpacker_path.exists(),
            'packed_pak': self.packed_pak_path.exists(),
        }
        
        self.logger.log(f'Setup requirements check: {checks}', context='VanillaSetup')
        
        if not checks['unpacker']:
            return False, f"Asset unpacker not found at {self.unpacker_path}"
        if not checks['packed_pak']:
            return False, f"packed.pak not found at {self.packed_pak_path}"
        
        return True, "All requirements met"
    
    def backup_packed_pak(self):
        """Backup the original packed.pak file before unpacking"""
        backup_dir = Path(self.vanilla_tracks_dir.parent.parent.parent) / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / 'packed.pak.backup'
        
        try:
            self.logger.log(f'Backing up packed.pak to {backup_path}', context='VanillaSetup')
            shutil.copy2(self.packed_pak_path, backup_path)
            self.logger.log('Backup complete', context='VanillaSetup')
            return True, str(backup_path)
        except Exception as e:
            self.logger.error(f'Failed to backup packed.pak: {e}', context='VanillaSetup')
            return False, str(e)
    
    def unpack_assets(self, output_dir: str, progress_callback=None):
        """Run asset_unpacker.exe to unpack packed.pak"""
        try:
            cmd = [
                str(self.unpacker_path),
                str(self.packed_pak_path),
                output_dir
            ]
            
            self.logger.log(f'Running unpacker: {" ".join(cmd)}', context='VanillaSetup')
            
            # Run unpacker with output capture
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                self.logger.error(f'Unpacker failed: {stderr}', context='VanillaSetup')
                return False, f"Unpacker error: {stderr}"
            
            self.logger.log('Unpacking complete', context='VanillaSetup')
            return True, "Assets unpacked successfully"
            
        except Exception as e:
            self.logger.error(f'Failed to run unpacker: {e}', context='VanillaSetup')
            return False, str(e)
    
    def organize_music_files(self, unpacked_dir: str, biome_tracks_data: dict):
        """Organize unpacked music files into vanilla_tracks biome structure"""
        try:
            unpacked_path = Path(unpacked_dir)
            music_source = unpacked_path / 'music'
            
            if not music_source.exists():
                return False, f"Music directory not found in unpacked assets at {music_source}"
            
            organized_count = 0
            
            # Check if biome_tracks_data has the correct format (dict with day/night keys)
            if biome_tracks_data and isinstance(biome_tracks_data, dict):
                try:
                    # Iterate through biomes (e.g., "surface/arctic", "core/blaststonecorelayer", etc.)
                    for biome_path, biome_info in biome_tracks_data.items():
                        if not isinstance(biome_info, dict):
                            continue
                        
                        day_tracks = biome_info.get('day', [])
                        night_tracks = biome_info.get('night', [])
                        
                        # Copy day tracks
                        if day_tracks:
                            day_dir = self.vanilla_tracks_dir / biome_path / 'day'
                            day_dir.mkdir(parents=True, exist_ok=True)
                            
                            for track_path in day_tracks:
                                track_name = Path(track_path).name
                                source_file = music_source / track_name
                                dest_file = day_dir / track_name
                                
                                if source_file.exists():
                                    shutil.copy2(source_file, dest_file)
                                    organized_count += 1
                        
                        # Copy night tracks
                        if night_tracks:
                            night_dir = self.vanilla_tracks_dir / biome_path / 'night'
                            night_dir.mkdir(parents=True, exist_ok=True)
                            
                            for track_path in night_tracks:
                                track_name = Path(track_path).name
                                source_file = music_source / track_name
                                dest_file = night_dir / track_name
                                
                                if source_file.exists():
                                    shutil.copy2(source_file, dest_file)
                                    organized_count += 1
                except Exception as parse_error:
                    self.logger.log(f'Error parsing biome data: {parse_error}, using fallback', context='VanillaSetup')
                    # Fall through to fallback
                    organized_count = 0
            
            # Fallback: organize all .ogg files into generic location if parsing failed
            if organized_count == 0:
                self.logger.log('Using fallback music organization (generic folder)', context='VanillaSetup')
                all_ogg_files = list(music_source.glob('*.ogg'))
                generic_day = self.vanilla_tracks_dir / 'music' / 'day'
                generic_day.mkdir(parents=True, exist_ok=True)
                for ogg_file in all_ogg_files:
                    dest = generic_day / ogg_file.name
                    shutil.copy2(ogg_file, dest)
                    organized_count += 1
            
            self.logger.log(f'Organized {organized_count} music files', context='VanillaSetup')
            return True, f"Organized {organized_count} music files"
            
        except Exception as e:
            self.logger.error(f'Failed to organize music files: {e}', context='VanillaSetup')
            return False, str(e)
    
    def cleanup_unpacked_files(self, unpacked_dir: str):
        """Remove temporary unpacked files and the entire temp directory"""
        try:
            unpacked_path = Path(unpacked_dir)
            
            # Remove the entire temp directory
            if unpacked_path.exists():
                shutil.rmtree(unpacked_path, ignore_errors=True)
            
            self.logger.log('Cleaned up temporary files and temp directory', context='VanillaSetup')
            return True, "Cleanup complete"
            
        except Exception as e:
            self.logger.error(f'Cleanup error (non-fatal): {e}', context='VanillaSetup')
            return True, "Cleanup completed with warnings"
    
    def run_full_setup(self, starbound_path: str, starsound_dir: str, progress_callback=None):
        """Execute complete setup workflow"""
        self.initialize_paths(starbound_path, starsound_dir)
        
        # Check requirements
        success, msg = self.check_requirements()
        if not success:
            return False, msg
        
        if progress_callback:
            progress_callback("Backing up your game files...")
        
        # Backup
        success, msg = self.backup_packed_pak()
        if not success:
            return False, f"Backup failed: {msg}"
        
        if progress_callback:
            progress_callback("Extracting the original music (this might take a moment)...")
        
        # Create temp directory for unpacking
        temp_unpack_dir = self.vanilla_tracks_dir.parent / '_temp_unpack'
        temp_unpack_dir.mkdir(parents=True, exist_ok=True)
        
        # Unpack
        success, msg = self.unpack_assets(str(temp_unpack_dir))
        if not success:
            return False, f"Unpacking failed: {msg}"
        
        if progress_callback:
            progress_callback("Sorting music by biome...")
        
        # Load biome_tracks.json to know which files to copy
        if not self.biome_tracks_json.exists():
            return False, f"biome_tracks.json not found at {self.biome_tracks_json}"
        
        with open(self.biome_tracks_json, 'r') as f:
            biome_tracks_data = json.load(f)
        
        # Organize music
        success, msg = self.organize_music_files(str(temp_unpack_dir), biome_tracks_data)
        if not success:
            return False, f"Organization failed: {msg}"
        
        if progress_callback:
            progress_callback("Almost done, tidying up...")
        
        # Cleanup temp files
        self.cleanup_unpacked_files(str(temp_unpack_dir))
        
        if progress_callback:
            progress_callback("Done! Music is ready to preview!")
        
        self.logger.log('Vanilla setup workflow completed successfully', context='VanillaSetup')
        return True, "Vanilla tracks setup complete! You can now preview tracks."
