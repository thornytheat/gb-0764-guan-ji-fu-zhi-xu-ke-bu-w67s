from app.intake.receive import receive


def test_reordered_gb18030_cancellation_retains_id():
    source = 'institution,entry,received,target,issn,pages,action\n00123,撤销甲,2026-04-01,复本乙,,,cancel\n'
    result=receive(source.encode('gb18030'))['orders'][0]
    assert (result['entry'],result['target'],result['institution'])==('撤销甲','复本乙','00123')
