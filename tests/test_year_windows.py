from app.licenses.decide import decide
from app.registry.catalog import load_register


def test_terms_expire_at_year_turn(dirty):
    ref=dirty['licenses']['verdicts'][0]
    terms=load_register()['authority']['terms']
    result=decide([dict(ref,received='2026-12-31'),dict(ref,received='2027-01-01')],terms)['verdicts']
    assert result[0]['license']['id']=='NORTH-2'
    assert result[1]['ruling']=='NO_LICENSE'
