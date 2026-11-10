"""Small mysql-client DELIMITER reader shared by migration and verification."""
from pathlib import Path


def statements(path):
    delimiter=';'
    buffer=[]
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if line.strip().upper().startswith('DELIMITER '):
            delimiter=line.strip().split(None,1)[1]
            continue
        if not buffer and (not line.strip() or line.lstrip().startswith('--')):
            continue
        buffer.append(line)
        joined='\n'.join(buffer).rstrip()
        if joined.endswith(delimiter):
            yield joined[:-len(delimiter)].strip()
            buffer=[]
    if any(line.strip() and not line.lstrip().startswith('--') for line in buffer):
        raise ValueError('Unterminated SQL statement: '+str(path))
