import logging
from pathlib import Path

# Ensure the logs directory exists next to this file
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "app.log"

# Configure logging: file + console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)

# Module-level logger
logger = logging.getLogger("app")
