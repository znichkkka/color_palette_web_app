from urllib.parse import urlparse, parse_qs
import json


class HttpRequest:
    def __init__(self, method, path, version, headers, body, query_params, cookies):
        self.method = method
        self.path = path
        self.version = version
        self.headers = headers
        self.body = body
        self.query_params = query_params
        self.cookies = cookies


def parse_http_request(request_data):
    header_end = request_data.find(b"\r\n\r\n")

    if header_end == -1:
        return None

    header_bytes = request_data[:header_end]
    body = request_data[header_end + 4:]

    header_text = header_bytes.decode("utf-8", errors="ignore")
    lines = header_text.split("\r\n")

    if len(lines) == 0:
        return None

    request_line = lines[0].split()

    if len(request_line) != 3:
        return None

    method = request_line[0].upper()
    target = request_line[1]
    version = request_line[2]

    parsed_url = urlparse(target)
    path = parsed_url.path
    query_params = parse_qs(parsed_url.query)

    headers = parse_headers(lines[1:])
    cookies = parse_cookies(headers.get("cookie", ""))

    return HttpRequest(
        method,
        path,
        version,
        headers,
        body,
        query_params,
        cookies
    )


def parse_headers(lines):
    headers = {}

    for line in lines:
        if ":" not in line:
            continue

        name, value = line.split(":", 1)
        headers[name.lower()] = value.strip()

    return headers


def parse_cookies(cookie_header):
    cookies = {}

    if cookie_header == "":
        return cookies

    parts = cookie_header.split(";")

    for part in parts:
        if "=" not in part:
            continue

        name, value = part.strip().split("=", 1)
        cookies[name] = value

    return cookies


def create_response(status_code, status_text, body="", content_type="text/html; charset=utf-8", extra_headers=None):
    if isinstance(body, str):
        body = body.encode("utf-8")

    headers = create_response_headers(body, content_type, extra_headers)

    response_text = f"HTTP/1.1 {status_code} {status_text}\r\n"

    for name, value in headers.items():
        response_text += f"{name}: {value}\r\n"

    response_text += "\r\n"

    return response_text.encode("utf-8") + body


def create_response_headers(body, content_type, extra_headers):
    headers = {
        "Content-Type": content_type,
        "Content-Length": str(len(body)),
        "Connection": "close"
    }

    if extra_headers is not None:
        headers.update(extra_headers)

    return headers


def json_response(status_code, status_text, data, extra_headers=None):
    body = json.dumps(data, ensure_ascii=False)

    return create_response(
        status_code,
        status_text,
        body,
        "application/json; charset=utf-8",
        extra_headers
    )


def json_error(status_code, status_text, message):
    return json_response(
        status_code,
        status_text,
        {
            "success": False,
            "error": message
        }
    )


def redirect(location, extra_headers=None):
    return create_response(
        303,
        "See Other",
        "",
        "text/html; charset=utf-8",
        {
            "Location": location,
            **(extra_headers or {})
        }
    )


def no_content():
    return create_response(
        204,
        "No Content",
        "",
        "text/plain; charset=utf-8"
    )


def method_not_allowed(allowed_methods):
    return create_response(
        405,
        "Method Not Allowed",
        "<h1>405 Method Not Allowed</h1><p>Метод не поддерживается для этого адреса</p>",
        "text/html; charset=utf-8",
        {
            "Allow": ", ".join(allowed_methods)
        }
    )


def json_method_not_allowed(allowed_methods):
    return json_response(
        405,
        "Method Not Allowed",
        {
            "success": False,
            "error": "Метод не поддерживается для этого ресурса"
        },
        {
            "Allow": ", ".join(allowed_methods)
        }
    )


def set_cookie_header(name, value):
    return f"{name}={value}; Path=/; HttpOnly"


def delete_cookie_header(name):
    return f"{name}=; Path=/; Max-Age=0; HttpOnly"