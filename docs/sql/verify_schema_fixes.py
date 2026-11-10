"""Test corrected historical seed only on the isolated soc_schema_test."""
import json
import re
from pathlib import Path
import run_schema_test as audit
from sqlalchemy import text, inspect

ROOT=audit.ROOT
engine=audit.engine
audit.report=json.loads((ROOT/'docs/sql/schema_test_results.json').read_text(encoding='utf-8'))
audit.report.pop('fatal_error',None)
try:
    with engine.begin() as c:
        assert c.exec_driver_sql('SELECT DATABASE()').scalar()=='soc_schema_test'
        # Original diagnostic import was rolled back: never reset business rows.
        for table in inspect(c).get_table_names():
            if table=='soc_bonus_policy':continue
            assert c.exec_driver_sql(f'SELECT COUNT(*) FROM soc_schema_test.`{table}`').scalar()==0,table
        triggers=c.exec_driver_sql("SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='soc_schema_test'").scalars().all()
        for name in triggers:
            assert re.fullmatch(r'\w+',name)
            c.exec_driver_sql(f'DROP TRIGGER soc_schema_test.`{name}`')
    audit.report['corrected_seed_workflow']='Remove test-only triggers; import historical seed; reapply workspace then business migration'
    with engine.begin() as c:
        for first,last,stmt in audit.located(ROOT/'docs/sql/03_seed_proposed.sql'):
            if stmt.upper() in ('START TRANSACTION','COMMIT'):continue
            try:c.execute(text(stmt))
            except Exception as ex:
                audit.report['corrected_seed_error']={'start_line':first,'end_line':last,'error':str(getattr(ex,'orig',ex))}
                raise
        assert c.exec_driver_sql('SELECT COUNT(*) FROM ioc GROUP BY GiaTriIOC HAVING COUNT(*)>1 LIMIT 1').first() is None
        original=(ROOT/'database-data/seed_soc_incident_management.sql').read_text(encoding='utf-8')
        blocks=re.findall(r'INSERT INTO `incident_ioc` .*?VALUES\s*(.*?);',original,re.S)
        expected=sum(len(re.findall(r"\('[^']*', '[^']*'\)",b)) for b in blocks)
        assert c.exec_driver_sql('SELECT COUNT(*) FROM incident_ioc').scalar()==expected
    from scripts.migrate_workspaces import migrate as workspace
    from scripts.migrate_business_rules import migrate as rules
    workspace();rules()
    audit.report['corrected_seed']='ok'
    with engine.connect() as c:
        audit.report['final_counts']={t:c.exec_driver_sql(f'SELECT COUNT(*) FROM soc_schema_test.`{t}`').scalar() for t in inspect(c).get_table_names()}
        audit.report['critical_missing_expert']=c.exec_driver_sql("SELECT COUNT(*) FROM su_co WHERE MucDoNghiemTrong='CRITICAL' AND (MaChuyenGia IS NULL OR VaiTroChuyenGia NOT IN ('SOC_L2','SOC_L3'))").scalar()
    audit.queries('queries_after_corrected_seed_default_parameters')
finally:
    audit.save()
    engine.dispose()
