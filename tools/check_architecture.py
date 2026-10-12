#!/usr/bin/env python3
"""Offline architecture guardrail for the ORIGINAL v0.4 Wealth Planner baseline.

It validates FILE/STRUCTURE and a few key language invariants. It CANNOT verify
financial reasoning, legal applicability, active host tools, or remote research.
Each release requires an additional HUMAN-RUN alignment table and E2E record.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'docs/architecture_contract.json'
EXPECTED_DOMAINS = [
    'profile_and_data_quality', 'jurisdiction_and_compliance', 'personal_cashflow',
    'life_cycle_and_goals', 'economics_and_evidence', 'long_term_macro',
    'investment_policy', 'simulation_and_risk', 'decision_and_execution',
    'audit_and_monitoring',
]
EXPECTED_STATES = [
    'INTAKE','CAPABILITY_CHECK','FACT_VERIFICATION','JURISDICTION_GATE',
    'HOUSEHOLD_SOLVENCY','GOAL_AND_LIFECYCLE','EVIDENCE_RESEARCH',
    'MACRO_SCENARIOS','CANDIDATE_PLANS','DETERMINISTIC_AND_STOCHASTIC_VALIDATION',
    'POLICY_CHECK','EXPLAIN_AND_MONITOR',
]

def check(root: Path = ROOT) -> dict:
    messages: list[str] = []
    warnings: list[str] = []
    try:
        contract = json.loads((root / 'docs/architecture_contract.json').read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return {'ok':False,'errors':[f'missing/bad contract: {exc}'],'warnings':[],'domains_present':0,'states_present':0}

    bpath = root / contract['baseline_file']
    if not bpath.is_file() or sha256(bpath.read_bytes()).hexdigest() != contract['baseline_sha256']:
        messages.append('Original v0.4 architecture baseline missing or modified; restore it before release.')

    skill = root / contract['skill_path']
    manifest = skill / 'SKILL.md'
    contents = manifest.read_text(encoding='utf-8') if manifest.is_file() else ''
    if not contents.startswith('---\n'):
        messages.append('SKILL.md must begin with YAML frontmatter')
        frontmatter = ''
    else:
        end = contents.find('\n---\n', 4)
        frontmatter = contents[4:end] if end > 0 else ''
        if not frontmatter:
            messages.append('SKILL.md YAML frontmatter closing separator missing')
    mname = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
    if not mname or mname.group(1).strip(' "\'') != skill.name:
        messages.append('SKILL.md name and containing directory differ or name absent')
    mdescription = re.search(r'^description:\s*(.+)$',frontmatter, re.MULTILINE)
    if not mdescription or not (1 <= len(mdescription.group(1)) <= 1024):
        messages.append('SKILL.md description missing or outside 1..1024 chars')
    if len(contents.splitlines()) > 500:
        messages.append('SKILL.md exceeds 500-line progressive disclosure recommendation')
    if contract['skill_version'] not in frontmatter:
        messages.append('Skill frontmatter version mismatched with contract')

    for rel in contract['mandatory_skill_resources']:
        if not (skill / rel).is_file():
            messages.append('Missing mandatory Skill resource: '+rel)

    # Catch broken relative links in the manifest, useful for independent Skill packaging.
    for href in re.findall(r'\]\(([^)]+)\)', contents):
        if href.startswith(('http:','https:','#')):
            continue
        if not (skill / href.split('#',1)[0]).is_file():
            messages.append('Broken SKILL.md local link: '+href)

    domain_rows = contract.get('ten_domains', [])
    keys = [d.get('key') for d in domain_rows]
    if keys != EXPECTED_DOMAINS:
        messages.append('Ten domains drift from original v0.4 ordering or keys')
    domain_index = (skill/'references/architecture-10-domains.md').read_text(encoding='utf-8') if (skill/'references/architecture-10-domains.md').is_file() else ''
    for row in domain_rows:
        for rel in (row['path'], row['implementation']):
            if not (skill/rel).is_file():
                messages.append(f'Domain {row["id"]} target missing: {rel}')
        if f'`{row["key"]}`' not in domain_index:
            messages.append(f'Domain {row["id"]} absent from normative Skill domain index')
        if row.get('status') == 'COMPLETE' and row.get('unresolved'):
            messages.append(f'Domain {row["id"]} declared COMPLETE while unresolved gaps remain')

    states = contract.get('twelve_states',[])
    if states != EXPECTED_STATES:
        messages.append('State machine differs from original v0.4 workflow')
    states_doc = (skill/'workflows/skill-first-execution.md').read_text(encoding='utf-8') if (skill/'workflows/skill-first-execution.md').is_file() else ''
    for state in EXPECTED_STATES:
        if f'`{state}`' not in states_doc:
            messages.append('Missing state instruction: '+state)

    # Enforce essential host/skill separation in entry point and runtime guide.
    for phrase in ('HOST Agent', 'host-queue', 'NOT_VERIFIED', 'No automated trades', 'monitoring'):
        if phrase.lower() not in contents.lower():
            messages.append('SKILL.md missing key instruction: '+phrase)
    host_protocol = skill/'workflows/host-research-protocol.md'
    protocol_text = host_protocol.read_text(encoding='utf-8').lower() if host_protocol.is_file() else ''
    for phrase in ('No autonomous', 'host', 'consent'):
        if phrase.lower() not in protocol_text:
            warnings.append('Host research protocol may not explicitly mention: '+phrase)

    # v5.2 optional financial-memory feature must never bypass the host consent
    # boundary; these are static checks, not human authorization proofs.
    if tuple(int(x) for x in contract['release'].split('.')) >= (5,2,0):
        memfiles=['workflows/local-memory.md','scripts/memory_cli.py',
                  'lib/wealth_core/local_memory.py','schemas/memory-changes-v5.2.schema.json']
        for rel in memfiles:
            if not (skill/rel).is_file():
                messages.append('Missing v5.2 optional memory component: '+rel)
        guide=(skill/'workflows/local-memory.md').read_text(encoding='utf-8') if (skill/'workflows/local-memory.md').is_file() else ''
        for phrase in ('L1','L2','preview','user approval','delete','no agent scheduler'):
            if phrase.lower() not in guide.lower():
                messages.append('Memory guide missing consent/privacy invariant: '+phrase)
        if 'Memory is OFF by default' not in contents:
            messages.append('SKILL.md must explicitly default private memory OFF')
        memory_cli=skill/'scripts/memory_cli.py'
        if memory_cli.is_file() and 'approved-preview-sha256' not in memory_cli.read_text(encoding='utf-8'):
            messages.append('Memory CLI must require match to user-reviewed proposed changes')

    # v5.3 professional consulting requirements; forbid another independently running Agent.
    if tuple(int(x) for x in contract['release'].split('.')) >= (5,3,0):
        consulting = (skill/'workflows/professional-consultation.md')
        content=consulting.read_text(encoding='utf-8') if consulting.is_file() else ''
        for marker in ('root cause', '30/90/365', 'two', 'HOST-driven', 'D01', 'D10'):
            if marker.lower() not in content.lower():
                messages.append('Professional consultation workflow missing gate: '+marker)
        for marker in ('Professional consultation mode', 'problem → root cause', 'workflows/professional-consultation.md'):
            if marker not in contents:
                messages.append('SKILL.md is not routing comprehensive-plan requests: '+marker)
        for rel in ('scripts/plan_quality.py','scripts/consultation_math.py','schemas/consultation-v5.3.schema.json'):
            if not (skill/rel).is_file():
                messages.append('Missing consultation validation component: '+rel)

    align = root / ('docs/ARCHITECTURE_ALIGNMENT_v'+contract['release']+'.md')
    if not align.is_file():
        messages.append('Every release requires a completed architecture comparison: '+align.name)
    release = root / 'docs/DEVELOPMENT_RELEASE_GATE.md'
    if not release.is_file():
        messages.append('Missing future-development release checklist')

    if not (root/'.github/workflows/tests.yml').is_file():
        warnings.append('No GitHub CI present')
    for p in (root/'tests/host_e2e').glob('*.md'):
        if 'live' in p.stem.lower():
            warnings.append(f'Check whether a host live test was actually executed: {p.name}')

    return {
        'ok':not messages, 'errors':messages, 'warnings':warnings,
        'baseline_sha256':contract['baseline_sha256'],
        'domains_present':len(keys),'states_present':len(states),
        'reported_domain_maturity':{d['key']:d['status'] for d in domain_rows},
        'contract_scope':'FILE_STRUCTURE_AND_TEXT_CHECKS_ONLY; DOES_NOT_PROVE_AGENT_BEHAVIOR_OR_LEGAL_ACCURACY',
    }

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--strict', action='store_true', help='exit nonzero on structural drift')
    parser.add_argument('--json',action='store_true',help='output machine-readable comparison')
    args = parser.parse_args()
    result=check()
    if args.json:
        print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print('Original v0.4 baseline hash:',result.get('baseline_sha256','?'))
        print('Release architecture alignment:', 'PASS (structure only)' if result['ok'] else 'FAIL')
        print(f"Ten domains: {result['domains_present']}/10; workflow states: {result['states_present']}/12")
        for msg in result.get('errors',[]):print('ERROR:',msg)
        for msg in result.get('warnings',[]):print('WARNING:',msg)
        print('LIMIT: structural validation is not a live financial/legal or host E2E evaluation.')
    return 0 if result['ok'] or not args.strict else 1

if __name__=='__main__':sys.exit(cli())
