import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend import database


def test_get_db_url_supabase(monkeypatch) -> None:
    monkeypatch.delenv("CORE_DB_URL", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://foo.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "bar")
    url = database.get_db_url()
    assert url.startswith("postgresql+psycopg2://postgres:bar@db.foo.supabase.co")


def test_get_db_url_env_override(monkeypatch) -> None:
    monkeypatch.setenv("CORE_DB_URL", "sqlite:///tmp.db")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    assert database.get_db_url() == "sqlite:///tmp.db"


def test_get_db_url_missing(monkeypatch) -> None:
    monkeypatch.delenv("CORE_DB_URL", raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://foo.supabase.co")
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    with pytest.raises(ValueError):
        database.get_db_url()
