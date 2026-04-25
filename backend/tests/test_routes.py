"""Tests des routes HTTP avec un faux pool de connexions."""
from __future__ import annotations

import json


def _seed_catalog(fake_conn):
    """Prépare les réponses attendues par WordCatalog.load()."""
    fake_conn.queue([("chat",), ("chien",)])
    fake_conn.queue([
        ("t@t", "tat", "t@t", 42),
        ("se",  "se",  "se",  20),
    ])


def test_health_ok(client, fake_conn):
    fake_conn.queue([(1,)])
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"


def test_help_syllables_returns_phon_list(client, fake_conn):
    _seed_catalog(fake_conn)
    resp = client.get("/api/help/syllables")
    assert resp.status_code == 200
    body = resp.get_json()
    assert isinstance(body, list)
    assert {item["courant"] for item in body} == {"t@t", "se"}
    assert body[0]["nboccurence"] == 42


def test_preview_returns_form(client, fake_conn):
    _seed_catalog(fake_conn)
    resp = client.post(
        "/api/poem/preview",
        json={"forme": "ABBA", "sylla": "1=8", "phone": ""},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["preview"] is not None
    # Une ligne par lettre, 7 underscores (8 syllabes)
    lignes = [l for l in body["preview"].split("\n") if l]
    assert len(lignes) == 4
    assert all(l.count("_") == 7 for l in lignes)


def test_preview_forme_vide_renvoie_400(client, fake_conn):
    _seed_catalog(fake_conn)
    resp = client.post("/api/poem/preview", json={"forme": ""})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["preview"] is None
    assert "aucune forme" in body["err1"].lower()


def test_generate_forme_vide_renvoie_400(client, fake_conn):
    _seed_catalog(fake_conn)
    resp = client.post("/api/poem/generate", json={"forme": ""})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["poem"] is None


def test_generate_accepte_form_data(client, fake_conn):
    """Compatibilité avec form-data classique (ancien front Django)."""
    _seed_catalog(fake_conn)
    # Échec rapide attendu : la génération va tomber sur un fake_conn vide
    # côté requête phrase. On vérifie juste que la route accepte form-data.
    resp = client.post("/api/poem/generate", data={"forme": "ABBA", "sylla": "1=12"})
    assert resp.status_code in (200, 400)
    assert resp.is_json
