import handlers
import file_service

from http_utils import create_response, method_not_allowed, json_error, json_method_not_allowed


def handle_request(request):
    if request.path.startswith("/api/"):
        return handle_api_request(request)

    return handle_page_request(request)


def handle_page_request(request):
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

    if request.path == "/result":
        if request.method == "GET":
            return handlers.show_result_page(request)

        return method_not_allowed(["GET"])

    if request.path == "/history":
        if request.method == "GET":
            return handlers.show_history_page(request)

        return method_not_allowed(["GET"])

    if request.path == "/account":
        if request.method == "GET":
            return handlers.show_account_page(request)

        return method_not_allowed(["GET"])

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


def handle_api_request(request):
    if request.path == "/api/images":
        if request.method == "POST":
            return handlers.create_image_api(request)

        if request.method == "GET":
            return handlers.get_images_api(request)

        if request.method == "DELETE":
            return handlers.delete_image_api(request)

        return json_method_not_allowed(["GET", "POST", "DELETE"])

    if request.path == "/api/account":
        if request.method == "DELETE":
            return handlers.delete_account_api(request)

        return json_method_not_allowed(["DELETE"])

    if request.path == "/api/palette":
        if request.method == "GET":
            return handlers.download_palette_api(request)

        return json_method_not_allowed(["GET"])

    if request.path == "/api/history":
        if request.method == "DELETE":
            return handlers.clear_history_api(request)

        return json_method_not_allowed(["DELETE"])

    return json_error(
        404,
        "Not Found",
        "API-ресурс не найден"
    )