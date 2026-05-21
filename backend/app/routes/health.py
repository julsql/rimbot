from flask import Blueprint, current_app, jsonify

from ..db import get_conn

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        db_status = "ok"
    except Exception:  # pragma: no cover - réseau
        # On logge le détail côté serveur sans l'exposer au client (fuite d'info).
        current_app.logger.exception("Health check: échec de la connexion à la base")
        return jsonify(status="degraded", db="unavailable"), 503
    return jsonify(status="ok", db=db_status)
