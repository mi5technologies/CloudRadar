"""Scheduled scan management.

Uses APScheduler (BackgroundScheduler) when available; falls back to a
simple threading.Timer-based scheduler otherwise.
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from cspm.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ScheduledJob:
    id: str
    cloud: str
    region: str
    cron_expr: str
    enabled: bool = True
    last_run: Optional[float] = None
    next_run: Optional[float] = None


# ---------------------------------------------------------------------------
# APScheduler-based implementation
# ---------------------------------------------------------------------------

try:
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
    from apscheduler.triggers.cron import CronTrigger  # type: ignore

    _HAS_APSCHEDULER = True
except ImportError:
    _HAS_APSCHEDULER = False
    logger.warning(
        "APScheduler not installed — scheduled scans will use threading.Timer fallback. "
        "Install with: pip install apscheduler>=3.10.0"
    )


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class SchedulerManager:
    """Manages periodic scan jobs.

    ``persist_callback`` is an optional callable that receives the current list
    of job dicts so the caller can persist them (e.g., to ``config.yaml``).
    """

    def __init__(
        self,
        scan_callback: Optional[Callable[[str, str], None]] = None,
        persist_callback: Optional[Callable[[list[dict]], None]] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._jobs: dict[str, ScheduledJob] = {}
        self._scan_callback = scan_callback or self._default_scan
        self._persist_callback = persist_callback
        self._running = False

        if _HAS_APSCHEDULER:
            self._scheduler: Any = BackgroundScheduler()
        else:
            self._scheduler = None
            self._timer_handles: dict[str, threading.Timer] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
        if _HAS_APSCHEDULER and self._scheduler is not None:
            try:
                self._scheduler.start()
                logger.info("APScheduler started")
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to start APScheduler: %s", exc)

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._running = False
        if _HAS_APSCHEDULER and self._scheduler is not None:
            try:
                self._scheduler.shutdown(wait=False)
                logger.info("APScheduler stopped")
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to stop APScheduler: %s", exc)
        else:
            for timer in list(self._timer_handles.values()):
                timer.cancel()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_job(self, cloud: str, region: str, cron_expr: str) -> str:
        job_id = uuid.uuid4().hex
        job = ScheduledJob(
            id=job_id,
            cloud=cloud,
            region=region,
            cron_expr=cron_expr,
        )
        with self._lock:
            self._jobs[job_id] = job

        if _HAS_APSCHEDULER and self._scheduler is not None:
            try:
                parts = cron_expr.strip().split()
                if len(parts) == 5:
                    minute, hour, day, month, day_of_week = parts
                    trigger = CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=day_of_week,
                    )
                else:
                    trigger = CronTrigger.from_crontab(cron_expr)

                self._scheduler.add_job(
                    self._run_job,
                    trigger=trigger,
                    id=job_id,
                    kwargs={"job_id": job_id},
                    replace_existing=True,
                )
                aps_job = self._scheduler.get_job(job_id)
                if aps_job and aps_job.next_run_time:
                    with self._lock:
                        self._jobs[job_id].next_run = aps_job.next_run_time.timestamp()
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to schedule job %s: %s", job_id, exc)
        else:
            self._schedule_timer(job_id)

        self._do_persist()
        logger.info("Added scheduled job %s (%s %s, cron=%s)", job_id, cloud, region, cron_expr)
        return job_id

    def remove_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id not in self._jobs:
                return False
            del self._jobs[job_id]

        if _HAS_APSCHEDULER and self._scheduler is not None:
            try:
                self._scheduler.remove_job(job_id)
            except Exception:
                pass
        else:
            timer = self._timer_handles.pop(job_id, None)
            if timer:
                timer.cancel()

        self._do_persist()
        return True

    def list_jobs(self) -> list[dict]:
        with self._lock:
            jobs = list(self._jobs.values())

        result = []
        for j in jobs:
            next_run = j.next_run
            if _HAS_APSCHEDULER and self._scheduler is not None:
                try:
                    aps_job = self._scheduler.get_job(j.id)
                    if aps_job and aps_job.next_run_time:
                        next_run = aps_job.next_run_time.timestamp()
                except Exception:
                    pass
            result.append({
                "id": j.id,
                "cloud": j.cloud,
                "region": j.region,
                "cron_expr": j.cron_expr,
                "enabled": j.enabled,
                "last_run": j.last_run,
                "next_run": next_run,
            })
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_job(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or not job.enabled:
                return
            job.last_run = time.time()

        logger.info("Running scheduled scan job %s", job_id)
        try:
            self._scan_callback(job.cloud, job.region)
        except Exception as exc:  # noqa: BLE001
            logger.error("Scheduled scan job %s failed: %s", job_id, exc)
        finally:
            self._do_persist()

    def _schedule_timer(self, job_id: str) -> None:
        """Very basic cron approximation using threading.Timer (fallback only)."""
        # Parse interval from cron: just use hourly as a safe default
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            return

        interval = 3600  # 1 hour default
        try:
            parts = job.cron_expr.strip().split()
            if len(parts) == 5 and parts[0].isdigit():
                interval = max(60, int(parts[0]) * 60)
        except Exception:
            pass

        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].next_run = time.time() + interval

        def _fire() -> None:
            self._run_job(job_id)
            # Re-schedule
            with self._lock:
                if job_id in self._jobs:
                    self._schedule_timer(job_id)

        timer = threading.Timer(interval, _fire)
        timer.daemon = True
        timer.start()
        self._timer_handles[job_id] = timer

    def _do_persist(self) -> None:
        if self._persist_callback is None:
            return
        try:
            self._persist_callback(self.list_jobs())
        except Exception as exc:  # noqa: BLE001
            logger.warning("Scheduler persist callback failed: %s", exc)

    @staticmethod
    def _default_scan(cloud: str, region: str) -> None:
        """Fallback scan runner — imports lazily to avoid circular deps."""
        try:
            from cspm.ui import jobs as jobs_module  # noqa: PLC0415

            jobs_module.start_scan_job(cloud=cloud, region=region)
        except Exception as exc:  # noqa: BLE001
            logger.error("Default scheduled scan failed: %s", exc)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

scheduler_manager = SchedulerManager()
