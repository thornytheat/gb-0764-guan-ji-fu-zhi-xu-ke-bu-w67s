from app.intake.receive import receive
from app.registry.catalog import load_register
from app.registry.identify import identify
from app.licenses.decide import decide
from app.pagination.ledger import allocate
from app.register.balance import reconcile


def steps(raw, until='balance', register=None):
    results = {'intake':receive(raw)}
    if until == 'intake':
        return results
    register = register if register is not None else load_register()
    results['registry'] = identify(results['intake']['orders'],register)
    if until == 'registry':
        return results
    authority = register['authority']
    results['licenses'] = decide(results['registry']['records'],authority['terms'])
    if until == 'licenses':
        return results
    results['pages'] = allocate(results['licenses']['verdicts'],authority['pools'])
    if until != 'pages':
        results['balance'] = reconcile(results['intake'],results['pages'])
    return results
