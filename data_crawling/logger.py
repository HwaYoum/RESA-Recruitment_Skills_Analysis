# data_crawling/logger.py

import logging
import os
from data_crawling.constants import LOGGING_CONFIG

def setup_logger(name):
    # Get directory of current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_CONFIG.get('level', 'INFO'))
    
    # Formatter
    formatter = logging.Formatter(LOGGING_CONFIG.get('format'))
    
    # File Handler
    log_file = os.path.join(current_dir, LOGGING_CONFIG.get('filename', 'crawler.log'))
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Stream Handler (Console)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    
    # Add handlers if not already added
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        
    return logger
