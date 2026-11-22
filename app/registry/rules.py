from datetime import date


def names(rows, canonical, aliases):
    index = {}
    for row in rows:
        for key in [row[canonical], *row[aliases]]:
            if not key or key in index:
                raise ValueError(f'登记键重复或为空: {key}')
            index[key] = row
    return index


def iso_day(value):
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def claim(entry):
    if isinstance(entry, str):
        return {'key': entry, 'from': None, 'until': None}
    if not isinstance(entry, dict):
        raise ValueError(f'刊号沿革登记无效: {entry}')
    key, start, end = entry.get('key'), entry.get('from'), entry.get('until')
    if any(not iso_day(value) for value in (start, end) if value is not None):
        raise ValueError(f'刊号沿革日期无效: {key}')
    if start and end and not start < end:
        raise ValueError(f'刊号沿革有效期无效: {key}')
    return {'key': key, 'from': start, 'until': end}


def journal_index(rows):
    index = {}
    for row in rows:
        canonical = row['issn']
        previous = [claim(entry) for entry in row['previous']]
        keys = [canonical, *[entry['key'] for entry in previous]]
        if not all(keys) or len(set(keys)) != len(keys) or canonical in index:
            raise ValueError(f'登记键重复或为空: {canonical}')
        index[canonical] = [{'journal': row, 'key': canonical, 'from': None, 'until': None, 'current': True}]
        for entry in previous:
            index.setdefault(entry['key'], []).append(dict(entry, journal=row, current=False))
    for key, claims in index.items():
        legacy = [entry for entry in claims if not entry['current']]
        if legacy and len(claims) > 1 and any(entry['current'] for entry in claims):
            raise ValueError(f'登记键重复或为空: {key}')
        if len(legacy) > 1 and all(entry['from'] is None and entry['until'] is None for entry in legacy):
            raise ValueError(f'登记键重复或为空: {key}')
    return index


def overlaps(first, second):
    return (first['from'] is None or second['until'] is None or first['from'] < second['until']) and (
        second['from'] is None or first['until'] is None or second['from'] < first['until'])


def find_conflicts(index):
    conflicts = []
    for key in sorted(index):
        claims = [entry for entry in index[key] if not entry['current']]
        involved = set()
        for i, first in enumerate(claims):
            for second in claims[i+1:]:
                if overlaps(first, second):
                    involved.update((id(first), id(second)))
        if involved:
            conflicts.append({'key': key, 'claims': [
                {'journal': entry['journal']['issn'], 'from': entry['from'], 'until': entry['until']}
                for entry in claims if id(entry) in involved]})
    return conflicts


def check_authority(authority):
    journals = journal_index(authority['journals'])
    institutions = names(authority['institutions'],'code','aliases')
    groups = {group for row in authority['institutions'] for group in row['groups']}
    for row in authority['journals']:
        first,last = row['pages']
        if type(first) is not int or type(last) is not int or not 1 <= first <= last:
            raise ValueError('刊物页界无效')
    if any(type(value) is not int or value < 0 for value in authority['pools'].values()):
        raise ValueError('额度池配置无效')
    versions = set()
    for term in authority['terms']:
        start,end = [date.fromisoformat(term[key]).isoformat() for key in ('from','until')]
        org = institutions.get(term['subject'])
        scopes = {'institution':org is not None and org['code']==term['subject'],
                  'consortium':term['subject'] in groups,'public':term['subject']=='*'}
        claims = journals.get(term['issn'])
        current = next((entry['journal'] for entry in claims or [] if entry['current']), None)
        if not (start == term['from'] < term['until'] == end and scopes.get(term['scope'])
                and current and current['issn']==term['issn'] and term['pool'] in authority['pools']
                and type(term['revision']) is int and term['revision']>=1 and term['id'] not in versions):
            raise ValueError(f"条款配置无效: {term['id']}")
        versions.add(term['id'])
    return journals,institutions
