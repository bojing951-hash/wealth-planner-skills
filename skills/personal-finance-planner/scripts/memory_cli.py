#!/usr/bin/env python3
"""Explicit-consent adapter for private local memory; invoked by a host Agent.

Examples:
  python memory_cli.py --profile user_001 status
  python memory_cli.py --profile user_001 init --consent-write
  python memory_cli.py --profile user_001 preview --expected-revision 0 --consent-read --stdin
  python memory_cli.py --profile user_001 update --expected-revision 0 --consent-write --stdin
  python memory_cli.py --profile user_001 read --consent-read --view summary
  python memory_cli.py --profile user_001 purge --category facts --expected-revision 1 --consent-write
  python memory_cli.py --profile user_001 delete --consent-write --confirm-profile user_001

Do not point data paths at a Git repository or pass sensitive JSON as command
arguments. By default no memory is created. Host must collect user consent.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'lib'))
from wealth_core.local_memory import (LocalMemory, MemoryErrorBase, ConsentRequired)


def cli(argv=None):
    p=argparse.ArgumentParser(description='Optional encrypted local memory for Personal Wealth Planner Skill')
    p.add_argument('--profile',required=True,help='Pseudonymous user profile ID, e.g. user_001')
    p.add_argument('--data-dir',type=Path,help='Dedicated private local vault root (not in Git)')
    p.add_argument('--keys-dir',type=Path,help='Dedicated private separate config key root')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('status')
    init=sub.add_parser('init');init.add_argument('--consent-write',action='store_true')
    read=sub.add_parser('read');read.add_argument('--consent-read',action='store_true')
    read.add_argument('--view',choices=('summary','full'),default='summary')
    read.add_argument('--as-of',help='Date for expiry calculation YYYY-MM-DD')
    for cmd in ('preview','update'):
        cp=sub.add_parser(cmd)
        cp.add_argument('--expected-revision',type=int,required=True)
        cp.add_argument('--stdin',action='store_true',required=True,help='Read changes JSON via stdin to avoid shell arguments')
        cp.add_argument('--consent-read',action='store_true')
        cp.add_argument('--consent-write',action='store_true')
        cp.add_argument('--approved-preview-sha256',help='For update: digest displayed by an approved preview; not a security token')
    compare=sub.add_parser('compare');compare.add_argument('--old-revision',type=int,required=True)
    compare.add_argument('--new-revision',type=int,required=True);compare.add_argument('--consent-read',action='store_true')
    purge=sub.add_parser('purge');purge.add_argument('--category',required=True,choices=('facts','plans','decisions','all_history'))
    purge.add_argument('--expected-revision',type=int,required=True)
    purge.add_argument('--consent-write',action='store_true')
    forget=sub.add_parser('forget');forget.add_argument('--field',required=True)
    forget.add_argument('--expected-revision',type=int,required=True);forget.add_argument('--consent-write',action='store_true')
    delete=sub.add_parser('delete');delete.add_argument('--consent-write',action='store_true');delete.add_argument('--confirm-profile')
    export=sub.add_parser('export');export.add_argument('--target',type=Path,required=True)
    export.add_argument('--consent-read',action='store_true');export.add_argument('--acknowledge-plaintext',action='store_true')
    args=p.parse_args(argv)
    try:
        store=LocalMemory(args.profile,args.data_dir,args.keys_dir)
        if args.command=='status': result=store.status()
        elif args.command=='init': result=store.init(consent_write=args.consent_write)
        elif args.command=='read': result=store.read(consent_read=args.consent_read,view=args.view,as_of=args.as_of)
        elif args.command in ('preview','update'):
            # Restrict input to modest JSON only; raw bank statements are not suitable for memory.
            raw=sys.stdin.read(128*1024+1)
            if len(raw)>128*1024: raise ValueError('Memory input exceeds 128 KiB')
            changes=json.loads(raw)
            if args.command=='preview':
                result=store.preview(changes,args.expected_revision,consent_read=args.consent_read)
            else:
                if not args.approved_preview_sha256:
                    raise ConsentRequired('Update requires --approved-preview-sha256 from prior preview and user approval')
                result=store.update(changes,args.expected_revision,consent_write=args.consent_write,
                                    approved_preview_sha256=args.approved_preview_sha256)
        elif args.command=='compare':
            result=store.compare(args.old_revision,args.new_revision,consent_read=args.consent_read)
        elif args.command=='purge':
            result=store.purge(args.category,args.expected_revision,consent_write=args.consent_write)
        elif args.command=='forget':
            result=store.forget_field(args.field,args.expected_revision,consent_write=args.consent_write)
        elif args.command=='delete':
            result=store.delete(consent_write=args.consent_write,confirm_profile_id=args.confirm_profile)
        elif args.command=='export':
            result=store.export_plaintext(args.target,consent_read=args.consent_read,
                                          acknowledge_plaintext=args.acknowledge_plaintext)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (MemoryErrorBase,ValueError,TypeError,json.JSONDecodeError) as exc:
        # Do not include full payload in error output.
        print(json.dumps({'ok':False,'error_type':type(exc).__name__,'message':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(cli())
