from qtpy.QtCore import QObject, QThread, Signal, Slot

from .service import copy_items


_ACTIVE_COPY_THREADS = set()


def _release_thread(thread):
    _ACTIVE_COPY_THREADS.discard(thread)
    thread.deleteLater()


class CopyWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, sources, destination):
        super(CopyWorker, self).__init__()
        self.sources = list(sources)
        self.destination = destination

    @Slot()
    def run(self):
        try:
            result = copy_items(self.sources, self.destination)
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.finished.emit(result)


class CopyUiBridge(QObject):
    def __init__(self, on_finished, on_failed, parent=None):
        super(CopyUiBridge, self).__init__(parent)
        self._on_finished = on_finished
        self._on_failed = on_failed

    @Slot(object)
    def handle_finished(self, result):
        self._on_finished(result)

    @Slot(str)
    def handle_failed(self, message):
        self._on_failed(message)


def create_copy_job(sources, destination, on_finished, on_failed):
    thread = QThread()
    worker = CopyWorker(sources, destination)
    bridge = CopyUiBridge(on_finished, on_failed)
    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.finished.connect(bridge.handle_finished)
    worker.failed.connect(bridge.handle_failed)
    worker.finished.connect(worker.deleteLater)
    worker.failed.connect(worker.deleteLater)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    _ACTIVE_COPY_THREADS.add(thread)
    thread.finished.connect(
        lambda current=thread: _release_thread(current)
    )

    thread.start()
    return {
        "thread": thread,
        "worker": worker,
        "bridge": bridge,
    }
