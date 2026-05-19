import re
from urllib.parse import parse_qs

from http_utils import redirect, set_cookie_header, delete_cookie_header
from database import (
    create_user,
    check_user,
    create_session,
    get_user_by_session,
    delete_session
)


def get_current_user(request):
    session_id = request.cookies.get("session_id")

    return get_user_by_session(session_id)


def parse_urlencoded_form(body):
    text = body.decode("utf-8", errors="ignore")
    parsed = parse_qs(text)

    result = {}

    for key in parsed:
        values = parsed[key]

        if len(values) > 0:
            result[key] = values[0]

    return result


def register_new_user(username, password):
    if not is_valid_username(username):
        return None, (
            "Логин должен содержать от 3 до 20 символов, "
            "начинаться с латинской буквы и состоять только "
            "из латинских букв, цифр и символа _."
        )

    if not is_valid_password(password):
        return None, (
            "Пароль должен содержать от 8 до 20 символов, "
            "минимум одну латинскую букву и одну цифру. "
            "Пробелы не допускаются."
        )

    user_id = create_user(username, password)

    if user_id is None:
        return None, "Пользователь с таким логином уже существует."

    return user_id, ""


def login_existing_user(username, password):
    if username == "" or password == "":
        return None, "Введите логин и пароль."

    if not is_valid_username(username):
        return None, "Некорректный формат логина."

    if not is_valid_password_length(password):
        return None, "Некорректный формат пароля."

    user_id = check_user(username, password)

    if user_id is None:
        return None, "Неверный логин или пароль."

    return user_id, ""


def is_valid_username(username):
    pattern = r"^[A-Za-z][A-Za-z0-9_]{2,19}$"

    return re.match(pattern, username) is not None


def is_valid_password(password):
    if not is_valid_password_length(password):
        return False

    if " " in password:
        return False

    has_letter = False
    has_digit = False

    for char in password:
        if char.isalpha():
            has_letter = True

        if char.isdigit():
            has_digit = True

    return has_letter and has_digit


def is_valid_password_length(password):
    return 8 <= len(password) <= 20


def create_login_redirect(user_id):
    session_id = create_session(user_id)
    cookie = set_cookie_header("session_id", session_id)

    return redirect("/", {
        "Set-Cookie": cookie
    })


def create_logout_redirect(request):
    session_id = request.cookies.get("session_id")

    if session_id is not None:
        delete_session(session_id)

    cookie = delete_cookie_header("session_id")

    return redirect("/", {
        "Set-Cookie": cookie
    })