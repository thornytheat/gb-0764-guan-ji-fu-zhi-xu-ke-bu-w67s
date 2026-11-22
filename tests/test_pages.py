from app.pagination.spans import normalize, split_limit
from app.pagination.ledger import allocate
from app.registry.catalog import load_register


def copy(dirty, entry):
    return next(row for row in dirty['pages']['copies'] if row['entry']==entry)


def test_page_union_before_debit(dirty):
    c=copy(dirty,'C01')
    assert (c['normalized'],c['granted'],c['outside'])==([[1,9]],[[3,9]],[[1,3]])


def test_page_union_needs_no_per_page_expansion():
    assert normalize('9000000-9999999;1-4;5;3-6')==[[1,7],[9000000,10000000]]


def test_quota_allocates_lowest_pages(dirty):
    c=copy(dirty,'C02')
    assert (c['granted'],c['shortage'])==([[8,12]],[[12,16]])


def test_late_recorded_cancel_restores_historical_order(dirty):
    assert dirty['pages']['reversals'][0]['restored']==6
    assert copy(dirty,'C03')['licensed']==6
    assert copy(dirty,'C01')['licensed']==6


def test_cut_both_article_limits():
    assert split_limit([[1,24]],3,20,2)==([[3,5]],[[1,3],[21,24]],[[5,21]])


def test_duplicate_and_wrong_holder_do_not_credit(dirty):
    assert [r['reason'] for r in dirty['pages']['reversals'][1:]]==['WRONG_ORG','REPEATED_CANCEL','UNKNOWN_TARGET']


def test_cancel_cannot_cross_quota_year(dirty):
    rows=dirty['licenses']['verdicts']
    source=next(row for row in rows if row['entry']=='C01')
    cancel=next(row for row in rows if row['entry']=='R01')
    result=allocate([source,dict(cancel,received='2027-01-01')],load_register()['authority']['pools'])
    assert result['reversals'][0]['reason']=='BOUNDARY'
    assert result['accounts']['2026/NORTH']['used']==6
