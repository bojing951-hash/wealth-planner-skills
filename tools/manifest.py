#!/usr/bin/env python3
"""Build/verify SHA256 manifest of project files. Does not publish or transfer anything.

Use on the ACTUAL GitHub checkout. Refresh after content changes (not against stale ZIP
README files). Git ignored private/financial data are excluded; scan the resulting
manifest for unintended paths before commit.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'MANIFEST.sha256'


def find_files() -> list[Path]:
    try:
        out=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT,stderr=subprocess.DEVNULL,timeout=5)
        files=[ROOT/name.decode('utf-8') for name in out.split(b'\0') if name]
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        files=[p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts]
    files=[p for p in files if p.is_file() and p.resolve()!=MANIFEST.resolve() and p.relative_to(ROOT).parts[0] not in ('private','user-data','userdata','reports','results') and not any(z in p.parts for z in ('__pycache__','.git','.venv','.tox','.pytest_cache'))]
    return sorted(files,key=lambda p:p.relative_to(ROOT).as_posix())


def render() -> str:
    return ''.join(f'{sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n' for p in find_files())


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--write',action='store_true')
    g.add_argument('--verify',action='store_true')
    args=p.parse_args()
    actual=render()
    if args.write:
        MANIFEST.write_text(actual,encoding='utf-8')
        print(f'Generated SHA256 manifest for {actual.count(chr(10))} files. Verify and stage it.')
        return 0
    if not MANIFEST.is_file():
        print('FAIL: MANIFEST.sha256 missing')
        return 1
    old=MANIFEST.read_text(encoding='utf-8')
    if old==actual:
        print(f'PASS: SHA256 manifest matches {actual.count(chr(10))} current files')
        return 0
    before={l.split('  ',1)[1]:l.split('  ',1)[0] for l in old.splitlines() if '  ' in l}
    after={l.split('  ',1)[1]:l.split('  ',1)[0] for l in actual.splitlines() if '  ' in l}
    print('FAIL: stale manifest; run python tools/manifest.py --write on the CURRENT checkout, inspect diff, commit MANIFEST.sha256')
    for k in sorted(before.keys()|after.keys()):
        if before.get(k)!=after.get(k):print('  changed/missing/added:',k)
    return 1


if __name__=='__main__':
    sys.exit(main())
