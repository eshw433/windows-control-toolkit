from __future__ import annotations

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from loguru import logger

from wct.db.repositories import BandwidthRepository, EventRepository, ProcessIdentityRepository
from wct.modules.network.bandwidth import BandwidthTracker, TrafficSummary


class BandwidthWorker(QThread):
    sample_ready = pyqtSignal(dict)

    def __init__(self, *, interval_sec: float = 3.0) -> None:
        super().__init__()
        self._interval = interval_sec
        self._tracker = BandwidthTracker()
        self._summary = TrafficSummary()
        self._stop = False

    def run(self) -> None:
        logger.info("BandwidthWorker started")
        while not self._stop:
            try:
                slices = self._tracker.sample()
                for s in slices:
                    self._summary.add_slice(s)
                self._emit_snapshot(slices)
            except Exception as exc:
                logger.warning("Bandwidth sample failed: {}", exc)
            self.sleep(int(self._interval))
        logger.info("BandwidthWorker stopped")

    def _emit_snapshot(self, slices) -> None:
        rate_sent = sum(s.rate_sent for s in slices)
        rate_recv = sum(s.rate_recv for s in slices)
        rows = []
        totals = self._tracker.totals()
        for s in slices:
            ts, tr = totals.get(s.exe, (0, 0))
            rows.append({
                "exe": s.exe,
                "name": s.name,
                "rate_sent": s.rate_sent,
                "rate_recv": s.rate_recv,
                "total_sent": ts,
                "total_recv": tr,
            })
        self.sample_ready.emit({
            "rate_sent": rate_sent,
            "rate_recv": rate_recv,
            "total_sent": self._summary.bytes_sent,
            "total_recv": self._summary.bytes_recv,
            "rows": rows,
        })

    def stop(self) -> None:
        self._stop = True

    def reset(self) -> None:
        self._summary.reset()
        self._tracker.reset_totals()


class BandwidthService(QObject):
    tick = pyqtSignal(dict)

    def __init__(self, bandwidth_repo: BandwidthRepository,
                 events_repo: EventRepository,
                 process_repo: ProcessIdentityRepository | None = None,
                 *, persist_every: int = 5) -> None:
        super().__init__()
        self._repo = bandwidth_repo
        self._events_repo = events_repo
        self._process_repo = process_repo
        self._worker = BandwidthWorker()
        self._worker.sample_ready.connect(self._on_sample)
        self._persist_every = max(1, persist_every)
        self._counter = 0

    def start(self) -> None:
        self._worker.start()

    def stop(self) -> None:
        self._worker.stop()
        self._worker.wait(2000)

    def reset(self) -> None:
        self._worker.reset()

    def _on_sample(self, payload: dict) -> None:
        self.tick.emit(payload)
        self._counter += 1
        if self._counter % self._persist_every == 0 and self._process_repo is not None:
            try:
                for r in payload.get("rows", []):
                    proc = self._process_repo.find_by_path(r.get("exe", ""))
                    if not proc:
                        continue
                    self._repo.add_to_day(
                        process_id=int(proc["id"]),
                        bytes_sent=int(r.get("rate_sent", 0)),
                        bytes_recv=int(r.get("rate_recv", 0)),
                    )
            except Exception as exc:
                logger.warning("Bandwidth persist failed: {}", exc)
