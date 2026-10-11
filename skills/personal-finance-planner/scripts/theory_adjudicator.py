#!/usr/bin/env python3
"""Compare scientific theories, decision heuristics and apparently conflicting policies.

This is a *transparent comparison procedure*, NOT a truth ranker or an optimizer.
Conflicts between binding laws are deliberately excluded from reconciliation.
"""
import argparse
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent.parent

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def reconcile_case(case):
    graph=read_json(BASE/'policies'/'theory_graph.json')
    target=case.get('targets',{})
    horizon=target.get('time_horizon_years')
    evidence=target.get('active_edge_evidence','unknown')
    recommendations=[]
    relations=[]
    for rel in graph['relations']:
        state='BOTH_SIDES_WITH_CONDITIONS'
        resolution=rel['resolution']
        if {'GRAHAM','BOGLE'} == {rel['a'],rel['b']}:
            if evidence != 'independently_verified_after_costs':
                state='INDEX_AS_BASELINE_ACTIVE_EDGE_UNVERIFIED'
                resolution='尚无独立验证且税费后的主动超额收益证据：将低成本分散指数作为研究基准；价值选股仅作为单独假设，不据此放大主动交易风险。'
            else:
                state='COMPARE_INDEX_VERSUS_RESEARCH_PROCESS'
                resolution='已有被独立验证的历史主动优势也不能推导未来必胜；比较成本、容量、失效、税务及风险预算后，可并行测试。'
        elif {'ALM','BOGLE'} == {rel['a'],rel['b']}:
            if isinstance(horizon,(int,float)) and horizon <= 3:
                state='LIQUIDITY_FIRST_FOR_THIS_GOAL'
                resolution='期限不超过3年的这笔目标资金先保证到期可用，不以长期指数权益波动来匹配固定到期支出。'
            elif isinstance(horizon,(int,float)) and horizon >= 10:
                state='LONG_HORIZON_WITH_SHORT_TERM_RESERVES'
                resolution='长期资金可研究广泛分散低成本组合，短期预算和应急储备保留为独立现金桶。'
        relations.append({'pair':[rel['a'],rel['b']],'relation':rel['relation'],
                          'question':rel['question'],'decision_state':state,
                          'resolution':resolution,'disclosure':rel['disclosure']})
    for p in graph['principles']:
        recommendations.append({'id':p['id'],'name':p['label'],'evidence_kind':p['kind'],
                                'role':p['decision'],'limits':p['limits'],
                                'reference_ids':p['refs']})
    return {'version':'0.3.0','long_horizon_years':horizon,
            'research_policy':'No popularity voting, no artificial averaging of contradictions. Law is externally verified and binding, finance is conditional on assumptions and evidence.',
            'principles':recommendations,'comparison':relations,
            'unresolved':['无法自动定论的真实经济学争议需给至少两个可检验方案及敏感性区间。',
                          '如果出现真实法律冲突或双重居民问题，必须查适用双边协定和执业律师/税务师，不能用AI投票解决。',
                          '书籍与大师意见是研究输入，不可自动提升为已验证法律或可保证盈利公式。']}

def main():
    ap=argparse.ArgumentParser(description='Conditional theory comparison')
    ap.add_argument('--case',required=True)
    ap.add_argument('--out')
    args=ap.parse_args()
    output=json.dumps(reconcile_case(read_json(args.case)),ensure_ascii=False,indent=2)+'\n'
    if args.out:
        out=Path(args.out)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(output,encoding='utf8')
    else:
        print(output,end='')

if __name__=='__main__':
    main()
