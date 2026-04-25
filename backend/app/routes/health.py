from flask import Blueprint, jsonify

from ..db import get_conn

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        db_status = "ok"
    except Exception as exc:  # pragma: no cover - réseau
        return jsonify(status="degraded", db=str(exc)), 503
    return jsonify(status="ok", db=db_status)
