from app.problem import MESSAGES


def identify(rows, register):
    resolved = []
    for row in rows:
        org = register['institutions'].get(row['institution'])
        journal = register['issn'].get(row['issn'].upper()) if row['action']=='copy' else None
        reasons = []
        if org is None:
            reasons.append('UNKNOWN_ORG')
        if journal is None and row['action']=='copy':
            reasons.append('UNKNOWN_ISSN')
        resolved.append(dict(row, org=org, journal=journal,
                             reasons=[{'code':code,'note':MESSAGES[code]} for code in reasons]))
    return {'records':resolved,'identified':sum(not r['reasons'] for r in resolved),
            'unresolved':sum(bool(r['reasons']) for r in resolved),
            'old_issn':sum(bool(r['journal'] and r['issn'].upper()!=r['journal']['issn']) for r in resolved)}
