import json


with open("config.json", "r", encoding="utf-8") as file:
    config = json.load(file)


HOST = config["host"]
PORT = config["port"]
BUFFER_SIZE = config["buffer_size"]
BACKLOG = config["backlog"]