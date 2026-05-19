import handlers
import file_service

from http_utils import create_response, method_not_allowed


def handle_request(request):
    if request.path == "/":
        if request.method == "GET":
            return handlers.show_index_page(request)

        return method_not_allowed(["GET"])

    if request.path == "/register":
        if request.method == "GET":
            return handlers.show_register_page(request)

        if request.method == "POST":
            return handlers.register_user(request)

        return method_not_allowed(["GET", "POST"])

    if request.path == "/login":
        if request.method == "GET":
            return handlers.show_login_page(request)

        if request.method == "POST":
            return handlers.login_user(request)

        return method_not_allowed(["GET", "POST"])

    if request.path == "/logout":
        if request.method == "POST":
            return handlers.logout_user(request)

        return method_not_allowed(["POST"])

    if request.path == "/upload":
        if request.method == "POST":
            return handlers.upload_image(request)

        return method_not_allowed(["POST"])

    if request.path == "/result":
        if request.method == "GET":
            return handlers.show_result_page(request)

        return method_not_allowed(["GET"])

    if request.path == "/history":
        if request.method == "GET":
            return handlers.show_history_page(request)

        return method_not_allowed(["GET"])

    if request.path == "/image":
        if request.method == "DELETE":
            return handlers.delete_history_image(request)

        return method_not_allowed(["DELETE"])

    if request.path == "/download_palette":
        if request.method == "GET":
            return handlers.download_palette(request)

        return method_not_allowed(["GET"])

    if request.path == "/account":
        if request.method == "GET":
            return handlers.show_account_page(request)

        if request.method == "DELETE":
            return handlers.delete_account(request)

        return method_not_allowed(["GET", "DELETE"])

    if request.path.startswith("/static/"):
        if request.method == "GET":
            return file_service.serve_static_file(request.path)

        return method_not_allowed(["GET"])

    if request.path.startswith("/uploads/"):
        if request.method == "GET":
            return file_service.serve_uploaded_file(request.path)

        return method_not_allowed(["GET"])

    return create_response(
        404,
        "Not Found",
        "<h1>404 Not Found</h1><p>Страница не найдена</p>"
    )