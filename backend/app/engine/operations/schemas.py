"""Formato de cada operação primitiva (catálogo fechado, ARCHITECTURE §5.2).

Referências a entidades e itens (`entity`, `owner`, `to`...) aceitam:
- "player": o protagonista;
- um apelido criado nesta mesma lista com `ref` (ex.: criar "goblin_1" e depois atacá-lo);
- o id (UUID) de algo que já existe na campanha.
Números podem vir como número ou texto (ex.: "1e40"), sem teto artificial.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, TypeAdapter

Key = Annotated[str, StringConstraints(pattern=r"^[a-z0-9_]{1,100}$")]
Ref = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
Number = int | float | str
DEFINITION_KINDS = ("attribute", "skill", "item", "species", "class", "effect", "check_rule", "death_rule", "title")


class CheckCondition(BaseModel):
    """Aplica a operação só se o teste `check` (apelido de um check.request anterior) deu esse resultado."""

    model_config = ConfigDict(extra="forbid")
    check: Ref
    success: bool = True


class Operation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: Reason = ""
    when: CheckCondition | None = None


class DefinitionCreate(Operation):
    op: Literal["definition.create"]
    kind: Annotated[str, StringConstraints(pattern=r"^[a-z_]{1,40}$")]
    key: Key
    data: dict[str, Any]


class DefinitionAmend(Operation):
    op: Literal["definition.amend"]
    kind: Annotated[str, StringConstraints(pattern=r"^[a-z_]{1,40}$")]
    key: Key
    data: dict[str, Any]


class AttributeValue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: Number
    max: Number | None = None


class EntityCreate(Operation):
    op: Literal["entity.create"]
    ref: Ref | None = None
    kind: Annotated[str, StringConstraints(pattern=r"^[a-z_]{1,40}$")]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    location: Ref | None = None
    is_player: bool = False
    data: dict[str, Any] = Field(default_factory=dict)
    attributes: dict[Key, Number | AttributeValue] = Field(default_factory=dict)


class EntityUpdate(Operation):
    op: Literal["entity.update"]
    entity: Ref
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)] | None = None
    status: Literal["active", "dead"] | None = None
    data: dict[str, Any] = Field(default_factory=dict)  # mesclado ao que já existe


class EntityRemove(Operation):
    op: Literal["entity.remove"]
    entity: Ref


class EntityMove(Operation):
    op: Literal["entity.move"]
    entity: Ref
    to: Ref


class AttributeSet(Operation):
    op: Literal["attribute.set"]
    entity: Ref
    key: Key
    value: Number
    max: Number | None = None


class AttributeModify(Operation):
    op: Literal["attribute.modify"]
    entity: Ref
    key: Key
    delta: Number  # número ou fórmula (texto), ex.: "-forca * 2"


class ResourceSpend(Operation):
    op: Literal["resource.spend"]
    entity: Ref
    key: Key
    amount: Number


class ResourceRestore(Operation):
    op: Literal["resource.restore"]
    entity: Ref
    key: Key
    amount: Number


class SkillGrant(Operation):
    op: Literal["skill.grant"]
    entity: Ref
    key: Key
    level: int = Field(default=1, ge=0)
    data: dict[str, Any] = Field(default_factory=dict)


class SkillRevoke(Operation):
    op: Literal["skill.revoke"]
    entity: Ref
    key: Key


class SkillEvolve(Operation):
    op: Literal["skill.evolve"]
    entity: Ref
    key: Key
    levels: int = Field(default=1, ge=1)


class SkillUse(Operation):
    """Usa uma habilidade: o motor cobra os custos definidos nela (tudo ou nada)."""

    op: Literal["skill.use"]
    entity: Ref
    key: Key
    target: Ref | None = None


class ItemCreate(Operation):
    op: Literal["item.create"]
    ref: Ref | None = None
    key: Key
    owner: Ref | None = None
    location: Ref | None = None
    quantity: int = Field(default=1, ge=1)
    data: dict[str, Any] = Field(default_factory=dict)


class ItemTransfer(Operation):
    op: Literal["item.transfer"]
    item: Ref
    to_owner: Ref | None = None
    to_location: Ref | None = None
    quantity: int | None = Field(default=None, ge=1)  # None = tudo


class ItemDestroy(Operation):
    op: Literal["item.destroy"]
    item: Ref
    quantity: int | None = Field(default=None, ge=1)  # None = tudo


class CheckRequest(Operation):
    """Pede um teste ao motor. A IA define o que está em jogo; o MOTOR rola (D-005)."""

    op: Literal["check.request"]
    ref: Ref | None = None  # para outras operações consultarem o resultado depois
    actor: Ref
    target: Ref | None = None
    label: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    dice: Annotated[str, StringConstraints(max_length=100)] = "1d20"
    modifier: Number = 0  # número ou fórmula com atributos do ator/alvo
    difficulty: Number  # número ou fórmula
    critical_success: Number | None = None  # resultado natural mínimo para crítico (ex.: 20)
    critical_failure: Number | None = None  # resultado natural máximo para falha crítica (ex.: 1)


class CanonAssert(Operation):
    """Registra um fato do mundo (regra, história, quem governa...). Não pode contradizer em silêncio."""

    op: Literal["canon.assert"]
    key: Key
    subject: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    statement: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    status: Literal["confirmed", "rumor", "false"] = "confirmed"


class CanonAmend(Operation):
    """Muda um fato já registrado: cria nova versão; exige motivo (reason)."""

    op: Literal["canon.amend"]
    key: Key
    statement: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)] | None = None
    status: Literal["confirmed", "rumor", "false"] | None = None


Duration = int | Annotated[str, StringConstraints(max_length=30)]


class TimeAdvance(Operation):
    """Avança o relógio do mundo. Acontecimentos agendados e efeitos vencidos são processados."""

    op: Literal["time.advance"]
    duration: Duration  # minutos ou "30m", "4h", "2d"


class EventSchedule(Operation):
    """Agenda algo para o futuro do mundo; `operations` são aplicadas quando a data chegar."""

    op: Literal["event.schedule"]
    after: Duration  # daqui a quanto tempo
    summary: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    operations: list[dict[str, Any]] = Field(default_factory=list, max_length=20)


class EffectApply(Operation):
    """Aplica um efeito (envenenado, abençoado...) com duração opcional em tempo do mundo."""

    op: Literal["effect.apply"]
    target: Ref
    key: Key  # definição do tipo "effect"
    duration: Duration | None = None  # None = até ser removido
    intensity: Number | None = None
    source: Ref | None = None


class EffectRemove(Operation):
    op: Literal["effect.remove"]
    target: Ref
    key: Key


class RelationshipChange(Operation):
    """Muda o que `source` sente/pensa de `target` (direcional). Sempre com o acontecimento que causou."""

    op: Literal["relationship.change"]
    source: Ref
    target: Ref
    changes: dict[Key, int | float] = Field(default_factory=dict, max_length=10)  # dimensão -> variação
    add_labels: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]] = Field(
        default_factory=list, max_length=5)
    remove_labels: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]] = Field(
        default_factory=list, max_length=5)
    cause: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class KnowledgeRecord(Operation):
    """O que `observer` sabe (ou acha que sabe) sobre `subject`. Ninguém sabe tudo automaticamente."""

    op: Literal["knowledge.record"]
    observer: Ref
    subject: Ref  # "player", apelido/id de entidade, ou um tema livre ("mapa_perdido")
    field: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    value: Annotated[str, StringConstraints(max_length=1000)] | None = None
    level: Literal["unknown", "estimated", "partial", "confirmed", "false"] = "confirmed"
    source: Literal["presenciou", "ouviu", "descobriu", "contaram", "deduziu", "avaliou", "ja_sabia"] = "descobriu"


class MemoryRecord(Operation):
    """Uma lembrança na memória individual de um personagem."""

    op: Literal["memory.record"]
    entity: Ref
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    importance: int = Field(default=2, ge=1, le=5)


class EventRecord(Operation):
    """Acontecimento narrativo importante, sem mudança mecânica (SPEC 15.2)."""

    op: Literal["event.record"]
    summary: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    entities: list[Ref] = Field(default_factory=list, max_length=20)
    data: dict[str, Any] = Field(default_factory=dict)


AnyOperation = Annotated[
    DefinitionCreate | DefinitionAmend | EntityCreate | EntityUpdate | EntityRemove | EntityMove
    | AttributeSet | AttributeModify | ResourceSpend | ResourceRestore
    | SkillGrant | SkillRevoke | SkillEvolve | SkillUse | ItemCreate | ItemTransfer | ItemDestroy
    | CheckRequest | CanonAssert | CanonAmend | TimeAdvance | EventSchedule | EffectApply | EffectRemove
    | RelationshipChange | KnowledgeRecord | MemoryRecord | EventRecord,
    Field(discriminator="op"),
]

OPERATION_ADAPTER: TypeAdapter[AnyOperation] = TypeAdapter(AnyOperation)
OPERATION_NAMES = (
    "definition.create", "definition.amend", "entity.create", "entity.update", "entity.remove", "entity.move",
    "attribute.set", "attribute.modify", "resource.spend", "resource.restore",
    "skill.grant", "skill.revoke", "skill.evolve", "skill.use", "item.create", "item.transfer", "item.destroy",
    "check.request", "canon.assert", "canon.amend", "time.advance", "event.schedule",
    "effect.apply", "effect.remove", "relationship.change", "knowledge.record", "memory.record", "event.record",
)


def parse_operation(raw: Any) -> AnyOperation:
    return OPERATION_ADAPTER.validate_python(raw)
