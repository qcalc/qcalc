# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from PIL import Image
from qcore import qurl, qpage, qf2img, qimage
from qutil import demo_url


class AsciiArt:
    def __init__(self, img_buf, width):
        self.img = Image.open(img_buf)
        self.width = width  # characters width

    def image(self):
        width, height = self.img.size
        aspect_ratio = height / width
        new_width = self.width
        new_height = int(aspect_ratio * new_width * 0.55)
        img = self.img.resize((new_width, new_height), resample=0)
        img = img.convert('L')
        pixels = img.getdata()
        chars = ["B", "S", "#", "&", "@", "$", "%", "*", "!", ":", "."]
        new_pixels = [chars[pixel // 25] for pixel in pixels]
        new_pixels = ''.join(new_pixels)
        new_pixels_count = len(new_pixels)
        ascii_image = [new_pixels[index:index + new_width]
                       for index in range(0, new_pixels_count, new_width)]
        ascii_image = "\n".join(ascii_image)
        return ascii_image


def img2asc__info():
    return {
        'title': 'Generate ASCII art from an image',
    }


def img2asc(upload_image: qimage, image_url: qurl = demo_url('dog.jpg'), width=60):
    qimg = qf2img(upload_image, image_url)
    art = AsciiArt(qimg.bio, width)
    return {
        'Image': qimg,
        'ASCII Art': qpage(art.image())
    }
