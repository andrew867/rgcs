"""Process-based background job manager.

* Every job runs in its own ``multiprocessing`` process (spawn context —
  Qt-safe and Windows-compatible); the UI thread never runs long
  calculations.
* Progress, logs and results arrive over a single IPC queue, drained by
  :meth:`poll` (a QTimer calls it in the app; tests call it directly, so no
  Qt event loop is required).
* Job inputs are recorded verbatim; results are written to the workspace as
  content-addressed artifacts (immutable, deterministic ids). Errors are
  preserved as artifacts too (full traceback).
* Cancellation terminates the worker process; the job record survives.
"""
from __future__ import annotations

import multiprocessing as mp
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from PySide6.QtCore import QObject, Signal

from rgcs_desktop.jobs.workers import WORKERS, run_worker
from rgcs_desktop.workspaces import Workspace


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def terminal(self) -> bool:
        return self in (JobStatus.SUCCEEDED, JobStatus.FAILED,
                        JobStatus.CANCELLED)


@dataclass
class JobRecord:
    job_id: str
    name: str
    worker: str
    params: dict[str, Any]
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    log_lines: list[str] = field(default_factory=list)
    result: dict[str, Any] | None = None
    result_artifact: str | None = None
    error: str | None = None
    error_artifact: str | None = None
    submitted_at: float = field(default_factory=time.time)

    @property
    def log_text(self) -> str:
        return "\n".join(self.log_lines)


class JobManager(QObject):
    """Owns worker processes and the IPC queue; persists jobs to a workspace."""

    job_updated = Signal(str)   # job_id
    job_finished = Signal(str)  # job_id (terminal state reached)

    def __init__(self, workspace: Workspace | None = None, parent=None):
        super().__init__(parent)
        self.workspace = workspace
        self._ctx = mp.get_context("spawn")
        self._queue = self._ctx.Queue()
        self._jobs: dict[str, JobRecord] = {}
        self._procs: dict[str, mp.process.BaseProcess] = {}

    # -- API ------------------------------------------------------------
    def submit(self, worker: str, params: dict[str, Any],
               name: str | None = None) -> str:
        if worker not in WORKERS:
            raise ValueError(f"unknown worker {worker!r}")
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        rec = JobRecord(job_id=job_id, name=name or worker, worker=worker,
                        params=dict(params))
        self._jobs[job_id] = rec
        proc = self._ctx.Process(target=run_worker,
                                 args=(worker, dict(params), self._queue,
                                       job_id),
                                 daemon=True)
        self._procs[job_id] = proc
        proc.start()
        rec.status = JobStatus.RUNNING
        self._persist(rec)
        self.job_updated.emit(job_id)
        return job_id

    def cancel(self, job_id: str) -> None:
        rec = self._jobs[job_id]
        proc = self._procs.get(job_id)
        if rec.status.terminal:
            return
        if proc is not None and proc.is_alive():
            proc.terminate()
            proc.join(timeout=5.0)
        rec.status = JobStatus.CANCELLED
        rec.log_lines.append("cancelled by user")
        self._persist(rec)
        self.job_updated.emit(job_id)
        self.job_finished.emit(job_id)

    def job(self, job_id: str) -> JobRecord:
        return self._jobs[job_id]

    def jobs(self) -> list[JobRecord]:
        return sorted(self._jobs.values(), key=lambda r: r.submitted_at)

    def poll(self) -> None:
        """Drain the IPC queue and reap finished processes. Called by a
        QTimer in the app and directly by tests (no event loop needed)."""
        updated: set[str] = set()
        while True:
            try:
                job_id, kind, payload = self._queue.get_nowait()
            except Exception:
                break
            rec = self._jobs.get(job_id)
            if rec is None or rec.status.terminal:
                continue
            if kind == "progress":
                rec.progress = float(payload)
            elif kind == "log":
                rec.log_lines.append(str(payload))
            elif kind == "result":
                rec.result = payload
                rec.progress = 1.0
                rec.status = JobStatus.SUCCEEDED
                self._store_result(rec)
            elif kind == "error":
                rec.error = str(payload)
                rec.status = JobStatus.FAILED
                self._store_error(rec)
            updated.add(job_id)
        # reap processes that died without reporting (e.g. hard crash)
        for job_id, proc in list(self._procs.items()):
            rec = self._jobs[job_id]
            if rec.status is JobStatus.RUNNING and not proc.is_alive():
                # allow queued messages already drained above to have settled
                if rec.status is JobStatus.RUNNING:
                    exit_code = proc.exitcode
                    # a just-finished proc may still have messages in flight;
                    # only fail it if the queue is empty and exit was abnormal
                    if self._queue.empty():
                        if exit_code == 0:
                            # normal exit but result not yet seen: leave for
                            # the next poll unless it never arrives
                            if time.time() - rec.submitted_at > 60.0:
                                rec.error = "worker exited without a result"
                                rec.status = JobStatus.FAILED
                                self._store_error(rec)
                                updated.add(job_id)
                        else:
                            rec.error = (f"worker process died "
                                         f"(exit code {exit_code})")
                            rec.status = JobStatus.FAILED
                            self._store_error(rec)
                            updated.add(job_id)
            if rec.status.terminal and not proc.is_alive():
                proc.join(timeout=0.1)
                del self._procs[job_id]
        for job_id in updated:
            self._persist(self._jobs[job_id])
            self.job_updated.emit(job_id)
            if self._jobs[job_id].status.terminal:
                self.job_finished.emit(job_id)

    def wait(self, job_id: str, timeout_s: float = 60.0) -> JobRecord:
        """Block (polling) until the job reaches a terminal state."""
        deadline = time.time() + timeout_s
        rec = self._jobs[job_id]
        while not rec.status.terminal:
            if time.time() > deadline:
                raise TimeoutError(f"job {job_id} did not finish in "
                                   f"{timeout_s}s (status {rec.status})")
            self.poll()
            if not rec.status.terminal:
                time.sleep(0.02)
        return rec

    def shutdown(self) -> None:
        for job_id in list(self._procs):
            rec = self._jobs[job_id]
            if not rec.status.terminal:
                self.cancel(job_id)
        self._procs.clear()

    # -- persistence ------------------------------------------------------
    def _store_result(self, rec: JobRecord) -> None:
        if self.workspace is None or rec.result is None:
            return
        art = self.workspace.write_artifact(rec.result, kind="result")
        rec.result_artifact = art["artifact_id"]
        self.workspace.put_object(
            "result", f"{rec.name} ({rec.job_id})",
            {"job_id": rec.job_id, "worker": rec.worker,
             "artifact_id": art["artifact_id"], "sha256": art["sha256"],
             "params": rec.params},
            object_id=f"result-{rec.job_id}")

    def _store_error(self, rec: JobRecord) -> None:
        if self.workspace is None:
            return
        art = self.workspace.write_artifact(
            {"job_id": rec.job_id, "worker": rec.worker, "params": rec.params,
             "traceback": rec.error, "log": rec.log_lines},
            kind="error")
        rec.error_artifact = art["artifact_id"]

    def _persist(self, rec: JobRecord) -> None:
        if self.workspace is None:
            return
        self.workspace.record_job(
            rec.job_id, rec.name, rec.status.value, rec.params,
            progress=rec.progress, result_artifact=rec.result_artifact,
            error=rec.error, log=rec.log_text)
