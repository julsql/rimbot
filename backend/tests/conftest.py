"""Fixtures pytest. Les tests unitaires n'ont pas besoin d'une vraie base
PostgreSQL : on remplace get_conn par un faux fournisseur de connexion pilotable.
Les tests d'intégration (marqueur `integration`) utilisent eux la fixture
`real_db` qui s'attache à la base pointée par la variable DATABASE_URL.
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

# Permet d'importer le package `app` sans installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class FakeCursor:
    def __init__(self, conn: "FakeConn") -> None:
        self.conn = conn
        self._result: list[tuple] = []
        self.last_query: str | None = None
        self.last_params: tuple | list | None = None

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None

    def execute(self, query, params=None):
        self.last_query = query
        self.last_params = params
        self.conn.queries.append((query, params))
        self._result = self.conn._next_result(query, params)

    def fetchone(self):
        return self._result[0] if self._result else None

    def fetchall(self):
        return list(self._result)


class FakeConn:
    def __init__(self) -> None:
        self.queries: list[tuple] = []
        self._responses: list = []

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def queue(self, rows):
        """Empile une réponse à renvoyer pour la prochaine requête."""
        self._responses.append(rows)

    def _next_result(self, query: str, params):
        if not self._responses:
            return []
        return self._responses.pop(0)


@pytest.fixture
def fake_conn():
    return FakeConn()


@pytest.fixture
def app_with_fake_db(monkeypatch, fake_conn):
    """Crée une app Flask avec un get_conn() qui retourne fake_conn."""
    @contextmanager
    def _get_conn():
        yield fake_conn

    # patcher avant le import de create_app
    import app.db as db_module
    import app.routes.poem as poem_module
    import app.routes.help as help_module
    import app.routes.health as health_module

    monkeypatch.setattr(db_module, "init_pool", lambda *a, **kw: None)
    monkeypatch.setattr(db_module, "get_conn", _get_conn)
    monkeypatch.setattr(poem_module, "get_conn", _get_conn)
    monkeypatch.setattr(help_module, "get_conn", _get_conn)
    monkeypatch.setattr(health_module, "get_conn", _get_conn)
    # Réinitialise les caches catalog
    monkeypatch.setattr(poem_module, "_catalog", None)
    monkeypatch.setattr(help_module, "_catalog", None)

    from app import create_app
    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture
def client(app_with_fake_db):
    return app_with_fake_db.test_client()


# ---------------------------------------------------------------------------
# Fixtures d'intégration : ces tests requièrent une vraie base Postgres seedée
# (typiquement celle du docker-compose ou un service Postgres en CI).
# ---------------------------------------------------------------------------


def _database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


@pytest.fixture(scope="session")
def real_db_url():
    url = _database_url()
    if not url:
        pytest.skip("DATABASE_URL non défini : tests d'intégration ignorés")
    return url


@pytest.fixture(scope="session")
def real_pool(real_db_url):
    """Pool psycopg réel, partagé pour la session. Vérifie aussi que la base
    est seedée (sinon on skip au lieu de planter sur une fausse erreur)."""
    from app.db import close_pool, init_pool

    pool = init_pool(real_db_url)
    try:
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM phrases")
            (n,) = cur.fetchone()
            if n == 0:
                pytest.skip("Base Postgres vide : seed non chargé")
        yield pool
    finally:
        close_pool()


@pytest.fixture(scope="session")
def real_catalog(real_pool):
    from app.services.poem_generator import WordCatalog

    with real_pool.connection() as conn:
        return WordCatalog.load(conn)


@pytest.fixture
def real_app(real_pool, real_db_url, monkeypatch):
    """App Flask connectée à la vraie base Postgres."""
    monkeypatch.setenv("DATABASE_URL", real_db_url)
    monkeypatch.setenv("CORS_ORIGINS", "*")

    # Réinitialise les caches de catalogues pour ne pas hériter de tests
    # unitaires précédents.
    import app.routes.help as help_module
    import app.routes.poem as poem_module
    monkeypatch.setattr(help_module, "_catalog", None)
    monkeypatch.setattr(poem_module, "_catalog", None)

    from app import create_app
    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture
def real_client(real_app):
    return real_app.test_client()
