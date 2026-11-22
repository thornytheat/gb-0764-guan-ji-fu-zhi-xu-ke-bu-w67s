import os
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / 'sample_data'
LEDGER = os.environ.get('LICENSE_DB', 'var/licenses.sqlite')
EDITION = 'rights-1.0'
