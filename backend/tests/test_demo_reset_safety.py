"""The reset must reject dangerous targets without opening any DB connection."""
import importlib.util
from pathlib import Path
import pytest
from scripts.demo_safety import validate_demo_database_name

PATH = Path(__file__).resolve().parents[2]/'docs/demo/reset_demo.py'
spec = importlib.util.spec_from_file_location('reset_demo', PATH)
reset = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reset)


@pytest.mark.parametrize('name', ['soc_incident_management','SOC_INCIDENT_MANAGEMENT','production','soc_test; DROP DATABASE x','../demo','demo`x','test.prod',''])
def test_rejects_unsafe_name_before_connecting(name, monkeypatch):
    import sqlalchemy
    monkeypatch.setattr(sqlalchemy, 'create_engine', lambda *a, **k: pytest.fail('Must reject before connecting'))
    with pytest.raises(SystemExit) as error:
        reset.main(['--database', name, '--reset-existing'])
    assert error.value.code == 2


@pytest.mark.parametrize('name', ['soc_schema_test','soc_demo','TEST_soc','demo_soc'])
def test_dry_run_never_connects(name, monkeypatch, capsys):
    import sqlalchemy
    monkeypatch.setattr(sqlalchemy, 'create_engine', lambda *a, **k: pytest.fail('Dry run must not connect'))
    assert reset.main(['--database', name, '--dry-run']) == 0
    assert 'Dry run' in capsys.readouterr().out


def test_sql_redirects_only_to_validated_target():
    target = validate_demo_database_name('soc_schema_test')
    sqls = reset.read_sql(PATH.parents[1]/'sql/03_seed_proposed.sql', target)
    assert 'USE `soc_schema_test`' in sqls
    assert not any(s.startswith('USE soc_incident_management') for s in sqls)
