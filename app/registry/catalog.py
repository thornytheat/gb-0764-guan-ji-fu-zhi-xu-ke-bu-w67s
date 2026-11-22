from hashlib import sha256
import json

from app.settings import CATALOG
from .rules import check_authority, find_conflicts


def compile_register(authority, digest):
    issn, orgs = check_authority(authority)
    return {'authority':authority,'issn':issn,'institutions':orgs,
            'conflicts':find_conflicts(issn),'sha256':digest}


def load_register():
    raw = (CATALOG / 'authority.json').read_bytes()
    return compile_register(json.loads(raw), sha256(raw).hexdigest())
