import csv
from io import StringIO

from app.problem import DeskError

COLUMNS = ('entry', 'action', 'received', 'institution', 'issn', 'pages', 'target')
SENTINELS = {'-', 'N/A', 'NULL', '未知'}


def csv_lines(raw):
    for name in ('utf-8-sig', 'gb18030'):
        try:
            text = raw.decode(name)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise DeskError('DECODE')
    if not text:
        raise DeskError('EMPTY_FILE')
    if not text.strip():
        raise DeskError('BLANK_FILE')
    reader = csv.reader(StringIO(text, newline=''), strict=True)
    try:
        header = next(reader)
        if sorted(header) != sorted(COLUMNS):
            raise DeskError('HEADER')
        start = reader.line_num + 1
        for values in reader:
            yield start, header, values
            start = reader.line_num + 1
    except csv.Error as exc:
        raise DeskError('DECODE') from exc
