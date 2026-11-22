from app.licenses.decide import decide
from app.registry.catalog import load_register


def verdict(dirty, name):
    return next(item for item in dirty['licenses']['verdicts'] if item['entry']==name)


def test_special_beats_public_high_revision(dirty):  # TRAP-19
    terms=load_register()['authority']['terms']
    result=decide(dirty['registry']['records'],list(reversed(terms)))
    assert result==dirty['licenses']
    assert verdict(dirty,'C01')['license']['id']=='NORTH-2'


def test_closed_at_valid_until(dirty):  # TRAP-23
    c=verdict(dirty,'C05')
    assert c['candidates']==['NET-1','OPEN-1'] and c['license']['id']=='NET-1'


def test_overlapping_versions_and_tie(dirty):  # TRAP-25
    assert verdict(dirty,'C04')['ruling']=='VERSION_TIE'
    assert {'PORT-A','PORT-B'} <= set(verdict(dirty,'C04')['candidates'])
    assert {'NORTH-1','NORTH-2'} <= set(verdict(dirty,'C01')['candidates'])


def test_eligible_open_on_first_day(dirty):
    row=dict(verdict(dirty,'C01'), received='2026-11-01')
    terms=load_register()['authority']['terms']
    assert decide([row],terms)['verdicts'][0]['license']['id']=='NORTH-2'


def test_no_consortium_membership(dirty):
    assert verdict(dirty,'C06')['ruling']=='NO_LICENSE'


def test_unknown_metadata_not_treated_as_denial(dirty):
    c=verdict(dirty,'C08')
    assert (c['ruling'],c['candidates'])==('UNKNOWN_ISSN',[])
