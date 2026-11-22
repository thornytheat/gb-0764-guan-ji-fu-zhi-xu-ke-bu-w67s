from app.problem import MESSAGES
from .spans import normalize, pages_in, split_limit


def cancellation(row, active, released, balances):
    target = active.get(row['target'])
    code = row['ruling']
    if not code and target is None:
        code = 'REPEATED_CANCEL' if row['target'] in released else 'UNKNOWN_TARGET'
    if not code and row['org']['code'] != target['org']:
        code = 'WRONG_ORG'
    if not code and row['received'][:4] != target['received'][:4]:
        code = 'BOUNDARY'
    credit = 0
    if not code:
        reference = active.pop(row['target'])
        released.add(row['target'])
        credit = reference['licensed']
        if reference['pool']:
            balances[reference['pool']]['used'] -= credit
    return dict(entry=row['entry'], line=row['line'], target=row['target'], restored=credit, reason=code,
                target_line=target['line'] if target else None)


def allocate(verdicts, pools):
    accounts, active, released = {}, {}, set()
    orders, reversals = [], []
    for row in verdicts:
        if row['action'] == 'cancel':
            reversals.append(cancellation(row, active, released, accounts))
            continue
        intervals = normalize(row['pages'])
        chosen = row['license']
        reasons = {}
        allowed = denied = pending = 0
        pool = None
        granted, outside, shortage = [], [], []
        total = pages_in(intervals)
        if chosen:
            quota_id = chosen['pool']
            pool = f"{row['received'][:4]}/{quota_id}"
            account = accounts.setdefault(pool, {'limit':pools[quota_id],'used':0,'gross':0})
            start,end = row['journal']['pages']
            granted,outside,shortage = split_limit(intervals,start,end,account['limit']-account['used'])
            allowed, denied = pages_in(granted), pages_in(outside)+pages_in(shortage)
            if outside:
                reasons['OUTSIDE_ARTICLE'] = pages_in(outside)
            if shortage:
                reasons['QUOTA'] = pages_in(shortage)
            account['used'] += allowed
            account['gross'] += allowed
        elif row['ruling'] == 'NO_LICENSE':
            denied = total
            reasons[row['ruling']] = total
        else:
            pending = total
            reasons[row['ruling']] = total
        result = {'entry':row['entry'],'line':row['line'],'received':row['received'],
                  'org':row['org']['code'] if row['org'] else None,'license':chosen['id'] if chosen else None,
                  'pool':pool,'requested':total,'licensed':allowed,'denied':denied,'pending':pending,
                  'normalized':intervals,'granted':granted,'outside':outside,'shortage':shortage,
                  'reasons':reasons,'notes':{code:MESSAGES[code] for code in reasons}}
        orders.append(result)
        if allowed:
            active[row['entry']] = result
    return {'copies':orders,'reversals':reversals,
            'accounts':{key:dict(value,available=value['limit']-value['used']) for key,value in accounts.items()},
            'cancelled':sorted(released)}
