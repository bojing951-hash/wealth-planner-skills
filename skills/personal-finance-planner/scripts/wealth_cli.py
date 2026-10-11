#!/usr/bin/env python3
"""Portable stdlib CLI for the v0.4 schema, host task planning and reporting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from wealth_core.capabilities import normalize_manifest, CapabilityError
from wealth_core.orchestration import build_plan, digest
from wealth_core.profile import validate_profile, ProfileError
from wealth_core.report import render_markdown


def load_json(filepath: str):
    return json.loads(Path(filepath).read_text(encoding='utf-8'))


def main(argv=None):
    ap = argparse.ArgumentParser(description='v0.4 offline profile validation + host tool routing (NO tax/legal conclusions)')
    sub = ap.add_subparsers(dest='command', required=True)
    p_validate = sub.add_parser('validate', help='Validate strict v0.4 personal finance input')
    p_validate.add_argument('--input', required=True)
    p_caps = sub.add_parser('capabilities', help='Inspect declared host capability map, without executing tools')
    p_caps.add_argument('--manifest')
    p_plan = sub.add_parser('plan', help='Build reproducible plan and conditional finance snapshot')
    p_plan.add_argument('--input', required=True)
    p_plan.add_argument('--capabilities', help='Host-provided declared capabilities; omission means OFFLINE')
    p_plan.add_argument('--receipts', help='Optional provenance metadata from ALREADY executed, authorized host tools')
    p_plan.add_argument('--format', choices=('json','md'), default='md')
    p_plan.add_argument('--out', help='Write to explicitly requested local path (never automatic remote upload)')
    a = ap.parse_args(argv)
    try:
        if a.command == 'validate':
            obj = load_json(a.input)
            validate_profile(obj)
            out = {'status':'VALID','schema_version':obj['schema_version'],
                   'profile_id':obj['profile_id'],'input_sha256':digest(obj)}
            rendered = json.dumps(out, ensure_ascii=False, indent=2) + '\n'
        elif a.command == 'capabilities':
            manifest = normalize_manifest(load_json(a.manifest) if a.manifest else None)
            rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
        else:
            profile = load_json(a.input)
            manifest = load_json(a.capabilities) if a.capabilities else None
            receipts = load_json(a.receipts) if a.receipts else None
            result = build_plan(profile, manifest, receipts)
            rendered = (render_markdown(result) if a.format == 'md'
                        else json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        if getattr(a, 'out', None):
            target = Path(a.out)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered, encoding='utf-8')
        else:
            print(rendered, end='')
        return 0
    except (ValueError, CapabilityError, ProfileError, json.JSONDecodeError, FileNotFoundError, PermissionError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
