from PIL import Image

from color_converter import rgb_to_hex


def get_dominant_colors(image_path, colors_count=5):
    image = Image.open(image_path)
    image = image.convert("RGB")

    image.thumbnail((150, 150))

    colors = image.getcolors(maxcolors=150 * 150)

    if colors is None:
        return []

    colors.sort(reverse=True, key=lambda item: item[0])

    result = []

    for count, color in colors:
        if is_too_light_or_too_dark(color):
            continue

        if is_similar_to_existing(color, result):
            continue

        result.append(color)

        if len(result) == colors_count:
            break

    if len(result) < colors_count:
        for count, color in colors:
            if is_similar_to_existing(color, result):
                continue

            result.append(color)

            if len(result) == colors_count:
                break

    return [rgb_to_hex(color) for color in result]


def is_similar_to_existing(color, selected_colors):
    for selected_color in selected_colors:
        if color_distance(color, selected_color) < 45:
            return True

    return False


def color_distance(color1, color2):
    red_difference = color1[0] - color2[0]
    green_difference = color1[1] - color2[1]
    blue_difference = color1[2] - color2[2]

    return (red_difference ** 2 + green_difference ** 2 + blue_difference ** 2) ** 0.5


def is_too_light_or_too_dark(color):
    brightness = (color[0] + color[1] + color[2]) / 3

    if brightness < 25:
        return True

    if brightness > 235:
        return True

    return False