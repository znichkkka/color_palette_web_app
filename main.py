from database import init_db
from server import start_server
from logger import set_log_level, INFO


if __name__ == "__main__":
    set_log_level(INFO)
    init_db()
    start_server()