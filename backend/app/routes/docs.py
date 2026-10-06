from flask import Blueprint, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

from ..openapi import SPEC

DOCS_URL = "/api/docs"
SPEC_URL = "/api/openapi.json"

bp = Blueprint("docs", __name__)


@bp.get("/openapi.json")
def openapi():
    return jsonify(SPEC)


swagger_bp = get_swaggerui_blueprint(DOCS_URL, SPEC_URL, config={"app_name": "Rimbot API"})
