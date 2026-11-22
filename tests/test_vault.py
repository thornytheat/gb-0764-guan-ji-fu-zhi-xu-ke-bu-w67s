from concurrent.futures import ThreadPoolExecutor
import sqlite3
import pytest
from app.main import create_app
from app.source import bundle
from app.vault.record import deposit,index


def test_return_unchanged_manifest(client):
    first=client.post('/api/volumes',json={'sample':'dirty'})
    repeat=client.post('/api/volumes',json={'sample':'dirty'})
    assert (first.status_code,repeat.status_code)==(201,200)
    assert repeat.json==dict(first.json,reused=True)


def test_distinct_catalog_input_keys(client):
    rst=[client.post('/api/volumes',json={'sample':name}).json for name in ('dirty','clean')]
    assert rst[0]['authority_sha256']==rst[1]['authority_sha256']
    assert rst[0]['run_id']!=rst[1]['run_id']


def test_restart_keeps_evidence(desk,client):
    path='/api/volumes/'+client.post('/api/volumes',json={'sample':'dirty'}).json['run_id']
    assert create_app(desk.vault.path).test_client().get(path).json==client.get(path).json


def test_constraint_error_rolls_back(desk):
    with desk.vault.session() as conn:
        conn.execute("CREATE TRIGGER fail BEFORE INSERT ON volumes BEGIN SELECT RAISE(ABORT,'injected');END")
    with pytest.raises(sqlite3.IntegrityError):
        deposit(desk.vault,bundle('dirty'))
    assert index(desk.vault)==[]


def test_concurrent_writers_commit_once(desk):
    with ThreadPoolExecutor(5) as pool:
        results=list(pool.map(lambda _:deposit(desk.vault,bundle('dirty')),range(10)))
    assert sum(not item['reused'] for item in results)==1
    assert len(index(desk.vault))==1


def test_bad_submit_does_not_create_volume(client):
    assert client.post('/api/volumes',json={'csv':'malformed','sample':'dirty'}).json['error']=='BAD_PAYLOAD'
    assert client.get('/api/volumes').json=={'volumes':[]}
