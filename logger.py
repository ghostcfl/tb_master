import sys
from loguru import logger


def get_logger(log_file_name="log"):
    config = {
        "handlers": [
            {
                "sink": sys.stdout,
                "format": "{time:YYYY-MM-DD HH:mm:ss} | ({level}){message}",
                "level": "INFO",
            },
            {
                "sink": "log/" + log_file_name + ".log",
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}",
                "enqueue": True,
                "rotation": "500 MB",
                "level": "ERROR",
                "encoding": "utf-8",
            },
        ]
    }
    logger.configure(**config)
    # logger.add(sys.stdout, encoding="utf-8")
    # logger.add("log/" + log_file_name + ".log", encoding="utf-8")
    return logger


if __name__ == '__main__':
    get_logger("abc")
