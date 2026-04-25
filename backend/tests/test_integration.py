"""Tests d'intégration end-to-end contre une vraie base PostgreSQL seedée.

Activés uniquement si DATABASE_URL est défini. En CI, le service Postgres
expose la base seedée via le workflow .github/workflows/backend.yml.
"""
from __future__ import annotations

import re

import pytest

pytestmark = pytest.mark.integration


def _is_french_punctuation_terminated(line: str) -> bool:
    return bool(re.search(r"[\.,;:!?…]\s*$", line))


_PUNCT_RE = re.compile(r"[^A-Za-zÀ-ÿ'\-]+")


def _strip_outer_punct(s: str) -> str:
    return _PUNCT_RE.sub("", s)


def _last_word_dersyll(conn, line: str) -> str | None:
    """Renvoie la dersyll du dernier mot d'un vers (ou None si introuvable).

    La base contient des entrées multi-mots ("nota bene", "a posteriori")
    et le générateur peut sortir des élisions ("j'cours") ou des composés
    ("là-bas"). On tente donc plusieurs tokenisations, du plus large au
    plus étroit, jusqu'à trouver une entrée correspondante."""
    tokens = [t for t in line.strip().rstrip(",;:!?…. ").split() if _strip_outer_punct(t)]
    if not tokens:
        return None

    # Variantes du dernier token (élision, composé à tirets…).
    last_raw = _strip_outer_punct(tokens[-1]).lower()
    last_variants: list[str] = [last_raw]
    if "'" in last_raw:
        last_variants.append(last_raw.split("'")[-1])
    if "-" in last_raw:
        last_variants.append(last_raw.split("-")[-1])
    last_variants.append(last_raw.rstrip("'"))

    # Combinaisons à tester : 3 derniers tokens, 2 derniers, puis variantes
    # du dernier seul (priorité aux entrées multi-mots).
    candidates: list[str] = []
    if len(tokens) >= 3:
        candidates.append(" ".join(_strip_outer_punct(t).lower() for t in tokens[-3:]))
    if len(tokens) >= 2:
        candidates.append(" ".join(_strip_outer_punct(t).lower() for t in tokens[-2:]))
    candidates.extend(last_variants)

    with conn.cursor() as cur:
        for cand in candidates:
            if not cand:
                continue
            cur.execute(
                """
                SELECT s.dersyll FROM mots m JOIN syllabes s ON s.id = m.iddersyll
                WHERE m.ortho = %s ORDER BY m.freqfilms DESC NULLS LAST LIMIT 1
                """,
                (cand,),
            )
            row = cur.fetchone()
            if row is not None:
                return row[0]
    return None


class TestSchemaAndSeed:
    def test_les_quatre_tables_sont_seedees(self, real_pool):
        with real_pool.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM mots")
            assert cur.fetchone()[0] > 100_000
            cur.execute("SELECT COUNT(*) FROM syllabes")
            assert cur.fetchone()[0] > 1_000
            cur.execute("SELECT COUNT(*) FROM phrases")
            assert cur.fetchone()[0] > 100
            cur.execute("SELECT COUNT(*) FROM ponctuation")
            assert cur.fetchone()[0] >= 1

    def test_pas_de_null_dans_les_colonnes_textes_critiques(self, real_pool):
        """Les colonnes texte sont stockées en chaîne vide, pas en NULL."""
        with real_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM mots "
                "WHERE genre IS NULL OR nombre IS NULL OR verper IS NULL"
            )
            assert cur.fetchone()[0] == 0


class TestCatalog:
    def test_charge_les_mots_et_les_syllabes(self, real_catalog):
        assert len(real_catalog.mots_possibles) > 100_000
        assert len(real_catalog.aide_phon) > 0
        first = real_catalog.aide_phon[0]
        assert {"courant", "dersyll", "API", "nboccurence"} <= set(first)


class TestGenerateAlgorithm:
    def test_generate_renvoie_un_poeme_quatre_vers(self, real_pool, real_catalog):
        from app.services.poem_generator import generate

        with real_pool.connection() as conn:
            poem, err1, err2 = generate(conn, real_catalog, "ABBA", "", "")

        assert poem is not None, f"Erreur: {err1}"
        # Quatre vers + ligne vide finale possiblement (split par \n)
        non_empty = [line for line in poem if line.strip()]
        assert len(non_empty) == 4
        assert all(_is_french_punctuation_terminated(l) for l in non_empty)

    def test_generate_avec_haiku_3_vers(self, real_pool, real_catalog):
        from app.services.poem_generator import generate

        with real_pool.connection() as conn:
            poem, err1, _ = generate(conn, real_catalog, "ABA", "1=5,2=7,3=5", "")

        assert poem is not None, f"Erreur: {err1}"
        non_empty = [line for line in poem if line.strip()]
        assert len(non_empty) == 3

    def test_generate_avec_rime_imposee_match(self, real_pool, real_catalog):
        """Avec une rime imposée, les deux vers doivent finir sur la même
        dernière syllabe en base (rime parfaite)."""
        from app.services.poem_generator import generate

        with real_pool.connection() as conn:
            poem, err1, err2 = generate(conn, real_catalog, "AA", "", "A=se")
        assert poem is not None, f"Erreur: {err1} / {err2}"

        non_empty = [l for l in poem if l.strip()]
        assert len(non_empty) == 2

        with real_pool.connection() as conn:
            ds = [_last_word_dersyll(conn, l) for l in non_empty]
        assert ds[0] is not None and ds[1] is not None
        # Comparaison insensible à la casse — la base contient "se", "Se", "SE"
        # comme entrées différentes alors qu'elles riment.
        assert ds[0].lower() == ds[1].lower() == "se", (
            f"rime imposée 'se' non respectée : {ds} sur vers {non_empty}"
        )

    def test_rimes_abba_se_correspondent(self, real_pool, real_catalog):
        """Forme ABBA : vers 1 ⇄ vers 4 et vers 2 ⇄ vers 3 doivent rimer."""
        from app.services.poem_generator import generate

        with real_pool.connection() as conn:
            poem, err1, _ = generate(conn, real_catalog, "ABBA", "1=8", "")
        assert poem is not None, f"Erreur: {err1}"

        non_empty = [l for l in poem if l.strip()]
        assert len(non_empty) == 4

        with real_pool.connection() as conn:
            ds = [_last_word_dersyll(conn, l) for l in non_empty]
        assert all(d is not None for d in ds), f"dersyll introuvable : {ds} / {non_empty}"
        # Comparaison insensible à la casse : la base contient des doublons
        # de syllabes phonétiquement identiques (Ne / ne / NE…).
        ds_lower = [d.lower() for d in ds]
        assert ds_lower[0] == ds_lower[3], (
            f"rime A (vers 1 et 4) ne match pas : {ds[0]!r} != {ds[3]!r}\n"
            f"vers : {non_empty[0]!r} / {non_empty[3]!r}"
        )
        assert ds_lower[1] == ds_lower[2], (
            f"rime B (vers 2 et 3) ne match pas : {ds[1]!r} != {ds[2]!r}\n"
            f"vers : {non_empty[1]!r} / {non_empty[2]!r}"
        )

    def test_rimes_abab_croisees(self, real_pool, real_catalog):
        """Forme ABAB : vers 1 rime avec vers 3, vers 2 avec vers 4."""
        from app.services.poem_generator import generate

        with real_pool.connection() as conn:
            poem, err1, _ = generate(conn, real_catalog, "ABAB", "1=8", "")
        assert poem is not None, f"Erreur: {err1}"

        non_empty = [l for l in poem if l.strip()]
        assert len(non_empty) == 4

        with real_pool.connection() as conn:
            ds = [_last_word_dersyll(conn, l) for l in non_empty]
        ds_lower = [d.lower() if d else None for d in ds]
        assert ds_lower[0] == ds_lower[2], f"A (1 et 3) : {ds}"
        assert ds_lower[1] == ds_lower[3], f"B (2 et 4) : {ds}"


class TestApiEndpointsIntegration:
    def test_health_renvoie_ok(self, real_client):
        resp = real_client.get("/api/health")
        assert resp.status_code == 200
        assert resp.get_json()["db"] == "ok"

    def test_help_syllables_retourne_des_rangees(self, real_client):
        resp = real_client.get("/api/help/syllables")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) > 100  # au moins 100 syllabes utilisables

    def test_preview_renvoie_la_forme(self, real_client):
        resp = real_client.post(
            "/api/poem/preview",
            json={"forme": "ABBA", "sylla": "1=10", "phone": ""},
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["preview"] is not None
        # 4 lignes (une par lettre), 9 underscores chacune (10 syllabes - 1)
        lignes = [l for l in body["preview"].split("\n") if l]
        assert len(lignes) == 4
        assert all(l.count("_") == 9 for l in lignes)

    def test_generate_un_poeme_via_api(self, real_client):
        resp = real_client.post(
            "/api/poem/generate",
            json={"forme": "ABAB", "sylla": "", "phone": ""},
        )
        assert resp.status_code == 200, resp.get_json()
        body = resp.get_json()
        assert body["poem"] is not None
        assert body["err1"] == ""
        assert isinstance(body["poem"], list) and len(body["poem"]) >= 4

    def test_generate_forme_vide_renvoie_400(self, real_client):
        resp = real_client.post("/api/poem/generate", json={"forme": ""})
        assert resp.status_code == 400
        assert resp.get_json()["poem"] is None
