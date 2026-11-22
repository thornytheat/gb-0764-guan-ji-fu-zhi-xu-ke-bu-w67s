from hashlib import sha256
import json

from app.problem import DeskError
from app.vault.record import encode, volume


def stamp(vault, run):
    report = volume(vault,run)
    stages = report['stages']
    document = {'document':'馆际复制签发凭证','manifest':report['manifest'],
                'accounting':stages['balance'],'requests':stages['pages']['copies'],
                'revocations':stages['pages']['reversals'],'isolated':stages['intake']['exceptions'],
                'suppressions':stages['intake']['duplicates'],'resolutions':stages['licenses']['verdicts']}
    body = encode(document)
    imprint = sha256(body.encode()).hexdigest()
    with vault.session() as conn:
        new = conn.execute('INSERT INTO slips VALUES (?,?,?) ON CONFLICT(id) DO NOTHING',(run,imprint,body)).rowcount
        signed = conn.execute('SELECT digest FROM slips WHERE id=?',(run,)).fetchone()[0]
    return {'run_id':run,'imprint':signed,'reused':not bool(new)}


def certificate(vault, run):
    volume(vault,run)
    with vault.session() as conn:
        record = conn.execute('SELECT digest,body FROM slips WHERE id=?',(run,)).fetchone()
    if record is None:
        raise DeskError('DRAFT_ONLY',409)
    fingerprint, body = record
    return {'imprint':fingerprint,'verified':sha256(body.encode()).hexdigest()==fingerprint,'document':json.loads(body)}
