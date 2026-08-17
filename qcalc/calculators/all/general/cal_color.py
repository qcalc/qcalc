# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# import colorsys
from qcore import qfl, qin, qhtml


def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def yiq_to_rgb(y, i, q):
    """Convert YIQ color to RGB color."""
    r = y + 0.946882 * i + 0.623556 * q
    g = y - 0.274787 * i - 0.635003 * q
    b = y - 1.108545 * i + 1.709007 * q

    # Clamp RGB values to be in the range [0, 255]
    r = min(max(0, int(round(r * 255))), 255)
    g = min(max(0, int(round(g * 255))), 255)
    b = min(max(0, int(round(b * 255))), 255)

    return r, g, b


def hls_to_rgb(h, l, s):
    """Convert HLS color to RGB color."""
    if s == 0:
        # Achromatic (gray)
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            """Helper function to convert hue to RGB."""
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1 / 3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1 / 3)

    # Convert RGB from [0,1] range to [0,255] range
    r = int(round(r * 255))
    g = int(round(g * 255))
    b = int(round(b * 255))

    return r, g, b


def hsv_to_rgb(h, s, v):
    """Convert HSV color to RGB color."""
    if s == 0:
        # Achromatic (gray)
        r = g = b = v
    else:
        h = h % 360  # Ensure hue is in [0, 360) range
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c

        r = 0
        g = 0
        b = 0
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        elif 300 <= h < 360:
            r, g, b = c, 0, x

        r = (r + m) * 255
        g = (g + m) * 255
        b = (b + m) * 255

    return int(round(r)), int(round(g)), int(round(b))


def ymck_to_rgb(y, m, c, k):
    """Convert YMCK color to RGB color."""
    # Clamp YMCK values to the [0, 1] range if they are not already
    y = max(0, min(y, 1))
    m = max(0, min(m, 1))
    c = max(0, min(c, 1))
    k = max(0, min(k, 1))

    # Convert YMCK to RGB
    r = 1 - min(1, y + k)
    g = 1 - min(1, m + k)
    b = 1 - min(1, c + k)

    # Convert RGB values from [0,1] range to [0,255] range
    r = int(round(r * 255))
    g = int(round(g * 255))
    b = int(round(b * 255))

    return r, g, b


def rgb_to_hex(r, g, b):
    """Convert an RGB tuple to a HEX color string."""
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def rgb_to_yiq(r, g, b):
    """Convert RGB color to YIQ color."""
    # Normalize RGB values to [0, 1]
    r /= 255.0
    g /= 255.0
    b /= 255.0

    # Convert RGB to YIQ
    y = 0.299 * r + 0.587 * g + 0.114 * b
    i = 0.596 * r - 0.274 * g - 0.322 * b
    q = 0.211 * r - 0.523 * g + 0.312 * b

    return y, i, q


def rgb_to_hls(r, g, b):
    """Convert RGB color to HLS color."""
    # Normalize RGB values to [0, 1]
    r /= 255.0
    g /= 255.0
    b /= 255.0

    # Calculate Lightness
    min_val = min(r, g, b)
    max_val = max(r, g, b)
    l = (max_val + min_val) / 2

    # Calculate Saturation
    if max_val == min_val:
        s = 0  # Achromatic (gray)
    else:
        if l <= 0.5:
            s = (max_val - min_val) / (max_val + min_val)
        else:
            s = (max_val - min_val) / (2.0 - max_val - min_val)

    # Calculate Hue
    if s == 0:
        h = 0  # Hue is undefined for grayscale
    else:
        if r == max_val:
            h = (g - b) / (max_val - min_val)
        elif g == max_val:
            h = 2.0 + (b - r) / (max_val - min_val)
        else:
            h = 4.0 + (r - g) / (max_val - min_val)

        h *= 60
        if h < 0:
            h += 360

    return h, l, s


def rgb_to_hsv(r, g, b):
    """Convert RGB color to HSV color."""
    # Normalize RGB values to [0, 1]
    r /= 255.0
    g /= 255.0
    b /= 255.0

    # Calculate Value (V)
    v = max(r, g, b)

    # Calculate Saturation (S)
    min_val = min(r, g, b)
    delta = v - min_val

    if v == 0:
        s = 0  # If Value is 0, Saturation is 0 (gray)
    else:
        s = delta / v

    # Calculate Hue (H)
    if delta == 0:
        h = 0  # If there is no difference, hue is undefined (gray)
    else:
        if r == v:
            h = (g - b) / delta
        elif g == v:
            h = 2.0 + (b - r) / delta
        else:
            h = 4.0 + (r - g) / delta

        h *= 60
        if h < 0:
            h += 360

    return h, s, v


def rgb_to_ymck(r, g, b):
    """Convert RGB color to YMCK color."""
    # Normalize RGB values to [0, 1]
    r /= 255.0
    g /= 255.0
    b /= 255.0

    # Calculate Key/Black (K)
    k = 1 - max(r, g, b)

    if k < 1:
        # Calculate Yellow (Y), Magenta (M), Cyan (C)
        y = (1 - r - k) / (1 - k)
        m = (1 - g - k) / (1 - k)
        c = (1 - b - k) / (1 - k)
    else:
        # If K is 1, then Y, M, C are all 0
        y = m = c = 0

    return y, m, c, k


def complementary_color(hex_color: str):
    rgb = hex_to_rgb(hex_color)
    comp_rgb = tuple(255 - x for x in rgb)
    return '#{:02x}{:02x}{:02x}'.format(*comp_rgb)


def analogous_colors(hex_color: str):
    rgb = hex_to_rgb(hex_color)
    shift = 30  # Shift by 30 degrees in the color wheel
    analogous_rgb1 = tuple((x + shift) % 256 for x in rgb)
    analogous_rgb2 = tuple((x - shift) % 256 for x in rgb)
    return (
        '#{:02x}{:02x}{:02x}'.format(*analogous_rgb1),
        '#{:02x}{:02x}{:02x}'.format(*analogous_rgb2)
    )


def color_profile__info():
    return {
        'title': 'Calculate Color Profile',
        'schema': {
            'known_values': {'type': 'choice', 'choices': ['HEX', 'RGB', 'YIQ', 'HLS', 'HSV', 'YMCK']}
        },
        'showhide': {
            'known_values': {
                'fields':
                    [
                        'hex_color',
                        'rgb', 'g_part', 'b_part',
                        'yiq', 'i_part', 'q_part',
                        'hls', 'l_part', 's_part',
                        'hsv', 's2_part', 'v_part',
                        'ymck', 'm_part', 'c_part', 'k_part',
                    ],
                'callback':
                    {
                        'HEX': "[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]",
                        'RGB': "[0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0]",
                        'YIQ': "[0,0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0]",
                        'HLS': "[0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,0,0]",
                        'HSV': "[0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0]",
                        'YMCK': "[0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1]",
                    },
            },
        },
    }


def color_profile(
    known_values='HEX', hex_color: str = '#aabbcc',
    rgb: qin = 50, g_part: int = 150, b_part: int = 250,
    yiq: qfl = 0.5, i_part=-0.1, q_part=0.2,
    hls: qfl = 0.5, l_part=0.5, s_part=0.5,
    hsv: qin = 210, s2_part=0.75, v_part=0.9,
    ymck: qfl = 0.2, m_part=0.4, c_part=0.6, k_part=0.1,
):
    r = 0
    g = 0
    b = 0
    if known_values == 'HEX':
        r, g, b = hex_to_rgb(hex_color)
    elif known_values == 'RGB':
        r, g, b = rgb, g_part, b_part
    elif known_values == 'YIQ':
        r, g, b = yiq_to_rgb(yiq, i_part, q_part)
    elif known_values == 'HLS':
        r, g, b = hls_to_rgb(hls, l_part, s_part)
    elif known_values == 'HSV':
        r, g, b = hsv_to_rgb(hsv, s2_part, v_part)
    elif known_values == 'YMCK':
        r, g, b = ymck_to_rgb(ymck, m_part, c_part, k_part)

    hex_color = rgb_to_hex(r, g, b)
    y1, i1, q1 = rgb_to_yiq(r, g, b)
    h2, l2, s2 = rgb_to_hls(r, g, b)
    h3, s3, v3 = rgb_to_hsv(r, g, b)
    y4, m4, c4, k4 = rgb_to_ymck(r, g, b)
    complementary = complementary_color(hex_color)
    analogous = analogous_colors(hex_color)
    return {
        'colors': qhtml(
            f"""
<div class="color-preview">
    <span>Color</span><div class="color-box" style="background-color: {hex_color};">{hex_color}</div>
    <span>Complementary</span><div class="color-box" style="background-color: {complementary};">{complementary}</div>
    <span>Analogous 1</span><div class="color-box" style="background-color: {analogous[0]};">{analogous[0]}</div>
    <span>Analogous 2</span><div class="color-box" style="background-color: {analogous[1]};">{analogous[1]}</div>
</div>"""
        ),
        'hex_color': hex_color,
        'rgb_color': f'Red={r}, Green={g}, Blue={b}',
        'yiq_color': f'Y/Brightness={y1:.3f}, I/Chroma={i1:.3f}, Q/Chroma={q1:.3f}',
        'hls_color': f'Hue={h2:.3f}, Lightness={l2:.3f}, Saturation={s2:.3f}',
        'hsv_color': f'Hue={h3:.3f}, Saturation={s3:.3f}, Value={v3:.3f}',
        'ymck_color': f'Yellow={y4:.3f}, Magenta={m4:.3f}, Cyan={c4:.3f}, Key/Black={k4:.3f}',
        'complementary': complementary,
        'analogous': analogous
    }
