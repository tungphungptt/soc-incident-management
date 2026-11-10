"""Integration audit restricted to the existing soc_schema_test database."""
import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import dotenv_values
from sqlalchemy.engine import make_url
from sqlalchemy import inspect, event, text

ROOT = Path(__file__).resolve().parents[2]
TARGET = 'soc_schema_test'
url = make_url(dotenv_values(ROOT/'backend/.env')['DATABASE_URL']).set(database=TARGET)
os.environ['DATABASE_URL'] = url.render_as_string(hide_password=False)
sys.path.insert(0, str(ROOT/'backend'))
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
from app.db import engine
from scripts.sql_runner import statements
assert engine.url.database == TARGET

@event.listens_for(engine, 'before_cursor_execute')
def guard(conn, cursor, statement, parameters, context, executemany):
    if re.search(r'\bsoc_incident_management\s*\.', statement, re.I):
        raise RuntimeError('Project database reference blocked')
    if re.match(r'\s*USE\s+', statement, re.I) and statement.strip().rstrip(';').lower() != 'use '+TARGET:
        raise RuntimeError('Database switch blocked')

report = {'target': TARGET, 'checked_at_utc': datetime.now(timezone.utc).isoformat()}
def save():
    (ROOT/'docs/sql/schema_test_results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

def located(path):
    lines=path.read_text(encoding='utf-8').splitlines()
    start=None; buffer=[]
    for n,line in enumerate(lines,1):
        if start is None and (not line.strip() or line.lstrip().startswith('--')): continue
        if start is None: start=n
        buffer.append(line)
        if line.rstrip().endswith(';'):
            yield start,n,'\n'.join(buffer).rstrip().rstrip(';')
            start=None; buffer=[]
    assert start is None

def queries(label, overrides=None):
    source=(ROOT/'sql/queries.sql').read_text(encoding='utf-8')
    blocks=re.split(r'^-- Q(\d{2})\. ',source,flags=re.M)[1:]
    results=[]
    with engine.connect() as c:
        assert c.exec_driver_sql('SELECT DATABASE()').scalar()==TARGET
        for stmt in statements(ROOT/'sql/queries.sql'):
            if stmt.lstrip().upper().startswith('SET '): c.execute(text(stmt))
        if overrides:
            for stmt in overrides:c.execute(text(stmt))
        report[label+'_parameters']=dict(c.exec_driver_sql('SELECT @month_start AS month_start, @month_end AS month_end, @date_from AS date_from, @date_to AS date_to, @incident_id AS incident_id, @now_ref AS now_ref').mappings().one())
        for i in range(0,len(blocks),2):
            number=blocks[i]; block=blocks[i+1]
            sql='\n'.join(block.splitlines()[1:]).strip().rstrip(';')
            try:
                rows=c.execute(text(sql)).mappings().all()
                item={'query':'Q'+number,'rows':len(rows),'status':'empty' if not rows else 'ok'}
                if number=='11': item['stored_risk_matches']=all(r['risk_score']==r['risk_score_luu'] for r in rows)
            except Exception as ex: item={'query':'Q'+number,'error':str(getattr(ex,'orig',ex))}
            results.append(item)
    report[label]=results
    print(label,json.dumps(results,ensure_ascii=True))

def main():
    global report
    if '--queries-only' in sys.argv:
        report=json.loads((ROOT/'docs/sql/schema_test_results.json').read_text(encoding='utf-8'))
        report.pop('fatal_error',None)
        queries('queries_after_original_seed_rollback')
        save()
        engine.dispose()
        sys.exit(0)
    
    try:
        with engine.begin() as c:
            assert c.exec_driver_sql('SELECT DATABASE()').scalar()==TARGET
            # Do not reset a previous audit run.
            assert not inspect(c).get_table_names(), 'Test database must be empty'
            for stmt in statements(ROOT/'docs/sql/01_schema.sql'): c.exec_driver_sql(stmt)
        report['schema']='ok: 18 tables'
        print(report['schema'])
        from scripts.migrate_workspaces import migrate as workspace
        from scripts.migrate_business_rules import migrate as rules
        workspace(); report['workspace_migration']='ok'
        rules(); report['business_rules_migration']='ok'
        inspector=inspect(engine)
        required={'incident_ioc':['LoaiIOC'],'hanh_dong_xu_ly':['ThoiLuongPhut'],
                  'lich_su_trang_thai':['NguoiThucHien'],'su_co':['MaChuyenGia','VaiTroChuyenGia','DiemRuiRo'],
                  'to_chuc':['DiemRuiRo'],'su_co_nhan_vien_soc':['ThoiDiemThamGia']}
        report['columns']={t:{c['name']:str(c['type']) for c in inspector.get_columns(t) if c['name'] in names} for t,names in required.items()}
        report['assignment_pk']=inspector.get_pk_constraint('su_co_nhan_vien_soc')['constrained_columns']
        report['seed_errors']=[]
        with engine.connect() as c:
            assert c.exec_driver_sql('SELECT DATABASE()').scalar()==TARGET
            for first,last,stmt in located(ROOT/'database-data/seed_soc_incident_management.sql'):
                if re.match(r'^USE\s+',stmt,re.I):
                    report['seed_database_redirect']={'line':first,'original':stmt,'executed':'USE '+TARGET}
                    c.exec_driver_sql('USE '+TARGET); continue
                if stmt.upper() in ('START TRANSACTION','COMMIT'): continue
                try: c.exec_driver_sql(stmt)
                except Exception as ex:
                    report['seed_errors'].append({'start_line':first,'end_line':last,'statement':stmt.splitlines()[0], 'error':str(getattr(ex,'orig',ex))})
            c.rollback()
        report['seed_transaction']='rolled back entirely after diagnostic import'
        print('Seed failed statements:',len(report['seed_errors']))
        queries('queries_after_original_seed_rollback')
    except Exception as ex:
        report['fatal_error']=str(getattr(ex,'orig',ex))
        print('AUDIT FAILED:', report['fatal_error'])
        raise
    finally:
        save()
        engine.dispose()

if __name__ == '__main__':
    main()
