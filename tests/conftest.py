# tests/conftest.py
import pytest
import django
from django.conf import settings

def pytest_configure():
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TIME_ZONE': 'UTC',
        'CONN_HEALTH_CHECKS': False,  # <-- Bu yerga ham qo'shamiz
        'OPTIONS': {
            'timeout': 20,
        }
    }
    django.setup()

@pytest.fixture(autouse=True)
def cleanup_db():
    """Har bir testdan keyin bazani tozalash"""
    from django.db import connections
    yield
    for conn in connections.all():
        tables = conn.introspection.table_names()
        with conn.cursor() as cursor:
            for table in tables:
                cursor.execute(f'DELETE FROM {table}')