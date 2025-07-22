import logging

def setup_logger(log_path):
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        encoding="utf-8",
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
