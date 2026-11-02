import json
import os
import sys
from datetime import datetime
from pathlib import Path

home = Path.home()
logdir = home / 'local-agent'
pairs = [
    ('Documents/Codex/2026-10-07/aijaa-reconcile', 'Code/AIJAA/aijaa-reconcile'),
    ('Downloads/AIJAA/aijaa', 'Code/AIJAA/aijaa'),
    ('Downloads/IncidentLens-main', 'Code/IncidentLens'),
    ('Downloads/AsyncML-Platform-main', 'Code/AsyncML-Platform'),
    ('Desktop/project-training', 'Code/project-training'),
    ('Documents/Codex/2026-10-07/https-github-com-galaimoshko-job-search', 'Code/job-search'),
]

def exists(path):
    return os.path.lexists(path)

def save(log, rows):
    temp = log.with_suffix('.tmp')
    with temp.open('w') as file:
        json.dump(rows, file, indent=2)
        file.flush()
        os.fsync(file.fileno())
    temp.chmod(0o600)
    os.replace(temp, log)

if len(sys.argv) == 2 and sys.argv[1] == 'move':
    rows = [
        {'from': str(home / src), 'to': str(home / dst), 'moved': False}
        for src, dst in pairs
    ]

    for row in rows:
        src, dst = Path(row['from']), Path(row['to'])
        if not src.is_dir() or src.is_symlink() or exists(dst):
            sys.exit(f'Stopped before moving: {src} -> {dst}')
        if (src / '.git').is_file():
            sys.exit(f'Linked Git checkout needs separate handling: {src}')
        parent = dst.parent
        while not parent.exists():
            parent = parent.parent
        if src.stat().st_dev != parent.stat().st_dev:
            sys.exit(f'Different volumes; stopped: {src}')

    logdir.mkdir(mode=0o700, exist_ok=True)
    log = logdir / (
        'moves-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.json'
    )
    if exists(log):
        sys.exit('Log file already exists; stopped')

    save(log, rows)
    print(f'Log: {log}', flush=True)

    for row in rows:
        src, dst = Path(row['from']), Path(row['to'])
        if not src.is_dir() or exists(dst):
            sys.exit(f'Stopped; check log for completed moves: {log}')
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        row['moved'] = True
        save(log, rows)
        print(f'Moved: {src} -> {dst}', flush=True)

    print(f'Done. Undo with: python3 organize_projects.py undo {log}')

elif len(sys.argv) == 3 and sys.argv[1] == 'undo':
    log = Path(sys.argv[2]).expanduser().resolve()
    if log.parent != logdir.resolve() or not log.name.startswith('moves-'):
        sys.exit('Log must be a moves-*.json file in ~/local-agent')

    rows = json.loads(log.read_text())
    pending = [
        row for row in reversed(rows)
        if not exists(row['from']) and exists(row['to'])
    ]

    for row in rows:
        if exists(row['from']) and not exists(row['to']):
            row['moved'] = False

    for row in pending:
        if not Path(row['to']).is_dir() or exists(row['from']):
            sys.exit(f'Undo stopped before moving anything: {row}')

    for row in pending:
        src, dst = Path(row['from']), Path(row['to'])
        src.parent.mkdir(parents=True, exist_ok=True)
        dst.rename(src)
        row['moved'] = False
        save(log, rows)
        print(f'Restored: {dst} -> {src}', flush=True)

    print('Undo complete')

else:
    sys.exit(
        'Usage: python3 organize_projects.py move | '
        'undo ~/local-agent/moves-....json'
    )
