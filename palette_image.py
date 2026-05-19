from PIL import Image, ImageDraw, ImageFont


BLOCK_WIDTH = 320
BLOCK_HEIGHT = 260
TEXT_HEIGHT = 90
PADDING = 60
GAP = 24
RADIUS = 28

BACKGROUND_COLOR = "#F8FAFC"
TEXT_COLOR = "#111827"

FONT_SIZE = 38


def create_palette_image(colors):
    width = get_image_width(len(colors))
    height = get_image_height()

    image = Image.new("RGB", (width, height), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    font = load_font(FONT_SIZE)

    for index, color in enumerate(colors):
        draw_color_block(draw, font, index, color)

    return image


def get_image_width(colors_count):
    return PADDING * 2 + BLOCK_WIDTH * colors_count + GAP * (colors_count - 1)


def get_image_height():
    return PADDING * 2 + BLOCK_HEIGHT + TEXT_HEIGHT


def draw_color_block(draw, font, index, color):
    x1 = PADDING + index * (BLOCK_WIDTH + GAP)
    y1 = PADDING
    x2 = x1 + BLOCK_WIDTH
    y2 = y1 + BLOCK_HEIGHT

    draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=RADIUS,
        fill=color
    )

    draw_color_text(draw, font, x1, y2, color)


def draw_color_text(draw, font, x1, y2, color):
    text_width = draw.textlength(color, font=font)

    text_x = x1 + (BLOCK_WIDTH - text_width) / 2
    text_y = y2 + 24

    draw.text(
        (text_x, text_y),
        color,
        fill=TEXT_COLOR,
        font=font
    )


def load_font(size):
    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "arial.ttf"
    ]

    for path in font_paths:
        font = try_load_font(path, size)

        if font is not None:
            return font

    return ImageFont.load_default()


def try_load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return None