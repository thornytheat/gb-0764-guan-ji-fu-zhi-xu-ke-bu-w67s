from app.source import bundle


def test_revised_volume_leaves_first_signed_decision_intact(client):
    source=bundle('clean').decode()
    first=client.post('/api/volumes',json={'csv':source}).json
    old='/api/volumes/'+first['run_id']
    signature=client.post(old+'/stamp').json['imprint']
    amended=source+'X1,cancel,2026-12-02,00007,,,C05\n'
    change=client.post('/api/volumes',json={'csv':amended}).json
    assert (first['totals']['effective'],change['totals']['effective'],change['totals']['restored'])==(12,8,4)
    assert client.get(old+'/export').json['imprint']==signature
