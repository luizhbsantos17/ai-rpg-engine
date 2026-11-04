"""Instruções para preparar a campanha (primeiro turno): regras básicas, protagonista e local."""

from __future__ import annotations

from app.ai.prompts.narrator import CampaignBrief
from app.providers import ChatMessage

SETUP_RULES = """\
Você prepara o início de uma campanha de RPG. Responda SOMENTE com um JSON neste formato:
{
  "attributes": [
    {"name": "Vida", "value_type": "integer", "resource": true, "description": "...", "initial_value": 20},
    {"name": "Força", "value_type": "integer", "resource": false, "description": "...", "initial_value": 5}
  ],
  "protagonist": {"name": "...", "kind": "character", "description": "aparência, origem, personalidade"},
  "starting_location": "nome do local onde a história começa",
  "location_description": "...",
  "world_facts": ["regra importante do mundo", "como funciona a morte neste universo"]
}
Regras:
- Crie de 3 a 6 atributos que façam sentido NESTE universo (não precisa ser o sistema tradicional).
  Pelo menos um deve ser recurso ("resource": true), como vida ou energia.
- value_type: "integer" (inteiro), "decimal", "nominal" (faixa como "Rank C") ou "conceptual" (texto livre).
- Use a premissa: se ela já diz quem é o protagonista, respeite. Se não diz, invente alguém coerente.
- world_facts: de 2 a 5 fatos curtos e importantes do universo. Um deles diz como funciona a morte
  (permanente, ressurreição, reencarnação...).
- Escreva em português do Brasil.
"""


def build_setup_messages(brief: CampaignBrief) -> list[ChatMessage]:
    lines = [f"Título: {brief.title}"]
    if brief.genre_tags:
        lines.append(f"Gêneros: {', '.join(brief.genre_tags)}")
    lines.append(f"Premissa: {brief.player_visible.get('premise') or '(livre: invente uma)'}")
    return [ChatMessage("system", SETUP_RULES), ChatMessage("user", "\n".join(lines) + "\n\nResponda só com o JSON.")]
