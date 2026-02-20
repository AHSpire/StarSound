import re

# --- Filename Sanitization ---
def sanitize_filename(name: str) -> str:
    """
    Converts a string to a safe filename:
    - Lowercase
    - Spaces and dots to underscores
    - Removes special characters (letters, numbers, underscores only)
    - Collapses multiple underscores
    - Strips leading/trailing underscores
    """
    sanitized = name.replace(' ', '_').replace('.', '_').replace('-', '_')
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', sanitized)
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.lower().strip('_')

import os
import subprocess
import sys
import shutil

def ensure_ffmpeg_installed():
    """
    Ensures ffmpeg is available: always prefer local install in utils/ffmpeg-8.0.1-full_build/bin/ffmpeg.exe (Windows) or ffmpeg (Linux/Mac), fallback to PATH.
    Returns (success: bool, message: str, ffmpeg_path: str)
    """
    import sys
    ffmpeg_local = os.path.join(os.path.dirname(__file__), 'ffmpeg-8.0.1-full_build', 'bin', 'ffmpeg.exe')
    if os.path.isfile(ffmpeg_local):
        return True, 'ffmpeg found in utils/ffmpeg-8.0.1-full_build/bin', ffmpeg_local
    # Fallback: check PATH (cross-platform)
    ffmpeg_name = 'ffmpeg.exe' if sys.platform.startswith('win') else 'ffmpeg'
    import shutil
    ffmpeg_path = shutil.which(ffmpeg_name)
    if ffmpeg_path:
        return True, 'ffmpeg found in PATH', ffmpeg_path
    return False, 'ffmpeg not found in local folder or PATH', ''

def convert_to_wav(input_path, output_path):
    """
    Converts input audio file to WAV using ffmpeg.
    Returns (success: bool, message: str)
    """
    success, msg, ffmpeg_path = ensure_ffmpeg_installed()
    if not success:
        return False, f"FFmpeg not available: {msg}"
    try:
        # Lower volume by 50% using ffmpeg's volume filter
        cmd = [ffmpeg_path, '-y', '-i', input_path, '-filter:a', 'volume=0.3', output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, f"Converted to {output_path} (volume reduced)"
        else:
            return False, f"ffmpeg error: {result.stderr}"
    except Exception as e:
        return False, f"Conversion failed: {e}"

if __name__ == '__main__':
    # Utility: Fix ship_confirm.wav from ship_confirm1.ogg
    sfx_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sfx')
    ogg_path = os.path.join(sfx_dir, 'ship_confirm1.ogg')
    wav_path = os.path.join(sfx_dir, 'ship_confirm.wav')
    ok, msg = convert_to_wav(ogg_path, wav_path)
    print('WAV conversion:', msg)
# audio_utils.py
# Audio validation and conversion utilities for Starbound Music Mod Generator (Python)

import os
import subprocess
import sys
import shutil

# Maximum allowed audio file size (500 MB) - prevents crashes and playback issues in Starbound
MAX_FILE_SIZE = 500 * 1024 * 1024

def ensure_ffmpeg_installed():
    ffmpeg_local = os.path.join(os.path.dirname(__file__), 'ffmpeg-8.0.1-full_build', 'bin', 'ffmpeg.exe')
    if os.path.isfile(ffmpeg_local):
        return True, 'ffmpeg found in utils/ffmpeg-8.0.1-full_build/bin', ffmpeg_local
    ffmpeg_name = 'ffmpeg.exe' if sys.platform.startswith('win') else 'ffmpeg'
    ffmpeg_path = shutil.which(ffmpeg_name)
    if ffmpeg_path:
        return True, 'ffmpeg found in PATH', ffmpeg_path
    return False, 'ffmpeg not found in local folder or PATH', ''


def validate_file_exists(file_path):
    return os.path.isfile(file_path)

def validate_file_size(file_path):
    """
    Validates that audio file does not exceed 500MB size limit.
    Large files can crash the game or cause playback issues in Starbound.
    Returns (valid: bool, file_size_mb: float, message: str)
    """
    try:
        if not os.path.isfile(file_path):
            return False, 0, f"File not found: {file_path}"
        
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size > MAX_FILE_SIZE:
            return False, file_size_mb, f"File is too large ({file_size_mb:.1f}MB). Maximum allowed size is 500MB."
        
        return True, file_size_mb, "OK"
    except Exception as e:
        return False, 0, f"Error checking file size: {e}"

def validate_file_duration(file_path, max_minutes=30):
    """
    Uses ffprobe to get audio duration in seconds.
    Returns (valid: bool, duration_seconds: float, message: str)
    """
    ffprobe_path = os.path.join(os.path.dirname(__file__), 'ffmpeg-8.0.1-full_build', 'bin', 'ffprobe.exe')
    try:
        result = subprocess.run([
            ffprobe_path, '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', file_path
        ], capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        duration_minutes = duration / 60
        if duration_minutes > max_minutes:
            return False, duration, f"File is {duration_minutes:.1f} minutes - exceeds {max_minutes} minute limit"
        return True, duration, "OK"
    except Exception as e:
        return False, 0, f"Error reading duration: {e}"

def get_audio_duration(file_path):
    """
    Extract audio file duration using ffprobe.
    Returns duration in minutes as float, or None on error.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        float: Duration in minutes, or None if unable to determine
    """
    ffprobe_path = os.path.join(os.path.dirname(__file__), 'ffmpeg-8.0.1-full_build', 'bin', 'ffprobe.exe')
    try:
        result = subprocess.run([
            ffprobe_path, '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', file_path
        ], capture_output=True, text=True, check=True)
        
        duration_seconds = float(result.stdout.strip())
        duration_minutes = duration_seconds / 60.0
        return duration_minutes
    except Exception as e:
        # Silently fail - return None if unable to get duration
        return None

def split_audio_file(file_path: str, segment_length_minutes: int = 25, logger=None) -> dict:
    """
    Split audio file into manageable segments using FFmpeg.
    
    Uses FFmpeg's segment muxer to split file into chunks without re-encoding
    (fast operation, preserves quality). Output files are WAV format for lossless
    processing. Final naming convention: original_track_part1.wav, original_track_part2.wav, etc.
    
    WAV segments will later receive blanket audio processing before final OGG conversion.
    
    Args:
        file_path: Path to audio file to split
        segment_length_minutes: Target segment duration in minutes (default 25)
        logger: Optional Logger object for debug output
        
    Returns:
        dict: {
            'success': bool,
            'split_files': ['/path/to/part1.wav', '/path/to/part2.wav', ...],
            'segment_durations': [24.5, 24.3, 18.2],  # minutes per segment
            'segment_count': int,
            'message': str
        }
    """
    def log_msg(msg: str):
        if logger:
            logger.log(f'[SPLIT] {msg}')
        else:
            print(f'[SPLIT] {msg}')
    
    # DEBUG: Verify segment_length parameter received
    log_msg(f'SPLIT FUNCTION CALLED with segment_length_minutes={segment_length_minutes} (type: {type(segment_length_minutes).__name__})')
    if segment_length_minutes is None or segment_length_minutes <= 0:
        log_msg(f'WARNING: Invalid segment_length_minutes={segment_length_minutes}, resetting to 25')
        segment_length_minutes = 25
    
    try:
        # Validate input file exists
        if not os.path.isfile(file_path):
            return {
                'success': False,
                'split_files': [],
                'segment_durations': [],
                'segment_count': 0,
                'message': f'File not found: {file_path}'
            }
        
        # Get total duration
        total_duration_minutes = get_audio_duration(file_path)
        if not total_duration_minutes:
            return {
                'success': False,
                'split_files': [],
                'segment_durations': [],
                'segment_count': 0,
                'message': f'Could not determine audio duration'
            }
        
        # Calculate segment count and duration in seconds
        segment_length_seconds = segment_length_minutes * 60
        total_duration_seconds = total_duration_minutes * 60
        segment_count = -(-int(total_duration_seconds) // segment_length_seconds)  # Ceiling division
        
        log_msg(f'Splitting {file_path} ({total_duration_minutes:.1f} min) into {segment_count} segments')
        log_msg(f'DEBUG: Using {segment_length_minutes} min per segment = {segment_length_seconds} seconds ({segment_length_seconds} -segment_time param)')
        
        # Get FFmpeg path
        ffmpeg_dir = os.path.join(os.path.dirname(__file__), 'ffmpeg-8.0.1-full_build', 'bin')
        ffmpeg_path = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
        
        if not os.path.isfile(ffmpeg_path):
            return {
                'success': False,
                'split_files': [],
                'segment_durations': [],
                'segment_count': 0,
                'message': 'FFmpeg not found'
            }
        
        # Create temp directory for segment output
        input_dir = os.path.dirname(file_path)
        temp_dir = os.path.join(input_dir, '.starsound_splits_temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Run FFmpeg segment command
        # -vn: Skip video streams (handles embedded cover art in MP3s)
        # -f segment: output format is segments
        # -segment_time: duration of each segment in seconds
        # -segment_format: format of each segment (WAV for lossless)
        # -reset_timestamps: reset timestamps for each segment (important for seamless playback)
        # -c:a pcm_s16le: PCM 16-bit audio codec (standard for WAV, no quality loss)
        # Audio processing and final OGG conversion happens AFTER splitting
        segment_pattern = os.path.join(temp_dir, 'segment_%03d.wav')
        
        cmd = [
            ffmpeg_path,
            '-i', file_path,
            '-vn',  # ← NO VIDEO (skip embedded cover art, metadata, etc)
            '-f', 'segment',
            '-segment_time', str(segment_length_seconds),
            '-segment_format', 'wav',
            '-reset_timestamps', '1',
            '-c:a', 'pcm_s16le',  # ← PCM audio (standard WAV codec, lossless)
            '-y',  # Overwrite without asking
            segment_pattern
        ]
        
        log_msg(f'Running FFmpeg: {" ".join(cmd[:5])}...')
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10-minute timeout
        
        if result.returncode != 0:
            return {
                'success': False,
                'split_files': [],
                'segment_durations': [],
                'segment_count': 0,
                'message': f'FFmpeg error: {result.stderr}'
            }
        
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Rename segments to follow naming convention
        # segment_000.wav → base_name_part1.wav, base_name_part2.wav, etc.
        split_files = []
        segment_durations = []
        
        for i in range(segment_count):
            temp_file = os.path.join(temp_dir, f'segment_{i:03d}.wav')
            
            if not os.path.isfile(temp_file):
                log_msg(f'Warning: Expected segment file not found: {temp_file}')
                continue
            
            # Final name: original_track_part1.wav, original_track_part2.wav, etc.
            final_name = f'{base_name}_part{i + 1}.wav'
            final_path = os.path.join(input_dir, final_name)
            
            # Move from temp to final location
            shutil.move(temp_file, final_path)
            split_files.append(final_path)
            
            # Get duration of this segment
            segment_duration = get_audio_duration(final_path)
            if segment_duration:
                segment_durations.append(segment_duration)
            
            log_msg(f'Created: {final_name} ({segment_duration:.1f} min)' if segment_duration else f'Created: {final_name}')
        
        # Cleanup temp directory
        try:
            os.rmdir(temp_dir)
        except:
            pass  # Dir might not be empty, that's okay
        
        log_msg(f'Successfully split into {len(split_files)} segments')
        
        return {
            'success': True,
            'split_files': split_files,
            'segment_durations': segment_durations,
            'segment_count': len(split_files),
            'message': f'Successfully split into {len(split_files)} segments'
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'split_files': [],
            'segment_durations': [],
            'segment_count': 0,
            'message': 'FFmpeg operation timed out (took longer than 10 minutes)'
        }
    except Exception as e:
        return {
            'success': False,
            'split_files': [],
            'segment_durations': [],
            'segment_count': 0,
            'message': f'Unexpected error during splitting: {str(e)}'
        }

def validate_file_format(file_path):
    """
    Uses ffprobe to check if file is OGG and 44100Hz.
    Returns (valid: bool, message: str)
    """
    ffprobe_path = os.path.join(os.path.dirname(__file__), 'ffmpeg-8.0.1-full_build', 'bin', 'ffprobe.exe')
    try:
        result = subprocess.run([
            ffprobe_path, '-v', 'error', '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_name,sample_rate',
            '-of', 'default=noprint_wrappers=1', file_path
        ], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        codec = None
        sample_rate = None
        for line in lines:
            if line.startswith('codec_name='):
                codec = line.split('=', 1)[1]
            if line.startswith('sample_rate='):
                sample_rate = line.split('=', 1)[1]
        if codec != 'vorbis' or sample_rate != '44100':
            return False, f"File must be OGG (vorbis) and 44100Hz. Got codec={codec}, sample_rate={sample_rate}"
        return True, "OK"
    except Exception as e:
        return False, f"Error reading format: {e}"

def check_audio_quality(file_path):
    """
    Check for audio quality issues: peak clipping, very low volume, etc.
    Returns (has_issues: bool, warnings: list_of_strings)
    
    Note: This is informational only. Invalid readings (like -inf dB) are skipped.
    """
    warnings = []
    ffmpeg_path, ffprobe_path = None, None
    
    try:
        # Find ffmpeg paths
        ffmpeg_dir = os.path.join(os.path.dirname(__file__), 'ffmpeg-8.0.1-full_build', 'bin')
        ffmpeg_path = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
        ffprobe_path = os.path.join(ffmpeg_dir, 'ffprobe.exe')
        
        if not os.path.isfile(ffmpeg_path) or not os.path.isfile(ffprobe_path):
            return False, []  # Skip check if ffmpeg not available
        
        # Check for peak levels using astats filter
        cmd = [
            ffmpeg_path,
            '-i', file_path,
            '-af', 'astats=metadata=1:reset=1',
            '-f', 'null',
            '-'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = result.stderr  # ffmpeg stats go to stderr
        
        # Parse for peak values
        peak_found = False
        for line in output.split('\n'):
            if 'Peak level dB' in line:
                try:
                    # Extract dB value (format: "Peak level dB: X.XXX")
                    db_str = line.split(':')[-1].strip().split()[0]
                    
                    # Skip invalid readings
                    if 'inf' in db_str.lower() or db_str == '-' or db_str == '':
                        continue
                    
                    peak_db = float(db_str)
                    peak_found = True
                    
                    # Warn if peak is very close to 0 dB (clipping risk)
                    if peak_db > -1.0:
                        warnings.append(f"⚠ WARNING: Audio peaks at {peak_db:.1f} dB (risk of distortion). Consider lowering source volume.")
                    elif peak_db > -6.0:
                        warnings.append(f"⚠ Audio peaks at {peak_db:.1f} dB. May need compression adjustment.")
                    elif peak_db < -40.0 and peak_found:
                        warnings.append(f"ℹ Audio soft (peaks at {peak_db:.1f} dB). Normalization can help if needed.")
                    break  # Found valid peak, stop searching
                except (ValueError, IndexError):
                    continue
        
        return len(warnings) > 0, warnings
        
    except subprocess.TimeoutExpired:
        # Quality check timed out - silently skip
        return False, []
    except Exception as e:
        # Silently fail - this is optional quality checking
        return False, []

def parse_time_string(time_str: str) -> float:
    """
    Parse time string and return total seconds.
    Supports formats like: "0hr30m0s", "30m", "0.5", "1hr30m", etc.
    """
    if not time_str:
        return 0.0
    
    time_str = time_str.strip().lower()
    
    # Try simple float conversion first (backward compatibility)
    try:
        return float(time_str)
    except ValueError:
        pass
    
    try:
        hours = 0.0
        minutes = 0.0
        seconds = 0.0
        
        # Extract hours
        if 'hr' in time_str:
            hr_parts = time_str.split('hr', 1)
            hours = float(hr_parts[0].strip()) if hr_parts[0].strip() else 0.0
            time_str = hr_parts[1] if len(hr_parts) > 1 else ""
        
        # Extract minutes
        if 'm' in time_str:
            m_parts = time_str.split('m', 1)
            m_str = m_parts[0].strip()
            minutes = float(m_str) if m_str else 0.0
            time_str = m_parts[1] if len(m_parts) > 1 else ""
        
        # Extract seconds
        if 's' in time_str:
            s_str = time_str.split('s', 1)[0].strip()
            seconds = float(s_str) if s_str else 0.0
        
        total = hours * 3600.0 + minutes * 60.0 + seconds
        return total
    except (ValueError, IndexError, AttributeError):
        return 0.0

def build_audio_filter_chain(audio_processing_options: dict) -> str:
    """
    Constructs FFmpeg audio filter chain based on selected processing options.
    Filters applied in professional mastering order:
    1. Silence Trimming
    2. Sonic Scrubber (Noise reduction)
    3. Compression
    4. Soft Clipping/Limiting
    5. 3-Band EQ
    6. De-Esser (Sibilance reduction)
    7. Audio Normalization
    8. Stereo to Mono (optional channel conversion)
    9. Fade In/Out
    
    Args:
        audio_processing_options: dict with keys:
            - silence_trim (bool)
            - sonic_scrubber (bool)
            - compression (bool)
            - compression_preset ('gentle', 'moderate', 'aggressive') 
            - soft_clip (bool)
            - eq (bool)
            - eq_preset ('warm', 'bright', 'dark')
            - de_esser (bool)
            - stereo_to_mono (bool)
            - fade (bool)
            - fade_in_duration (float) - seconds
            - fade_out_start (float) - when to begin fade in seconds
            - fade_out_duration (float) - how long fade takes in seconds
    
    Returns: FFmpeg filter chain string (empty if no processing selected)
    """
    filters = []
    
    # LOG: Show what tools are enabled
    print("[AUDIO TOOLS DEBUG] Checking audio processing options:")
    print(f"  - trim: {audio_processing_options.get('trim')}")
    print(f"  - silence_trim: {audio_processing_options.get('silence_trim')}")
    print(f"  - sonic_scrubber: {audio_processing_options.get('sonic_scrubber')}")
    print(f"  - compression: {audio_processing_options.get('compression')}")
    print(f"  - soft_clip: {audio_processing_options.get('soft_clip')}")
    print(f"  - eq: {audio_processing_options.get('eq')}")
    print(f"  - de_esser: {audio_processing_options.get('de_esser')}")
    print(f"  - normalize: {audio_processing_options.get('normalize')}")
    print(f"  - stereo_to_mono: {audio_processing_options.get('stereo_to_mono')}")
    print(f"  - fade: {audio_processing_options.get('fade')}")
    
    # SAFETY CHECK: If silence_trim is True, log it loudly
    if audio_processing_options.get('silence_trim'):
        print("[AUDIO TOOLS DEBUG] ⚠️ WARNING: SILENCE_TRIM IS ENABLED - This will remove leading/trailing silence!")
    
    # Stage 1: Audio Trimmer (precise start/end time control)
    # Applied first so all downstream effects work on the trimmed segment
    if audio_processing_options.get('trim'):
        trim_start = audio_processing_options.get('trim_start_time', '0hr0m0s')
        trim_end = audio_processing_options.get('trim_end_time', '0hr30m0s')  # Starbound max: 30 min
        try:
            # Parse time strings (supports "0hr30m0s" or simple floating point format)
            trim_start_sec = parse_time_string(str(trim_start))
            trim_end_sec = parse_time_string(str(trim_end))
            # atrim: start=X:end=Y (in seconds)
            filters.append(f'atrim=start={trim_start_sec}:end={trim_end_sec}')
        except (ValueError, TypeError):
            # Invalid trim times, skip trimming
            pass
    
    # Stage 2: Silence Trimming
    if audio_processing_options.get('silence_trim'):
        filter_params = []
        
        # Trim Start
        if audio_processing_options.get('silence_trim_start'):
            threshold_text = audio_processing_options.get('silence_threshold_start', '-60dB (default)')
            threshold = threshold_text.split()[0] if threshold_text else '-60dB'
            
            duration_text = audio_processing_options.get('silence_duration_start', '0.1')
            try:
                duration = float(duration_text) if isinstance(duration_text, str) else duration_text
                duration = max(0.05, min(5.0, duration))
            except (ValueError, TypeError):
                duration = 0.1
            
            filter_params.append(f'start_periods=1:start_duration={duration}:start_threshold={threshold}')
        
        # Trim End
        if audio_processing_options.get('silence_trim_end'):
            threshold_text = audio_processing_options.get('silence_threshold_end', '-60dB (default)')
            threshold = threshold_text.split()[0] if threshold_text else '-60dB'
            
            duration_text = audio_processing_options.get('silence_duration_end', '0.1')
            try:
                duration = float(duration_text) if isinstance(duration_text, str) else duration_text
                duration = max(0.05, min(5.0, duration))
            except (ValueError, TypeError):
                duration = 0.1
            
            filter_params.append(f'stop_periods=1:stop_duration={duration}:stop_threshold={threshold}')
        
        # Only add silenceremove if at least one trimming is enabled
        if filter_params:
            filters.append('silenceremove=' + ':'.join(filter_params))
    
    # Stage 3: Sonic Scrubber (Noise Reduction)
    if audio_processing_options.get('sonic_scrubber'):
        filters.append('highpass=f=20')  # Remove subsonic rumble
        filters.append('lowpass=f=15000')  # Remove high-frequency hiss
    
    # Stage 3.5: SAFETY PRE-LIMITER (before EQ gains)
    # Catches peaks BEFORE they hit the EQ stage gains to prevent clipping
    # Uses soft limiting to preserve audio quality while protecting against clipping
    filters.append('alimiter=limit=0.95:attack=2:release=10')
    
    # Stage 4: Compression
    if audio_processing_options.get('compression'):
        preset = audio_processing_options.get('compression_preset', 'moderate').lower()
        if preset == 'gentle':
            # Threshold in linear scale: -20dB = 0.1
            filters.append('acompressor=threshold=0.1:ratio=4:attack=0.05:release=0.05')
        elif preset == 'aggressive':
            # Threshold in linear scale: -10dB = 0.316
            filters.append('acompressor=threshold=0.316:ratio=8:attack=0.01:release=0.01')
        else:  # moderate (default)
            # Threshold in linear scale: -15dB = 0.178
            filters.append('acompressor=threshold=0.178:ratio=6:attack=0.02:release=0.03')
    
    # Stage 5: Soft Clipping/Limiting
    # More aggressive to protect against clipping from filter stages
    # Using lower limit and faster attack to catch peaks early
    if audio_processing_options.get('soft_clip'):
        filters.append('alimiter=limit=0.92:attack=3:release=15')
    
    # Stage 6: 3-Band EQ
    # NOTE: Gains are conservative to avoid clipping after loudness boost stages
    # Peak limiting happens before EQ to catch any peaks from gain changes
    if audio_processing_options.get('eq'):
        preset = audio_processing_options.get('eq_preset', 'bright').lower()
        if preset == 'warm':
            # Bass boost +2dB (was +3), mid unchanged, treble -1.5dB (was -2)
            filters.append('lowshelf=f=200:g=2')
            filters.append('equalizer=f=1000:g=0:w=0.7')
            filters.append('highshelf=f=8000:g=-1.5')
        elif preset == 'dark':
            # Bass +1.5dB (was +2), mid +0.5dB (was +1), treble -2dB (was -3)
            filters.append('lowshelf=f=200:g=1.5')
            filters.append('equalizer=f=1000:g=0.5:w=0.7')
            filters.append('highshelf=f=8000:g=-2')
        else:  # bright (default)
            # Bass flat, mid +0.5dB (was +1) @ 1kHz, treble +2dB (was +3) @ 5kHz
            filters.append('equalizer=f=1000:g=0.5:w=0.7')
            filters.append('highshelf=f=5000:g=2')
    
    # Stage 7: De-Esser (Reduce sibilance - harsh S/T sounds)
    if audio_processing_options.get('de_esser'):
        # Target 4.5kHz where sibilance peaks with -4dB reduction
        filters.append('equalizer=f=4500:t=h:w=2:g=-4')
    
    # Stage 8: Audio Normalization
    if audio_processing_options.get('normalize'):
        filters.append('loudnorm=I=-23:TP=-1.5:LRA=7')
    
    # Stage 9: Stereo to Mono (optional channel conversion)
    if audio_processing_options.get('stereo_to_mono'):
        filters.append('aformat=channel_layouts=mono')
    
    # Stage 10: Fade In/Out (applied last for smooth envelope)
    # NOTE: Starbound has a 30-minute max track length limit. Longer tracks can crash the game.
    # Default: fade-in 0.5s (quick entry) + fade-out 30m (smooth Starbound transition).
    if audio_processing_options.get('fade'):
        fade_in = audio_processing_options.get('fade_in_duration', '0hr0m0.5s')
        fade_out_start = audio_processing_options.get('fade_out_start', '0hr30m0s')  # When to begin fading
        fade_out_duration = audio_processing_options.get('fade_out_duration', '0hr0m5s')  # How long fade takes
        try:
            # Parse time strings (supports "0hr30m0s" or simple "0.5" format)
            fade_in = parse_time_string(str(fade_in))
            fade_out_start = parse_time_string(str(fade_out_start))
            fade_out_duration = parse_time_string(str(fade_out_duration))
            
            # LOG: Show fade parameters for debugging
            print(f"[AUDIO TOOLS DEBUG] Fade settings: in={fade_in}s, out_start={fade_out_start}s, out_duration={fade_out_duration}s")
            
            filters.append(f'afade=t=in:st=0:d={fade_in}')
            filters.append(f'afade=t=out:st={fade_out_start}:d={fade_out_duration}')
        except (ValueError, TypeError):
            # Invalid fade duration, skip fades
            pass
    
    # Join all filters with commas
    final_filter = ','.join(filters) if filters else ''
    print(f"[AUDIO TOOLS DEBUG] Final filter chain: {final_filter if final_filter else '(EMPTY - no processing selected)'}")
    return final_filter

def convert_to_ogg(input_path, output_path, bitrate='192k', audio_filter='', log_callback=None):
    """
    Converts input audio file to OGG Vorbis 44100Hz stereo using ffmpeg.
    If log_callback is provided, streams ffmpeg output to it in real time.
    Returns (success: bool, message: str)
    """
    # Validate file size before attempting conversion (prevents crashes/issues in Starbound)
    valid, file_size_mb, size_msg = validate_file_size(input_path)
    if not valid:
        if log_callback:
            log_callback(f"File size validation failed: {size_msg}")
        return False, size_msg
    
    success, msg, ffmpeg_path = ensure_ffmpeg_installed()
    if not success:
        if log_callback:
            log_callback(f"FFmpeg not available: {msg}")
        return False, f"FFmpeg not available: {msg}"
    try:
        # LOG: Show what we're about to do
        if log_callback:
            log_callback(f"[DEBUG] Input: {input_path}")
            log_callback(f"[DEBUG] Output: {output_path}")
            log_callback(f"[DEBUG] Bitrate: {bitrate}")
            if audio_filter:
                log_callback(f"[DEBUG] Audio Filter Chain: {audio_filter}")
            else:
                log_callback(f"[DEBUG] Audio Filter Chain: (NONE - no processing)")
        
        cmd = [
            ffmpeg_path, '-y', '-i', input_path,
            '-vn', '-acodec', 'libvorbis', '-ar', '44100', '-ac', '2', '-b:a', bitrate
        ]
        
        # Add audio filter if provided
        if audio_filter:
            cmd.extend(['-af', audio_filter])
        
        cmd.append(output_path)
        
        if log_callback:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in process.stdout:
                # Suppress non-critical FFmpeg warnings about clipping
                # These are now handled by the pre-limiter stage in the filter chain
                if 'clipping' not in line.lower():
                    log_callback(line.rstrip())
            process.stdout.close()
            returncode = process.wait()
            if returncode == 0:
                return True, f"Converted to {output_path}"
            else:
                return False, f"ffmpeg error: nonzero exit code {returncode}"
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return True, f"Converted to {output_path}"
            else:
                return False, f"ffmpeg error: {result.stderr}"
    except Exception as e:
        if log_callback:
            log_callback(f"Conversion failed: {e}")
        return False, f"Conversion failed: {e}"
