from .setup_logging import create_logger
import socket


logger = create_logger()

def get_local_ip() -> str:
    try:
        host_name: str = socket.gethostname()
        local_ip: str = socket.gethostbyname(host_name)
        return local_ip
    except Exception as error:
        logger.error(f"An error occured while getting local IP: {error}")
        return None



