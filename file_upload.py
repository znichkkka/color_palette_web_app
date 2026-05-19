def parse_multipart_form(body, content_type):
    result = {
        "files": {},
        "fields": {}
    }

    boundary = get_boundary(content_type)

    if boundary is None:
        return result

    boundary_bytes = ("--" + boundary).encode("utf-8")
    parts = body.split(boundary_bytes)

    for part in parts:
        parse_multipart_part(part, result)

    return result


def parse_multipart_part(part, result):
    if b"Content-Disposition" not in part:
        return

    header_end = part.find(b"\r\n\r\n")

    if header_end == -1:
        return

    headers_bytes = part[:header_end]
    content = part[header_end + 4:]

    content = content.rstrip(b"\r\n")
    headers_text = headers_bytes.decode("utf-8", errors="ignore")

    field_name = get_field_name(headers_text)

    if field_name is None:
        return

    filename = get_filename(headers_text)

    if filename is None:
        result["fields"][field_name] = content.decode("utf-8", errors="ignore")
    else:
        result["files"][field_name] = {
            "filename": filename,
            "content": content
        }


def parse_uploaded_file(body, content_type):
    form = parse_multipart_form(body, content_type)

    if len(form["files"]) == 0:
        return None

    first_key = list(form["files"].keys())[0]

    return form["files"][first_key]


def get_boundary(content_type):
    parts = content_type.split(";")

    for part in parts:
        part = part.strip()

        if part.startswith("boundary="):
            boundary = part.replace("boundary=", "", 1)
            boundary = boundary.strip('"')
            return boundary

    return None


def get_field_name(headers):
    return get_header_parameter(headers, "name")


def get_filename(headers):
    return get_header_parameter(headers, "filename")


def get_header_parameter(headers, parameter_name):
    lines = headers.split("\r\n")

    for line in lines:
        if "Content-Disposition" not in line:
            continue

        parts = line.split(";")

        for part in parts:
            part = part.strip()

            if part.startswith(parameter_name + "="):
                value = part.replace(parameter_name + "=", "", 1)
                value = value.strip('"')
                return value

    return None