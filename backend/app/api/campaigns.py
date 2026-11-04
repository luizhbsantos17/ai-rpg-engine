"""Rotas de campanhas: /api/campaigns."""

from flask import Blueprint, request

from app.api.request_body import parse_body
from app.api.schemas import (
    CreateCampaignRequest,
    DeleteCampaignRequest,
    GenerateCampaignRequest,
    UpdateDraftRequest,
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


@bp.delete("/campaigns/<campaign_id>")
def delete_campaign(campaign_id: str):
    services = get_services()
    body = parse_body(DeleteCampaignRequest)
    services.campaigns.delete(services.local_user_id, campaign_id, body.confirm_title)
    return "", 204
