
# ================= STARBOUND LOGGER NAMING RULE =====================
# Log files MUST always be named and ordered as:
#   starsoundlog1_DATE-TIME.txt
#   starsoundlog2_DATE-TIME.txt
#   starsoundlog3_DATE-TIME.txt
# ...and so on, with the number always increasing, never resetting or skipping,
# and always matching the order in which the logs were created.
#
# Do NOT use only timestamps for log file names. The number must always be present and incremented.
# ====================================================================

# --- Singleton logger instance for global use ---
_logger_instance = None

def get_logger():
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StarSoundLogger()
    return _logger_instance
# logger.py
# Simple logging system for Starbound Music Mod Generator (Python)
import os
import datetime
from pathlib import Path


import platform
import getpass
import glob

class StarSoundLogger:
    def log(self, message, level='INFO', context=None):
        """
        Append a log entry to the session log file, then overwrite AStarSoundlog_current.txt with the latest log.
        context: string or list of tags for the [context/tags] field.
        """
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if context is None:
            context_str = 'General'
        elif isinstance(context, (list, tuple)):
            context_str = ', '.join(str(tag) for tag in context)
        else:
            context_str = str(context)
        entry = f'[{timestamp}] [{level}] [{context_str}] {message}\n'
        # Only write header if file does not exist
        if not os.path.exists(self.log_path):
            self._write_header()
        # Append log entry to session log
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(entry)
        except Exception as e:
            print(f'[LOGGER ERROR] Failed to append log: {e}')
        # Overwrite AStarSoundlog_current.txt with the latest session log
        try:
            current_log = os.path.join(os.path.dirname(__file__), '..', 'starsoundlogs', 'AStarSoundlog_current.txt')
            with open(self.log_path, 'r', encoding='utf-8') as src, open(current_log, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        except Exception as e:
            print(f'[LOGGER ERROR] Failed to update current log: {e}')

    def warn(self, message, context=None):
        self.log(message, level='WARNING', context=context)

    def error(self, message, context=None):
        self.log(message, level='ERROR', context=context)
    def __init__(self):
        # Always create a new sequentially numbered log file for each session
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'starsoundlogs')
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        # Find the next available log number
        existing_logs = sorted(Path(log_dir).glob('starsoundlog*_*.txt'), key=lambda f: f.stat().st_mtime)
        max_num = 0
        for log in existing_logs:
            name = log.stem
            if name.startswith('starsoundlog'):
                parts = name.split('_')[0]  # e.g. 'starsoundlog1'
                num_part = ''.join(filter(str.isdigit, parts.replace('starsoundlog', '')))
                if num_part.isdigit():
                    max_num = max(max_num, int(num_part))
        next_num = max_num + 1
        self.log_path = os.path.join(log_dir, f'starsoundlog{next_num}_{timestamp}.txt')
        # Keep only the 10 most recent logs, delete older ones
        if len(existing_logs) >= 10:
            for old_log in existing_logs[:-9]:
                try:
                    os.remove(old_log)
                except Exception as e:
                    print(f'[LOGGER WARNING] Failed to delete old log: {old_log} ({e})')
        self.session_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.session_metadata = {
            'mod_name': None,
            'mod_path': None,
            'game_path': None,
            'ffmpeg_path': None,
            'session_mode': 'GUI',
            'user_language': os.environ.get('LANG', 'Unknown'),
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'gui_theme': None,
            'last_action': None
        }
        self._write_header()

    def update_metadata(self, **kwargs):
        """
        Update the session_metadata dictionary with new values.
        Only updates keys that already exist in session_metadata.
        After updating, rewrite the header at the top of the log file with the new metadata, preserving all log entries below.
        """
        if not hasattr(self, 'session_metadata') or self.session_metadata is None:
            self.session_metadata = {}
        for key, value in kwargs.items():
            if key in self.session_metadata:
                self.session_metadata[key] = value
        # Rewrite the header with updated metadata
        self._rewrite_header_with_metadata()

    def _rewrite_header_with_metadata(self):
        """
        Rewrites the header at the top of the log file with the current metadata, preserving all log entries below.
        """
        header_marker = '=================== StarSound Log File ===================='  # Used to detect header
        # Generate new header
        try:
            import psutil
        except Exception:
            psutil = None
        try:
            user = getpass.getuser()
        except Exception:
            user = 'Unknown'
        try:
            now = datetime.datetime.now()
        except Exception:
            now = 'Unknown'
        try:
            os_info = f'{platform.system()} {platform.release()} ({platform.machine()})'
        except Exception:
            os_info = 'Unknown'
        app_version = '1.0.0'
        node_version = 'N/A (Python)'
        debug_mode = 'Yes' if __debug__ else 'No'
        try:
            cpu_core_count = psutil.cpu_count(logical=True) if psutil else 'Unknown'
        except Exception:
            cpu_core_count = 'Unknown'
        try:
            total_memory_mb = int(psutil.virtual_memory().total / (1024 * 1024)) if psutil else 'Unknown'
        except Exception:
            total_memory_mb = 'Unknown'
        try:
            high_res_time = f'{datetime.datetime.now().isoformat()}'
        except Exception:
            high_res_time = 'Unknown'

        header_lines = [
            header_marker,
            '',
        ]
        if now != 'Unknown':
            header_lines.append(f'Local Date/Time: {now.strftime("%m/%d/%Y %I:%M:%S %p %Z")}')
            header_lines.append(f'Session Start: {now.isoformat()}')
        header_lines.append(f'Session ID: {self.session_id}')
        if app_version not in ('Unknown', 'N/A'):
            header_lines.append(f'App Version: {app_version}')
        if os_info not in ('Unknown', 'N/A'):
            header_lines.append(f'OS: {os_info}')
        if node_version not in ('Unknown', 'N/A'):
            header_lines.append(f'Node.js: {node_version}')
        if user not in ('Unknown', 'N/A'):
            header_lines.append(f'User: {user}')
        if debug_mode not in ('Unknown', 'N/A'):
            header_lines.append(f'Debug Mode: {debug_mode}')
        if cpu_core_count not in ('Unknown', 'N/A', 'Unknown'):
            header_lines.append(f'CPU Core Count: {cpu_core_count}')
        if total_memory_mb not in ('Unknown', 'N/A', 'Unknown'):
            header_lines.append(f'Total Memory: {total_memory_mb} MB')
        if high_res_time not in ('Unknown', 'N/A'):
            header_lines.append(f'High-Resolution Time: {high_res_time}')
        header_lines.append('')
        header_lines.append('------------------ APP METADATA START --------------------')
        meta = self._format_metadata_kv(self.session_metadata)
        if meta:
            header_lines.append(meta)
        header_lines.append('------------------ APP METADATA END ----------------------')
        header_lines.append('')
        header_lines.append('Log Format: [timestamp] [LEVEL] [context/tags] message')
        header_lines.append('')
        header_lines.append('------------------ BOOT COMPLETE -------------------------')
        header_lines.append('')
        header_str = '\n'.join(header_lines)

        # Read the existing log file, skip old header if present
        log_entries = ''
        if os.path.exists(self.log_path):
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            # Find where the header ends (after BOOT COMPLETE)
            end_idx = 0
            for i, line in enumerate(lines):
                if '------------------ BOOT COMPLETE -------------------------' in line:
                    end_idx = i + 1
                    break
            log_entries = ''.join(lines[end_idx:])
        # Write new header + old log entries
        try:
            with open(self.log_path, 'w', encoding='utf-8') as f:
                f.write(header_str)
                if log_entries:
                    f.write(log_entries if log_entries.startswith('\n') else '\n' + log_entries)
        except Exception as e:
            print(f'[LOGGER ERROR] Failed to rewrite log header: {e}')

    def _format_metadata_kv(self, meta):
        return '\n'.join(f'{k}: {v}' for k, v in meta.items() if v not in (None, '', 'Unknown'))

    def _write_header(self):
        header_marker = '=================== StarSound Log File ===================='  # Used to detect header
        header_lines = []
        try:
            import psutil
        except Exception:
            psutil = None
        try:
            user = getpass.getuser()
        except Exception:
            user = 'Unknown'
        try:
            now = datetime.datetime.now()
        except Exception:
            now = 'Unknown'
        try:
            os_info = f'{platform.system()} {platform.release()} ({platform.machine()})'
        except Exception:
            os_info = 'Unknown'
        app_version = '1.0.0'
        node_version = 'N/A (Python)'
        debug_mode = 'Yes' if __debug__ else 'No'
        try:
            cpu_core_count = psutil.cpu_count(logical=True) if psutil else 'Unknown'
        except Exception:
            cpu_core_count = 'Unknown'
        try:
            total_memory_mb = int(psutil.virtual_memory().total / (1024 * 1024)) if psutil else 'Unknown'
        except Exception:
            total_memory_mb = 'Unknown'
        try:
            high_res_time = f'{datetime.datetime.now().isoformat()}'
        except Exception:
            high_res_time = 'Unknown'

        header_lines = [
            header_marker,
            '',
        ]
        if now != 'Unknown':
            header_lines.append(f'Local Date/Time: {now.strftime("%m/%d/%Y %I:%M:%S %p %Z")}')
            header_lines.append(f'Session Start: {now.isoformat()}')
        header_lines.append(f'Session ID: {self.session_id}')
        if app_version not in ('Unknown', 'N/A'):
            header_lines.append(f'App Version: {app_version}')
        if os_info not in ('Unknown', 'N/A'):
            header_lines.append(f'OS: {os_info}')
        if node_version not in ('Unknown', 'N/A'):
            header_lines.append(f'Node.js: {node_version}')
        if user not in ('Unknown', 'N/A'):
            header_lines.append(f'User: {user}')
        if debug_mode not in ('Unknown', 'N/A'):
            header_lines.append(f'Debug Mode: {debug_mode}')
        if cpu_core_count not in ('Unknown', 'N/A', 'Unknown'):
            header_lines.append(f'CPU Core Count: {cpu_core_count}')
        if total_memory_mb not in ('Unknown', 'N/A', 'Unknown'):
            header_lines.append(f'Total Memory: {total_memory_mb} MB')
        if high_res_time not in ('Unknown', 'N/A'):
            header_lines.append(f'High-Resolution Time: {high_res_time}')
        header_lines.append('')
        header_lines.append('------------------ APP METADATA START --------------------')
        meta = self._format_metadata_kv(self.session_metadata)
        if meta:
            header_lines.append(meta)
        header_lines.append('------------------ APP METADATA END ----------------------')
        header_lines.append('')
        header_lines.append('Log Format: [timestamp] [LEVEL] [context/tags] message')
        header_lines.append('')
        header_lines.append('------------------ BOOT COMPLETE -------------------------')
        header_lines.append('')
        header_str = '\n'.join(header_lines)

        # Check if file exists and if header is present
        needs_header = True
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line == header_marker:
                        needs_header = False
            except Exception:
                pass

        if needs_header:
            # Prepend header to existing log (if any)
            try:
                old_content = ''
                if os.path.exists(self.log_path):
                    with open(self.log_path, 'r', encoding='utf-8') as f:
                        old_content = f.read()
                with open(self.log_path, 'w', encoding='utf-8') as f:
                    f.write(header_str)
                    if old_content:
                        f.write(old_content if old_content.startswith('\n') else '\n' + old_content)
            except Exception as e:
                print(f'[LOGGER ERROR] Failed to write log header: {e}')
