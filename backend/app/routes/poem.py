from flask import Blueprint, jsonify, request

from ..db import get_conn
from ..services.poem_generator import (
    WordCatalog,
    generate,
    prev,
)

bp = Blueprint("poem", __name__)

_catalog: WordCatalog | None = None


def _catalog_singleton() -> WordCatalog:
    global _catalog
    if _catalog is None:
        with get_conn() as conn:
            _catalog = WordCatalog.load(conn)
    return _catalog


@bp.post("/generate")
def generate_route():
    payload = request.get_json(silent=True) or request.form.to_dict()
    forme = (payload.get("forme") or "").strip()
    sylla = (payload.get("sylla") or "").strip()
    phone = (payload.get("phone") or "").strip()

    if not forme:
        return jsonify(poem=None, err1="Vous n'avez donné aucune forme", err2=""), 400

    catalog = _catalog_singleton()
    with get_conn() as conn:
        poem, err1, err2 = generate(conn, catalog, forme, sylla, phone)

    status = 200 if poem is not None else 400
    return jsonify(poem=poem, err1=err1, err2=err2), status


@bp.post("/preview")
def preview_route():
    payload = request.get_json(silent=True) or request.form.to_dict()
    forme = (payload.get("forme") or "").strip()
    sylla = (payload.get("sylla") or "").strip().strip(",").replace(" ", "")
    phone = (payload.get("phone") or "").strip().strip(",").replace(" ", "")

    catalog = _catalog_singleton()
    texte, err1, err2 = prev(catalog, forme, sylla, phone)
    status = 200 if texte is not None else 400
    return jsonify(preview=texte, err1=err1, err2=err2), status
