"""Rotas do modo administrador (SPEC 16). Separadas do turno: comandos nunca passam pela IA.

POST /api/admin/login                    {password} -> {token}
POST /api/admin/logout                   (cabeçalho X-Admin-Token)
POST /api/campaigns/<id>/admin           {command} + cabeçalho X-Admin-Token
"""

from flask import Blueprint, request

from app.admin.sessions import AdminAccessError
from app.api.request_body import parse_body
from app.api.schemas import AdminCommandRequest, AdminLoginRequest
from app.services.startup import get_services

bp = Blueprint("admin", __name__)
TOKEN_HEADER = "X-Admin-Token"


@bp.post("/admin/login")
def login():
    services = get_services()
    body = parse_body(AdminLoginRequest)
    try:
        token = services.admin_sessions.login(body.password)
    except AdminAccessError as exc:
        return {"error": {"code": 403, "name": "forbidden", "message": str(exc)}}, 403
    return {"token": token}


@bp.post("/admin/logout")
def logout():
    get_services().admin_sessions.logout(request.headers.get(TOKEN_HEADER))
    return "", 204


@bp.post("/campaigns/<campaign_id>/admin")
def run_command(campaign_id: str):
    services = get_services()
    body = parse_body(AdminCommandRequest)
    try:
        result = services.admin.execute(services.local_user_id, campaign_id, request.headers.get(TOKEN_HEADER),
                                        body.command)
    except AdminAccessError as exc:
        return {"error": {"code": 401, "name": "unauthorized", "message": str(exc)}}, 401
    return result.to_dict()
