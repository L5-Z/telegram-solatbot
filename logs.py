import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.handlers:
    _fmt = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _fh = logging.FileHandler("app.log")
    _fh.setFormatter(_fmt)
    logger.addHandler(_fh)

    _sh = logging.StreamHandler()
    _sh.setFormatter(_fmt)
    logger.addHandler(_sh)
