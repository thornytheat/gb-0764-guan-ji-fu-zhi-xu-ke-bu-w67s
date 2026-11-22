from hashlib import sha256
from app.vault.record import encode


def path(client):
    return '/api/volumes/'+client.post('/api/volumes',json={'sample':'dirty'}).json['run_id']


def test_unsigned_draft_blocked(client):
    response=client.get(path(client)+'/export')
    assert (response.status_code,response.json['error'])==(409,'DRAFT_ONLY')


def test_certificate_signature_matches_detached_document(client):
    address=path(client)
    signature=client.post(address+'/stamp').json['imprint']
    reply=client.get(address+'/export')
    assert reply.headers['Content-Disposition'].startswith('attachment;')
    assert reply.json['verified'] and sha256(encode(reply.json['document']).encode()).hexdigest()==signature


def test_stamp_is_immutable_on_repeat(client):
    address=path(client)+'/stamp'
    first=client.post(address).json
    assert client.post(address).json==dict(first,reused=True)


def test_unknown_archive(client):
    result=client.post('/api/volumes/unknown/stamp')
    assert (result.status_code,result.json['error'])==(404,'RUN_UNKNOWN')


def test_evidence_contains_old_orders_and_reversals(client):
    address=path(client)
    client.post(address+'/stamp')
    doc=client.get(address+'/export').json['document']
    assert doc['requests'][0]['licensed']==6 and doc['revocations'][0]['restored']==6
    assert len(doc['isolated'])==5


def test_reveals_tampered_certificate(client,desk):
    address=path(client)
    client.post(address+'/stamp')
    with desk.vault.session() as conn:
        conn.execute("UPDATE slips SET body='{}'")
    assert client.get(address+'/export').json['verified'] is False
