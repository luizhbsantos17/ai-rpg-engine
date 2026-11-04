"""Repositórios de turnos, mensagens, eventos e chamadas à IA."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select, update

from app.persistence.models import AiRequest, Event, Message, Turn
from app.persistence.repositories.base import CampaignScopedRepository
from app.persistence.types import utc_now


class TurnRepository(CampaignScopedRepository[Turn]):
    model = Turn

    def create(self, turn_id: str, player_input: str) -> Turn:
        turn = Turn(
            id=turn_id,
            number=self._next_value(Turn.number),
            player_input=player_input,
            status=Turn.STATUS_PROCESSING,
        )
        return self.add(turn)

    def list_ordered(self) -> list[Turn]:
        return list(self.session.scalars(self._select().order_by(Turn.number)))

    def count_completed(self) -> int:
        """Quantos turnos concluídos (contado pelo banco, sem carregar os turnos)."""
        query = select(func.count()).select_from(Turn).where(
            Turn.campaign_id == self.campaign_id, Turn.status == Turn.STATUS_COMPLETED)
        return self.session.scalar(query) or 0

    def completed_after(self, number: int, limit: int) -> list[Turn]:
        """Os primeiros `limit` turnos concluídos depois do turno `number`, em ordem."""
        query = (self._select().where(Turn.number > number, Turn.status == Turn.STATUS_COMPLETED)
                 .order_by(Turn.number).limit(limit))
        return list(self.session.scalars(query))

    def latest(self) -> Turn | None:
        return self.session.scalars(self._select().order_by(Turn.number.desc()).limit(1)).first()

    def find_processing(self) -> Turn | None:
        query = self._select().where(Turn.status == Turn.STATUS_PROCESSING).order_by(Turn.number)
        return self.session.scalars(query).first()

    def mark_completed(self, turn: Turn) -> None:
        turn.status = Turn.STATUS_COMPLETED
        turn.error = None
        turn.completed_at = utc_now()
        self.session.flush()

    def mark_failed(self, turn: Turn, error: str) -> None:
        turn.status = Turn.STATUS_FAILED
        turn.error = error
        self.session.flush()

    def mark_processing(self, turn: Turn) -> None:
        turn.status = Turn.STATUS_PROCESSING
        turn.error = None
        self.session.flush()


def fail_interrupted_turns(session, reason: str) -> int:
    """Ao iniciar: turnos que ficaram em `processing` (programa fechado no meio) viram `failed`.

    Única operação que atravessa campanhas, de propósito: é manutenção do programa
    inteiro, feita na inicialização, e só muda o status (D-012).
    """
    result = session.execute(
        update(Turn).where(Turn.status == Turn.STATUS_PROCESSING).values(
            status=Turn.STATUS_FAILED, error=reason
        )
    )
    return result.rowcount or 0


class MessageRepository(CampaignScopedRepository[Message]):
    model = Message

    def append(self, role: str, content: str, turn_id: str | None = None) -> Message:
        message = Message(role=role, content=content, turn_id=turn_id, seq=self._next_value(Message.seq))
        return self.add(message)

    def list_ordered(self, after_seq: int = 0, limit: int | None = None) -> list[Message]:
        query = self._select().where(Message.seq > after_seq).order_by(Message.seq)
        if limit is not None:
            query = query.limit(limit)
        return list(self.session.scalars(query))

    def with_role(self, role: str) -> list[Message]:
        return list(self.session.scalars(self._select().where(Message.role == role).order_by(Message.seq)))

    def recent(self, limit: int) -> list[Message]:
        """As `limit` mensagens mais recentes, em ordem cronológica."""
        query = self._select().order_by(Message.seq.desc()).limit(limit)
        return list(reversed(list(self.session.scalars(query))))

    def recent_from_completed_turns(self, limit: int) -> list[Message]:
        """Mensagens recentes de turnos concluídos (e avisos sem turno), em ordem cronológica.

        Usado para montar o contexto da IA: jogadas que falharam não entram na história.
        """
        query = (
            self._select()
            .outerjoin(Turn, Message.turn_id == Turn.id)
            .where(or_(Message.turn_id.is_(None), Turn.status == Turn.STATUS_COMPLETED))
            .order_by(Message.seq.desc())
            .limit(limit)
        )
        return list(reversed(list(self.session.scalars(query))))

    def for_turn(self, turn_id: str) -> list[Message]:
        query = self._select().where(Message.turn_id == turn_id).order_by(Message.seq)
        return list(self.session.scalars(query))


class EventRepository(CampaignScopedRepository[Event]):
    model = Event

    def record(
        self,
        type_: str,
        source: str,
        payload: dict[str, Any] | None = None,
        turn_id: str | None = None,
        world_time: int = 0,
    ) -> Event:
        event = Event(type=type_, source=source, payload=payload or {}, turn_id=turn_id, world_time=world_time)
        return self.add(event)

    def list_ordered(self, last: int | None = None) -> list[Event]:
        if last is None:
            return list(self.session.scalars(self._select().order_by(Event.seq)))
        query = self._select().order_by(Event.seq.desc()).limit(last)
        return list(reversed(list(self.session.scalars(query))))


class AiRequestRepository(CampaignScopedRepository[AiRequest]):
    model = AiRequest

    def record(self, **fields: Any) -> AiRequest:
        return self.add(AiRequest(**fields))

    def latest(self, limit: int = 10) -> list[AiRequest]:
        query = self._select().order_by(AiRequest.created_at.desc()).limit(limit)
        return list(self.session.scalars(query))
