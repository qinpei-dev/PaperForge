from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, TypeVar


T = TypeVar("T")


class TaskWorker:
    """Small in-process worker for decoupling task execution from HTTP requests."""

    def __init__(self, max_workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="paperforge-task")

    def submit(self, function: Callable[..., T], *args: object, **kwargs: object) -> Future[T]:
        return self._executor.submit(function, *args, **kwargs)


task_worker = TaskWorker()
