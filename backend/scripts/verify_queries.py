"""Execute all 18 numbered read-only SQL queries on one parameterized session."""
import json
import re
from sqlalchemy import text
from datetime import datetime
from pathlib import Path
from app.db import engine
from scripts.sql_runner import statements


def verify():
    root=Path(__file__).resolve().parents[2]
    source=(root/'sql'/'queries.sql').read_text(encoding='utf-8')
    blocks=re.split(r'-- Q(\d{2})\. ',source)[1:]
    result=[]
    with engine.connect() as conn:
        for statement in statements(root/'sql'/'queries.sql'):
            if statement.lstrip().upper().startswith('SET '):conn.execute(text(statement))
        for index in range(0,len(blocks),2):
            number=int(blocks[index]);block=blocks[index+1]
            title=block.splitlines()[0]
            sql='\n'.join(block.splitlines()[1:]).strip().rstrip(';')
            values=conn.execute(text(sql)).mappings().all()
            if number==11:assert all(r['risk_score']==r['risk_score_luu'] for r in values)
            result.append({'query':number,'requirement':title,'row_count':len(values)})
            print(f'Q{number:02}: {len(values)} rows')
        assert [r['query'] for r in result]==list(range(1,19))
        parameters=dict(conn.exec_driver_sql('SELECT @month_start AS month_start,@date_from AS date_from,@date_to AS date_to,@incident_id AS incident_id,@now_ref AS now_ref,@overload_threshold AS overload_threshold').mappings().one())
    report={'checked_at_utc':datetime.utcnow().isoformat(),'parameters':parameters,'queries':result}
    (root/'docs'/'sql-query-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    return result


if __name__=='__main__':verify()
