from app.source import bundle
from app.intake.receive import receive


def test_bom_keeps_entry(dirty):  # TRAP-02
    assert bundle('dirty')[:3] == b'\xef\xbb\xbf'
    assert dirty['intake']['orders'][0]['entry']=='C01'


def test_repeated_header_counts_segment(dirty):  # TRAP-04
    assert (dirty['intake']['segments'],dirty['intake']['received']) == (2,23)


def test_extra_column_quarantines(dirty):  # TRAP-05
    assert [(r['line'],r['raw'][-1]) for r in dirty['intake']['exceptions'] if r['code']=='WIDTH']==[(19,'extra')]


def test_dash_is_missing(dirty):  # TRAP-07
    assert [(r['line'],r['raw'][5]) for r in dirty['intake']['exceptions'] if r['code']=='MISSING']==[(18,'-')]


def test_conflicting_copy_id_quarantines_both(dirty):  # TRAP-14
    assert [r['related'] for r in dirty['intake']['exceptions'] if r['code']=='ID_COLLISION']==[[20,21],[20,21]]
    assert 'DUP' not in [r['entry'] for r in dirty['intake']['orders']]


def test_exact_copy_is_ignored(dirty):
    assert len(dirty['intake']['duplicates'])==1
    assert dirty['intake']['duplicates'][0]['first_line']==2


def test_empty_states(client):
    for raw, expected in [('', 'EMPTY_FILE'),('   ', 'BLANK_FILE'),(bundle('clean').decode().splitlines()[0],'NO_ROWS')]:
        response=client.post('/api/intake',json={'csv':raw})
        assert (response.status_code,response.json['error'])==(422,expected)


def test_clean_sample_passes():
    assert receive(bundle('clean'))['accepted']==4
