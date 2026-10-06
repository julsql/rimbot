"""Tests de la documentation OpenAPI / Swagger UI."""
from __future__ import annotations

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def _routes_documentees(spec: dict) -> set[tuple[str, str]]:
    prefix = spec["servers"][0]["url"]
    return {
        (method.upper(), prefix + path)
        for path, operations in spec["paths"].items()
        for method in operations
    }


def test_openapi_json_est_servi(client):
    resp = client.get("/api/openapi.json")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["openapi"].startswith("3.")
    assert body["info"]["title"] == "Rimbot API"


def test_swagger_ui_est_servi(client):
    resp = client.get("/api/docs/")
    assert resp.status_code == 200
    assert b"swagger-ui" in resp.data
    assert b"/api/openapi.json" in resp.data


def test_spec_couvre_toutes_les_routes(app_with_fake_db, client):
    """Une route ajoutée sans être documentée (ou l'inverse) fait échouer ce test."""
    spec = client.get("/api/openapi.json").get_json()
    routes_reelles = {
        (method, rule.rule)
        for rule in app_with_fake_db.url_map.iter_rules()
        if rule.endpoint.split(".")[0] in {"health", "help", "poem"}
        for method in rule.methods & HTTP_METHODS
    }
    assert _routes_documentees(spec) == routes_reelles


def test_refs_de_schemas_existent(client):
    spec = client.get("/api/openapi.json").get_json()
    schemas = spec["components"]["schemas"]

    def refs(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "$ref":
                    yield value.rsplit("/", 1)[-1]
                else:
                    yield from refs(value)
        elif isinstance(node, list):
            for item in node:
                yield from refs(item)

    assert set(refs(spec["paths"])) <= set(schemas)
