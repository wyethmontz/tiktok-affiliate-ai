"""In-memory job store for tracking ad generation jobs.

Swappable to Redis or Supabase-backed store for production.
"""
import uuid
from datetime import datetime, timezone
from threading import Lock


class JobStore:
    def __init__(self):
        self._jobs: dict[str, dict] = {}
        self._lock = Lock()

    def create_job(self, input_data: dict) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": "pending",
                "current_step": None,
                "input": input_data,
                "result": None,
                "error": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
            }
        return job_id

    def update_step(self, job_id: str, step: str):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "processing"
                self._jobs[job_id]["current_step"] = step

    def complete_job(self, job_id: str, result: dict):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "completed"
                self._jobs[job_id]["result"] = result
                self._jobs[job_id]["current_step"] = None
                self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

    def fail_job(self, job_id: str, error: str):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = "failed"
                self._jobs[job_id]["error"] = error
                self._jobs[job_id]["current_step"] = None
                self._jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            return self._jobs.get(job_id)


# Singleton instance
jobs = JobStore()
