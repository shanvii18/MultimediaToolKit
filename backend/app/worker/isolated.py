"""
Run one conversion job in a separate child process with a memory watchdog.

Why: on a 512 MB server (Render Free) a heavy conversion used to push the *API process* over the
limit; the platform then killed the whole service, and every browser request failed with
"Failed to fetch" for ~2 minutes while it restarted. With isolation:
  - the API process stays small and keeps answering;
  - the watchdog stops the child (and its FFmpeg subprocesses) before the container limit is hit;
  - if the kernel OOM killer acts first, it picks the largest process, which is the child;
  - either way the job is marked failed with a clear message and is never retried in a crash loop.
"""
import logging
import multiprocessing
import time
from datetime import datetime

import psutil

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.entities import Job

logger = logging.getLogger(__name__)

TERMINAL = {"succeeded", "failed", "cancelled"}


def _child_main(job_id: str) -> None:  # pragma: no cover - runs in the child process
    from app.services.job_runner_service import job_runner_service

    job_runner_service.process_job(job_id, already_claimed=True)


def _read(path: str) -> str | None:
    try:
        with open(path, encoding="ascii") as f:
            return f.read().strip()
    except OSError:
        return None


def _stat_value(text: str | None, key: str) -> int:
    for line in (text or "").splitlines():
        name, _, value = line.partition(" ")
        if name == key and value.isdigit():
            return int(value)
    return 0


def container_memory_mb() -> tuple[float, float] | None:
    """(working set MB, limit MB) of this Linux container, or None when not in a limited cgroup.

    Working set = usage minus reclaimable file cache, as Kubernetes/Docker count it for OOM decisions."""
    usage = _read("/sys/fs/cgroup/memory.current")                      # cgroup v2
    if usage is not None:
        limit = _read("/sys/fs/cgroup/memory.max")
        inactive = _stat_value(_read("/sys/fs/cgroup/memory.stat"), "inactive_file")
    else:                                                                # cgroup v1
        usage = _read("/sys/fs/cgroup/memory/memory.usage_in_bytes")
        limit = _read("/sys/fs/cgroup/memory/memory.limit_in_bytes")
        inactive = _stat_value(_read("/sys/fs/cgroup/memory/memory.stat"), "total_inactive_file")
    if not usage or not usage.isdigit():
        return None
    limit_mb = settings.JOB_CONTAINER_LIMIT_MB or (
        int(limit) / 2**20 if limit and limit.isdigit() and int(limit) < 2**50 else 0)
    if not limit_mb:
        return None
    return max(0, int(usage) - inactive) / 2**20, float(limit_mb)


def _tree_rss_mb(proc: psutil.Process) -> float:
    total = proc.memory_info().rss
    for child in proc.children(recursive=True):
        try:
            total += child.memory_info().rss
        except psutil.Error:
            pass
    return total / (1024 * 1024)


def _kill_tree(proc: psutil.Process) -> None:
    try:
        children = proc.children(recursive=True)
    except psutil.Error:
        children = []
    for p in children + [proc]:
        try:
            p.kill()
        except psutil.Error:
            pass


def _mark_failed(job_id: str, code: str, message: str) -> None:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job and job.status not in TERMINAL:
            job.status = "failed"
            job.error_code = code
            job.error_message = message
            job.progress_message = "Failed"
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


def run_job_isolated(job_id: str, memory_limit_mb: int | None = None, poll_seconds: float = 0.1) -> dict:
    """Execute ``job_id`` in a spawned child. Returns {"exitcode", "peak_mb", "killed_for_memory"}."""
    limit = settings.JOB_MEMORY_LIMIT_MB if memory_limit_mb is None else memory_limit_mb
    ctx = multiprocessing.get_context("spawn")      # never fork a multi-threaded server process
    child = ctx.Process(target=_child_main, args=(job_id,), name=f"mtk-job-{job_id[:8]}", daemon=True)
    child.start()
    peak, killed = 0.0, False
    use_cgroup = bool(limit) and memory_limit_mb is None and container_memory_mb() is not None
    try:
        ps = psutil.Process(child.pid)
        while child.is_alive():
            try:
                if use_cgroup:
                    used, cap = container_memory_mb() or (0.0, 0.0)
                    over = cap and used > cap - settings.JOB_CONTAINER_MARGIN_MB
                    what = f"container at {used:.0f} of {cap:.0f} MB"
                else:
                    used = _tree_rss_mb(ps)
                    over = limit and used > limit
                    what = f"{used:.0f} MB (limit {limit} MB)"
            except psutil.Error:
                break
            peak = max(peak, used)
            if over:
                killed = True
                logger.warning("Job %s stopped for memory: %s.", job_id, what)
                _kill_tree(ps)
                break
            child.join(poll_seconds)
    finally:
        child.join(30)
        if child.is_alive():  # pragma: no cover - defensive
            child.kill()
            child.join(5)

    exitcode = child.exitcode
    if killed or exitcode in (-9, 137):
        _mark_failed(job_id, "OUT_OF_MEMORY",
                     "This conversion needed more memory than the free server provides and was stopped. "
                     "Try a shorter text or a smaller/shorter file.")
    elif exitcode != 0:
        _mark_failed(job_id, "WORKER_CRASHED",
                     "The conversion process stopped unexpectedly. Please try again with a smaller input.")
    logger.info("Job %s child exited with %s (peak %.0f MB).", job_id, exitcode, peak)
    return {"exitcode": exitcode, "peak_mb": round(peak, 1), "killed_for_memory": killed}
