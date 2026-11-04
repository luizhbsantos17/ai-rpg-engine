"""Instruções para preparar a campanha (primeiro turno): regras básicas, protagonista e local."""

from __future__ import annotations

from app.ai.prompts.narrator import CampaignBrief
from app.providers import ChatMessage

SETUP_RULES = """\
Você prepara o início de uma campanha de RPG. Responda SOMENTE com um JSON neste formato:
{
  "attributes": [
    {"name": "...", "value_type": "integer", "resource": true, "description": "...", "initial_value": 20},
    {"name": "...", "value_type": "integer", "resource": false, "description": "...", "initial_value": 5}
  ],
  "protagonist": {"name": "...", "kind": "character", "description": "aparência, origem, personalidade",
                  "character_class": "", "race": ""},
  "starting_location": "nome do local onde a história começa",
  "location_description": "...",
  "world_facts": ["regra importante do mundo", "como funciona a morte neste universo"],
  "death_rule": {"mode": "permanent | unconscious | resurrection | reincarnation | narrative",
                 "description": "o que acontece quando alguém chega a 0 de vida", "revive_after": "8h"},
  "starting_skills": [{"name": "...", "description": "...", "category": "...", "level": 1}],
  "starting_items": [{"name": "...", "description": "...", "quantity": 1, "slot": "", "bonus": {}, "equipped": false}],
  "companions": [
    {"name": "...", "description": "...", "personality": "...", "goal": "o que ele quer",
     "bond": "amigo de infância", "attributes": {"Vida": 18, "Força": 7}}
  ]
}
Regras:
- attributes: de 5 a 10 atributos que façam sentido NESTE universo (não precisa ser o sistema tradicional).
  Pense no que um jogador deste gênero espera ver na ficha. Monte assim:
  * recursos ("resource": true): a vida (ou equivalente) e, se o universo tiver magia, poderes ou esforço
    físico importante, a energia dele (mana, chakra, estamina, sanidade... o nome que combinar);
  * atributos principais: de 3 a 6 qualidades do personagem (físicas, mentais, sociais ou sobrenaturais);
  * progressão: se o universo for estilo jogo (sistema, níveis, isekai, RPG de fantasia), inclua "Nível"
    (começa em 1) e "Experiência" (começa em 0); se não for, a progressão pode ser só pelas habilidades;
  * extras que combinem (sorte, reputação, fama, ouro...), se fizerem sentido.
- value_type: "integer" (inteiro), "decimal", "nominal" (faixa como "Rank C") ou "conceptual" (texto livre).
- Use a premissa: se ela já diz quem é o protagonista, respeite. Se não diz, invente alguém coerente.
- character_class e race: classe/ofício e raça/espécie do protagonista que existam NESTE universo e
  combinem com o gênero e a premissa. Se o universo não tiver isso, deixe "".
- starting_skills: de 1 a 3 habilidades com que o protagonista começa, coerentes com quem ele é.
- starting_items: de 1 a 4 itens iniciais (roupa, arma, ferramenta, dinheiro...). Item que se usa no corpo
  tem "slot" (ex.: "mao", "corpo", "cabeca") e pode ter "bonus" ({"nome do atributo": número}) e
  "equipped": true se ele já começa usando. Itens comuns: "slot": "".
- world_facts: de 2 a 5 fatos curtos e importantes do universo. Um deles diz como funciona a morte
  (permanente, ressurreição, reencarnação...).
- companions: só se a premissa tiver uma turma, grupo ou companheiros (senão, lista vazia []).
  Crie de 2 a 6 pessoas REALMENTE diferentes: personalidade, objetivo, laço com o protagonista e
  valores de atributos próprios (use os mesmos nomes de atributos). Nada de cópias com nomes trocados.
- Escreva em português do Brasil.
"""


def build_setup_messages(brief: CampaignBrief, system_window: bool = True) -> list[ChatMessage]:
    lines = [f"Título: {brief.title}"]
    if brief.genre_tags:
        lines.append(f"Gêneros: {', '.join(brief.genre_tags)}")
    lines.append(f"Premissa: {brief.player_visible.get('premise') or '(livre: invente uma)'}")
    lines.append("Janela de status: " + ("SIM (o protagonista vê números e avisos de sistema, estilo jogo)."
                                         if system_window else "NÃO (sem números visíveis no mundo; atributos mais narrativos)."))
    if brief.gm_secret:
        lines.append("Segredos do mestre (para manter coerência; não os revele na premissa nem no nome):")
        lines += [f"- {value}" for value in brief.gm_secret.values()]
    return [ChatMessage("system", SETUP_RULES), ChatMessage("user", "\n".join(lines) + "\n\nResponda só com o JSON.")]
