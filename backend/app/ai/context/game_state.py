"""Estado do jogo para a IA intérprete: regras, protagonista e a cena atual.

Os ids (UUID) viram apelidos curtos (e1, e2... para entidades; i1, i2... para itens).
Isso economiza contexto e reduz erros de modelos pequenos. O motor traduz os apelidos
de volta para os ids reais ao aplicar as operações.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engine.time import format_world_time
from app.persistence.models import Definition, Entity
from app.persistence.repositories import CampaignData

MAX_DEFINITIONS = 60
MAX_SCENE_ENTITIES = 15
MAX_ITEMS_PER_HOLDER = 20
MAX_CANON_FACTS = 40
STATUS_LABELS = {"confirmed": "confirmado", "rumor": "rumor", "false": "crença falsa"}


@dataclass
class GameStateSnapshot:
    text: str
    aliases: dict[str, str] = field(default_factory=dict)  # apelido -> id real
    player_id: str | None = None


class _Aliases:
    def __init__(self):
        self.by_id: dict[str, str] = {}
        self.counters = {"e": 0, "i": 0}

    def get(self, prefix: str, record_id: str) -> str:
        if record_id not in self.by_id:
            self.counters[prefix] += 1
            self.by_id[record_id] = f"{prefix}{self.counters[prefix]}"
        return self.by_id[record_id]

    def mapping(self) -> dict[str, str]:
        return {alias: record_id for record_id, alias in self.by_id.items()}


def build_game_state(data: CampaignData) -> GameStateSnapshot:
    aliases = _Aliases()
    lines: list[str] = [f"Tempo do mundo: {format_world_time(data.campaign().world_clock)}.", ""]

    definitions = data.definitions.list_current()
    if definitions:
        lines.append("Regras definidas nesta campanha (use estas chaves):")
        lines.extend(f"- {_describe_definition(d)}" for d in definitions[:MAX_DEFINITIONS])
        if len(definitions) > MAX_DEFINITIONS:
            lines.append(f"- ... e mais {len(definitions) - MAX_DEFINITIONS} definições.")
    else:
        lines.append("Nenhuma regra definida ainda (nenhum atributo, habilidade ou item).")

    facts = data.canon.list_current(MAX_CANON_FACTS)
    if facts:
        lines.append("")
        lines.append("Fatos do mundo já estabelecidos (não contradiga; para mudar use canon.amend):")
        lines.extend(f"- [{STATUS_LABELS.get(f.status, f.status)}] {f.key}: {f.statement}" for f in facts)

    player = data.entities.player()
    lines.append("")
    if player is None:
        lines.append("Ainda NÃO existe protagonista nesta campanha.")
        scene = data.entities.list()[:MAX_SCENE_ENTITIES]
        location = None
    else:
        location = data.entities.get(player.location_id) if player.location_id else None
        where = f"; local: {location.name} ({aliases.get('e', location.id)})" if location else "; local: indefinido"
        lines.append(f"Protagonista (use \"player\"): {player.name} — {player.kind}, {_status(player)}{where}")
        lines.extend(_entity_details(data, player, aliases))
        scene = data.entities.at_location(player.location_id) if player.location_id else []

    others = [e for e in scene if not e.is_player and (location is None or e.id != location.id)]
    if others:
        lines.append("")
        lines.append("Presentes na cena:" if player else "Entidades existentes:")
        for entity in others[:MAX_SCENE_ENTITIES]:
            lines.append(f"- {aliases.get('e', entity.id)}: {entity.name} — {entity.kind}, {_status(entity)}")
            lines.extend("  " + line for line in _entity_details(data, entity, aliases))
    if location is not None:
        floor = data.items.at_location(location.id)[:MAX_ITEMS_PER_HOLDER]
        if floor:
            lines.append(f"Itens soltos em {location.name}: " + ", ".join(_item(i, aliases) for i in floor))

    return GameStateSnapshot("\n".join(lines), aliases.mapping(), player.id if player else None)


def _status(entity: Entity) -> str:
    return {"active": "ativo", "dead": "MORTO"}.get(entity.status, entity.status)


def _entity_details(data: CampaignData, entity: Entity, aliases: _Aliases) -> list[str]:
    details = []
    attributes = data.attributes.for_entity(entity.id)
    if attributes:
        details.append("  atributos: " + ", ".join(
            f"{a.definition_key}={a.value}" + (f"/{a.max_value}" if a.max_value is not None else "") for a in attributes
        ))
    skills = data.skills.for_entity(entity.id)
    if skills:
        details.append("  habilidades: " + ", ".join(f"{s.definition_key} (nível {s.level})" for s in skills))
    items = data.items.held_by(entity.id)[:MAX_ITEMS_PER_HOLDER]
    if items:
        details.append("  itens: " + ", ".join(_item(i, aliases) for i in items))
    effects = data.effects.active_for(entity.id)
    if effects:
        details.append("  efeitos: " + ", ".join(
            e.definition_key + (f" (até {format_world_time(e.ends_at)})" if e.ends_at is not None else "") for e in effects
        ))
    return details


def _item(item, aliases: _Aliases) -> str:
    return f"{aliases.get('i', item.id)}={item.definition_key}×{item.quantity}"


def _describe_definition(definition: Definition) -> str:
    data = definition.data
    kind_names = {"attribute": "atributo", "skill": "habilidade", "item": "item"}
    label = f"{kind_names.get(definition.kind, definition.kind)} {definition.key}: {data.get('name', definition.key)}"
    extras = []
    if definition.kind == "attribute":
        extras.append(data.get("value_type", "decimal"))
        if data.get("resource"):
            extras.append("recurso com máximo")
        if data.get("scale"):
            extras.append("escala " + "<".join(data["scale"]))
        for bound in ("min", "max"):
            if bound in data:
                extras.append(f"{bound} {data[bound]}")
    elif definition.kind == "skill":
        if data.get("max_level"):
            extras.append(f"nível máx. {data['max_level']}")
        for cost in data.get("costs", []):
            extras.append(f"custa {cost['amount']} de {cost['resource']}")
    elif definition.kind == "item" and data.get("stackable") is False:
        extras.append("não empilhável")
    return label + (f" ({', '.join(extras)})" if extras else "")
