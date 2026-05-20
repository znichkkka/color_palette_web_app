import socket
from threading import Thread

from config import HOST, PORT, BUFFER_SIZE, BACKLOG
from http_utils import parse_http_request, create_response
from router import handle_request
from logger import log_request, log_error


def read_request(client_socket):
    request_data = b""

    while True:
        data = client_socket.recv(BUFFER_SIZE)

        if not data:
            break

        request_data += data

        if b"\r\n\r\n" in request_data:
            break

    headers_end = request_data.find(b"\r\n\r\n")

    if headers_end == -1:
        return request_data

    headers_text = request_data[:headers_end].decode(
        "utf-8",
        errors="ignore"
    )

    body = request_data[headers_end + 4:]

    content_length = get_content_length(headers_text)

    while len(body) < content_length:
        data = client_socket.recv(BUFFER_SIZE)

        if not data:
            break

        request_data += data
        body += data

    return request_data


def get_content_length(headers_text):
    lines = headers_text.split("\r\n")

    for line in lines:
        if line.lower().startswith("content-length:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return 0

    return 0


def get_status_code(response):
    first_line = response.split(b"\r\n", 1)[0]

    try:
        parts = first_line.decode(
            "utf-8",
            errors="ignore"
        ).split()

        if len(parts) >= 2:
            return parts[1]

    except UnicodeDecodeError:
        pass

    return "000"


def send_error_response(client_socket, status_code, status_text):
    response = create_response(
        status_code,
        status_text,
        f"<h1>{status_code} {status_text}</h1>",
        "text/html; charset=utf-8"
    )

    try:
        client_socket.sendall(response)
    except OSError:
        pass


def handle_client(client_socket, address):
    try:
        request_data = read_request(client_socket)

        if not request_data:
            return

        request = parse_http_request(request_data)

        if request is None:
            send_error_response(
                client_socket,
                400,
                "Bad Request"
            )

            log_request(
                address[0],
                "UNKNOWN",
                "UNKNOWN",
                "400"
            )

            return

        response = handle_request(request)

        status_code = get_status_code(response)

        log_request(
            address[0],
            request.method,
            request.path,
            status_code
        )

        client_socket.sendall(response)

    except Exception as error:
        log_error(
            "Ошибка обработки запроса: " + str(error)
        )

        send_error_response(
            client_socket,
            500,
            "Internal Server Error"
        )

    finally:
        try:
            client_socket.close()
        except OSError:
            pass


def start_server():
    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind((HOST, PORT))
    server_socket.listen(BACKLOG)

    print(f"Сервер запущен: http://{HOST}:{PORT}")

    try:
        while True:
            client_socket, address = server_socket.accept()

            thread = Thread(
                target=handle_client,
                args=(client_socket, address),
                daemon=True
            )

            thread.start()

    except KeyboardInterrupt:
        print("Сервер остановлен")

    finally:
        server_socket.close()