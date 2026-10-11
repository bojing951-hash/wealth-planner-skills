"""A *tool-call plan* for Claude Code/Codex hosts, not an autonomous agent.

All source retrieval is delegated to authorized host tools. Receipts are
host-provided provenance records and can never, by themselves, turn into a
legally binding tax determination or an automated transaction.
"""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlparse

from . import VERSION
from .capabilities import capability_state, normalize_manifest
from .finance import financial_snapshot
from .profile import validate_profile, ProfileError

REGISTRY = json.loads((Path(__file__).resolve().parent / 'data' / 'official_domains.json').read_text(encoding='utf-8'))


def canonical(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(obj: dict) -> str:
    return sha256(canonical(obj).encode('utf-8')).hexdigest()


def jurisdiction_scopes(p: dict) -> list[dict]:
    roles = {}
    def add(scope: str, role: str):
        roles.setdefault(scope, set()).add(role)
    person = p['person']
    res = person['residence']
    country = res['country']
    add(country, 'actual_residence_reported')
    for c in person.get('citizenships', []):
        add(c, 'citizenship_not_automatically_tax_residency')
    for c in person.get('tax_residencies_claimed', []):
        add(c, 'tax_residency_unverified_claim')
    if country in {'US', 'CN'}:
        region = (res.get('region') or '').strip()
        city = (res.get('city') or '').strip()
        if region:
            add(country + ':' + region, 'state_or_province_rule_research')
            if city:
                add(country + ':' + region + ':' + city, 'city_level_rule_research')
    for inc in p['income']:
        for field, role in (
            ('activity_country','income_activity_place_not_automatically_source'),
            ('payer_country','payer_contact_not_necessarily_source'),
            ('bank_country','bank_location_not_tax_residence'),
        ):
            code = inc.get(field)
            if code:
                add(code, role + ':' + inc['id'])
    for asset in p['assets']:
        if asset.get('location_country'):
            add(asset['location_country'], 'asset_situs_or_custody:' + asset['id'])
    return [{'scope': scope, 'roles': sorted(roles[scope]),
             'needs_current_law_verification': True}
            for scope in sorted(roles)]


def _source_action(scope: str, year: int) -> dict:
    return {
        'id': f'law:{scope}:{year}', 'kind': 'verify_official_rules',
        'requires': ['source_discovery', 'source_fetch'],
        'scope': scope, 'tax_year': year,
        'purpose': ('Locate and open primary current sources: residence tests, applicable tax and social insurance, '
                    'investment permission, international reporting, estate and pension where relevant; '
                    'verify effective dates, definitions and the precise locality. Do NOT copy rates from an old example.'),
        'expected_receipt_fields': ['action_id', 'status', 'source_url', 'retrieved_on', 'content_sha256', 'tax_year'],
        'not_a_conclusion': 'Source retrieval alone does not establish user legal status or the correct tax amount.',
    }


def plan_actions(profile: dict, capabilities: dict, scopes: list[dict]) -> list[dict]:
    year = date.fromisoformat(profile['as_of']).year
    actions = []
    for obj in scopes:
        a = _source_action(obj['scope'], year)
        a['state'] = capability_state(capabilities, a['requires'])
        a['fallback'] = ('Collect tax-year-specific official URLs for licensed review; mark conclusions unverified; '
                         'continue only with labelled hypothetical non-binding arithmetic.')
        actions.append(a)
    goals = profile['goals']
    as_of = date.fromisoformat(profile['as_of'])
    long_targets = [g for g in goals if (date.fromisoformat(g['target_date'])-as_of).days >= 365*8]
    for cur in sorted(set(g['currency'] for g in long_targets)):
        a = {
            'id': f'macro:{cur}:long-horizon', 'kind': 'research_long_horizon_capital_market_assumptions',
            'requires': ['source_discovery', 'source_fetch'], 'currency': cur,
            'purpose': ('Retrieve dated primary/credible macro series in spending currency: inflation, real yield, '
                        'long-horizon valuation and risks. Separate observation, inference, future assumption. '
                        'Do NOT make tactical asset allocation changes based on one-month news.'),
            'expected_receipt_fields': ['action_id', 'status', 'source_url', 'retrieved_on', 'content_sha256'],
            'not_a_conclusion': 'Retrieved macro data does not automatically become forecast parameters.',
        }
        a['state'] = capability_state(capabilities, a['requires'])
        a['fallback'] = 'Use clearly labelled scenario ranges; never claim historical market data has been freshly retrieved.'
        actions.append(a)
    if profile.get('documents'):
        a = {
            'id': 'files:parse:user-provided', 'kind': 'parse_user_documents', 'requires': ['parse_user_files'],
            'purpose': 'Read only explicitly authorized files; extract provenance, date, currency and accounting ownership.',
            'fallback': 'Use manual user-reported inputs, marked unverified.'}
        a['state'] = capability_state(capabilities, a['requires'], consent=profile['consents']['use_user_files'])
        actions.append(a)
    if profile.get('account_connection_requested'):
        a = {
            'id': 'accounts:read_only', 'kind': 'authorized_account_read',
            'requires': ['authorized_account_read'], 'purpose': 'Read authorized account records in read-only mode.',
            'fallback': 'Use manual data; never authenticate on behalf of user or pretend connector was used.'}
        a['state'] = capability_state(capabilities, a['requires'], consent=profile['consents']['connect_accounts'])
        actions.append(a)
    if profile.get('schedule_requested'):
        a = {
            'id': 'schedule:periodic-review', 'kind': 'schedule_review',
            'requires': ['scheduled_execution', 'private_state'],
            'purpose': 'Schedule non-transactional review only if the user explicitly requested and approved persistence.',
            'fallback': 'Provide user a manual monthly/annual checklist; do not claim background monitoring.'}
        a['state'] = capability_state(capabilities, a['requires'], consent=profile['consents']['persist'])
        actions.append(a)
    return actions


def official_domain(scope: str, url: str) -> bool:
    domains = REGISTRY['jurisdiction_domains']
    allowed = domains.get(scope)
    if not allowed:
        # Unknown jurisdictions are NOT automatically verifiable by this hardcoded allowlist.
        return False
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        return False
    host = parsed.hostname.lower().rstrip('.')
    return any(host == domain or host.endswith('.' + domain) for domain in allowed)


def receipts_result(receipts: list | None, actions: list, as_of: str) -> dict:
    """Check receipt *metadata* only; no retrieval and no legal interpretation."""
    if receipts is None:
        receipts = []
    if not isinstance(receipts, list):
        raise ProfileError('receipts must be a list')
    actions_by_id = {a['id']: a for a in actions}
    errors, validated = [], []
    used = set()
    for n, r in enumerate(receipts):
        if not isinstance(r, dict):
            raise ProfileError(f'receipts[{n}] must be an object')
        identity = r.get('action_id')
        if identity not in actions_by_id or identity in used:
            raise ProfileError(f'receipts[{n}] contains unknown or duplicate action_id')
        used.add(identity)
        action = actions_by_id[identity]
        if action['state'] != 'READY_FOR_HOST_EXECUTION':
            raise ProfileError(f'{identity}: may not supply receipt for unavailable or unauthorized capability')
        if r.get('status') != 'completed':
            validated.append({'action_id':identity,'state':'FAILED_OR_INCOMPLETE',
                              'reason':'The host did not report a completed retrieval.'})
            continue
        url = r.get('source_url')
        fetched = r.get('retrieved_on')
        sh = r.get('content_sha256')
        if not isinstance(url,str) or not isinstance(fetched,str) or not isinstance(sh,str):
            raise ProfileError(f'{identity}: completed receipt must contain URL, retrieval date and SHA256')
        try:
            fetched_date = date.fromisoformat(fetched)
        except ValueError:
            raise ProfileError(f'{identity}: retrieved_on must be YYYY-MM-DD') from None
        if fetched_date > date.fromisoformat(as_of):
            raise ProfileError(f'{identity}: retrieved_on cannot be in the future relative to plan as_of')
        if len(sh) != 64 or any(c not in '0123456789abcdef' for c in sh.lower()):
            raise ProfileError(f'{identity}: content_sha256 must contain 64 hex chars')
        if action['kind'] == 'verify_official_rules':
            is_primary = official_domain(action['scope'], url)
            year_matched = type(r.get('tax_year')) is int and r['tax_year'] == action['tax_year']
            review_state = ('RETRIEVED_PRIMARY_DOMAIN_PENDING_LEGAL_INTERPRETATION' if is_primary and year_matched
                            else 'UNVERIFIED_WRONG_YEAR_OR_NONOFFICIAL_DOMAIN')
        else:
            is_primary = urlparse(url).scheme == 'https'
            review_state = ('MACRO_SOURCE_RETRIEVED_NOT_MODEL_CALIBRATED' if is_primary else 'UNVERIFIED_MACRO_SOURCE')
        validated.append({'action_id': identity, 'state': review_state,
                          'url': url, 'retrieved_on': fetched,
                          'content_sha256': sh.lower(),
                          'applicable_tax_year': r.get('tax_year'),
                          'assurance_limit': 'Metadata/domain-only check; no substantive content or legal applicability confirmed.'})
    return {'receipt_count':len(validated),'items':validated,'errors':errors,
            'note':'Receipts are delegated host observations, not skill-side web executions or legal opinions.'}


def _blocking_and_missing(profile: dict, financial: dict, scopes: list[dict], actions: list[dict]) -> tuple[list, list]:
    missing = []
    blocked = []
    person = profile['person']
    if not person.get('tax_residencies_claimed'):
        missing.append('Self-reported tax residence not provided; cannot infer from bank, citizenship or current home alone.')
    if person['residence']['country'] == 'EU':
        blocked.append('EU is not a standalone personal-income-tax jurisdiction; specify a member state.')
    if any(':' not in o['scope'] and o['scope'] not in {'US','CN','FR','HK','TH','EU'} for o in scopes):
        blocked.append('At least one country lacks a curated official-source checklist; perform country-specific primary research.')
    if any(a['kind'] == 'verify_official_rules' for a in actions):
        blocked.append('No tax-year-specific binding legal or tax conclusion without substantive official-source and user-status review.')
    blocked.extend(['No automatic tax filing, bank transfer, brokerage trade, or tax-avoidance execution.',
                    'Final investable amount and personalized securities trades are NOT authorized by this v0.4 skill.'])
    for cur, bucket in financial['currency_buckets'].items():
        if bucket['cashflow_status'] == 'INCOMPLETE_GROSS_ONLY':
            blocked.append(f'{cur}: gross income cannot be used as post-tax investable cash; supply actual net receipts and tax reserve.')
        if bucket['cashflow_status'] == 'PROVISIONAL_TAX_UNVERIFIED':
            missing.append(f'{cur}: tax treatment/settlement not verified; monthly surplus is provisional.')
    return sorted(set(blocked)), sorted(set(missing))


def _states(financial: dict, actions: list[dict], source_receipts: dict) -> list[dict]:
    has_cash_data = any(bucket['monthly_surplus_conditional'] is not None for bucket in financial['currency_buckets'].values())
    has_source_actions = any(a['kind'] == 'verify_official_rules' for a in actions)
    has_macro_evidence = any(r['action_id'].startswith('macro:') and r['state'].startswith('MACRO_SOURCE_RETRIEVED') for r in source_receipts['items'])
    has_source_evidence = any(r['state'] == 'RETRIEVED_PRIMARY_DOMAIN_PENDING_LEGAL_INTERPRETATION' for r in source_receipts['items'])
    stages = [
        ('INTAKE', 'COMPLETE_INPUT_SCHEMA_CHECK'),
        ('CAPABILITY_CHECK', 'COMPLETE_DECLARATIONS_ONLY'),
        ('FACT_VERIFICATION', 'USER_REPORTED_NOT_INDEPENDENTLY_AUDITED'),
        ('JURISDICTION_GATE', 'BLOCKED_FINAL_TAX_UNTIL_PRIMARY_REVIEW' if has_source_actions else 'NEEDS_JURISDICTION'),
        ('HOUSEHOLD_SOLVENCY', 'CONDITIONAL_MATH' if has_cash_data else 'BLOCKED_INSUFFICIENT_NET_DATA'),
        ('GOAL_AND_LIFECYCLE', 'GOALS_REGISTERED_NOT_OPTIMIZED'),
        ('EVIDENCE_RESEARCH', 'HOST_SOURCE_METADATA_RECEIVED_PENDING_CONTENT_REVIEW' if has_source_evidence else 'RESEARCH_TASKS_PLANNED_NOT_EXECUTED'),
        ('MACRO_SCENARIOS', 'MACRO_SOURCE_RECEIVED_NOT_MODEL_CALIBRATED' if has_macro_evidence else 'DEFERRED_NO_MODEL_CALIBRATION'),
        ('CANDIDATE_PLANS', 'DEFERRED_PENDING_GATES'),
        ('DETERMINISTIC_AND_STOCHASTIC_VALIDATION', 'DETERMINISTIC_CASHFLOW_ONLY_NO_MC'),
        ('POLICY_CHECK', 'NO_L3_ACTIONS_ALLOWED'),
        ('EXPLAIN_AND_MONITOR', 'LOCAL_REPORT_WITH_NO_BACKGROUND_MONITORING'),
    ]
    return [{'name':n,'status':s} for n,s in stages]


def build_plan(profile: dict, raw_manifest: dict | None = None, receipts: list | None = None) -> dict:
    validate_profile(profile)
    capabilities = normalize_manifest(raw_manifest)
    financial = financial_snapshot(profile)
    scopes = jurisdiction_scopes(profile)
    actions = plan_actions(profile, capabilities, scopes)
    source_receipts = receipts_result(receipts, actions, profile['as_of'])
    blocked, missing = _blocking_and_missing(profile, financial, scopes, actions)
    input_hash = digest(profile)
    capability_hash = digest(capabilities)
    run_id = 'v04-' + sha256((input_hash + capability_hash + VERSION).encode('ascii')).hexdigest()[:16]
    if source_receipts['receipt_count']:
        run_id = 'v04-' + digest({'profile':input_hash,'capabilities':capability_hash,
                                 'receipts':source_receipts['items']})[:16]
    return {
        'run_id': run_id, 'skill_version': VERSION, 'schema_version': profile['schema_version'],
        'as_of': profile['as_of'], 'profile_id': profile['profile_id'],
        'audit': {
            'input_sha256': input_hash, 'capabilities_sha256': capability_hash,
            'calculator': 'wealth_core.finance v0.4.0', 'code_version':VERSION,
            'reproducible_with_same_inputs': True,
            'stores_personal_financial_data': False,
            'warning':'Inputs are not independently audited. This tool does not make binding legal/tax assessments.'},
        'host': {'name':capabilities['host'], 'status':capabilities['status'],
                 'capabilities':capabilities['capabilities']},
        'jurisdiction_map': scopes,
        'requested_host_actions': actions,
        'host_action_receipts': source_receipts,
        'financial_snapshot': financial,
        'goals_registered_not_forecast': [
            {'id':g['id'],'currency':g['currency'],'target_amount':g['target_amount'],
             'target_date':g['target_date']} for g in profile['goals']],
        'workflow': _states(financial, actions, source_receipts),
        'blocked_decisions': blocked,
        'missing_facts': missing,
        'monitoring_triggers': ['income or household expense material change','move or different tax residence',
                                'major debt/health/family event','official tax rule effective date change',
                                'annual policy review (manual unless separately scheduled)'],
        'out_of_scope_until_later_version': [
            'Exact locality-specific tax engines and 401(k)/social contributions (v0.5)',
            'Tax-aware investment allocation and life-cycle ALM (v0.6)',
            'Calibrated Monte Carlo, historical replay and sequence risk (v0.7)',
            'Always-on account sync / automatic monitoring (later with explicit consent)',
        ],
    }
