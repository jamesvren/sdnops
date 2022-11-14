import logging

def logger(name, level=logging.INFO):
    logging.basicConfig(level=level,format = '%(asctime)s - %(name)s [%(levelname)s]: %(message)s')
    return logging.getLogger(name)
