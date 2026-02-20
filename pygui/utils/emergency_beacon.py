import os

def read_starbound_log(log_path):
    """
    Analyze a Starbound log file and return critical and benign errors.
    """
    if not os.path.isfile(log_path):
        return {'success': False, 'message': 'Log file does not exist.'}
    with open(log_path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    critical_errors = []
    benign_errors = []
    for line in lines:
        if is_critical_error(line):
            critical_errors.append(line.strip())
        elif is_benign_error(line):
            benign_errors.append(line.strip())
    return {
        'success': True,
        'criticalErrors': critical_errors,
        'benignErrors': benign_errors
    }

def is_critical_error(line):
    # Heuristic: lines with [Error], [Exception], [CRITICAL], or 'fatal' not matching benign patterns
    lower = line.lower()
    if '[error]' in lower or '[exception]' in lower or '[critical]' in lower or 'fatal' in lower:
        if not is_benign_error(line):
            return True
    return False

def is_benign_error(line):
    # Known benign Starbound log messages
    lower = line.lower()
    if 'vortex' in lower:
        return True
    if 'mods_go_here' in lower:
        return True
    if 'unrecognized file' in lower:
        return True
    if 'discord' in lower:
        return True
    if 'could not find' in lower and 'asset' in lower:
        return True
    if 'could not find sound' in lower:
        return True
    if 'unknown item' in lower:
        return True
    if 'shader' in lower or 'opengl' in lower:
        return True
    if 'warning' in lower:
        return True
    return False

def explain_starbound_error(error):
    lower = error.lower()
    if 'music' in lower or 'audio' in lower or 'sound' in lower:
        if 'not found' in lower or 'cannot find' in lower:
            return 'Audio file not found. Check that your music file exists at the specified path.'
        if 'format' in lower or 'unsupported' in lower:
            return 'Unsupported audio format. Make sure your music files are in .ogg format.'
        if 'decode' in lower or 'corrupt' in lower:
            return 'Audio file is corrupted or unreadable. Try re-encoding your music files.'
        return 'Audio file issue. Verify your music files and try re-adding them.'
    if 'json' in lower or 'patch' in lower:
        if 'parse' in lower or 'syntax' in lower:
            return 'JSON format error in patch file. Check for missing commas, quotes, or brackets.'
        if 'not found' in lower:
            return 'Patch cannot find the target location in assets. Verify biome/path names are correct.'
        if 'operation' in lower or 'invalid' in lower:
            return 'Invalid patch operation. Ensure your patch follows Starbound format rules.'
        return 'Issue with patch file. Re-generate your mod patch and try again.'
    if 'asset' in lower or 'file' in lower or 'path' in lower:
        if 'not found' in lower or 'missing' in lower:
            return 'Required file or directory not found. Check your mod folder structure.'
        if 'permission' in lower or 'access denied' in lower:
            return 'Permission denied. Try running Starbound as Administrator or check file permissions.'
        if 'duplicate' in lower:
            return 'Duplicate file or conflict detected. Remove duplicate entries from your patch.'
        return 'File system issue. Verify your mod folder structure is correct.'
    if 'mod' in lower or 'load' in lower:
        if 'dependency' in lower:
            return 'Mod dependency issue. This mod requires another mod to be loaded first.'
        if 'conflict' in lower:
            return 'Mod conflict detected. Disable conflicting mods and try again.'
        if 'version' in lower or 'compatibility' in lower:
            return 'Mod compatibility issue. Update your mods to compatible versions.'
        return 'Mod loading issue. Check mod compatibility and dependencies.'
    if 'memory' in lower or 'out of' in lower or 'too many' in lower:
        return 'Out of memory. Close other programs and restart Starbound.'
    if 'crash' in lower or 'exception' in lower or 'fatal' in lower:
        return 'Game crashed. Check mod compatibility and disable conflicting mods.'
    if 'server' in lower or 'connect' in lower or 'network' in lower:
        return 'Server connection issue. Check your internet connection.'
    return 'Error detected. Check logs for more details or verify mod installation.'

def get_benign_error_explanation(error):
    lower = error.lower()
    if 'vortex.deployment.json' in lower:
        return 'Vortex mod manager message that enables Vortex to manage mods in your Starbound folder. Safe to ignore.'
    if 'mods_go_here' in lower:
        return 'Starbound folder reminder. It is how Starbound organizes it\'s mod folder. Safe to ignore.'
    if 'unrecognized file' in lower:
        return 'Unrecognized file warning. Usually harmless, but may indicate a file with metadata issues such as incorrect file names or missing attributes.'
    if 'discord' in lower:
        return 'Discord integration warning. Safe to ignore.'
    if 'could not find' in lower and 'asset' in lower:
        return 'Missing asset warning. Usually harmless unless mod is missing content.'
    if 'could not find sound' in lower:
        return 'Missing sound warning. Usually harmless unless it affects gameplay or mod functionality.'
    if 'unknown item' in lower:
        return 'Unknown item warning. Usually harmless unless it affects gameplay or mod functionality.'
    if 'shader' in lower or 'opengl' in lower:
        return 'Graphics driver or shader warning. Safe to ignore.'
    if 'warning' in lower:
        return 'General warning. Usually not critical.'
    return 'Benign Starbound log message. Safe to ignore.'

def auto_detect_log():
    """
    Attempts to find the most recent starbound.log file in common Starbound locations.
    Returns a dict with 'success', 'logPath', and 'message'.
    """
    import os
    import glob
    # Add the actual Starbound storage path first
    possible_dirs = [
        r'c:/Steam/steamapps/common/Starbound/storage',
        os.path.expandvars(r'%ProgramFiles(x86)%/Steam/steamapps/common/Starbound/storage'),
        os.path.expandvars(r'%ProgramFiles%/Steam/steamapps/common/Starbound/storage'),
        os.path.expanduser(r'~/AppData/Local/Steam/steamapps/common/Starbound/storage'),
        os.path.expanduser(r'~/Steam/steamapps/common/Starbound/storage'),
        os.path.expanduser(r'~/Documents/Starbound/storage'),
        os.path.expanduser(r'~/Starbound/storage'),
    ]
    for d in possible_dirs:
        d = os.path.normpath(d)
        if os.path.isdir(d):
            log_path = os.path.join(d, 'starbound.log')
            if os.path.isfile(log_path):
                return {'success': True, 'logPath': log_path, 'message': 'Found starbound.log'}
            # Try to find the most recent log if multiple
            logs = glob.glob(os.path.join(d, 'starbound.log*'))
            if logs:
                logs.sort(key=os.path.getmtime, reverse=True)
                return {'success': True, 'logPath': logs[0], 'message': 'Found starbound.log'}
    return {'success': False, 'message': 'starbound.log not found in common locations.'}

# For user file selection, just use QFileDialog in the GUI
