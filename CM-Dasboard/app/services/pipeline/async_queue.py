import asyncio
import logging
import json
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AsyncQueue:
    """
    Mock background task queue.
    Replaces Celery/Redis for a clean local environment.
    Executes post-decision tasks asynchronously.
    """
    def __init__(self):
        self.queue = asyncio.Queue()
        self.workers = []
        
        # Ensure log dir exists
        os.makedirs("logs", exist_ok=True)
        self.pipeline_log = "logs/pipeline.log"

    async def start_workers(self, num_workers: int = 2):
        """Starts background worker tasks."""
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(i))
            self.workers.append(task)
        logger.info(f"Started {num_workers} async background workers.")

    async def stop_workers(self):
        """Stops background worker tasks."""
        for task in self.workers:
            task.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers = []

    async def dispatch(self, payload: Dict[str, Any]):
        """Pushes a task onto the queue."""
        await self.queue.put(payload)
        
    async def _worker(self, worker_id: int):
        """Processes tasks from the queue continuously."""
        while True:
            try:
                task_payload = await self.queue.get()
                
                incident_id = task_payload.get("incident_id", "UNKNOWN")
                team = task_payload.get("assigned_team", "NONE")
                
                # Mock async execution delay (e.g. sending emails, DB writes)
                await asyncio.sleep(0.1) 
                
                log_msg = f"[Worker-{worker_id}] DISPATCHED Incident {incident_id} -> {team}\n"
                
                # Log to pipeline.log
                with open(self.pipeline_log, "a") as f:
                    f.write(log_msg)
                    
                # We could also write decisions to decisions.json here
                self._record_decision(task_payload)
                
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker-{worker_id} encountered an error: {e}")
                
    def _record_decision(self, decision: Dict[str, Any]):
        """Records the final executed decision to outputs/decisions.json"""
        os.makedirs("outputs", exist_ok=True)
        file_path = "outputs/decisions.json"
        
        decisions = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    decisions = json.load(f)
            except json.JSONDecodeError:
                pass
                
        decisions.append(decision)
        
        with open(file_path, "w") as f:
            json.dump(decisions, f, indent=4)
