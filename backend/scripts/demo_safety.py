"""Fail closed before connecting demo writers to a project database."""
import re


def validate_demo_database_name(name):
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_]+', name):
        raise ValueError('Demo database name must contain only letters, digits and underscores')
    lowered = name.lower()
    if lowered == 'soc_incident_management' or not any(word in lowered for word in ('test', 'demo')):
        raise ValueError('Refusing database: only names containing test or demo are allowed; soc_incident_management is forbidden')
    return name


def require_demo_engine(engine):
    # In-memory SQLite is used exclusively by unit tests.
    if engine.dialect.name == 'sqlite' and engine.url.database in (None, '', ':memory:'):
        return
    validate_demo_database_name(engine.url.database)
