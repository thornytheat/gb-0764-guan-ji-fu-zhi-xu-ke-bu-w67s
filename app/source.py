from flask import request
from app.problem import DeskError
from app.settings import CATALOG


def bundle(name):
    if name not in ('dirty','clean'):
        raise DeskError('SAMPLE_UNKNOWN',404)
    return (CATALOG / f'{name}.csv').read_bytes()


def read_request():
    if request.method == 'GET':
        return bundle(request.args.get('sample','dirty'))
    data = request.get_json(silent=True)
    if not isinstance(data,dict) or len(data)!=1:
        raise DeskError('BAD_PAYLOAD')
    if isinstance(data.get('sample'),str):
        return bundle(data['sample'])
    if isinstance(data.get('csv'),str):
        try:
            return data['csv'].encode()
        except UnicodeEncodeError as exc:
            raise DeskError('DECODE') from exc
    raise DeskError('BAD_PAYLOAD')
