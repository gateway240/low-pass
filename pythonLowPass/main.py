# Logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Hello from pythonlowpass!")


if __name__ == "__main__":
    main()
