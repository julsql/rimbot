from flask import Blueprint, jsonify

from ..db import get_conn
from ..services.poem_generator import WordCatalog

bp = Blueprint("help", __name__)

_catalog: WordCatalog | None = None


def _catalog_singleton() -> WordCatalog:
    global _catalog
    if _catalog is None:
        with get_conn() as conn:
            _catalog = WordCatalog.load(conn)
    return _catalog


@bp.get("/syllables")
def syllables():
    return jsonify(_catalog_singleton().aide_phon)
