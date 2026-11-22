from datetime import date


def names(rows, canonical, aliases):
    index = {}
    for row in rows:
        for key in [row[canonical], *row[aliases]]:
            if not key or key in index:
                raise ValueError(f'登记键重复或为空: {key}')
            index[key] = row
    return index


def check_authority(authority):
    journals = names(authority['journals'],'issn','previous')
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
        journal = journals.get(term['issn'])
        if not (start == term['from'] < term['until'] == end and scopes.get(term['scope'])
                and journal and journal['issn']==term['issn'] and term['pool'] in authority['pools']
                and type(term['revision']) is int and term['revision']>=1 and term['id'] not in versions):
            raise ValueError(f"条款配置无效: {term['id']}")
        versions.add(term['id'])
    return journals,institutions
