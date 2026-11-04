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
  "protagonist": {"name": "...", "kind": "character", "description": "aparência, origem, personalidade",
                  "character_class": "", "race": ""},
  "starting_location": "nome do local onde a história começa",
  "location_description": "...",
  "world_facts": ["regra importante do mundo", "como funciona a morte neste universo"],
  "death_rule": {"mode": "permanent | unconscious | resurrection | reincarnation | narrative",
                 "description": "o que acontece quando alguém chega a 0 de vida", "revive_after": "8h"},
  "companions": [
    {"name": "...", "description": "...", "personality": "...", "goal": "o que ele quer",
     "bond": "amigo de infância", "attributes": {"Vida": 18, "Força": 7}}
  ]
}
Regras:
- Crie de 3 a 6 atributos que façam sentido NESTE universo (não precisa ser o sistema tradicional).
  Pelo menos um deve ser recurso ("resource": true), como vida ou energia.
- value_type: "integer" (inteiro), "decimal", "nominal" (faixa como "Rank C") ou "conceptual" (texto livre).
- Use a premissa: se ela já diz quem é o protagonista, respeite. Se não diz, invente alguém coerente.
- character_class e race: classe/ofício e raça/espécie do protagonista que existam NESTE universo e
  combinem com o gênero e a premissa. Se o universo não tiver isso, deixe "".
- world_facts: de 2 a 5 fatos curtos e importantes do universo. Um deles diz como funciona a morte
  (permanente, ressurreição, reencarnação...).
- companions: só se a premissa tiver uma turma, grupo ou companheiros (senão, lista vazia []).
  Crie de 2 a 6 pessoas REALMENTE diferentes: personalidade, objetivo, laço com o protagonista e
  valores de atributos próprios (use os mesmos nomes de atributos). Nada de cópias com nomes trocados.
- Escreva em português do Brasil.
"""


def build_setup_messages(brief: CampaignBrief) -> list[ChatMessage]:
    lines = [f"Título: {brief.title}"]
    if brief.genre_tags:
        lines.append(f"Gêneros: {', '.join(brief.genre_tags)}")
    lines.append(f"Premissa: {brief.player_visible.get('premise') or '(livre: invente uma)'}")
    if brief.gm_secret:
        lines.append("Segredos do mestre (para manter coerência; não os revele na premissa nem no nome):")
        lines += [f"- {value}" for value in brief.gm_secret.values()]
    return [ChatMessage("system", SETUP_RULES), ChatMessage("user", "\n".join(lines) + "\n\nResponda só com o JSON.")]
