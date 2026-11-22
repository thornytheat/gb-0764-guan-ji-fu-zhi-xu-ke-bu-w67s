from collections import Counter, defaultdict
from app.problem import DeskError, MESSAGES
from .spec import csv_lines
from .form import order


def receive(raw):
    seen = defaultdict(list)
    rejected, duplicates = [], []
    rows, headers = 0, 1
    for line, header, values in csv_lines(raw):
        if values == header:
            headers += 1
            continue
        rows += 1
        try:
            if not any(value.strip() for value in values):
                raise ValueError('BLANK_ROW')
            if len(values) != len(header):
                raise ValueError('WIDTH')
            item = order(line, {key: val.strip() for key, val in zip(header, values)})
            seen[item['entry']].append(item)
        except ValueError as exc:
            rejected.append({'line':line,'code':str(exc),'note':MESSAGES[str(exc)],'raw':values})
    if not rows:
        raise DeskError('NO_ROWS')
    accepted = []
    for group in seen.values():
        first = group[0]
        if any({k:v for k,v in item.items() if k!='line'} != {k:v for k,v in first.items() if k!='line'}
               for item in group[1:]):
            rejected.extend({'line':item['line'],'code':'ID_COLLISION','note':MESSAGES['ID_COLLISION'],
                             'raw':item,'related':[other['line'] for other in group]} for item in group)
        else:
            accepted.append(first)
            duplicates.extend({'line':item['line'],'first_line':first['line']} for item in group[1:])
    return {'received':rows,'segments':headers,'accepted':len(accepted),'duplicates':duplicates,
            'isolated':len(rejected),'exceptions':sorted(rejected,key=lambda r:r['line']),
            'reasons':dict(Counter(r['code'] for r in rejected)),
            'orders':sorted(accepted,key=lambda item:(item['received'],item['line']))}
