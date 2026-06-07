from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from loguru import logger


class EventBus:

    _subscribers: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    @classmethod
    def subscribe(cls, event: str, callback: Callable[..., Any]) -> None:
        cls._subscribers[event].append(callback)
        logger.debug("EventBus: subscribed {} to '{}'", callback.__qualname__, event)

    @classmethod
    def unsubscribe(cls, event: str, callback: Callable[..., Any]) -> None:
        try:
            cls._subscribers[event].remove(callback)
        except ValueError:
            pass

    @classmethod
    def emit(cls, event: str, **kwargs: Any) -> None:
        for cb in cls._subscribers.get(event, []):
            try:
                cb(**kwargs)
            except Exception as exc:
                logger.error("EventBus: error in handler {} for '{}': {}", cb.__qualname__, event, exc)

    @classmethod
    def clear(cls) -> None:
        cls._subscribers.clear()
