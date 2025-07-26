import logging
from pathlib import Path

log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

logger.addFilter(lambda record: record.levelno == logging.INFO)
