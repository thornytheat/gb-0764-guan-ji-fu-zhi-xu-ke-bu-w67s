from copy import deepcopy
from app.register.balance import reconcile


def test_requested_conserved(dirty):
    b=dirty['balance']
    assert b['requested']==b['licensed']+b['denied']+b['pending']==58


def test_quota_reconciles_to_active_copies(dirty):
    b=dirty['balance']
    assert b['effective']==26==sum(value['used'] for value in b['accounts'].values())


def test_pending_sources_separate(dirty):
    reasons=dirty['balance']['reasons']
    assert {k:reasons[k] for k in ('VERSION_TIE','UNKNOWN_ISSN','UNKNOWN_ORG')}=={'VERSION_TIE':4,'UNKNOWN_ISSN':2,'UNKNOWN_ORG':2}


def test_reconciliation_detects_changed_balance(dirty):
    pages=deepcopy(dirty['pages']); pages['accounts']['2026/NORTH']['used']-=1
    result=reconcile(dirty['intake'],pages)
    assert result['source_ok'] and not result['balanced']


def test_rejected_material_is_not_counted_as_pages(dirty):
    assert {'C12','C13','DUP','C14'}.isdisjoint(row['entry'] for row in dirty['balance']['explanations'])
    assert dirty['balance']['source_ok']


def test_clean_balance_api(client):
    b=client.get('/api/balance?sample=clean').json
    assert (b['requested'],b['licensed'],b['denied'],b['pending'])==(12,12,0,0)
