# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from PIL import Image, ImageOps, ExifTags
from qcore import qurl, qf2img, qimage, QImage, QScreen, qhtml
import io
from qutil import demo_url


def image_reader__info():
    return {
        'title': 'Image Reader',
        'calculate': 'Display',
        'schema': {
            'upload_image': {
                'help_text': 'Maximum image file size is 10 MB. '
                             'Either select an image file to upload or enter the Image Url.'
            },
        }
    }


def image_reader(upload_image: qimage = None, image_url: qurl = demo_url('dog.jpg'), show_exif_tags=False):
    qimg = qf2img(upload_image, image_url)
    toret = {
        'image': qimg,
    }
    if show_exif_tags:
        out = QScreen()
        with Image.open(qimg.bio) as img:
            out.write(f"Image file format: {img.format}")
            out.write(f"Image pixel format: {img.mode}")
            out.write(f"Image size (width, height): {img.size}")
            out.write(f"Image palette: {img.palette}")
            out.write("")
            exif = {ExifTags.TAGS[k]: v for k, v in img.getexif().items() if k in ExifTags.TAGS}
            out.write(f"Image exif tags{": none" if exif == {} else " follows:"}")
            for k, v in exif.items():
                out.write(f"{k} = {v}")
            toret['exif tags'] = out.flush()
    return toret


def image_gray__info():
    return {
        'title': 'Convert Image to Grayscale or Black & White',
        'calculate': 'Convert',
        'schema': {
            'option': {'type': 'choice', 'choices': {'gray': 'Gray Scale', 'bw': 'Black & white'}},
            'upload_image': {
                'help_text': 'Maximum image file size is 10 MB. '
                             'Either select an image file to upload or enter the Image Url.'
            },
        }
    }


def image_gray(upload_image: qimage = None, image_url: qurl = demo_url('parrot.jpg'), option='gray'):
    qimg = qf2img(upload_image, image_url)
    with Image.open(qimg.bio) as img:
        if option == 'gray':
            img_out = ImageOps.grayscale(img)
        elif option == 'bw':
            # img_out = img.convert('1')
            thresh = 128
            fn = lambda x: 255 if x > thresh else 0
            img_out = img.convert('L').point(fn, mode='1')

        bio = io.BytesIO()
        img_out.save(bio, format='png')
    return {
        'Converted Image': QImage(bio),
        'Original Image': qimg
    }


def image_rotate__info():
    return {
        'title': 'Rotate an Image',
        'calculate': 'Rotate',
        'schema': {
            'option': {'type': 'choice', 'choices': {'gray': 'Gray Scale', 'bw': 'Black & white'}},
            'upload_image': {
                'help_text': 'Maximum image file size is 10 MB. '
                             'Either select an image file to upload or enter the Image Url.'
            },
            'rotation': {
                'help_text': 'Enter a value in degree rotation, between -180 and 180. '
                             'Positive value means counter clockwise rotation. '
                             'Negative value means clockwise rotation.',
                'attrs': {'max': 180.0, 'min': -180.0},
            },
        }
    }


def image_rotate(upload_image: qimage = None, image_url: qurl = demo_url('parrot.jpg'), rotation: float = 90.0):
    qimg = qf2img(upload_image, image_url)
    with Image.open(qimg.bio) as img:
        img_out = img.rotate(rotation)
        bio = io.BytesIO()
        img_out.save(bio, format='png')
    return {
        'Converted Image': QImage(bio),
        'Original Image': qimg
    }


def image_resize__info():
    return {
        'title': 'Resize an Image',
        'calculate': 'Resize',
        'schema': {
            'upload_image': {
                'help_text': 'Maximum image file size is 10 MB. '
                             'Either select an image file to upload or enter the Image Url.'
            },
            'option': {
                'type': 'choice',
                'choices':
                    {
                        'w': 'Change width (hight proportional)',
                        'h': 'Change height (width proportional)',
                        'wp': 'Change width%, (hight proportional)',
                        'hp': 'Change height% (width proportional)',
                        'wh': 'Change both width and heigth',
                        'whp': 'Change both width% and height%',
                    }
            },
            'width': {
                'help_text': 'Enter a value between 16 and 5000',
                'attrs': {'max': 5000, 'min': 16},
            },
            'height': {
                'help_text': 'Enter a value between 16 and 5000',
                'attrs': {'max': 5000, 'min': 16},
            },
            'width_percent': {
                'help_text': 'Enter a value between 10 and 1000',
                'attrs': {'max': 1000, 'min': 10},
            },
            'height_percent': {
                'help_text': 'Enter a value between 10 and 1000',
                'attrs': {'max': 1000, 'min': 10},
            },
        },
        'showhide': {
            'option': {
                'fields': ['width', 'height', 'width_percent', 'height_percent'],
                'callback': {
                    'w': '[1, 0, 0, 0]',
                    'h': '[0, 1, 0, 0]',
                    'wp': '[0, 0, 1, 0]',
                    'hp': '[0, 0, 0, 1]',
                    'wh': '[1, 1, 0, 0]',
                    'whp': '[0, 0, 1, 1]',
                }
            }
        },
    }


def image_resize(upload_image: qimage = None, image_url: qurl = demo_url('parrot.jpg'),
                 option='w',
                 width: int = 640, height: int = 640,
                 width_percent: int = 200, height_percent: int = 200):
    qimg = qf2img(upload_image, image_url)
    with Image.open(qimg.bio) as img:
        img_aspect = img.size[0] / img.size[1]
        if option == 'w':
            img2_width = width
            img2_height = int(width / img_aspect)
        elif option == 'h':
            img2_width = int(height * img_aspect)
            img2_height = height
        elif option == 'wp':
            img2_width = int(width_percent * img.size[0] / 100)
            img2_height = int(img2_width / img_aspect)
        elif option == 'hp':
            img2_width = int(height_percent * img.size[1] * img_aspect / 100)
            img2_height = int(img2_width / img_aspect)
        elif option == 'wh':
            img2_width = width
            img2_height = height
        elif option == 'whp':
            img2_width = int(width_percent * img.size[0] / 100)
            img2_height = int(height_percent * img.size[1] * img_aspect / 100)

        img2_width = 16 if img2_width < 16 else img2_width
        img2_width = 5000 if img2_width > 5000 else img2_width

        if option in ['wh', 'whp']:  # aspect changed
            img2_height = 1 if img2_height < 1 else img2_height
            img2_height = 5000 if img2_height > 5000 else img2_height
        else:
            img2_height = int(img2_width / img_aspect)
            img2_height = 16 if img2_height < 16 else img2_height
            img2_height = 5000 if img2_height > 5000 else img2_height
            img2_width = int(img2_height * img_aspect)

        img2_size = (img2_width, img2_height)
        img2 = img.resize(img2_size)
        bio = io.BytesIO()
        img2.save(bio, format='png')

    return {
        'Converted Image Size': qhtml(f"Width {img2_width} x Height {img2_height}"),
        'Original Image Size': qhtml(f"Width {img.size[0]} x Height {img.size[1]}"),
        'Converted Image': QImage(bio),
        'Original Image': qimg
    }
