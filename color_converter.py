def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")

    red = int(hex_color[0:2], 16)
    green = int(hex_color[2:4], 16)
    blue = int(hex_color[4:6], 16)

    return red, green, blue


def rgb_to_hsl(red, green, blue):
    red = red / 255
    green = green / 255
    blue = blue / 255

    max_value = max(red, green, blue)
    min_value = min(red, green, blue)

    lightness = (max_value + min_value) / 2

    if max_value == min_value:
        hue = 0
        saturation = 0
    else:
        difference = max_value - min_value

        if lightness > 0.5:
            saturation = difference / (2 - max_value - min_value)
        else:
            saturation = difference / (max_value + min_value)

        if max_value == red:
            hue = (green - blue) / difference

            if green < blue:
                hue += 6

        elif max_value == green:
            hue = (blue - red) / difference + 2

        else:
            hue = (red - green) / difference + 4

        hue = hue / 6

    return round(hue * 360), round(saturation * 100), round(lightness * 100)


def rgb_to_hex(color):
    red = color[0]
    green = color[1]
    blue = color[2]

    return "#{:02X}{:02X}{:02X}".format(red, green, blue)


def hex_to_rgb_text(hex_color):
    red, green, blue = hex_to_rgb(hex_color)

    return f"rgb({red}, {green}, {blue})"


def hex_to_hsl_text(hex_color):
    red, green, blue = hex_to_rgb(hex_color)
    hue, saturation, lightness = rgb_to_hsl(red, green, blue)

    return f"hsl({hue}, {saturation}%, {lightness}%)"