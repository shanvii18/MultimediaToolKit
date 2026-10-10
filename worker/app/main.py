import logging
import signal
import sys
import time
import redis
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [Worker] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("worker")

running = True


def handle_shutdown(signum, frame):
    global running
    logger.info("Received termination signal (%s). Shutting down worker gracefully...", signum)
    running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def main():
    logger.info("==================================================")
    logger.info("Starting %s (Day 1)", settings.PROJECT_NAME)
    logger.info("Target Redis URL: %s", settings.REDIS_URL)
    logger.info("Poll Interval: %ss", settings.POLL_INTERVAL_SECONDS)
    logger.info("==================================================")

    redis_client = None

    while running:
        try:
            if redis_client is None:
                logger.info("Attempting connection to Redis...")
                redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
                redis_client.ping()
                logger.info("Connected to Redis successfully.")

            # Heartbeat check and placeholder task listener
            logger.info("Worker heartbeat: active. Waiting for tasks in Redis queue...")
            time.sleep(settings.POLL_INTERVAL_SECONDS)

        except (redis.ConnectionError, redis.TimeoutError) as ce:
            logger.warning("Redis connection pending/unavailable (%s). Retrying in %ss...", ce, settings.POLL_INTERVAL_SECONDS)
            redis_client = None
            time.sleep(settings.POLL_INTERVAL_SECONDS)
        except Exception as ex:
            logger.error("Unexpected worker exception: %s", ex, exc_info=True)
            time.sleep(settings.POLL_INTERVAL_SECONDS)

    logger.info("Worker process terminated gracefully.")


if __name__ == "__main__":
    main()
