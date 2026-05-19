import os
from datetime import datetime


LOGS_FOLDER = "logs"
LOG_FILE = os.path.join(LOGS_FOLDER, "server.log")

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40

LOG_LEVEL = INFO

LEVEL_NAMES = {
    DEBUG: "DEBUG",
    INFO: "INFO",
    WARNING: "WARNING",
    ERROR: "ERROR"
}


def set_log_level(level):
    global LOG_LEVEL

    LOG_LEVEL = level


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_log(level, text):
    if level < LOG_LEVEL:
        return

    os.makedirs(LOGS_FOLDER, exist_ok=True)

    current_time = get_current_time()
    level_name = LEVEL_NAMES.get(level, "INFO")

    log_line = f"[{current_time}] [{level_name}] {text}"

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(log_line + "\n")


def log_debug(text):
    write_log(DEBUG, text)


def log_info(text):
    write_log(INFO, text)


def log_warning(text):
    write_log(WARNING, text)


def log_error(text):
    write_log(ERROR, text)


def log_request(client_ip, method, path, status_code):
    text = f"{client_ip} {method} {path} -> {status_code}"

    log_info(text)