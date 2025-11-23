import logging
import traceback


def log_error(e):
    logging.error(f"Error: {e}")
    logging.error(traceback.format_exc())   

def log_info(message):
    logging.info(message)