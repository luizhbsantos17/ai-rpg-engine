"""Repositórios do mundo: definições, entidades, atributos, habilidades, itens e rolagens."""

from __future__ import annotations

from typing import Any

from sqlalchemy import or_, select

from app.persistence.models import (
    AdminAudit,
    CampaignSetting,
    CanonFact,
    Definition,
    DiceRollRecord,
    Disguise,
    Effect,
    Entity,
    EntityAttribute,
    EntitySkill,
    ItemInstance,
    Knowledge,
    NpcMemory,
    Quest,
    Relationship,
    RelationshipEvent,
    ScheduledEvent,
)
from app.persistence.repositories.base import CampaignScopedRepository


class QuestRepository(CampaignScopedRepository[Quest]):
    model = Quest

    def by_key(self, key: str) -> Quest | None:
        return self.session.scalars(self._select().where(Quest.key == key)).first()

    def list(self, include_hidden: bool = True, only_active: bool = False) -> list[Quest]:
        query = self._select()
        if not include_hidden:
            query = query.where(Quest.hidden.is_(False))
        if only_active:
            query = query.where(Quest.status == "active")
        return list(self.session.scalars(query.order_by(Quest.created_at)))


class DisguiseRepository(CampaignScopedRepository[Disguise]):
    model = Disguise

    def active_for(self, entity_id: str) -> list[Disguise]:
        query = self._select().where(Disguise.entity_id == entity_id, Disguise.active.is_(True))
        return list(self.session.scalars(query.order_by(Disguise.field)))

    def for_field(self, entity_id: str, field: str) -> Disguise | None:
        """Ocultação que vale para o campo: a específica dele ou a geral ("*")."""
        active = {d.field: d for d in self.active_for(entity_id)}
        return active.get(field) or active.get("*")

    def upsert(self, entity_id: str, field: str, presented_value: str | None, power: str) -> Disguise:
        query = self._select().where(Disguise.entity_id == entity_id, Disguise.field == field)
        disguise = self.session.scalars(query).first()
        if disguise is None:
            return self.add(Disguise(entity_id=entity_id, field=field, presented_value=presented_value, power=power))
        disguise.presented_value, disguise.power, disguise.active = presented_value, power, True
        self.session.flush()
        return disguise


class KnowledgeRepository(CampaignScopedRepository[Knowledge]):
    model = Knowledge

    def get_for(self, observer_id: str, subject: str, field: str) -> Knowledge | None:
        query = self._select().where(Knowledge.observer_id == observer_id, Knowledge.subject == subject,
                                     Knowledge.field == field)
        return self.session.scalars(query).first()

    def known_by(self, observer_id: str, subject: str | None = None) -> list[Knowledge]:
        query = self._select().where(Knowledge.observer_id == observer_id)
        if subject is not None:
            query = query.where(Knowledge.subject == subject)
        return list(self.session.scalars(query.order_by(Knowledge.subject, Knowledge.field)))

    def upsert(self, observer_id: str, subject: str, field: str, value, level: str, source: str) -> Knowledge:
        record = self.get_for(observer_id, subject, field)
        if record is None:
            return self.add(Knowledge(observer_id=observer_id, subject=subject, field=field,
                                      known_value=value, level=level, source=source))
        record.known_value, record.level, record.source = value, level, source
        self.session.flush()
        return record


class NpcMemoryRepository(CampaignScopedRepository[NpcMemory]):
    model = NpcMemory

    def remember(self, npc_id: str, content: str, importance: int, world_time: int, turn_id) -> NpcMemory:
        return self.add(NpcMemory(npc_id=npc_id, content=content, importance=importance,
                                  world_time=world_time, turn_id=turn_id))

    def recall(self, npc_id: str, limit: int = 5) -> list[NpcMemory]:
        """As lembranças mais importantes e recentes, em ordem cronológica."""
        query = (self._select().where(NpcMemory.npc_id == npc_id)
                 .order_by(NpcMemory.importance.desc(), NpcMemory.created_at.desc()).limit(limit))
        return sorted(self.session.scalars(query), key=lambda m: m.created_at)


class RelationshipRepository(CampaignScopedRepository[Relationship]):
    model = Relationship

    def between(self, source_id: str, target_id: str) -> Relationship | None:
        query = self._select().where(Relationship.source_id == source_id, Relationship.target_id == target_id)
        return self.session.scalars(query).first()

    def get_or_create(self, source_id: str, target_id: str) -> Relationship:
        return self.between(source_id, target_id) or self.add(Relationship(source_id=source_id, target_id=target_id))

    def involving(self, entity_id: str) -> list[Relationship]:
        query = self._select().where(or_(Relationship.source_id == entity_id, Relationship.target_id == entity_id))
        return list(self.session.scalars(query.order_by(Relationship.created_at)))

    def record_change(self, relationship: Relationship, changes: dict, cause: str, turn_id, world_time: int) -> RelationshipEvent:
        event = RelationshipEvent(relationship_id=relationship.id, changes=changes, cause=cause,
                                  turn_id=turn_id, world_time=world_time, campaign_id=self.campaign_id)
        self.session.add(event)
        self.session.flush()
        return event

    def history(self, relationship_id: str) -> list[RelationshipEvent]:
        query = select(RelationshipEvent).where(
            RelationshipEvent.campaign_id == self.campaign_id, RelationshipEvent.relationship_id == relationship_id
        )
        return list(self.session.scalars(query.order_by(RelationshipEvent.created_at)))


class AdminAuditRepository(CampaignScopedRepository[AdminAudit]):
    model = AdminAudit

    def last_undoable(self) -> AdminAudit | None:
        """O comando mais recente que ainda pode ser desfeito.

        Filtrado em Python: um JSON vazio pode estar gravado como `null` (JSON), que o SQL não vê como NULL.
        """
        query = self._select().where(AdminAudit.undone.is_(False)).order_by(AdminAudit.created_at.desc()).limit(50)
        return next((row for row in self.session.scalars(query) if row.undo_operations), None)

    def latest(self, limit: int = 20) -> list[AdminAudit]:
        return list(self.session.scalars(self._select().order_by(AdminAudit.created_at.desc()).limit(limit)))


class SettingsRepository(CampaignScopedRepository[CampaignSetting]):
    model = CampaignSetting

    def current(self, kind: str) -> CampaignSetting | None:
        query = self._select().where(CampaignSetting.kind == kind).order_by(CampaignSetting.version.desc()).limit(1)
        return self.session.scalars(query).first()

    def save(self, kind: str, data: dict[str, Any]) -> CampaignSetting:
        previous = self.current(kind)
        return self.add(CampaignSetting(kind=kind, data=data, version=(previous.version + 1) if previous else 1))

    def history(self, kind: str) -> list[CampaignSetting]:
        query = self._select().where(CampaignSetting.kind == kind).order_by(CampaignSetting.version)
        return list(self.session.scalars(query))


class ScheduledEventRepository(CampaignScopedRepository[ScheduledEvent]):
    model = ScheduledEvent

    def due(self, until: int) -> list[ScheduledEvent]:
        """Pendentes com data até `until`, na ordem em que vencem."""
        query = self._select().where(
            ScheduledEvent.status == ScheduledEvent.STATUS_PENDING, ScheduledEvent.due_at <= until
        )
        return list(self.session.scalars(query.order_by(ScheduledEvent.due_at, ScheduledEvent.created_at)))

    def pending(self) -> list[ScheduledEvent]:
        query = self._select().where(ScheduledEvent.status == ScheduledEvent.STATUS_PENDING)
        return list(self.session.scalars(query.order_by(ScheduledEvent.due_at)))


class EffectRepository(CampaignScopedRepository[Effect]):
    model = Effect

    def active_for(self, entity_id: str) -> list[Effect]:
        query = self._select().where(Effect.target_id == entity_id, Effect.active.is_(True))
        return list(self.session.scalars(query.order_by(Effect.starts_at)))

    def active_by_key(self, entity_id: str, key: str) -> Effect | None:
        query = self._select().where(Effect.target_id == entity_id, Effect.definition_key == key, Effect.active.is_(True))
        return self.session.scalars(query).first()

    def expiring(self, until: int) -> list[Effect]:
        query = self._select().where(Effect.active.is_(True), Effect.ends_at.is_not(None), Effect.ends_at <= until)
        return list(self.session.scalars(query.order_by(Effect.ends_at)))


class DefinitionRepository(CampaignScopedRepository[Definition]):
    model = Definition

    def current(self, kind: str, key: str) -> Definition | None:
        query = self._select().where(Definition.kind == kind, Definition.key == key, Definition.is_current.is_(True))
        return self.session.scalars(query).first()

    def current_by_key(self, key: str) -> Definition | None:
        """Definição atual com essa chave, de qualquer tipo (chaves são únicas por tipo)."""
        query = self._select().where(Definition.key == key, Definition.is_current.is_(True))
        return self.session.scalars(query.order_by(Definition.kind)).first()

    def list_current(self, kind: str | None = None) -> list[Definition]:
        query = self._select().where(Definition.is_current.is_(True))
        if kind:
            query = query.where(Definition.kind == kind)
        return list(self.session.scalars(query.order_by(Definition.kind, Definition.key)))

    def history(self, kind: str, key: str) -> list[Definition]:
        query = self._select().where(Definition.kind == kind, Definition.key == key)
        return list(self.session.scalars(query.order_by(Definition.version)))

    def create(self, kind: str, key: str, data: dict[str, Any], created_by: str) -> Definition:
        return self.add(Definition(kind=kind, key=key, version=1, data=data, created_by=created_by))

    def amend(self, previous: Definition, data: dict[str, Any], created_by: str) -> Definition:
        """Nova versão; a anterior fica guardada e deixa de ser a atual."""
        previous.is_current = False
        self.session.flush()
        return self.add(
            Definition(
                kind=previous.kind, key=previous.key, version=previous.version + 1,
                data=data, supersedes_id=previous.id, created_by=created_by,
            )
        )


class CanonRepository(CampaignScopedRepository[CanonFact]):
    model = CanonFact

    def current(self, key: str) -> CanonFact | None:
        query = self._select().where(CanonFact.key == key, CanonFact.is_current.is_(True))
        return self.session.scalars(query).first()

    def list_current(self, limit: int | None = None) -> list[CanonFact]:
        query = self._select().where(CanonFact.is_current.is_(True)).order_by(CanonFact.created_at.desc())
        if limit is not None:
            query = query.limit(limit)
        return list(reversed(list(self.session.scalars(query))))

    def history(self, key: str) -> list[CanonFact]:
        return list(self.session.scalars(self._select().where(CanonFact.key == key).order_by(CanonFact.version)))

    def assert_fact(self, key: str, subject: str, statement: str, status: str, created_by: str) -> CanonFact:
        return self.add(CanonFact(key=key, subject=subject, statement=statement, status=status, created_by=created_by))

    def amend(self, previous: CanonFact, statement: str, status: str, reason: str, created_by: str) -> CanonFact:
        previous.is_current = False
        self.session.flush()
        return self.add(CanonFact(
            key=previous.key, subject=previous.subject, statement=statement, status=status,
            version=previous.version + 1, supersedes_id=previous.id, reason=reason, created_by=created_by,
        ))


class EntityRepository(CampaignScopedRepository[Entity]):
    model = Entity

    def player(self) -> Entity | None:
        query = self._select().where(Entity.is_player.is_(True), Entity.status != Entity.STATUS_REMOVED)
        return self.session.scalars(query.order_by(Entity.created_at)).first()

    def list(self, kind: str | None = None, include_removed: bool = False) -> list[Entity]:
        query = self._select()
        if kind:
            query = query.where(Entity.kind == kind)
        if not include_removed:
            query = query.where(Entity.status != Entity.STATUS_REMOVED)
        return list(self.session.scalars(query.order_by(Entity.created_at)))

    def at_location(self, location_id: str) -> list[Entity]:
        query = self._select().where(Entity.location_id == location_id, Entity.status != Entity.STATUS_REMOVED)
        return list(self.session.scalars(query.order_by(Entity.created_at)))


class AttributeRepository(CampaignScopedRepository[EntityAttribute]):
    model = EntityAttribute

    def get_for(self, entity_id: str, key: str) -> EntityAttribute | None:
        query = self._select().where(EntityAttribute.entity_id == entity_id, EntityAttribute.definition_key == key)
        return self.session.scalars(query).first()

    def for_entity(self, entity_id: str) -> list[EntityAttribute]:
        query = self._select().where(EntityAttribute.entity_id == entity_id)
        return list(self.session.scalars(query.order_by(EntityAttribute.definition_key)))

    def upsert(self, entity_id: str, key: str, value: str, max_value: str | None = None) -> EntityAttribute:
        attribute = self.get_for(entity_id, key)
        if attribute is None:
            return self.add(EntityAttribute(entity_id=entity_id, definition_key=key, value=value, max_value=max_value))
        attribute.value = value
        if max_value is not None:
            attribute.max_value = max_value
        self.session.flush()
        return attribute


class SkillRepository(CampaignScopedRepository[EntitySkill]):
    model = EntitySkill

    def get_for(self, entity_id: str, key: str) -> EntitySkill | None:
        query = self._select().where(EntitySkill.entity_id == entity_id, EntitySkill.definition_key == key)
        return self.session.scalars(query).first()

    def for_entity(self, entity_id: str, only_active: bool = True) -> list[EntitySkill]:
        query = self._select().where(EntitySkill.entity_id == entity_id)
        if only_active:
            query = query.where(EntitySkill.active.is_(True))
        return list(self.session.scalars(query.order_by(EntitySkill.acquired_at)))


class ItemRepository(CampaignScopedRepository[ItemInstance]):
    model = ItemInstance

    def held_by(self, entity_id: str) -> list[ItemInstance]:
        query = self._select().where(ItemInstance.owner_id == entity_id, ItemInstance.status == ItemInstance.STATUS_ACTIVE)
        return list(self.session.scalars(query.order_by(ItemInstance.created_at)))

    def at_location(self, location_id: str) -> list[ItemInstance]:
        query = self._select().where(
            ItemInstance.location_id == location_id, ItemInstance.status == ItemInstance.STATUS_ACTIVE
        )
        return list(self.session.scalars(query.order_by(ItemInstance.created_at)))

    def active_ids_conflicting(self) -> list[ItemInstance]:
        """Itens ativos sem dono e sem local, ou com os dois ao mesmo tempo (inconsistência)."""
        query = self._select().where(
            ItemInstance.status == ItemInstance.STATUS_ACTIVE,
            or_(
                (ItemInstance.owner_id.is_(None) & ItemInstance.location_id.is_(None)),
                (ItemInstance.owner_id.is_not(None) & ItemInstance.location_id.is_not(None)),
            ),
        )
        return list(self.session.scalars(query))


class DiceRollRepository(CampaignScopedRepository[DiceRollRecord]):
    model = DiceRollRecord

    def record(self, expression: str, seed: int, result: int, context: dict[str, Any], turn_id: str | None) -> DiceRollRecord:
        return self.add(DiceRollRecord(expression=expression, seed=seed, result=result, context=context, turn_id=turn_id))

    def for_turn(self, turn_id: str) -> list[DiceRollRecord]:
        query = self._select().where(DiceRollRecord.turn_id == turn_id).order_by(DiceRollRecord.created_at)
        return list(self.session.scalars(query))
