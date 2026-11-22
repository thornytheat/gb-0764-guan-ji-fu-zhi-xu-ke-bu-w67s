from hashlib import sha256
import json

from app.settings import CATALOG
from .rules import check_authority


def load_register():
    raw = (CATALOG / 'authority.json').read_bytes()
    authority = json.loads(raw)
    issn, orgs = check_authority(authority)
    return {'authority':authority,'issn':issn,'institutions':orgs,'sha256':sha256(raw).hexdigest()}
