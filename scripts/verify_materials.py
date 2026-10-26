"""Verify the archived materials using Python 3's standard library."""

from pathlib import Path
import hashlib
import json
import sys


def sha256(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def verify_archive(base):
    checksum_file = base / 'SHA256SUMS.txt'
    problems = []
    expected_files = {checksum_file}
    checked = 0

    for line in checksum_file.read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        path = (base / relative).resolve()
        if base not in path.parents:
            problems.append('Invalid path: ' + relative)
            continue
        expected_files.add(path)
        if not path.is_file():
            problems.append('Missing: ' + relative)
        elif sha256(path) != expected:
            problems.append('SHA-256 mismatch: ' + relative)
        else:
            checked += 1

    manifest = json.loads((base / '文件清单.json').read_text(encoding='utf-8'))
    for record in manifest['records']:
        path = (base / record['path']).resolve()
        if base not in path.parents or not path.is_file():
            problems.append('Missing or invalid manifest path: ' + record['path'])
        elif sha256(path) != record['sha256'] or path.stat().st_size != record['size_bytes']:
            problems.append('Manifest mismatch: ' + record['path'])

    actual = {p.resolve() for p in base.rglob('*') if p.is_file() and p.name != '.DS_Store'}
    for path in sorted(actual - expected_files):
        problems.append('Unlisted file: ' + str(path.relative_to(base)))

    if problems:
        print('\n'.join(problems), file=sys.stderr)
        return 1
    print('Verified {}: {} checksum entries, {} manifest records, {} archived files.'.format(
        base.name, checked, len(manifest['records']), len(actual)))
    return 0


def main():
    root = Path(__file__).resolve().parents[1]
    names = ('materials', 'policies', 'updates/2026-10-26-corrected-assets')
    results = [verify_archive((root / name).resolve()) for name in names]
    return 1 if any(results) else 0


if __name__ == '__main__':
    sys.exit(main())
