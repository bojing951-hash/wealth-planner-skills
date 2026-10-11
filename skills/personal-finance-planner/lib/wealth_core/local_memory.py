"""Optional, local-only encrypted memory store for a host-driven personal finance Skill.

NOT an agent, scheduler or bank connector. Host must obtain user consent for
reads and each write. Persist only normalized user-reported/verified facts,
scenario summaries and decisions. No account numbers, credentials or raw files.

Encryption: AES-256-GCM with a random 256-bit key in a DIFFERENT private config
folder. This protects the data file if copied alone; same-OS-account malware,
users with access to the key, compromised hosts, swap, backups and snapshots are
outside this protection boundary. Refuse plaintext fallback if cryptography is
unavailable. This version intentionally does not claim OS hardware key storage.
"""
from __future__ import annotations

import base64
import hashlib
import copy
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import tempfile
import time
from contextlib import contextmanager
from typing import Any, Optional

STORE_FORMAT = 'wealth-planner-memory-v1'
MEMORY_SCHEMA = '5.2.0'
PROFILE_PATTERN = re.compile(r'^[a-z][a-z0-9_-]{2,47}$')
CURRENCY_PATTERN = re.compile(r'^[A-Z]{3}$')
ALLOWED_CONFIDENCE = {'user_reported', 'verified', 'assumption', 'unknown'}
ALLOWED_SOURCE = {'user', 'document_reviewed', 'authorized_connector', 'model', 'unknown'}
ALLOWED_FACTS = {
    'residence.country': 'country', 'residence.region': 'short_text',
    'residence.city': 'short_text', 'tax_residency.claims': 'countries',
    'household.status': 'household', 'household.dependents': 'integer',
    'income.source_type': 'income_source', 'income.monthly_gross': 'money',
    'income.monthly_net_realized': 'money', 'income.monthly_pf_bank_received': 'money',
    'expenses.essential_monthly': 'money',
    'expenses.discretionary_monthly': 'money',
    'assets.liquid': 'money', 'assets.investments': 'money',
    'assets.restricted': 'money', 'liabilities.total': 'money',
    'goal.target_amount': 'money', 'goal.target_date': 'date',
    'goal.horizon_years': 'years',
    'risk.max_drawdown_pct': 'percent',
    'preferences.investment_style': 'style',
}
FRESHNESS_DAYS = {
    'income.': 90, 'expenses.': 90, 'assets.': 31, 'liabilities.': 31,
    'residence.': 365, 'tax_residency.': 365, 'household.': 365,
    'goal.': 365, 'risk.': 365, 'preferences.': 730,
}
MAX_SNAPSHOTS = 600
MAX_RECORDS = 1000
MAX_VAULT_BYTES = 12 * 1024 * 1024
# Reject common personal identifiers and secrets in narrative fields. This is
# a defense-in-depth filter, NOT a guarantee against storing sensitive text.
SENSITIVE_NARRATIVE = re.compile(
    r"(?i)(?:[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|\b(?:\d[ -]?){13,19}\b|"
    r"(?:api[_ -]?key|access[_ -]?token|secret[_ -]?key|password|"
    r"account[_ -]?number|银行卡号|身份证号|密码|私钥))"
)

class MemoryErrorBase(Exception):
    """User-friendly error. Do not attach raw financial payload to errors."""

class ConsentRequired(MemoryErrorBase):
    pass

class RevisionConflict(MemoryErrorBase):
    pass

class MemorySecurityError(MemoryErrorBase):
    pass

class DataValidationError(MemoryErrorBase):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _date(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise DataValidationError(f'{name} must be ISO 8601 date')
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise DataValidationError(f'{name} must be YYYY-MM-DD') from None
    if parsed.isoformat() != value:
        raise DataValidationError(f'{name} must be YYYY-MM-DD')
    return value


def _profile_id(pid: str) -> str:
    if not isinstance(pid, str) or not PROFILE_PATTERN.fullmatch(pid):
        raise DataValidationError('profile_id must be a pseudonymous slug, e.g. user_001')
    return pid


def default_data_root() -> Path:
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA') or str(Path.home()/'AppData'/'Local'))/'WealthPlannerSkill'
    if sys.platform == 'darwin':
        return Path.home()/'Library'/'Application Support'/'WealthPlannerSkill'
    return Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local'/'share')/'wealth-planner-skill'


def default_key_root() -> Path:
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA') or str(Path.home()/'AppData'/'Local'))/'WealthPlannerSkillKeys'
    if sys.platform == 'darwin':
        return Path.home()/'Library'/'Preferences'/'WealthPlannerSkillKeys'
    return Path(os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')/'wealth-planner-skill'/'private-keys'


def _is_repo_path(target: Path) -> bool:
    """Never store private memory within a repo, including a parent repo."""
    for parent in (target, *target.parents):
        if (parent/'.git').exists():
            return True
    return False


def _assert_no_symlink_path(path: Path):
    for component in (path, *path.parents):
        if component.is_symlink():
            raise MemorySecurityError('Refusing symlinked memory directory or file')


def _secure_dir(path: Path, create: bool = False):
    path = path.expanduser().absolute()
    _assert_no_symlink_path(path)
    if _is_repo_path(path):
        raise MemorySecurityError('Refusing private memory inside a Git repository')
    if not path.exists():
        if not create:
            raise MemorySecurityError('Memory directory has not been initialized')
        path.mkdir(parents=True, mode=0o700, exist_ok=True)
    st = path.lstat()
    if not stat.S_ISDIR(st.st_mode):
        raise MemorySecurityError('Memory location must be a directory')
    if os.name == 'posix':
        if st.st_uid != os.getuid():
            raise MemorySecurityError('Memory directory owner mismatch')
        if st.st_mode & 0o077:
            if create:
                # Only modify the dedicated leaf directory, not ancestors.
                path.chmod(0o700)
            else:
                raise MemorySecurityError('Memory directory permissions must be 0700')
    return path


def _read_private(path: Path) -> bytes:
    _assert_no_symlink_path(path)
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(str(path), flags)
    except FileNotFoundError:
        raise MemorySecurityError('Encrypted vault or local key is missing') from None
    except OSError:
        raise MemorySecurityError('Unable to open private memory file') from None
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise MemorySecurityError('Private memory must be a regular single-link file')
        if os.name == 'posix' and (st.st_uid != os.getuid() or st.st_mode & 0o077):
            raise MemorySecurityError('Private memory file requires user ownership and 0600')
        if st.st_size > MAX_VAULT_BYTES:
            raise MemorySecurityError('Private memory file exceeds maximum allowed size')
        return os.read(fd, st.st_size + 1)
    finally:
        os.close(fd)


def _create_private_file(path: Path, content: bytes):
    _assert_no_symlink_path(path)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(str(path), flags, 0o600)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as f:
            f.write(content)
            f.flush()
            os.fsync(fd)
    finally:
        os.close(fd)


def _atomic_replace(path: Path, content: bytes):
    _assert_no_symlink_path(path)
    fd, tmp = tempfile.mkstemp(prefix='.memory-', suffix='.tmp', dir=path.parent)
    try:
        if os.name == 'posix': os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        if os.name == 'posix':
            dfd = os.open(str(path.parent), os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def _aesgcm_class():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        raise MemorySecurityError('Encrypted memory requires cryptography; no plaintext fallback') from None
    return AESGCM


def _encrypt(pid: str, key: bytes, state: dict) -> bytes:
    nonce = secrets.token_bytes(12)
    data = json.dumps(state, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    ciphertext = _aesgcm_class()(key).encrypt(nonce, data, ('wealth-memory:'+pid).encode())
    envelope = {'format':STORE_FORMAT,'nonce':base64.b64encode(nonce).decode(),
                'ciphertext':base64.b64encode(ciphertext).decode()}
    return json.dumps(envelope,separators=(',',':')).encode('ascii')


def _decrypt(pid: str, key: bytes, content: bytes) -> dict:
    try:
        envelope=json.loads(content)
        if envelope['format'] != STORE_FORMAT: raise ValueError('format mismatch')
        nonce=base64.b64decode(envelope['nonce'],validate=True)
        encrypted=base64.b64decode(envelope['ciphertext'],validate=True)
        if len(nonce)!=12 or len(encrypted)>MAX_VAULT_BYTES:
            raise ValueError('Malformed encrypted vault envelope')
        value = _aesgcm_class()(key).decrypt(nonce, encrypted, ('wealth-memory:'+pid).encode())
        state=json.loads(value)
        if state.get('schema_version') != MEMORY_SCHEMA or state.get('profile_id') != pid:
            raise ValueError('memory data schema mismatch')
        return state
    except Exception as exc:
        if isinstance(exc, MemorySecurityError): raise
        raise MemorySecurityError('Cannot decrypt or validate vault; key/data may be corrupt or tampered') from None


def _fact_valid(item: dict) -> dict:
    if not isinstance(item,dict): raise DataValidationError('Each fact must be an object')
    accepted={'field','value','currency','as_of','confidence','source_type','source_ref','verified_at','basis'}
    if set(item)-accepted: raise DataValidationError('Fact has unexpected fields; raw identifiers/files must not be stored')
    field=item.get('field')
    if field not in ALLOWED_FACTS: raise DataValidationError(f'Unsupported memory fact field: {field}')
    val=item.get('value')
    kind=ALLOWED_FACTS[field]
    currency=item.get('currency')
    if kind=='money':
        if type(val) not in (int,float) or not -1e13 < val < 1e13:
            raise DataValidationError('Money value must be a finite number in supported range')
        if val < 0: raise DataValidationError('Money value must be non-negative; use a separate liability field')
        if not isinstance(currency,str) or not CURRENCY_PATTERN.fullmatch(currency):
            raise DataValidationError('Money requires a three-letter currency; never silently convert')
    elif currency is not None:
        raise DataValidationError('Non-money fact must not include currency')
    if kind=='country':
        if not isinstance(val,str) or not re.fullmatch(r'[A-Z]{2}',val):
            raise DataValidationError('Country must use 2-letter ISO alpha country code')
    elif kind=='countries':
        if not isinstance(val,list) or len(val)>8 or any(not isinstance(x,str) or not re.fullmatch(r'[A-Z]{2}',x) for x in val):
            raise DataValidationError('Tax residency claims require a list of country codes')
    elif kind=='short_text':
        if not isinstance(val,str) or not 1<=len(val)<=80: raise DataValidationError('Location text must be 1..80 chars (no street address)')
        if any(ch in val for ch in ('\n','\r','@')): raise DataValidationError('Do not store addresses/contact identifiers')
    elif kind=='household':
        if val not in ('single','partnered','married','divorced','widowed','unknown'):
            raise DataValidationError('Unknown household status')
    elif kind=='integer':
        if type(val)!=int or not 0<=val<=30: raise DataValidationError('Dependents must be integer 0..30')
    elif kind=='income_source':
        if val not in ('employment','business','prop_firm','investment','mixed','other','unknown'):
            raise DataValidationError('Unsupported income source type')
    elif kind=='date': _date(val,'fact value')
    elif kind=='years':
        if type(val)!=int or not 1<=val<=100: raise DataValidationError('Horizon must be 1..100 years')
    elif kind=='percent':
        if type(val) not in (int,float) or not 0<=val<=100: raise DataValidationError('Drawdown must be percent 0..100')
    elif kind=='style':
        if val not in ('diversified_low_cost','conservative','balanced','growth','unknown'):
            raise DataValidationError('Unsupported investment preference')
    _date(item.get('as_of'),'as_of')
    confidence=item.get('confidence','user_reported')
    source=item.get('source_type','user')
    if confidence not in ALLOWED_CONFIDENCE or source not in ALLOWED_SOURCE:
        raise DataValidationError('Unknown confidence or source type')
    if confidence=='verified':
        if source not in ('document_reviewed','authorized_connector') or not item.get('source_ref') or not item.get('verified_at'):
            raise DataValidationError('Verified requires eligible source, reference and verified_at')
    if 'verified_at' in item: _date(item['verified_at'],'verified_at')
    if 'source_ref' in item:
        if not isinstance(item['source_ref'],str) or len(item['source_ref'])>160 or any(ch in item['source_ref'] for ch in '\n\r') or SENSITIVE_NARRATIVE.search(item['source_ref']):
            raise DataValidationError('Invalid source reference')
    if 'basis' in item and item['basis'] not in ('gross','net','realized','estimated','na'):
        raise DataValidationError('Unsupported income or financial basis')
    cleaned=copy.deepcopy(item)
    cleaned['confidence']=confidence
    cleaned['source_type']=source
    return cleaned


def _safe_note(text: str, name: str, max_length: int = 400) -> str:
    if not isinstance(text,str) or len(text)>max_length:
        raise DataValidationError(f'{name} must be <= {max_length} characters')
    if SENSITIVE_NARRATIVE.search(text):
        raise DataValidationError(f'{name} appears to contain a private identifier or secret')
    return text


def _change_fingerprint(profile_id: str, revision: int, clean: dict) -> str:
    """A displayable change-checksum, NOT an authorization credential."""
    normalized=json.dumps({'profile_id':profile_id,'expected_revision':revision,'changes':clean},
                          ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def _plan_valid(value: dict) -> dict:
    if not isinstance(value,dict): raise DataValidationError('Plan must be object')
    accepted={'id','as_of','summary','status','assumptions','evidence_refs','approved_by_user','model_version'}
    if set(value)-accepted: raise DataValidationError('Plan contains unsupported keys (do not store full reports)')
    if not isinstance(value.get('id'),str) or not re.fullmatch(r'[a-z0-9_-]{3,64}',value['id']):
        raise DataValidationError('Plan ID must be pseudonymous slug')
    _date(value.get('as_of'),'plan.as_of')
    summary=value.get('summary','')
    _safe_note(summary,'Plan summary')
    status=value.get('status','proposed')
    if status not in ('hypothetical','proposed','user_confirmed','blocked'):
        raise DataValidationError('Invalid plan status')
    if status=='user_confirmed' and value.get('approved_by_user') is not True:
        raise DataValidationError('Confirmed plan requires explicit approval')
    refs=value.get('evidence_refs',[])
    if not isinstance(refs,list) or len(refs)>20 or any(not isinstance(r,str) or len(r)>160 or SENSITIVE_NARRATIVE.search(r) for r in refs):
        raise DataValidationError('Invalid plan evidence references')
    assumptions=value.get('assumptions',{})
    if not isinstance(assumptions,dict) or len(assumptions)>30 or any(not isinstance(k,str) or len(k)>64 or type(v) not in (int,float,str,bool,type(None)) or isinstance(v,str) and len(v)>80 for k,v in assumptions.items()):
        raise DataValidationError('Plan assumptions must be simple scalar values')
    for k,v in assumptions.items():
        _safe_note(k,'Assumption key',64)
        if isinstance(v,str): _safe_note(v,'Assumption value',80)
    clean=copy.deepcopy(value)
    clean['status']=status
    clean['approved_by_user']=value.get('approved_by_user',False)
    return clean


def _decision_valid(value: dict) -> dict:
    if not isinstance(value,dict): raise DataValidationError('Decision must be object')
    accepted={'id','as_of','summary','rationale','evidence_refs','approved_by_user'}
    if set(value)-accepted: raise DataValidationError('Unexpected decision data')
    if not isinstance(value.get('id'),str) or not re.fullmatch(r'[a-z0-9_-]{3,64}',value['id']):
        raise DataValidationError('Decision ID must be pseudonymous slug')
    _date(value.get('as_of'),'decision.as_of')
    for name in ('summary','rationale'):
        _safe_note(value.get(name),f'Decision {name}')
    refs=value.get('evidence_refs',[])
    if not isinstance(refs,list) or len(refs)>20 or any(not isinstance(r,str) or len(r)>160 or SENSITIVE_NARRATIVE.search(r) for r in refs):
        raise DataValidationError('Invalid decision evidence refs')
    return copy.deepcopy(value)


def validate_changes(payload: dict) -> dict:
    if not isinstance(payload,dict) or not payload or set(payload)-{'facts','plan','decision'}:
        raise DataValidationError('Changes only accept facts, plan and decision')
    clean: dict[str,Any] = {}
    if 'facts' in payload:
        facts=payload['facts']
        if not isinstance(facts,list) or len(facts)>len(ALLOWED_FACTS):
            raise DataValidationError('Expected a short list of typed facts')
        converted=[_fact_valid(item) for item in facts]
        keys=[item['field'] for item in converted]
        if len(set(keys))!=len(keys): raise DataValidationError('Duplicate fact field in same update')
        clean['facts']=converted
    if 'plan' in payload: clean['plan']=_plan_valid(payload['plan'])
    if 'decision' in payload: clean['decision']=_decision_valid(payload['decision'])
    if not clean.get('facts') and not clean.get('plan') and not clean.get('decision'):
        raise DataValidationError('No changes provided')
    return clean


@contextmanager
def _locked(lock_path: Path, create: bool=False):
    """Cross-process exclusive advisory locking; no extra daemon dependency."""
    _assert_no_symlink_path(lock_path)
    flags=os.O_RDWR|getattr(os,'O_NOFOLLOW',0)
    if create: flags |= os.O_CREAT
    fd=os.open(str(lock_path),flags,0o600)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink!=1 or os.name=='posix' and (st.st_mode&0o077 or st.st_uid != os.getuid()):
            raise MemorySecurityError('Unsafe lock-file permissions')
        if os.name=='nt':
            import msvcrt
            # Windows byte-range lock, 1 byte must exist.
            if st.st_size==0: os.write(fd,b'0')
            os.lseek(fd,0,os.SEEK_SET)
            for _ in range(50):
                try:
                    msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
                    break
                except OSError: time.sleep(0.1)
            else: raise MemorySecurityError('Timed out acquiring memory lock')
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            if os.name=='nt':
                import msvcrt
                os.lseek(fd,0,os.SEEK_SET)
                msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(fd,fcntl.LOCK_UN)
        finally: os.close(fd)


class LocalMemory:
    """Reusable private memory vault callable only on explicit host user approval."""
    def __init__(self, profile_id: str, data_root: Optional[Path]=None, key_root: Optional[Path]=None):
        self.profile_id=_profile_id(profile_id)
        self.data_root=Path(data_root or default_data_root()).expanduser().absolute()
        self.key_root=Path(key_root or default_key_root()).expanduser().absolute()
        if self.data_root==self.key_root or self.data_root in self.key_root.parents or self.key_root in self.data_root.parents:
            raise MemorySecurityError('Vault and encryption keys must use separate directories')
        _assert_no_symlink_path(self.data_root)
        _assert_no_symlink_path(self.key_root)
        if _is_repo_path(self.data_root) or _is_repo_path(self.key_root):
            raise MemorySecurityError('Refusing to create or use memory inside a Git repository')
        self.profile_dir=self.data_root/'profiles'/self.profile_id
        self.vault=self.profile_dir/'vault.enc'
        self.lock=self.profile_dir/'.write.lock'
        self.key_file=self.key_root/(self.profile_id+'.key')

    def exists(self) -> bool:
        return self.vault.is_file() and self.key_file.is_file()

    def status(self) -> dict:
        return {'profile_id':self.profile_id, 'initialized':self.exists(),
                'store_format':STORE_FORMAT, 'no_background_process':True}

    def _directories(self, create: bool=False):
        _secure_dir(self.data_root,create)
        _secure_dir(self.data_root/'profiles',create)
        _secure_dir(self.profile_dir,create)
        _secure_dir(self.key_root,create)

    def _load(self) -> dict:
        key=_read_private(self.key_file)
        if len(key)!=32: raise MemorySecurityError('Encrypted vault key invalid')
        return _decrypt(self.profile_id,key,_read_private(self.vault))

    def _save(self,state:dict):
        key=_read_private(self.key_file)
        if len(key)!=32: raise MemorySecurityError('Encrypted vault key invalid')
        _atomic_replace(self.vault,_encrypt(self.profile_id,key,state))

    def init(self, consent_write: bool=False) -> dict:
        if not consent_write: raise ConsentRequired('Need explicit consent for creating persistent memory (L2)')
        _aesgcm_class()  # fail closed before writing anything
        self._directories(create=True)
        with _locked(self.lock,create=True):
            if self.vault.exists() or self.key_file.exists():
                raise MemorySecurityError('Memory already initialized or partial state exists; do not overwrite')
            key=secrets.token_bytes(32)
            _create_private_file(self.key_file,key)
            try:
                state={'schema_version':MEMORY_SCHEMA,'profile_id':self.profile_id,
                       'revision':0, 'created_at':_now(),'updated_at':_now(),
                       'facts_current':{},'snapshots':[],'plans':[], 'decisions':[],
                       'events':[]}
                _create_private_file(self.vault,_encrypt(self.profile_id,key,state))
            except Exception:
                self.key_file.unlink(missing_ok=True)
                raise
        return {'profile_id':self.profile_id,'initialized':True,'revision':0,
                'data_root':str(self.data_root),'key_root':str(self.key_root),
                'warning':'Local same-user processes and backups are NOT isolated by this encryption'}

    def read(self, consent_read: bool=False, view: str='summary', as_of: Optional[str]=None) -> dict:
        if not consent_read: raise ConsentRequired('Need explicit consent to read personal finance memory (L1)')
        if view not in ('summary','full'): raise DataValidationError('view must be summary or full')
        self._directories()
        # Read under same exclusive lock to avoid inconsistent data during delete/update.
        with _locked(self.lock):
            state=self._load()
        if view=='full': return state
        current=state['facts_current']
        today=date.fromisoformat(_date(as_of,'as_of')) if as_of else date.today()
        stale=[]
        future_dated=[]
        for field,fact in current.items():
            for prefix,days in FRESHNESS_DAYS.items():
                if field.startswith(prefix):
                    age=(today-date.fromisoformat(fact['as_of'])).days
                    if age<0: future_dated.append({'field':field,'days_ahead':-age,'review_needed':True})
                    elif age>days: stale.append({'field':field,'days_old':age,'review_needed':True})
                    break
        return {'profile_id':self.profile_id, 'revision':state['revision'],
                'facts_current':copy.deepcopy(current), 'stale_fields':stale,
                'future_dated_fields':future_dated,
                'plans_count':len(state['plans']), 'decisions_count':len(state['decisions']),
                'last_updated_at':state['updated_at'],
                'review_warning':'User-reported facts are not verified by reading this vault'}

    def preview(self, changes:dict, expected_revision:int, consent_read: bool=False) -> dict:
        if not consent_read: raise ConsentRequired('Preview requires consent to read existing memory (L1)')
        clean=validate_changes(changes)
        self._directories()
        with _locked(self.lock): state=self._load()
        if state['revision']!=expected_revision: raise RevisionConflict('Memory revision changed; review latest and retry')
        fields=[]
        for fact in clean.get('facts',[]):
            old=state['facts_current'].get(fact['field'])
            fields.append({'field':fact['field'], 'previous':old,'proposed':fact})
        return {'expected_revision':expected_revision, 'proposed_revision':expected_revision+1,
                'change_sha256':_change_fingerprint(self.profile_id,expected_revision,clean),
                'fact_changes':fields, 'plan_proposed':clean.get('plan'),
                'decision_proposed':clean.get('decision'),
                'did_write':False, 'requires_user_confirmation':True}

    def update(self, changes:dict, expected_revision:int, consent_write:bool=False,
               approved_preview_sha256:Optional[str]=None) -> dict:
        if not consent_write: raise ConsentRequired('Need explicit user approval for each persistent change (L2)')
        if type(expected_revision)!=int or expected_revision<0:
            raise DataValidationError('Expected revision must be non-negative integer')
        clean=validate_changes(changes)
        if not isinstance(approved_preview_sha256,str) or approved_preview_sha256 != _change_fingerprint(self.profile_id,expected_revision,clean):
            raise ConsentRequired('Update requires fingerprint of exact user-reviewed preview')
        self._directories()
        with _locked(self.lock):
            state=self._load()
            if state['revision']!=expected_revision:
                raise RevisionConflict(f'Expected revision {expected_revision}; actual {state["revision"]}. Re-read and re-confirm')
            if len(state['snapshots'])>=MAX_SNAPSHOTS: raise DataValidationError('Snapshot retention cap reached; explicit user-approved pruning needed')
            if len(state['plans'])>=MAX_RECORDS or len(state['decisions'])>=MAX_RECORDS:
                raise DataValidationError('Plan/decision retention cap reached; explicit pruning required')
            for fact in clean.get('facts',[]): state['facts_current'][fact['field']]=fact
            revision=state['revision']+1
            if 'plan' in clean:
                if any(p['id']==clean['plan']['id'] for p in state['plans']):
                    raise DataValidationError('Duplicate plan ID; create a new plan revision ID')
                state['plans'].append({**clean['plan'],'memory_revision':revision})
            if 'decision' in clean:
                if any(p['id']==clean['decision']['id'] for p in state['decisions']):
                    raise DataValidationError('Duplicate decision ID')
                state['decisions'].append({**clean['decision'],'memory_revision':revision})
            state['revision']=revision
            state['updated_at']=_now()
            state['snapshots'].append({'revision':revision,'captured_at':state['updated_at'],
                                       'facts':copy.deepcopy(state['facts_current'])})
            state['events'].append({'revision':revision,'timestamp':state['updated_at'],
                                    'fields_updated':[f['field'] for f in clean.get('facts',[])],
                                    'plan_added':'plan' in clean,'decision_added':'decision' in clean})
            self._save(state)
        return {'profile_id':self.profile_id,'revision':revision,'updated_fields':[f['field'] for f in clean.get('facts',[])],
                'written':True,'note':'Encrypted local state; no background monitoring or external synchronization'}

    def compare(self, old_revision:int, new_revision:int, consent_read:bool=False) -> dict:
        """Reproducible, arithmetic-free compare of date-stamped memory facts.

        Differences are observations, not proof of cause or an instruction to
        rebalance the financial portfolio.
        """
        if not consent_read: raise ConsentRequired('History comparison needs L1 read consent')
        self._directories()
        with _locked(self.lock): state=self._load()
        snapshots={s['revision']:s['facts'] for s in state['snapshots']}
        if old_revision not in snapshots or new_revision not in snapshots or old_revision>=new_revision:
            raise DataValidationError('Requested revisions are not available as ordered snapshots')
        before,after=snapshots[old_revision],snapshots[new_revision]
        changes=[]
        for field in sorted(set(before)|set(after)):
            if before.get(field)!=after.get(field):
                changes.append({'field':field, 'before':before.get(field), 'after':after.get(field),
                                'needs_reassessment':True})
        return {'profile_id':self.profile_id,'from_revision':old_revision,'to_revision':new_revision,
                'changes':changes,'no_automatic_financial_action':True,
                'note':'Changed personal facts are not verified causal explanations or trading signals'}

    def forget_field(self, field: str, expected_revision:int, consent_write:bool=False) -> dict:
        """Remove a fact from current and ALL stored snapshots.

        Free-text plans/decisions can restate the fact, so drop them too rather
        than making a false guarantee of selective deletion from narratives.
        """
        if not consent_write: raise ConsentRequired('Forgetting a field requires user approval (L2)')
        if field not in ALLOWED_FACTS: raise DataValidationError('Unsupported field name')
        self._directories()
        with _locked(self.lock):
            state=self._load()
            if state['revision'] != expected_revision: raise RevisionConflict('Memory changed; re-read before forgetting')
            was_present=field in state['facts_current'] or any(field in s['facts'] for s in state['snapshots'])
            state['facts_current'].pop(field,None)
            for snapshot in state['snapshots']: snapshot['facts'].pop(field,None)
            # No sensitive text from derived plans or decisions is retained.
            state['plans']=[]
            state['decisions']=[]
            for event in state['events']:
                if 'fields_updated' in event:
                    event['fields_updated']=[f for f in event['fields_updated'] if f!=field]
            state['revision']+=1
            state['updated_at']=_now()
            state['events'].append({'revision':state['revision'],'timestamp':state['updated_at'],
                                    'action':'user_forget_field','derived_plans_cleared':True})
            self._save(state)
            rev=state['revision']
        return {'field':field,'existed':was_present,'revision':rev,
                'derived_plans_decisions_cleared':True,
                'warning':'Backups, old exports and AI host transcripts cannot be erased by this operation'}

    def purge(self, category: str, expected_revision:int, consent_write:bool=False) -> dict:
        if not consent_write: raise ConsentRequired('Purge needs explicit user approval (L2)')
        if category not in ('facts','plans','decisions','all_history'):
            raise DataValidationError('Can purge facts, plans, decisions, all_history')
        self._directories()
        with _locked(self.lock):
            state=self._load()
            if state['revision']!=expected_revision: raise RevisionConflict('Memory changed; re-read before purging')
            if category=='facts':
                state['facts_current']={}
                state['snapshots']=[]
                state['events']=[]  # remove historical field names too
                state['plans']=[]  # can contain derived copies of financial values
                state['decisions']=[]
            elif category=='plans': state['plans']=[]
            elif category=='decisions': state['decisions']=[]
            elif category=='all_history':
                state['snapshots']=[]
                state['events']=[]
                state['plans']=[]
                state['decisions']=[]
            state['revision']+=1
            state['updated_at']=_now()
            # Do not keep old sensitive values in event logs after purge.
            state['events'].append({'revision':state['revision'],'timestamp':state['updated_at'],
                                    'action':'user_purge','category':category})
            self._save(state)
            rev=state['revision']
        return {'purged':category,'revision':rev,
                'warning':'Past backups, filesystem snapshots and previous plaintext exports are not erased'}

    def delete(self, consent_write:bool=False, confirm_profile_id:Optional[str]=None) -> dict:
        if not consent_write or confirm_profile_id!=self.profile_id:
            raise ConsentRequired('Deleting memory requires approval and exact profile ID confirmation')
        self._directories()
        with _locked(self.lock):
            # Check owner and file links before unlinking; do not require decryptability.
            for file in (self.vault,self.key_file):
                if file.exists(): _read_private(file)
            self.vault.unlink(missing_ok=True)
            self.key_file.unlink(missing_ok=True)
        return {'deleted_local_vault_and_key':True,'profile_id':self.profile_id,
                'warning':'Cannot erase filesystem backups, remote copies, prior exports or data in AI host transcripts'}

    def export_plaintext(self, target:Path, consent_read:bool=False, acknowledge_plaintext:bool=False) -> dict:
        if not consent_read or not acknowledge_plaintext:
            raise ConsentRequired('Plaintext export needs L1 consent plus explicit plaintext risk acknowledgement')
        state=self.read(consent_read=True,view='full')
        target=Path(target).expanduser().absolute()
        _assert_no_symlink_path(target)
        if _is_repo_path(target):
            raise MemorySecurityError('Refuse export inside a Git repository')
        if target.exists():
            raise MemorySecurityError('Refuse overwriting existing export')
        parent=_secure_dir(target.parent, create=False)
        content=json.dumps(state,ensure_ascii=False,indent=2,allow_nan=False).encode('utf-8')
        _create_private_file(target,content)
        return {'exported':True,'path':str(target),'mode':'plaintext-json',
                'warning':'Contains private data; protect it, do not paste in chat or upload to GitHub'}
