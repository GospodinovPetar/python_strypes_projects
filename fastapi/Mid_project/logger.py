# logger.py
import os
import logging

# 1) Make sure logs/ exists
os.makedirs("logs", exist_ok=True)

# 2) Define your app log file path (static)
LOG_FILE = "logs/app.log"

# 3) Create a named logger for your application
logger = logging.getLogger("news_api")
logger.setLevel(logging.INFO)

# 4) Attach just one FileHandler (append mode, same file every time)
fh = logging.FileHandler(LOG_FILE, mode="a")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

logger.addHandler(fh)
