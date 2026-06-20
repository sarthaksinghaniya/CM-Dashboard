import asyncio
import logging
import signal
from app.engines.scheduler import SchedulerEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("cm_dashboard.scheduler_service")

async def main():
    engine = SchedulerEngine()
    engine.start()
    logger.info("[SCHEDULER_SERVICE] Standalone Scheduler Engine started successfully.")
    
    # Event to wait for shutdown signals
    stop_event = asyncio.Event()
    
    def handle_shutdown(sig, frame):
        logger.info(f"[SCHEDULER_SERVICE] Received signal {sig}. Initiating graceful shutdown...")
        stop_event.set()

    # Register signal handlers for clean container termination
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, handle_shutdown)
        except ValueError:
            # Signal handling might fail on some platforms/environments, ignore
            pass
            
    try:
        await stop_event.wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        engine.stop()
        logger.info("[SCHEDULER_SERVICE] Standalone Scheduler Engine stopped successfully.")

if __name__ == "__main__":
    asyncio.run(main())
