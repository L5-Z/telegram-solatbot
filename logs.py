import logging
import os


class FsyncFileHandler(logging.FileHandler):
    """FileHandler that fsyncs to disk after every emit so logs survive abrupt termination."""
    def emit(self, record):
        super().emit(record)
        if self.stream is not None:
            try:
                self.stream.flush()
                os.fsync(self.stream.fileno())
            except (OSError, ValueError):
                pass


logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.handlers:
    _fmt = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _fh = FsyncFileHandler("app.log")
    _fh.setFormatter(_fmt)
    logger.addHandler(_fh)

    _sh = logging.StreamHandler()
    _sh.setFormatter(_fmt)
    logger.addHandler(_sh)
