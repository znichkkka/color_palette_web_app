import os
import io

from http_utils import create_response, redirect, no_content
from database import (
    save_image,
    get_image,
    get_all_images,
    delete_image,
    get_user_image_paths,
    delete_user_account,
    get_user_images_count
)
from auth import (
    get_current_user,
    parse_urlencoded_form,
    register_new_user,
    login_existing_user,
    create_login_redirect,
    create_logout_redirect
)
from file_upload import parse_multipart_form
from image_analyzer import get_dominant_colors
from palette_image import create_palette_image
from color_converter import hex_to_rgb_text, hex_to_hsl_text
from file_service import (
    is_image_file,
    has_allowed_image_extension,
    save_uploaded_file,
    delete_file_if_exists
)
from logger import log_error


TEMPLATE_FOLDER = "templates"
MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_COLORS_COUNT = [3, 6, 9, 12]


def read_template(filename):
    path = os.path.join(TEMPLATE_FOLDER, filename)

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def create_error_response(status_code, status_text, message):
    html = f"<h1>{status_code} {status_text}</h1><p>{message}</p>"

    return create_response(status_code, status_text, html)


def create_error_block(error_message):
    if error_message == "":
        return ""

    return f"""
    <div class="form-error">
        {error_message}
    </div>
    """


def get_header_links(user):
    if user is None:
        return """
        <a class="nav-link" href="/">Главная</a>
        <a class="nav-link" href="/login">Войти</a>
        <a class="nav-button" href="/register">Регистрация</a>
        """

    return """
    <a class="nav-link" href="/">Главная</a>
    <a class="nav-link" href="/history">История</a>
    <a class="nav-link" href="/account">Аккаунт</a>

    <form
    class="logout-form"
    action="/logout"
    method="post"
    onsubmit="return confirm('Выйти из аккаунта?')"
>
    <button class="nav-button logout-button" type="submit">
        Выйти
    </button>
</form>
    """


def show_index_page(request):
    user = get_current_user(request)
    html = read_template("index.html")

    html = html.replace("{{ header_links }}", get_header_links(user))
    html = html.replace("{{ history_notice }}", create_history_notice(user))

    return create_response(200, "OK", html)


def create_history_notice(user):
    if user is not None:
        return ""

    return """
    <div class="notice">
        Вы можете анализировать изображения без аккаунта, но история загрузок будет доступна только после входа.
        <a href="/login">Войти</a> или <a href="/register">зарегистрироваться</a>
    </div>
    """


def show_register_page(request, error_message=""):
    html = read_template("register.html")
    html = html.replace("{{ error }}", create_error_block(error_message))

    return create_response(200, "OK", html)


def show_login_page(request, error_message=""):
    html = read_template("login.html")
    html = html.replace("{{ error }}", create_error_block(error_message))

    return create_response(200, "OK", html)


def register_user(request):
    try:
        form = parse_urlencoded_form(request.body)

        username = form.get("username", "").strip()
        password = form.get("password", "").strip()

        user_id, error_message = register_new_user(username, password)

        if error_message != "":
            return show_register_page(request, error_message)

        return create_login_redirect(user_id)

    except Exception as error:
        log_error("Ошибка регистрации: " + str(error))

        return create_error_response(
            500,
            "Internal Server Error",
            "Ошибка при регистрации пользователя"
        )


def login_user(request):
    try:
        form = parse_urlencoded_form(request.body)

        username = form.get("username", "").strip()
        password = form.get("password", "").strip()

        user_id, error_message = login_existing_user(username, password)

        if error_message != "":
            return show_login_page(request, error_message)

        return create_login_redirect(user_id)

    except Exception as error:
        log_error("Ошибка входа: " + str(error))

        return create_error_response(
            500,
            "Internal Server Error",
            "Ошибка при входе в аккаунт"
        )


def logout_user(request):
    return create_logout_redirect(request)


def show_account_page(request):
    user = get_current_user(request)

    if user is None:
        return redirect("/login")

    images_count = get_user_images_count(user["id"])
    html = read_template("account.html")

    html = html.replace("{{ header_links }}", get_header_links(user))
    html = html.replace("{{ username }}", user["username"])
    html = html.replace("{{ images_count }}", str(images_count))

    return create_response(200, "OK", html)


def upload_image(request):
    try:
        user = get_current_user(request)
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" not in content_type:
            return create_error_response(
                415,
                "Unsupported Media Type",
                "Форма отправлена в неверном формате"
            )

        form = parse_multipart_form(request.body, content_type)
        uploaded_file = form["files"].get("image")

        if uploaded_file is None:
            return create_error_response(
                400,
                "Bad Request",
                "Файл не был загружен"
            )

        filename = uploaded_file["filename"]
        file_data = uploaded_file["content"]
        colors_count = get_colors_count(form)

        if filename == "":
            return create_error_response(
                400,
                "Bad Request",
                "Имя файла пустое"
            )

        if len(file_data) > MAX_FILE_SIZE:
            return create_error_response(
                413,
                "Payload Too Large",
                "Размер файла не должен превышать 20 МБ"
            )

        if not has_allowed_image_extension(filename):
            return create_error_response(
                415,
                "Unsupported Media Type",
                "Недопустимый формат файла"
            )

        filepath, safe_filename = save_uploaded_file(user, filename, file_data)

        if not is_image_file(filepath):
            delete_file_if_exists(filepath)

            return create_error_response(
                415,
                "Unsupported Media Type",
                "Загруженный файл не является изображением"
            )

        palette = get_dominant_colors(filepath, colors_count)
        user_id = get_user_id(user)

        image_id = save_image(
            user_id,
            safe_filename,
            filepath,
            palette,
            colors_count
        )

        return redirect(f"/result?id={image_id}")

    except Exception as error:
        log_error("Ошибка загрузки изображения: " + str(error))

        return create_error_response(
            500,
            "Internal Server Error",
            "Ошибка при обработке изображения"
        )


def get_user_id(user):
    if user is None:
        return None

    return user["id"]


def get_colors_count(form):
    colors_count_text = form["fields"].get("colors_count", "6")

    try:
        colors_count = int(colors_count_text)
    except ValueError:
        return 6

    if colors_count not in ALLOWED_COLORS_COUNT:
        return 6

    return colors_count


def show_result_page(request):
    try:
        user = get_current_user(request)
        image_id = get_id_from_query(request, "id")

        if image_id is None:
            return create_error_response(
                400,
                "Bad Request",
                "Некорректный id результата"
            )

        image = get_image(image_id)

        if image is None:
            return create_error_response(
                404,
                "Not Found",
                "Результат не найден"
            )

        access_response = check_image_access(user, image)

        if access_response is not None:
            return access_response

        html = read_template("result.html")

        html = html.replace("{{ header_links }}", get_header_links(user))
        html = html.replace("{{ image_id }}", str(image["id"]))
        html = html.replace("{{ filename }}", image["filename"])
        html = html.replace("{{ image_path }}", get_image_url(image["filepath"]))
        html = html.replace("{{ upload_date }}", image["upload_date"])
        html = html.replace("{{ colors_count }}", str(image["colors_count"]))
        html = html.replace("{{ colors }}", create_palette_html(image["palette"]))
        html = html.replace("{{ save_notice }}", create_save_notice(user, image))

        return create_response(200, "OK", html)

    except Exception as error:
        log_error("Ошибка страницы результата: " + str(error))

        return create_error_response(
            500,
            "Internal Server Error",
            "Ошибка при открытии результата"
        )


def check_image_access(user, image):
    if image["user_id"] is None:
        return None

    if user is None:
        return create_error_response(
            401,
            "Unauthorized",
            "Для просмотра результата необходимо войти в аккаунт"
        )

    if image["user_id"] != user["id"]:
        return create_error_response(
            403,
            "Forbidden",
            "Нет доступа к этому результату"
        )

    return None


def get_image_url(filepath):
    return "/" + filepath.replace("\\", "/")


def create_palette_html(palette):
    colors_html = ""

    for color in palette:
        rgb_color = hex_to_rgb_text(color)
        hsl_color = hex_to_hsl_text(color)

        colors_html += f"""
        <div class="color-item" data-hex="{color}" data-rgb="{rgb_color}" data-hsl="{hsl_color}" data-color="{color}">
            <div class="color-box" style="background-color: {color};"></div>
            <span>{color}</span>
        </div>
        """

    return colors_html


def create_save_notice(user, image):
    if user is None:
        return """
        <div class="notice">
            Результат получен, но не сохранён в личную историю. 
            Для сохранения истории <a href="/login">войдите</a> или <a href="/register">зарегистрируйтесь</a>.
        </div>
        """

    if image["user_id"] == user["id"]:
        return """
        <div class="notice success">
            Результат сохранён в вашей истории.
        </div>
        """

    return ""


def get_id_from_query(request, name):
    values = request.query_params.get(name)

    if not values:
        return None

    try:
        return int(values[0])
    except ValueError:
        return None


def show_history_page(request):
    user = get_current_user(request)

    if user is None:
        return show_guest_history_page()

    images = get_all_images(user["id"])
    rows = create_history_rows(images)

    html = read_template("history.html")
    html = html.replace("{{ header_links }}", get_header_links(user))
    html = html.replace("{{ rows }}", rows)

    return create_response(200, "OK", html)


def show_guest_history_page():
    html = read_template("history.html")

    rows = """
    <div class="empty">
        История доступна только после входа в аккаунт.
        <br><br>
        <a class="nav-button" href="/login">Войти</a>
        <a class="nav-link" href="/register">Зарегистрироваться</a>
    </div>
    """

    html = html.replace("{{ header_links }}", get_header_links(None))
    html = html.replace("{{ rows }}", rows)

    return create_response(200, "OK", html)


def create_history_rows(images):
    if len(images) == 0:
        return """
        <div class="empty">
            История загрузок пока пуста.
        </div>
        """

    rows = ""

    for image in images:
        rows += create_history_item(image)

    return rows


def create_history_item(image):
    palette_html = ""

    for color in image["palette"]:
        palette_html += f"""
        <span class="small-color" style="background-color: {color};"></span>
        """

    return f"""
    <div class="history-item">
        <div>
            <div class="history-name">{image["filename"]}</div>

            <div class="history-date">
                Дата загрузки: {image["upload_date"]}
            </div>

            <div class="history-date">
                Количество цветов: {image["colors_count"]}
            </div>

            <div class="small-palette">
                {palette_html}
            </div>
        </div>

        <div class="history-actions">
            <a class="open-link" href="/result?id={image["id"]}">
                Открыть
            </a>

            <button
                class="delete-button"
                type="button"
                onclick="deleteImage({image["id"]})"
            >
                Удалить
            </button>
        </div>
    </div>
    """


def delete_history_image(request):
    try:
        user = get_current_user(request)

        if user is None:
            return create_error_response(
                401,
                "Unauthorized",
                "Для удаления изображения необходимо войти в аккаунт"
            )

        image_id = get_id_from_query(request, "id")

        if image_id is None:
            return create_error_response(
                400,
                "Bad Request",
                "Некорректный id изображения"
            )

        filepath = delete_image(image_id, user["id"])

        if filepath is None:
            return create_error_response(
                404,
                "Not Found",
                "Изображение не найдено"
            )

        delete_file_if_exists(filepath)

        return no_content()

    except Exception as error:
        log_error("Ошибка удаления изображения: " + str(error))

        return create_error_response(
            500,
            "Internal Server Error",
            "Ошибка при удалении записи"
        )


def delete_account(request):
    try:
        user = get_current_user(request)

        if user is None:
            return create_error_response(
                401,
                "Unauthorized",
                "Для удаления аккаунта необходимо войти в аккаунт"
            )

        filepaths = get_user_image_paths(user["id"])

        for filepath in filepaths:
            delete_file_if_exists(filepath)

        delete_user_account(user["id"])

        return no_content()

    except Exception as error:
        log_error("Ошибка удаления аккаунта: " + str(error))

        return create_error_response(
            500,
            "Internal Server Error",
            "Ошибка при удалении аккаунта"
        )


def download_palette(request):
    try:
        user = get_current_user(request)
        image_id = get_id_from_query(request, "id")

        if image_id is None:
            return create_error_response(
                400,
                "Bad Request",
                "Некорректный id палитры"
            )

        image = get_image(image_id)

        if image is None:
            return create_error_response(
                404,
                "Not Found",
                "Палитра не найдена"
            )

        access_response = check_image_access(user, image)

        if access_response is not None:
            return access_response

        palette_image = create_palette_image(image["palette"])

        buffer = io.BytesIO()
        palette_image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        filename = f"palette_{image['id']}.png"

        return create_response(
            200,
            "OK",
            image_bytes,
            "image/png",
            {
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as error:
        log_error("Ошибка скачивания палитры: " + str(error))

        return create_error_response(
            500,
            "Internal Server Error",
            "Ошибка при создании изображения палитры"
        )