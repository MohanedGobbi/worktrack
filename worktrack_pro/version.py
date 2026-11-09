"""The installed WorkTrack Pro version.

A release package carries version.json (version, commit, build date), written by deploy/build_package.sh.
A git checkout has only the VERSION file.
"""
import json
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def version_info():
    try:
        data = json.loads((BASE_DIR / 'version.json').read_text(encoding='utf-8'))
        if isinstance(data, dict) and data.get('version'):
            return {'version': str(data['version']), 'commit': str(data.get('commit', '')), 'build_date': str(data.get('build_date', ''))}
    except (OSError, ValueError):
        pass
    try:
        return {'version': (BASE_DIR / 'VERSION').read_text(encoding='utf-8').strip(), 'commit': '', 'build_date': ''}
    except OSError:
        return {'version': '0.0.0', 'commit': '', 'build_date': ''}


def get_version():
    return version_info()['version']
