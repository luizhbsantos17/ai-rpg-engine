"""Rotas de campanhas: /api/campaigns."""

from flask import Blueprint, request, send_file

from app.api.request_body import parse_body
from app.api.schemas import (
    CreateCampaignRequest,
    DeleteCampaignRequest,
    GenerateCampaignRequest,
    GenerateImageRequest,
    UpdateDraftRequest,
    UpdateSettingsRequest,
)
from app.services.startup import get_services

bp = Blueprint("campaigns", __name__)


@bp.get("/campaigns")
def list_campaigns():
    services = get_services()
    return {"campaigns": services.campaigns.list(services.local_user_id)}


@bp.post("/campaigns")
def create_campaign():
    services = get_services()
    body = parse_body(CreateCampaignRequest)
    campaign = services.campaigns.create(services.local_user_id, body.title, body.premise, body.genre_tags)
    return {"campaign": campaign}, 201


@bp.post("/campaigns/generate")
def generate_campaign():
    """Gera (ou gera de novo) uma campanha aleatória como rascunho. Segredos ficam no servidor."""
    services = get_services()
    body = parse_body(GenerateCampaignRequest)
    campaign = services.generation.generate(services.local_user_id, body.genres, body.themes,
                                            draft_id=body.draft_id, keep=list(body.keep))
    return {"campaign": campaign}, 201


@bp.patch("/campaigns/<campaign_id>")
def update_draft(campaign_id: str):
    services = get_services()
    body = parse_body(UpdateDraftRequest)
    changes = body.model_dump(exclude_none=True)
    return {"campaign": services.generation.update_draft(services.local_user_id, campaign_id, changes)}


@bp.post("/campaigns/<campaign_id>/start")
def start_campaign(campaign_id: str):
    services = get_services()
    return {"campaign": services.generation.start(services.local_user_id, campaign_id)}


@bp.get("/campaigns/<campaign_id>")
def get_campaign(campaign_id: str):
    services = get_services()
    return {"campaign": services.campaigns.get(services.local_user_id, campaign_id)}


@bp.get("/campaigns/<campaign_id>/history")
def campaign_history(campaign_id: str):
    services = get_services()
    after_seq = request.args.get("after_seq", default=0, type=int)
    return services.campaigns.history(services.local_user_id, campaign_id, after_seq=after_seq)


@bp.get("/campaigns/<campaign_id>/sheet")
def character_sheet(campaign_id: str):
    services = get_services()
    return services.sheets.sheet(services.local_user_id, campaign_id)


@bp.get("/campaigns/<campaign_id>/known")
def known_characters(campaign_id: str):
    """O que o protagonista sabe sobre outros personagens (nunca o estado verdadeiro deles)."""
    services = get_services()
    return services.known.known(services.local_user_id, campaign_id)


@bp.get("/campaigns/<campaign_id>/journal")
def campaign_journal(campaign_id: str):
    """Mapa, diário e laços do ponto de vista do protagonista."""
    services = get_services()
    return services.journal.journal(services.local_user_id, campaign_id)


@bp.get("/campaigns/<campaign_id>/settings")
def campaign_settings(campaign_id: str):
    services = get_services()
    return services.campaign_settings.get(services.local_user_id, campaign_id)


@bp.put("/campaigns/<campaign_id>/settings")
def update_campaign_settings(campaign_id: str):
    """Grava uma versão nova das configurações (experiência e/ou conteúdo). Avisos de impacto voltam em "warnings"."""
    services = get_services()
    body = parse_body(UpdateSettingsRequest)
    return services.campaign_settings.update(services.local_user_id, campaign_id, body.experience, body.content)


@bp.get("/images/status")
def images_status():
    return get_services().images.status()


@bp.post("/campaigns/<campaign_id>/images")
def generate_image(campaign_id: str):
    """Gera (ou reaproveita) a imagem de uma entidade. Sem provedor: 503 "desligado"."""
    services = get_services()
    body = parse_body(GenerateImageRequest)
    return services.images.generate_for_entity(services.local_user_id, campaign_id, body.entity_id), 201


@bp.get("/campaigns/<campaign_id>/images/<image_id>")
def image_file(campaign_id: str, image_id: str):
    services = get_services()
    path, mime_type = services.images.file_for(services.local_user_id, campaign_id, image_id)
    return send_file(path, mimetype=mime_type)


@bp.get("/campaigns/<campaign_id>/export")
def export_campaign(campaign_id: str):
    """Baixa a campanha inteira como arquivo JSON (guardar, levar para outro computador, importar)."""
    services = get_services()
    snapshot = services.campaigns.export(services.local_user_id, campaign_id)
    filename = f"campanha-{campaign_id[:8]}.json"
    return snapshot, 200, {"Content-Disposition": f'attachment; filename="{filename}"'}


@bp.post("/campaigns/import")
def import_campaign():
    services = get_services()
    snapshot = request.get_json(silent=True)
    if not isinstance(snapshot, dict):
        return {"error": {"code": 400, "name": "invalid_input", "message": "Envie o arquivo JSON da campanha."}}, 400
    return {"campaign": services.campaigns.import_(services.local_user_id, snapshot)}, 201


@bp.delete("/campaigns/<campaign_id>")
def delete_campaign(campaign_id: str):
    services = get_services()
    body = parse_body(DeleteCampaignRequest)
    services.campaigns.delete(services.local_user_id, campaign_id, body.confirm_title)
    return "", 204
