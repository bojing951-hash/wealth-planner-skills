"""Host-mediated research/action lifecycle; does NOT invoke a host Agent by itself.

A Skill cannot summon network tools unavailable at runtime. The returned calls
are tool-intent records for the host to inspect/execute with actual permission.
"""
from __future__ import annotations
from .orchestration import build_plan


def make_host_queue(plan: dict) -> dict:
    queue = []
    for action in plan['requested_host_actions']:
        state = action['state']
        queue.append({
            'id': action['id'], 'action_kind': action['kind'],
            'status': 'QUEUED_FOR_HOST' if state == 'READY_FOR_HOST_EXECUTION' else state,
            'host_must_choose_actual_tool': True,
            'capabilities_required': action['requires'],
            'task_instructions': action['purpose'],
            'receipt_expected': action.get('expected_receipt_fields', []),
            'scope': action.get('scope'), 'tax_year': action.get('tax_year'),
            'fallback': action.get('fallback'),
            'permission_requirement': 'Host checks actual runtime tool availability and applicable user consent before every call.',
        })
    received = {r['action_id']: r for r in plan['host_action_receipts']['items']}
    for item in queue:
        r = received.get(item['id'])
        if r:
            item['status'] = r['state']
            item['source_metadata'] = {k: v for k,v in r.items() if k in ('url', 'retrieved_on', 'content_sha256', 'applicable_tax_year')}
            item['still_needs_human_substantive_review'] = True
    return {
        'queue': queue,
        'ready_count': sum(x['status'] == 'QUEUED_FOR_HOST' for x in queue),
        'completed_metadata_count': len(received),
        'execution_guarantee': 'NONE: queue is declarative; only real host-side calls are executable',
        'boundary': 'User-facing investments, account actions, tax filings and private disclosures are never implicitly authorized.',
    }
