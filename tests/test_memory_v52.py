"""Offline security/privacy and two-session acceptance tests for opt-in local memory."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills'/'personal-finance-planner'
sys.path.insert(0,str(SKILL/'lib'))
from wealth_core.local_memory import (LocalMemory, ConsentRequired, RevisionConflict,
                                      DataValidationError, MemorySecurityError)


def money(field,value,as_of='2026-10-11',currency='CNY',confidence='user_reported'):
    return {'field':field,'value':value,'currency':currency,'as_of':as_of,'confidence':confidence}


def loc(city,date='2026-10-11'):
    return {'field':'residence.city','value':city,'as_of':date,'confidence':'user_reported'}


class MemoryLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.store=LocalMemory('user_001',self.root/'data',self.root/'config'/'keys')

    def init(self):
        self.store.init(consent_write=True)

    def update(self,rev=0,facts=None,**extra):
        payload={'facts':facts or [loc('Shenzhen')],**extra}
        digest=self.store.preview(payload,rev,consent_read=True)['change_sha256']
        return self.store.update(payload,rev,consent_write=True,approved_preview_sha256=digest)

    def test_no_files_without_user_consent(self):
        self.assertFalse((self.root/'data').exists())
        self.assertEqual(self.store.status()['initialized'],False)
        with self.assertRaises(ConsentRequired): self.store.init()
        with self.assertRaises(ConsentRequired): self.store.read()
        with self.assertRaises(ConsentRequired): self.store.update({'facts':[loc('Shenzhen')]},0)
        self.assertFalse((self.root/'data').exists())

    def test_create_encrypted_file_and_separate_key(self):
        self.init()
        self.update(facts=[money('income.monthly_net_realized',20000),loc('Shenzhen')])
        encrypted=self.store.vault.read_bytes()
        self.assertNotIn(b'Shenzhen',encrypted)
        self.assertNotIn(b'20000',encrypted)
        self.assertIn(b'ciphertext',encrypted)
        self.assertEqual(len(self.store.key_file.read_bytes()),32)
        self.assertNotIn(self.store.key_file, self.store.profile_dir.parents)
        if os.name=='posix':
            for path in (self.store.data_root,self.store.key_root,self.store.profile_dir):
                self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o700)
            for path in (self.store.vault,self.store.key_file):
                self.assertEqual(stat.S_IMODE(path.stat().st_mode),0o600)

    def test_read_consent_and_snapshot_revision(self):
        self.init()
        self.update(0,[money('income.monthly_net_realized',20000),loc('Shenzhen')])
        with self.assertRaises(ConsentRequired): self.store.read(view='full')
        observed=self.store.read(consent_read=True,view='summary',as_of='2026-10-11')
        self.assertEqual(observed['revision'],1)
        self.assertEqual(observed['facts_current']['income.monthly_net_realized']['value'],20000)
        self.assertEqual(len(observed['stale_fields']),0)
        entire=self.store.read(consent_read=True,view='full')
        self.assertEqual(len(entire['snapshots']),1)

    def test_two_session_load_and_update_increase_salary(self):
        self.init()
        self.update(0,[money('income.monthly_net_realized',20000),loc('Shenzhen')])
        other_host=LocalMemory('user_001',self.root/'data',self.root/'config'/'keys')
        old=other_host.read(consent_read=True,view='summary')
        self.assertEqual(old['facts_current']['income.monthly_net_realized']['value'],20000)
        revision_two={'facts':[money('income.monthly_net_realized',30000,as_of='2027-01-11')]}
        approved=other_host.preview(revision_two,1,consent_read=True)['change_sha256']
        other_host.update(revision_two,1,consent_write=True,approved_preview_sha256=approved)
        new=self.store.read(consent_read=True,view='full')
        self.assertEqual(new['revision'],2)
        self.assertEqual(new['facts_current']['income.monthly_net_realized']['value'],30000)
        self.assertEqual(new['snapshots'][0]['facts']['income.monthly_net_realized']['value'],20000)
        self.assertEqual(new['snapshots'][1]['facts']['income.monthly_net_realized']['value'],30000)
        self.assertEqual(new['facts_current']['residence.city']['value'],'Shenzhen')

    def test_compare_two_months_reports_observed_changes_without_autotrade(self):
        self.init()
        self.update(0,[money('income.monthly_net_realized',20000),loc('Shenzhen')])
        self.update(1,[money('income.monthly_net_realized',30000,as_of='2027-01-11')])
        with self.assertRaises(ConsentRequired): self.store.compare(1,2)
        diff=self.store.compare(1,2,consent_read=True)
        self.assertTrue(diff['no_automatic_financial_action'])
        self.assertEqual(len(diff['changes']),1)
        self.assertEqual(diff['changes'][0]['before']['value'],20000)
        self.assertEqual(diff['changes'][0]['after']['value'],30000)

    def test_preview_requires_read_and_does_not_write(self):
        self.init()
        before=hashlib.sha256(self.store.vault.read_bytes()).hexdigest()
        changes={'facts':[loc('Shanghai')]}
        with self.assertRaises(ConsentRequired): self.store.preview(changes,0)
        preview=self.store.preview(changes,0,consent_read=True)
        self.assertFalse(preview['did_write'])
        self.assertEqual(preview['proposed_revision'],1)
        self.assertEqual(before,hashlib.sha256(self.store.vault.read_bytes()).hexdigest())

    def test_no_stale_cas_writes(self):
        self.init()
        self.update(0)
        with self.assertRaises(RevisionConflict): self.update(0,[loc('Shanghai')])
        self.assertEqual(self.store.read(consent_read=True)['revision'],1)

    def test_user_reported_cannot_claim_verification(self):
        self.init()
        sample=money('income.monthly_net_realized',20000,confidence='verified')
        with self.assertRaises(DataValidationError): self.update(0,[sample])
        sample.update({'source_type':'authorized_connector','source_ref':'connector:receipt-123',
                       'verified_at':'2026-10-11'})
        self.update(0,[sample])

    def test_reject_unknown_identifiers_and_nominal_prop_firm(self):
        self.init()
        for value in ({'facts':[{'field':'bank.account_number','value':'123456','as_of':'2026-10-11'}]},
                      {'facts':[{'field':'prop_firm.nominal_50k','value':50000,'currency':'USD','as_of':'2026-10-11'}]},
                      {'facts':[{'field':'residence.city','value':'person@private.test','as_of':'2026-10-11'}]},
                      {'facts':[{'field':'income.monthly_gross','value':20000,'as_of':'2026-10-11'}]}):
            with self.subTest(value=value),self.assertRaises(DataValidationError):
                self.store.update(value,0,consent_write=True)
        self.assertEqual(self.store.read(consent_read=True)['revision'],0)

    def test_reject_currency_mixing_at_fact_level(self):
        self.init()
        with self.assertRaises(DataValidationError): self.update(0,[money('assets.liquid',10000,currency='USDollars')])
        self.update(0,[money('assets.liquid',10000,currency='USD'),money('income.monthly_net_realized',20000,currency='CNY')])
        observed=self.store.read(consent_read=True)
        self.assertEqual(observed['facts_current']['assets.liquid']['currency'],'USD')
        self.assertEqual(observed['facts_current']['income.monthly_net_realized']['currency'],'CNY')
        self.assertNotIn('total_wealth',observed)

    def test_staleness_warning_does_not_fabricate_facts(self):
        self.init()
        self.update(0,[money('assets.liquid',100000,as_of='2025-01-11'),loc('Shenzhen','2025-01-11')])
        result=self.store.read(consent_read=True,as_of='2026-10-11')
        self.assertEqual({x['field'] for x in result['stale_fields']},{'assets.liquid','residence.city'})
        self.assertEqual(result['facts_current']['assets.liquid']['confidence'],'user_reported')

    def test_corrupt_ciphertext_fails_closed(self):
        self.init()
        content=json.loads(self.store.vault.read_text())
        content['ciphertext']='AAAA'+content['ciphertext'][4:]
        self.store.vault.write_text(json.dumps(content))
        with self.assertRaises(MemorySecurityError): self.store.read(consent_read=True)

    def test_key_missing_fails_closed(self):
        self.init()
        self.store.key_file.unlink()
        with self.assertRaises(MemorySecurityError): self.store.read(consent_read=True)

    def test_disable_cryptography_has_no_plaintext_fallback(self):
        with patch('wealth_core.local_memory._aesgcm_class',side_effect=MemorySecurityError('cryptography missing')):
            with self.assertRaises(MemorySecurityError): self.store.init(consent_write=True)
        self.assertFalse(self.store.exists())

    def test_purge_facts_clears_old_snapshots_and_derived_plans(self):
        self.init()
        plan={'id':'plan_2026','as_of':'2026-10-11','summary':'Salary 20000, 10-year plan','status':'proposed'}
        dec={'id':'choice_a','as_of':'2026-10-11','summary':'Save CNY 20000',
             'rationale':'Based on salary history'}
        self.update(0,[money('income.monthly_net_realized',20000)],plan=plan,decision=dec)
        self.store.purge('facts',1,consent_write=True)
        obj=self.store.read(consent_read=True,view='full')
        self.assertEqual(obj['facts_current'],{})
        self.assertEqual(obj['snapshots'],[])
        self.assertEqual(obj['plans'],[])
        self.assertEqual(obj['decisions'],[])
        self.assertNotIn('20000',json.dumps(obj))

    def test_forget_a_single_field_also_clears_derived_text(self):
        self.init()
        self.update(0,[money('income.monthly_net_realized',20000),loc('Shenzhen')],
                    plan={'id':'plan_2026','as_of':'2026-10-11','summary':'20000 planned investments'})
        out=self.store.forget_field('income.monthly_net_realized',1,consent_write=True)
        self.assertTrue(out['derived_plans_decisions_cleared'])
        data=self.store.read(consent_read=True,view='full')
        self.assertNotIn('income.monthly_net_realized',json.dumps(data))
        self.assertNotIn('20000',json.dumps(data))
        self.assertEqual(data['facts_current']['residence.city']['value'],'Shenzhen')

    def test_delete_needs_explicit_confirmation_and_removes_key(self):
        self.init()
        with self.assertRaises(ConsentRequired): self.store.delete()
        with self.assertRaises(ConsentRequired): self.store.delete(consent_write=True,confirm_profile_id='someone_else')
        result=self.store.delete(consent_write=True,confirm_profile_id='user_001')
        self.assertTrue(result['deleted_local_vault_and_key'])
        self.assertFalse(self.store.vault.exists())
        self.assertFalse(self.store.key_file.exists())
        self.assertIn('backups',result['warning'])

    def test_export_needs_ack_and_cannot_target_git(self):
        self.init()
        self.update()
        with self.assertRaises(ConsentRequired):
            self.store.export_plaintext(self.root/'data'/'user-export.json',consent_read=True)
        # Exports only into a user-prepared 0700 directory.
        export_dir=self.root/'export'; export_dir.mkdir(mode=0o700)
        target=export_dir/'financial.json'
        out=self.store.export_plaintext(target,consent_read=True,acknowledge_plaintext=True)
        self.assertTrue(out['exported'])
        self.assertIn('Shenzhen',target.read_text())
        with self.assertRaises(MemorySecurityError):
            self.store.export_plaintext(target,consent_read=True,acknowledge_plaintext=True)

    def test_reject_git_path(self):
        repo=self.root/'my-project';repo.mkdir();(repo/'.git').mkdir()
        with self.assertRaises(MemorySecurityError):
            LocalMemory('user_001',repo/'data',self.root/'other').init(consent_write=True)

    def test_reject_linked_vault_and_symlink_directory(self):
        self.init()
        alt=self.root/'linked';alt.symlink_to(self.store.profile_dir,target_is_directory=True)
        with self.assertRaises(MemorySecurityError):
            LocalMemory('user_001',alt.parent/'linked'/'some_data',self.root/'other').status()
        self.store.vault.unlink()
        self.store.vault.symlink_to(self.store.key_file)
        with self.assertRaises(MemorySecurityError): self.store.read(consent_read=True)

    def test_pseudonym_prevents_path_traversal(self):
        for pid in ('../parent','../../etc/passwd','Jane Doe','私密姓名','.hidden','john@example.com'):
            with self.subTest(pid=pid), self.assertRaises(DataValidationError):
                LocalMemory(pid,self.root/'data',self.root/'keys')

    def test_plan_must_not_be_marked_approved_without_approval(self):
        self.init()
        plan={'id':'plan_2026','as_of':'2026-10-11','status':'user_confirmed','summary':'draft'}
        with self.assertRaises(DataValidationError):
            self.store.update({'plan':plan},0,consent_write=True)
        plan['approved_by_user']=True
        approved=self.store.preview({'plan':plan},0,consent_read=True)['change_sha256']
        self.store.update({'plan':plan},0,consent_write=True,approved_preview_sha256=approved)

    def test_profile_a_vault_cannot_be_assigned_to_profile_b(self):
        self.init()
        other=LocalMemory('user_002',self.root/'data',self.root/'config'/'keys')
        other.init(consent_write=True)
        # Data cannot decrypt when moved to a different profile even if key were copied.
        other.vault.write_bytes(self.store.vault.read_bytes())
        other.key_file.write_bytes(self.store.key_file.read_bytes())
        with self.assertRaises(MemorySecurityError): other.read(consent_read=True)

    def test_independent_cli_process_shared_memory(self):
        script=SKILL/'scripts/memory_cli.py'
        base=[sys.executable,str(script),'--profile','user_001','--data-dir',str(self.root/'data'),'--keys-dir',str(self.root/'config'/'keys')]
        r=subprocess.run(base+['init','--consent-write'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        payload={'facts':[money('income.monthly_net_realized',20000)]}
        r=subprocess.run(base+['preview','--expected-revision','0','--consent-read','--stdin'],
                         input=json.dumps(payload),capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertFalse(json.loads(r.stdout)['did_write'])
        digest=json.loads(r.stdout)['change_sha256']
        r=subprocess.run(base+['update','--expected-revision','0','--consent-write',
                               '--approved-preview-sha256',digest,'--stdin'],
                         input=json.dumps(payload),capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        r=subprocess.run(base+['read','--consent-read'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['facts_current']['income.monthly_net_realized']['value'],20000)


    def test_change_fingerprint_binds_exact_preview_revision_and_profile(self):
        self.init()
        original={'facts':[money('income.monthly_net_realized',20000)]}
        preview=self.store.preview(original,0,consent_read=True)
        digest=preview['change_sha256']
        self.assertEqual(len(digest),64)
        with self.assertRaises(ConsentRequired):
            self.store.update({'facts':[money('income.monthly_net_realized',21000)]},0,
                              consent_write=True,approved_preview_sha256=digest)
        with self.assertRaises(ConsentRequired):
            self.store.update(original,0,consent_write=True,approved_preview_sha256='0'*64)
        self.assertEqual(self.store.read(consent_read=True)['revision'],0)
        self.store.update(original,0,consent_write=True,approved_preview_sha256=digest)
        with self.assertRaises(RevisionConflict):
            self.store.update(original,0,consent_write=True,approved_preview_sha256=digest)

    def test_cli_requires_preview_fingerprint(self):
        script=SKILL/'scripts/memory_cli.py'
        base=[sys.executable,str(script),'--profile','user_001','--data-dir',str(self.root/'data'),
              '--keys-dir',str(self.root/'config'/'keys')]
        self.assertEqual(subprocess.run(base+['init','--consent-write'],capture_output=True).returncode,0)
        payload=json.dumps({'facts':[loc('Shenzhen')]})
        p=subprocess.run(base+['update','--expected-revision','0','--consent-write','--stdin'],
                         capture_output=True,text=True,input=payload)
        self.assertNotEqual(p.returncode,0)
        self.assertEqual(self.store.read(consent_read=True)['revision'],0)

    def test_future_dated_memory_is_flagged_not_current_verified(self):
        self.init()
        self.update(0,[money('assets.liquid',30000,as_of='2027-01-11')])
        result=self.store.read(consent_read=True,as_of='2026-10-11')
        self.assertEqual(result['future_dated_fields'][0]['field'],'assets.liquid')

    def test_secret_identifiers_rejected_in_free_text(self):
        self.init()
        bad_plans=[{'id':'plan_001','as_of':'2026-10-11','summary':'contact me at user@example.net'},
                   {'id':'plan_002','as_of':'2026-10-11','summary':'password: XYZ'},
                   {'id':'plan_003','as_of':'2026-10-11','assumptions':{'bank_account':'6222021122334455667'}}]
        for plan in bad_plans:
            with self.subTest(plan=plan), self.assertRaises(DataValidationError):
                self.store.update({'plan':plan},0,consent_write=True)
        self.assertEqual(self.store.read(consent_read=True)['revision'],0)

    def test_no_financial_data_committed_to_repo(self):
        # Build tree contains only synthetic examples. Private roots are absent.
        self.assertFalse((ROOT/'private').exists())
        self.assertFalse((ROOT/'user-data').exists())
        self.assertIn('user-data/',(ROOT/'.gitignore').read_text())

if __name__=='__main__': unittest.main()
