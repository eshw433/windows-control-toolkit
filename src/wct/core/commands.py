from __future__ import annotations

import abc
from collections import deque
from typing import Any

from loguru import logger


class Command(abc.ABC):

    description: str = ""

    @abc.abstractmethod
    def execute(self) -> Any:
        ...

    @abc.abstractmethod
    def undo(self) -> Any:
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.description}>"


class CommandHistory:

    def __init__(self, max_size: int = 5000) -> None:
        self._history: deque[Command] = deque(maxlen=max_size)

    def execute(self, cmd: Command) -> Any:
        result = cmd.execute()
        self._history.append(cmd)
        logger.info("Command executed: {}", cmd)
        return result

    def undo_last(self) -> Command | None:
        if not self._history:
            return None
        cmd = self._history.pop()
        try:
            cmd.undo()
            logger.info("Command undone: {}", cmd)
        except Exception as exc:
            logger.error("Undo failed for {}: {}", cmd, exc)
            raise
        return cmd

    def undo_all(self) -> int:
        count = 0
        while self._history:
            self.undo_last()
            count += 1
        return count

    @property
    def history(self) -> list[Command]:
        return list(self._history)

    @property
    def size(self) -> int:
        return len(self._history)
