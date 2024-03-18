import logging

def create_logger() -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)