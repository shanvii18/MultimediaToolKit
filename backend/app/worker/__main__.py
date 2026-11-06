"""Standalone worker process: `python -m app.worker` (used by docker-compose)."""
import logging
import signal

from app.core.migrations import upgrade_database
from app.worker.runner import JobWorker

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] [Worker] %(message)s")


def main() -> None:
    upgrade_database()
    worker = JobWorker()

    def _shutdown(signum, frame):
        logging.info("Signal %s received; finishing current job then stopping.", signum)
        worker._stop.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    worker.run_forever()


if __name__ == "__main__":
    main()
