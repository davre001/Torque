"""Single-job worker with independent lease renewal and cooperative shutdown."""
import logging
import threading
from backend.models import Cancelled, LeaseLost, Status

log = logging.getLogger(__name__)

class Worker:
    def __init__(self, store, settings, processor):
        self.store, self.settings, self.processor = store, settings, processor
        self.stopping = threading.Event()

    def stop(self, *_):
        self.stopping.set()

    def once(self):
        claimed = self.store.claim(self.settings.lease_seconds)
        if claimed is None:
            return False
        run_id, owner = claimed
        finished, lost = threading.Event(), threading.Event()

        def renew():
            while not finished.wait(self.settings.heartbeat_seconds):
                try:
                    self.store.heartbeat(run_id,owner,self.settings.lease_seconds)
                except Exception:
                    lost.set()
                    return

        def checkpoint():
            if lost.is_set():
                raise LeaseLost("Lease renewal failed")
            if self.stopping.is_set():
                raise InterruptedError("Worker shutdown requested")
            if self.store.get(run_id)["cancel_requested"]:
                raise Cancelled("Cancellation requested")
            # Validate ownership even between heartbeat ticks.
            self.store.heartbeat(run_id,owner,self.settings.lease_seconds)

        thread = threading.Thread(target=renew,daemon=True,name="torque-lease")
        thread.start()
        try:
            checkpoint()
            self.processor(self.store,run_id,owner,checkpoint)
            record = self.store.get(run_id)
            if record["status"] not in {"failed","cancelled","interrupted","completed","ready_to_publish"}:
                self.store.update(run_id,owner,Status.FAILED,error="Processor returned without a final outcome")
        except LeaseLost:
            log.warning("Lost job lease: %s",run_id)
        except Cancelled:
            self._finish(run_id,owner,Status.CANCELLED)
        except InterruptedError:
            self._finish(run_id,owner,Status.INTERRUPTED,"Worker shutdown requested")
        except Exception:
            # Exceptions may include API credentials; do not store raw messages.
            self._finish(run_id,owner,Status.FAILED,"Execution failed; check backend configuration and integration readiness")
            log.error("Job failed: %s",run_id)
        finally:
            finished.set()
            thread.join(timeout=self.settings.heartbeat_seconds+1)
        return True

    def _finish(self, run_id, owner, status, error=None):
        try:
            self.store.update(run_id,owner,status,error=error)
        except LeaseLost:
            log.warning("Outcome rejected after lease loss: %s",run_id)

    def run(self):
        while not self.stopping.is_set():
            if not self.once():
                self.stopping.wait(self.settings.poll_seconds)
