#!/usr/bin/env python3
"""Conservative, deterministic country/jurisdiction research router.

Outputs research obligations, missing facts and blocked actions. Never computes
personal taxes, determines tax residency conclusively, or grants investment access.
The bundled country packs are bibliographic guides, not a legal rule engine.
"""
import argparse
from datetime import date
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
SUPPORTED = {p.stem for p in (BASE / 'jurisdictions').glob('*.json')}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def codes(value):
    return str(value or '').strip().upper()


def scan_sources(source_ids, on):
    registry = read_json(BASE / 'policies' / 'authority_sources.json')
    as_of = date.fromisoformat(on)
    result = []
    for sid in sorted(source_ids):
        record = registry.get(sid)
        if record is None:
            result.append({'id': sid, 'state': 'SOURCE_MISSING'})
            continue
        last = date.fromisoformat(record['last_checked'])
        age = (as_of - last).days
        expired = age > int(record['review_after_days'])
        result.append({'id': sid, 'title': record['title'], 'publisher': record['publisher'],
                       'url': record['url'], 'last_checked': str(last),
                       'state': 'STALE_RECHECK_REQUIRED' if expired or age < 0 else 'REFERENCE_ONLY_RECHECK_ON_USE'})
    return result


def route_case(case):
    if not isinstance(case, dict):
        raise ValueError('case must be an object')
    date.fromisoformat(case['as_of_date'])
    year = int(case.get('tax_year', 0))
    if year < 1900 or year > 2200:
        raise ValueError('tax_year must be a plausible integer')
    person = case.get('person', {})
    if not isinstance(person, dict):
        raise ValueError('person must be an object')
    roles = defaultdict(set)
    flags = []
    missing = []
    blocking = []
    income_events = []
    recognized = set()
    living = codes(person.get('living_country'))
    if not living:
        missing.append('实际居住国家/地区未知；需要居住地及税务年度')
    else:
        roles[living].add('living_country')
    for c in person.get('citizenships', []):
        c = codes(c)
        if c:
            roles[c].add('citizenship_does_not_equal_tax_residency')
    for c in person.get('tax_residences_claimed', []):
        c = codes(c)
        if c:
            roles[c].add('user_claimed_tax_residence_unverified')
    for c in (person.get('presence_days') or {}):
        if codes(c):
            roles[codes(c)].add('presence_days_requires_local_legal_test')
    us_person = str(person.get('us_person_status', 'unknown')).lower()
    if us_person == 'yes':
        roles['US'].add('self_declared_us_person_global_reporting_check')
    elif us_person == 'unknown':
        missing.append('美国公民/绿卡/税法居民身份尚未排除；涉及美国时需确认')
    if living == 'EU':
        member = codes(person.get('eu_member_country'))
        if not member:
            blocking.append('欧盟不是统一个人所得税国家：必须指定具体成员国（例如FR、DE）')
        else:
            roles[member].add('specified_eu_member_state')
            roles['EU'].add('eu_coordination_reference_only')
    elif living == 'FR':
        roles['EU'].add('eu_coordination_reference_only')

    incomes = case.get('income_streams', [])
    if not isinstance(incomes, list):
        raise ValueError('income_streams must be a list')
    for index, obj in enumerate(incomes):
        if not isinstance(obj, dict):
            raise ValueError('income event must be an object')
        ident = str(obj.get('id') or f'income_{index + 1}')
        if obj.get('payer_country'):
            roles[codes(obj['payer_country'])].add('payer_location_not_necessarily_tax_source')
        if obj.get('activity_country'):
            roles[codes(obj['activity_country'])].add('income_earning_activity')
        else:
            missing.append(f'{ident}:实际提供服务/产生收入活动的地区未知')
        if obj.get('bank_country'):
            roles[codes(obj['bank_country'])].add('bank_location_not_tax_residency')
        if not obj.get('kind'):
            missing.append(f'{ident}:所得种类和法律性质未明确')
        if not isinstance(obj.get('bank_received'), bool):
            missing.append(f'{ident}:是否已实际到账未知')
        if not obj.get('gross_or_net'):
            missing.append(f'{ident}:税前/税后收入口径未知')
        if obj.get('tax_status') not in ('professional_verified', 'unknown', 'reserved_estimate', 'not_applicable'):
            missing.append(f'{ident}:税务核定/预留状态未明确（不得默认为零税）')
        if obj.get('tax_status') in ('unknown', 'reserved_estimate', None):
            blocking.append(f'{ident}:税务分类或负担未核实，不能给出确定税后可投资金额')
        if obj.get('bank_received') is False:
            blocking.append(f'{ident}:尚未银行实际到账，不可计入当前已归属可用现金')
        if obj.get('kind') == 'prop_firm_simulated_profit':
            blocking.append(f'{ident}:PF模拟账户盈利不能计入个人已拥有的金融资产')
        if obj.get('gross_or_net') == 'net_declared' and obj.get('tax_status') != 'professional_verified':
            missing.append(f'{ident}:净收入为用户口径但相关法定税务未验证，须保留税务备付')
        if codes(obj.get('bank_country')) != codes(obj.get('activity_country')):
            flags.append({'severity':'high','id':'BANK_NOT_SOURCE',
                          'message':f'{ident}:收款银行所在地与收入活动所在地不同；银行地址不决定所得来源、居民身份或免税。'})
        if obj.get('kind', '').startswith('prop_firm'):
            flags.append({'severity':'high','id':'PF_INCOME_CLASSIFICATION',
                          'message':f'{ident}:PF收入性质可能涉及劳务/经营等分类，不能把模拟盈利直接视为证券资本利得。需按所在地法律与实际合同核定。'})
        if obj.get('earned_year') and int(obj['earned_year']) > year:
            missing.append(f'{ident}:取得收入年份晚于当前申报年度，请核查收入事件日期')
        income_events.append({'id':ident,'kind':obj.get('kind','unspecified'),
                              'bank_received':obj.get('bank_received','unknown'),
                              'tax_status':obj.get('tax_status','unknown'),
                              'sourcing_ambiguous':codes(obj.get('payer_country')) != codes(obj.get('activity_country'))})
    for obj in case.get('asset_locations', []):
        if obj.get('country'):
            roles[codes(obj['country'])].add('asset_or_custody_location')
    planned = []
    for obj in case.get('planned_moves', []):
        c = codes(obj.get('country'))
        if c:
            roles[c].add('future_move_not_current_tax_residency')
            planned.append({'jurisdiction':c,'year':obj.get('year','unknown'),
                            'note':'仅是未来情景；需建立迁移前、当年、迁移后三段税务及资产规划，不提前视作税务身份已变更。'})
    contexts = []
    source_ids = set()
    for c in sorted(roles):
        if c not in SUPPORTED:
            contexts.append({'jurisdiction':c,'roles':sorted(roles[c]),'status':'UNSUPPORTED_REQUIRES_PRIMARY_RESEARCH',
                             'questions':['查询该司法管辖区适用税年官方税务机关及法律','确认税收居民、收入来源、投资准入和资产继承规则'],
                             'flags':[],'source_ids':[]})
            blocking.append(f'{c}:知识库无已核查国家包，不能直接套用邻国或欧盟通用税率')
            continue
        pack = read_json(BASE / 'jurisdictions' / (c+'.json'))
        source_ids.update(pack['source_ids'])
        recognized.add(c)
        contexts.append({'jurisdiction':c,'name':pack['name'],'roles':sorted(roles[c]),
                         'status':'COUNTRY_RESEARCH_REQUIRED',
                         'questions':pack['questions'],'flags':pack['flags'],
                         'source_ids':pack['source_ids']})
        if pack.get('requires_member_state') and not person.get('eu_member_country'):
            blocking.append('欧盟规则不是个税率表：缺少具体成员国')
    if len([c for c in roles if c not in ['EU']]) > 1:
        flags.append({'severity':'high','id':'CROSS_BORDER_MULTIPLE_RULESETS',
                      'message':'同时出现多个国家/地区的税务联系点；税收居民、来源地课税、协定、抵免、账户报告及社保义务需逐项区分。'})
    if not person.get('tax_residences_claimed'):
        missing.append('未提供已申报的税收居民地区；不能由居住地、收款地自动推断')
    if year != date.fromisoformat(case['as_of_date']).year:
        flags.append({'severity':'medium','id':'YEAR_MISMATCH',
                      'message':'所分析税年与报告生成日期年份不同，必须加载该税年适用条文与过渡规则。'})
    evidence = scan_sources(source_ids, case['as_of_date'])
    if any(e['state'] != 'REFERENCE_ONLY_RECHECK_ON_USE' for e in evidence):
        blocking.append('有官方规则来源过期/缺失，必须更新后才能作时间敏感结论')
    status = 'NEEDS_LEGAL_TAX_REVIEW' if blocking or missing else 'READY_FOR_NON_BINDING_PLANNING'
    return {'version':'0.3.0','as_of_date':case['as_of_date'],'tax_year':year,
            'status':status,'jurisdictions':contexts,
            'issues':flags,'missing_facts':sorted(set(missing)),
            'blocking_facts':sorted(set(blocking)),'income_events':income_events,
            'planned_moves':planned,'primary_sources':evidence,
            'allowed_now':['教育性现金流/投资原则与假设情景计算（条件明确）','本地研究材料清单和需专业核实的问题'],
            'not_allowed_without_review':['宣称确定税收居民/法律结论','计算具体应缴税额并作为最终申报依据','未经核实将税前/模拟收益作为税后可投资资金','未核实准入就推荐跨境账户或投资交易','宣称收到香港银行即免税'],
            'method':'Deterministic legal research triage; no determination, no tax-rate calculator, not regulated advice.'}


def main():
    ap=argparse.ArgumentParser(description='Multi-jurisdiction research router, NOT a tax calculator.')
    ap.add_argument('--case',required=True)
    ap.add_argument('--out')
    args=ap.parse_args()
    report=route_case(read_json(args.case))
    result=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.out:
        out=Path(args.out)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(result,encoding='utf8')
    else:
        print(result,end='')

if __name__ == '__main__':
    main()
