"""Cut a release: bump VERSION, commit, tag vX.Y.Z and push. GitHub Actions then tests, builds and publishes it,
and every server with automatic updates installs it at night.

    python scripts/release.py patch      # 1.0.0 -> 1.0.1
    python scripts/release.py minor      # 1.0.1 -> 1.1.0
    python scripts/release.py major      # 1.1.0 -> 2.0.0
    python scripts/release.py 1.4.2      # exact version

Run it on main with a clean working tree.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / 'VERSION'


def git(*args, capture=False):
    result = subprocess.run(['git', *args], cwd=ROOT, check=True, text=True,
                            capture_output=capture)
    return result.stdout.strip() if capture else ''


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    current = VERSION_FILE.read_text(encoding='utf-8').strip()
    major, minor, patch = (int(x) for x in current.split('.'))
    arg = sys.argv[1]
    if arg == 'patch':
        new = f'{major}.{minor}.{patch + 1}'
    elif arg == 'minor':
        new = f'{major}.{minor + 1}.0'
    elif arg == 'major':
        new = f'{major + 1}.0.0'
    elif re.fullmatch(r'\d+\.\d+\.\d+', arg):
        new = arg
    else:
        sys.exit(f'Unknown bump "{arg}". Use patch, minor, major or X.Y.Z.')

    if git('status', '--porcelain', capture=True):
        sys.exit('The working tree has uncommitted changes. Commit or stash them first.')
    branch = git('rev-parse', '--abbrev-ref', 'HEAD', capture=True)
    if branch != 'main':
        sys.exit(f'Releases are cut from main (you are on {branch}).')

    VERSION_FILE.write_text(new + '\n', encoding='utf-8')
    git('add', 'VERSION')
    git('commit', '-m', f'Release v{new}')
    git('tag', '-a', f'v{new}', '-m', f'WorkTrack Pro v{new}')
    git('push', '--follow-tags', 'origin', 'main')
    print(f'v{new} pushed. Watch the Release workflow on GitHub; servers pick it up at the next nightly check.')


if __name__ == '__main__':
    main()
