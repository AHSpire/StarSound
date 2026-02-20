# config_health_detailed.py
# Detailed config health check for Starbound Music Mod Generator (Python)
import os
import json

def validate_json_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, data, None
    except Exception as e:
        return False, None, str(e)

def check_starbound_config(config_path):
    issues = []
    warnings = []
    info = []
    # Check config directory
    if not os.path.isdir(config_path):
        issues.append(f"Starbound config directory not found: {config_path}")
        return build_report(issues, warnings, info, config_path)
    info.append(f"✓ Starbound config directory exists: {config_path}")
    # Check for critical config files
    critical_files = ['starbound.config']
    for file in critical_files:
        file_path = os.path.join(config_path, file)
        if not os.path.isfile(file_path):
            warnings.append(f"{file} not found (may be auto-generated on first launch)")
        else:
            valid, _, err = validate_json_file(file_path)
            if not valid:
                issues.append(f"{file} has invalid JSON: {err}")
            else:
                info.append(f"✓ {file} JSON is valid")
    # Check mods directory
    mods_path = os.path.join(config_path, 'mods')
    if os.path.isdir(mods_path):
        mod_dirs = [d for d in os.listdir(mods_path) if os.path.isdir(os.path.join(mods_path, d)) and not d.startswith('.')]
        if mod_dirs:
            info.append(f"✓ StarSound export directory exists with {len(mod_dirs)} generated mod(s)")
            building_mods = [d for d in mod_dirs if d.endswith('_BUILDING')]
            if building_mods:
                warnings.append(f"Found {len(building_mods)} incomplete mod(s) being built: {', '.join(building_mods)}")
        else:
            info.append("✓ StarSound export directory exists but is empty")
    else:
        info.append("StarSound export directory not found (will be created automatically when you generate your first mod)")
    # Check universe directory
    universe_path = os.path.join(config_path, 'universe')
    if os.path.isdir(universe_path):
        info.append("✓ Universe directory exists")
    else:
        warnings.append("Universe directory not found (will be created on first launch)")
    # Check player directory
    player_path = os.path.join(config_path, 'player')
    if os.path.isdir(player_path):
        player_files = [f for f in os.listdir(player_path) if f.endswith('.player') and not f.startswith('.')]
        if player_files:
            info.append(f"✓ Player directory exists with {len(player_files)} character(s)")
        else:
            all_files = [f for f in os.listdir(player_path) if not f.startswith('.')]
            info.append(f"✓ Player directory exists ({len(all_files)} file(s) total, no characters created yet)")
    else:
        warnings.append("Player directory not found (will be created on first launch)")
    # Advanced checks: mod metadata
    corrupted_count = 0
    checked_count = 0
    if os.path.isdir(mods_path):
        for d in os.listdir(mods_path):
            mod_dir = os.path.join(mods_path, d)
            if os.path.isdir(mod_dir) and not d.startswith('.'):
                metadata_path = os.path.join(mod_dir, '_metadata')
                if os.path.isfile(metadata_path):
                    valid, _, _ = validate_json_file(metadata_path)
                    checked_count += 1
                    if not valid:
                        corrupted_count += 1
                        warnings.append(f'Mod "{d}" has corrupted _metadata file')
        if checked_count > 0:
            if corrupted_count == 0:
                info.append(f"✓ Checked {checked_count} mod(s) - all metadata files valid")
            else:
                warnings.append(f"Found {corrupted_count} mod(s) with invalid metadata out of {checked_count} checked")
    return build_report(issues, warnings, info, config_path)

def build_report(issues, warnings, info, config_path):
    has_issues = len(issues) > 0
    has_warnings = len(warnings) > 0
    is_healthy = not has_issues and not has_warnings
    health_status = 'healthy'
    icon = '✓'
    color = 'success'
    if has_issues:
        health_status = 'critical'
        icon = '✗'
        color = 'error'
    elif has_warnings:
        health_status = 'warning'
        icon = '⚠️'
        color = 'warning'
    return {
        'success': not has_issues,
        'healthStatus': health_status,
        'icon': icon,
        'color': color,
        'isHealthy': is_healthy,
        'hasWarnings': has_warnings,
        'hasIssues': has_issues,
        'issues': issues,
        'warnings': warnings,
        'info': info,
        'summary': build_summary(issues, warnings, info)
    }

def build_summary(issues, warnings, info):
    if not issues and not warnings:
        summary = '✓ Starbound configuration is healthy and ready to use.\n'
        summary += '\n'.join([f'  ✓ {line.lstrip("✓ ")}' for line in info])
        return summary
    summary = ''
    if issues:
        summary += f'Found {len(issues)} critical issue(s) that need attention:\n'
        summary += '\n'.join([f'  ✗ {issue}' for issue in issues])
    if warnings:
        if summary:
            summary += '\n\n'
        summary += f'Found {len(warnings)} warning(s):\n'
        summary += '\n'.join([f'  ⚠️ {warning}' for warning in warnings])
    if info:
        summary += ('\n\n' if summary else '')
        summary += 'Info:\n'
        summary += '\n'.join([f'  ✓ {line.lstrip("✓ ")}' for line in info])
    return summary
