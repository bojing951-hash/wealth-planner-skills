#!/usr/bin/env python3
"""Portable Wealth Planner v5 CLI. No API calls, broker operations or backdoor IO."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
LIB=ROOT / 'lib'
if str(LIB) not in sys.path:sys.path.insert(0,str(LIB))

from wealth_core.integrated import build_integrated,normalize_profile_v5
from wealth_core.report_v5 import render_md
from wealth_core.dynamic import compare
from wealth_core.evidence import evaluate
from wealth_core.tax_scenarios import calculate_hypothetical_tax
from wealth_core.portfolio import portfolio_diagnostics
from wealth_core.simulation import simulate
from wealth_core.orchestration import digest


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def cli(argv=None):
    app=argparse.ArgumentParser(description='Wealth Planner v5 developer preview: host-delegated, source-aware, reproducible; NOT a tax/financial advisor')
    sub=app.add_subparsers(dest='command',required=True)
    val=sub.add_parser('validate',help='Validate profile schema 0.4 or 5.0 compatibility')
    val.add_argument('--input',required=True)
    plan=sub.add_parser('run',help='Integrated offline research planner / optional user-supplied scenarios')
    plan.add_argument('--input',required=True)
    for arg,helpstr in [
        ('--capabilities','Host-declared capability map, NOT proof of tools or authorization'),
        ('--receipts','Actual host-submitted provenance metadata; host must review substance'),
        ('--assumptions','Explicit UNCALIBRATED model assumptions, not forecasts'),
        ('--portfolio','User-defined portfolio risk study'),
        ('--tax-scenario','Hypothetical user-defined tax math only'),
        ('--previous','Previous plan JSON for on-demand state comparison'),
        ('--law-packets','Host-supplied official-law metadata, not a binding interpretation'),
        ('--macro-bundle','Dated observations, currency-matched and not a forecast'),
    ]:
        plan.add_argument(arg,help=helpstr)
    plan.add_argument('--format',choices=['md','json'],default='md')
    research=sub.add_parser('host-queue',help='Emit declarative host-agent research tasks; DOES NOT execute external tools')
    research.add_argument('--input',required=True)
    research.add_argument('--capabilities')
    research.add_argument('--receipts')
    evidence=sub.add_parser('evidence',help='Conditionally select studies and analyze documented theory tensions')
    evidence.add_argument('--input',required=True)
    sim=sub.add_parser('simulate',help='Seeded, UNCALIBRATED Monte Carlo with user scenario parameters')
    sim.add_argument('--input',required=True)
    sim.add_argument('--assumptions',required=True)
    tax=sub.add_parser('tax-math',help='HYPOTHETICAL user-provided brackets; not jurisdiction-specific tax')
    tax.add_argument('--input',required=True)
    portfolio=sub.add_parser('portfolio',help='Study weighted mean, costs and risk for user-supplied assumptions')
    portfolio.add_argument('--input',required=True)
    compare_cmd=sub.add_parser('review',help='Compare two fully generated JSON plans; no background activity')
    compare_cmd.add_argument('--previous',required=True)
    compare_cmd.add_argument('--current',required=True)
    for cmd in [plan,research,evidence,sim,tax,portfolio,compare_cmd]:
        cmd.add_argument('--out',help='Explicitly requested local path for generated result; no cloud upload')
    a=app.parse_args(argv)
    try:
        if a.command=='validate':
            p=read(a.input);normalized,schema=normalize_profile_v5(p)
            ans={'status':'VALID','input_schema':schema,'internal_compat_schema':normalized['schema_version'],
                 'input_hash':digest(p),'external_calls_executed':0}
        elif a.command in ('run','host-queue'):
            args=dict(
                profile=read(a.input),capabilities=read(a.capabilities) if a.capabilities else None,
                receipts=read(a.receipts) if a.receipts else None,
            )
            if a.command=='run':
                args.update(assumptions=read(a.assumptions) if a.assumptions else None,
                            hypothetical_tax=read(a.tax_scenario) if a.tax_scenario else None,
                            portfolio=read(a.portfolio) if a.portfolio else None,
                            previous=read(a.previous) if a.previous else None,
                            law_packets=read(a.law_packets) if a.law_packets else None,
                            macro_bundle=read(a.macro_bundle) if a.macro_bundle else None)
            report=build_integrated(**args)
            ans=report if a.command=='run' else report['host_action_queue']
        elif a.command=='evidence':
            p,_=normalize_profile_v5(read(a.input));ans=evaluate(p)
        elif a.command=='simulate':
            p,_=normalize_profile_v5(read(a.input));ans=simulate(p,read(a.assumptions))
        elif a.command=='tax-math':ans=calculate_hypothetical_tax(read(a.input))
        elif a.command=='portfolio':ans=portfolio_diagnostics(read(a.input))
        else:ans=compare(read(a.previous),read(a.current))
        result=render_md(ans) if a.command=='run' and a.format=='md' else json.dumps(ans,ensure_ascii=False,indent=2)+'\n'
        if getattr(a,'out',None):
            target=Path(a.out)
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(result,encoding='utf8')
            try:target.chmod(0o600)
            except OSError:pass
        else:print(result,end='')
        return 0
    except (ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError,FileNotFoundError,
            PermissionError,json.JSONDecodeError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':sys.exit(cli())
