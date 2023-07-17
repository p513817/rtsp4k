import logging
import colorlog

def init_logger() -> logging.Logger:

    # Get Default Logger
    logger = logging.getLogger()            # get logger

    # Double Check if logger exist
    if logger.hasHandlers():
        return logger
    
    # Set Default
    logger.setLevel(logging.DEBUG)          # set default level
    
    # Add Stream Handler
    formatter = colorlog.ColoredFormatter( "%(asctime)s %(log_color)s [%(levelname)-.4s] %(reset)s %(message)s ", "%y-%m-%d %H:%M:%S")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)

    return logger