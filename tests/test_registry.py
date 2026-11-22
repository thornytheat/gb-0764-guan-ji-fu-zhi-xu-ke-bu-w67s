from app.registry.catalog import load_register


def row(dirty, name):
    return next(item for item in dirty['registry']['records'] if item['entry']==name)


def test_literal_org_codes_keep_zeroes(dirty):  # TRAP-08
    assert row(dirty,'C01')['org']['code']=='00123'
    assert row(dirty,'C09')['reasons'][0]['code']=='UNKNOWN_ORG'


def test_retired_issn_resolves(dirty):
    c=row(dirty,'C01')
    assert (c['issn'],c['journal']['issn'],c['journal']['pages'])==('0412-2023','2049-3630',[3,20])


def test_alias_resolves_to_same_org(dirty):
    assert (row(dirty,'C02')['institution'], row(dirty,'C02')['org']['code'])==('NORTH','00123')


def test_unknown_journal_leaves_source(dirty):
    c=row(dirty,'C08')
    assert (c['line'],c['issn'],c['reasons'][0]['code'])==(11,'9999-9999','UNKNOWN_ISSN')


def test_revocation_needs_no_journal(dirty):
    c=row(dirty,'R01')
    assert c['journal'] is None and c['reasons']==[]


def test_registry_counts(client):
    result=client.get('/api/registry').json
    assert (result['old_issn'],result['identified'],result['unresolved'])==(1,15,2)


def test_catalog_lookup_identity():
    register=load_register()
    assert register['issn']['0412-2023'] is register['issn']['2049-3630']
