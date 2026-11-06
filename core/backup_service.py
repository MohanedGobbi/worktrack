"""
WorkTrack Pro - System Database & Version Archive Service
Provides atomic live online backups, safe restoration,
download, delete, upload, and metadata tracking for the system SQLite database.
"""

import os
import sqlite3
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.db import connections
from django.core.cache import cache

BACKUPS_DIR = settings.BASE_DIR / 'backups'
MANIFEST_FILE = BACKUPS_DIR / 'backups_manifest.json'
DB_PATH = Path(settings.DATABASES['default']['NAME'])
EMERGENCY_BACKUP_PATH = BACKUPS_DIR / '.emergency_pre_restore.sqlite3'

def ensure_backup_dir():
    """Ensure the backups directory and manifest exist."""
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    if not MANIFEST_FILE.exists():
        with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)

def _read_manifest():
    ensure_backup_dir()
    try:
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []

def _write_manifest(backups):
    ensure_backup_dir()
    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(backups, f, indent=2, ensure_ascii=False)

def _format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def get_database_stats(db_file=None):
    """Inspect a database file and return table and record counts."""
    target_path = Path(db_file) if db_file else DB_PATH
    if not target_path.exists():
        return {
            'exists': False,
            'size': 0,
            'size_human': '0 B',
            'tables_count': 0,
            'integrity': 'Missing',
            'user_count': 0,
            'task_count': 0,
            'module_count': 0,
            'submission_count': 0,
        }

    size_bytes = target_path.stat().st_size
    stats = {
        'exists': True,
        'size': size_bytes,
        'size_human': _format_size(size_bytes),
        'tables_count': 0,
        'integrity': 'OK',
        'user_count': 0,
        'task_count': 0,
        'module_count': 0,
        'submission_count': 0,
    }

    try:
        conn = sqlite3.connect(f"file:{target_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        # Integrity Check
        cursor.execute("PRAGMA integrity_check;")
        res = cursor.fetchone()
        stats['integrity'] = 'OK' if (res and res[0] == 'ok') else 'Warning'

        # Tables count
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        stats['tables_count'] = cursor.fetchone()[0]

        # Key entity counts if tables exist
        def safe_count(table):
            try:
                cursor.execute(f"SELECT count(*) FROM {table};")
                return cursor.fetchone()[0]
            except Exception:
                return 0

        stats['user_count'] = safe_count('users_customuser')
        stats['task_count'] = safe_count('tasks_task')
        stats['module_count'] = safe_count('work_modules_workmodule')
        stats['submission_count'] = safe_count('submissions_submission')

        conn.close()
    except Exception as e:
        stats['integrity'] = f"Error: {e}"

    return stats

def list_backups():
    """
    List all available database backup versions with full metadata.
    Guarantees strict 1-to-1 mapping with physical files and no duplicates.
    """
    ensure_backup_dir()
    manifest = _read_manifest()

    # Deduplicate existing manifest by filename
    seen_files = set()
    cleaned_manifest = []
    for b in manifest:
        if not isinstance(b, dict):
            continue
        fname = b.get('filename')
        # Skip auto_safety entries if any exist
        if b.get('is_safety') or (fname and fname.startswith('auto_safety_')):
            continue
        if fname and fname not in seen_files:
            seen_files.add(fname)
            cleaned_manifest.append(b)

    manifest_by_filename = {b.get('filename'): b for b in cleaned_manifest if b.get('filename')}
    manifest_by_id = {b.get('id'): b for b in cleaned_manifest if b.get('id')}

    changed = len(manifest) != len(cleaned_manifest)

    # Check for any loose .sqlite3 files in backups/ not recorded yet
    for p in BACKUPS_DIR.glob('*.sqlite3'):
        # Ignore hidden files, temporary files, and obsolete auto-safety files
        if p.name.startswith('.') or p.name.startswith('auto_safety_'):
            continue

        if p.name not in manifest_by_filename and p.stem not in manifest_by_id:
            size_b = p.stat().st_size
            mtime = datetime.fromtimestamp(p.stat().st_mtime)
            stats = get_database_stats(p)
            entry = {
                'id': p.stem,
                'name': p.stem.replace('_', ' ').title(),
                'description': 'Database backup archive',
                'filename': p.name,
                'size_bytes': size_b,
                'size_human': _format_size(size_b),
                'created_at': mtime.isoformat(),
                'created_by': 'System',
                'is_safety': False,
                'tables_count': stats['tables_count'],
                'user_count': stats['user_count'],
                'task_count': stats['task_count'],
                'module_count': stats['module_count'],
                'submission_count': stats['submission_count'],
                'integrity': stats['integrity'],
            }
            manifest_by_filename[p.name] = entry
            changed = True

    # Filter out entries where file was deleted on disk
    valid_list = []
    for fname, entry in manifest_by_filename.items():
        fpath = BACKUPS_DIR / fname
        if fpath.exists():
            actual_size = fpath.stat().st_size
            entry['size_bytes'] = actual_size
            entry['size_human'] = _format_size(actual_size)
            # Ensure id matches stem
            entry['id'] = entry.get('id') or fpath.stem
            valid_list.append(entry)
        else:
            changed = True

    # Sort newest first
    valid_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    if changed:
        _write_manifest(valid_list)

    return valid_list

def create_backup(name=None, description='', user=None):
    """
    Perform an atomic online backup of the SQLite database.
    Does not lock or interrupt live web visitors.
    Creates exactly ONE backup record.
    """
    ensure_backup_dir()
    now = datetime.now()
    timestamp_str = now.strftime('%Y%m%d_%H%M%S')
    
    clean_name = name.strip() if name and name.strip() else f"WorkTrack Backup {now.strftime('%b %d, %Y - %H:%M')}"
    backup_id = f"backup_{timestamp_str}"
    filename = f"{backup_id}.sqlite3"
    dest_path = BACKUPS_DIR / filename

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Source database file not found at {DB_PATH}")

    # Use SQLite's online backup API for an atomic, clean copy
    src_conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    dst_conn = sqlite3.connect(dest_path)
    src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()

    # Gather stats of the created backup
    stats = get_database_stats(dest_path)

    creator_name = 'Administrator'
    if user:
        creator_name = getattr(user, 'username', str(user))

    backup_entry = {
        'id': backup_id,
        'name': clean_name,
        'description': description.strip(),
        'filename': filename,
        'size_bytes': stats['size'],
        'size_human': stats['size_human'],
        'created_at': now.isoformat(),
        'created_by': creator_name,
        'is_safety': False,
        'tables_count': stats['tables_count'],
        'user_count': stats['user_count'],
        'task_count': stats['task_count'],
        'module_count': stats['module_count'],
        'submission_count': stats['submission_count'],
        'integrity': stats['integrity'],
    }

    # Clean existing manifest, remove any entry with same filename, and insert
    current_backups = list_backups()
    filtered = [b for b in current_backups if b.get('filename') != filename and b.get('id') != backup_id]
    filtered.insert(0, backup_entry)
    _write_manifest(filtered)

    return backup_entry

def restore_backup(backup_id, user=None):
    """
    Safely restore the SQLite database from a selected backup version.
    Restores the selected database snapshot directly without creating
    unwanted extra backups in the user's version archive list.
    """
    ensure_backup_dir()
    manifest = list_backups()
    
    # Locate target backup by id or filename
    target = next((b for b in manifest if b.get('id') == backup_id or b.get('filename') == backup_id or Path(b.get('filename', '')).stem == backup_id), None)
    if not target:
        raise ValueError(f"Backup with ID '{backup_id}' not found.")

    src_file = BACKUPS_DIR / target.get('filename', '')
    if not src_file.exists():
        raise FileNotFoundError(f"Backup file '{src_file.name}' not found on disk.")

    # 1. Take a hidden emergency recovery copy of current live database in case copy fails
    if DB_PATH.exists():
        try:
            s_src = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            s_dst = sqlite3.connect(EMERGENCY_BACKUP_PATH)
            s_src.backup(s_dst)
            s_dst.close()
            s_src.close()
        except Exception as e:
            print(f"[Backup] Emergency snapshot note: {e}")

    # 2. Close active Django database connections
    connections.close_all()

    # 3. Restore the database file
    shutil.copy2(src_file, DB_PATH)

    # 4. Verify integrity of newly restored database
    stats = get_database_stats(DB_PATH)
    if stats['integrity'] != 'OK':
        # Roll back to emergency copy if corrupted
        if EMERGENCY_BACKUP_PATH.exists():
            shutil.copy2(EMERGENCY_BACKUP_PATH, DB_PATH)
        raise RuntimeError(f"Restored database integrity warning: {stats['integrity']}. Reverted to previous state.")

    # 5. Clear cache to reflect new database state
    try:
        cache.clear()
    except Exception:
        pass

    return target

def delete_backup(backup_id):
    """Delete a backup archive and remove from manifest."""
    ensure_backup_dir()
    manifest = _read_manifest()
    target = next((b for b in manifest if b.get('id') == backup_id or b.get('filename') == backup_id or Path(b.get('filename', '')).stem == backup_id), None)
    if not target:
        return False

    fname = target.get('filename')
    if fname:
        fpath = BACKUPS_DIR / fname
        if fpath.exists():
            try:
                os.remove(fpath)
            except Exception as e:
                print(f"[Backup] Failed removing file {fpath}: {e}")

    updated = [b for b in manifest if b.get('id') != backup_id and b.get('filename') != fname]
    _write_manifest(updated)
    return True

def save_uploaded_backup(uploaded_file, name=None, description='', user=None):
    """Save and register an uploaded SQLite database backup file."""
    ensure_backup_dir()
    now = datetime.now()
    timestamp_str = now.strftime('%Y%m%d_%H%M%S')
    backup_id = f"imported_{timestamp_str}"
    filename = f"{backup_id}.sqlite3"
    dest_path = BACKUPS_DIR / filename

    # Verify SQLite header
    header = uploaded_file.read(16)
    if not header.startswith(b'SQLite format 3\x00'):
        raise ValueError("Invalid file format. Only valid SQLite database (.sqlite3 / .db) files are accepted.")
    
    uploaded_file.seek(0)
    with open(dest_path, 'wb') as dst:
        for chunk in uploaded_file.chunks():
            dst.write(chunk)

    stats = get_database_stats(dest_path)
    clean_name = name.strip() if name and name.strip() else f"Imported Backup ({uploaded_file.name})"

    creator_name = getattr(user, 'username', 'Uploaded') if user else 'Uploaded'

    backup_entry = {
        'id': backup_id,
        'name': clean_name,
        'description': description.strip() or f"Imported from {uploaded_file.name}",
        'filename': filename,
        'size_bytes': stats['size'],
        'size_human': stats['size_human'],
        'created_at': now.isoformat(),
        'created_by': creator_name,
        'is_safety': False,
        'tables_count': stats['tables_count'],
        'user_count': stats['user_count'],
        'task_count': stats['task_count'],
        'module_count': stats['module_count'],
        'submission_count': stats['submission_count'],
        'integrity': stats['integrity'],
    }

    current_backups = list_backups()
    filtered = [b for b in current_backups if b.get('filename') != filename and b.get('id') != backup_id]
    filtered.insert(0, backup_entry)
    _write_manifest(filtered)

    return backup_entry
