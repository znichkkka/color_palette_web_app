import os
import time
from urllib.parse import unquote
from PIL import Image, UnidentifiedImageError

from http_utils import create_response


STATIC_FOLDER = "static"
UPLOAD_FOLDER = "uploads"

ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]


def has_allowed_image_extension(filename):
    extension = os.path.splitext(filename)[1].lower()

    return extension in ALLOWED_IMAGE_EXTENSIONS


def is_image_file(filepath):
    try:
        image = Image.open(filepath)
        image.verify()
        image.close()

        return True

    except (UnidentifiedImageError, OSError):
        return False


def save_uploaded_file(user, filename, file_data):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    safe_filename = create_safe_filename(user, filename)
    filepath = os.path.join(UPLOAD_FOLDER, safe_filename)

    with open(filepath, "wb") as file:
        file.write(file_data)

    return filepath, safe_filename


def create_safe_filename(user, filename):
    original_filename = os.path.basename(filename)
    timestamp = str(int(time.time()))

    if user is None:
        user_prefix = "guest"
    else:
        user_prefix = str(user["id"])

    return user_prefix + "_" + timestamp + "_" + original_filename


def delete_file_if_exists(filepath):
    if filepath is None:
        return

    if os.path.exists(filepath):
        os.remove(filepath)


def serve_static_file(path):
    file_path = path.replace("/static/", "", 1)
    file_path = unquote(file_path)

    full_path = get_safe_path(STATIC_FOLDER, file_path)

    if full_path is None:
        return create_file_error_response(400, "Bad Request", "Некорректный путь к файлу")

    return serve_file(full_path)


def serve_uploaded_file(path):
    file_path = path.replace("/uploads/", "", 1)
    file_path = unquote(file_path)

    full_path = get_safe_path(UPLOAD_FOLDER, file_path)

    if full_path is None:
        return create_file_error_response(400, "Bad Request", "Некорректный путь к файлу")

    return serve_file(full_path)


def get_safe_path(base_folder, file_path):
    base_path = os.path.abspath(str(base_folder))
    full_path = os.path.abspath(os.path.join(base_path, str(file_path)))

    if not full_path.startswith(base_path + os.sep) and full_path != base_path:
        return None

    return full_path


def serve_file(full_path):
    if not os.path.exists(full_path):
        return create_file_error_response(404, "Not Found", "Файл не найден")

    if not os.path.isfile(full_path):
        return create_file_error_response(404, "Not Found", "Файл не найден")

    content_type = get_content_type(full_path)

    with open(full_path, "rb") as file:
        content = file.read()

    return create_response(200, "OK", content, content_type)


def create_file_error_response(status_code, status_text, message):
    html = f"<h1>{status_code} {status_text}</h1><p>{message}</p>"

    return create_response(status_code, status_text, html)


def get_content_type(path):
    extension = os.path.splitext(path)[1].lower()

    if extension == ".css":
        return "text/css; charset=utf-8"

    if extension == ".js":
        return "application/javascript; charset=utf-8"

    if extension == ".png":
        return "image/png"

    if extension == ".jpg" or extension == ".jpeg":
        return "image/jpeg"

    if extension == ".gif":
        return "image/gif"

    if extension == ".webp":
        return "image/webp"

    return "application/octet-stream"