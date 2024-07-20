import logging

BASE_FORMAT="%(asctime)s %(levelname)s %(message)s"
DATE_FORMAT="%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=BASE_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("log_result.txt", mode='a')
    ]
)