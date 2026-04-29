from __future__ import annotations

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class _TaskSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(object)


class _TaskRunnable(QRunnable):
    def __init__(self, fn):
        super().__init__()
        self._fn = fn
        self.signals = _TaskSignals()

    def run(self) -> None:
        try:
            result = self._fn()
        except Exception as error:  # pragma: no cover - Qt thread callback
            self.signals.failed.emit(error)
            return
        self.signals.succeeded.emit(result)


class QtTaskRunner:
    def __init__(self) -> None:
        self._thread_pool = QThreadPool.globalInstance()
        self._active_tasks: set[_TaskRunnable] = set()

    def submit(self, fn, on_success, on_error) -> None:
        task = _TaskRunnable(fn)

        def cleanup() -> None:
            self._active_tasks.discard(task)

        def handle_success(result) -> None:
            cleanup()
            on_success(result)

        def handle_error(error) -> None:
            cleanup()
            if isinstance(error, Exception):
                on_error(error)
            else:
                on_error(RuntimeError(str(error)))

        task.signals.succeeded.connect(handle_success)
        task.signals.failed.connect(handle_error)
        self._active_tasks.add(task)
        self._thread_pool.start(task)
