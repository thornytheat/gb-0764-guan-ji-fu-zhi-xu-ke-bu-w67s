SPECIFICITY = {'institution':3,'consortium':2,'public':1}


def eligible(license, row):
    if license['issn'] != row['journal']['issn'] or not license['from'] <= row['received'] < license['until']:
        return False
    scope = license['scope']
    return scope == 'public' or (scope == 'consortium' and license['subject'] in row['org']['groups']) or (
        scope == 'institution' and license['subject'] == row['org']['code'])


def rank(license):
    return SPECIFICITY[license['scope']], license['revision']
