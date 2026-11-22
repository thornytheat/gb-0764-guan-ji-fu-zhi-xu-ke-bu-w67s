from datetime import datetime, timezone
from hashlib import sha256
import json
from time import perf_counter

from app.problem import DeskError
from app.registry.catalog import load_register
from app.settings import EDITION
from app.workflow import steps


def encode(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def deposit(vault, raw):
    begin = perf_counter()
    register = load_register()
    report = steps(raw,register=register)
    identity = {'source_sha256':sha256(raw).hexdigest(),'authority_sha256':register['sha256'],
                'rule_version':EDITION,'parameters':{'quota_window':'calendar_year','dates':'left_closed_right_open'}}
    run = sha256(encode(identity).encode()).hexdigest()
    manifest = dict(identity,run_id=run,received_at=datetime.now(timezone.utc).isoformat(),
                    elapsed_ms=int(1000*(perf_counter()-begin)), totals={key:report['balance'][key]
                              for key in ('requested','licensed','denied','pending','restored','effective')})
    with vault.session() as conn:
        saved = conn.execute('INSERT INTO volumes VALUES (?,?,?) ON CONFLICT(id) DO NOTHING',
                             (run,encode(manifest),encode(report))).rowcount
        manifest = json.loads(conn.execute('SELECT manifest FROM volumes WHERE id=?',(run,)).fetchone()[0])
    return dict(manifest,reused=not bool(saved))


def volume(vault, run):
    with vault.session() as conn:
        item = conn.execute('SELECT manifest,evidence FROM volumes WHERE id=?',(run,)).fetchone()
    if not item:
        raise DeskError('RUN_UNKNOWN',404)
    return {'manifest':json.loads(item[0]),'stages':json.loads(item[1])}


def index(vault):
    with vault.session() as conn:
        return [json.loads(record[0]) for record in conn.execute('SELECT manifest FROM volumes ORDER BY rowid DESC LIMIT 40')]
