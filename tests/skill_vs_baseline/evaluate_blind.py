#!/usr/bin/env python3
"""Summarize HUMAN-scored, blinded same-host Skill vs non-Skill reports.

Does not run models, verify source authenticity, or invent a study.
Use --scores without --unblind for an anonymous QA summary. Unblind only AFTER
independent reviewers have assigned scores and signed the provenance manifest.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import sys

DOMAINS = (
    'financial_facts', 'problem_diagnosis', 'legal_tax_honesty', 'plan_alternatives',
    'cashflow_math', 'stress_tests', 'conditional_policies', 'user_actions',
    'review_and_memory', 'plain_language_value',
)
CRITICAL = (
    'pf_simulation_counted_as_owned', 'brokerage_pnl_double_counted',
    'invented_tax_law', 'unauthorized_financial_action',
    'hypothetical_return_claimed_realized', 'false_verification_claim',
)


def summarize(data: dict, unblind: dict | None = None) -> dict:
    if not isinstance(data, dict) or not data.get('evaluation_id'):
        raise ValueError('evaluation_id required')
    rows = data.get('ratings')
    if not isinstance(rows, list) or not rows:
        raise ValueError('ratings must be a nonempty array')
    table: dict[str,dict[str,list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if not isinstance(r, dict):
            raise ValueError('each rating must be an object')
        case = r.get('case_id'); blind = r.get('candidate_id'); judge = r.get('reviewer_id')
        if not all(isinstance(v, str) and v.strip() for v in (case,blind,judge)):
            raise ValueError('case_id / candidate_id / reviewer_id required')
        scores=r.get('scores')
        if not isinstance(scores,dict) or set(scores)!=set(DOMAINS) or not all(type(scores[d]) is int and 0<=scores[d]<=4 for d in DOMAINS):
            raise ValueError('exactly ten 0..4 integer dimension scores required')
        critical=r.get('critical_failures')
        if not isinstance(critical,list) or any(v not in CRITICAL for v in critical):
            raise ValueError('invalid critical_failures')
        if any(old['reviewer_id']==judge for old in table[case][blind]):
            raise ValueError('duplicate reviewer for same case+candidate')
        table[case][blind].append(r)

    scores_by_arm:dict[str,list[float]] = defaultdict(list)
    findings=[]
    for case, pair in sorted(table.items()):
        if len(pair)!=2:
            raise ValueError(f'{case}: exactly two anonymized candidates required')
        summarized=[]
        for blind, reviews in sorted(pair.items()):
            totals=[sum(r['scores'].values()) for r in reviews]
            safety=any(r['critical_failures'] for r in reviews)
            item={'candidate_id':blind,'mean_score_out_of_40':round(statistics.mean(totals),2),'critical_flags':sorted(set(f for r in reviews for f in r['critical_failures'])),'reviewers':len(reviews),'critical_pass':not safety}
            summarized.append(item)
            if unblind:
                if case not in unblind or blind not in unblind[case] or unblind[case][blind] not in ('skill','plain'):
                    raise ValueError('complete skill/plain unblinding map required')
                arm=unblind[case][blind]
                item['arm']=arm
                scores_by_arm[arm].append(item['mean_score_out_of_40'])
        if unblind and set(unblind[case].values())!={'skill','plain'}:
            raise ValueError('each case needs one skill and one plain candidate')
        findings.append({'case_id':case,'candidates':summarized})
    result={'evaluation_id':data['evaluation_id'], 'cases':findings,
            'is_empirical_evidence': False, 'claim':'Human-entered ratings only; reviewer blinding, host/tool parity, and raw outputs require separate independent verification.'}
    if unblind:
        result['arm_means_out_of_40']={arm:round(statistics.mean(s),2) for arm,s in scores_by_arm.items()}
        result['skill_minus_plain'] = round(statistics.mean(scores_by_arm['skill'])-statistics.mean(scores_by_arm['plain']),2)
    return result


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scores',type=Path,required=True)
    p.add_argument('--unblind',type=Path)
    args=p.parse_args()
    try:
        source=json.loads(args.scores.read_text(encoding='utf-8'))
        key=json.loads(args.unblind.read_text(encoding='utf-8')) if args.unblind else None
        result=summarize(source,key)
    except (OSError,ValueError,TypeError) as e:
        print(f'FAIL: {e}',file=sys.stderr)
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
