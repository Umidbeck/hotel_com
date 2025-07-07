# tests/conftest.py
import pytest
from django.db import connections

@pytest.fixture(autouse=True)
def cleanup_db(request):
    """Har bir testdan keyin bazani tozalash, faqat django_db belgilangan testlar uchun"""
    if "django_db" not in request.node.keywords:
        yield
        return
    yield
    for conn in connections.all():
        tables = conn.introspection.table_names()
        with conn.cursor() as cursor:
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")