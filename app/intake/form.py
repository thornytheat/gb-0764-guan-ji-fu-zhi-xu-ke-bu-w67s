from datetime import date
import re

from app.intake.spec import SENTINELS

PAGE_SYNTAX = re.compile(r'[1-9][0-9]{0,6}(?:-[1-9][0-9]{0,6})?(?:\s*;\s*[1-9][0-9]{0,6}(?:-[1-9][0-9]{0,6})?)*')


def order(line, row):
    fields = ['entry','action','received','institution']
    fields += ['issn','pages'] if row['action']=='copy' else ['target']
    if any(not row[key] or row[key] in SENTINELS for key in fields):
        raise ValueError('MISSING')
    try:
        received = date.fromisoformat(row['received']).isoformat()
        if received != row['received']:
            raise ValueError
        if row['action'] == 'copy':
            if row['target'] or len(row['pages']) > 512 or not PAGE_SYNTAX.fullmatch(row['pages']):
                raise ValueError
            for span in row['pages'].split(';'):
                ends = [int(number) for number in span.split('-')]
                if ends[0] > ends[-1]:
                    raise ValueError
        elif row['action'] != 'cancel' or row['issn'] or row['pages']:
            raise ValueError
    except ValueError as exc:
        raise ValueError('INVALID') from exc
    return dict(row, line=line)
