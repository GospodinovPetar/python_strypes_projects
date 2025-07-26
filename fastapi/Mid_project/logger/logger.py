import os
import logging

os.makedirs("logger/logs", exist_ok=True)

LOG_FILE = "logger/logs/app.log"

logger = logging.getLogger("news_api")
logger.setLevel(logging.INFO)

fh = logging.FileHandler(LOG_FILE, mode="a")
fh.setLevel(logging.INFO)
fh.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)

logger.addHandler(fh)
