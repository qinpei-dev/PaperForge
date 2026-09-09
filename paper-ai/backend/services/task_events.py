"""Small in-process event stream for asynchronous PaperForge tasks."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Condition
from time import monotonic
from typing import Any, Iterator


TERMINAL_EVENTS = {"task_completed", "task_failed"}


@dataclass(frozen=True)
class TaskEvent:
    sequence: int
    task_id: str
    event_type: str
    payload: dict[str, Any]


class TaskEventStore:
    """Thread-safe bounded event history shared by the in-process workers."""

    def __init__(
        self,
        max_events_per_task: int = 100,
        terminal_ttl_seconds: float = 300.0,
        max_completed_histories: int = 1000,
    ) -> None:
        self._events: dict[str, deque[TaskEvent]] = {}
        self._terminal_at: dict[str, float] = {}
        self._next_sequence = 1
        self._condition = Condition()
        self._max_events_per_task = max_events_per_task
        self._terminal_ttl_seconds = terminal_ttl_seconds
        self._max_completed_histories = max_completed_histories

    def publish_event(self, task_id: str, event_type: str, **payload: Any) -> TaskEvent:
        event_payload = {
            "status": payload.get("status"),
            "workflow_stage": payload.get("workflow_stage"),
            "progress": payload.get("progress"),
            "message": payload.get("message") or event_type,
            "timestamp": payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
        }
        event_payload.update({key: value for key, value in payload.items() if key not in event_payload})
        with self._condition:
            self._purge_expired_locked()
            event = TaskEvent(self._next_sequence, str(task_id), event_type, event_payload)
            self._next_sequence += 1
            task_key = str(task_id)
            history = self._events.setdefault(task_key, deque(maxlen=self._max_events_per_task))
            history.append(event)
            if event_type in TERMINAL_EVENTS:
                self._terminal_at[task_key] = monotonic()
                self._trim_completed_histories_locked()
            self._condition.notify_all()
            return event

    def has_events(self, task_id: str) -> bool:
        with self._condition:
            self._purge_expired_locked()
            return bool(self._events.get(str(task_id)))

    def subscribe_event(self, task_id: str, after_sequence: int = 0, timeout: float = 15.0) -> Iterator[TaskEvent | None]:
        """Yield replayable events; yield None periodically as an SSE keep-alive."""
        task_key = str(task_id)
        next_sequence = after_sequence + 1
        while True:
            event: TaskEvent | None = None
            with self._condition:
                self._purge_expired_locked()
                history = self._events.get(task_key, ())
                pending = [event for event in history if event.sequence >= next_sequence]
                if not pending:
                    self._condition.wait(timeout=timeout)
                    history = self._events.get(task_key, ())
                    pending = [event for event in history if event.sequence >= next_sequence]
                if not pending:
                    event = None
                else:
                    event = pending[0]
            if event is None:
                yield None
                continue
            next_sequence = event.sequence + 1
            yield event
            if event.event_type in TERMINAL_EVENTS:
                return

    def _purge_expired_locked(self) -> None:
        cutoff = monotonic() - self._terminal_ttl_seconds
        expired = [task_id for task_id, terminal_at in self._terminal_at.items() if terminal_at <= cutoff]
        for task_id in expired:
            self._events.pop(task_id, None)
            self._terminal_at.pop(task_id, None)

    def _trim_completed_histories_locked(self) -> None:
        overflow = len(self._terminal_at) - self._max_completed_histories
        if overflow <= 0:
            return
        for task_id, _ in sorted(self._terminal_at.items(), key=lambda item: item[1])[:overflow]:
            self._events.pop(task_id, None)
            self._terminal_at.pop(task_id, None)


event_store = TaskEventStore()


def publish_event(task_id: str, event_type: str, **payload: Any) -> TaskEvent:
    return event_store.publish_event(task_id, event_type, **payload)


def subscribe_event(task_id: str, after_sequence: int = 0, timeout: float = 15.0) -> Iterator[TaskEvent | None]:
    return event_store.subscribe_event(task_id, after_sequence=after_sequence, timeout=timeout)


def has_events(task_id: str) -> bool:
    return event_store.has_events(task_id)
