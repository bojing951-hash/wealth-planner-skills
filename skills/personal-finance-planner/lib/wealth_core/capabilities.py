"""Host capability manifest validation and conservative routing.

A manifest reflects a host's *declaration*, NOT proof that an action was actually
executed. This library cannot discover Claude/Codex private tools by itself.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_CAPABILITIES = (
    'source_discovery', 'source_fetch', 'execute_math', 'parse_user_files',
    'authorized_account_read', 'private_state', 'scheduled_execution',
    'professional_handoff',
)
PERMISSIONS = {'granted', 'ask', 'denied'}


class CapabilityError(ValueError):
    pass


def normalize_manifest(raw: dict | None) -> dict:
    if raw is None:
        raw = {'host': 'offline_unprovided', 'capabilities': {}}
    if not isinstance(raw, dict):
        raise CapabilityError('capability manifest must be an object')
    host = raw.get('host', 'unknown')
    if not isinstance(host, str) or not host.strip():
        raise CapabilityError('host must be a nonempty string')
    caps = raw.get('capabilities', {})
    if not isinstance(caps, dict):
        raise CapabilityError('capabilities must be an object')
    extra = set(caps) - set(VALID_CAPABILITIES)
    if extra:
        raise CapabilityError('unknown capabilities: ' + ', '.join(sorted(extra)))
    out = {}
    for name in VALID_CAPABILITIES:
        c = caps.get(name, {})
        if not isinstance(c, dict):
            raise CapabilityError(f'{name} must be an object')
        available = c.get('available', False)
        permission = c.get('permission', 'ask')
        if type(available) is not bool or permission not in PERMISSIONS:
            raise CapabilityError(f'{name}: available must be bool, permission must be granted/ask/denied')
        tool = c.get('tool_label')
        if tool is not None and not isinstance(tool, str):
            raise CapabilityError(f'{name}.tool_label must be a string')
        out[name] = {'available': available, 'permission': permission,
                     'tool_label': tool or 'host_selects_actual_tool'}
    return {'host': host, 'capabilities': out, 'status': 'DECLARED_NOT_EXECUTED'}


def capability_state(manifest: dict, needed: list[str], consent: bool | None = None) -> str:
    if consent is False:
        return 'DISABLED_NO_USER_CONSENT'
    infos = [manifest['capabilities'][name] for name in needed]
    if any(not x['available'] for x in infos):
        return 'UNAVAILABLE'
    if any(x['permission'] == 'denied' for x in infos):
        return 'PERMISSION_DENIED'
    if any(x['permission'] == 'ask' for x in infos):
        return 'NEEDS_USER_OR_HOST_APPROVAL'
    return 'READY_FOR_HOST_EXECUTION'
