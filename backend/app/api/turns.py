"""POST /api/campaigns/<id>/turns — joga um turno e devolve a narração aos poucos (SSE).

Erros do pedido (campanha inexistente, turno em andamento, texto vazio) voltam como
JSON comum com o código HTTP adequado, antes de o stream começar. Falhas da IA durante
o stream chegam como evento "error" e deixam o turno pronto para ser repetido.
"""

from flask import Blueprint, Response

from app.api.request_body import parse_body
from app.api.schemas import PlayTurnRequest
from app.api.sse import turn_events_to_sse
from app.services.startup import get_services

bp = Blueprint("turns", __name__)


@bp.post("/campaigns/<campaign_id>/turns")
def play_turn(campaign_id: str):
    services = get_services()
    body = parse_body(PlayTurnRequest)
    prepared = services.turns.prepare(services.local_user_id, campaign_id, body.turn_id, body.input)
    return Response(
        turn_events_to_sse(services.turns.run(prepared)),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@bp.post("/campaigns/<campaign_id>/turns/<turn_id>/regenerate")
def regenerate_narration(campaign_id: str, turn_id: str):
    """Outra versão da narração da última jogada (mesmos dados e resultados). Mesmo formato SSE."""
    services = get_services()
    prepared = services.turns.prepare_regeneration(services.local_user_id, campaign_id, turn_id)
    return Response(
        turn_events_to_sse(services.turns.run(prepared)),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
