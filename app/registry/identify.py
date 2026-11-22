from app.problem import MESSAGES


def covers(entry, day):
    return (entry['from'] is None or entry['from'] <= day) and (entry['until'] is None or day < entry['until'])


def recognize(key, day, index):
    matched = [entry for entry in index.get(key, []) if entry['current'] or covers(entry, day)]
    if len(matched) == 1:
        entry = matched[0]
        window = None if entry['current'] or (entry['from'] is None and entry['until'] is None) else {
            'from': entry['from'], 'until': entry['until']}
        basis = {'key': key, 'journal': entry['journal']['issn'],
                 'via': 'current' if entry['current'] else 'legacy', 'window': window}
        return entry['journal'], basis, None
    if not matched:
        return None, {'key': key, 'journal': None, 'via': None, 'window': None, 'candidates': []}, 'UNKNOWN_ISSN'
    return None, {'key': key, 'journal': None, 'via': 'legacy', 'window': None,
                  'candidates': sorted({entry['journal']['issn'] for entry in matched})}, 'ISSN_OVERLAP'


def identify(rows, register):
    resolved = []
    for row in rows:
        org = register['institutions'].get(row['institution'])
        journal = basis = None
        reasons = []
        if org is None:
            reasons.append('UNKNOWN_ORG')
        if row['action'] == 'copy':
            journal, basis, code = recognize(row['issn'].upper(), row['received'], register['issn'])
            if code:
                reasons.append(code)
        resolved.append(dict(row, org=org, journal=journal, basis=basis,
                             reasons=[{'code':code,'note':MESSAGES[code]} for code in reasons]))
    return {'records':resolved,'identified':sum(not r['reasons'] for r in resolved),
            'unresolved':sum(bool(r['reasons']) for r in resolved),
            'old_issn':sum(bool(r['journal'] and r['issn'].upper()!=r['journal']['issn']) for r in resolved),
            'issn_overlap':sum(any(reason['code']=='ISSN_OVERLAP' for reason in r['reasons']) for r in resolved),
            'conflicts':register.get('conflicts',[])}
